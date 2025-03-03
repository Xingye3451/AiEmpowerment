import os
import logging
import aiohttp
import json
from typing import Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class RunwayMLService:
    """使用RunwayML的API进行视频修复和字幕移除"""
    def __init__(self):
        self.api_key = settings.RUNWAY_API_KEY
        self.api_base = "https://api.runwayml.com/v1"

    async def inpaint_video(self, input_path: str, output_path: str, mask_type: str = "text", restoration_quality: str = "high"):
        """
        使用RunwayML的Inpainting模型移除视频中的字幕并修复背景
        """
        async with aiohttp.ClientSession() as session:
            # 1. 上传视频
            upload_url = f"{self.api_base}/uploads"
            async with session.post(upload_url, 
                                 headers={"Authorization": f"Bearer {self.api_key}"},
                                 data={'file': open(input_path, 'rb')}) as response:
                upload_result = await response.json()
                
            # 2. 开始处理任务
            payload = {
                "input": {
                    "video": upload_result["url"],
                    "mask_type": mask_type,
                    "restoration_quality": restoration_quality
                }
            }
            
            inference_url = f"{self.api_base}/inference"
            async with session.post(inference_url,
                                 headers={"Authorization": f"Bearer {self.api_key}"},
                                 json=payload) as response:
                result = await response.json()
                
            # 3. 下载处理后的视频
            async with session.get(result["output"]["video"],
                                headers={"Authorization": f"Bearer {self.api_key}"}) as response:
                with open(output_path, 'wb') as f:
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
            async with session.post(upload_url,
                                 headers={"Authorization": f"Bearer {self.api_key}"},
                                 data={'audio': open(audio_path, 'rb')}) as response:
                return await response.json()

    async def generate_speech(self, text: str, voice_features: Dict[str, Any], output_path: str):
        """使用提取的声音特征生成新的语音"""
        async with aiohttp.ClientSession() as session:
            generate_url = f"{self.api_base}/tts/clone"
            payload = {
                "text": text,
                "voice_features": voice_features,
                "quality": "high"
            }
            
            async with session.post(generate_url,
                                 headers={"Authorization": f"Bearer {self.api_key}"},
                                 json=payload) as response:
                with open(output_path, 'wb') as f:
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

    async def sync_video_with_audio(self, video_path: str, audio_path: str, output_path: str, sync_quality: str = "high"):
        """将视频和音频进行唇形同步"""
        async with aiohttp.ClientSession() as session:
            # 1. 上传视频和音频
            files = {
                'video': open(video_path, 'rb'),
                'audio': open(audio_path, 'rb')
            }
            
            payload = {
                'quality': sync_quality,
                'enhance_face': True,
                'sync_precision': 'frame'
            }
            
            sync_url = f"{self.api_base}/sync"
            async with session.post(sync_url,
                                headers={"Authorization": f"Bearer {self.api_key}"},
                                data=payload,
                                files=files) as response:
                # 下载处理后的视频
                with open(output_path, 'wb') as f:
                    while True:
                        chunk = await response.content.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)