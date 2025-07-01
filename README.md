# 小说视频生成系统

Novel Video Generator System

## 项目简介

这是一个基于AI的小说视频生成系统，能够将小说文本转换为高质量的视频内容。系统通过以下步骤完成视频生成：

1. **小说分析**：使用DeepSeek大模型分析小说内容，生成分镜脚本
2. **素材生成**：调用火山引擎的TTS、文生图、图生视频模型生成相应素材
3. **视频合成**：将多个素材合成为完整的分镜视频
4. **最终合成**：将多个分镜视频合成为完整的小说解读视频

## 系统架构

```
novel_video/
├── config/                 # 配置文件
│   └── config.yaml        # 主配置文件
├── src/                   # 源代码
│   ├── core/             # 核心模块
│   │   ├── config.py     # 配置管理
│   │   ├── logger.py     # 日志管理
│   │   └── database.py   # 数据库管理
│   ├── services/         # 服务模块
│   │   ├── deepseek_service.py    # DeepSeek API服务
│   │   ├── volcengine_service.py  # 火山引擎基础服务
│   │   ├── tts_service.py         # TTS服务
│   │   ├── image_gen_service.py   # 图像生成服务
│   │   └── video_gen_service.py   # 视频生成服务
│   ├── processors/       # 处理器模块
│   │   ├── video_processor.py     # 视频处理器
│   │   ├── storyboard_processor.py # 分镜脚本处理器
│   │   └── novel_processor.py     # 小说处理器
│   └── scheduler/        # 调度器模块
│       ├── task_scheduler.py      # 任务调度器
│       ├── task_queue.py          # 任务队列
│       └── task_worker.py         # 任务工作线程
├── data/                 # 数据目录
│   ├── input/           # 输入文件
│   ├── output/          # 输出文件
│   ├── temp/            # 临时文件
│   └── database/        # 数据库文件
├── logs/                # 日志文件
├── assets/              # 资源文件
│   ├── fonts/           # 字体文件
│   └── templates/       # 模板文件
├── main.py              # 主程序入口
├── requirements.txt     # 依赖包列表
└── README.md           # 项目说明
```

## 功能特性

### 核心功能
- **批量处理**：支持批量处理大量小说文件
- **任务调度**：多线程任务调度，支持并发处理
- **进度跟踪**：实时跟踪任务执行进度
- **错误处理**：完善的错误处理和重试机制
- **日志管理**：详细的日志记录和监控

### 视频生成
- **智能分镜**：基于AI的智能分镜脚本生成
- **多模态合成**：TTS、图像生成、视频生成的完美结合
- **高质量输出**：支持多种视频格式和分辨率
- **字幕支持**：自动生成和合成字幕

### 系统管理
- **配置管理**：灵活的配置文件管理
- **数据库存储**：任务状态和文件信息的持久化存储
- **文件管理**：自动的文件清理和存储管理
- **API监控**：详细的API调用记录和监控

## 安装配置

### 环境要求
- Python 3.8+
- FFmpeg（用于视频处理）
- 足够的磁盘空间（用于视频文件存储）

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd novel_video
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
创建 `.env` 文件并配置以下变量：
```env
# 豆包统一API配置
DOUBAO_API_KEY=your_doubao_api_key
DOUBAO_APP_ID=your_doubao_app_id
```

4. **配置豆包API**
根据火山引擎官方文档配置豆包大模型、语音、文生图、图生视频API：
- [豆包大模型API文档](https://www.volcengine.com/docs/82379/1494384)
- [豆包语音API文档](https://www.volcengine.com/docs/6561/1257584)
- [豆包文生图API文档](https://www.volcengine.com/docs/82379/1541523)
- [豆包图生视频API文档](https://www.volcengine.com/docs/82379/1520757)

## 使用方法

### 命令行使用

1. **提交新任务**
```bash
python main.py --input novel.txt --output output_dir
```

2. **查看系统状态**
```bash
python main.py --status
```

3. **列出所有任务**
```bash
python main.py --list-tasks
```

4. **查看任务状态**
```bash
python main.py --task-id task_id
```

5. **重试失败任务**
```bash
python main.py --task-id task_id --retry
```

6. **守护进程模式**
```bash
python main.py --daemon
```

### 交互模式
```bash
python main.py
```

### 批量处理
```bash
# 处理目录下的所有txt文件
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