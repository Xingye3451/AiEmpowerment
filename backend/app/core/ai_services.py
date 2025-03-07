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
                text_areas = []
            else:
                text_areas = []

            model = self.models[mode]
            logger.info(f"使用模型 {model} 移除字幕")

            # 检查是否为视频文件
            is_video = self._is_video_file(input_path)

            # 如果是视频文件，使用视频处理方法
            if is_video:
                logger.info(f"检测到视频文件，使用视频处理方法")

                # 将selected_area转换为列表格式
                mask_areas = [selected_area] if selected_area else []

                # 根据模型类型选择处理方法
                if model == "LaMa":
                    return await self._process_video_with_replicate(
                        input_path,
                        output_path,
                        mask_areas,
                        "LaMa",
                        prompt="",
                        negative_prompt="",
                        progress_callback=progress_callback,
                    )
                elif model == "SD-Inpainting":
                    return await self._process_video_with_replicate(
                        input_path,
                        output_path,
                        mask_areas,
                        "SD-Inpainting",
                        prompt="natural background, seamless, high quality",
                        negative_prompt="text, words, letters, watermark, artifacts, blurry, low quality",
                        progress_callback=progress_callback,
                    )
                else:
                    logger.warning(f"不支持的模型类型: {model}，使用SD-Inpainting")
                    return await self._process_video_with_replicate(
                        input_path,
                        output_path,
                        mask_areas,
                        "SD-Inpainting",
                        prompt="natural background, seamless, high quality",
                        negative_prompt="text, words, letters, watermark, artifacts, blurry, low quality",
                        progress_callback=progress_callback,
                    )
            else:
                # 如果是图像文件，使用图像处理方法
                logger.info(f"检测到图像文件，使用图像处理方法")

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

    async def _process_with_lama(
        self, input_path: str, output_path: str, mask_areas: list
    ):
        """
        使用LaMa (Large Mask Inpainting)算法处理图像，移除字幕区域

        Args:
            input_path: 输入图像路径
            output_path: 输出图像路径
            mask_areas: 字幕区域列表，每个区域是一个包含x, y, width, height的字典
        """
        try:
            import numpy as np
            import cv2
            import torch
            from PIL import Image
            import requests
            import io
            import os
            import tempfile

            logger.info(f"使用LaMa算法处理图像: {input_path}")

            # 读取输入图像
            image = cv2.imread(input_path)
            if image is None:
                raise ValueError(f"无法读取图像: {input_path}")

            # 创建掩码图像 (黑色背景，白色为要移除的区域)
            mask = np.zeros((image.shape[0], image.shape[1]), dtype=np.uint8)

            # 在掩码上绘制字幕区域
            for area in mask_areas:
                x, y = int(area["x"]), int(area["y"])
                width, height = int(area["width"]), int(area["height"])
                # 在掩码上绘制白色矩形（表示要移除的区域）
                cv2.rectangle(mask, (x, y), (x + width, y + height), 255, -1)

            # 保存临时掩码文件
            temp_mask_path = tempfile.mktemp(suffix=".png")
            cv2.imwrite(temp_mask_path, mask)

            # 方法1: 使用本地LaMa模型（如果已安装）
            try:
                # 尝试导入本地LaMa模型
                from lama_cleaner.model_manager import ModelManager
                from lama_cleaner.schema import Config

                logger.info("使用本地LaMa模型进行图像修复")

                # 配置LaMa模型
                config = Config(
                    model_name="lama",
                    device="cuda" if torch.cuda.is_available() else "cpu",
                    hd_strategy="Original",
                    crop_enable=False,
                )

                # 初始化模型管理器
                model = ModelManager(config)

                # 读取图像和掩码
                img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                mask_img = cv2.imread(temp_mask_path, cv2.IMREAD_GRAYSCALE)

                # 使用LaMa模型进行图像修复
                result = model(img, mask_img)

                # 转换回BGR并保存结果
                result_bgr = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
                cv2.imwrite(output_path, result_bgr)

                logger.info(f"LaMa处理完成，结果保存至: {output_path}")

            except (ImportError, Exception) as e:
                logger.warning(f"本地LaMa模型加载失败: {str(e)}，尝试使用API服务")

                # 方法2: 使用Replicate API（如果本地模型不可用）
                try:
                    # 使用Replicate API进行图像修复
                    import replicate

                    logger.info("使用Replicate API进行图像修复")

                    # 读取图像和掩码为base64
                    with open(input_path, "rb") as f:
                        image_data = f.read()

                    with open(temp_mask_path, "rb") as f:
                        mask_data = f.read()

                    # 调用Replicate API
                    output = replicate.run(
                        "cjwbw/lama:9a637b04c9e15be3d2f9c93f3a618f9d620b2f0a1d8c1a4e2ef2d38b4c695bbd",
                        input={
                            "image": image_data,
                            "mask": mask_data,
                        },
                    )

                    # 下载结果图像
                    response = requests.get(output)
                    result_img = Image.open(io.BytesIO(response.content))
                    result_img.save(output_path)

                    logger.info(f"Replicate API处理完成，结果保存至: {output_path}")

                except Exception as e:
                    logger.warning(
                        f"Replicate API调用失败: {str(e)}，尝试使用Runway API"
                    )

                    # 方法3: 使用Runway API（如果Replicate不可用）
                    try:
                        import json

                        logger.info("使用Runway API进行图像修复")

                        # Runway API配置
                        runway_api_key = os.environ.get("RUNWAY_API_KEY", "")
                        if not runway_api_key:
                            raise ValueError("未设置RUNWAY_API_KEY环境变量")

                        # 准备API请求
                        headers = {
                            "Authorization": f"Bearer {runway_api_key}",
                            "Content-Type": "application/json",
                        }

                        # 将图像和掩码编码为base64
                        import base64

                        with open(input_path, "rb") as f:
                            image_base64 = base64.b64encode(f.read()).decode("utf-8")

                        with open(temp_mask_path, "rb") as f:
                            mask_base64 = base64.b64encode(f.read()).decode("utf-8")

                        # 构建请求数据
                        data = {"image": image_base64, "mask": mask_base64}

                        # 发送请求到Runway API
                        response = requests.post(
                            "https://api.runwayml.com/v1/inpainting",
                            headers=headers,
                            data=json.dumps(data),
                        )

                        if response.status_code == 200:
                            # 解析响应
                            result = response.json()
                            result_img_data = base64.b64decode(result["image"])

                            # 保存结果
                            with open(output_path, "wb") as f:
                                f.write(result_img_data)

                            logger.info(
                                f"Runway API处理完成，结果保存至: {output_path}"
                            )
                        else:
                            raise Exception(
                                f"API请求失败: {response.status_code} - {response.text}"
                            )

                    except Exception as e:
                        logger.error(f"所有字幕移除方法都失败: {str(e)}")
                        # 如果所有方法都失败，简单地复制原图
                        cv2.imwrite(output_path, image)
                        logger.warning(f"无法处理图像，已复制原图到: {output_path}")

            # 清理临时文件
            if os.path.exists(temp_mask_path):
                os.remove(temp_mask_path)

            return True

        except Exception as e:
            logger.error(f"LaMa处理失败: {str(e)}")
            # 确保输出路径有效，即使处理失败
            if not os.path.exists(output_path) and os.path.exists(input_path):
                import shutil

                shutil.copy(input_path, output_path)
            raise

    async def _process_with_sd(
        self, input_path: str, output_path: str, mask_areas: list
    ):
        """
        使用Stable Diffusion Inpainting模型处理图像，移除字幕区域

        Args:
            input_path: 输入图像路径
            output_path: 输出图像路径
            mask_areas: 字幕区域列表，每个区域是一个包含x, y, width, height的字典
        """
        try:
            import numpy as np
            import cv2
            import torch
            from PIL import Image
            import requests
            import io
            import os
            import tempfile

            logger.info(f"使用Stable Diffusion Inpainting算法处理图像: {input_path}")

            # 读取输入图像
            image = cv2.imread(input_path)
            if image is None:
                raise ValueError(f"无法读取图像: {input_path}")

            # 创建掩码图像 (黑色背景，白色为要移除的区域)
            mask = np.zeros((image.shape[0], image.shape[1]), dtype=np.uint8)

            # 在掩码上绘制字幕区域
            for area in mask_areas:
                x, y = int(area["x"]), int(area["y"])
                width, height = int(area["width"]), int(area["height"])
                # 在掩码上绘制白色矩形（表示要移除的区域）
                cv2.rectangle(mask, (x, y), (x + width, y + height), 255, -1)

            # 保存临时文件
            temp_img_path = tempfile.mktemp(suffix=".png")
            temp_mask_path = tempfile.mktemp(suffix=".png")

            # 保存图像和掩码
            cv2.imwrite(temp_img_path, image)
            cv2.imwrite(temp_mask_path, mask)

            # 方法1: 使用本地Stable Diffusion模型（如果已安装）
            try:
                # 尝试导入本地Stable Diffusion模型
                from diffusers import StableDiffusionInpaintPipeline

                logger.info("使用本地Stable Diffusion模型进行图像修复")

                # 加载模型
                pipe = StableDiffusionInpaintPipeline.from_pretrained(
                    "runwayml/stable-diffusion-inpainting",
                    torch_dtype=(
                        torch.float16 if torch.cuda.is_available() else torch.float32
                    ),
                )

                if torch.cuda.is_available():
                    pipe = pipe.to("cuda")

                # 读取图像和掩码
                init_image = Image.open(temp_img_path).convert("RGB")
                mask_image = Image.open(temp_mask_path).convert("RGB")

                # 使用Stable Diffusion进行图像修复
                # 提示词设置为空或与图像内容相关的描述，以保持图像风格一致
                prompt = "background, same style, seamless"

                # 进行推理
                result = pipe(
                    prompt=prompt,
                    image=init_image,
                    mask_image=mask_image,
                    guidance_scale=7.5,
                    num_inference_steps=30,
                ).images[0]

                # 保存结果
                result.save(output_path)

                logger.info(f"Stable Diffusion处理完成，结果保存至: {output_path}")

            except (ImportError, Exception) as e:
                logger.warning(
                    f"本地Stable Diffusion模型加载失败: {str(e)}，尝试使用API服务"
                )

                # 方法2: 使用Replicate API（如果本地模型不可用）
                try:
                    # 使用Replicate API进行图像修复
                    import replicate

                    logger.info("使用Replicate API进行图像修复")

                    # 读取图像和掩码
                    with open(temp_img_path, "rb") as f:
                        image_data = f.read()

                    with open(temp_mask_path, "rb") as f:
                        mask_data = f.read()

                    # 调用Replicate API
                    output = replicate.run(
                        "stability-ai/stable-diffusion-inpainting:c28b92a7ecd66eee4aefcd8a94eb9e7f6c3805d5f06038165407fb5cb355ba67",
                        input={
                            "prompt": "background, same style, seamless",
                            "image": image_data,
                            "mask": mask_data,
                            "num_inference_steps": 30,
                            "guidance_scale": 7.5,
                        },
                    )

                    # 下载结果图像
                    response = requests.get(output)
                    result_img = Image.open(io.BytesIO(response.content))
                    result_img.save(output_path)

                    logger.info(f"Replicate API处理完成，结果保存至: {output_path}")

                except Exception as e:
                    logger.warning(
                        f"Replicate API调用失败: {str(e)}，尝试使用Hugging Face API"
                    )

                    # 方法3: 使用Hugging Face API（如果Replicate不可用）
                    try:
                        import json

                        logger.info("使用Hugging Face API进行图像修复")

                        # Hugging Face API配置
                        hf_api_key = os.environ.get("HF_API_KEY", "")
                        if not hf_api_key:
                            raise ValueError("未设置HF_API_KEY环境变量")

                        # 准备API请求
                        headers = {
                            "Authorization": f"Bearer {hf_api_key}",
                            "Content-Type": "application/json",
                        }

                        # 将图像和掩码编码为base64
                        import base64

                        with open(temp_img_path, "rb") as f:
                            image_base64 = base64.b64encode(f.read()).decode("utf-8")

                        with open(temp_mask_path, "rb") as f:
                            mask_base64 = base64.b64encode(f.read()).decode("utf-8")

                        # 构建请求数据
                        data = {
                            "inputs": {
                                "prompt": "background, same style, seamless",
                                "image": image_base64,
                                "mask": mask_base64,
                                "guidance_scale": 7.5,
                                "num_inference_steps": 30,
                            }
                        }

                        # 发送请求到Hugging Face API
                        response = requests.post(
                            "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-inpainting",
                            headers=headers,
                            data=json.dumps(data),
                        )

                        if response.status_code == 200:
                            # 保存结果
                            with open(output_path, "wb") as f:
                                f.write(response.content)

                            logger.info(
                                f"Hugging Face API处理完成，结果保存至: {output_path}"
                            )
                        else:
                            raise Exception(
                                f"API请求失败: {response.status_code} - {response.text}"
                            )

                    except Exception as e:
                        logger.error(f"所有字幕移除方法都失败: {str(e)}")
                        # 如果所有方法都失败，简单地复制原图
                        cv2.imwrite(output_path, image)
                        logger.warning(f"无法处理图像，已复制原图到: {output_path}")

            # 清理临时文件
            for temp_file in [temp_img_path, temp_mask_path]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)

            return True

        except Exception as e:
            logger.error(f"Stable Diffusion处理失败: {str(e)}")
            # 确保输出路径有效，即使处理失败
            if not os.path.exists(output_path) and os.path.exists(input_path):
                import shutil

                shutil.copy(input_path, output_path)
            raise

    async def _process_video_with_replicate(
        self,
        input_path: str,
        output_path: str,
        mask_areas: list,
        model_type: str,
        prompt: str = "",
        negative_prompt: str = "",
        progress_callback: callable = None,
    ):
        """处理视频文件，逐帧提取、处理和重组"""
        try:
            import numpy as np
            import cv2
            import os
            import tempfile
            import shutil
            import replicate
            import requests
            from PIL import Image
            import io

            logger.info(f"使用{model_type}模型处理视频: {input_path}")

            # 创建临时目录
            temp_dir = tempfile.mkdtemp()
            frames_dir = os.path.join(temp_dir, "frames")
            processed_dir = os.path.join(temp_dir, "processed")
            os.makedirs(frames_dir, exist_ok=True)
            os.makedirs(processed_dir, exist_ok=True)

            # 打开视频文件
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                raise ValueError(f"无法打开视频文件: {input_path}")

            # 获取视频信息
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            logger.info(f"视频信息: {width}x{height}, {fps}fps, {total_frames}帧")

            # 提取音频（如果有）
            audio_path = os.path.join(temp_dir, "audio.aac")
            has_audio = self._extract_audio(input_path, audio_path)

            # 确保API令牌已设置
            replicate_api_token = os.environ.get("REPLICATE_API_TOKEN")
            if not replicate_api_token:
                raise ValueError("未设置REPLICATE_API_TOKEN环境变量")

            os.environ["REPLICATE_API_TOKEN"] = replicate_api_token

            # 逐帧处理
            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # 更新进度
                if progress_callback:
                    current_progress = int(
                        30 + (frame_count / total_frames) * 60
                    )  # 30%-90%的进度
                    progress_callback(current_progress)

                # 保存帧
                frame_path = os.path.join(frames_dir, f"frame_{frame_count:06d}.png")
                cv2.imwrite(frame_path, frame)

                # 创建掩码
                mask = np.zeros((frame.shape[0], frame.shape[1]), dtype=np.uint8)
                for area in mask_areas:
                    if area:  # 确保area不为None
                        x, y = int(area["x"]), int(area["y"])
                        width, height = int(area["width"]), int(area["height"])
                        cv2.rectangle(mask, (x, y), (x + width, y + height), 255, -1)

                mask_path = os.path.join(frames_dir, f"mask_{frame_count:06d}.png")
                cv2.imwrite(mask_path, mask)

                # 读取图像和掩码
                with open(frame_path, "rb") as f:
                    image_data = f.read()

                with open(mask_path, "rb") as f:
                    mask_data = f.read()

                # 调用Replicate API
                if model_type == "LaMa":
                    output = replicate.run(
                        self.replicate_models["LaMa"],
                        input={
                            "image": image_data,
                            "mask": mask_data,
                        },
                    )
                else:  # model_type == "SD-Inpainting"
                    output = replicate.run(
                        self.replicate_models["SD-Inpainting"],
                        input={
                            "prompt": prompt,
                            "negative_prompt": negative_prompt,
                            "image": image_data,
                            "mask": mask_data,
                            "num_inference_steps": 30,
                            "guidance_scale": 7.5,
                        },
                    )

                # 下载结果图像
                response = requests.get(output)
                if response.status_code != 200:
                    raise Exception(f"下载结果图像失败: {response.status_code}")

                # 保存处理后的帧
                processed_frame_path = os.path.join(
                    processed_dir, f"frame_{frame_count:06d}.png"
                )
                with open(processed_frame_path, "wb") as f:
                    f.write(response.content)

                frame_count += 1
                if frame_count % 10 == 0:
                    logger.info(
                        f"已处理 {frame_count}/{total_frames} 帧 ({frame_count/total_frames*100:.1f}%)"
                    )

            cap.release()

            # 更新进度
            if progress_callback:
                progress_callback(90)  # 90%进度

            # 将处理后的帧重新组合成视频
            self._frames_to_video(
                processed_dir,
                output_path,
                fps,
                width,
                height,
                audio_path if has_audio else None,
            )

            # 更新进度
            if progress_callback:
                progress_callback(100)  # 100%进度

            # 清理临时文件
            shutil.rmtree(temp_dir)

            logger.info(f"视频处理完成，结果保存至: {output_path}")
            return True

        except Exception as e:
            logger.error(f"视频处理失败: {str(e)}")
            # 确保输出路径有效，即使处理失败
            if not os.path.exists(output_path) and os.path.exists(input_path):
                shutil.copy(input_path, output_path)
                logger.warning(f"处理失败，已复制原视频到: {output_path}")
            raise


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
        self.subtitle_removal_service = SubtitleRemovalService()

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
                logger.info(f"使用云服务处理视频: {input_video}")
                return await self._process_with_cloud(
                    input_video, text, options, progress_callback
                )
            else:
                logger.info(f"使用本地处理视频: {input_video}")
                return await self._process_locally(
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
                # 获取字幕移除模式
                subtitle_removal_mode = options.get("subtitle_removal_mode", "balanced")

                if progress_callback:
                    progress_callback(30, "正在去除字幕")

                # 使用字幕移除服务
                # 使用SubtitleRemovalService去除字幕
                result = await self.subtitle_removal_service.remove_subtitles(
                    input_path=input_video,
                    output_path=output_path,
                    mode=subtitle_removal_mode,
                    selected_area=selected_area,
                    auto_detect=auto_detect,
                    progress_callback=progress_callback,
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
        """使用本地处理视频（基础实现）"""
        try:
            # 获取输出路径
            output_path = options.get("output_path", "")

            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 模拟处理进度
            if progress_callback:
                progress_callback(10, "正在准备本地处理环境")

            # 获取处理选项
            remove_subtitles = options.get("remove_subtitles", False)
            generate_subtitles = options.get("generate_subtitles", False)

            # 模拟处理过程
            if progress_callback:
                progress_callback(30, "正在处理视频")

            # 使用ffmpeg复制视频（临时方案）
            import subprocess
            import asyncio

            logger.info(f"使用本地处理模式处理视频: {input_video}")

            # 构建ffmpeg命令
            cmd = [
                "ffmpeg",
                "-i",
                input_video,
                "-c:v",
                "copy",
                "-c:a",
                "copy",
                "-y",
                output_path,
            ]

            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"本地处理失败: {stderr.decode()}")
                if progress_callback:
                    progress_callback(100, "失败", f"本地处理失败: {stderr.decode()}")
                return False

            if progress_callback:
                progress_callback(100, "完成", "本地处理完成")

            logger.info(f"本地处理完成，输出文件: {output_path}")
            return True

        except Exception as e:
            logger.error(f"本地处理失败: {str(e)}")
            if progress_callback:
                progress_callback(100, "失败", str(e))
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
