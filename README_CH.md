# Novel Video Generator System

Novel Video Generator System

## Project Overview

This is an AI-based novel video generation system that converts novel text into high-quality video content. The system completes video generation through the following steps:

1. **Novel Analysis**: Uses DeepSeek large language model to analyze novel content and generate storyboard scripts
2. **Asset Generation**: Calls Volcengine's TTS, text-to-image, and image-to-video models to generate corresponding assets
3. **Video Composition**: Combines multiple assets into complete scene videos
4. **Final Assembly**: Merges multiple scene videos into a complete novel interpretation video

## System Architecture

```
novel_video/
├── config/                 # Configuration files
│   └── config.yaml        # Main configuration file
├── src/                   # Source code
│   ├── core/             # Core modules
│   │   ├── config.py     # Configuration management
│   │   ├── logger.py     # Logging management
│   │   └── database.py   # Database management
│   ├── services/         # Service modules
│   │   ├── doubao_service.py     # Doubao API service
│   │   ├── volcengine_service.py # Volcengine base service
│   │   ├── tts_service.py        # TTS service
│   │   ├── image_gen_service.py  # Image generation service
│   │   └── video_gen_service.py  # Video generation service
│   ├── processors/       # Processor modules
│   │   ├── video_processor.py     # Video processor
│   │   ├── novel_processor.py     # Novel processor
│   │   └── subtitle_service.py    # Subtitle service
│   └── scheduler/        # Scheduler modules
│       ├── task_scheduler.py      # Task scheduler
│       ├── task_queue.py          # Task queue
│       └── task_worker.py         # Task worker threads
├── data/                 # Data directory
│   ├── input/           # Input files
│   ├── output/          # Output files
│   ├── temp/            # Temporary files
│   └── database/        # Database files
├── logs/                # Log files
├── assets/              # Asset files
│   ├── fonts/           # Font files
│   ├── bgm/             # Background music
│   └── templates/       # Template files
├── main.py              # Main program entry
├── requirements.txt     # Dependencies list
└── README.md           # Project documentation
```

## Features

### Core Features
- **Batch Processing**: Supports batch processing of large numbers of novel files
- **Task Scheduling**: Multi-threaded task scheduling with concurrent processing support
- **Progress Tracking**: Real-time tracking of task execution progress
- **Error Handling**: Comprehensive error handling and retry mechanisms
- **Logging Management**: Detailed logging and monitoring

### Video Generation
- **Intelligent Storyboarding**: AI-based intelligent storyboard script generation
- **Multi-modal Synthesis**: Perfect integration of TTS, image generation, and video generation
- **High-Quality Output**: Support for multiple video formats and resolutions
- **Subtitle Support**: Automatic subtitle generation and composition

### System Management
- **Configuration Management**: Flexible configuration file management
- **Database Storage**: Persistent storage of task status and file information
- **File Management**: Automatic file cleanup and storage management
- **API Monitoring**: Detailed API call logging and monitoring

## Installation and Configuration

### Requirements
- Python 3.8+
- FFmpeg (for video processing)
- Sufficient disk space (for video file storage)

### Installation Steps

1. **Clone the repository**
```bash
git clone <repository-url>
cd novel_video
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
Create a `.env` file and configure the following variables:
```env
# Doubao unified API configuration
DOUBAO_API_KEY=your_doubao_api_key
DOUBAO_APP_ID=your_doubao_app_id
```

4. **Configure Doubao API**
Configure Doubao large language model, TTS, text-to-image, and image-to-video APIs according to Volcengine official documentation:
- [Doubao Large Language Model API Documentation](https://www.volcengine.com/docs/82379/1494384)
- [Doubao TTS API Documentation](https://www.volcengine.com/docs/6561/1257584)
- [Doubao Text-to-Image API Documentation](https://www.volcengine.com/docs/82379/1541523)
- [Doubao Image-to-Video API Documentation](https://www.volcengine.com/docs/82379/1520757)

## Usage

### Command Line Usage

1. **Submit a new task**
```bash
python main.py --input novel.txt --output output_dir
```

2. **Check system status**
```bash
python main.py --status
```

3. **List all tasks**
```bash
python main.py --list-tasks
```

4. **Check task status**
```bash
python main.py --task-id task_id
```

5. **Retry failed task**
```bash
python main.py --task-id task_id --retry
```

6. **Daemon mode**
```bash
python main.py --daemon
```

### Interactive Mode
```bash
python main.py
```

### Batch Processing
```bash
# Process all txt files in the directory
for file in data/input/*.txt; do
    python main.py --input "$file"
done
```

## 配置说明

### 主要配置项

```yaml
# 项目配置
project:
  name: "novel_video_generator"
  version: "1.0.0"

# 文件路径配置
paths:
  input_dir: "data/input"
  output_dir: "data/output"
  temp_dir: "data/temp"
  logs_dir: "logs"

# 任务调度配置
scheduler:
  max_concurrent_tasks: 3
  task_timeout: 3600
  retry_attempts: 3

# 视频处理配置
video:
  fps: 30
  resolution: [1920, 1080]
  codec: "libx264"
  bitrate: "5000k"

# 分镜脚本配置
storyboard:
  max_scenes_per_chapter: 10
  min_scene_duration: 5
  max_scene_duration: 30
```

## API服务配置

### 豆包大模型API
用于小说分析和分镜脚本生成，需要在配置文件中设置API密钥和端点。

### 豆包API服务
豆包系列服务使用统一的API密钥，包括：
- **豆包大模型服务**：小说分析和分镜脚本生成
- **豆包语音服务**：文本转语音
- **豆包文生图服务**：文本生成图像
- **豆包图生视频服务**：图像生成视频

具体的API调用方式需要根据火山引擎的官方文档进行调整。

## 监控和日志

### 日志文件
- `logs/novel_video_YYYY-MM-DD.log`：主要日志文件
- `logs/error_YYYY-MM-DD.log`：错误日志文件

### 数据库监控
系统使用SQLite数据库存储任务状态和文件信息，可以通过以下方式查看：
```bash
sqlite3 data/database/novel_video.db
```

### 性能监控
系统提供详细的性能监控信息，包括：
- API调用统计
- 任务执行时间
- 资源使用情况

## 故障排除

### 常见问题

1. **API调用失败**
   - 检查API密钥配置
   - 确认网络连接
   - 查看API配额限制

2. **视频生成失败**
   - 检查FFmpeg安装
   - 确认磁盘空间充足
   - 查看临时文件权限

3. **任务超时**
   - 调整任务超时配置
   - 检查系统资源使用
   - 优化并发设置

### 调试模式
启用详细日志：
```bash
# 修改配置文件中的日志级别
logging:
  level: "DEBUG"
```

## 开发指南

### 添加新的服务
1. 在 `src/services/` 目录下创建新的服务类
2. 继承 `VolcengineService` 或创建独立服务类
3. 实现相应的API调用方法
4. 在 `NovelProcessor` 中集成新服务

### 扩展处理器
1. 在 `src/processors/` 目录下创建新的处理器
2. 实现相应的处理方法
3. 在任务调度器中注册新的任务类型

### 自定义配置
1. 修改 `config/config.yaml` 文件
2. 在代码中使用 `config.get()` 获取配置
3. 支持环境变量覆盖

## 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## 贡献指南

欢迎提交 Issue 和 Pull Request 来改进项目。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 GitHub Issue
- 发送邮件至项目维护者

---

**注意**：使用本系统需要相应的API密钥和配额，请确保遵守各服务商的使用条款。 