"""
完整依赖列表及安装指南：

1. 基础依赖
   pip install -i https://mirrors.aliyun.com/pypi/simple/ \\
       numpy>=1.26.0 \\
       opencv-python>=4.8.0 \\
       torch>=2.1.0 \\
       torchaudio>=2.1.0 \\
       torchvision>=0.21.0

2. OCR相关（选择一个即可）
   # PaddleOCR (推荐)
   pip install -i https://mirror.baidu.com/pypi/simple \\
       paddlepaddle-gpu==2.5.1  # 如果有NVIDIA GPU
       # 或
       paddlepaddle==2.5.1      # CPU版本
   pip install "paddleocr>=2.7.0"

   # EasyOCR (备选)
   pip install easyocr

   # Tesseract (备选)
   # Windows: 下载安装器 https://github.com/UB-Mannheim/tesseract/wiki
   pip install pytesseract

3. 音视频处理
   pip install -i https://mirrors.aliyun.com/pypi/simple/ \\
       ffmpeg-python>=0.2.0 \\
       moviepy>=1.0.3 \\
       resemblyzer>=0.1.0 \\
       face-alignment>=1.3.5 \\
       montreal-forced-aligner>=2.0.0

4. HTTP和异步支持
   pip install -i https://mirrors.aliyun.com/pypi/simple/ \\
       aiohttp>=3.8.1 \\
       aiofiles>=0.8.0

5. 工具类库
   pip install -i https://mirrors.aliyun.com/pypi/simple/ \\
       pypinyin>=0.44.0 \\
       pyyaml>=5.4.1 \\
       python-dotenv>=0.19.0

环境要求：
1. Python 3.8-3.10 (推荐3.10)
2. CUDA 11.8+ (如果使用GPU)
3. Windows 10/11 或 Linux
4. 最小8GB内存，推荐16GB
5. NVIDIA GPU 6GB+ (推荐)

安装步骤：
1. 创建虚拟环境
   python -m venv venv
   .\\venv\\Scripts\\activate  # Windows
   source venv/bin/activate # Linux/Mac

2. 升级pip
   python -m pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/

3. 安装基础依赖
   # 复制上面的命令进行安装

4. 安装OCR引擎
   # 根据需求选择一个OCR引擎进行安装

5. 安装其他依赖
   # 复制相应的命令进行安装

注意事项：
1. 建议使用国内镜像源加速安装
2. GPU版本的paddle需要匹配CUDA版本
3. 部分包可能需要Visual C++ Build Tools（Windows）
4. 建议按照依赖类别分批安装，便于排查问题

云服务API选项：
1. RunwayML API - https://runwayml.com/
   - 视频修复、字幕去除、视频增强
   - 价格: 基础版$15/月起

2. ElevenLabs API - https://elevenlabs.io/
   - 语音克隆、文本转语音
   - 价格: 基础版$5/月起

3. SyncLabs API - https://synclabs.so/
   - 唇形同步
   - 价格: 按项目计费

4. Replicate API - https://replicate.com/
   - 多种AI模型集成
   - 价格: 按使用量计费
"""

import os
import logging
import aiohttp
import json
from typing import Dict, Any, Optional, List, Union
from app.core.config import settings
import time
import uuid

# 暂时注释掉不兼容的导入
# from resemblyzer import VoiceEncoder
# import face_alignment
# from montreal_forced_aligner import align
from pypinyin import pinyin, Style
import numpy as np
import cv2
import torch
import asyncio
from concurrent.futures import ProcessPoolExecutor

logger = logging.getLogger(__name__)

# 添加警告信息
logger.warning(
    "PaddleOCR is not available on this platform. Some OCR features may be limited."
)
logger.warning(
    "Voice cloning features are not available on this platform. Some voice features may be limited."
)


# 云服务API配置
class APIConfig:
    """API服务配置类"""

    def __init__(self):
        # 从环境变量或配置文件加载API密钥
        self.runway_api_key = (
            settings.RUNWAY_API_KEY
            if hasattr(settings, "RUNWAY_API_KEY")
            else os.getenv("RUNWAY_API_KEY", "")
        )
        self.eleven_labs_api_key = (
            settings.ELEVEN_LABS_API_KEY
            if hasattr(settings, "ELEVEN_LABS_API_KEY")
            else os.getenv("ELEVEN_LABS_API_KEY", "")
        )
        self.sync_labs_api_key = (
            settings.SYNC_LABS_API_KEY
            if hasattr(settings, "SYNC_LABS_API_KEY")
            else os.getenv("SYNC_LABS_API_KEY", "")
        )
        self.replicate_api_key = (
            settings.REPLICATE_API_KEY
            if hasattr(settings, "REPLICATE_API_KEY")
            else os.getenv("REPLICATE_API_KEY", "")
        )

        # API端点
        self.runway_endpoint = "https://api.runwayml.com/v1"
        self.eleven_labs_endpoint = "https://api.elevenlabs.io/v1"
        self.sync_labs_endpoint = "https://api.synclabs.so/v1"
        self.replicate_endpoint = "https://api.replicate.com/v1"

        # 检查API密钥是否配置
        self.runway_available = bool(self.runway_api_key)
        self.eleven_labs_available = bool(self.eleven_labs_api_key)
        self.sync_labs_available = bool(self.sync_labs_api_key)
        self.replicate_available = bool(self.replicate_api_key)

        # 日志记录API可用性
        if not self.runway_available:
            logger.warning("RunwayML API密钥未配置，相关功能将不可用")
        if not self.eleven_labs_available:
            logger.warning("ElevenLabs API密钥未配置，相关功能将不可用")
        if not self.sync_labs_available:
            logger.warning("SyncLabs API密钥未配置，相关功能将不可用")
        if not self.replicate_available:
            logger.warning("Replicate API密钥未配置，相关功能将不可用")


# 创建全局API配置实例
api_config = APIConfig()


class ProcessingMode:
    """处理模式枚举"""

    CLOUD = "cloud"  # 云服务处理
    LOCAL = "local"  # 本地处理


class RunwayMLService:
    """RunwayML API服务类"""

    def __init__(self):
        self.api_key = api_config.runway_api_key
        self.api_url = api_config.runway_endpoint
        self.available = api_config.runway_available

        if not self.available:
            logger.warning("RunwayML服务不可用，请检查API密钥配置")

    async def detect_subtitle_area(self, input_path: str) -> Optional[Dict[str, int]]:
        """检测视频中的字幕区域"""
        if not self.available:
            logger.error("RunwayML API未配置，无法检测字幕区域")
            return None

        try:
            # 准备请求数据
            video_data = await self._prepare_video_data(input_path)

            async with aiohttp.ClientSession() as session:
                # 调用RunwayML API检测字幕区域
                async with session.post(
                    f"{self.api_url}/detect/text",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"video": video_data},
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"RunwayML API错误: {error_text}")
                        return None

                    result = await response.json()

                    # 处理API返回结果
                    if "text_areas" in result and result["text_areas"]:
                        # 找到最可能的字幕区域（通常在底部）
                        subtitle_area = max(
                            result["text_areas"],
                            key=lambda area: area["y"] + area["height"],
                        )

                        return {
                            "x": subtitle_area["x"],
                            "y": subtitle_area["y"],
                            "width": subtitle_area["width"],
                            "height": subtitle_area["height"],
                        }

            return None
        except Exception as e:
            logger.error(f"字幕区域检测失败: {str(e)}")
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
        """使用RunwayML API进行视频修复"""
        if not self.available:
            logger.error("RunwayML API未配置，无法进行视频修复")
            return False

        try:
            # 准备请求数据
            video_data = await self._prepare_video_data(input_path)

            # 准备请求参数
            payload = {
                "video": video_data,
                "mask_type": mask_type,
                "quality": restoration_quality,
            }

            # 如果提供了选定区域，添加到请求中
            if selected_area:
                payload["mask_area"] = selected_area
            elif auto_detect:
                # 自动检测字幕区域
                detected_area = await self.detect_subtitle_area(input_path)
                if detected_area:
                    payload["mask_area"] = detected_area
                    logger.info(f"自动检测到字幕区域: {detected_area}")
                else:
                    logger.warning("未能自动检测到字幕区域，将处理整个视频")

            # 调用RunwayML API进行视频修复
            async with aiohttp.ClientSession() as session:
                # 创建任务
                async with session.post(
                    f"{self.api_url}/inpainting",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload,
                ) as response:
                    if response.status != 202:  # 202 Accepted
                        error_text = await response.text()
                        logger.error(f"RunwayML API错误: {error_text}")
                        return False

                    result = await response.json()
                    task_id = result.get("id")

                    if not task_id:
                        logger.error("未能获取任务ID")
                        return False

                # 轮询任务状态
                status = "processing"
                while status == "processing":
                    await asyncio.sleep(5)  # 每5秒检查一次

                    async with session.get(
                        f"{self.api_url}/inpainting/{task_id}",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                    ) as status_response:
                        if status_response.status != 200:
                            error_text = await status_response.text()
                            logger.error(f"获取任务状态失败: {error_text}")
                            return False

                        status_result = await status_response.json()
                        status = status_result.get("status", "")

                        if status == "failed":
                            logger.error(
                                f"视频修复任务失败: {status_result.get('error', '')}"
                            )
                            return False
                        elif status == "completed":
                            # 下载处理后的视频
                            video_url = status_result.get("output", {}).get("video", "")
                            if not video_url:
                                logger.error("未能获取处理后的视频URL")
                                return False

                            # 下载视频
                            async with session.get(video_url) as video_response:
                                if video_response.status != 200:
                                    logger.error("下载处理后的视频失败")
                                    return False

                                video_data = await video_response.read()

                                # 保存到输出路径
                                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                                with open(output_path, "wb") as f:
                                    f.write(video_data)

                                logger.info(f"视频修复完成，已保存到: {output_path}")
                                return True

            return False
        except Exception as e:
            logger.error(f"视频修复失败: {str(e)}")
            return False

    async def _prepare_video_data(self, video_path: str) -> str:
        """准备视频数据用于API请求"""
        # 对于RunwayML API，我们需要将视频转换为base64或上传到临时URL
        # 这里简化处理，假设API接受视频文件路径
        # 实际实现可能需要根据API要求进行调整
        return video_path


class VoiceCloningService:
    """语音克隆服务类"""

    def __init__(self):
        self.api_key = api_config.eleven_labs_api_key
        self.api_url = api_config.eleven_labs_endpoint
        self.available = api_config.eleven_labs_available

        if not self.available:
            logger.warning("ElevenLabs服务不可用，请检查API密钥配置")

    async def extract_voice_features(self, audio_path: str) -> Dict[str, Any]:
        """从音频中提取声音特征"""
        if not self.available:
            logger.error("ElevenLabs API未配置，无法提取声音特征")
            return {}

        try:
            # 为ElevenLabs API创建声音ID
            voice_id = await self._create_voice_from_audio(audio_path)
            if not voice_id:
                return {}

            return {"voice_id": voice_id}
        except Exception as e:
            logger.error(f"声音特征提取失败: {str(e)}")
            return {}

    async def generate_speech(
        self, text: str, voice_features: Dict[str, Any], output_path: str
    ):
        """生成语音"""
        if not self.available:
            logger.error("ElevenLabs API未配置，无法生成语音")
            return False

        try:
            voice_id = voice_features.get("voice_id")
            if not voice_id:
                logger.error("未提供有效的声音ID")
                return False

            # 调用ElevenLabs API生成语音
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/text-to-speech/{voice_id}",
                    headers={
                        "xi-api-key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json={
                        "text": text,
                        "model_id": "eleven_multilingual_v2",
                        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                    },
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"ElevenLabs API错误: {error_text}")
                        return False

                    # 保存音频文件
                    audio_data = await response.read()
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(audio_data)

                    logger.info(f"语音生成完成，已保存到: {output_path}")
                    return True
        except Exception as e:
            logger.error(f"语音生成失败: {str(e)}")
            return False

    async def _create_voice_from_audio(self, audio_path: str) -> str:
        """从音频文件创建ElevenLabs声音ID"""
        try:
            # 准备音频数据
            with open(audio_path, "rb") as f:
                audio_data = f.read()

            # 生成唯一名称
            voice_name = f"custom_voice_{uuid.uuid4().hex[:8]}"

            # 调用ElevenLabs API创建声音
            async with aiohttp.ClientSession() as session:
                # 创建表单数据
                form_data = aiohttp.FormData()
                form_data.add_field("name", voice_name)
                form_data.add_field(
                    "description", "Custom voice created from audio sample"
                )
                form_data.add_field(
                    "files",
                    audio_data,
                    filename=os.path.basename(audio_path),
                    content_type="audio/mpeg",
                )

                async with session.post(
                    f"{self.api_url}/voices/add",
                    headers={"xi-api-key": self.api_key},
                    data=form_data,
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"创建声音失败: {error_text}")
                        return ""

                    result = await response.json()
                    voice_id = result.get("voice_id", "")

                    if voice_id:
                        logger.info(f"成功创建声音ID: {voice_id}")
                        return voice_id
                    else:
                        logger.error("未能获取声音ID")
                        return ""
        except Exception as e:
            logger.error(f"创建声音失败: {str(e)}")
            return ""


class LipSyncService:
    """唇形同步服务类"""

    def __init__(self):
        self.api_key = api_config.sync_labs_api_key
        self.api_url = api_config.sync_labs_endpoint
        self.available = api_config.sync_labs_available

        if not self.available:
            logger.warning("SyncLabs服务不可用，请检查API密钥配置")

    async def sync_video_with_audio(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        sync_quality: str = "high",
    ):
        """同步视频和音频"""
        if not self.available:
            logger.error("SyncLabs API未配置，无法进行唇形同步")
            return False

        try:
            # 准备视频和音频数据
            video_data = await self._prepare_file_data(video_path)
            audio_data = await self._prepare_file_data(audio_path)

            # 调用SyncLabs API进行唇形同步
            async with aiohttp.ClientSession() as session:
                # 创建任务
                async with session.post(
                    f"{self.api_url}/sync",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "video": video_data,
                        "audio": audio_data,
                        "quality": sync_quality,
                    },
                ) as response:
                    if response.status != 202:  # 202 Accepted
                        error_text = await response.text()
                        logger.error(f"SyncLabs API错误: {error_text}")
                        return False

                    result = await response.json()
                    task_id = result.get("id")

                    if not task_id:
                        logger.error("未能获取任务ID")
                        return False

                # 轮询任务状态
                status = "processing"
                while status == "processing":
                    await asyncio.sleep(5)  # 每5秒检查一次

                    async with session.get(
                        f"{self.api_url}/sync/{task_id}",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                    ) as status_response:
                        if status_response.status != 200:
                            error_text = await status_response.text()
                            logger.error(f"获取任务状态失败: {error_text}")
                            return False

                        status_result = await status_response.json()
                        status = status_result.get("status", "")

                        if status == "failed":
                            logger.error(
                                f"唇形同步任务失败: {status_result.get('error', '')}"
                            )
                            return False
                        elif status == "completed":
                            # 下载处理后的视频
                            video_url = status_result.get("output", {}).get("video", "")
                            if not video_url:
                                logger.error("未能获取处理后的视频URL")
                                return False

                            # 下载视频
                            async with session.get(video_url) as video_response:
                                if video_response.status != 200:
                                    logger.error("下载处理后的视频失败")
                                    return False

                                video_data = await video_response.read()

                                # 保存到输出路径
                                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                                with open(output_path, "wb") as f:
                                    f.write(video_data)

                                logger.info(f"唇形同步完成，已保存到: {output_path}")
                                return True

            return False
        except Exception as e:
            logger.error(f"唇形同步失败: {str(e)}")
            return False

    async def _prepare_file_data(self, file_path: str) -> str:
        """准备文件数据用于API请求"""
        # 对于SyncLabs API，我们需要将文件转换为base64或上传到临时URL
        # 这里简化处理，假设API接受文件路径
        # 实际实现可能需要根据API要求进行调整
        return file_path


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


class SubtitleRemovalService:
    def __init__(self):
        self.models = {
            "fast": "LaMa",
            "quality": "RunwayML",
            "balanced": "SD-Inpainting",
        }
        # 暂时注释掉 paddleocr
        # self.ocr = PaddleOCR(use_angle_cls=True, lang="ch")

    async def remove_subtitles(
        self,
        input_path: str,
        output_path: str,
        mode: str = "balanced",
        selected_area: dict = None,
        auto_detect: bool = False,
        progress_callback: callable = None,
    ):
        """移除视频中的字幕"""
        try:
            if auto_detect:
                # 暂时注释掉OCR相关代码
                # result = self.ocr.ocr(input_path)
                # text_areas = self._extract_text_areas(result)
                # logger.info(f"检测到 {len(text_areas)} 个文字区域")
                logger.warning("Auto detection is currently not available")
                pass

            model = self.models[mode]
            logger.info(f"使用模型 {model} 移除字幕")

            # 实际的字幕移除处理
            if model == "LaMa":
                await self._process_with_lama(
                    input_path, output_path, selected_area or text_areas
                )
            elif model == "SD-Inpainting":
                await self._process_with_sd(
                    input_path, output_path, selected_area or text_areas
                )

            return True
        except Exception as e:
            logger.error(f"字幕移除失败: {str(e)}")
            raise

    def _extract_text_areas(self, ocr_result):
        text_areas = []
        for line in ocr_result:
            points = line[0]
            text_areas.append(
                {
                    "x": min(p[0] for p in points),
                    "y": min(p[1] for p in points),
                    "width": max(p[0] for p in points) - min(p[0] for p in points),
                    "height": max(p[1] for p in points) - min(p[1] for p in points),
                }
            )
        return text_areas


class EnhancedVoiceService:
    def __init__(self):
        self.available_models = {
            "chinese": {"fast": "VITS", "quality": "YourTTS"},
            "english": {"fast": "Coqui", "quality": "MockingBird"},
        }
        # 暂时注释掉
        # self.voice_encoder = VoiceEncoder()
        logger.warning("Voice encoder is not available, some features will be limited")

    async def clone_voice(
        self,
        text: str,
        reference_audio: str,
        output_path: str,
        language: str = "chinese",
        quality: str = "quality",
        progress_callback: callable = None,
    ):
        try:
            model = self.available_models[language][quality]
            logger.info(f"使用模型 {model} 进行语音克隆")
            logger.warning("Voice cloning is currently not available")
            return False
        except Exception as e:
            logger.error(f"语音克隆失败: {str(e)}")
            raise


class EnhancedLipSyncService:
    def __init__(self):
        self.models = {
            "fast": "Wav2Lip",
            "quality": "SadTalker",
            "realistic": "GeneFace",
        }
        # 暂时注释掉
        # self.face_aligner = face_alignment.FaceAlignment(
        #     face_alignment.LandmarksType._2D
        # )
        logger.warning("Face alignment is not available, some features will be limited")

    async def sync_lip(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        mode: str = "quality",
        language: str = "chinese",
        enhance_quality: bool = True,
        progress_callback: callable = None,
    ):
        try:
            model = self.models[mode]
            logger.info(f"使用模型 {model} 进行唇形同步")
            logger.warning("Lip sync is currently not available")
            return False
        except Exception as e:
            logger.error(f"唇形同步失败: {str(e)}")
            raise


class VideoProcessor:
    """视频处理器类"""

    def __init__(self):
        # 初始化各种服务
        self.runway_service = RunwayMLService()
        self.voice_service = VoiceCloningService()
        self.lip_sync_service = LipSyncService()
        self.subtitle_service = SubtitleService()

        # 默认使用云服务处理
        self.processing_mode = ProcessingMode.CLOUD

        # 检查GPU可用性（用于本地处理）
        self.gpu_available = self._check_gpu_memory() > 0
        if not self.gpu_available:
            logger.info("未检测到可用GPU，将使用云服务处理")

    async def process_video(
        self,
        input_video: str,
        text: str,
        options: dict,
        progress_callback: callable = None,
    ):
        """处理视频"""
        try:
            # 获取处理模式
            mode = options.get("processing_mode", ProcessingMode.CLOUD)

            # 根据处理模式选择处理方法
            if mode == ProcessingMode.CLOUD:
                return await self._process_with_cloud(
                    input_video, text, options, progress_callback
                )
            else:
                # TODO: 实现本地处理逻辑
                logger.warning("本地处理模式尚未实现，将使用云服务处理")
                return await self._process_with_cloud(
                    input_video, text, options, progress_callback
                )
        except Exception as e:
            logger.error(f"视频处理失败: {str(e)}")
            if progress_callback:
                progress_callback(100, "失败", str(e))
            return False

    async def _process_with_cloud(
        self,
        input_video: str,
        text: str,
        options: dict,
        progress_callback: callable = None,
    ):
        """使用云服务处理视频"""
        try:
            # 解析选项
            task_type = options.get("task_type", "subtitle_removal")
            output_path = options.get("output_path", "")

            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 根据任务类型选择处理方法
            if task_type == "subtitle_removal":
                # 字幕去除
                if progress_callback:
                    progress_callback(10, "正在检测字幕区域")

                # 检测字幕区域
                selected_area = options.get("selected_area")
                auto_detect = options.get("auto_detect", False)

                if progress_callback:
                    progress_callback(30, "正在去除字幕")

                # 使用RunwayML API去除字幕
                result = await self.runway_service.inpaint_video(
                    input_video,
                    output_path,
                    mask_type="text",
                    restoration_quality=options.get("quality", "high"),
                    selected_area=selected_area,
                    auto_detect=auto_detect,
                )

                if progress_callback:
                    progress_callback(100, "完成" if result else "失败")

                return result

            elif task_type == "voice_cloning":
                # 语音克隆
                if progress_callback:
                    progress_callback(10, "正在提取声音特征")

                # 提取声音特征
                reference_audio = options.get("reference_audio", "")
                voice_features = await self.voice_service.extract_voice_features(
                    reference_audio
                )

                if not voice_features:
                    if progress_callback:
                        progress_callback(100, "失败", "无法提取声音特征")
                    return False

                if progress_callback:
                    progress_callback(50, "正在生成语音")

                # 生成语音
                result = await self.voice_service.generate_speech(
                    text, voice_features, output_path
                )

                if progress_callback:
                    progress_callback(100, "完成" if result else "失败")

                return result

            elif task_type == "lip_sync":
                # 唇形同步
                if progress_callback:
                    progress_callback(10, "正在准备音频")

                # 获取音频路径
                audio_path = options.get("audio_path", "")

                if progress_callback:
                    progress_callback(30, "正在进行唇形同步")

                # 使用SyncLabs API进行唇形同步
                result = await self.lip_sync_service.sync_video_with_audio(
                    input_video,
                    audio_path,
                    output_path,
                    sync_quality=options.get("quality", "high"),
                )

                if progress_callback:
                    progress_callback(100, "完成" if result else "失败")

                return result

            else:
                logger.error(f"不支持的任务类型: {task_type}")
                if progress_callback:
                    progress_callback(100, "失败", f"不支持的任务类型: {task_type}")
                return False

        except Exception as e:
            logger.error(f"云服务处理失败: {str(e)}")
            if progress_callback:
                progress_callback(100, "失败", str(e))
            return False

    async def _process_locally(
        self,
        input_video: str,
        text: str,
        options: dict,
        progress_callback: callable = None,
    ):
        """使用本地处理视频（TODO）"""
        # TODO: 实现本地处理逻辑
        logger.warning("本地处理功能尚未实现")
        if progress_callback:
            progress_callback(100, "失败", "本地处理功能尚未实现")
        return False

    def _check_gpu_memory(self) -> int:
        """检查GPU可用内存"""
        try:
            if torch.cuda.is_available():
                # 获取当前设备
                device = torch.cuda.current_device()
                # 获取总内存（字节）
                total_memory = torch.cuda.get_device_properties(device).total_memory
                # 获取已分配内存（字节）
                allocated_memory = torch.cuda.memory_allocated(device)
                # 计算可用内存（GB）
                available_memory = (total_memory - allocated_memory) / (1024**3)

                logger.info(f"检测到GPU: {torch.cuda.get_device_name(device)}")
                logger.info(f"可用GPU内存: {available_memory:.2f} GB")

                return available_memory
            else:
                logger.info("未检测到可用GPU")
                return 0
        except Exception as e:
            logger.error(f"检查GPU内存失败: {str(e)}")
            return 0

    def _determine_quality(self, available_memory: int) -> str:
        """根据可用内存确定处理质量"""
        if available_memory >= 8:
            return "high"
        elif available_memory >= 4:
            return "medium"
        else:
            return "low"
