# 视频处理测试工具

这个目录包含用于测试视频处理服务各个独立功能的工具和示例。通过这些工具，您可以单独测试字幕擦除、音色提取、语音生成、唇形同步和字幕添加等功能，而不必运行完整的处理流程。

## 文件说明

- `test_video_processing.py`: 主要测试工具，提供了各个处理步骤的独立测试函数
- `test_examples.py`: 示例代码，展示如何使用测试工具
- `README.md`: 本文档，提供使用说明

## 准备工作

1. 确保您已经安装了所有必要的依赖
2. 准备测试用的视频文件，放在 `uploads/test` 目录下

## 使用方法

### 命令行使用

您可以通过命令行直接调用 `test_video_processing.py` 来测试特定功能：

```bash
# 测试字幕擦除功能
python -m app.tests.test_video_processing --test remove_subtitles --video uploads/test/your_test_video.mp4 --mode balanced --auto-detect

# 测试音色提取功能
python -m app.tests.test_video_processing --test extract_voice --video uploads/test/your_test_video.mp4

# 测试语音生成功能
python -m app.tests.test_video_processing --test generate_speech --text "这是测试文本" --voice-id your_voice_id

# 测试唇形同步功能
python -m app.tests.test_video_processing --test sync_lips --video uploads/test/your_test_video.mp4 --audio uploads/test/your_test_audio.wav

# 测试添加字幕功能
python -m app.tests.test_video_processing --test add_subtitles --video uploads/test/your_test_video.mp4 --text "这是测试字幕"

# 测试完整处理流程
python -m app.tests.test_video_processing --test full_pipeline --video uploads/test/your_test_video.mp4 --text "这是测试文本"
```

### 在代码中使用

您也可以在自己的 Python 代码中导入并使用这些测试函数：

```python
import asyncio
from app.tests.test_video_processing import test_remove_subtitles

async def my_test():
    result = await test_remove_subtitles(
        video_path="uploads/test/your_test_video.mp4",
        mode="balanced",
        auto_detect=True
    )
    print(f"处理结果: {result}")

if __name__ == "__main__":
    asyncio.run(my_test())
```

### 运行示例

您可以运行 `test_examples.py` 来查看所有功能的示例：

```bash
python -m app.tests.test_examples
```

注意：在运行示例之前，请确保 `uploads/test` 目录中有适当的测试视频文件。

## 测试视频准备

为了充分测试各个功能，建议准备以下测试视频：

1. `test_video_with_subtitles.mp4`: 带有硬字幕的视频，用于测试字幕擦除
2. `test_video_with_voice.mp4`: 带有清晰人声的视频，用于测试音色提取
3. `test_video_for_lip_sync.mp4`: 有人物面部特写的视频，用于测试唇形同步
4. `test_video_without_subtitles.mp4`: 不带字幕的视频，用于测试添加字幕
5. `test_video_original.mp4`: 原始视频，用于测试完整处理流程

## 常见问题

### 1. 测试时出现"找不到模型"错误

确保您已经下载并配置了所需的 AI 模型。检查系统配置中的模型路径是否正确。

### 2. 处理速度很慢

视频处理，特别是 AI 相关的处理（如唇形同步）通常需要较长时间。建议使用较短的测试视频（5-10 秒）来加快测试速度。

### 3. 内存不足错误

处理高分辨率视频可能需要大量内存。如果遇到内存不足错误，尝试使用较低分辨率的测试视频，或增加系统可用内存。

## 自定义测试

您可以基于 `test_video_processing.py` 中的函数创建自己的测试用例。每个处理步骤都有独立的测试函数，您可以根据需要组合使用它们。
