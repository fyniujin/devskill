"""字幕样式生成器"""

from typing import Any, Dict, List, Optional

from ..logger import get_logger

logger = get_logger(__name__)


class SubtitleStylist:
    """
    生成字幕样式文件。
    
    支持格式：
    - SRT (基础字幕)
    - ASS/SSA (高级样式字幕，支持字体/颜色/位置)
    - VTT (WebVTT，用于网页)
    
    样式模板：
    - 抖音风格（白字黑边，底部居中）
    - B站风格（彩色弹幕风）
    - 电影风格（底部大字）
    - 简洁风格（无边框）
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.editing_config = config.get("editing", {})
        self.subtitle_config = self.editing_config.get("subtitle", {})
        
        self.default_style = self.subtitle_config.get("default_style", "douyin")
        self.font_size = self.subtitle_config.get("font_size", 48)
        self.font_name = self.subtitle_config.get("font_name", "Microsoft YaHei")
    
    def generate(
        self,
        transcript: Dict,
        output_path: str,
        style: str = None,
        format: str = "ass",
    ) -> Optional[str]:
        """
        生成字幕文件。
        
        Args:
            transcript: 语音识别结果
            output_path: 输出文件路径
            style: 样式模板 (douyin/bilibili/movie/minimal)
            format: 输出格式 (srt/ass/vtt)
            
        Returns:
            输出文件路径
        """
        style = style or self.default_style
        
        try:
            if format == "srt":
                return self._generate_srt(transcript, output_path)
            elif format == "ass":
                return self._generate_ass(transcript, output_path, style)
            elif format == "vtt":
                return self._generate_vtt(transcript, output_path)
            else:
                logger.error(f"不支持的字幕格式: {format}")
                return None
                
        except Exception as e:
            logger.error(f"字幕生成失败: {e}")
            return None
    
    def _generate_srt(self, transcript: Dict, output_path: str) -> str:
        """生成 SRT 格式"""
        segments = transcript.get("segments", [])
        
        lines = []
        for i, seg in enumerate(segments):
            start = self._format_srt_time(seg.get("start", 0))
            end = self._format_srt_time(seg.get("end", 0))
            text = seg.get("text", "").strip()
            
            if text:
                lines.append(str(i + 1))
                lines.append(f"{start} --> {end}")
                lines.append(text)
                lines.append("")
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        return output_path
    
    def _generate_ass(
        self, transcript: Dict, output_path: str, style: str
    ) -> str:
        """生成 ASS 格式（带样式）"""
        style_templates = self._get_style_templates()
        style_def = style_templates.get(style, style_templates["douyin"])
        
        lines = [
            "[Script Info]",
            "Title: Video Analyzer Subtitles",
            "ScriptType: v4.00+",
            "PlayResX: 1920",
            "PlayResY: 1080",
            "ScaledBorderAndShadow: yes",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        ]
        
        # 添加样式定义
        for name, style_info in style_def.items():
            lines.append(
                f"Style: {name},{style_info['font']},{style_info['size']},"
                f"{style_info['primary']},{style_info['secondary']},"
                f"{style_info['outline']},{style_info['back']},"
                f"{style_info['bold']},{style_info['italic']},"
                f"0,0,100,100,0,0,{style_info['border_style']},"
                f"{style_info['outline_width']},{style_info['shadow']},"
                f"{style_info['alignment']},100,100,50,1"
            )
        
        lines.extend([
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        ])
        
        # 添加字幕事件
        segments = transcript.get("segments", [])
        for seg in segments:
            start = self._format_ass_time(seg.get("start", 0))
            end = self._format_ass_time(seg.get("end", 0))
            text = seg.get("text", "").strip()
            
            if text:
                # 处理换行
                text = text.replace("\\N", "\\N")
                lines.append(
                    f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}"
                )
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        return output_path
    
    def _generate_vtt(self, transcript: Dict, output_path: str) -> str:
        """生成 WebVTT 格式"""
        lines = ["WEBVTT", ""]
        
        segments = transcript.get("segments", [])
        for seg in segments:
            start = self._format_vtt_time(seg.get("start", 0))
            end = self._format_vtt_time(seg.get("end", 0))
            text = seg.get("text", "").strip()
            
            if text:
                lines.append(f"{start} --> {end}")
                lines.append(text)
                lines.append("")
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        return output_path
    
    def _get_style_templates(self) -> Dict:
        """获取样式模板"""
        return {
            "douyin": {
                "Default": {
                    "font": "Microsoft YaHei",
                    "size": 48,
                    "primary": "&H00FFFFFF",  # 白色
                    "secondary": "&H000000FF",
                    "outline": "&H00000000",  # 黑色描边
                    "back": "&H80000000",
                    "bold": -1,
                    "italic": 0,
                    "border_style": 1,
                    "outline_width": 3,
                    "shadow": 0,
                    "alignment": 2,  # 底部居中
                }
            },
            "bilibili": {
                "Default": {
                    "font": "Microsoft YaHei",
                    "size": 52,
                    "primary": "&H00FFFFFF",
                    "secondary": "&H000000FF",
                    "outline": "&H00FF00FF",  # 粉色描边
                    "back": "&H80000000",
                    "bold": -1,
                    "italic": 0,
                    "border_style": 1,
                    "outline_width": 2,
                    "shadow": 1,
                    "alignment": 2,
                }
            },
            "movie": {
                "Default": {
                    "font": "Microsoft YaHei",
                    "size": 56,
                    "primary": "&H00FFFFFF",
                    "secondary": "&H000000FF",
                    "outline": "&H00000000",
                    "back": "&H00000000",
                    "bold": 0,
                    "italic": 0,
                    "border_style": 1,
                    "outline_width": 2,
                    "shadow": 2,
                    "alignment": 2,
                }
            },
            "minimal": {
                "Default": {
                    "font": "Microsoft YaHei",
                    "size": 44,
                    "primary": "&H00FFFFFF",
                    "secondary": "&H000000FF",
                    "outline": "&H00000000",
                    "back": "&H00000000",
                    "bold": 0,
                    "italic": 0,
                    "border_style": 0,
                    "outline_width": 0,
                    "shadow": 0,
                    "alignment": 2,
                }
            },
        }
    
    def _format_srt_time(self, seconds: float) -> str:
        """格式化 SRT 时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _format_ass_time(self, seconds: float) -> str:
        """格式化 ASS 时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centis = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"
    
    def _format_vtt_time(self, seconds: float) -> str:
        """格式化 VTT 时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
