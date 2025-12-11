# G:\PYthon\AssetManager\ui\dialogs.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                             QHBoxLayout, QPushButton, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QColor, QPalette 

from services.local_store import LocalStoreService
from ui.tag_widget import TagInputArea

# ==================== 样式预加载（模块级） ====================
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

# 【新增】撤销/恢复按钮样式
_BTN_UNDO_STYLE = """
    QPushButton {
        background-color: transparent;
        border: 1px solid #555555;
        color: #AAAAAA;
        font-size: 12px;
        font-weight: normal;
        padding: 2px 8px;
        border-radius: 3px;
        min-height: 20px;
        font-family: 'Microsoft YaHei';
    }
    QPushButton:hover { 
        background-color: #3a3a3a;
        border-color: #0078D7;
        color: #FFFFFF;
    }
    QPushButton:disabled {
        color: #555555;
        border-color: #3a3a3a;
    }
"""

# 【新增】清空按钮样式
_BTN_CLEAR_STYLE = """
    QPushButton {
        background-color: transparent;
        border: none;
        color: #888888;
        font-size: 16px;
        font-weight: bold;
        padding: 0px;
        min-width: 24px;
        max-width: 24px;
        min-height: 24px;
        max-height: 24px;
    }
    QPushButton:hover { 
        color: #FF5555; 
        background-color: #3a3a3a;
        border-radius: 3px;
    }
"""

class AutoTagDialog(QDialog):
    def __init__(self, folder_path, parent=None):
        super().__init__(parent)
        self.folder_path = folder_path
        self.result_tags = []
        self.popup = None
        
        # 【新增】撤销/恢复历史记录
        self.undo_stack = []  # 撤销栈
        self.redo_stack = []  # 恢复栈

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

        # --- 标签输入区 (新增撤销/恢复和清空按钮) ---
        tag_block = QVBoxLayout()
        tag_block.setSpacing(8)
        
        # 【修改】标题行 - 包含标题、撤销/恢复按钮、清空按钮
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # 垂直居中对齐
        
        lbl_tags = QLabel("自动添加标签")
        lbl_tags.setStyleSheet(_TITLE_STYLE)
        lbl_tags.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # 标签垂直居中
        title_row.addWidget(lbl_tags)
        
        title_row.addStretch()  # 弹簧，把按钮推到右边
        
        # 【新增】撤销按钮
        self.btn_undo = QPushButton("↶")
        self.btn_undo.setStyleSheet(_BTN_UNDO_STYLE)
        self.btn_undo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_undo.setToolTip("撤销上一步操作 (Ctrl+Z)")
        self.btn_undo.clicked.connect(self.undo_action)
        self.btn_undo.setEnabled(False)  # 初始禁用
        title_row.addWidget(self.btn_undo)
        
        # 【新增】恢复按钮
        self.btn_redo = QPushButton("↷")
        self.btn_redo.setStyleSheet(_BTN_UNDO_STYLE)
        self.btn_redo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_redo.setToolTip("恢复上一步撤销 (Ctrl+Y)")
        self.btn_redo.clicked.connect(self.redo_action)
        self.btn_redo.setEnabled(False)  # 初始禁用
        title_row.addWidget(self.btn_redo)
        
        # 【新增】清空按钮
        self.btn_clear_tags = QPushButton("×")
        self.btn_clear_tags.setStyleSheet(_BTN_CLEAR_STYLE)
        self.btn_clear_tags.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear_tags.setToolTip("清空所有标签")
        self.btn_clear_tags.clicked.connect(self.clear_all_tags)
        title_row.addWidget(self.btn_clear_tags)
        
        tag_block.addLayout(title_row)

        # 标签输入区域
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
        # 初始状态保存到撤销栈
        self.save_state(tags)

    def on_tags_changed(self, tags):
        # 保存当前状态到撤销栈
        if tags != self.result_tags:  # 只有标签真正改变时才保存
            self.save_state(self.result_tags)
        self.result_tags = tags
        self.update_button_states()

    # 【新增】保存状态到撤销栈
    def save_state(self, tags):
        self.undo_stack.append(list(tags))  # 深拷贝
        # 清空恢复栈（新操作后无法恢复之前的撤销）
        self.redo_stack.clear()
        self.update_button_states()

    # 【新增】撤销操作
    def undo_action(self):
        if len(self.undo_stack) > 1:  # 至少保留初始状态
            # 当前状态保存到恢复栈
            current = self.undo_stack.pop()
            self.redo_stack.append(current)
            
            # 恢复到上一个状态
            previous = self.undo_stack[-1]
            self.tag_input_area.set_tags(previous)
            self.result_tags = list(previous)
            self.update_button_states()

    # 【新增】恢复操作
    def redo_action(self):
        if self.redo_stack:
            # 从恢复栈取出状态
            next_state = self.redo_stack.pop()
            self.undo_stack.append(next_state)
            
            # 应用状态
            self.tag_input_area.set_tags(next_state)
            self.result_tags = list(next_state)
            self.update_button_states()

    # 【新增】更新按钮状态
    def update_button_states(self):
        self.btn_undo.setEnabled(len(self.undo_stack) > 1)
        self.btn_redo.setEnabled(len(self.redo_stack) > 0)

    # 【新增】清空所有标签
    def clear_all_tags(self):
        if self.result_tags:  # 只有标签不为空时才保存状态
            self.save_state(self.result_tags)
        self.tag_input_area.set_tags([])
        self.result_tags = []
        self.update_button_states()

    def save_tags(self):
        # result_tags 已经通过 on_tags_changed 实时更新
        self.accept()