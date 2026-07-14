"""报告生成模块 — HTML交互报告 + JSON + Markdown 剧本"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from .logger import get_logger

logger = get_logger(__name__)


class ReportGenerator:
    """多格式报告生成器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.report_config = config.get("report", {})
        self.theme = self.report_config.get("theme", "dark")
    
    def generate(
        self,
        transcript: Dict,
        scenes: Dict,
        visual_data: Dict,
        aligned_data: Dict,
        fused_data: Dict,
        highlights,  # 接受 dict (HighlightExtractor 输出) 或 None
        media_info: Dict,
        output_dir: str,
    ) -> Dict[str, str]:
        """
        生成所有格式的报告文件。
        
        Returns:
            格式 -> 文件路径 映射
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # 创建子目录
        assets_dir = os.path.join(output_dir, "assets")
        scenes_dir = os.path.join(output_dir, "scenes")
        os.makedirs(assets_dir, exist_ok=True)
        os.makedirs(scenes_dir, exist_ok=True)
        
        # 复制场景关键帧到 scenes 目录
        self._copy_keyframes(scenes.get("scenes", []), scenes_dir)
        
        output_paths = {}
        
        formats = self.report_config.get("formats", ["html", "json", "md"])
        
        if "html" in formats:
            html_path = self._generate_html(
                transcript, scenes, visual_data, aligned_data,
                fused_data, highlights, media_info, output_dir, assets_dir
            )
            output_paths["html"] = html_path
        
        if "json" in formats:
            json_path = self._generate_json(
                transcript, scenes, visual_data, aligned_data,
                fused_data, highlights, media_info, output_dir
            )
            output_paths["json"] = json_path
        
        if "md" in formats:
            md_path = self._generate_markdown(
                transcript, scenes, visual_data, aligned_data,
                fused_data, highlights, media_info, output_dir
            )
            output_paths["md"] = md_path
        
        return output_paths
    
    def _generate_html(
        self,
        transcript: Dict,
        scenes: Dict,
        visual_data: Dict,
        aligned_data: Dict,
        fused_data: Dict,
        highlights: List[Dict],
        media_info: Dict,
        output_dir: str,
        assets_dir: str,
    ) -> str:
        """生成交互式 HTML 报告"""
        
        html_content = self._build_html_document(
            transcript, scenes, fused_data, highlights, media_info, aligned_data
        )
        
        output_path = os.path.join(output_dir, "report.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        logger.info(f"HTML 报告已生成: {output_path}")
        return output_path
    
    def _build_html_document(
        self,
        transcript: Dict,
        scenes: Dict,
        fused_data: Dict,
        highlights: List[Dict],
        media_info: Dict,
        aligned_data: Dict,
    ) -> str:
        """构建完整 HTML 文档"""
        
        summary = fused_data.get("summary", {})
        metrics = fused_data.get("metrics", {})
        enriched_scenes = fused_data.get("scenes", [])
        
        # 主题色
        if self.theme == "dark":
            bg_color = "#1a1a2e"
            card_bg = "#16213e"
            text_color = "#e0e0e0"
            accent_color = "#0f3460"
            highlight_color = "#e94560"
            muted_color = "#888"
        else:
            bg_color = "#f5f5f5"
            card_bg = "#ffffff"
            text_color = "#333333"
            accent_color = "#e0e0e0"
            highlight_color = "#d32f2f"
            muted_color = "#666"
        
        # 构建场景时间轴 HTML
        timeline_html = self._build_timeline_html(enriched_scenes, media_info)
        
        # 构建对话剧本 HTML
        script_html = self._build_script_html(transcript.get("segments", []))
        
        # 构建光谱数据 HTML
        metrics_html = self._build_metrics_html(metrics, media_info)
        
        # 构建精华片段 HTML
        highlights_html = self._build_highlights_html(highlights)
        
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>视频分析报告 — video-analyzer</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: {bg_color};
            color: {text_color};
            line-height: 1.6;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{
            text-align: center;
            padding: 30px 0;
            border-bottom: 1px solid {accent_color};
            margin-bottom: 30px;
        }}
        .header h1 {{ font-size: 24px; margin-bottom: 8px; }}
        .header .subtitle {{ color: {muted_color}; font-size: 14px; }}
        .card {{
            background: {card_bg};
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .card h2 {{
            font-size: 18px;
            margin-bottom: 16px;
            color: {highlight_color};
        }}
        .card h3 {{
            font-size: 14px;
            color: {muted_color};
            margin: 12px 0 8px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
        }}
        .metric-item {{
            text-align: center;
            padding: 16px;
            background: {accent_color}22;
            border-radius: 8px;
        }}
        .metric-value {{ font-size: 24px; font-weight: 600; color: {highlight_color}; }}
        .metric-label {{ font-size: 12px; color: {muted_color}; margin-top: 4px; }}
        .timeline {{ position: relative; padding: 20px 0; }}
        .scene-block {{
            display: flex;
            align-items: center;
            padding: 12px 16px;
            margin: 8px 0;
            background: {accent_color}33;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.2s;
        }}
        .scene-block:hover {{ background: {accent_color}66; }}
        .scene-time {{ min-width: 100px; color: {highlight_color}; font-size: 13px; }}
        .scene-title {{ flex: 1; font-weight: 500; }}
        .scene-tags {{ display: flex; gap: 6px; }}
        .tag {{
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            background: {accent_color}44;
        }}
        .script-line {{
            padding: 8px 12px;
            border-left: 3px solid {accent_color};
            margin: 4px 0;
            font-size: 13px;
        }}
        .script-time {{ color: {highlight_color}; margin-right: 12px; }}
        .highlight-item {{
            padding: 12px;
            margin: 8px 0;
            background: {highlight_color}11;
            border: 1px solid {highlight_color}33;
            border-radius: 8px;
        }}
        .highlight-score {{
            float: right;
            background: {highlight_color}22;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
        }}
        .summary-text {{ font-size: 14px; color: {text_color}; padding: 12px; }}
        .search-box {{
            width: 100%;
            padding: 10px 16px;
            border: 1px solid {accent_color};
            border-radius: 8px;
            background: {card_bg};
            color: {text_color};
            font-size: 14px;
            margin-bottom: 16px;
        }}
        .filter-buttons {{ margin-bottom: 16px; }}
        .filter-btn {{
            padding: 6px 16px;
            margin: 0 4px 4px 0;
            border: 1px solid {accent_color};
            border-radius: 6px;
            background: transparent;
            color: {text_color};
            cursor: pointer;
            font-size: 12px;
        }}
        .filter-btn.active, .filter-btn:hover {{
            background: {highlight_color};
            color: white;
            border-color: {highlight_color};
        }}
        .footer {{
            text-align: center;
            padding: 30px;
            color: {muted_color};
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>视频分析报告</h1>
            <div class="subtitle">由 video-analyzer v3.0.0 生成 · {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
        </div>

        <div class="card">
            <h2>摘要</h2>
            <div class="summary-text">{summary.get("text", "无摘要")}</div>
            <h3>整体指标</h3>
            {metrics_html}
        </div>

        <div class="card">
            <h2>时间轴场景</h2>
            <div class="timeline">
                {timeline_html}
            </div>
        </div>

        <div class="card">
            <h2>完整剧本</h2>
            <input type="text" class="search-box" placeholder="搜索对话内容..." onkeyup="searchScript(this.value)">
            <div id="script-content">
                {script_html}
            </div>
        </div>

        {highlights_html}

        <div class="footer">
            video-analyzer · 视频分析处理 Skill<br>
            仅供参考，识别结果以原始视频为准
        </div>
    </div>

    <script>
        // 搜索过滤
        function searchScript(query) {{
            const lines = document.querySelectorAll('.script-line');
            const q = query.toLowerCase();
            lines.forEach(line => {{
                const text = line.textContent.toLowerCase();
                line.style.display = text.includes(q) ? 'block' : 'none';
            }});
        }}

        // 场景跳转（简化版，实际可定位到视频时间）
        document.querySelectorAll('.scene-block').forEach(block => {{
            block.addEventListener('click', function() {{
                const time = this.dataset.time;
                console.log('跳转到时间:', time);
                // 可扩展：通过 URL hash 或 postMessage 控制播放器
            }});
        }});
    </script>
</body>
</html>"""
    
    def _build_timeline_html(self, scenes: List[Dict], media_info: Dict) -> str:
        """构建时间轴场景 HTML"""
        total_duration = media_info.get("duration", 1)
        
        html_parts = []
        for scene in scenes:
            time_range = scene.get("time_range", {})
            start = time_range.get("start", 0)
            duration = time_range.get("duration", 0)
            progress = round((duration / total_duration) * 100, 1)
            
            tags_html = " ".join(
                f'<span class="tag">{tag}</span>'
                for tag in scene.get("semantic_tags", [])[:3]
            )
            
            html_parts.append(f"""
            <div class="scene-block" data-time="{start}">
                <div class="scene-time">{self._format_time(start)} - {self._format_time(start + duration)}</div>
                <div class="scene-title">场景 {scene.get("index", "?")} ({progress}%)</div>
                <div class="scene-tags">{tags_html}</div>
            </div>
            """)
        
        return "\n".join(html_parts)
    
    def _build_script_html(self, segments: List[Dict]) -> str:
        """构建对话剧本 HTML"""
        html_parts = []
        for seg in segments:
            start = seg.get("start", 0)
            text = seg.get("text", "")
            html_parts.append(f"""
            <div class="script-line">
                <span class="script-time">{self._format_time(start)}</span>
                {text}
            </div>
            """)
        return "\n".join(html_parts)
    
    def _build_metrics_html(self, metrics: Dict, media_info: Dict) -> str:
        """构建指标面板 HTML"""
        return f"""
        <div class="metrics-grid">
            <div class="metric-item">
                <div class="metric-value">{self._format_time(metrics.get("total_duration", 0) or 0)}</div>
                <div class="metric-label">总时长</div>
            </div>
            <div class="metric-item">
                <div class="metric-value">{metrics.get("total_scenes", 0)}</div>
                <div class="metric-label">场景数</div>
            </div>
            <div class="metric-item">
                <div class="metric-value">{int(metrics.get("dialog_coverage", 0) * 100)}%</div>
                <div class="metric-label">对话覆盖率</div>
            </div>
            <div class="metric-item">
                <div class="metric-value">{metrics.get("scene_switch_rate", 0)}</div>
                <div class="metric-label">场景切换/分钟</div>
            </div>
            <div class="metric-item">
                <div class="metric-value">{int(metrics.get("avg_confidence", 0) * 100)}%</div>
                <div class="metric-label">平均置信度</div>
            </div>
            <div class="metric-item">
                <div class="metric-value">{metrics.get("silent_scene_count", 0)}</div>
                <div class="metric-label">无声场景</div>
            </div>
        </div>
        """
    
    def _build_highlights_html(self, highlights) -> str:
        """构建精华片段 HTML"""
        # 兼容 dict 和 list 两种格式
        if isinstance(highlights, dict):
            highlights_list = highlights.get("highlights", [])
        elif isinstance(highlights, list):
            highlights_list = highlights
        else:
            highlights_list = []
        
        if not highlights_list:
            return ""
        
        items_html = []
        for h in highlights_list:
            tags = " ".join(f'<span class="tag">{t}</span>' for t in h.get("tags", [])[:3])
            items_html.append(f"""
            <div class="highlight-item">
                <span class="highlight-score">⭐ {h.get("score", 0)}</span>
                <strong>场景 {h.get("scene_index", "?")}</strong>
                {self._format_time(h.get("start_time", 0))} - {self._format_time(h.get("end_time", 0))}
                <div style="margin-top:8px; color:#888; font-size:12px;">{h.get("text_preview", "")[:100]}</div>
                <div style="margin-top:4px;">{tags}</div>
            </div>
            """)
        
        return f"""
        <div class="card">
            <h2>精华片段</h2>
            {"".join(items_html)}
        </div>
        """
    
    def _generate_json(self, *args, **kwargs) -> str:
        """生成 JSON 结构化数据"""
        import json
        transcript, scenes, visual_data, aligned_data, fused_data, highlights, media_info, output_dir = args
        
        data = {
            "meta": {
                "generator": "video-analyzer",
                "version": "3.0.0",
                "generated_at": datetime.now().isoformat(),
            },
            "media_info": media_info,
            "transcript": transcript,
            "scenes": scenes,
            "visual_data": visual_data,
            "alignment": aligned_data,
            "fusion": fused_data,
            "highlights": highlights,
        }
        
        output_path = os.path.join(output_dir, "data.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"JSON 数据已保存: {output_path}")
        return output_path
    
    def _generate_markdown(self, *args, **kwargs) -> str:
        """生成 Markdown 剧本"""
        transcript, scenes, visual_data, aligned_data, fused_data, highlights, media_info, output_dir = args
        
        md = self._build_markdown_content(
            transcript, scenes, fused_data, highlights, media_info
        )
        
        output_path = os.path.join(output_dir, "script.md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md)
        
        logger.info(f"Markdown 剧本已保存: {output_path}")
        return output_path
    
    def _build_markdown_content(
        self,
        transcript: Dict,
        scenes: Dict,
        fused_data: Dict,
        highlights: List[Dict],
        media_info: Dict,
    ) -> str:
        """构建 Markdown 内容"""
        duration = media_info.get("duration", 0)
        summary = fused_data.get("summary", {})
        metrics = fused_data.get("metrics", {})
        
        lines = [
            "# 视频解析报告",
            "",
            f"**生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"**视频时长:** {self._format_time(duration)}",
            f"**分辨率:** {media_info.get('width', '?')}x{media_info.get('height', '?')}",
            "",
            "## 摘要",
            "",
            summary.get("text", "无"),
            "",
            "## 场景分析",
            "",
            f"| 场景 | 时间段 | 时长 | 对话覆盖率 | 标签 |",
            f"|------|--------|------|------------|------|",
        ]
        
        for scene in fused_data.get("scenes", []):
            tr = scene.get("time_range", {})
            tags = ", ".join(scene.get("semantic_tags", [])[:3])
            lines.append(
                f"| 场景 {scene.get('index')} "
                f"| {self._format_time(tr.get('start', 0))} - {self._format_time(tr.get('end', 0))} "
                f"| {tr.get('duration', 0):.1f}s "
                f"| {int(scene.get('metrics', {}).get('dialog_coverage', 0) * 100)}% "
                f"| {tags} |"
            )
        
        lines.extend([
            "",
            "## 完整剧本（语音转文字）",
            "",
        ])
        
        for seg in transcript.get("segments", []):
            start = seg.get("start", 0)
            text = seg.get("text", "")
            lines.append(f"[{self._format_time(start)}] {text}")
        
        if highlights:
            lines.extend([
                "",
                "## 精华片段",
                "",
            ])
            for h in highlights:
                lines.append(
                    f"- **{self._format_time(h.get('start_time', 0))}** "
                    f"(评分: {h.get('score', 0)}) — "
                    f"{h.get('text_preview', '')[:60]}"
                )
        
        return "\n".join(lines)
    
    def _copy_keyframes(self, scenes: List[Dict], dest_dir: str):
        """复制关键帧场景缩略图"""
        for i, scene in enumerate(scenes):
            keyframe = scene.get("keyframe_path") or scene.get("keyframe_index", 0)
            if isinstance(keyframe, str) and os.path.exists(keyframe):
                shutil.copy2(keyframe, os.path.join(dest_dir, f"scene_{i+1:03d}.jpg"))
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """格式化时间为 mm:ss 格式"""
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m:02d}:{s:02d}"
