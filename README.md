# YouTube 视频下载和播放器

这是一个基于 Python 的 YouTube 视频下载和播放工具，支持视频下载、播放和管理功能。

## 功能特点

- 视频下载
  - 支持输入 YouTube 视频链接下载视频
  - 可选择不同的视频质量和格式
  - 显示下载进度和速度
  - 保存下载历史记录

- 视频播放
  - 支持本地视频文件播放
  - 视频列表显示（包含文件名、大小、下载日期）
  - 播放控制（播放、停止）
  - 视频信息查看
  - 支持打开原始视频链接

- 历史记录
  - 记录已下载视频的信息
  - 支持查看和管理下载历史

## 系统要求

- Python 3.8+
- FFmpeg
- 操作系统：Windows

## 安装要求

- Python 3.8 或更高版本
- FFmpeg（需要预先安装）
- 项目依赖包（见 requirements.txt）

## 安装步骤

1. 安装 Python 3.8+
2. 安装 FFmpeg 并确保可以在命令行中运行
3. 克隆或下载本项目
4. 安装依赖包：
```bash
pip install -r requirements.txt
```

## 使用说明

### 下载器
```bash
python youtube_downloader.py
```

### 播放器
```bash
python video_player.py
```

## 数据存储

- 下载的视频存储在 `downloads` 目录
- 下载历史记录存储在 `data/history.json`
- 播放器配置存储在 `data/player_config.json`

## 项目结构

- `youtube_downloader.py`: 视频下载器主程序
- `video_player.py`: 视频播放器主程序
- `utils/`：公共工具函数
- `ui/`：UI相关代码
- `config/`：配置文件
- `data/history.json`: 下载历史记录文件
- `downloads/`: 下载的视频文件存储目录

## 注意事项

- 确保系统中已正确安装 FFmpeg
- 下载的视频默认保存在 downloads 目录下
- 每个视频文件都会有一个对应的 .vinfo 文件，保存视频的详细信息

## 版本历史

- v3.0.0 (2024-12-09)
  - 重构了整个项目结构
  - 改进了视频播放器界面
  - 添加了视频信息查看功能
  - 优化了下载历史记录管理
