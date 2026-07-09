#!/usr/bin/env python3
"""
企业微信智能机器人语音消息回调服务器

功能：
1. 接收企业微信智能机器人的消息回调（包括语音消息）
2. 自动解析语音消息内容（企业微信内置 ASR）
3. 执行意图识别和任务分发
4. 支持被动回复（同步）和主动回复（异步）

使用方法：
    python scripts/wecom_webhook_server.py
    python scripts/wecom_webhook_server.py --port 9000
"""

import http.server
import json
import hashlib
import base64
import time
import logging
import sys
import os
from urllib.parse import urlparse, parse_qs
from datetime import datetime

# 尝试导入可选的加密库（如果需要）
try:
    from Crypto.Cipher import AES
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

# ==========================================
# 配置
# ==========================================

# 企业微信回调配置（请根据你的应用信息修改）
WECHAT_CONFIG = {
    "token": "your_token_here",           # 智能机器人回调 Token
    "encoding_aes_key": "your_key_here",  # 智能机器人回调 EncodingAESKey
    "corp_id": "your_corp_id",            # 企业 CorpID
    "corp_secret": "your_corp_secret",    # 应用 Secret
    "agent_id": "your_agent_id",          # 应用 AgentID
    "access_token": None,                 # 接口调用凭证（自动获取）
    "token_expire_time": 0,               # token 过期时间
}

# 服务器配置
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8080

# 日志配置
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("WeComWebhook")

# ==========================================
# AES 解密（企业微信回调加密）
# ==========================================

class PrpCrypt:
    """企业微信回调消息解密"""
    
    def __init__(self, key):
        if not HAS_CRYPTO:
            raise ImportError("需要安装 pycryptodome: pip install pycryptodome")
        self.key = base64.b64decode(key + "=")
        self.mode = AES.MODE_CBC
    
    def decrypt(self, text, receive_id):
        """解密回调消息"""
        try:
            cipher = AES.new(self.key, self.mode, self.key[:16])
            decrypted = cipher.decrypt(base64.b64decode(text))
            pad = decrypted[-1]
            if pad < 1 or pad > 32:
                pad = 0
            content = decrypted[:-pad]
            # 去除随机前缀和网络字节序
            content = content[16:]
            msg_len = int.from_bytes(content[:4], "little")
            msg = content[4:msg_len+4].decode("utf-8")
            from_receive_id = content[msg_len+4:].decode("utf-8")
            if from_receive_id != receive_id:
                logger.warning("receive_id 不匹配")
                return None
            return json.loads(msg) if msg.startswith("{") else msg
        except Exception as e:
            logger.error(f"解密失败: {e}")
            return None

# ==========================================
# 消息处理器
# ==========================================

class WeComMessageHandler:
    """企业微信消息处理器"""
    
    def __init__(self):
        self.sessions = {}  # session_id -> session_data
        self.msgid_history = set()  # 用于排重
    
    def handle_callback(self, callback_data):
        """
        处理企业微信回调
        
        Args:
            callback_data: 回调 JSON 数据
            
        Returns:
            dict: 回复消息内容
        """
        # 1. 基础验证
        msgid = callback_data.get("msgid", "")
        if msgid in self.msgid_history:
            logger.info(f"重复消息 ID: {msgid}")
            return None
        self.msgid_history.add(msgid)
        
        # 保留最近 10000 条记录
        if len(self.msgid_history) > 10000:
            self.msgid_history.clear()
        
        msgtype = callback_data.get("msgtype", "")
        userid = callback_data.get("from", {}).get("userid", "")
        
        logger.info(f"收到消息: type={msgtype}, userid={userid}, msgid={msgid[:16]}...")
        
        # 2. 按消息类型分发
        handler_map = {
            "text": self._handle_text,
            "voice": self._handle_voice,
            "image": self._handle_image,
            "mixed": self._handle_mixed,
            "file": self._handle_file,
            "video": self._handle_video,
        }
        
        handler = handler_map.get(msgtype, self._handle_unknown)
        return handler(callback_data)
    
    def _handle_voice(self, data):
        """处理语音消息"""
        voice_data = data.get("voice", {})
        content = voice_data.get("content", "").strip()
        userid = data.get("from", {}).get("userid", "")
        
        logger.info(f"语音消息内容: {content[:50]}...")
        
        # 空内容检查
        if not content:
            return self._text_response("抱歉，我没有听清您的语音 😅 请重新发送。")
        
        # 意图识别
        intent_result = self._parse_intent(content)
        intent = intent_result["intent"]
        confidence = intent_result.get("confidence", 0)
        entities = intent_result.get("entities", {})
        
        logger.info(f"意图识别: {intent} (置信度: {confidence:.2f})")
        
        # 置信度低时主动确认
        if confidence < 0.3:
            return self._build_help_response()
        
        # 分发到对应处理器
        response_map = {
            "query_schedule": self._handle_query_schedule,
            "create_todo": self._handle_create_todo,
            "query_weather": self._handle_query_weather,
            "send_message": self._handle_send_message,
            "help": self._handle_help,
            "exit_voice": self._handle_exit_voice,
            "custom": self._handle_custom,
        }
        
        handler = response_map.get(intent, self._handle_custom)
        return handler(entities, data)
    
    def _handle_text(self, data):
        """处理文本消息"""
        text = data.get("text", {}).get("content", "").strip()
        
        # 特定命令处理
        if text in ["退出语音模式", "结束", "再见"]:
            return self._text_response("已退出语音模式，欢迎下次使用～如需帮助请对我说「帮助」🙂")
        
        if text in ["帮助", "能做什么", "怎么用"]:
            return self._build_help_response()
        
        # 默认：将文本当作语音转写内容处理
        intent_result = self._parse_intent(text)
        intent = intent_result["intent"]
        if intent != "custom" and intent != "help":
            return intent_result  # 走语音处理流程
        
        return self._text_response("您好！我是企业微信语音助手。请「私聊」我并为我发送语音消息，我会帮您查日程、建待办、问天气。如需帮助请对我说「帮助」。")
    
    def _parse_intent(self, text):
        """统一的意图解析器"""
        if not text:
            return {"intent": "custom", "confidence": 0, "entities": {}}
        
        # 关键词映射表
        intent_keywords = {
            "query_schedule": [
                "日程", "会议", "安排", "行程", "有什么会", "几点开会",
                "日程安排", "会议安排", "什么安排", "下周", "下周有什么"
            ],
            "create_todo": [
                "提醒", "待办", "任务", "别忘了", "记得", "定时提醒",
                "设提醒", "创建待办", "定提醒"
            ],
            "query_weather": [
                "天气", "气温", "下雨", "温度", "穿什么", "热不冷",
                "天气预报", "气温多少"
            ],
            "send_message": [
                "发消息", "告诉", "通知", "转发", "发信息", "发微信"
            ],
            "exit_voice": [
                "退出", "不用了", "谢谢", "结束", "再见", "拜拜", "先这样"
            ],
            "help": [
                "帮助", "能做什么", "怎么用", "功能", "help",
                "你可以做什么", "使用说明"
            ]
        }
        
        max_score = 0
        best_intent = "custom"
        
        for intent, keywords in intent_keywords.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > max_score:
                max_score = score
                best_intent = intent
        
        entities = self._extract_entities(text)
        confidence = min(max_score * 0.3, 1.0)
        
        return {
            "intent": best_intent,
            "confidence": confidence,
            "entities": entities
        }
    
    def _extract_entities(self, text):
        """实体信息提取"""
        import re
        entities = {}
        
        # 时间提取
        time_map = {"今天": 0, "明天": 1, "后天": 2, "大后天": 3}
        for word, offset in time_map.items():
            if word in text:
                from datetime import timedelta
                target = datetime.now() + timedelta(days=offset)
                entities["time"] = word
                entities["date"] = target.strftime("%Y-%m-%d")
                break
        
        # 长相对时间
        if "下周" in text and "下周" not in [k for k in time_map]:
            entities["time"] = "下周"
            entities["date_range"] = "next_week"
        
        # 日期提取 MM月DD日
        date_match = re.search(r'(\d{1,2})月(\d{1,2})日', text)
        if date_match:
            month, day = date_match.groups()
            entities["date"] = f"{datetime.now().year}-{int(month):02d}-{int(day):02d}"
        
        # 人物提取
        people = ["张三", "李四", "王五", "赵六"]
        for p in people:
            if p in text:
                entities["person"] = p
                break
        
        # 地点提取
        cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安"]
        for c in cities:
            if c in text:
                entities["location"] = c
                break
        
        return entities
    
    # ==========================================
    # 各意图处理器
    # ==========================================
    
    def _handle_query_schedule(self, entities, data):
        """处理日程查询"""
        date = entities.get("date", "今天")
        time = entities.get("time", "")
        person = entities.get("person", "")
        
        # 这里可以接入企业微信日程 API
        # 目前返回模拟响应
        parts = []
        if time:
            parts.append(f"{time}")
        if person:
            parts.append(f"{person}参与的")
        
        date_str = f"({date})" if date else ""
        target = "、".join(parts) if parts else ""
        
        # 实际部署时调用 wecom skill 查询
        return self._text_response(
            f"正在为您查询{date_str}的日程安排{'（' + target + '）' if target else ''}...\n\n"
            f"（此功能需要配置企业微信日程 API 接入）\n"
            f"查询完成后将为您展示：\n"
            f"📅 时间 - 事项 - 地点\n\n"
            f"💡 您还可以通过微信联系人获取更多帮助"
        )
    
    def _handle_create_todo(self, entities, data):
        """处理待办创建"""
        date = entities.get("date", "今天")
        
        return self._text_response(
            f"好的，我来为您创建待办提醒...\n\n"
            f"（此功能需要配置企业微信待办 API 接入）\n"
            f"请告诉我：\n"
            f"1️⃣ 提醒什么内容？\n"
            f"2️⃣ 什么时候提醒？\n\n"
            f"例如：\"提醒我明天下午3点提交报告\""
        )
    
    def _handle_query_weather(self, entities, data):
        """处理天气查询"""
        location = entities.get("location", "当地")
        date = entities.get("date", "今天")
        
        return self._text_response(
            f"正在查询{location}的天气信息...\n\n"
            f"（此功能需要配置天气查询 API 接入）\n\n"
            f"查询完成后将为您展示：\n"
            f"🌤️ 天气状况\n"
            f"🌡️ 温度范围\n"
            f"💡 穿衣建议\n"
            f"🌬️ 风力风向"
        )
    
    def _handle_send_message(self, entities, data):
        """处理消息发送"""
        person = entities.get("person", "")
        
        if not person:
            return self._text_response(
                "（此功能需要配置企业微信消息 API 接入）\n\n"
                "请确认：\n"
                f"1️⃣ 发给谁？（请说姓名）\n"
                f"2️⃣ 发什么内容？"
            )
        
        return self._text_response(
            f"好的，我来帮您给{person}发消息...\n\n"
            f"（此功能需要配置企业微信消息 API 接入）\n"
            f"请告诉我具体要发送的内容。"
        )
    
    def _handle_help(self, entities=None, data=None):
        """处理帮助请求"""
        return self._build_help_response()
    
    def _handle_exit_voice(self, entities, data):
        """退出语音模式"""
        return self._text_response("好的，语音模式已退出。如需帮助，随时可以再次召唤我～🌟")
    
    def _handle_custom(self, entities, data):
        """无法识别的意图"""
        return self._text_response(
            "抱歉，我没有完全理解您的意思 😅\n\n"
            "你可以试试这样对我说：\n"
            "🗣️ \"明天有什么会议？\"（查日程）\n"
            "🗣️ \"提醒我下午3点开会\"（建待办）\n"
            "🗣️ \"北京今天天气怎么样？\"（问天气）\n"
            "🗣️ \"帮助\"（获取完整指令清单）"
        )
    
    # ==========================================
    # 其他消息类型处理器
    # ==========================================
    
    def _handle_image(self, data):
        return self._text_response("收到图片消息 📷（暂不支持图片识别，请用语音或文字告诉我您的需求）")
    
    def _handle_mixed(self, data):
        return self._text_response("收到混合消息 📎（请发送语音或文字消息获取最佳体验）")
    
    def _handle_file(self, data):
        return self._text_response("收到文件 📎（暂不支持文件处理，请用语音或文字告诉我您的需求）")
    
    def _handle_video(self, data):
        return self._text_response("收到视频消息 🎬（暂不支持视频处理，请用语音或文字告诉我您的需求）")
    
    def _handle_unknown(self, data):
        return self._text_response("抱歉，暂不支持此类消息格式 😅 请发送语音或文字消息。")
    
    # ==========================================
    # 响应构建器
    # ==========================================
    
    def _text_response(self, content):
        """构建文本回复"""
        return {"msgtype": "text", "text": {"content": content}}
    
    def _build_help_response(self):
        """构建帮助信息"""
        return self._text_response(
            "📋 我可以帮您：\n\n"
            "🗣️ 语音查日程：\"明天有什么会议？\"\n"
            "🗣️ 语音建待办：\"提醒我下午3点提交报告\"\n"
            "🗣️ 语音问天气：\"北京今天天气怎么样？\"\n"
            "🗣️ 语音发消息：\"发消息给张三，明天开会\"\n\n"
            "⚠️ 注意事项：\n"
            "• 请在安静环境使用普通话发送语音\n"
            "• 语音时长建议控制在 60 秒内\n"
            "• 仅支持私聊，群聊暂不支持\n\n"
            "如需退出语音模式，请说「退出」或「谢谢」"
        )


# ==========================================
# HTTP 服务器
# ==========================================

class WeComWebhookHandler(http.server.BaseHTTPRequestHandler):
    """企业微信回调 HTTP 处理器"""
    
    # 共享的消息处理器
    handler = WeComMessageHandler()
    
    def do_GET(self):
        """处理 GET 请求（URL 验证）"""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        # 健康检查
        if parsed.path == "/health":
            self._json_response(200, {"status": "ok", "time": int(time.time())})
            return
        
        # 企业微信 URL 验证
        msg_signature = params.get("msg_signature", [None])[0]
        timestamp = params.get("timestamp", [None])[0]
        nonce = params.get("nonce", [None])[0]
        echostr = params.get("echostr", [None])[0]
        
        if all([msg_signature, timestamp, nonce, echostr]):
            # TODO: 验证签名（需要配置 Token/EncodingAESKey）
            # 暂时直接返回 echostr（实际部署时请实现签名验证）
            self._json_response(200, {"echostr": echostr})
            logger.info("URL 验证请求已处理")
        else:
            self._json_response(400, {"error": "missing parameters"})
    
    def do_POST(self):
        """处理 POST 请求（消息回调）"""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        try:
            callback_data = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self._json_response(400, {"error": "invalid json"})
            return
        
        # 处理回调
        response = self.handler.handle_callback(callback_data)
        
        if response:
            self._json_response(200, response)
        else:
            # 无回复时返回空成功（避免企业微信认为失败）
            self._json_response(200, {"errcode": 0})
    
    def _json_response(self, status_code, data):
        """返回 JSON 响应"""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    
    def log_message(self, format, *args):
        """自定义日志（替换默认的 stderr 输出）"""
        logger.info(f"HTTP_LOG: {args[0]}")


# ==========================================
# 启动服务器
# ==========================================

def start_server(host=SERVER_HOST, port=SERVER_PORT):
    """启动回调服务器"""
    server = http.server.HTTPServer((host, port), WeComWebhookHandler)
    logger.info("=" * 60)
    logger.info(f"企业微信语音消息回调服务器已启动")
    logger.info(f"监听地址: http://{host}:{port}")
    logger.info("")
    logger.info("1. 确保你的电脑有公网 IP 或使用内网穿透（ngrok/frp）")
    logger.info("2. 将回调 URL 填入企业微信管理后台")
    logger.info("3. 发送语音消息测试")
    logger.info("")
    logger.info("按 Ctrl+C 停止")
    logger.info("=" * 60)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("\n服务器已停止")
        server.server_close()


if __name__ == "__main__":
    port = SERVER_PORT
    if len(sys.argv) >= 3 and sys.argv[1] == "--port":
        port = int(sys.argv[2])
    start_server(port=port)
