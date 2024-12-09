import sys
import os
import json
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                           QTextEdit, QMessageBox)
from PyQt6.QtCore import Qt

class HistoryWindow(QDialog):
    """下载历史窗口"""
    def __init__(self, history_file):
        super().__init__()
        self.history_file = history_file
        self.setup_ui()
        self.load_history()

    def setup_ui(self):
        """设置UI界面"""
        self.setWindowTitle("下载历史")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)

        # 按钮区域
        buttons_layout = QHBoxLayout()

        self.delete_today_btn = QPushButton("删除今日历史")
        self.delete_week_btn = QPushButton("删除本周历史")
        self.delete_month_btn = QPushButton("删除一个月内历史")
        self.delete_all_btn = QPushButton("删除全部历史")

        self.delete_today_btn.clicked.connect(lambda: self.delete_history('today'))
        self.delete_week_btn.clicked.connect(lambda: self.delete_history('week'))
        self.delete_month_btn.clicked.connect(lambda: self.delete_history('month'))
        self.delete_all_btn.clicked.connect(lambda: self.delete_history('all'))

        buttons_layout.addWidget(self.delete_today_btn)
        buttons_layout.addWidget(self.delete_week_btn)
        buttons_layout.addWidget(self.delete_month_btn)
        buttons_layout.addWidget(self.delete_all_btn)

        layout.addLayout(buttons_layout)

        # 历史显示区域
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        layout.addWidget(self.history_text)

        # 应用样式
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
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #3d7ab3;
            }
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
            }
        """)

    def load_history(self):
        """加载历史记录"""
        self.history_text.clear()
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    for item in reversed(history):
                        # 兼容旧版本的历史记录
                        download_time = item.get('download_time') or item.get('timestamp', '未知')
                        self.history_text.append(
                            f"标题: {item.get('title', '未知')}\n"
                            f"时间: {download_time}\n"
                            f"分辨率: {item.get('resolution', '未知')}\n"
                            f"原始URL: {item.get('url', '未知')}\n"
                            f"文件: {item.get('file_path', '未知')}\n"
                            f"{'-'*50}\n"
                        )
            except Exception as e:
                self.history_text.setText(f"加载历史记录失败: {str(e)}")

    def delete_history(self, period):
        """删除指定时期的历史记录"""
        if not os.path.exists(self.history_file):
            return

        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)

            now = datetime.now()
            new_history = []

            for item in history:
                # 兼容旧版本的历史记录
                time_str = item.get('download_time')
                if not time_str and 'timestamp' in item:
                    # 将旧版本的时间戳转换为新格式
                    timestamp = item['timestamp']
                    try:
                        dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        time_str = "未知"
                
                if not time_str:
                    # 如果无法获取时间，保留该记录
                    new_history.append(item)
                    continue

                try:
                    download_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                    keep = True

                    if period == 'today':
                        keep = not (download_time.date() == now.date())
                    elif period == 'week':
                        keep = not (now - download_time <= timedelta(days=7))
                    elif period == 'month':
                        keep = not (now - download_time <= timedelta(days=30))
                    elif period == 'all':
                        keep = False

                    if keep:
                        new_history.append(item)
                except:
                    # 如果日期解析失败，保留该记录
                    new_history.append(item)

            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(new_history, f, ensure_ascii=False, indent=2)

            self.load_history()
            QMessageBox.information(self, "成功", "历史记录已删除")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"删除历史记录失败: {str(e)}")
