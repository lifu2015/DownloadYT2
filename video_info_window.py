from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QWidget, QApplication)
from PyQt6.QtCore import Qt
import json
import os

class VideoInfoWindow(QDialog):
    def __init__(self, vinfo_path):
        super().__init__()
        self.vinfo_path = vinfo_path
        self.setup_ui()
        self.load_info()
        
    def setup_ui(self):
        """设置UI界面"""
        self.setWindowTitle("视频信息")
        self.setMinimumSize(500, 400)
        
        # 主布局
        layout = QVBoxLayout(self)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 创建内容容器
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        
        # 设置滚动区域的widget
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)
        
    def format_duration(self, seconds):
        """格式化时长"""
        if not seconds:
            return "未知"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}小时{minutes}分{secs}秒"
        elif minutes > 0:
            return f"{minutes}分{secs}秒"
        else:
            return f"{secs}秒"
            
    def format_date(self, date_str):
        """格式化日期"""
        if not date_str:
            return "未知"
        try:
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        except:
            return date_str
        
    def load_info(self):
        """加载视频信息"""
        try:
            with open(self.vinfo_path, 'r', encoding='utf-8') as f:
                info = json.load(f)
                
            # 定义显示顺序和格式化
            info_display = [
                ("标题", info.get("title", "未知")),
                ("下载时间", info.get("download_time", "未知")),
                ("分辨率", info.get("resolution", "未知")),
                ("视频格式", info.get("format", "未知")),
                ("时长", self.format_duration(info.get("duration"))),
                ("上传日期", self.format_date(info.get("upload_date"))),
                ("观看次数", f"{info.get('view_count', '未知'):,}" if info.get('view_count') else "未知"),
                ("点赞数", f"{info.get('like_count', '未知'):,}" if info.get('like_count') else "未知"),
                ("频道", info.get("channel", "未知")),
                ("频道链接", info.get("channel_url", "未知")),
                ("视频链接", info.get("url", "未知")),
                ("视频描述", info.get("description", "无描述"))
            ]
            
            # 添加所有信息
            for key, value in info_display:
                # 创建可选择的标签
                label = QLabel(f"{key}: {value}")
                label.setTextInteractionFlags(
                    Qt.TextInteractionFlag.TextSelectableByMouse | 
                    Qt.TextInteractionFlag.TextSelectableByKeyboard
                )
                label.setWordWrap(True)  # 允许文本换行
                label.setStyleSheet("""
                    QLabel {
                        padding: 5px;
                        background-color: #f5f5f5;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        margin: 2px;
                    }
                """)
                self.content_layout.addWidget(label)
                
        except Exception as e:
            error_label = QLabel(f"加载信息出错: {str(e)}")
            error_label.setStyleSheet("color: red;")
            self.content_layout.addWidget(error_label)
            
        # 添加弹性空间
        self.content_layout.addStretch()
