# /ui/tag_suggestion.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QGridLayout, QWidget,
                             QLabel, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QColor

from services.preference_service import PreferenceService
from ui.tag_widget import TagGridItem

class TagSuggestPopup(QDialog):
    """一个只显示最近使用标签的弹出建议窗口。"""
    sig_tag_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # 窗口设置
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setFixedHeight(260) # 只设置固定高度，宽度将由外部控制

        # 样式
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E1E;
                border: 1px solid #333;
                border-radius: 6px;
            }
            QScrollBar:vertical {
                background: #1E1E1E; width: 8px;
            }
            QScrollBar::handle:vertical {
                background: #444; border-radius: 4px;
            }
        """)

        # 成员变量
        self.nav_items = []
        self.current_nav_index = -1

        # 初始化UI
        self.setup_ui()
        self.load_tags()

        # 安装事件过滤器以捕获键盘事件
        self.installEventFilter(self)

    def setup_ui(self):
        """构建UI界面。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)

        # --- 滚动区域 ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("border: none; background: transparent;")

        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(content_widget)
        # 顶部留出更少空间
        self.content_layout.setContentsMargins(10, 5, 10, 10)
        self.content_layout.setSpacing(8)

        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

        # --- 底部提示 ---
        footer = QLabel("移动: ↑↓  选中: Enter  关闭: Esc")
        footer.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        footer.setStyleSheet("color: #666; font-size: 11px; padding: 6px 10px; background-color: #252526; border-top: 1px solid #333;")
        layout.addWidget(footer)

    def load_tags(self):
        """加载并显示最近的标签。"""
        recent_tags = PreferenceService.get_recent_tags()[:20]

        if not recent_tags:
            lbl = QLabel("没有最近使用的标签")
            lbl.setStyleSheet("color: #666; font-style: italic; margin-top: 20px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(lbl)
            self.content_layout.addStretch()
            return

        # --- 创建网格布局来展示标签 ---
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setVerticalSpacing(2)
        grid.setHorizontalSpacing(8)

        # 【UI优化】移除独立的标题 QLabel

        self.nav_items = []
        for i, tag in enumerate(recent_tags):
            row, col = i // 2, i % 2
            item = TagGridItem(tag, is_recent=True, is_selected=False)
            item.sig_clicked.connect(self.on_tag_clicked)
            grid.addWidget(item, row, col)
            self.nav_items.append(item)

        self.content_layout.addWidget(grid_widget)
        self.content_layout.addStretch()

        if self.nav_items:
            self.current_nav_index = 0
            self.nav_items[0].set_highlight(True)

    def on_tag_clicked(self, tag):
        self.sig_tag_selected.emit(tag)
        self.close()

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key in [Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Escape]:
                if key == Qt.Key.Key_Down:
                    self.move_selection(1)
                elif key == Qt.Key.Key_Up:
                    self.move_selection(-1)
                elif key in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
                    self.trigger_current_selection()
                elif key == Qt.Key.Key_Escape:
                    self.close()
                return True

        if event.type() == QEvent.Type.WindowDeactivate:
            self.close()

        return super().eventFilter(source, event)

    def move_selection(self, step):
        count = len(self.nav_items)
        if count == 0: return

        if 0 <= self.current_nav_index < count:
            self.nav_items[self.current_nav_index].set_highlight(False)

        self.current_nav_index = (self.current_nav_index + step + count) % count

        target = self.nav_items[self.current_nav_index]
        target.set_highlight(True)

    def trigger_current_selection(self):
        if 0 <= self.current_nav_index < len(self.nav_items):
            item = self.nav_items[self.current_nav_index]
            self.on_tag_clicked(item.text_val)
