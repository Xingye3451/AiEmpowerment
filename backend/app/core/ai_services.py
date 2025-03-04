import os
import logging
import aiohttp
import json
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class RunwayMLService:
    """使用RunwayML的API进行视频修复和字幕移除"""

    def __init__(self):
        self.api_key = settings.RUNWAY_API_KEY
        self.api_base = "https://api.runwayml.com/v1"

    async def detect_subtitle_area(self, input_path: str) -> Optional[Dict[str, int]]:
        """
        使用AI检测视频中的字幕区域

        Args:
            input_path: 输入视频路径

        Returns:
            字幕区域坐标，格式为 {"x": x, "y": y, "width": w, "height": h}
            如果未检测到字幕，返回 None
        """
        async with aiohttp.ClientSession() as session:
            # 1. 上传视频
            upload_url = f"{self.api_base}/detect"
            async with session.post(
                upload_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                data={"file": open(input_path, "rb")},
            ) as response:
                upload_result = await response.json()

            # 2. 开始检测任务
            payload = {
                "input": {
                    "video": upload_result["url"],
                    "detection_type": "subtitle",
                    "detection_quality": "high",
                }
            }

            detect_url = f"{self.api_base}/inference"
            async with session.post(
                detect_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            ) as response:
                result = await response.json()

                if "subtitle_area" in result:
                    return result["subtitle_area"]
                return None

    async def inpaint_video(
        self,
        input_path: str,
        output_path: str,
        mask_type: str = "text",
        restoration_quality: str = "high",
        selected_area: Optional[Dict[str, int]] = None,
        auto_detect: bool = False,
    ):
        """
        使用RunwayML的Inpainting模型移除视频中的字幕并修复背景

        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            mask_type: 遮罩类型，默认为"text"（文字）
            restoration_quality: 修复质量，默认为"high"
            selected_area: 选定的区域，格式为 {"x": x, "y": y, "width": w, "height": h}
            auto_detect: 是否自动检测字幕区域，如果为True且未提供selected_area，将自动检测
        """
        # 如果启用自动检测且未指定区域，尝试检测字幕区域
        if auto_detect and not selected_area:
            selected_area = await self.detect_subtitle_area(input_path)
            if not selected_area:
                logger.warning(f"未在视频 {input_path} 中检测到字幕区域")

        async with aiohttp.ClientSession() as session:
            # 1. 上传视频
            upload_url = f"{self.api_base}/uploads"
            async with session.post(
                upload_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                data={"file": open(input_path, "rb")},
            ) as response:
                upload_result = await response.json()

            # 2. 开始处理任务
            payload = {
                "input": {
                    "video": upload_result["url"],
                    "mask_type": mask_type,
                    "restoration_quality": restoration_quality,
                }
            }

            # 如果指定了区域，添加到请求中
            if selected_area:
                payload["input"]["mask_area"] = {
                    "x": selected_area["x"],
                    "y": selected_area["y"],
                    "width": selected_area["width"],
                    "height": selected_area["height"],
                }
                # 添加区域追踪选项
                payload["input"]["track_area"] = True
                payload["input"]["tracking_quality"] = "high"

            inference_url = f"{self.api_base}/inference"
            async with session.post(
                inference_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            ) as response:
                result = await response.json()

            # 3. 下载处理后的视频
            async with session.get(
                result["output"]["video"],
                headers={"Authorization": f"Bearer {self.api_key}"},
            ) as response:
                with open(output_path, "wb") as f:
                    while True:
                        chunk = await response.content.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)


class VoiceCloningService:
    """使用Coqui TTS或YourTTS进行声音克隆"""

    def __init__(self):
        self.api_key = settings.COQUI_API_KEY
        self.api_base = "https://api.coqui.ai/v2"

    async def extract_voice_features(self, audio_path: str) -> Dict[str, Any]:
        """从原始音频中提取说话人的声音特征"""
        async with aiohttp.ClientSession() as session:
            upload_url = f"{self.api_base}/voice/extract_features"
            async with session.post(
                upload_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                data={"audio": open(audio_path, "rb")},
            ) as response:
                return await response.json()

    async def generate_speech(
        self, text: str, voice_features: Dict[str, Any], output_path: str
    ):
        """使用提取的声音特征生成新的语音"""
        async with aiohttp.ClientSession() as session:
            generate_url = f"{self.api_base}/tts/clone"
            payload = {
                "text": text,
                "voice_features": voice_features,
                "quality": "high",
            }

            async with session.post(
                generate_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            ) as response:
                with open(output_path, "wb") as f:
                    while True:
                        chunk = await response.content.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)


class LipSyncService:
    """使用SadTalker进行唇形同步"""

    def __init__(self):
        self.api_key = settings.SADTALKER_API_KEY
        self.api_base = "https://api.sadtalker.io/v1"

    async def sync_video_with_audio(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        sync_quality: str = "high",
    ):
        """将视频和音频进行唇形同步"""
        async with aiohttp.ClientSession() as session:
            # 1. 上传视频和音频
            files = {"video": open(video_path, "rb"), "audio": open(audio_path, "rb")}

            payload = {
                "quality": sync_quality,
                "enhance_face": True,
                "sync_precision": "frame",
            }

            sync_url = f"{self.api_base}/sync"
            async with session.post(
                sync_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                data=payload,
                files=files,
            ) as response:
                # 下载处理后的视频
                with open(output_path, "wb") as f:
                    while True:
                        chunk = await response.content.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)


class SubtitleService:
    """使用AI服务生成视频字幕"""

    def __init__(self):
        self.api_key = settings.SUBTITLE_API_KEY
        self.api_base = "https://api.subtitle.ai/v1"

    async def generate_subtitles(self, video_path: str, text: str, output_path: str):
        """生成视频字幕并将其嵌入到视频中"""
        async with aiohttp.ClientSession() as session:
            # 1. 上传视频
            upload_url = f"{self.api_base}/upload"
            async with session.post(
                upload_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                data={"file": open(video_path, "rb")},
            ) as response:
                upload_result = await response.json()

            # 2. 生成字幕
            payload = {
                "video_url": upload_result["url"],
                "text": text,
                "style": {
                    "font": "Arial",
                    "size": 32,
                    "color": "#FFFFFF",
                    "background": "#000000",
                    "opacity": 0.8,
                },
                "position": "bottom",
                "format": "srt",
            }

            generate_url = f"{self.api_base}/generate"
            async with session.post(
                generate_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            ) as response:
                result = await response.json()

            # 3. 将字幕嵌入到视频中
            embed_url = f"{self.api_base}/embed"
            embed_payload = {
                "video_url": upload_result["url"],
                "subtitle_url": result["subtitle_url"],
            }

            async with session.post(
                embed_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=embed_payload,
            ) as response:
                # 下载带字幕的视频
                with open(output_path, "wb") as f:
                    while True:
                        chunk = await response.content.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
