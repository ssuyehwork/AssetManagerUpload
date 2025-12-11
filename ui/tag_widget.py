# G:\PYthon\AssetManager\ui\tag_widget.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QFrame, QScrollArea, QDialog, 
                             QGridLayout, QLayout, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect, QSize, QEvent
from PyQt6.QtGui import QColor, QCursor, QPainter, QPen

import data_manager
from services.preference_service import PreferenceService

# ==================== 0. 基础：流式布局 ====================
class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, hSpacing=6, vSpacing=6):
        super(FlowLayout, self).__init__(parent)
        self._hSpace = hSpacing
        self._vSpace = vSpacing
        self._items = []
        # 初始化设置边距
        self.setContentsMargins(margin, margin, margin, margin)

    def addItem(self, item): self._items.append(item)
    def horizontalSpacing(self): return self._hSpace
    def verticalSpacing(self): return self._vSpace
    def expandingDirections(self): return Qt.Orientation(0)
    def hasHeightForWidth(self): return True
    def heightForWidth(self, width): return self.doLayout(QRect(0, 0, width, 0), True)
    def count(self): return len(self._items)
    def itemAt(self, index): return self._items[index] if 0 <= index < len(self._items) else None
    def minimumSize(self):
        size = QSize()
        for item in self._items: size = size.expandedTo(item.minimumSize())
        left, top, right, bottom = self.getContentsMargins()
        size += QSize(left + right, top + bottom)
        return size
        
    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)
    def sizeHint(self): return self.minimumSize()
    def takeAt(self, index): return self._items.pop(index) if 0 <= index < len(self._items) else None

    def doLayout(self, rect, testOnly):
        left, top, right, bottom = self.getContentsMargins()
        effectiveRect = rect.adjusted(left, top, -right, -bottom)
        x = effectiveRect.x()
        y = effectiveRect.y()
        lineHeight = 0
        for item in self._items:
            wid = item.widget()
            spaceX = self.horizontalSpacing()
            spaceY = self.verticalSpacing()
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > effectiveRect.right() and lineHeight > 0:
                x = effectiveRect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0
            if not testOnly: 
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())
        return y + lineHeight - rect.y() + bottom

# ==================== 1. 标签块 (Tag Chip) - 增强样式优先级 ====================
class TagChip(QFrame):
    sig_remove = pyqtSignal(str) 

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text = text
        
        # 设置尺寸策略为自适应宽度
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(28)
        
        # 【关键修复】使用 TagChip 类名选择器提高优先级，避免被全局样式覆盖
        self.setStyleSheet("""
            TagChip { 
                background-color: #3C3C3C !important; 
                border: 1px solid #505050 !important; 
                border-radius: 4px; 
            }
            TagChip:hover { 
                background-color: #444 !important;
                border: 1px solid #888 !important; 
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 4, 0)
        layout.setSpacing(4)
        
        # 标签文本
        lbl = QLabel(text)
        lbl.setObjectName("TagChipLabel")  # 设置对象名便于定位
        lbl.setStyleSheet("""
            QLabel#TagChipLabel { 
                border: none !important; 
                background: transparent !important; 
                color: #E0E0E0 !important; 
                font-size: 12px;
            }
        """)
        lbl.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        layout.addWidget(lbl)
        
        # 【关键修复】关闭按钮使用更高优先级样式
        btn_close = QPushButton("×")
        btn_close.setObjectName("TagChipCloseBtn")  # 设置对象名
        btn_close.setFixedSize(20, 20)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton#TagChipCloseBtn { 
                border: none !important; 
                background: transparent !important; 
                color: #AAAAAA !important;          
                font-family: Arial; 
                font-size: 18px;
                font-weight: normal;
                padding: 0px !important;
                margin: 0px !important;
            }
            QPushButton#TagChipCloseBtn:hover { 
                color: #FF5555 !important;       
                background: transparent !important;
            }
            QPushButton#TagChipCloseBtn:pressed { 
                background: transparent !important;
            }
        """)
        btn_close.clicked.connect(lambda: self.sig_remove.emit(self.text))
        layout.addWidget(btn_close)
        
        # 调整整体宽度以适应内容
        self.adjustSize()

# ==================== 2. 下拉项 (Grid Item) ====================
class TagGridItem(QFrame):
    sig_clicked = pyqtSignal(str) 

    def __init__(self, text, is_recent=False, is_selected=False, parent=None):
        super().__init__(parent)
        self.text_val = text
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(30)
        
        self.default_style = """
            QFrame { background-color: transparent; border-radius: 3px; border: 1px solid transparent; }
            QFrame:hover { background-color: #2D2D2D; border: 1px solid #444; }
        """
        self.selected_style = """
            QFrame { background-color: #1A3650; border-radius: 3px; border: 1px solid #2B5C8A; }
            QFrame:hover { background-color: #1F4060; }
        """
        self.highlight_style = """
            QFrame { background-color: #2D2D2D; border-radius: 3px; border: 1px solid #0078D7; }
        """
        
        if is_selected:
            self.setStyleSheet(self.selected_style)
        else:
            self.setStyleSheet(self.default_style)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(8)

        lbl_icon = QLabel()
        if is_recent:
            lbl_icon.setText("🕒")
            lbl_icon.setStyleSheet("color: #888; font-size: 11px; border: none; background: transparent;")
        else:
            lbl_icon.setText("#") 
            lbl_icon.setStyleSheet("color: #555; font-size: 12px; font-weight: bold; border: none; background: transparent;")
        layout.addWidget(lbl_icon)

        self.lbl_text = QLabel(text)
        text_color = "#FFFFFF" if is_selected else "#CCCCCC"
        self.lbl_text.setStyleSheet(f"color: {text_color}; font-size: 12px; border: none; background: transparent;")
        layout.addWidget(self.lbl_text, 1)

        self.lbl_check = QLabel("✔")
        self.lbl_check.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 12px; border: none; background: transparent;")
        if not is_selected:
            self.lbl_check.hide()
        layout.addWidget(self.lbl_check)

        self.is_selected = is_selected

    def set_highlight(self, active):
        if self.is_selected: return
        if active:
            self.setStyleSheet(self.highlight_style)
        else:
            self.setStyleSheet(self.default_style)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.sig_clicked.emit(self.text_val)

# ==================== 3. 弹窗容器 (Popup) ====================
class TagSelectionPopup(QDialog):
    sig_tags_changed = pyqtSignal(list) 
    # 【正确实现】定义一个新信号，只用于传递被选中的标签文本
    sig_tag_selected_for_input = pyqtSignal(str)

    def __init__(self, current_tags, parent=None, selection_mode='multi'):
        super().__init__(parent)
        self.selection_mode = selection_mode
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(360, 420)
        
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
        
        self.selected_tags = set(current_tags) 
        self.all_db_tags = []
        self.recent_tags = []
        self.nav_items = [] 
        self.current_nav_index = -1

        self.setup_ui()
        self.load_data()
        
        self.search_input.installEventFilter(self)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        search_frame = QFrame()
        search_frame.setStyleSheet("border-bottom: 1px solid #333; background-color: #252526;")
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(12, 12, 12, 12)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索或创建标签...")
        self.search_input.setStyleSheet("""
            QLineEdit { 
                background-color: #3C3C3C; 
                border: 1px solid #3C3C3C; 
                border-radius: 2px; 
                color: #CCCCCC; 
                padding: 6px 8px;
                font-size: 13px;
            }
            QLineEdit:focus { 
                border: 1px solid #0078D7; 
                background-color: #1E1E1E;
            }
        """)
        self.search_input.textChanged.connect(self.on_search)
        search_layout.addWidget(self.search_input)
        layout.addWidget(search_frame)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("border: none; background: transparent;")
        
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(12, 12, 12, 12)
        self.content_layout.setSpacing(8) 
        
        self.scroll_area.setWidget(self.content_widget)
        layout.addWidget(self.scroll_area)

        footer = QLabel("移动: ↑↓  选中: Enter  关闭: Esc")
        footer.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        footer.setStyleSheet("color: #666; font-size: 11px; padding: 6px 12px; background-color: #252526; border-top: 1px solid #333;")
        layout.addWidget(footer)

    def eventFilter(self, source, event):
        if source == self.search_input and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Down:
                self.move_selection(1)
                return True
            elif key == Qt.Key.Key_Up:
                self.move_selection(-1)
                return True
            elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
                self.trigger_current_selection()
                return True
            elif key == Qt.Key.Key_Escape:
                self.close()
                return True
        return super().eventFilter(source, event)

    def move_selection(self, step):
        count = len(self.nav_items)
        if count == 0: return
        
        if 0 <= self.current_nav_index < count:
            self.nav_items[self.current_nav_index].set_highlight(False)
            
        self.current_nav_index += step
        if self.current_nav_index >= count: self.current_nav_index = 0
        if self.current_nav_index < 0: self.current_nav_index = count - 1
        
        target = self.nav_items[self.current_nav_index]
        target.set_highlight(True)
        self.scroll_area.ensureWidgetVisible(target)

    def trigger_current_selection(self):
        if 0 <= self.current_nav_index < len(self.nav_items):
            item = self.nav_items[self.current_nav_index]
            if isinstance(item, TagGridItem):
                self.toggle_tag(item.text_val)
            elif hasattr(item, "is_create_btn"):
                text = self.search_input.text().strip()
                self.create_and_select_tag(text)

    def load_data(self):
        self.all_db_tags = data_manager.get_all_tags()
        self.recent_tags = PreferenceService.get_recent_tags()
        self.refresh_ui()

    def refresh_ui(self, filter_text=""):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        
        self.nav_items = []
        self.current_nav_index = -1
        filter_text = filter_text.strip().lower()

        if not self.all_db_tags and not filter_text:
            lbl = QLabel("暂无标签，请输入文字创建")
            lbl.setStyleSheet("color: #666; font-style: italic; margin-top: 20px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(lbl)
            self.content_layout.addStretch()
            return

        matches = []
        if filter_text:
            matches = [t for t in self.all_db_tags if filter_text in t.lower()]
            db_tags_lower = [t.lower() for t in self.all_db_tags]
            
            if filter_text not in db_tags_lower:
                self.add_create_button(self.search_input.text().strip())
            
            if matches:
                self.add_section("搜索结果", matches)
        else:
            if self.recent_tags:
                self.add_section("最近使用", self.recent_tags, is_recent=True)
            
            others = [t for t in self.all_db_tags if t not in self.recent_tags]
            if others:
                self.add_section("所有标签", others, is_recent=False)

        self.content_layout.addStretch() 

        if self.nav_items:
            self.current_nav_index = 0
            self.nav_items[0].set_highlight(True)

    def add_create_button(self, text):
        btn = QPushButton(f"＋ 新建标签 \"{text}\"")
        btn.setStyleSheet("""
            QPushButton { 
                text-align: left; 
                padding: 8px; 
                color: #4CAF50; 
                font-weight: bold; 
                background: #252526; 
                border: 1px dashed #4CAF50; 
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #2D2D2D; }
        """)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self.create_and_select_tag(text))
        
        btn.set_highlight = lambda active: btn.setStyleSheet(
            f"QPushButton {{ text-align: left; padding: 8px; color: #4CAF50; font-weight: bold; background: {'#2D2D2D' if active else '#252526'}; border: 1px dashed #4CAF50; border-radius: 4px; }}"
        )
        btn.is_create_btn = True
        
        self.content_layout.addWidget(btn)
        self.nav_items.append(btn)

    def add_section(self, title, tags, is_recent=False):
        lbl_title = QLabel(f"{title} ({len(tags)})")
        lbl_title.setStyleSheet("color: #888; font-size: 11px; font-weight: bold; text-transform: uppercase;")
        self.content_layout.addWidget(lbl_title)

        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setVerticalSpacing(2) 
        grid.setHorizontalSpacing(8)
        
        for i, tag in enumerate(tags):
            row = i // 2
            col = i % 2
            
            is_selected = tag in self.selected_tags
            item = TagGridItem(tag, is_recent, is_selected)
            item.sig_clicked.connect(self.toggle_tag)
            
            grid.addWidget(item, row, col)
            self.nav_items.append(item)
            
        self.content_layout.addWidget(grid_widget)

    def on_search(self, text):
        self.refresh_ui(text)

    def toggle_tag(self, tag):
        # 【最终修复】根据选择模式决定行为
        if self.selection_mode == 'single':
            # 单选模式：只发射信号，不改变内部状态
            self.sig_tag_selected_for_input.emit(tag)
        else:
            # 默认多选模式：更新内部状态并刷新
            if tag in self.selected_tags:
                self.selected_tags.remove(tag)
            else:
                self.selected_tags.add(tag)
                PreferenceService.add_recent_tag(tag)

            self.sig_tags_changed.emit(list(self.selected_tags))
            self.search_input.setFocus()

            old_idx = self.current_nav_index
            self.refresh_ui(self.search_input.text())

            if 0 <= old_idx < len(self.nav_items):
                self.current_nav_index = old_idx
                if len(self.nav_items) > 0: self.nav_items[0].set_highlight(False)
                self.nav_items[old_idx].set_highlight(True)

    def create_and_select_tag(self, tag):
        data_manager.add_tag(tag)
        PreferenceService.add_recent_tag(tag)
        self.selected_tags.add(tag)
        
        self.all_db_tags = data_manager.get_all_tags()
        self.recent_tags = PreferenceService.get_recent_tags()
        
        self.search_input.clear()
        self.refresh_ui()
        self.sig_tags_changed.emit(list(self.selected_tags))

# ==================== 4. 标签输入区域 (对外接口) ====================
class TagInputArea(QFrame):
    sig_tags_changed = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tags = []
        self.popup = None
        
        # 【修改】最小高度从 52 减少到 47 (减少5px)
        self.setMinimumHeight(47) 
        
        # 【增强】使用对象名提高样式优先级
        self.setObjectName("TagInputArea")
        self.setStyleSheet("""
            QFrame#TagInputArea {
                background-color: #252525 !important; 
                border: 1px solid #444 !important; 
                border-radius: 4px;
            }
            QFrame#TagInputArea:hover { 
                border: 1px solid #0078D7 !important; 
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.layout = FlowLayout(self, margin=7, hSpacing=8, vSpacing=8)
        
        self.lbl_placeholder = QLabel("点击设置标签...")
        self.lbl_placeholder.setStyleSheet("color: #666; font-style: italic; margin-left: 4px; border: none;")
        self.layout.addWidget(self.lbl_placeholder)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.show_popup()
        super().mousePressEvent(event)

    def set_tags(self, tags_list):
        self.tags = list(tags_list)
        self.render()

    def get_tags(self):
        return self.tags

    def render(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.tags:
            self.layout.addWidget(self.lbl_placeholder)
            self.lbl_placeholder.show()
        else:
            self.lbl_placeholder.hide()
            for tag in self.tags:
                chip = TagChip(tag)
                chip.sig_remove.connect(self.remove_tag)
                self.layout.addWidget(chip)
        
        self.updateGeometry()

    def remove_tag(self, tag):
        if tag in self.tags:
            self.tags.remove(tag)
            self.render()
            
            self.sig_tags_changed.emit(self.tags)
            
            if self.popup and self.popup.isVisible():
                self.popup.selected_tags = set(self.tags)
                self.popup.refresh_ui(self.popup.search_input.text())

    def show_popup(self):
        self.popup = TagSelectionPopup(self.tags, self)
        self.popup.sig_tags_changed.connect(self.on_popup_tags_changed)
        
        global_pos = self.mapToGlobal(QPoint(0, self.height() + 4))
        self.popup.move(global_pos)
        self.popup.show()
        self.popup.search_input.setFocus()

    def on_popup_tags_changed(self, new_tags):
        self.tags = new_tags
        self.render()
        
        self.sig_tags_changed.emit(self.tags)