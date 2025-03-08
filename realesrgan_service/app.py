import os
import uuid
import subprocess
import tempfile
import shutil
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("realesrgan-service")

app = FastAPI(title="Real-ESRGAN API Service")

# 配置
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/app/uploads/temp")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/app/uploads/processed_videos")
MODELS_DIR = os.environ.get("MODELS_DIR", "/app/models")

# 确保目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# 可用模型
AVAILABLE_MODELS = {
    "realesrgan-x4plus": {
        "name": "通用模型",
        "description": "适用于各种真实照片和视频的超分辨率处理",
        "path": os.path.join(MODELS_DIR, "RealESRGAN_x4plus.pth"),
        "max_scale": 4,
    },
    "realesrgan-x4plus-anime": {
        "name": "动漫模型",
        "description": "专为动漫内容优化的超分辨率模型",
        "path": os.path.join(MODELS_DIR, "RealESRGAN_x4plus_anime_6B.pth"),
        "max_scale": 4,
    },
    "realesrgan-x2plus": {
        "name": "2倍通用模型",
        "description": "适用于2倍放大的通用模型",
        "path": os.path.join(MODELS_DIR, "RealESRGAN_x2plus.pth"),
        "max_scale": 2,
    },
}


@app.get("/")
async def root():
    return {"message": "Real-ESRGAN API Service"}


@app.get("/status")
async def status():
    # 检查CUDA是否可用
    try:
        import torch

        cuda_available = torch.cuda.is_available()
        device_count = torch.cuda.device_count() if cuda_available else 0
        device_info = []

        for i in range(device_count):
            device_info.append(
                {
                    "index": i,
                    "name": torch.cuda.get_device_name(i),
                    "memory": torch.cuda.get_device_properties(i).total_memory,
                }
            )

        # 检查模型文件是否存在
        models = []
        for model_id, model_info in AVAILABLE_MODELS.items():
            model_exists = os.path.exists(model_info["path"])
            if model_exists:
                models.append(model_id)

        return {
            "status": "running",
            "cuda_available": cuda_available,
            "device_count": device_count,
            "device_info": device_info,
            "models": models,
        }
    except Exception as e:
        logger.error(f"检查状态失败: {str(e)}")
        return {"status": "error", "message": str(e), "models": []}


@app.post("/enhance_video")
async def enhance_video(
    video: UploadFile = File(...),
    scale: str = Form("2"),
    model_name: str = Form("realesrgan-x4plus"),
    denoise_strength: str = Form("0.5"),
    task_id: str = Form(None),
):
    try:
        # 验证参数
        try:
            scale_value = int(scale)
            if scale_value not in [2, 3, 4]:
                raise ValueError("放大倍数必须是2、3或4")
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的放大倍数")

        try:
            denoise_value = float(denoise_strength)
            if not (0 <= denoise_value <= 1):
                raise ValueError("降噪强度必须在0到1之间")
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的降噪强度")

        if model_name not in AVAILABLE_MODELS:
            raise HTTPException(status_code=400, detail=f"未知的模型: {model_name}")

        # 检查模型文件是否存在
        model_path = AVAILABLE_MODELS[model_name]["path"]
        if not os.path.exists(model_path):
            raise HTTPException(status_code=500, detail=f"模型文件不存在: {model_name}")

        # 检查模型支持的最大放大倍数
        max_scale = AVAILABLE_MODELS[model_name]["max_scale"]
        if scale_value > max_scale:
            raise HTTPException(
                status_code=400, detail=f"模型 {model_name} 最大支持 {max_scale} 倍放大"
            )

        # 生成任务ID
        if not task_id:
            task_id = str(uuid.uuid4())

        # 创建任务目录
        task_dir = os.path.join(UPLOAD_DIR, task_id)
        os.makedirs(task_dir, exist_ok=True)

        # 保存上传的视频
        video_path = os.path.join(task_dir, f"original_{video.filename}")
        with open(video_path, "wb") as f:
            f.write(await video.read())

        logger.info(f"视频已保存: {video_path}")

        # 创建输出目录
        frames_dir = os.path.join(task_dir, "frames")
        enhanced_frames_dir = os.path.join(task_dir, "enhanced_frames")
        os.makedirs(frames_dir, exist_ok=True)
        os.makedirs(enhanced_frames_dir, exist_ok=True)

        # 提取视频帧
        logger.info("开始提取视频帧")
        extract_cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-vf",
            "fps=24",  # 固定帧率为24fps
            os.path.join(frames_dir, "frame_%05d.png"),
        ]

        extract_process = subprocess.run(
            extract_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        if extract_process.returncode != 0:
            error_msg = extract_process.stderr.decode()
            logger.error(f"提取视频帧失败: {error_msg}")
            raise HTTPException(status_code=500, detail=f"提取视频帧失败: {error_msg}")

        # 获取所有帧
        frames = sorted([f for f in os.listdir(frames_dir) if f.endswith(".png")])
        total_frames = len(frames)

        if total_frames == 0:
            raise HTTPException(status_code=500, detail="未能提取到视频帧")

        logger.info(f"共提取到 {total_frames} 帧")

        # 使用Real-ESRGAN处理每一帧
        logger.info("开始处理视频帧")
        for i, frame in enumerate(frames):
            frame_path = os.path.join(frames_dir, frame)
            output_path = os.path.join(enhanced_frames_dir, frame)

            # 构建Real-ESRGAN命令
            enhance_cmd = [
                "python",
                "-m",
                "realesrgan.inference_realesrgan",
                "-i",
                frame_path,
                "-o",
                enhanced_frames_dir,
                "-n",
                model_name,
                "-s",
                str(scale_value),
                "--face_enhance",  # 启用面部增强
                "--fp32",  # 使用FP32精度
                "--denoise_strength",
                str(denoise_value),
            ]

            enhance_process = subprocess.run(
                enhance_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            if enhance_process.returncode != 0:
                error_msg = enhance_process.stderr.decode()
                logger.error(f"处理帧 {frame} 失败: {error_msg}")
                raise HTTPException(status_code=500, detail=f"处理帧失败: {error_msg}")

            logger.info(f"已处理 {i+1}/{total_frames} 帧")

        # 提取原始视频的音频
        logger.info("提取音频")
        audio_path = os.path.join(task_dir, "audio.wav")
        extract_audio_cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "44100",
            "-ac",
            "2",
            audio_path,
        ]

        audio_process = subprocess.run(
            extract_audio_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        if audio_process.returncode != 0:
            error_msg = audio_process.stderr.decode()
            logger.error(f"提取音频失败: {error_msg}")
            # 继续处理，即使没有音频

        # 生成输出视频路径
        output_filename = f"enhanced_{os.path.basename(video_path)}"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        # 使用ffmpeg合成视频
        logger.info("合成增强视频")
        compose_cmd = [
            "ffmpeg",
            "-framerate",
            "24",  # 与提取时相同的帧率
            "-i",
            os.path.join(enhanced_frames_dir, "frame_%05d.png"),
        ]

        # 如果音频提取成功，添加音频
        if os.path.exists(audio_path):
            compose_cmd.extend(["-i", audio_path])

        compose_cmd.extend(
            [
                "-c:v",
                "libx264",
                "-crf",
                "18",  # 高质量编码
                "-preset",
                "medium",  # 平衡编码速度和质量
            ]
        )

        # 如果有音频，添加音频编码参数
        if os.path.exists(audio_path):
            compose_cmd.extend(["-c:a", "aac", "-b:a", "192k", "-shortest"])

        compose_cmd.append(output_path)

        compose_process = subprocess.run(
            compose_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        if compose_process.returncode != 0:
            error_msg = compose_process.stderr.decode()
            logger.error(f"合成视频失败: {error_msg}")
            raise HTTPException(status_code=500, detail=f"合成视频失败: {error_msg}")

        logger.info(f"视频处理完成: {output_path}")

        # 清理临时文件
        try:
            shutil.rmtree(frames_dir)
            shutil.rmtree(enhanced_frames_dir)
            if os.path.exists(audio_path):
                os.remove(audio_path)
            os.remove(video_path)
        except Exception as e:
            logger.warning(f"清理临时文件失败: {str(e)}")

        # 返回处理后的视频
        return FileResponse(
            output_path, media_type="video/mp4", filename=output_filename
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理视频失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理视频失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=6060)
