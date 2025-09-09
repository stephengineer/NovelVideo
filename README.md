# 🎬 Novel Video Generator System

> 🤖 AI-powered novel-to-video conversion platform

## 📖 Project Overview

This is an AI-based novel video generation system that converts novel text into high-quality video content. The system completes video generation through the following steps:

1. **📚 Novel Analysis**: Uses DeepSeek large language model to analyze novel content and generate storyboard scripts
2. **🎨 Asset Generation**: Calls Volcengine's TTS, text-to-image, and image-to-video models to generate corresponding assets
3. **🎞️ Video Composition**: Combines multiple assets into complete scene videos
4. **🎯 Final Assembly**: Merges multiple scene videos into a complete novel interpretation video

## 🏗️ System Architecture

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

## ✨ Features

### 🚀 Core Features
- **📦 Batch Processing**: Supports batch processing of large numbers of novel files
- **⚡ Task Scheduling**: Multi-threaded task scheduling with concurrent processing support
- **📊 Progress Tracking**: Real-time tracking of task execution progress
- **🛡️ Error Handling**: Comprehensive error handling and retry mechanisms
- **📝 Logging Management**: Detailed logging and monitoring

### 🎥 Video Generation
- **🧠 Intelligent Storyboarding**: AI-based intelligent storyboard script generation
- **🎭 Multi-modal Synthesis**: Perfect integration of TTS, image generation, and video generation
- **🎬 High-Quality Output**: Support for multiple video formats and resolutions
- **📺 Subtitle Support**: Automatic subtitle generation and composition

### ⚙️ System Management
- **🔧 Configuration Management**: Flexible configuration file management
- **💾 Database Storage**: Persistent storage of task status and file information
- **🗂️ File Management**: Automatic file cleanup and storage management
- **📈 API Monitoring**: Detailed API call logging and monitoring

## 🚀 Installation and Configuration

### 📋 Requirements
- 🐍 Python 3.8+
- 🎬 FFmpeg (for video processing)
- 💾 Sufficient disk space (for video file storage)

### 📦 Installation Steps

1. **📥 Clone the repository**
```bash
git clone <repository-url>
cd novel_video
```

2. **📚 Install dependencies**
```bash
pip install -r requirements.txt
```

3. **🔑 Configure environment variables**
Create a `.env` file and configure the following variables:
```env
# Doubao unified API configuration
DOUBAO_API_KEY=your_doubao_api_key
DOUBAO_APP_ID=your_doubao_app_id
```

4. **⚙️ Configure Doubao API**
Configure Doubao large language model, TTS, text-to-image, and image-to-video APIs according to Volcengine official documentation:
- [🧠 Doubao Large Language Model API Documentation](https://www.volcengine.com/docs/82379/1494384)
- [🎤 Doubao TTS API Documentation](https://www.volcengine.com/docs/6561/1257584)
- [🎨 Doubao Text-to-Image API Documentation](https://www.volcengine.com/docs/82379/1541523)
- [🎬 Doubao Image-to-Video API Documentation](https://www.volcengine.com/docs/82379/1520757)

## 🎯 Usage

### 💻 Command Line Usage

1. **📤 Submit a new task**
```bash
python main.py --input novel.txt --output output_dir
```

2. **📊 Check system status**
```bash
python main.py --status
```

3. **📋 List all tasks**
```bash
python main.py --list-tasks
```

4. **🔍 Check task status**
```bash
python main.py --task-id task_id
```

5. **🔄 Retry failed task**
```bash
python main.py --task-id task_id --retry
```

6. **👻 Daemon mode**
```bash
python main.py --daemon
```

### 🖥️ Interactive Mode
```bash
python main.py
```

### 📦 Batch Processing
```bash
# Process all txt files in the directory
for file in data/input/*.txt; do
    python main.py --input "$file"
done
```

## ⚙️ Configuration

### 🔧 Main Configuration Items

```yaml
# Project configuration
project:
  name: "novel_video_generator"
  version: "1.0.0"

# File path configuration
paths:
  input_dir: "data/input"
  output_dir: "data/output"
  temp_dir: "data/temp"
  logs_dir: "logs"

# Task scheduling configuration
scheduler:
  max_concurrent_tasks: 3
  task_timeout: 3600
  retry_attempts: 3

# Video processing configuration
video:
  fps: 30
  resolution: [1920, 1080]
  codec: "libx264"
  bitrate: "5000k"

# Storyboard configuration
storyboard:
  max_scenes_per_chapter: 10
  min_scene_duration: 5
  max_scene_duration: 30
```

## 🔌 API Service Configuration

### 🧠 Doubao Large Language Model API
Used for novel analysis and storyboard script generation. API key and endpoint need to be configured in the configuration file.

### 🌐 Doubao API Services
Doubao series services use unified API keys, including:
- **🧠 Doubao Large Language Model Service**: Novel analysis and storyboard script generation
- **🎤 Doubao TTS Service**: Text-to-speech conversion
- **🎨 Doubao Text-to-Image Service**: Text-to-image generation
- **🎬 Doubao Image-to-Video Service**: Image-to-video generation

Specific API calling methods need to be adjusted according to Volcengine's official documentation.

## 📊 Monitoring and Logging

### 📝 Log Files
- `logs/novel_video_YYYY-MM-DD.log`: Main log file
- `logs/error_YYYY-MM-DD.log`: Error log file

### 💾 Database Monitoring
The system uses SQLite database to store task status and file information. You can view it using:
```bash
sqlite3 data/database/novel_video.db
```

### 📈 Performance Monitoring
The system provides detailed performance monitoring information, including:
- 📞 API call statistics
- ⏱️ Task execution time
- 💻 Resource usage

## 🔧 Troubleshooting

### ❗ Common Issues

1. **🚫 API call failures**
   - 🔑 Check API key configuration
   - 🌐 Verify network connection
   - 📊 Check API quota limits

2. **🎬 Video generation failures**
   - 🎥 Check FFmpeg installation
   - 💾 Ensure sufficient disk space
   - 🔒 Check temporary file permissions

3. **⏰ Task timeouts**
   - ⚙️ Adjust task timeout configuration
   - 💻 Check system resource usage
   - ⚡ Optimize concurrency settings

### 🐛 Debug Mode
Enable detailed logging:
```bash
# Modify log level in configuration file
logging:
  level: "DEBUG"
```

## 👨‍💻 Development Guide

### 🔧 Adding New Services
1. 📁 Create a new service class in the `src/services/` directory
2. 🔗 Inherit from `VolcengineService` or create an independent service class
3. ⚙️ Implement corresponding API calling methods
4. 🔌 Integrate the new service in `NovelProcessor`

### 🎯 Extending Processors
1. 📁 Create a new processor in the `src/processors/` directory
2. ⚙️ Implement corresponding processing methods
3. 📋 Register new task types in the task scheduler

### ⚙️ Custom Configuration
1. 📝 Modify the `config/config.yaml` file
2. 🔧 Use `config.get()` in code to retrieve configuration
3. 🌍 Support environment variable overrides

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🤝 Contributing

We welcome contributions! Please feel free to submit Issues and Pull Requests to improve the project.

## 📞 Contact

If you have questions or suggestions, please contact us through:
- 🐛 Submit a GitHub Issue
- 📧 Send an email to the project maintainer

---

**⚠️ Note**: Using this system requires appropriate API keys and quotas. Please ensure compliance with each service provider's terms of use. 