#!/usr/bin/env python3
"""
video-analyzer 主入口
视频分析处理 Skill — 将视频反编译为结构化分析报告

用法:
    python main.py -i <视频路径或URL> [-o 输出目录] [--model 模型名] [--lang 语言]
"""

import argparse
import os
import sys
import time
from pathlib import Path

# 确保 core 模块可被导入
sys.path.insert(0, str(Path(__file__).parent))

from core.input_handler import InputHandler
from core.media_processor import MediaProcessor
from core.asr import ASRRouter
from core.ocr import PaddleOCREngine
from core.nlp import ChineseNLPEnhancement
from core.scene_detector import SceneDetector
from core.visual_analyzer import VisualAnalyzer
from core.alignment_engine import AlignmentEngine
from core.semantic_fusion import SemanticFusion
from core.highlight_extractor import HighlightExtractor
from core.report_generator import ReportGenerator
from core.config import load_config
from core.logger import get_logger
from core.hardware_probe import HardwareProbe, ResourceMonitor
from core.chapter_slicer import ChapterSlicer
from core.speaker_diarization import SpeakerDiarization
from core.timestamped_summary import TimestampedSummary
from core.update_notifier import UpdateNotifier
from core.platform_adapters import PlatformRouter
from core.editing import HighlightDetector, RedundancyDetector, TimelineGenerator, EDLExporter, SubtitleStylist, JianyingExporter
from core.speaker_diarization.quality_scorer import QualityScorer
from core.scene_manager import SceneManager
from core.viral_predictor import ViralPredictor
from core.live_analyzer import LiveAnalyzer
from core.media_probe import MediaProbe
from core.queue_manager import QueueManager
from core.gpu_accelerator import GPUAccelerator

logger = get_logger(__name__)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="video-analyzer: 视频分析处理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py -i video.mp4
  python main.py -i video.mp4 -o ./report --model medium --lang zh
  python main.py -i "https://example.com/video.mp4" --no-visual
        """
    )
    
    parser.add_argument("-i", "--input", required=True,
                        help="视频文件路径或 HTTP URL")
    parser.add_argument("-o", "--output", default="./output",
                        help="输出目录 (默认: ./output)")
    parser.add_argument("--format", default="html,json,md",
                        help="报告格式，逗号分隔 (默认: html,json,md)")
    parser.add_argument("-m", "--model", default=None,
                        choices=["tiny", "base", "small", "medium", "large-v3"],
                        help="Whisper 模型大小 (默认: 自动根据硬件选择)")
    parser.add_argument("-l", "--lang", default=None,
                        help="语言代码: auto/zh/en/ja 等 (默认: 自动检测)")
    parser.add_argument("--asr-engine", default=None,
                        choices=["whisper", "paraformer", "sensevoice", "auto"],
                        help="ASR 语音识别引擎 (默认: 从配置读取)")
    parser.add_argument("--ocr-engine", default=None,
                        choices=["paddleocr", "auto"],
                        help="OCR 文字识别引擎 (默认: 从配置读取)")
    parser.add_argument("--no-nlp-enhance", action="store_true",
                        help="跳过中文 NLP 增强（NER + 标签中文化）")
    parser.add_argument("--no-visual", action="store_true",
                        help="跳过视觉分析（场景分类/物体检测）")
    parser.add_argument("--no-ocr", action="store_true",
                        help="跳过画面文字识别")
    parser.add_argument("--no-highlight", action="store_true",
                        help="跳过精华提取")
    parser.add_argument("--scenes-only", action="store_true",
                        help="仅输出场景切割 JSON")
    parser.add_argument("-f", "--force", action="store_true",
                        help="忽略缓存，强制重新分析")
    parser.add_argument("--temp-dir", default=None,
                        help="临时文件目录 (默认: ./.cache)")
    parser.add_argument("--config", default="config.yaml",
                        help="配置文件路径 (默认: config.yaml)")
    parser.add_argument("--verbose", action="store_true",
                        help="显示详细日志")
    parser.add_argument("--no-adaptive", action="store_true",
                        help="禁用硬件自适应 (默认启用)")
    parser.add_argument("--max-memory", type=float, default=None,
                        help="最大内存使用 (GB)")
    parser.add_argument("--nice", type=int, default=None,
                        help="进程优先级 (0-19, 越大优先级越低)")
    parser.add_argument("--no-update-check", action="store_true",
                        help="跳过启动时的版本更新检查")
    parser.add_argument("--diarize", action="store_true",
                        help="启用说话人分离（多人对话场景）")
    parser.add_argument("--slice-chapters", action="store_true",
                        help="按章节切片视频片段 + 生成SRT字幕")
    parser.add_argument("--platform", action="store_true",
                        help="启用短视频平台适配（自动识别抖音/快手/B站/视频号链接）")
    parser.add_argument("--editing-suggest", action="store_true",
                        help="启用自动剪辑建议（高光检测/冗余标记/时间线生成/EDL导出）")
    parser.add_argument("--edl-format", default="cmx3600",
                        choices=["cmx3600", "csv", "json"],
                        help="EDL 导出格式 (默认: cmx3600)")
    parser.add_argument("--subtitle-style", default=None,
                        choices=["douyin", "bilibili", "movie", "minimal"],
                        help="字幕样式模板")
    parser.add_argument("--subtitle-format", default="ass",
                        choices=["srt", "ass", "vtt"],
                        help="字幕输出格式 (默认: ass)")
    parser.add_argument("--export-edl", action="store_true",
                        help="导出 EDL 剪辑时间线文件")
    parser.add_argument("--jianying", action="store_true",
                        help="导出剪映 draft.json 格式（可直接导入剪映专业版）")
    parser.add_argument("--quality-score", action="store_true",
                        help="启用说话人分离质量评分")
    parser.add_argument("--scene-management", action="store_true",
                        help="启用场景管理（detect→slice 一条链）")
    parser.add_argument("--viral-predict", action="store_true",
                        help="启用短视频爆款预测")
    parser.add_argument("--live-analyze", action="store_true",
                        help="启用实时直播分析（流式ASR+敏感词检测）")
    parser.add_argument("--dir", default=None,
                        help="批量处理目录（扫描视频文件逐个入队）")
    parser.add_argument("--hardware-tier", default=None,
                        choices=["low", "mid", "high"],
                        help="硬件档位（决定批量并发数）")
    parser.add_argument("--download-ct2-model", default=None,
                        choices=["tiny", "small", "medium"],
                        help="下载 Whisper CT2 量化模型")
    
    return parser.parse_args()


def print_banner():
    """打印启动横幅"""
    banner = """
╔══════════════════════════════════════════════════╗
║          🎬 video-analyzer v4.2.0               ║
║        视频分析处理 — 本地视频反编译工具         ║
╚══════════════════════════════════════════════════╝
    """
    print(banner)


def apply_process_priority(nice_level: int):
    """设置进程优先级，避免拖垮用户电脑"""
    try:
        if sys.platform == "win32":
            # Windows: 使用 BELOW_NORMAL_PRIORITY_CLASS
            import ctypes
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            # BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
            ctypes.windll.kernel32.SetPriorityClass(handle, 0x00004000)
            logger.debug("Windows 进程优先级已设置为 BELOW_NORMAL")
        else:
            # Linux/macOS: 使用 nice
            os.nice(nice_level)
            logger.debug(f"Process nice level set to {nice_level}")
    except Exception as e:
        logger.debug(f"无法设置进程优先级: {e}")


def limit_cache_size(cache_dir: str, max_size_gb: float):
    """限制缓存目录大小，自动清理旧文件"""
    try:
        if not os.path.exists(cache_dir):
            return
        
        # 计算目录大小
        total_size = 0
        file_list = []
        for root, dirs, files in os.walk(cache_dir):
            for f in files:
                fp = os.path.join(root, f)
                size = os.path.getsize(fp)
                total_size += size
                file_list.append((fp, size, os.path.getmtime(fp)))
        
        max_size = max_size_gb * 1024 * 1024 * 1024
        
        if total_size > max_size:
            # 按修改时间排序，删除最旧的文件
            file_list.sort(key=lambda x: x[2])
            
            freed = 0
            for fp, size, _ in file_list:
                if total_size - freed <= max_size * 0.8:  # 清理到 80%
                    break
                os.remove(fp)
                freed += size
            
            logger.info(f"缓存清理完成，释放 {freed / (1024**2):.1f}MB")
    
    except Exception as e:
        logger.debug(f"缓存清理失败: {e}")


def main():
    """主流程"""
    print_banner()
    args = parse_args()
    
    # 加载配置
    config = load_config(args.config if os.path.exists(args.config) else None)
    
    # ========== 硬件自适应配置 ==========
    if not args.no_adaptive:
        logger.info("🔍 检测硬件配置...")
        probe = HardwareProbe(config)
        config = probe.apply_to_config(config)
        
        # 应用硬件推荐的进程优先级
        nice_level = config.get("processing", {}).get("nice_level", 5)
        apply_process_priority(nice_level)
        
        # 启动实时资源监控
        resource_monitor = ResourceMonitor(
            max_memory_gb=config.get("processing", {}).get("max_memory_gb", 4),
            check_interval=5,
        )
        resource_monitor.start()
        logger.info("🖥️  实时资源监控已启动")
    else:
        resource_monitor = None
    
    # ========== GPU 自动加速探测（v4.3 新增） ==========
    gpu_accelerator = GPUAccelerator(config)
    gpu_probe_result = gpu_accelerator.probe_cuda()
    if gpu_probe_result["device"] == "cuda":
        logger.info(f"🚀 GPU 加速已启用: {gpu_probe_result.get('gpu_name', 'unknown')}")
    else:
        logger.info("💻 GPU 不可用，使用 CPU 模式")
        logger.info(gpu_accelerator.get_fallback_message())
    
    # 命令行参数覆盖配置 (优先级最高)
    if args.model:
        config["whisper"]["model_name"] = args.model
    if args.lang:
        config["whisper"]["language"] = args.lang
    config["visual_analysis"]["enable_scene_classification"] = not args.no_visual
    config["visual_analysis"]["enable_object_detection"] = not args.no_visual
    config["visual_analysis"]["enable_ocr"] = not args.no_ocr
    if args.temp_dir:
        config["processing"]["cache_dir"] = args.temp_dir
    if args.max_memory:
        config["processing"]["max_memory_gb"] = args.max_memory
    if args.nice is not None:
        config["processing"]["nice_level"] = args.nice
        apply_process_priority(args.nice)
    
    config["report"]["formats"] = args.format.split(",")
    
    if args.verbose:
        import logging
        get_logger().setLevel(logging.DEBUG)
    
    start_time = time.time()
    media = None
    
    try:
        # ========== 版本更新检查（非阻塞） ==========
        if not args.no_update_check:
            try:
                notifier = UpdateNotifier(config, current_version="4.2.0")
                update_result = notifier.check_for_updates()
                update_msg = notifier.format_update_message(update_result)
                if update_msg:
                    print(update_msg)
            except Exception:
                pass  # 更新检查失败不影响主流程
        
        # ========== 阶段 1: 输入处理 ==========
        logger.info("📥 [1/7] 处理输入...")
        input_handler = InputHandler(config)
        video_path = input_handler.process(args.input)
        logger.info(f"   视频路径: {video_path}")
        
        # ========== 媒体探测（v4.3 新增：纯音频支持） ==========
        media_probe = MediaProbe(config)
        is_pure_audio = media_probe.is_pure_audio(video_path)
        
        if is_pure_audio:
            logger.info("🎵 检测到纯音频输入，启用音频模式...")
            media_info = media_probe.get_media_info_for_video(video_path)
            audio_path = media_info["audio_path"]
            frames_dir = None
            logger.info(f"   时长: {media_info['duration']:.1f}s")
            logger.info(f"   音频已转换: {audio_path}")
        else:
            # ========== 阶段 2: 媒体处理 ==========
            logger.info("🔧 [2/7] 媒体处理...")
            media = MediaProcessor(config)
            media_info = media.get_media_info(video_path)
            logger.info(f"   分辨率: {media_info['width']}x{media_info['height']}")
            logger.info(f"   时长: {media_info['duration']:.1f}s")
            logger.info(f"   帧率: {media_info['fps']:.1f}")
            
            # 预估处理时间
            if not args.no_adaptive:
                probe = HardwareProbe(config)
                time_est = probe.estimate_processing_time(media_info['duration'], media_info)
                logger.info(f"   ⏱️  预估处理时间: {time_est['estimated_formatted']}")
            
            # 提取音频
            audio_path = media.extract_audio(video_path)
            logger.info(f"   音频已提取: {audio_path}")
            
            # 提取帧序列 (根据硬件能力自动选择采样率)
            frames_dir = media.extract_frames(video_path)
            logger.info(f"   帧序列已提取到: {frames_dir}")
        
        # ========== 阶段 3: 语音识别 ==========
        logger.info("🎙️  [3/7] 语音转文字...")
        
        # 根据配置/参数选择引擎
        asr_engine = args.asr_engine if args.asr_engine else config.get("asr", {}).get("engine", "auto")
        asr_router = ASRRouter(config)
        asr_result = asr_router.transcribe(
            audio_path,
            preferred_engine=asr_engine,
            language=args.lang if args.lang else config.get("asr", {}).get("language", "auto"),
        )
        
        # 将 ASRResult 转换为原 transcript 格式（兼容下游模块）
        transcript = {
            "text": asr_result.text,
            "language": asr_result.language,
            "duration": asr_result.duration,
            "segments": [
                {
                    "id": seg.id,
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text,
                    "confidence": seg.confidence,
                    "words": seg.words,
                    "speaker": seg.speaker,
                    "emotion": seg.emotion,
                }
                for seg in asr_result.segments
            ],
        }
        
        asr_active = asr_router.active_engine
        if asr_active and asr_active.name != "whisper":
            logger.info(f"   使用引擎: {asr_active.name}")
        logger.info(f"   识别完成: {len(transcript['segments'])} 个语音段")
        logger.info(f"   语言: {transcript.get('language', 'unknown')}")
        
        # ========== 中文 NLP 增强（可选） ==========
        nlp_enhancer = None
        if not args.no_nlp_enhance:
            nlp_enhancer = ChineseNLPEnhancement(config)
            if nlp_enhancer.use_jieba:
                logger.info("🔤 中文 NLP 增强已启用（NER + 标签中文化）")
        
        # ========== 说话人分离（可选） ==========
        diarize_result = None
        quality_score = None
        if args.diarize:
            logger.info("🗣️  说话人分离...")
            diarizer = SpeakerDiarization(config)
            diarize_result = diarizer.diarize(audio_path, transcript.get("segments", []))
            logger.info(f"   分离完成: {diarize_result['n_speakers']} 人")
            
            # 分离质量评分（v4.1 新增）
            if args.quality_score:
                logger.info("📊 评估分离质量...")
                scorer = QualityScorer(config)
                # 提取特征用于评分
                features = diarizer._extract_segment_features(audio_path, transcript.get("segments", []))
                quality_score = scorer.score(diarize_result, features, transcript.get("segments", []))
                logger.info(f"   质量评分: {quality_score.get('overall_score')} 分 ({quality_score.get('level')}可信度)")
                logger.info(f"   声纹距离: {quality_score.get('voiceprint_distance')}, 重叠率得分: {quality_score.get('overlap_ratio')}")
                logger.info(f"   建议: {quality_score.get('suggestion')}")
        
        # ========== 纯音频模式跳过场景检测和视觉分析 ==========
        scenes = None
        visual_data = None
        aligned_data = None
        fused_data = None
        highlights = None
        
        if is_pure_audio:
            logger.info("🎵 [音频模式] 跳过场景检测、视觉分析和 OCR")
            # 构建纯音频的 scenes（空）
            scenes = {"scenes": [], "total_scenes": 0}
            visual_data = {"scenes": []}
        else:
            # ========== 阶段 4: 场景检测 ==========
            logger.info("🎬 [4/7] 场景检测...")
            scene_detector = SceneDetector(config)
            scenes = scene_detector.detect_scenes(video_path, frames_dir)
            logger.info(f"   检测到 {len(scenes['scenes'])} 个场景")
            
            # 如果仅需要场景切割，到此为止
            if args.scenes_only:
                import json
                output_path = os.path.join(args.output, "scenes_only.json")
                os.makedirs(args.output, exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(scenes, f, ensure_ascii=False, indent=2)
                logger.info(f"✅ 场景 JSON 已保存: {output_path}")
                return
            
            # ========== 阶段 5: 视觉分析 ==========
            logger.info("🔍 [5/7] 视觉分析...")
            visual_analyzer = VisualAnalyzer(config)
            visual_data = visual_analyzer.analyze(scenes, video_path)
            logger.info(f"   视觉分析完成")
            
            # ✨ 中文 NLP 增强：物体标签 + 场景标签中文化
            if nlp_enhancer:
                from core.nlp import get_chinese_label
                for scene_data in visual_data.get("scenes", []):
                    # 物体标签中文化
                    for obj in scene_data.get("objects", []):
                        name = obj.get("name", "")
                        obj["name_zh"] = get_chinese_label(name)
                    # 场景标签中文化
                    scene_types = scene_data.get("scene_types", [])
                    scene_data["scene_types_zh"] = nlp_enhancer.translate_scene_labels(scene_types)
            
            # ========== 阶段 6: 时空对齐与融合 ==========
            logger.info("🔗 [6/7] 时空对齐与语义融合...")
            
            workers = config.get("processing", {}).get("num_workers", 4)
            logger.info(f"   使用 {workers} 个子进程并行处理")
            
            alignment = AlignmentEngine(config)
            aligned_data = alignment.align(transcript, scenes, visual_data, media_info)
            
            fusion = SemanticFusion(config)
            fused_data = fusion.fuse(aligned_data)
            logger.info(f"   融合完成")
            
            # ✨ 中文 NLP 增强：融合数据中的人名/地名/术语识别
            if nlp_enhancer and nlp_enhancer.use_ner:
                for scene in fused_data.get("scenes", []):
                    dialog = scene.get("content", {}).get("dialog", "")
                    if dialog:
                        entities = nlp_enhancer.recognize_entities(dialog)
                        scene["entities"] = entities
                        terms = nlp_enhancer.detect_terminology(dialog)
                        scene["terminology"] = terms
            
            # ========== 阶段 7: 精华提取与报告 ==========
            logger.info("✨ [7/7] 精华提取与报告生成...")
            
            if not args.no_highlight:
                extractor = HighlightExtractor(config)
                highlights = extractor.extract(fused_data)
                logger.info(f"   提取 {highlights.get('total_highlights', 0)} 个精华片段")
        
        # 生成报告
        reporter = ReportGenerator(config)
        output_paths = reporter.generate(
            transcript=transcript,
            scenes=scenes,
            visual_data=visual_data,
            aligned_data=aligned_data,
            fused_data=fused_data,
            highlights=highlights,
            media_info=media_info,
            output_dir=args.output,
            platform_analysis=platform_analysis,
            platform_meta=platform_meta,
            editing_result=editing_result,
            viral_result=viral_result,
            live_stats=live_stats,
        )
        
        # ========== 章节切片（可选） ==========
        if args.slice_chapters:
            logger.info("✂️  章节切片...")
            chapters_dir = os.path.join(args.output, "chapters")
            slicer = ChapterSlicer(config)
            chapters_result = slicer.slice_chapters(video_path, scenes, transcript, chapters_dir)
            logger.info(f"   切片完成: {chapters_result['total_chapters']} 个章节")
            output_paths["chapters"] = chapters_dir
        
        # ========== 短视频平台适配（可选） ==========
        platform_analysis = None
        platform_meta = None
        if args.platform:
            logger.info("📱 短视频平台适配...")
            platform_router = PlatformRouter(config)
            
            # 尝试从输入识别平台
            parse_result = platform_router.parse_link(args.input)
            if parse_result:
                platform_name, video_id = parse_result
                logger.info(f"   识别平台: {platform_name}, 视频ID: {video_id}")
                
                # 提取平台元数据
                platform_meta = platform_router.extract_metadata(platform_name, video_id)
                if platform_meta:
                    logger.info(f"   标题: {platform_meta.title[:30]}...")
                    logger.info(f"   作者: {platform_meta.author}")
                    logger.info(f"   点赞: {platform_meta.like_count}, 评论: {platform_meta.comment_count}")
                
                # 执行短视频特有分析
                platform_analysis = platform_router.analyze_short_video(
                    platform_name, video_path, platform_meta, transcript, scenes
                )
                
                if platform_analysis:
                    logger.info(f"   黄金前3秒: {platform_analysis.opening_3s.get('hook_type', '未知')}")
                    logger.info(f"   带货分析: {'是' if platform_analysis.ecommerce_analysis.get('is_ecommerce') else '否'}")
            else:
                logger.info("   未识别到平台链接，跳过平台分析")
        
        # ========== 自动剪辑建议（可选） ==========
        editing_result = None
        if args.editing_suggest:
            logger.info("🎬 自动剪辑建议...")
            
            # 高光检测
            logger.info("   检测高光片段...")
            highlight_detector = HighlightDetector(config)
            highlights_list = highlight_detector.detect(video_path, transcript, scenes)
            logger.info(f"   发现 {len(highlights_list)} 个高光片段")
            
            # 冗余检测
            logger.info("   检测冗余片段...")
            redundancy_detector = RedundancyDetector(config)
            redundancies = redundancy_detector.detect(video_path, transcript, scenes)
            logger.info(f"   发现 {len(redundancies)} 个冗余片段")
            
            # 生成剪辑时间线
            logger.info("   生成剪辑时间线...")
            timeline_gen = TimelineGenerator(config)
            original_duration = media_info.get("duration", 0)
            timeline = timeline_gen.generate(highlights_list, redundancies, original_duration)
            logger.info(f"   时间线: {len(timeline.get('clips', []))} 个片段, "
                       f"压缩比 {timeline.get('compression_ratio', 0):.0%}")
            
            editing_result = {
                "highlights": highlights_list,
                "redundancies": redundancies,
                "timeline": timeline,
            }
            
            # 导出 EDL
            if args.export_edl:
                logger.info("   导出 EDL 文件...")
                edl_exporter = EDLExporter(config)
                edl_dir = os.path.join(args.output, "edl")
                os.makedirs(edl_dir, exist_ok=True)
                edl_path = os.path.join(edl_dir, f"timeline.{args.edl_format}")
                edl_exporter.export(timeline, edl_path, format=args.edl_format)
                output_paths["edl"] = edl_path
                logger.info(f"   EDL 已导出: {edl_path}")
            
            # 导出剪映 draft.json（v4.1 新增）
            if args.jianying:
                logger.info("   导出剪映 draft.json...")
                jianying_exporter = JianyingExporter(config)
                jy_dir = os.path.join(args.output, "jianying")
                os.makedirs(jy_dir, exist_ok=True)
                jy_path = os.path.join(jy_dir, "draft.json")
                jianying_exporter.export(
                    timeline=timeline,
                    transcript=transcript,
                    video_path=video_path,
                    output_path=jy_path
                )
                output_paths["jianying"] = jy_path
                logger.info(f"   剪映文件已导出: {jy_path}")
            
            # 生成字幕文件
            logger.info("   生成字幕文件...")
            subtitle_stylist = SubtitleStylist(config)
            subtitle_dir = os.path.join(args.output, "subtitles")
            os.makedirs(subtitle_dir, exist_ok=True)
            subtitle_path = os.path.join(subtitle_dir, f"subtitle.{args.subtitle_format}")
            subtitle_stylist.generate(
                transcript, subtitle_path,
                style=args.subtitle_style,
                format=args.subtitle_format
            )
            output_paths["subtitle"] = subtitle_path
            logger.info(f"   字幕已生成: {subtitle_path}")
        
        # ========== 场景管理（可选，v4.2 新增） ==========
        if args.scene_management:
            logger.info("🎬 [场景管理] detect→slice 一条链...")
            scene_manager = SceneManager(config)
            scene_result = scene_manager.detect_and_slice(
                video_path, transcript, args.output, frames_dir
            )
            logger.info(f"   场景管理完成: {scene_result['total_chapters']} 个章节")
            
            # 更新 scenes 变量供后续报告使用
            scenes = scene_result["scenes"]
            output_paths["scene_management"] = scene_result["output_dir"]
        
        # ========== 爆款预测（可选，v4.2 新增） ==========
        viral_result = None
        if args.viral_predict:
            logger.info("🔥 [爆款预测] 分析爆款潜力...")
            predictor = ViralPredictor(config)
            viral_result = predictor.predict(
                video_path, transcript, scenes,
                platform_meta=platform_meta,
                visual_data=visual_data,
            )
            logger.info(f"   爆款得分: {viral_result['viral_score']}/100 ({viral_result['level']})")
            
            # 保存预测结果
            import json
            viral_path = os.path.join(args.output, "viral_prediction.json")
            os.makedirs(os.path.dirname(viral_path), exist_ok=True)
            with open(viral_path, "w", encoding="utf-8") as f:
                json.dump(viral_result, f, ensure_ascii=False, indent=2)
            output_paths["viral_prediction"] = viral_path
        
        # ========== 实时直播分析（可选，v4.2 新增） ==========
        live_stats = None
        if args.live_analyze:
            logger.info("🔴 [实时直播分析] 启动...")
            live = LiveAnalyzer(config)
            
            # 启动实时分析
            live.start(video_source=None)  # 模拟模式
            
            # 模拟实时输入（实际使用时应从流式 ASR 获取）
            for seg in transcript.get("segments", []):
                if not live._running:
                    break
                live.feed_segment(seg)
                time.sleep(0.01)  # 模拟实时间隔
            
            # 获取统计并停止
            live_stats = live.stop()
            logger.info(f"   直播分析完成: {live_stats['total_segments']} 段, "
                       f"{live_stats['total_sensitive_detected']} 次敏感词")
            
            # 导出敏感词日志
            if live_stats["total_sensitive_detected"] > 0:
                log_path = os.path.join(args.output, "live_sensitive_log.json")
                live.export_sensitive_log(log_path)
                output_paths["live_sensitive_log"] = log_path
        
        # ========== 说话人字幕（可选） ==========
        if diarize_result:
            logger.info("📝 生成说话人字幕...")
            speaker_srt_path = os.path.join(args.output, "speakers.srt")
            diarizer = SpeakerDiarization(config)
            diarizer.generate_srt_with_speakers(diarize_result, speaker_srt_path)
            output_paths["speaker_srt"] = speaker_srt_path
        
        # ========== 时间戳摘要 ==========
        logger.info("📋 生成时间戳摘要...")
        summary_dir = os.path.join(args.output, "summary")
        summary_gen = TimestampedSummary(config)
        summary_result = summary_gen.generate(highlights, fused_data, summary_dir)
        output_paths["timestamped_summary"] = summary_result.get("markdown_path")
        
        # 清理缓存
        max_cache = config.get("processing", {}).get("max_memory_gb", 4)
        limit_cache_size(config.get("processing", {}).get("cache_dir", ".cache"), max_cache)
        
        elapsed = time.time() - start_time
        logger.info(f"\n{'='*50}")
        logger.info(f"✅ 分析完成！耗时: {elapsed:.1f}s")
        logger.info(f"📄 输出文件:")
        for fmt, path in output_paths.items():
            logger.info(f"   [{fmt}] {path}")
        logger.info(f"{'='*50}")
        
        # 停止资源监控
        if resource_monitor:
            resource_monitor.stop()
            status = resource_monitor.get_status()
            logger.info(f"📊 峰值内存: {status['peak_memory_gb']:.1f}GB")
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ 错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        # 停止资源监控
        if resource_monitor:
            resource_monitor.stop()
        # 清理子进程，确保不残留
        if media and hasattr(media, '_subprocesses'):
            for proc in media._subprocesses:
                try:
                    proc.terminate()
                except Exception:
                    pass


def run_batch_mode(args, config):
    """
    批量处理模式（v4.3 新增）。
    
    Args:
        args: 命令行参数
        config: 配置
    """
    logger.info("📂 批量处理模式")
    
    # 创建队列管理器
    queue = QueueManager(config)
    
    # 扫描目录
    video_files = queue.scan_directory(args.dir)
    
    if not video_files:
        logger.warning(f"目录中没有视频文件: {args.dir}")
        return
    
    # 批量入队
    task_ids = queue.enqueue_batch(video_files, args.output)
    logger.info(f"已入队 {len(task_ids)} 个任务")
    
    # 确定硬件档位
    tier = args.hardware_tier if args.hardware_tier else 'mid'
    
    # 定义处理函数
    def process_task(task):
        input_path = task["input_path"]
        output_dir = task["output_dir"]
        
        if not output_dir:
            output_dir = os.path.join(args.output, os.path.splitext(os.path.basename(input_path))[0])
        
        # 单文件处理逻辑（简化版）
        from core.media_probe import MediaProbe
        from core.media_processor import MediaProcessor
        
        media_probe = MediaProbe(config)
        
        if media_probe.is_pure_audio(input_path):
            media_info = media_probe.get_media_info_for_video(input_path)
            audio_path = media_info["audio_path"]
        else:
            media = MediaProcessor(config)
            media_info = media.get_media_info(input_path)
            audio_path = media.extract_audio(input_path)
        
        # ASR 识别
        from core.asr import ASRRouter
        asr_router = ASRRouter(config)
        asr_result = asr_router.transcribe(audio_path)
        
        transcript = {
            "text": asr_result.text,
            "language": asr_result.language,
            "duration": asr_result.duration,
            "segments": [
                {
                    "id": seg.id,
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text,
                    "confidence": seg.confidence,
                }
                for seg in asr_result.segments
            ],
        }
        
        # 生成报告
        reporter = ReportGenerator(config)
        output_paths = reporter.generate(
            transcript=transcript,
            scenes={"scenes": [], "total_scenes": 0},
            visual_data={"scenes": []},
            aligned_data={},
            fused_data={},
            highlights=None,
            media_info=media_info,
            output_dir=output_dir,
        )
        
        return {"artifact_paths": output_dir, "transcript": transcript}
    
    # 运行批量处理
    stats = queue.run_batch(process_task, tier=tier)
    
    logger.info(f"批量处理完成: {stats}")


def run_download_ct2_model(args, config):
    """
    下载 CT2 模型（v4.3 新增）。
    
    Args:
        args: 命令行参数
        config: 配置
    """
    accelerator = GPUAccelerator(config)
    model_name = args.download_ct2_model
    
    # 获取下载指引
    instructions = accelerator.get_download_instructions(model_name)
    print(instructions)


if __name__ == "__main__":
    # 检查是否是批量模式
    args = parse_args()
    
    if args.dir:
        # 批量处理模式
        config = load_config(args.config if os.path.exists(args.config) else None)
        run_batch_mode(args, config)
    elif args.download_ct2_model:
        # 下载 CT2 模型模式
        config = load_config(args.config if os.path.exists(args.config) else None)
        run_download_ct2_model(args, config)
    else:
        # 单文件处理模式
        main()
