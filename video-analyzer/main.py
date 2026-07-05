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
from core.audio_transcriber import AudioTranscriber
from core.scene_detector import SceneDetector
from core.visual_analyzer import VisualAnalyzer
from core.alignment_engine import AlignmentEngine
from core.semantic_fusion import SemanticFusion
from core.highlight_extractor import HighlightExtractor
from core.report_generator import ReportGenerator
from core.config import load_config
from core.logger import get_logger
from core.hardware_probe import HardwareProbe

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
    
    return parser.parse_args()


def print_banner():
    """打印启动横幅"""
    banner = """
╔══════════════════════════════════════════════════╗
║          🎬 video-analyzer v2.0.0               ║
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
        # ========== 阶段 1: 输入处理 ==========
        logger.info("📥 [1/7] 处理输入...")
        input_handler = InputHandler(config)
        video_path = input_handler.process(args.input)
        logger.info(f"   视频路径: {video_path}")
        
        # ========== 阶段 2: 媒体处理 ==========
        logger.info("🔧 [2/7] 媒体处理...")
        media = MediaProcessor(config)
        media_info = media.get_media_info(video_path)
        logger.info(f"   分辨率: {media_info['width']}x{media_info['height']}")
        logger.info(f"   时长: {media_info['duration']:.1f}s")
        logger.info(f"   帧率: {media_info['fps']:.1f}")
        
        # 提取音频
        audio_path = media.extract_audio(video_path)
        logger.info(f"   音频已提取: {audio_path}")
        
        # 提取帧序列 (根据硬件能力自动选择采样率)
        frames_dir = media.extract_frames(video_path)
        logger.info(f"   帧序列已提取到: {frames_dir}")
        
        # ========== 阶段 3: 语音识别 ==========
        logger.info("🎙️  [3/7] 语音转文字...")
        transcriber = AudioTranscriber(config)
        transcript = transcriber.transcribe(audio_path)
        logger.info(f"   识别完成: {len(transcript['segments'])} 个语音段")
        logger.info(f"   语言: {transcript.get('language', 'unknown')}")
        
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
        
        # ========== 阶段 6: 时空对齐与融合 ==========
        logger.info("🔗 [6/7] 时空对齐与语义融合...")
        
        workers = config.get("processing", {}).get("num_workers", 4)
        logger.info(f"   使用 {workers} 个子进程并行处理")
        
        alignment = AlignmentEngine(config)
        aligned_data = alignment.align(transcript, scenes, visual_data, media_info)
        
        fusion = SemanticFusion(config)
        fused_data = fusion.fuse(aligned_data)
        logger.info(f"   融合完成")
        
        # ========== 阶段 7: 精华提取与报告 ==========
        logger.info("✨ [7/7] 精华提取与报告生成...")
        
        highlights = None
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
            output_dir=args.output
        )
        
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
        # 清理子进程，确保不残留
        if media and hasattr(media, '_subprocesses'):
            for proc in media._subprocesses:
                try:
                    proc.terminate()
                except Exception:
                    pass


if __name__ == "__main__":
    main()
