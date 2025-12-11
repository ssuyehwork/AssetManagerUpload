# G:\PYthon\AssetManager\ui\dialogs.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                             QHBoxLayout, QPushButton, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QColor, QPalette 

from services.local_store import LocalStoreService
from ui.tag_widget import TagInputArea

# ==================== 样式预加载（模块级） ====================
# 在模块加载时就编译好样式，避免首次显示时的延迟
_DIALOG_BASE_STYLE = """
    QDialog {
        background-color: #1F1F1F;
    }
"""

_TITLE_STYLE = "color: #E0E0E0; font-weight: bold; font-size: 14px; font-family: 'Microsoft YaHei'; border: none; background: transparent;"
_HINT_STYLE = "color: #888888; font-size: 12px; font-family: 'Microsoft YaHei'; border: none; background: transparent;"

_INPUT_STYLE = """
    QLineEdit {
        background-color: #2D2D2D;
        border: 1px solid #383838;
        border-radius: 4px;
        color: #CCCCCC;
        padding: 8px;
        font-size: 12px;
    }
"""
_BTN_CANCEL_STYLE = """
    QPushButton {
        background-color: transparent;
        border: 1px solid #444444;
        color: #CCCCCC;
        border-radius: 4px;
        padding: 6px 16px;
        font-size: 13px;
        font-family: 'Microsoft YaHei';
    }
    QPushButton:hover { background-color: #333333; border-color: #555555; }
"""
_BTN_SAVE_STYLE = """
    QPushButton {
        background-color: #0078D7;
        border: none;
        color: #FFFFFF;
        border-radius: 4px;
        padding: 6px 16px;
        font-size: 13px;
        font-weight: bold;
        font-family: 'Microsoft YaHei';
    }
    QPushButton:hover { background-color: #0063B1; }
    QPushButton:pressed { background-color: #005A9E; }
"""

class AutoTagDialog(QDialog):
    def __init__(self, folder_path, parent=None):
        super().__init__(parent)
        self.folder_path = folder_path
        self.result_tags = []
        self.popup = None

        self.setWindowOpacity(0)
        self.setStyleSheet(_DIALOG_BASE_STYLE)
        
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor("#1F1F1F"))
        self.setPalette(pal)
        
        self.setWindowTitle("设置自动标签")
        self.setFixedSize(480, 320)
        
        self.setup_ui()
        self.load_current()
        
        QTimer.singleShot(50, lambda: self.setWindowOpacity(1))

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # --- 文件夹路径 ---
        folder_block = QVBoxLayout()
        folder_block.setSpacing(8)
        lbl_name = QLabel("文件夹路径")
        lbl_name.setStyleSheet(_TITLE_STYLE)
        folder_block.addWidget(lbl_name)
        self.txt_folder_name = QLineEdit(self.folder_path)
        self.txt_folder_name.setReadOnly(True)
        self.txt_folder_name.setStyleSheet(_INPUT_STYLE)
        folder_block.addWidget(self.txt_folder_name)
        layout.addLayout(folder_block)

        # --- 标签输入区 (核心修改) ---
        tag_block = QVBoxLayout()
        tag_block.setSpacing(8)
        lbl_tags = QLabel("自动添加标签")
        lbl_tags.setStyleSheet(_TITLE_STYLE)
        tag_block.addWidget(lbl_tags)

        self.tag_input_area = TagInputArea()
        self.tag_input_area.sig_tags_changed.connect(self.on_tags_changed)
        tag_block.addWidget(self.tag_input_area)

        lbl_hint = QLabel("说明：保存后，该文件夹内现有的及未来拖入的文件都将自动绑定以上标签。")
        lbl_hint.setStyleSheet(_HINT_STYLE)
        lbl_hint.setWordWrap(True)
        tag_block.addWidget(lbl_hint)
        layout.addLayout(tag_block)

        layout.addStretch()

        # --- 底部按钮 ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_cancel.setStyleSheet(_BTN_CANCEL_STYLE)
        btn_save = QPushButton("保存配置")
        btn_save.clicked.connect(self.save_tags)
        btn_save.setStyleSheet(_BTN_SAVE_STYLE)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def load_current(self):
        tags = LocalStoreService.get_folder_auto_tags(self.folder_path)
        self.tag_input_area.set_tags(tags)

    def on_tags_changed(self, tags):
        self.result_tags = tags

    def save_tags(self):
        # result_tags 已经通过 on_tags_changed 实时更新
        self.accept()