import sys
import os
import json
import webbrowser
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QLineEdit, QPushButton, QTextEdit,
                           QComboBox, QLabel, QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import yt_dlp
from history_window import HistoryWindow

class DownloadThread(QThread):
    """下载线程，处理视频下载过程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, url, download_dir, resolution='1080p'):
        super().__init__()
        self.url = url
        self.download_dir = download_dir
        self.resolution = resolution
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def run(self):
        try:
            # 设置下载选项
            ydl_opts = {
                'format': f'bestvideo[height<={self.resolution[:-1]}]+bestaudio/best',
                'outtmpl': os.path.join(
                    self.download_dir,
                    f'%(title)s_{self.timestamp}.%(ext)s'
                ),
                'progress_hooks': [self.progress_hook],
                'merge_output_format': 'mp4',
            }

            # 开始下载
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=True)
                
                # 准备视频信息
                video_info = {
                    'title': info['title'],
                    'url': self.url,
                    'download_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'resolution': self.resolution,
                    'duration': info.get('duration'),
                    'format': info.get('format'),
                    'channel': info.get('channel', 'Unknown'),
                    'channel_url': info.get('channel_url', ''),
                    'description': info.get('description', ''),
                    'view_count': info.get('view_count'),
                    'like_count': info.get('like_count'),
                    'upload_date': info.get('upload_date')
                }

                # 视频文件路径
                video_path = os.path.join(
                    self.download_dir,
                    f"{info['title']}_{self.timestamp}.mp4"
                )

                # 创建同名的.vinfo文件
                vinfo_path = video_path.rsplit('.', 1)[0] + '.vinfo'
                with open(vinfo_path, 'w', encoding='utf-8') as f:
                    json.dump(video_info, f, ensure_ascii=False, indent=2)

                # 发送完成信号
                result = video_info.copy()
                result['file_path'] = video_path
                result['vinfo_path'] = vinfo_path
                self.finished.emit(result)

        except Exception as e:
            self.error.emit(str(e))

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            progress = d.get('_percent_str', '0%')
            speed = d.get('_speed_str', 'N/A')
            self.progress.emit(f'下载进度: {progress} 速度: {speed}')
        elif d['status'] == 'finished':
            self.progress.emit('下载完成，正在处理...')

class DownloaderWindow(QMainWindow):
    """下载器主窗口"""
    def __init__(self):
        super().__init__()
        self.download_thread = None
        self.history_file = 'data/history.json'
        self.setup_ui()

    def setup_ui(self):
        """设置UI界面"""
        self.setWindowTitle("YouTube视频下载器")
        self.setMinimumSize(800, 400)  

        # 主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # URL输入区域
        url_layout = QHBoxLayout()
        url_label = QLabel("视频URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("输入YouTube视频URL")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)

        # 控制区域
        controls_layout = QHBoxLayout()

        # 分辨率选择
        resolution_layout = QHBoxLayout()
        resolution_label = QLabel("分辨率:")
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(['2160p', '1440p', '1080p', '720p', '480p'])
        resolution_layout.addWidget(resolution_label)
        resolution_layout.addWidget(self.resolution_combo)
        controls_layout.addLayout(resolution_layout)

        # 下载目录选择
        self.download_dir = os.path.join(os.getcwd(), 'downloads')
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

        dir_layout = QHBoxLayout()
        dir_label = QLabel("保存位置:")
        self.dir_display = QLabel(self.download_dir)
        self.dir_button = QPushButton("更改")
        self.dir_button.clicked.connect(self.select_directory)
        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(self.dir_display)
        dir_layout.addWidget(self.dir_button)
        controls_layout.addLayout(dir_layout)

        # 下载按钮
        self.download_button = QPushButton("下载")
        self.download_button.clicked.connect(self.start_download)
        controls_layout.addWidget(self.download_button)

        layout.addLayout(controls_layout)

        # 进度显示
        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        self.progress_text.setMaximumHeight(150)
        layout.addWidget(self.progress_text)

        # 底部按钮区域
        bottom_layout = QHBoxLayout()
        
        # 打开目录按钮
        self.open_dir_button = QPushButton("打开保存目录")
        self.open_dir_button.clicked.connect(self.open_download_dir)
        bottom_layout.addWidget(self.open_dir_button)
        
        # 添加弹性空间
        bottom_layout.addStretch()
        
        # 历史按钮
        self.history_button = QPushButton("下载历史")
        self.history_button.clicked.connect(self.show_history)
        bottom_layout.addWidget(self.history_button)

        layout.addLayout(bottom_layout)

        # 设置样式
        self.apply_styles()

    def apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QPushButton {
                background-color: #2b5b84;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3d7ab3;
            }
            QLineEdit, QTextEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QLabel {
                color: #333;
            }
        """)

    def select_directory(self):
        """选择下载目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择下载目录", self.download_dir
        )
        if dir_path:
            self.download_dir = dir_path
            self.dir_display.setText(dir_path)

    def start_download(self):
        """开始下载"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "错误", "请输入视频URL")
            return

        self.download_button.setEnabled(False)
        self.progress_text.clear()
        resolution = self.resolution_combo.currentText()

        self.download_thread = DownloadThread(url, self.download_dir, resolution)
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.error.connect(self.download_error)
        self.download_thread.start()

    def update_progress(self, message):
        """更新进度信息"""
        self.progress_text.append(message)

    def download_finished(self, result):
        """下载完成处理"""
        self.download_button.setEnabled(True)
        self.progress_text.append("下载完成！")
        self.save_to_history(result)

    def download_error(self, error_message):
        """下载错误处理"""
        self.download_button.setEnabled(True)
        QMessageBox.critical(self, "错误", f"下载失败: {error_message}")

    def save_to_history(self, download_info):
        """保存下载历史"""
        os.makedirs('data', exist_ok=True)
        history = []
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except Exception as e:
                self.progress_text.append(f"读取历史记录失败: {str(e)}")
        
        history.append(download_info)
        
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.progress_text.append(f"保存历史记录失败: {str(e)}")

    def show_history(self):
        """显示历史窗口"""
        history_dialog = HistoryWindow(self.history_file)
        history_dialog.exec()

    def open_download_dir(self):
        """打开下载目录"""
        try:
            if sys.platform == 'win32':
                os.startfile(self.download_dir)
            else:
                import subprocess
                subprocess.Popen(['xdg-open', self.download_dir])
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法打开目录: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DownloaderWindow()
    window.show()
    sys.exit(app.exec())
