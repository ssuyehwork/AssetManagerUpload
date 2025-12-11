# /ui/tag_suggestion.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QGridLayout, QWidget, 
                             QLabel, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QColor

from services.preference_service import PreferenceService
from ui.tag_widget import TagGridItem 

class TagSuggestPopup(QDialog):
    """一个支持多选的、显示最近使用标签的弹出窗口。"""
    # 信号：当选择的标签集合发生变化时发出
    sig_selection_changed = pyqtSignal(list)

    def __init__(self, current_tags, parent=None):
        super().__init__(parent)
        self.selected_tags = set(current_tags)
        
        # 窗口设置
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setFixedHeight(280)
        
        # 样式
        self.setStyleSheet("""
            QDialog { 
                background-color: #1E1E1E; 
                border: 1px solid #333; 
                border-radius: 4px; 
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
        self.load_and_display_tags()

        # 事件过滤器
        self.installEventFilter(self)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("border: none; background: transparent;")
        
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(10, 8, 10, 10)
        self.content_layout.setSpacing(8)
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

        footer = QLabel("移动: ↑↓  选中: Space/Enter  关闭: Esc")
        footer.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        footer.setStyleSheet("color: #666; font-size: 11px; padding: 6px 10px; background-color: #252526; border-top: 1px solid #333;")
        layout.addWidget(footer)

    def load_and_display_tags(self):
        """加载、渲染标签并刷新导航项。"""
        # 清空现有内容
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.nav_items = []

        recent_tags = PreferenceService.get_recent_tags()[:20]
        
        if not recent_tags:
            lbl = QLabel("没有最近使用的标签")
            lbl.setStyleSheet("color: #666; font-style: italic; margin-top: 20px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(lbl)
            self.content_layout.addStretch()
            return
        
        # 【UI修复】重新加入“最近使用”标题，并采用紧凑样式
        title_label = QLabel(f"最近使用 ({len(recent_tags)})")
        title_label.setStyleSheet("color: #888; font-size: 11px; font-weight: bold; margin-bottom: 4px;")
        self.content_layout.addWidget(title_label)
        
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setVerticalSpacing(2)
        grid.setHorizontalSpacing(8)
        
        for i, tag in enumerate(recent_tags):
            row, col = i // 2, i % 2
            is_selected = tag in self.selected_tags
            item = TagGridItem(tag, is_recent=True, is_selected=is_selected)
            item.sig_clicked.connect(self.toggle_tag_selection)
            grid.addWidget(item, row, col)
            self.nav_items.append(item)
            
        self.content_layout.addWidget(grid_widget)
        self.content_layout.addStretch()

        if self.nav_items:
            self.current_nav_index = 0
            self.nav_items[0].set_highlight(True)

    def toggle_tag_selection(self, tag):
        """切换单个标签的选中状态。"""
        if tag in self.selected_tags:
            self.selected_tags.remove(tag)
        else:
            self.selected_tags.add(tag)
        
        # 刷新UI以显示勾选状态
        self.load_and_display_tags() 
        # 发出信号，通知父组件选择集已变更
        self.sig_selection_changed.emit(list(self.selected_tags))

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key in [Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space, Qt.Key.Key_Escape]:
                if key == Qt.Key.Key_Down: self.move_selection(1)
                elif key == Qt.Key.Key_Up: self.move_selection(-1)
                elif key in [Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space]:
                    self.trigger_current_selection()
                elif key == Qt.Key.Key_Escape: self.close()
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
            self.toggle_tag_selection(item.text_val)
