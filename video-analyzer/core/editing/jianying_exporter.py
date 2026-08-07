"""剪映 draft.json 导出器 — 直接导入剪映专业版"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..logger import get_logger

logger = get_logger(__name__)


class JianyingExporter:
    """
    剪映 draft.json 格式导出器。
    
    剪映专业版支持导入 draft.json 格式的草稿文件。
    本模块将视频分析结果转换为剪映可直接打开的格式。
    
    draft.json 结构：
    - version: 剪映版本号
    - tracks: 轨道列表（视频/音频/文字）
    - materials: 素材信息
    - segments: 片段信息（含时间码）
    - texts: 字幕文本
    - effects: 转场/特效
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.editing_config = config.get("editing", {})
        self.jianying_config = self.editing_config.get("jianying", {})
        self.fps = self.jianying_config.get("fps", 30)
        self.resolution = self.jianying_config.get("resolution", {"width": 1920, "height": 1080})
    
    def export(
        self,
        timeline: Dict,
        transcript: Dict = None,
        video_path: str = None,
        output_path: str = "draft.json",
    ) -> Optional[str]:
        """
        导出剪映 draft.json 文件。
        
        Args:
            timeline: 剪辑时间线
            transcript: 语音识别结果（用于字幕）
            video_path: 原始视频路径
            output_path: 输出文件路径
            
        Returns:
            输出文件路径，失败返回 None
        """
        try:
            draft = self._build_draft(timeline, transcript, video_path)
            
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(draft, f, ensure_ascii=False, indent=2)
            
            logger.info(f"剪映 draft.json 已导出: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"剪映导出失败: {e}")
            return None
    
    def _build_draft(
        self,
        timeline: Dict,
        transcript: Dict = None,
        video_path: str = None,
    ) -> Dict:
        """构建完整的 draft.json 结构"""
        
        # 基础信息
        draft = {
            "version": "8.0.0",
            "type": "draft",
            "created_at": datetime.now().isoformat(),
            "title": "video-analyzer 导出",
        }
        
        # 素材信息
        draft["materials"] = self._build_materials(video_path, transcript)
        
        # 轨道信息
        draft["tracks"] = self._build_tracks(timeline, video_path, transcript)
        
        # 片段信息
        draft["segments"] = self._build_segments(timeline, video_path)
        
        # 字幕文本
        if transcript:
            draft["texts"] = self._build_texts(transcript)
        
        # 特效/转场
        draft["effects"] = self._build_effects(timeline)
        
        return draft
    
    def _build_materials(
        self,
        video_path: str = None,
        transcript: Dict = None,
    ) -> Dict:
        """构建素材信息"""
        materials = {
            "videos": [],
            "audios": [],
            "texts": [],
            "effects": [],
        }
        
        if video_path:
            materials["videos"].append({
                "id": "video_001",
                "path": video_path,
                "name": os.path.basename(video_path),
                "duration": 0,  # 剪映会自动识别
                "width": self.resolution["width"],
                "height": self.resolution["height"],
                "fps": self.fps,
            })
        
        return materials
    
    def _build_tracks(
        self,
        timeline: Dict,
        video_path: str = None,
        transcript: Dict = None,
    ) -> List[Dict]:
        """构建轨道列表"""
        tracks = []
        
        # 视频轨道
        if video_path:
            tracks.append({
                "id": "track_video_001",
                "type": "video",
                "name": "视频轨道 1",
                "flag": 1,  # 主轨道
                "segments": self._build_video_segments(timeline),
            })
        
        # 音频轨道
        if video_path:
            tracks.append({
                "id": "track_audio_001",
                "type": "audio",
                "name": "音频轨道 1",
                "flag": 1,
                "segments": self._build_audio_segments(timeline),
            })
        
        # 字幕轨道
        if transcript:
            tracks.append({
                "id": "track_text_001",
                "type": "text",
                "name": "字幕轨道 1",
                "flag": 0,
                "segments": self._build_text_segments(transcript),
            })
        
        return tracks
    
    def _build_video_segments(self, timeline: Dict) -> List[Dict]:
        """构建视频片段"""
        segments = []
        clips = timeline.get("clips", [])
        
        for i, clip in enumerate(clips):
            segments.append({
                "id": f"seg_video_{i:03d}",
                "material_id": "video_001",
                "source_time": [int(clip.get("source_start", 0) * 1000), int(clip.get("source_end", 0) * 1000)],
                "target_time": [int(clip.get("output_start", 0) * 1000), int(clip.get("output_end", 0) * 1000)],
                "speed": 1.0,
            })
        
        return segments
    
    def _build_audio_segments(self, timeline: Dict) -> List[Dict]:
        """构建音频片段"""
        segments = []
        clips = timeline.get("clips", [])
        
        for i, clip in enumerate(clips):
            segments.append({
                "id": f"seg_audio_{i:03d}",
                "material_id": "video_001",
                "source_time": [int(clip.get("source_start", 0) * 1000), int(clip.get("source_end", 0) * 1000)],
                "target_time": [int(clip.get("output_start", 0) * 1000), int(clip.get("output_end", 0) * 1000)],
                "speed": 1.0,
            })
        
        return segments
    
    def _build_text_segments(self, transcript: Dict) -> List[Dict]:
        """构建字幕片段"""
        segments = []
        segs = transcript.get("segments", [])
        
        for i, seg in enumerate(segs):
            start_ms = int(seg.get("start", 0) * 1000)
            end_ms = int(seg.get("end", 0) * 1000)
            text = seg.get("text", "").strip()
            
            if text:
                segments.append({
                    "id": f"seg_text_{i:03d}",
                    "text": text,
                    "start": start_ms,
                    "duration": end_ms - start_ms,
                    "style": self._get_text_style(),
                })
        
        return segments
    
    def _build_segments(self, timeline: Dict, video_path: str = None) -> List[Dict]:
        """构建片段列表"""
        segments = []
        clips = timeline.get("clips", [])
        
        for i, clip in enumerate(clips):
            segments.append({
                "id": f"segment_{i:03d}",
                "track_id": "track_video_001",
                "material_id": "video_001" if video_path else None,
                "source_range": [int(clip.get("source_start", 0) * 1000), int(clip.get("source_end", 0) * 1000)],
                "target_range": [int(clip.get("output_start", 0) * 1000), int(clip.get("output_end", 0) * 1000)],
            })
        
        return segments
    
    def _build_texts(self, transcript: Dict) -> List[Dict]:
        """构建文本列表"""
        texts = []
        segs = transcript.get("segments", [])
        
        for i, seg in enumerate(segs):
            text = seg.get("text", "").strip()
            if text:
                texts.append({
                    "id": f"text_{i:03d}",
                    "content": text,
                    "start": int(seg.get("start", 0) * 1000),
                    "duration": int((seg.get("end", 0) - seg.get("start", 0)) * 1000),
                })
        
        return texts
    
    def _build_effects(self, timeline: Dict) -> List[Dict]:
        """构建转场/特效列表"""
        effects = []
        clips = timeline.get("clips", [])
        
        for i in range(len(clips) - 1):
            # 在每个片段之间添加淡入淡出转场
            effects.append({
                "id": f"effect_{i:03d}",
                "type": "transition",
                "name": "淡入淡出",
                "duration": 500,  # 500ms
                "target_segment": f"segment_{i:03d}",
                "next_segment": f"segment_{i+1:03d}",
            })
        
        return effects
    
    def _get_text_style(self) -> Dict:
        """获取默认字幕样式"""
        return {
            "font": "Microsoft YaHei",
            "size": 48,
            "color": "#FFFFFF",
            "background": "#000000",
            "background_alpha": 0.5,
            "position": "bottom_center",
            "alignment": "center",
        }
