"""
视频处理服务测试模块

此模块提供了测试视频处理服务各个独立功能的工具和测试用例。
可以单独测试字幕擦除、音色提取、语音生成、唇形同步和字幕添加等功能。
"""

import os
import sys
import asyncio
import logging
import argparse
from typing import Dict, Any, List, Optional
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.video_processing_service import VideoProcessingService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# 测试目录配置
BASE_DIR = "uploads"
TEMP_DIR = "uploads/temp"
OUTPUT_DIR = "uploads/processed_videos"
VOICE_DIR = "uploads/voices"
TEST_DIR = "uploads/test"

# 确保目录存在
for directory in [BASE_DIR, TEMP_DIR, OUTPUT_DIR, VOICE_DIR, TEST_DIR]:
    os.makedirs(directory, exist_ok=True)


async def progress_callback(
    task_id: str, progress: int, message: str, data: Dict[str, Any]
):
    """进度回调函数，用于显示处理进度"""
    logger.info(f"任务 {task_id} - 进度: {progress}% - {message}")
    if data.get("current_stage"):
        logger.info(f"当前阶段: {data['current_stage']}")


async def test_remove_subtitles(
    video_path: str,
    mode: str = "balanced",
    selected_area: Optional[Dict[str, Any]] = None,
    auto_detect: bool = False,
):
    """测试字幕擦除功能"""
    logger.info(f"开始测试字幕擦除功能 - 模式: {mode}")

    service = VideoProcessingService(BASE_DIR, TEMP_DIR, OUTPUT_DIR, VOICE_DIR)
    task_id = f"test_remove_subtitles_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    task_dir = os.path.join(TEMP_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)

    try:
        result = await service._remove_subtitles(
            video_path=video_path,
            task_dir=task_dir,
            task_id=task_id,
            mode=mode,
            selected_area=selected_area,
            auto_detect=auto_detect,
            start_progress=0,
            end_progress=100,
            progress_callback=progress_callback,
        )

        logger.info(f"字幕擦除完成，输出文件: {result}")
        return result
    except Exception as e:
        logger.error(f"字幕擦除测试失败: {str(e)}")
        raise


async def test_extract_voice(video_path: str):
    """测试音色提取功能"""
    logger.info("开始测试音色提取功能")

    service = VideoProcessingService(BASE_DIR, TEMP_DIR, OUTPUT_DIR, VOICE_DIR)
    task_id = f"test_extract_voice_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    task_dir = os.path.join(TEMP_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)

    try:
        audio_path, voice_id = await service._extract_voice(
            video_path=video_path,
            task_dir=task_dir,
            task_id=task_id,
            start_progress=0,
            end_progress=100,
            progress_callback=progress_callback,
        )

        logger.info(f"音色提取完成，音频文件: {audio_path}, 音色ID: {voice_id}")
        return audio_path, voice_id
    except Exception as e:
        logger.error(f"音色提取测试失败: {str(e)}")
        raise


async def test_generate_speech(text: str, voice_id: str):
    """测试语音生成功能"""
    logger.info(f"开始测试语音生成功能 - 文本: {text[:30]}...")

    service = VideoProcessingService(BASE_DIR, TEMP_DIR, OUTPUT_DIR, VOICE_DIR)
    task_id = f"test_generate_speech_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    task_dir = os.path.join(TEMP_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)

    try:
        audio_path = await service._generate_speech(
            text=text,
            voice_id=voice_id,
            task_dir=task_dir,
            task_id=task_id,
            start_progress=0,
            end_progress=100,
            progress_callback=progress_callback,
        )

        logger.info(f"语音生成完成，音频文件: {audio_path}")
        return audio_path
    except Exception as e:
        logger.error(f"语音生成测试失败: {str(e)}")
        raise


async def test_sync_lips(video_path: str, audio_path: str):
    """测试唇形同步功能"""
    logger.info("开始测试唇形同步功能")

    service = VideoProcessingService(BASE_DIR, TEMP_DIR, OUTPUT_DIR, VOICE_DIR)
    task_id = f"test_sync_lips_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    task_dir = os.path.join(TEMP_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)

    try:
        result_video = await service._sync_lips(
            video_path=video_path,
            audio_path=audio_path,
            task_dir=task_dir,
            task_id=task_id,
            start_progress=0,
            end_progress=100,
            progress_callback=progress_callback,
        )

        logger.info(f"唇形同步完成，输出视频: {result_video}")
        return result_video
    except Exception as e:
        logger.error(f"唇形同步测试失败: {str(e)}")
        raise


async def test_add_subtitles(
    video_path: str, subtitle_text: str, subtitle_style: Optional[Dict[str, Any]] = None
):
    """测试添加字幕功能"""
    logger.info(f"开始测试添加字幕功能 - 文本: {subtitle_text[:30]}...")

    service = VideoProcessingService(BASE_DIR, TEMP_DIR, OUTPUT_DIR, VOICE_DIR)
    task_id = f"test_add_subtitles_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    task_dir = os.path.join(TEMP_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)

    if subtitle_style is None:
        subtitle_style = {
            "font_size": 24,
            "font_color": "#FFFFFF",
            "bg_color": "#000000",
            "bg_opacity": 0.5,
            "position": "bottom",
        }

    try:
        result_video = await service._add_subtitles(
            video_path=video_path,
            subtitle_text=subtitle_text,
            task_dir=task_dir,
            task_id=task_id,
            subtitle_style=subtitle_style,
            start_progress=0,
            end_progress=100,
            progress_callback=progress_callback,
        )

        logger.info(f"添加字幕完成，输出视频: {result_video}")
        return result_video
    except Exception as e:
        logger.error(f"添加字幕测试失败: {str(e)}")
        raise


async def test_full_pipeline(
    video_path: str,
    text: str,
    remove_subtitles: bool = True,
    extract_voice: bool = True,
    generate_speech: bool = True,
    lip_sync: bool = True,
    add_subtitles: bool = True,
    subtitle_style: Optional[Dict[str, Any]] = None,
):
    """测试完整的视频处理流程"""
    logger.info("开始测试完整视频处理流程")

    service = VideoProcessingService(BASE_DIR, TEMP_DIR, OUTPUT_DIR, VOICE_DIR)
    task_id = f"test_full_pipeline_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # 构建任务数据
    task_data = {
        "original_path": video_path,
        "text": text,
        "remove_subtitles": remove_subtitles,
        "extract_voice": extract_voice,
        "generate_speech": generate_speech,
        "lip_sync": lip_sync,
        "add_subtitles": add_subtitles,
        "subtitle_style": subtitle_style or {},
        "processing_pipeline": [],
    }

    # 根据选项构建处理流程
    if remove_subtitles:
        task_data["processing_pipeline"].append("remove_subtitles")
    if extract_voice:
        task_data["processing_pipeline"].append("extract_voice")
    if generate_speech:
        task_data["processing_pipeline"].append("generate_speech")
    if lip_sync:
        task_data["processing_pipeline"].append("lip_sync")
    if add_subtitles:
        task_data["processing_pipeline"].append("add_subtitles")

    try:
        result = await service.process_video(
            task_id=task_id, task_data=task_data, progress_callback=progress_callback
        )

        logger.info(f"完整流程处理完成: {result}")
        return result
    except Exception as e:
        logger.error(f"完整流程测试失败: {str(e)}")
        raise


async def main():
    """主函数，解析命令行参数并执行相应的测试"""
    parser = argparse.ArgumentParser(description="视频处理服务测试工具")
    parser.add_argument(
        "--test",
        type=str,
        required=True,
        choices=[
            "remove_subtitles",
            "extract_voice",
            "generate_speech",
            "sync_lips",
            "add_subtitles",
            "full_pipeline",
        ],
        help="要测试的功能",
    )
    parser.add_argument("--video", type=str, help="输入视频路径")
    parser.add_argument("--audio", type=str, help="输入音频路径（用于唇形同步测试）")
    parser.add_argument("--text", type=str, help="文本内容（用于语音生成和字幕测试）")
    parser.add_argument("--voice-id", type=str, help="音色ID（用于语音生成测试）")
    parser.add_argument(
        "--mode",
        type=str,
        default="balanced",
        choices=["light", "balanced", "aggressive"],
        help="字幕擦除模式",
    )
    parser.add_argument("--auto-detect", action="store_true", help="自动检测字幕区域")

    args = parser.parse_args()

    if args.test == "remove_subtitles":
        if not args.video:
            parser.error("--video 参数是必需的")
        await test_remove_subtitles(args.video, args.mode, None, args.auto_detect)

    elif args.test == "extract_voice":
        if not args.video:
            parser.error("--video 参数是必需的")
        await test_extract_voice(args.video)

    elif args.test == "generate_speech":
        if not args.text or not args.voice_id:
            parser.error("--text 和 --voice-id 参数是必需的")
        await test_generate_speech(args.text, args.voice_id)

    elif args.test == "sync_lips":
        if not args.video or not args.audio:
            parser.error("--video 和 --audio 参数是必需的")
        await test_sync_lips(args.video, args.audio)

    elif args.test == "add_subtitles":
        if not args.video or not args.text:
            parser.error("--video 和 --text 参数是必需的")
        await test_add_subtitles(args.video, args.text)

    elif args.test == "full_pipeline":
        if not args.video or not args.text:
            parser.error("--video 和 --text 参数是必需的")
        await test_full_pipeline(args.video, args.text)


if __name__ == "__main__":
    asyncio.run(main())
