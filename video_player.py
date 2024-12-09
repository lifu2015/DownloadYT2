import sys
import os
import json
import subprocess
import webbrowser
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QLabel, QFileDialog,
                           QTreeWidget, QTreeWidgetItem, QMessageBox, QDialog, QTextBrowser,
                           QHeaderView)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from video_info_window import VideoInfoWindow  # 添加导入语句到文件顶部

class FFplayThread(QThread):
    """FFplay播放线程"""
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path
        self.process = None
        self.is_playing = False

    def run(self):
        try:
            # 使用ffplay播放视频
            command = [
                'ffplay',
                '-window_title', os.path.basename(self.video_path),
                '-x', '800',  # 窗口宽度
                '-y', '600',  # 窗口高度
                '-autoexit',  # 播放完成后自动退出
                '-loglevel', 'error',  # 只显示错误日志
                self.video_path
            ]
            
            # 使用subprocess.PIPE捕获输出
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW  # 在Windows上不显示命令行窗口
            )
            self.is_playing = True
            
            # 读取错误输出
            _, stderr = self.process.communicate()
            if stderr:
                error_msg = stderr.decode('utf-8', errors='ignore').strip()
                if error_msg:
                    self.error.emit(f"FFplay错误: {error_msg}")
                    return

            # 检查进程返回码
            if self.process.returncode != 0 and self.process.returncode != -9:  # -9是SIGKILL信号，正常停止时会收到
                self.error.emit(f"FFplay异常退出，返回码: {self.process.returncode}")
            
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.is_playing = False
            self.process = None
            self.finished.emit()

    def stop(self):
        """停止播放"""
        if self.process and self.is_playing:
            try:
                if sys.platform == 'win32':
                    # Windows上使用taskkill强制结束进程
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.process.pid)],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
                else:
                    self.process.terminate()
                self.process.wait(timeout=2)  # 等待进程结束
            except Exception as e:
                print(f"停止播放时出错: {e}")
            finally:
                self.is_playing = False
                self.process = None

class PlayerWindow(QMainWindow):
    """播放器主窗口"""
    def __init__(self):
        super().__init__()
        self.play_thread = None
        self.current_video = None
        self.setup_ui()
        self.load_video_list()

    def setup_ui(self):
        """设置UI界面"""
        self.setWindowTitle("视频播放器")
        self.setMinimumSize(800, 500)

        # 主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # 目录选择区域
        dir_layout = QHBoxLayout()
        dir_label = QLabel("保存位置:")
        self.dir_display = QLabel(os.path.join(os.getcwd(), 'downloads'))
        self.dir_display.setStyleSheet("padding: 5px; background-color: #f5f5f5; border: 1px solid #ddd; border-radius: 4px;")
        
        # 更改目录按钮
        self.change_dir_button = QPushButton("更改")
        self.change_dir_button.clicked.connect(self.select_directory)
        
        # 打开目录按钮
        self.open_dir_button = QPushButton("打开保存目录")
        self.open_dir_button.clicked.connect(self.open_directory)
        
        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(self.dir_display, 1)  # 1表示拉伸因子
        dir_layout.addWidget(self.change_dir_button)
        dir_layout.addWidget(self.open_dir_button)
        
        layout.addLayout(dir_layout)

        # 视频列表
        list_label = QLabel("视频列表:")
        layout.addWidget(list_label)
        
        # 使用QTreeWidget替代QListWidget
        self.video_list = QTreeWidget()
        self.video_list.setHeaderLabels(["文件名", "大小", "下载日期"])
        self.video_list.setAlternatingRowColors(True)  # 交替行颜色
        self.video_list.itemSelectionChanged.connect(self.on_selection_changed)  # 添加选择变化事件
        
        # 设置列宽
        header = self.video_list.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # 文件名列自适应
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 大小列适应内容
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 日期列适应内容
        
        layout.addWidget(self.video_list)

        # 控制按钮
        controls_layout = QHBoxLayout()

        # 左侧播放控制按钮
        play_controls_layout = QHBoxLayout()
        
        # 播放按钮
        self.play_button = QPushButton("播放")
        self.play_button.setEnabled(False)  # 初始禁用
        self.play_button.clicked.connect(self.play_selected_video)
        play_controls_layout.addWidget(self.play_button)

        # 停止按钮
        self.stop_button = QPushButton("停止")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_video)
        play_controls_layout.addWidget(self.stop_button)

        play_controls_layout.addStretch()  # 添加弹性空间
        controls_layout.addLayout(play_controls_layout)

        # 右侧功能按钮
        right_controls_layout = QHBoxLayout()

        # 打开原始视频按钮
        self.open_original_button = QPushButton("原始视频")
        self.open_original_button.clicked.connect(self.open_original_url)
        self.open_original_button.setEnabled(False)  # 初始禁用
        right_controls_layout.addWidget(self.open_original_button)

        # 视频信息按钮
        self.info_button = QPushButton("视频信息")
        self.info_button.clicked.connect(self.show_video_info)
        self.info_button.setEnabled(False)
        right_controls_layout.addWidget(self.info_button)

        controls_layout.addLayout(right_controls_layout)
        layout.addLayout(controls_layout)

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
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #3d7ab3;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QTreeWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
            }
            QTreeWidget::item {
                height: 30px;  /* 增加项目高度 */
                border-bottom: 1px solid #eee;  /* 添加底部边框 */
            }
            QTreeWidget::item:selected {
                background-color: #2b5b84;  /* 选中项的背景色 */
                color: white;  /* 选中项的文字颜色 */
            }
            QTreeWidget::item:hover {
                background-color: #e0e0e0;  /* 悬停项的背景色 */
            }
            QTreeWidget::item:selected:hover {
                background-color: #3d7ab3;  /* 选中项悬停时的背景色 */
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 5px;
                border: none;
                border-right: 1px solid #ccc;
                font-weight: bold;  /* 加粗表头文字 */
            }
            QLabel {
                color: #333;
                font-weight: bold;
            }
        """)

    def on_selection_changed(self):
        """处理视频选择变化"""
        selected_items = self.video_list.selectedItems()
        has_selection = len(selected_items) > 0
        
        # 更新按钮状态
        self.play_button.setEnabled(has_selection)
        self.info_button.setEnabled(has_selection)
        self.open_original_button.setEnabled(has_selection)

    def format_size(self, size_in_bytes):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_in_bytes < 1024:
                return f"{size_in_bytes:.2f} {unit}"
            size_in_bytes /= 1024
        return f"{size_in_bytes:.2f} TB"

    def load_video_list(self):
        """加载视频列表"""
        self.video_list.clear()
        downloads_dir = self.dir_display.text()
        
        if os.path.exists(downloads_dir):
            for file in os.listdir(downloads_dir):
                if file.endswith(('.mp4', '.mkv', '.avi', '.mov')):
                    video_path = os.path.join(downloads_dir, file)
                    vinfo_path = video_path.rsplit('.', 1)[0] + '.vinfo'
                    
                    # 创建列表项
                    item = QTreeWidgetItem()
                    item.setText(0, file)  # 文件名
                    
                    # 尝试从.vinfo文件获取信息
                    try:
                        if os.path.exists(vinfo_path):
                            with open(vinfo_path, 'r', encoding='utf-8') as f:
                                info = json.load(f)
                                
                                # 获取文件大小
                                file_size = os.path.getsize(video_path)
                                item.setText(1, self.format_size(file_size))
                                
                                # 获取下载日期
                                download_time = info.get('download_time', '')
                                if download_time:
                                    try:
                                        # 转换时间格式
                                        dt = datetime.strptime(download_time, "%Y-%m-%d %H:%M:%S")
                                        formatted_time = dt.strftime("%Y-%m-%d %H:%M")
                                        item.setText(2, formatted_time)
                                    except ValueError:
                                        item.setText(2, download_time)
                        else:
                            # 如果没有.vinfo文件，显示文件系统信息
                            file_size = os.path.getsize(video_path)
                            item.setText(1, self.format_size(file_size))
                            
                            # 使用文件修改时间
                            mtime = os.path.getmtime(video_path)
                            dt = datetime.fromtimestamp(mtime)
                            item.setText(2, dt.strftime("%Y-%m-%d %H:%M"))
                            
                    except Exception as e:
                        print(f"加载视频信息时出错: {e}")
                        # 出错时显示基本文件信息
                        try:
                            file_size = os.path.getsize(video_path)
                            item.setText(1, self.format_size(file_size))
                            mtime = os.path.getmtime(video_path)
                            dt = datetime.fromtimestamp(mtime)
                            item.setText(2, dt.strftime("%Y-%m-%d %H:%M"))
                        except:
                            item.setText(1, "未知")
                            item.setText(2, "未知")
                    
                    self.video_list.addTopLevelItem(item)

    def play_selected_video(self):
        """播放选中的视频"""
        item = self.video_list.currentItem()
        if item is None:
            QMessageBox.warning(self, "提示", "请先选择要播放的视频")
            return

        video_path = os.path.join(self.dir_display.text(), item.text(0))  # 使用当前目录
        self.play_video(video_path)

    def select_directory(self):
        """选择目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择保存目录", self.dir_display.text()
        )
        if dir_path:
            self.dir_display.setText(dir_path)
            self.load_video_list()

    def open_directory(self):
        """打开保存目录"""
        dir_path = self.dir_display.text()
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            
        try:
            if sys.platform == 'win32':
                os.startfile(dir_path)
            else:
                import subprocess
                subprocess.Popen(['xdg-open', dir_path])
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法打开目录: {str(e)}")

    def play_video(self, video_path):
        """播放视频"""
        if self.play_thread and self.play_thread.is_playing:
            self.stop_video()

        self.current_video = video_path
        self.play_thread = FFplayThread(video_path)
        self.play_thread.error.connect(self.handle_error)
        self.play_thread.finished.connect(self.playback_finished)
        self.play_thread.start()

        # 启用相关按钮
        self.stop_button.setEnabled(True)
        self.info_button.setEnabled(True)
        self.open_original_button.setEnabled(True)

    def stop_video(self):
        """停止视频播放"""
        if self.play_thread and self.play_thread.is_playing:
            try:
                self.play_thread.stop()
                self.play_thread.wait()  # 等待线程结束
                self.play_thread = None
                self.stop_button.setEnabled(False)
            except Exception as e:
                QMessageBox.warning(self, "错误", f"停止播放时出错: {str(e)}")
        else:
            self.stop_button.setEnabled(False)

    def handle_error(self, error_message):
        """错误处理"""
        QMessageBox.critical(self, "错误", f"播放错误: {error_message}")
        self.stop_button.setEnabled(False)

    def playback_finished(self):
        """播放完成处理"""
        self.stop_button.setEnabled(False)

    def show_video_info(self):
        """显示视频信息"""
        item = self.video_list.currentItem()
        if not item:
            QMessageBox.warning(self, "提示", "请先选择一个视频")
            return

        video_path = os.path.join(self.dir_display.text(), item.text(0))
        vinfo_path = video_path.rsplit('.', 1)[0] + '.vinfo'

        if not os.path.exists(vinfo_path):
            QMessageBox.warning(self, "错误", "找不到视频信息文件")
            return

        try:
            info_window = VideoInfoWindow(vinfo_path)
            info_window.exec()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"打开视频信息时出错: {str(e)}")

    def open_original_url(self):
        """打开视频原始URL"""
        item = self.video_list.currentItem()
        if not item:
            QMessageBox.warning(self, "提示", "请先选择一个视频")
            return

        video_path = os.path.join(self.dir_display.text(), item.text(0))
        vinfo_path = video_path.rsplit('.', 1)[0] + '.vinfo'

        if not os.path.exists(vinfo_path):
            QMessageBox.warning(self, "错误", "找不到视频信息文件")
            return

        try:
            with open(vinfo_path, 'r', encoding='utf-8') as f:
                info = json.load(f)
                url = info.get('url')
                if url:
                    webbrowser.open(url)
                else:
                    QMessageBox.warning(self, "错误", "视频信息文件中没有URL信息")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"打开URL时出错: {str(e)}")

    def closeEvent(self, event):
        """窗口关闭事件"""
        self.stop_video()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PlayerWindow()
    window.show()
    sys.exit(app.exec())
