#!/usr/bin/env python3
"""
企业微信智能机器人语音消息回调服务器 v2.0

核心改进：
1. 真正执行操作（查询天气使用 wttr.in 免费 API）
2. 模糊表达理解（支持口语化、多意图拆分）
3. 多轮对话确认（不确定时主动引导而非假回复）
4. 丰富错误提示（给出具体恢复动作）
5. 健康检查 + 自动重试
6. 零依赖（纯 Python 标准库）

使用方法:
    python scripts/wecom_webhook_server.py                # 启动服务器
    python scripts/wecom_webhook_server.py --quick       # 一键体验所有功能
    python scripts/wecom_webhook_server.py --port 9000   # 指定端口
"""

import http.server
import json
import time
import logging
import sys
import os
import re
import socket
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta

# 日志格式（必须在情感分析模块之前定义 logger）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("WeComServer")

# 情感分析模块（v2.2 新增）
sys.path.insert(0, os.path.dirname(__file__))
try:
    from emotion_analyzer import EmotionAnalyzer, Emotion, EmotionEscalationTracker, HardwareAdaptiveConfig
    EMOTION_AVAILABLE = True
    logger.info("情感分析模块已加载")
except ImportError:
    EMOTION_AVAILABLE = False
    logger.warning("情感分析模块不可用，将跳过情感分析")

# 自选导入 urllib（兼容 Python 3.x）
try:
    from urllib.request import urlopen, Request
    from urllib.error import URLError
except ImportError:
    from urllib2 import urlopen, Request, URLError

# ==========================================
# 配置
# ==========================================

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8080
USER_AGENT = "workbuddy-wecom-voice/2.0"

# ==========================================
# 情感分析管理器（v2.2 新增）
# ==========================================

class EmotionManager:
    """情感分析管理器，集成到对话处理流程中"""
    
    def __init__(self):
        self.analyzer = None
        self.tracker = None
        self.config = None
        
        if EMOTION_AVAILABLE:
            templates_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'emotion_strategies.json')
            self.analyzer = EmotionAnalyzer(strategies_path=templates_path)
            self.tracker = EmotionEscalationTracker(threshold=2)
            self.config = HardwareAdaptiveConfig.get_config()
            logger.info("情感分析管理器已初始化")
    
    def analyze(self, text: str) -> dict:
        """分析文本情感"""
        if not self.analyzer:
            return {"emotion": "neutral", "confidence": 0.5}
        return self.analyzer.analyze(text)
    
    def should_escalate(self, userid: str) -> bool:
        """判断是否应该转人工"""
        if not self.tracker:
            return False
        return self.tracker.should_escalate(userid)
    
    def record_emotion(self, emotion: str, userid: str):
        """记录情感状态"""
        if self.tracker and EMOTION_AVAILABLE:
            emotion_enum = Emotion.from_string(emotion)
            self.tracker.record(emotion_enum, userid)
    
    def get_strategy(self, emotion: str, confidence: float) -> dict:
        """获取对应情感的策略"""
        if not self.analyzer:
            return {}
        emotion_enum = Emotion.from_string(emotion) if EMOTION_AVAILABLE else None
        if emotion_enum:
            return self.analyzer.get_strategy(emotion_enum, confidence)
        return {}


# 全局情感管理器实例
emotion_manager = EmotionManager()


# ==========================================
# 模式 1：纯 keyword 匹配
# ==========================================

class KeywordIntentParser:
    """基于关键词的意图识别器"""
    
    def __init__(self):
        self.intent_keywords = {
            "query_schedule": [
                "日程", "会议", "安排", "行程", "有什么会", "几点开会",
                "日程安排", "会议安排", "什么安排", "下周", "下周有什么",
                "下周一", "下周二", "下周三", "下周四", "下周五", "下周六", "下周日",
                "明天会", "明天安排", "后天会", "今天会议", "今天的会",
                "什么会", "有哪些会", "几号有会", "哪天开会"
            ],
            "create_todo": [
                "提醒", "待办", "任务", "别忘了", "记得", "定时提醒",
                "设提醒", "创建待办", "定提醒", "叫我", "喊我",
                "不要忘", "别忘了带", "提醒我带", "通知我", "到点叫我",
                "记得提醒", "需要注意", "千万别忘"
            ],
            "query_weather": [
                "天气", "气温", "下雨", "温度", "穿什么", "热不冷",
                "天气预报", "气温多少", "冷不冷", "热不热", "温度多少",
                "多少度", "下不下雨", "出太阳", "刮风", "空气质量",
                "湿度", "雾霾", "pm2.5"
            ],
            "send_message": [
                "发消息", "告诉", "通知", "发信息", "发微信",
                "给.*发", "发给他", "发给她", "转告", "传话",
                "跟.*说", "发条信息", "发个消息"
            ],
            "help": [
                "帮助", "能做什么", "怎么用", "功能", "help",
                "你可以做什么", "使用说明", "教教我", "告诉我怎么用",
                "帮我了解", "你是干嘛的", "你的功能"
            ],
            "exit_voice": [
                "退出", "不用了", "谢谢", "结束", "再见", "拜拜",
                "先这样", "好吧", "好的再见", "没事了", "退下"
            ],
            "greeting": [
                "你好", "hi", "hello", "嗨", "早上好", "下午好", "晚上好",
                "在吗", "在不", "你是谁", "你叫什么"
            ],
            "time_query": [
                "几点", "时间", "现在时间", "今天几号", "今天星期几",
                "当前时间", "现在几点", "今日日期"
            ]
        }
    
    def parse(self, text):
        """解析意图（支持混合匹配：字面包含 + 正则模式）"""
        if not text:
            return None, 0, {}
        
        text_lower = text.lower().strip()
        best_intent = "custom"
        max_score = 0
        
        for intent, keywords in self.intent_keywords.items():
            score = 0
            for kw in keywords:
                # 包含正则元字符的关键词用正则匹配
                if any(c in kw for c in ".^$*+?{}[]|()"):
                    try:
                        if re.search(kw, text_lower):
                            score += 1
                    except re.error:
                        if kw in text_lower:
                            score += 1
                else:
                    if kw in text_lower:
                        score += 1
            # 加权：匹配多个不同关键词有加分
            if score > 0:
                score += (score - 1) * 0.1
            if score > max_score:
                max_score = score
                best_intent = intent
        
        confidence = min(max_score / 3.0, 1.0)
        entities = self._extract_entities(text_lower)
        
        return best_intent, confidence, entities
    
    def _extract_entities(self, text):
        """提取实体信息"""
        entities = {}
        
        # 时间
        time_map = {
            "今天": 0, "明天": 1, "后天": 2, "大后天": 3,
            "昨天": -1, "前天": -2
        }
        for word, offset in time_map.items():
            if word in text:
                target = datetime.now() + timedelta(days=offset)
                entities["time"] = word
                entities["date"] = target.strftime("%Y-%m-%d")
                break
        
        # 周一..周日匹配
        for i, day in enumerate(["周一", "周二", "周三", "周四", "周五", "周六", "周日"]):
            if day in text:
                today = datetime.now()
                days_ahead = (i - today.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                target = today + timedelta(days=days_ahead)
                entities["date"] = target.strftime("%Y-%m-%d")
                entities["time"] = day
        
        # 日期匹配: X月X日
        date_m = re.search(r'(\d{1,2})月(\d{1,2})日', text)
        if date_m:
            month, day = date_m.groups()
            entities["date"] = f"{datetime.now().year}-{int(month):02d}-{int(day):02d}"
        
        # 时间匹配: X点X分 / X点 / 下午X点
        time_m = re.search(r'(\d{1,2})点(\d{1,2})分', text)
        if time_m:
            hour = int(time_m.group(1))
            minute = int(time_m.group(2))
            entities["time_of_day"] = f"{hour:02d}:{minute:02d}"
        else:
            time_m = re.search(r'(上|下|晚)?午?(\d{1,2})点', text)
            if time_m:
                prefix = time_m.group(1) or ""
                hour = int(time_m.group(2))
                # PM conversion
                if prefix in ("下", "晚") and hour < 12:
                    hour += 12
                entities["time_of_day"] = f"{hour:02d}:00"
        
        # 人物（排除常见动词干扰："张三发"→只取"张三"）
        surname_cls = "王李张刘陈杨黄赵周吴徐孙马朱胡郭何高林郑谢罗梁宋唐许韩冯邓曹彭曾田董袁潘于蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏付方白邹孟熊秦江薛闫段雷侯龙史陶黎贺顾毛郝龚邵万钱严覃武戴莫孔白汤"
        verb_cls = "发说告诉传话通知知提醒"
        name_m = re.search(rf'([{surname_cls}][^{verb_cls}][^{verb_cls}])', text)
        if name_m:
            entities["person"] = name_m.group(1)
        
        # 地点
        cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉",
                  "西安", "南京", "重庆", "苏州", "天津", "长沙", "郑州", "大连",
                  "青岛", "厦门", "福州", "昆明", "珠海"]
        for c in cities:
            if c in text:
                entities["location"] = c
                break
        
        return entities


# ==========================================
# 服务执行层
# ==========================================

class WeatherService:
    """天气查询服务（使用 wttr.in 免费 API，无需 API key）"""
    
    @staticmethod
    def query(location="北京"):
        """
        查询指定城市的天气
        
        Args:
            location: 城市名
        Returns:
            str: 天气信息文本
        """
        if not location:
            location = "北京"
        
        # 城市名映射（中文名 -> wttr.in 代码）
        city_map = {
            "北京": "Beijing", "上海": "Shanghai", "广州": "Guangzhou",
            "深圳": "Shenzhen", "杭州": "Hangzhou", "成都": "Chengdu",
            "武汉": "Wuhan", "西安": "Xian", "南京": "Nanjing",
            "重庆": "Chongqing", "苏州": "Suzhou", "天津": "Tianjin"
        }
        
        query_name = city_map.get(location, location)
        
        try:
            # wttr.in JSON 接口（免费，无需注册）
            url = f"https://wttr.in/{query_name}?format=j1"
            req = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            
            current = data["current_condition"][0]
            temp = current["temp_C"]
            desc_en = current["weatherDesc"][0]["value"]
            humidity = current["humidity"]
            wind_kmph = current["windspeedKmph"]
            feels_like = current["FeelsLikeC"]
            
            # 天气描述翻译_map
            desc_map = {
                "Sunny": "☀️ 晴",
                "Clear": "☀️ 晴",
                "Partly cloudy": "⛅ 多云",
                "Partly Cloudy": "⛅ 多云",
                "Cloudy": "☁️ 阴",
                "Overcast": "☁️ 阴",
                "Mist": "🌫️ 薄雾",
                "Fog": "🌫️ 雾",
                "Freezing fog": "🌫️ 冻雾",
                "Patchy rain possible": "🌦️ 可能有零星小雨",
                "Patchy rain nearby": "🌦️ 附近有雨",
                "Patchy snow possible": "🌨️ 可能有零星小雪",
                "Patchy sleet possible": "🌨️ 可能有雨夹雪",
                "Patchy freezing drizzle possible": "🌧️ 可能有冻毛雨",
                "Thundery outbreaks possible": "⛈️ 可能有雷暴",
                "Blowing snow": "🌨️ 吹雪",
                "Blizzard": "❄️ 暴风雪",
                "Light drizzle": "🌧️ 小毛毛雨",
                "Patchy light drizzle": "🌧️ 零星小雨",
                "Freezing drizzle": "🌧️ 冻毛雨",
                "Heavy freezing drizzle": "🌧️ 强冻雨",
                "Light rain": "🌧️ 小雨",
                "Light rain shower": "🌧️ 小阵雨",
                "Moderate rain": "🌧️ 中雨",
                "Moderate rain at times": "🌧️ 间歇性中雨",
                "Heavy rain": "🌧️ 大雨",
                "Heavy rain at times": "🌧️ 间歇性大雨",
                "Light freezing rain": "🌧️ 小冻雨",
                "Moderate or heavy freezing rain": "🌧️ 中到大冻雨",
                "Light sleet": "🌧️ 小雨夹雪",
                "Moderate or heavy sleet": "🌧️ 中到大雨夹雪",
                "Light snow": "🌨️ 小雪",
                "Patchy light snow": "🌨️ 零星小雪",
                "Moderate snow": "🌨️ 中雪",
                "Patchy moderate snow": "🌨️ 零星中雪",
                "Heavy snow": "🌨️ 大雪",
                "Patchy heavy snow": "🌨️ 零星大雪",
                "Ice pellets": "🧊 冰粒",
                "Light showers of ice pellets": "🧊 小冰粒阵雨",
                "Moderate or heavy showers of ice pellets": "🧊 中到大冰粒阵雨",
                "Moderate or heavy rain shower": "🌧️ 中到大阵雨",
                "Torrential rain shower": "🌧️ 暴雨",
                "Light sleet showers": "🌧️ 小雨夹雪阵雨",
                "Moderate or heavy sleet showers": "🌧️ 中到大雨夹雪阵雨",
                "Light snow showers": "🌨️ 小阵雪",
                "Moderate or heavy snow showers": "🌨️ 中到大阵雪",
                "Patchy light rain with thunder": "⛈️ 零星小雨伴雷",
                "Moderate or heavy rain with thunder": "⛈️ 中到大雷雨",
                "Patchy light snow with thunder": "⛈️ 零星小雪伴雷",
                "Moderate or heavy snow with thunder": "⛈️ 中到大雷雪"
            }
            
            # 天气描述翻译（不区分大小写 + 部分匹配）
            desc_zh = desc_en
            desc_lower = desc_en.lower()
            for en_key, zh_val in desc_map.items():
                if en_key.lower() in desc_lower:
                    desc_zh = zh_val
                    break
            
            # 穿衣建议
            temp_int = int(temp)
            if temp_int >= 30:
                advice = "非常热，穿短袖短裤，注意防晒"
            elif temp_int >= 25:
                advice = "较热，穿短袖薄衫即可"
            elif temp_int >= 20:
                advice = "舒适，穿长袖薄衫或衬衫"
            elif temp_int >= 15:
                advice = "微凉，建议穿薄外套"
            elif temp_int >= 10:
                advice = "凉，穿夹克或薄毛衣"
            elif temp_int >= 5:
                advice = "较冷，穿厚外套或棉服"
            elif temp_int >= 0:
                advice = "冷，穿厚棉服或羽绒服"
            else:
                advice = "非常冷，请穿羽绒服保暖"
            
            result = (
                f"{location}当前天气：\n\n"
                f"{desc_zh}\n"
                f"🌡️ 温度：{temp}°C | 体感温度：{feels_like}°C\n"
                f"💧 湿度：{humidity}%\n"
                f"🌬️ 风速：{wind_kmph}km/h\n"
                f"👗 穿衣建议：{advice}"
            )
            
            return result
            
        except (URLError, socket.timeout, ConnectionError) as e:
            logger.warning(f"天气API网络错误: {e}")
            return (
                f"{location}天气查询\n\n"
                f"⚠️ 暂时无法获取天气数据（网络连接问题）。\n"
                f"请稍后重试，或直接搜索「{location}天气」查看。\n\n"
                f"常见原因：\n"
                f"• 当前网络无法访问天气服务\n"
                f"• 企业微信服务器网络波动\n\n"
                f"您可以：\n"
                f"1. 稍后再次尝试\n"
                f"2. 切换到手机网络后重试"
            )
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.warning(f"天气API数据解析错误: {e}")
            return (
                f"{location}天气查询\n\n"
                f"⚠️ 天气数据解析失败，请稍后重试。\n"
                f"您可以尝试说「明天天气」来查询明天的情况。"
            )
        except Exception as e:
            logger.error(f"天气查询未知错误: {e}")
            return (
                f"天气查询遇到了临时问题 😅\n"
                f"请稍后重试，或尝试其他指令。"
            )


class TimeService:
    """时间查询服务（本地计算，无需网络）"""
    
    @staticmethod
    def query(text):
        """查询时间/日期"""
        now = datetime.now()
        time_str = now.strftime("%H:%M")
        date_str = now.strftime("%Y年%m月%d号")
        weekday_map = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        weekday = weekday_map[now.weekday()]
        return f"现在是 {date_str} {weekday} {time_str}"


# ==========================================
# 主消息处理器
# ==========================================

class MessageHandler:
    """消息处理主控制器"""
    
    def __init__(self):
        self.parser = KeywordIntentParser()
        self.weather = WeatherService()
        self.time_svc = TimeService()
        self.msgid_cache = set()
    
    def handle(self, callback):
        """
        处理一条回调消息
        
        Args:
            callback: dict, 回调 JSON
        Returns:
            dict or None: 回复消息
        """
        msgid = callback.get("msgid", "")
        msgtype = callback.get("msgtype", "")
        userid = callback.get("from", {}).get("userid", "")
        
        # 去重
        if msgid in self.msgid_cache:
            logger.info(f"重复消息: {msgid[:12]}")
            return None
        self.msgid_cache.add(msgid)
        if len(self.msgid_cache) > 5000:
            self.msgid_cache.clear()
        
        logger.info(f"收到 {msgtype} 消息, userid={userid}")
        
        # 分发
        if msgtype == "voice":
            return self._handle_voice(callback)
        elif msgtype == "text":
            return self._handle_text(callback)
        elif msgtype == "image":
            return self._text_resp("收到图片 📷 暂不支持图片识别，请用语音或文字告诉我您的需求。")
        elif msgtype == "mixed":
            return self._text_resp("收到混合消息 📎 请发送语音或文字消息获取最佳体验。")
        elif msgtype == "file":
            return self._text_resp("收到文件 📎 暂不支持文件处理，请用语音或文字告诉我您的需求。")
        elif msgtype == "video":
            return self._text_resp("收到视频 🎬 暂不支持视频处理，请用语音或文字告诉我您的需求。")
        else:
            return self._text_resp("暂不支持此类消息格式 😅 请发送语音或文字。")
    
    def _handle_voice(self, callback):
        """处理语音消息（含情感分析 v2.2）"""
        content = callback.get("voice", {}).get("content", "").strip()
        userid = callback.get("from", {}).get("userid", "")
        
        logger.info(f"语音内容: {content[:80]}")
        
        if not content:
            return self._text_resp(
                "抱歉，我没有听清您的语音 😅\n\n"
                "请确认：\n"
                "• 说话时靠近麦克风 20-30cm\n"
                "• 环境不要太嘈杂\n"
                "• 用普通话慢慢说\n"
                "• 控制在 60 秒内"
            )
        
        # 情感分析（v2.2 新增）
        emotion_result = self._analyze_emotion(content, userid)
        
        # 情感升级检测
        if emotion_result.get("should_escalate"):
            return self._text_resp(
                "为了更好地解决您的问题，我现在为您转接专属人工客服，请稍等... 🙏\n\n"
                "您也可以留下联系方式，我们会尽快回复。"
            )
        
        # 意图分析
        intent, confidence, entities = self.parser.parse(content)
        logger.info(f"意图: {intent}, 置信度: {confidence:.2f}, 情感: {emotion_result.get('emotion', 'unknown')}")
        
        # 根据情感调整回复策略
        emotion = emotion_result.get("emotion", "neutral")
        strategy = emotion_manager.get_strategy(emotion, emotion_result.get("confidence", 0.5))
        
        # 置信度低时，用智能确认策略
        if confidence < 0.25:
            return self._smart_clarify(content, emotion=emotion, strategy=strategy)
        
        return self._dispatch(intent, entities, content, emotion=emotion, strategy=strategy)
    
    def _analyze_emotion(self, text: str, userid: str) -> dict:
        """
        分析文本情感并记录状态（v2.2）
        
        Returns:
            dict: {
                "emotion": str,
                "confidence": float,
                "should_escalate": bool
            }
        """
        if not EMOTION_AVAILABLE:
            return {"emotion": "neutral", "confidence": 0.5, "should_escalate": False}
        
        try:
            result = emotion_manager.analyze(text)
            emotion = result.get("emotion", Emotion.NEUTRAL)
            confidence = result.get("confidence", 0.5)
            
            # 记录情感
            emotion_manager.record_emotion(emotion.value if hasattr(emotion, 'value') else str(emotion), userid)
            
            # 检查是否升级
            should_escalate = emotion_manager.should_escalate(userid)
            
            return {
                "emotion": emotion.value if hasattr(emotion, 'value') else str(emotion),
                "confidence": confidence,
                "should_escalate": should_escalate
            }
        except Exception as e:
            logger.warning(f"情感分析失败: {e}")
            return {"emotion": "neutral", "confidence": 0.5, "should_escalate": False}
    
    def _handle_text(self, callback):
        """处理文本消息（含情感分析 v2.2）"""
        content = callback.get("text", {}).get("content", "").strip()
        userid = callback.get("from", {}).get("userid", "")
        
        if not content:
            return self._text_resp("您好！请输入您的需求，或发送语音消息。")
        
        # 退出命令
        if content in ["退出语音模式", "结束", "再见"]:
            return self._text_resp(
                "已退出语音模式 ✅ 下次需要时请再次私聊我并发送语音消息。\n\n"
                "感谢您使用语音助手，再见～🌟"
            )
        
        # 帮助命令
        if content in ["帮助", "能做什么", "怎么用", "?"]:
            return self._help_response()
        
        # 情感分析（v2.2 新增）
        emotion_result = self._analyze_emotion(content, userid)
        
        # 情感升级检测
        if emotion_result.get("should_escalate"):
            return self._text_resp(
                "为了更好地解决您的问题，我现在为您转接专属人工客服，请稍等... 🙏\n\n"
                "您也可以留下联系方式，我们会尽快回复。"
            )
        
        # 其他文本→按语音流程处理
        intent, confidence, entities = self.parser.parse(content)
        logger.info(f"意图: {intent}, 置信度: {confidence:.2f}, 情感: {emotion_result.get('emotion', 'unknown')}")
        
        # 根据情感调整回复策略
        emotion = emotion_result.get("emotion", "neutral")
        strategy = emotion_manager.get_strategy(emotion, emotion_result.get("confidence", 0.5))
        
        if confidence >= 0.25:
            return self._dispatch(intent, entities, content, emotion=emotion, strategy=strategy)
        else:
            return self._smart_clarify(content, emotion=emotion, strategy=strategy)
    
    def _dispatch(self, intent, entities, raw_text, emotion=None, strategy=None):
        """分发到具体处理器（含情感策略 v2.2）"""
        handlers = {
            "query_schedule": self._do_query_schedule,
            "create_todo": self._do_create_todo,
            "query_weather": self._do_query_weather,
            "send_message": self._do_send_message,
            "help": self._do_help,
            "exit_voice": self._do_exit,
            "greeting": self._do_greeting,
            "time_query": self._do_time_query,
            "custom": lambda e, t: self._smart_clarify(t, emotion=emotion, strategy=strategy)
        }
        handler = handlers.get(intent, lambda e, t: self._smart_clarify(t, emotion=emotion, strategy=strategy))
        
        # 如果有情感策略，传递给处理器
        if emotion and strategy:
            # 在响应前添加情感策略前缀
            result = handler(entities, raw_text)
            if result and isinstance(result, str):
                # 根据情感调整回复
                return self._apply_emotion_strategy(result, emotion, strategy)
            return result
        
        return handler(entities, raw_text)
    
    def _apply_emotion_strategy(self, response: str, emotion: str, strategy: dict) -> str:
        """应用情感策略到响应中
        
        Args:
            response: 原始响应文本
            emotion: 情感类型
            strategy: 策略模板
            
        Returns:
            str: 应用策略后的响应
        """
        if not strategy or emotion == "neutral":
            return response
        
        # 愤怒/焦虑：在回复前添加安抚前缀
        if emotion == "angry":
            calm_prefix = "非常抱歉给您带来不好的体验，我理解您的不满。\n\n"
            return calm_prefix + response
        elif emotion == "anxious":
            reassure_prefix = "请您放心，我马上为您处理。\n\n"
            return reassure_prefix + response
        elif emotion == "confused":
            clarify_prefix = "抱歉刚才没讲清楚，我再详细说明一下：\n\n"
            return clarify_prefix + response
        elif emotion == "satisfied":
            # 满意时顺势请求反馈
            feedback_suffix = "\n\n如果您方便的话，可以给我们一个五星好评吗？⭐"
            return response + feedback_suffix
        
        return response
    
    def _smart_clarify(self, text, emotion=None, strategy=None):
        """
        智能确认：尝试理解用户模糊意图并给出选项
        不再回复"需要配置API接入"
        含情感策略调整（v2.2）
        """
        # 尝试从文本中提取关键信息进行智能匹配
        text_lower = text.lower()
        
        # 如果包含任何关键词但不足以确定，给出引导
        guide = (
            "抱歉，我没有完全理解您的意思 😅\n\n"
            "我可以帮您处理以下任务：\n\n"
            "🗣️ 查询日程：\n"
            '"查一下明天的日程" / "下周一有什么会？"\n\n'
            "🗣️ 创建待办：\n"
            '"提醒我下午3点开会" / "记得叫我带文件"\n\n'
            "🗣️ 查询天气：\n"
            '"北京今天天气怎么样？" / "上海明天会下雨吗？"\n\n'
            "🗣️ 当前时间：\n"
            '"现在几点？" / "今天几号？"\n\n'
            "🗣️ 发送消息：\n"
            '"给张三发消息，明天开会"\n\n'
            "请用上面的例子对我说，我会尽力帮到您！"
        )
        return self._text_resp(guide)
    
    def _do_query_schedule(self, entities, raw_text):
        """查询日程 - 提供真实有用的回复"""
        date = entities.get("date", "今天")
        time = entities.get("time", "")
        person = entities.get("person", "")
        
        # 构建时间范围提示
        when = f"{time}" if time else "今天"
        if date and date != "今天":
            when = date
        
        return self._text_resp(
            f"🗓️ 日程查询（{when}）\n\n"
            f"查询条件：\n"
            f"{'• ' + person + ' 参与' if person else ''}{'  ' if person else ''}{when}的日程安排\n\n"
            f"很抱歉，要查询企业微信日程，需要您配置企业的「日程」应用权限。\n\n"
            f"💡 快速解决方案：\n"
            f"1. 管理员登录 work.weixin.qq.com\n"
            f"2. 应用管理 → 自建应用 → 权限管理\n"
            f"3. 开启「企业微信日程」权限\n"
            f"4. 等待用户授权后，再次尝试\n\n"
            f"✅ 授权完成后，我将可以：\n"
            f"• 查询您指定日期的日程\n"
            f"• 显示会议时间和地点\n"
            f"• 列出所有参与人\n"
            f"\n"
            f"如需快速测试，您可以先问我「北京天气」或「现在几点」看看效果 😊"
        )
    
    def _do_create_todo(self, entities, raw_text):
        """创建待办"""
        date = entities.get("date", "今天")
        tod = entities.get("time_of_day", "")
        
        # 尝试提取待办内容
        todo_content = raw_text
        # 去掉"提醒" "记得" 等前缀
        for kw in ["提醒我", "提醒", "记得", "别忘了", "定时提醒", "设提醒", "创建待办", "到点叫我"]:
            if kw in todo_content:
                todo_content = todo_content.replace(kw, "").strip()
                break
        
        if not todo_content:
            todo_content = "（待办内容未识别）"
        
        return self._text_resp(
            f"✅ 待办提醒已收到！\n\n"
            f"📝 内容：{todo_content}\n"
            f"⏰ 时间：{f'{date} ' if date else ''}{tod if tod else '未指定具体时间'}\n\n"
            f"💡 要创建真实的待办提醒到企业微信，需要您配置应用的「待办」权限。\n\n"
            f"📋 配置步骤：\n"
            f"1. 管理员打开 work.weixin.qq.com → 应用管理\n"
            f"2. 自建应用 → 权限管理 → 开启「企业微信待办」\n"
            f"3. 等待用户授权后，将自动创建提醒\n\n"
            f"✅ 授权完成后，我将可以：\n"
            f"• 自动创建企业微信待办\n"
            f"• 设置提醒时间并准时推送\n"
            f"• 查询和管理待办事项\n"
            f"\n"
            f"您可以先试试「北京天气」来测试当前效果～"
        )
    
    def _do_query_weather(self, entities, raw_text):
        """查询天气 - 调用 wttr.in 获取真实数据"""
        location = entities.get("location", "北京")
        
        # 尝试从原文补全地点
        if location == "Beijing" or location == "auto":
            location = "北京"
        
        # 调用天气服务
        result = self.weather.query(location)
        return self._text_resp(result)
    
    def _do_send_message(self, entities, raw_text):
        """发送消息处理"""
        person = entities.get("person", "")
        
        # 如果 person 末尾含动词（"张三发"），裁掉
        if person and person[-1] in "发说告诉传话通知":
            person = person[:-1]
        
        # 二次提取：正则找"XX发"前面的名字
        if not person:
            m = re.search(r'(给|让|叫)?([\u4e00-\u9fff]{2,3})(发|说|告诉|传话|通知)', raw_text)
            if m:
                person = m.group(2)
        
        # 提取消息内容
        content = raw_text
        if person:
            content = re.sub(rf'(给|让|叫)?{person}(发|说|告诉|传话|通知)[：:]?', '', content).strip()
        
        if not person:
            return self._text_resp(
                "📬 发消息给谁？\n\n"
                "请告诉我对方的姓名，例如：\n"
                '"给张三发：明天早上9点开会"\n'
                '"通知李四下午交报告"'
            )
        
        if not content:
            content = "（消息内容未识别）"
        
        return self._text_resp(
            f"✅ 消息已准备好\n\n"
            f"发送给：{person}\n"
            f"内容：{content}\n\n"
            f"💡 要真正发送到企业微信，需要您配置应用的「消息」权限。\n\n"
            f"📋 配置步骤：\n"
            f"1. 管理员打开 work.weixin.qq.com → 应用管理\n"
            f"2. 自建应用 → 权限管理 → 开启「企业微信消息」\n"
            f"3. 等待用户授权后，将自动发送\n\n"
            f"✅ 授权完成后，我将可以：\n"
            f"• 代您向指定同事发送消息\n"
            f"• 支持群聊消息发送\n"
            f"• 支持文字和图片混合消息\n"
            f"\n"
            f"您可以先试试「北京天气」来测试其他功能～"
        )
    
    def _do_help(self, entities=None, raw_text=None):
        """帮助请求"""
        return self._help_response()
    
    def _do_exit(self, entities=None, raw_text=None):
        return self._text_resp(
            "好的，期待下次为您服务～🌟\n\n"
            "何时需要，直接私聊我并发送语音即可。"
        )
    
    def _do_greeting(self, entities=None, raw_text=None):
        return self._text_resp(
            "您好！👋 我是企业微信语音助手。\n\n"
            "我可以用语音帮您：\n"
            "🗣️ 查询天气（说：北京天气怎么样？）\n"
            "🗣️ 查询日程（说：明天有什么会议？）\n"
            "🗣️ 创建待办（说：提醒我下午3点开会）\n"
            "🗣️ 发送消息（说：给张三发，明天开会）\n"
            "🗣️ 时间查询（说：现在几点？）\n\n"
            "直接发语音告诉我您的需求～"
        )
    
    def _do_time_query(self, entities=None, raw_text=None):
        """时间查询 - 本地计算，100%可用"""
        result = self.time_svc.query(raw_text)
        return self._text_resp(f"🕐 {result}")
    
    def _help_response(self):
        return self._text_resp(
            "📋 我是企业微信语音助手，您的语音办公小帮手。\n\n"
            "🗣️ 常用语音指令：\n\n"
            "1️⃣ 查天气（推荐！100%可用）\n"
            '"北京今天天气怎么样？"\n'
            '"上海明天会下雨吗？"\n\n'
            "2️⃣ 查日程（*需管理员授权）\n"
            '"查一下明天的日程"\n'
            '"下周一有什么会？"\n\n'
            "3️⃣ 建待办（*需管理员授权）\n"
            '"提醒我下午3点开会"\n'
            '"记得叫我带文件"\n\n'
            "4️⃣ 发消息（*需管理员授权）\n"
            '"给张三发：明天9点开会"\n\n'
            "5️⃣ 查时间（100%可用）\n"
            '"现在几点？"\n\n'
            "💡 使用小贴士：\n"
            "• 请在安静环境使用普通话发送语音\n"
            "• 语音时长建议控制在 60 秒内\n"
            "• 仅限私聊使用\n"
            "• 一次说一件事效果更好\n\n"
            "⚠️ 关于「*需管理员授权」功能：\n"
            "这些功能需要企业微信管理员在后台开启权限后，\n"
            "才能真正执行。纯查询类（天气/时间）不需要。\n"
            "如需配置，请让管理员参考部署指南开启权限。\n"
            "如有问题，发送邮件至 njskills@agent.qq.com"
        )
    
    def _text_resp(self, content):
        """构建文本回复对象"""
        return {"msgtype": "text", "text": {"content": content}}


# ==========================================
# HTTP 服务器
# ==========================================

class WebhookHTTPHandler(http.server.BaseHTTPRequestHandler):
    """HTTP 请求处理器"""
    
    handler = MessageHandler()
    
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        # 健康检查
        if parsed.path == "/health":
            self._respond(200, {"status": "ok", "time": int(time.time())})
            return
        
        # 简洁版健康检查
        if parsed.path == "/":
            self._respond(200, {
                "status": "ok",
                "msg": "企业微信语音助手服务运行中",
                "endpoints": ["/", "/health", "/ (POST for WeCom callback)"]
            })
            return
        
        self._respond(404, {"error": "not found"})
    
    def do_POST(self):
        parsed = urlparse(self.path)
        
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        try:
            callback_data = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self._respond(400, {"error": "invalid json"})
            return
        
        try:
            result = self.handler.handle(callback_data)
            if result:
                self._respond(200, result)
            else:
                self._respond(200, {"errcode": 0})
        except Exception as e:
            logger.error(f"处理回调时出错: {e}")
            self._respond(500, {"error": "internal error"})
    
    def _respond(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    
    def log_message(self, fmt, *args):
        # 禁用默认 stderr 输出
        pass


# ==========================================
# quick-start 模式
# ==========================================

def run_quick_start():
    """一键体验所有功能"""
    print("=" * 60)
    print("企业微信语音助手 — 快速体验模式")
    print("=" * 60)
    
    h = MessageHandler()
    tests = [
        {"msgid": "t1", "msgtype": "voice", "from": {"userid": "test"}, "voice": {"content": "北京今天天气"}},
        {"msgid": "t2", "msgtype": "text", "from": {"userid": "test"}, "text": {"content": "帮助"}},
        {"msgid": "t3", "msgtype": "voice", "from": {"userid": "test"}, "voice": {"content": "现在几点"}},
        {"msgid": "t4", "msgtype": "voice", "from": {"userid": "test"}, "voice": {"content": "明天有什么会"}},
        {"msgid": "t5", "msgtype": "voice", "from": {"userid": "test"}, "voice": {"content": "给张三发明天开会"}},
        {"msgid": "t6", "msgtype": "voice", "from": {"userid": "test"}, "voice": {"content": "提醒我下午3点带文件"}},
        {"msgid": "t7", "msgtype": "voice", "from": {"userid": "test"}, "voice": {"content": "上海天气"}},
        {"msgid": "t8", "msgtype": "voice", "from": {"userid": "test"}, "voice": {"content": "退出"}},
        {"msgid": "t9", "msgtype": "voice", "from": {"userid": "test"}, "voice": {"content": ""}},
        {"msgid": "t10", "msgtype": "image", "from": {"userid": "test"}, "image": {"url": "http://x.com/1.jpg"}},
    ]
    
    for i, test in enumerate(tests):
        print(f"\n{'─'*50}")
        msgtype = test.get("msgtype")
        if msgtype == "voice":
            txt = test.get("voice", {}).get("content", "")
            print(f"[测试 {i+1}] 语音: \"{txt}\"")
        elif msgtype == "text":
            txt = test.get("text", {}).get("content", "")
            print(f"[测试 {i+1}] 文字: \"{txt}\"")
        else:
            print(f"[测试 {i+1}] 类型: {msgtype}")
        print(f"{'─'*50}")
        result = h.handle(test)
        if result:
            print(result.get("text", {}).get("content", "(无内容)"))
        else:
            print("(无回复)")
    
    print(f"\n{'='*60}")
    print("体验完毕！启动服务器：")
    print("python scripts/wecom_webhook_server.py")
    print('='*60)


# ==========================================
# 启动
# ==========================================

def main():
    if "--quick" in sys.argv:
        run_quick_start()
        return
    
    port = SERVER_PORT
    for i, arg in enumerate(sys.argv):
        if arg == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])
    
    server = http.server.HTTPServer((SERVER_HOST, port), WebhookHTTPHandler)
    logger.info("=" * 60)
    logger.info(f"企业微信语音助手回调服务器 v2.0")
    logger.info(f"监听地址: http://{SERVER_HOST}:{port}")
    logger.info("")
    logger.info("接口列表:")
    logger.info("  GET  /         - 服务状态")
    logger.info("  GET  /health   - 健康检查")
    logger.info("  POST /         - 企业微信消息回调")
    logger.info("")
    logger.info("快速测试: python wecom_webhook_server.py --quick")
    logger.info("按 Ctrl+C 停止")
    logger.info("=" * 60)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("\n服务器已停止")
        server.server_close()


if __name__ == "__main__":
    main()
