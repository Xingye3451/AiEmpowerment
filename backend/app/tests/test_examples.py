"""
视频处理测试示例

此脚本提供了使用视频处理测试框架的示例代码。
"""

import os
import asyncio
import logging
from test_video_processing import (
    test_remove_subtitles,
    test_extract_voice,
    test_generate_speech,
    test_sync_lips,
    test_add_subtitles,
    test_full_pipeline,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


async def example_remove_subtitles():
    """字幕擦除示例"""
    # 替换为实际的测试视频路径
    video_path = "uploads/test/test_video_with_subtitles.mp4"

    # 测试不同模式的字幕擦除
    for mode in ["light", "balanced", "aggressive"]:
        logger.info(f"测试 {mode} 模式的字幕擦除")
        try:
            result = await test_remove_subtitles(
                video_path=video_path, mode=mode, auto_detect=True
            )
            logger.info(f"{mode} 模式字幕擦除结果: {result}")
        except Exception as e:
            logger.error(f"{mode} 模式字幕擦除失败: {str(e)}")

    # 测试手动选择区域的字幕擦除
    selected_area = {
        "x": 100,  # 左上角x坐标
        "y": 400,  # 左上角y坐标
        "width": 800,  # 宽度
        "height": 100,  # 高度
    }

    try:
        result = await test_remove_subtitles(
            video_path=video_path,
            mode="balanced",
            selected_area=selected_area,
            auto_detect=False,
        )
        logger.info(f"手动选择区域字幕擦除结果: {result}")
    except Exception as e:
        logger.error(f"手动选择区域字幕擦除失败: {str(e)}")


async def example_voice_processing():
    """音色提取和语音生成示例"""
    # 替换为实际的测试视频路径
    video_path = "uploads/test/test_video_with_voice.mp4"

    try:
        # 1. 提取音色
        audio_path, voice_id = await test_extract_voice(video_path)
        logger.info(f"音色提取结果: 音频={audio_path}, 音色ID={voice_id}")

        # 2. 使用提取的音色生成新语音
        text = (
            "这是一段测试文本，用于测试语音生成功能。我们使用提取的音色来生成这段语音。"
        )
        speech_path = await test_generate_speech(text, voice_id)
        logger.info(f"语音生成结果: {speech_path}")

        return audio_path, speech_path
    except Exception as e:
        logger.error(f"音色处理示例失败: {str(e)}")
        return None, None


async def example_lip_sync():
    """唇形同步示例"""
    # 替换为实际的测试视频和音频路径
    video_path = "uploads/test/test_video_for_lip_sync.mp4"
    audio_path = "uploads/test/test_audio_for_lip_sync.wav"

    try:
        result = await test_sync_lips(video_path, audio_path)
        logger.info(f"唇形同步结果: {result}")
        return result
    except Exception as e:
        logger.error(f"唇形同步示例失败: {str(e)}")
        return None


async def example_add_subtitles():
    """添加字幕示例"""
    # 替换为实际的测试视频路径
    video_path = "uploads/test/test_video_without_subtitles.mp4"
    subtitle_text = (
        "这是测试字幕内容。\n这是第二行字幕。\n这是第三行字幕，用于测试多行字幕效果。"
    )

    # 测试不同样式的字幕
    subtitle_styles = [
        {
            "font_size": 24,
            "font_color": "#FFFFFF",
            "bg_color": "#000000",
            "bg_opacity": 0.5,
            "position": "bottom",
        },
        {
            "font_size": 32,
            "font_color": "#FFFF00",
            "bg_color": "#0000AA",
            "bg_opacity": 0.7,
            "position": "top",
        },
    ]

    results = []
    for i, style in enumerate(subtitle_styles):
        try:
            logger.info(f"测试字幕样式 {i+1}")
            result = await test_add_subtitles(video_path, subtitle_text, style)
            logger.info(f"字幕样式 {i+1} 结果: {result}")
            results.append(result)
        except Exception as e:
            logger.error(f"字幕样式 {i+1} 失败: {str(e)}")

    return results


async def example_full_pipeline():
    """完整处理流程示例"""
    # 替换为实际的测试视频路径
    video_path = "uploads/test/test_video_original.mp4"
    text = "这是一段用于测试完整视频处理流程的文本。我们将测试字幕擦除、音色提取、语音生成、唇形同步和添加字幕等功能。"

    subtitle_style = {
        "font_size": 28,
        "font_color": "#FFFFFF",
        "bg_color": "#000000",
        "bg_opacity": 0.6,
        "position": "bottom",
    }

    try:
        result = await test_full_pipeline(
            video_path=video_path,
            text=text,
            remove_subtitles=True,
            extract_voice=True,
            generate_speech=True,
            lip_sync=True,
            add_subtitles=True,
            subtitle_style=subtitle_style,
        )
        logger.info(f"完整流程处理结果: {result}")
        return result
    except Exception as e:
        logger.error(f"完整流程处理失败: {str(e)}")
        return None


async def run_examples():
    """运行所有示例"""
    examples = [
        ("字幕擦除示例", example_remove_subtitles),
        ("音色处理示例", example_voice_processing),
        ("唇形同步示例", example_lip_sync),
        ("添加字幕示例", example_add_subtitles),
        ("完整流程示例", example_full_pipeline),
    ]

    for name, example_func in examples:
        logger.info(f"开始运行 {name}")
        try:
            await example_func()
            logger.info(f"{name} 运行完成")
        except Exception as e:
            logger.error(f"{name} 运行失败: {str(e)}")
        logger.info("-" * 50)


if __name__ == "__main__":
    # 确保测试目录存在
    os.makedirs("uploads/test", exist_ok=True)

    # 运行示例
    asyncio.run(run_examples())
