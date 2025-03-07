"""
视频处理服务类，用于处理视频的字幕擦除、音色提取、文字转语音和唇形同步功能。
"""

import os
import uuid
import json
import asyncio
import logging
import subprocess
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class VideoProcessingService:
    def __init__(self, base_dir: str, temp_dir: str, output_dir: str, voice_dir: str):
        """
        初始化视频处理服务

        Args:
            base_dir: 基础目录
            temp_dir: 临时文件目录
            output_dir: 输出文件目录
            voice_dir: 音色文件目录
        """
        self.base_dir = base_dir
        self.temp_dir = temp_dir
        self.output_dir = output_dir
        self.voice_dir = voice_dir

        # 确保目录存在
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.voice_dir, exist_ok=True)

        # 任务状态存储
        self.tasks = {}

    async def process_video(
        self,
        task_id: str,
        task_data: Dict[str, Any],
        progress_callback: Optional[
            Callable[[str, int, str, Dict[str, Any]], None]
        ] = None,
    ) -> Dict[str, Any]:
        """
        处理视频的完整流程

        Args:
            task_id: 任务ID
            task_data: 任务数据
            progress_callback: 进度回调函数

        Returns:
            包含处理结果的字典
        """
        # 创建任务目录
        task_dir = os.path.join(self.temp_dir, task_id)
        os.makedirs(task_dir, exist_ok=True)

        # 初始化任务状态
        self.tasks[task_id] = {
            "status": "initialized",
            "progress": 0,
            "message": "任务初始化完成",
            "task_data": task_data,
            "task_dir": task_dir,
            "output_paths": {},
            "start_time": datetime.now(),
            "end_time": None,
        }

        try:
            # 获取原始视频路径
            video_path = task_data.get("original_path")
            if not video_path or not os.path.exists(video_path):
                raise ValueError(f"原始视频文件不存在: {video_path}")

            # 更新进度
            await self._update_progress(
                task_id, 0, "开始处理视频", {}, progress_callback
            )

            # 获取处理流程
            pipeline = task_data.get("processing_pipeline", [])
            if not pipeline:
                raise ValueError("未指定处理流程")

            # 当前视频路径（会在处理过程中更新）
            current_video_path = video_path

            # 处理流程执行
            total_steps = len(pipeline)
            progress_per_step = 85 / total_steps  # 预留15%用于最终处理

            for i, step in enumerate(pipeline):
                step_start_progress = i * progress_per_step
                step_end_progress = (i + 1) * progress_per_step

                if step == "subtitle_removal":
                    # 字幕擦除
                    await self._update_progress(
                        task_id,
                        step_start_progress,
                        "开始擦除字幕",
                        {"current_stage": "subtitle_removal"},
                        progress_callback,
                    )
                    no_subtitle_video = await self._remove_subtitles(
                        current_video_path,
                        task_dir,
                        task_id,
                        task_data.get("subtitle_removal_mode", "balanced"),
                        task_data.get("selected_area"),
                        task_data.get("auto_detect", False),
                        step_start_progress,
                        step_end_progress,
                        progress_callback,
                    )
                    current_video_path = no_subtitle_video
                    self.tasks[task_id]["output_paths"][
                        "no_subtitle_video"
                    ] = no_subtitle_video

                elif step == "voice_extraction":
                    # 音色提取
                    await self._update_progress(
                        task_id,
                        step_start_progress,
                        "开始提取音色",
                        {},
                        progress_callback,
                    )
                    voice_id, voice_path = await self._extract_voice(
                        current_video_path,
                        task_dir,
                        task_id,
                        step_start_progress,
                        step_end_progress,
                        progress_callback,
                    )
                    self.tasks[task_id]["output_paths"]["voice_id"] = voice_id
                    self.tasks[task_id]["output_paths"]["voice_path"] = voice_path

                elif step == "speech_generation":
                    # 生成新语音
                    await self._update_progress(
                        task_id,
                        step_start_progress,
                        "开始生成新语音",
                        {"current_stage": "speech_generation"},
                        progress_callback,
                    )
                    voice_id = self.tasks[task_id]["output_paths"].get("voice_id")
                    if not voice_id:
                        raise ValueError("未找到提取的音色ID")

                    new_audio_path = await self._generate_speech(
                        task_data.get("voice_text", ""),
                        voice_id,
                        task_dir,
                        task_id,
                        step_start_progress,
                        step_end_progress,
                        progress_callback,
                    )
                    self.tasks[task_id]["output_paths"][
                        "new_audio_path"
                    ] = new_audio_path

                elif step == "lip_sync":
                    # 唇形同步
                    await self._update_progress(
                        task_id,
                        step_start_progress,
                        "开始唇形同步",
                        {"current_stage": "lip_sync"},
                        progress_callback,
                    )
                    no_subtitle_video = self.tasks[task_id]["output_paths"].get(
                        "no_subtitle_video"
                    )
                    new_audio_path = self.tasks[task_id]["output_paths"].get(
                        "new_audio_path"
                    )

                    if not no_subtitle_video:
                        raise ValueError("未找到无字幕视频")
                    if not new_audio_path:
                        raise ValueError("未找到生成的语音文件")

                    final_video_path = await self._sync_lips(
                        no_subtitle_video,
                        new_audio_path,
                        task_dir,
                        task_id,
                        step_start_progress,
                        step_end_progress,
                        progress_callback,
                    )
                    current_video_path = final_video_path
                    self.tasks[task_id]["output_paths"][
                        "final_video_path"
                    ] = final_video_path

                elif step == "add_subtitles":
                    # 添加字幕
                    await self._update_progress(
                        task_id,
                        step_start_progress,
                        "开始添加字幕",
                        {"current_stage": "add_subtitles"},
                        progress_callback,
                    )

                    # 获取字幕文本
                    subtitle_text = task_data.get("voice_text", "") or task_data.get(
                        "text", ""
                    )
                    if not subtitle_text:
                        raise ValueError("未找到字幕文本")

                    # 添加字幕
                    subtitled_video_path = await self._add_subtitles(
                        current_video_path,
                        subtitle_text,
                        task_dir,
                        task_id,
                        task_data.get("subtitle_style", {}),
                        step_start_progress,
                        step_end_progress,
                        progress_callback,
                    )
                    current_video_path = subtitled_video_path
                    self.tasks[task_id]["output_paths"][
                        "subtitled_video_path"
                    ] = subtitled_video_path

            # 最终处理
            output_filename = f"processed_{os.path.basename(video_path)}"
            output_path = os.path.join(self.output_dir, output_filename)

            # 复制最终视频到输出目录
            await self._update_progress(
                task_id, 85, "正在生成最终视频", {}, progress_callback
            )

            # 使用ffmpeg复制视频（可以进行格式转换等操作）
            cmd = [
                "ffmpeg",
                "-i",
                current_video_path,
                "-c",
                "copy",  # 直接复制，不重新编码
                "-y",  # 覆盖已存在的文件
                output_path,
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            await process.communicate()

            if process.returncode != 0:
                raise Exception("生成最终视频失败")

            # 生成预览图
            preview_path = await self._generate_preview(output_path, task_id)

            # 更新任务状态
            self.tasks[task_id]["status"] = "completed"
            self.tasks[task_id]["progress"] = 100
            self.tasks[task_id]["message"] = "视频处理完成"
            self.tasks[task_id]["output_paths"]["final_output"] = output_path
            self.tasks[task_id]["output_paths"]["preview"] = preview_path
            self.tasks[task_id]["end_time"] = datetime.now()

            await self._update_progress(
                task_id,
                100,
                "视频处理完成",
                {"output_path": output_path, "preview_path": preview_path},
                progress_callback,
            )

            return {
                "task_id": task_id,
                "status": "completed",
                "output_path": output_path,
                "preview_path": preview_path,
                "processing_time": (
                    self.tasks[task_id]["end_time"] - self.tasks[task_id]["start_time"]
                ).total_seconds(),
            }

        except Exception as e:
            logger.error(f"处理视频失败: {str(e)}", exc_info=True)
            self.tasks[task_id]["status"] = "failed"
            self.tasks[task_id]["message"] = f"处理失败: {str(e)}"
            self.tasks[task_id]["end_time"] = datetime.now()

            if progress_callback:
                await progress_callback(task_id, -1, f"处理失败: {str(e)}", {})

            return {"task_id": task_id, "status": "failed", "error": str(e)}

    async def _update_progress(
        self,
        task_id: str,
        progress: int,
        message: str,
        data: Dict[str, Any],
        progress_callback: Optional[
            Callable[[str, int, str, Dict[str, Any]], None]
        ] = None,
    ):
        """
        更新任务进度

        Args:
            task_id: 任务ID
            progress: 进度值（0-100）
            message: 进度消息
            data: 附加数据
            progress_callback: 进度回调函数
        """
        # 更新内部任务状态
        if task_id in self.tasks:
            self.tasks[task_id]["progress"] = progress
            self.tasks[task_id]["message"] = message

            # 如果数据中包含当前处理阶段，也更新它
            if "current_stage" in data:
                self.tasks[task_id]["current_stage"] = data["current_stage"]

        # 调用进度回调函数
        if progress_callback:
            # 确保数据中包含当前处理阶段
            callback_data = data.copy() if data else {}
            if (
                "current_stage" not in callback_data
                and task_id in self.tasks
                and "current_stage" in self.tasks[task_id]
            ):
                callback_data["current_stage"] = self.tasks[task_id]["current_stage"]

            await progress_callback(task_id, progress, message, callback_data)

    async def _remove_subtitles(
        self,
        video_path: str,
        task_dir: str,
        task_id: str,
        mode: str,
        selected_area: Optional[Dict[str, Any]] = None,
        auto_detect: bool = False,
        start_progress: float = 0,
        end_progress: float = 25,
        progress_callback: Optional[
            Callable[[str, int, str, Dict[str, Any]], None]
        ] = None,
    ) -> str:
        """擦除视频字幕"""
        output_path = os.path.join(task_dir, "no_subtitle.mp4")

        # TODO: 集成video-subtitle-remover项目
        # 这里是调用video-subtitle-remover的代码
        # 示例命令:
        # python backend/main.py --video {video_path} --output {output_path} --mode {mode}

        # 模拟进度更新
        await self._update_progress(
            task_id,
            start_progress,
            "正在准备字幕擦除",
            {"current_stage": "subtitle_removal"},
            progress_callback,
        )
        await asyncio.sleep(1)
        await self._update_progress(
            task_id,
            (start_progress + end_progress) / 2,
            "正在擦除字幕",
            {"current_stage": "subtitle_removal"},
            progress_callback,
        )
        await asyncio.sleep(1)

        # 临时方案：直接复制原视频（实际实现中应替换为真正的字幕擦除）
        cmd = ["ffmpeg", "-i", video_path, "-c", "copy", "-y", output_path]

        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        await process.communicate()

        if process.returncode != 0 or not os.path.exists(output_path):
            raise Exception("字幕擦除失败")

        await self._update_progress(
            task_id,
            end_progress,
            "字幕擦除完成",
            {"current_stage": "subtitle_removal"},
            progress_callback,
        )

        return output_path

    async def _extract_voice(
        self,
        video_path: str,
        task_dir: str,
        task_id: str,
        start_progress: float = 25,
        end_progress: float = 50,
        progress_callback: Optional[
            Callable[[str, int, str, Dict[str, Any]], None]
        ] = None,
    ) -> Tuple[str, str]:
        """从视频中提取音色"""
        # 提取音频
        audio_path = os.path.join(task_dir, "original_audio.wav")
        voice_id = str(uuid.uuid4())
        voice_path = os.path.join(self.voice_dir, f"{voice_id}.npz")

        # 更新进度
        await self._update_progress(
            task_id,
            start_progress,
            "正在从视频中提取音频",
            {"current_stage": "voice_extraction"},
            progress_callback,
        )

        # 提取音频
        cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "16000",
            "-ac",
            "1",
            "-y",
            audio_path,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        await process.communicate()

        if process.returncode != 0 or not os.path.exists(audio_path):
            raise Exception("音频提取失败")

        # 更新进度
        await self._update_progress(
            task_id,
            int(start_progress + (end_progress - start_progress) * 0.5),
            "正在提取音色特征",
            {"current_stage": "voice_extraction"},
            progress_callback,
        )

        # 模拟音色提取过程
        await asyncio.sleep(2)

        # 创建一个空的音色文件（实际实现中应替换为真正的音色提取）
        with open(voice_path, "wb") as f:
            f.write(b"dummy voice data")

        # 更新进度
        await self._update_progress(
            task_id,
            end_progress,
            "音色提取完成",
            {"current_stage": "voice_extraction"},
            progress_callback,
        )

        return audio_path, voice_path

    async def _generate_speech(
        self,
        text: str,
        voice_id: str,
        task_dir: str,
        task_id: str,
        start_progress: float = 50,
        end_progress: float = 75,
        progress_callback: Optional[
            Callable[[str, int, str, Dict[str, Any]], None]
        ] = None,
    ) -> str:
        """生成语音"""
        output_path = os.path.join(task_dir, "generated_speech.wav")

        # 更新进度
        await self._update_progress(
            task_id,
            start_progress,
            "开始生成新语音",
            {"current_stage": "speech_generation"},
            progress_callback,
        )

        # TODO: 集成VALL-E-X或其他语音合成工具
        # 这里是调用语音合成工具的代码
        # 示例:
        # python inference.py --text "{text}" --voice_prompt {voice_prompt} --output {output_path}

        # 模拟语音生成过程
        await asyncio.sleep(3)

        # 更新进度
        await self._update_progress(
            task_id,
            int(start_progress + (end_progress - start_progress) * 0.7),
            "正在优化语音质量",
            {"current_stage": "speech_generation"},
            progress_callback,
        )

        # 模拟继续处理
        await asyncio.sleep(2)

        # 临时方案：创建一个空的音频文件（实际实现中应替换为真正的语音生成）
        cmd = [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=16000:cl=mono",
            "-t",
            "5",
            "-q:a",
            "9",
            "-acodec",
            "libmp3lame",
            output_path,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        await process.communicate()

        if process.returncode != 0 or not os.path.exists(output_path):
            raise Exception("语音生成失败")

        # 更新进度
        await self._update_progress(
            task_id,
            end_progress,
            "新语音生成完成",
            {"current_stage": "speech_generation"},
            progress_callback,
        )

        return output_path

    async def _sync_lips(
        self,
        video_path: str,
        audio_path: str,
        task_dir: str,
        task_id: str,
        start_progress: float = 75,
        end_progress: float = 90,
        progress_callback: Optional[
            Callable[[str, int, str, Dict[str, Any]], None]
        ] = None,
    ) -> str:
        """唇形同步"""
        output_path = os.path.join(task_dir, "lip_synced.mp4")

        # 更新进度
        await self._update_progress(
            task_id,
            start_progress,
            "开始唇形同步",
            {"current_stage": "lip_sync"},
            progress_callback,
        )

        # TODO: 集成Wav2Lip或其他唇形同步工具
        # 这里是调用唇形同步工具的代码
        # 示例:
        # python inference.py --face {video_path} --audio {audio_path} --outfile {output_path}

        # 模拟唇形同步过程
        await asyncio.sleep(3)

        # 更新进度
        await self._update_progress(
            task_id,
            int(start_progress + (end_progress - start_progress) * 0.5),
            "正在进行唇形同步",
            {"current_stage": "lip_sync"},
            progress_callback,
        )

        # 模拟继续处理
        await asyncio.sleep(3)

        # 临时方案：合并视频和音频（实际实现中应替换为真正的唇形同步）
        cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-i",
            audio_path,
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-shortest",
            "-y",
            output_path,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        await process.communicate()

        if process.returncode != 0 or not os.path.exists(output_path):
            raise Exception("唇形同步失败")

        # 更新进度
        await self._update_progress(
            task_id,
            end_progress,
            "唇形同步完成",
            {"current_stage": "lip_sync"},
            progress_callback,
        )

        return output_path

    async def _add_subtitles(
        self,
        video_path: str,
        subtitle_text: str,
        task_dir: str,
        task_id: str,
        subtitle_style: Dict[str, Any] = None,
        start_progress: float = 90,
        end_progress: float = 95,
        progress_callback: Optional[
            Callable[[str, int, str, Dict[str, Any]], None]
        ] = None,
    ) -> str:
        """添加字幕到视频"""
        output_path = os.path.join(task_dir, "subtitled_video.mp4")
        subtitle_file = os.path.join(task_dir, "subtitles.srt")

        await self._update_progress(
            task_id,
            start_progress,
            "开始添加字幕",
            {"current_stage": "add_subtitles"},
            progress_callback,
        )

        # 默认字幕样式
        default_style = {
            "font_size": 24,
            "font_color": "white",
            "bg_color": "black@0.5",
            "position": "bottom",
            "align": "center",
        }

        # 合并用户自定义样式
        if subtitle_style:
            style = {**default_style, **subtitle_style}
        else:
            style = default_style

        # 生成SRT字幕文件
        await self._generate_srt_file(subtitle_text, subtitle_file)

        # 使用FFmpeg添加字幕
        await self._update_progress(
            task_id,
            (start_progress + end_progress) / 2,
            "正在添加字幕",
            {"current_stage": "add_subtitles"},
            progress_callback,
        )

        # 构建字幕样式
        font_size = style.get("font_size", 24)
        font_color = style.get("font_color", "white")
        bg_color = style.get("bg_color", "black@0.5")
        position = style.get("position", "bottom")
        align = style.get("align", "center")

        # 根据位置设置字幕位置
        if position == "bottom":
            y_position = "h-th-10"
        elif position == "top":
            y_position = "10"
        elif position == "middle":
            y_position = "(h-th)/2"
        else:
            y_position = "h-th-10"  # 默认底部

        # 根据对齐方式设置字幕对齐
        if align == "left":
            x_position = "10"
        elif align == "right":
            x_position = "w-tw-10"
        elif align == "center":
            x_position = "(w-tw)/2"
        else:
            x_position = "(w-tw)/2"  # 默认居中

        # 构建FFmpeg命令
        cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-vf",
            f"subtitles={subtitle_file}:force_style='FontSize={font_size},PrimaryColour={font_color},BackColour={bg_color},Alignment={align},MarginV=10'",
            "-c:a",
            "copy",
            "-y",
            output_path,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        await process.communicate()

        if process.returncode != 0 or not os.path.exists(output_path):
            # 如果使用subtitles滤镜失败，尝试使用drawtext滤镜
            cmd = [
                "ffmpeg",
                "-i",
                video_path,
                "-vf",
                f"drawtext=fontsize={font_size}:fontcolor={font_color}:box=1:boxcolor={bg_color}:text='{subtitle_text}':x={x_position}:y={y_position}",
                "-c:a",
                "copy",
                "-y",
                output_path,
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            await process.communicate()

            if process.returncode != 0 or not os.path.exists(output_path):
                raise Exception("添加字幕失败")

        await self._update_progress(
            task_id,
            end_progress,
            "字幕添加完成",
            {"current_stage": "add_subtitles"},
            progress_callback,
        )

        return output_path

    async def _generate_srt_file(self, text: str, output_file: str) -> None:
        """生成SRT格式字幕文件"""
        # 简单实现：将整个文本作为一个字幕条目
        # 实际应用中，应该根据语音时长和内容进行分段

        # 计算大致的字幕持续时间（假设每个字符0.2秒）
        duration_seconds = len(text) * 0.2
        end_time = duration_seconds if duration_seconds > 5 else 5  # 至少5秒

        # 格式化时间
        def format_time(seconds: float) -> str:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millisecs = int((seconds - int(seconds)) * 1000)
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

        # 写入SRT文件
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("1\n")
            f.write(f"00:00:00,000 --> {format_time(end_time)}\n")
            f.write(f"{text}\n\n")

    async def _generate_preview(self, video_path: str, task_id: str) -> str:
        """生成视频预览图"""
        preview_path = os.path.join(self.output_dir, f"preview_{task_id}.jpg")

        cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-ss",
            "00:00:01",  # 从第1秒开始
            "-vframes",
            "1",  # 提取1帧
            "-q:v",
            "2",  # 质量设置
            "-y",
            preview_path,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        await process.communicate()

        if process.returncode != 0 or not os.path.exists(preview_path):
            logger.warning(f"生成预览图失败: {video_path}")
            return ""

        return preview_path

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        if task_id not in self.tasks:
            return {"status": "not_found", "message": "任务不存在"}

        task = self.tasks[task_id]
        return {
            "status": task.get("status", "unknown"),
            "progress": task.get("progress", 0),
            "message": task.get("message", ""),
            "output_paths": task.get("output_paths", {}),
            "start_time": task.get("start_time"),
            "end_time": task.get("end_time"),
            "processing_time": (
                (task.get("end_time") - task.get("start_time")).total_seconds()
                if task.get("end_time")
                else None
            ),
        }

    def clean_task(self, task_id: str) -> bool:
        """清理任务临时文件"""
        if task_id not in self.tasks:
            return False

        task_dir = self.tasks[task_id].get("task_dir")
        if task_dir and os.path.exists(task_dir):
            import shutil

            shutil.rmtree(task_dir)

        return True
