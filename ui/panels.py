# G:\PYthon\AssetManager\ui\panels.py

import os
import subprocess
import time
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QAbstractItemView, QMenu, QFileIconProvider, QPushButton, 
    QApplication, QLabel, QTreeView, QFrame, QScrollArea, QLayout, QSizePolicy,
    QLineEdit, QCompleter, QTreeWidgetItemIterator, QStyleOptionViewItem
)
from PyQt6.QtGui import QPalette, QColor, QCursor, QIcon, QPixmap
from PyQt6.QtCore import Qt, QFileInfo, pyqtSignal, QPoint, QRect, QSize, QStringListModel

try:
    from data_manager import add_favorite, remove_favorite, get_favorites
except ImportError:
    def add_favorite(path): pass
    def remove_favorite(path): pass
    def get_favorites(): return []

from services.preference_service import PreferenceService
# 【核心修复】从 tag_widget 导入正确的弹窗
from ui.tag_widget import TagInputArea
from services.tag_service import TagService

# ==================== TagFlowLayout ====================
class TagFlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, hSpacing=6, vSpacing=6):
        super(TagFlowLayout, self).__init__(parent)
        self._hSpace = hSpacing
        self._vSpace = vSpacing
        self._items = []
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
        super(TagFlowLayout, self).setGeometry(rect)
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

# ==================== ClickableLineEdit (for tag input) ====================
class ClickableLineEdit(QLineEdit):
    """A QLineEdit that emits a 'clicked' signal on mouse press."""
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

# ==================== Utils ====================
def format_time(t): return time.strftime("%Y/%m/%d %H:%M", time.localtime(t)) if t else "-"
def get_dark_palette():
    p = QPalette()
    p.setColor(QPalette.ColorRole.Base, QColor("#252525"))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor("#2a2a2a"))
    p.setColor(QPalette.ColorRole.Text, QColor("#cccccc"))
    p.setColor(QPalette.ColorRole.Highlight, QColor("#0078d7"))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    return p

class FloatingCopyBtn(QPushButton):
    def __init__(self, parent=None):
        super().__init__("复制", parent)
        self.setObjectName("FloatCopyBtn")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hide()
        self.clicked.connect(self.do_copy)
        self._target_text = ""
        self.setStyleSheet("""
            QPushButton#FloatCopyBtn {
                background-color: #0078d7; color: white; border: 1px solid #005a9e; border-radius: 3px; 
                padding: 2px 5px; font-weight: bold; font-size: 11px;
            }
            QPushButton#FloatCopyBtn:hover { background-color: #006cc1; }
        """)
    def show_at(self, global_pos, text):
        self._target_text = text
        self.adjustSize()
        parent = self.parent()
        local_pos = parent.mapFromGlobal(global_pos)
        parent_width = parent.width()
        btn_width = self.width()
        target_x = local_pos.x() + 10
        target_y = local_pos.y() - 25 
        if target_x + btn_width > parent_width - 5:
            target_x = local_pos.x() - btn_width - 10
        self.move(target_x, target_y)
        self.show()
        self.raise_()
    def do_copy(self):
        if self._target_text:
            QApplication.clipboard().setText(self._target_text)
            self.hide()

class SelectableLabel(QLabel):
    def __init__(self, text="", parent_panel=None):
        super().__init__(text)
        self.parent_panel = parent_panel
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setStyleSheet("background-color: transparent; padding: 2px; color: #ddd;")
        self.setCursor(Qt.CursorShape.IBeamCursor)
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.parent_panel: self.parent_panel.check_selection(self)

# ==================== Favorites ====================
class FavoritesListWidget(QListWidget):
    sig_favorite_clicked = pyqtSignal(str)
    sig_set_auto_tag = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.setPalette(get_dark_palette())
        self.setStyleSheet("""
            QListWidget { border: none; background-color: #252525; }
            QListWidget::item { height: 32px; padding-left: 8px; color: #ddd; border-bottom: 1px solid #2a2a2a; }
            QListWidget::item:hover { background-color: #333; }
            QListWidget::item:selected { background-color: #444; border-left: 3px solid #0078d7; }
        """)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_menu)
        self.icon_provider = QFileIconProvider()
        self.itemClicked.connect(self.on_item_click)
        self.itemDoubleClicked.connect(self.on_item_click)
        self.load_favorites()

    def load_favorites(self):
        self.clear()
        favs = get_favorites()
        for path in favs:
            info = QFileInfo(path)
            display_name = info.fileName() or path
            item = QListWidgetItem(f" {display_name}")
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            if os.path.exists(path): item.setIcon(self.icon_provider.icon(info))
            else: item.setForeground(QColor("#777"))
            self.addItem(item)

    def remove_by_path(self, path):
        remove_favorite(path)
        self.load_favorites()

    def on_item_click(self, item):
        if not item: return
        raw_data = item.data(Qt.ItemDataRole.UserRole)
        path = str(raw_data) if raw_data else ""
        if path: self.sig_favorite_clicked.emit(path)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()
        else: event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.LinkAction)
            event.accept()
        else: event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if path: add_favorite(path)
            self.load_favorites()
            event.accept()
        else: event.ignore()

    def show_menu(self, pos):
        item = self.itemAt(pos)
        if not item: return
        path = str(item.data(Qt.ItemDataRole.UserRole))
        
        logging.critical(f">>> [面板] 收藏夹右键菜单触发，路径: {path}")

        menu = QMenu(self)
        action_remove = menu.addAction("从“收藏夹”中移除")
        action_remove.triggered.connect(lambda: self.do_remove(path))
        
        if os.path.isdir(path):
            menu.addSeparator()
            action_tag = menu.addAction("🏷️ 设置自动标签...")
            def emit_auto_tag_signal():
                logging.critical(f"!!! [面板] 用户点击了 '设置自动标签'，正在发射信号，路径: {path}")
                self.sig_set_auto_tag.emit(path)
            action_tag.triggered.connect(emit_auto_tag_signal)
            menu.addSeparator()

        action_explore = menu.addAction("在资源管理器中显示")
        action_explore.triggered.connect(lambda: subprocess.run(['explorer', '/select,', path.replace("/", "\\")]))
        
        menu.exec(self.mapToGlobal(pos))

    def do_remove(self, path):
        remove_favorite(path)
        self.load_favorites()

    def add_favorite(self, path):
        add_favorite(path)
        self.load_favorites()

class FavoritesPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.list_view = FavoritesListWidget()
        layout.addWidget(self.list_view)

# ==================== MetadataPanel (Refactored) ====================
class MetadataPanel(QWidget):
    # This new signal will be emitted to the main window to handle data saving and model updates.
    sig_tags_updated = pyqtSignal(str, list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file_path = None
        self.current_tags = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Top part (unchanged) ---
        self.table = QTableWidget(8, 2) 
        self.table.setHorizontalHeaderLabels(["属性", "值"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setPalette(get_dark_palette())
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setFixedHeight(285) 
        layout.addWidget(self.table, 0)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #000; border: none; min-height: 1px; max-height: 1px;")
        layout.addWidget(line)

        # --- Tag Area (Refactored) ---
        tag_container = QWidget()
        tag_container.setStyleSheet("background-color: #252525;")
        tag_layout = QVBoxLayout(tag_container)
        tag_layout.setContentsMargins(10, 10, 10, 10)
        tag_layout.setSpacing(8)

        lbl_tag_title = QLabel("标签")
        lbl_tag_title.setStyleSheet("color: #ccc; font-weight: bold; font-size: 12px;")
        tag_layout.addWidget(lbl_tag_title)

        self.tag_input_area = TagInputArea()
        self.tag_input_area.setEnabled(False)
        # Connect the internal widget's signal to our new emitter method
        self.tag_input_area.sig_tags_changed.connect(self._emit_tags_updated)
        tag_layout.addWidget(self.tag_input_area, 1)

        layout.addWidget(tag_container, 1)
        # --- End of Tag Area Refactor ---

        self.copy_btn = FloatingCopyBtn(self)

    def _emit_tags_updated(self, new_tags_list):
        """
        This method is a slot that receives the tag list from the TagInputArea
        and emits it along with the current file path to the main window.
        """
        if self.current_file_path:
            # We must check if the tags have actually changed to prevent loops
            # and unnecessary updates, especially on initial load.
            if set(new_tags_list) != set(self.current_tags):
                self.sig_tags_updated.emit(self.current_file_path, new_tags_list)

    def clear_info(self):
        """Clears all displayed information."""
        self.table.clearContents()
        self.current_file_path = None
        self.current_tags = []
        self.tag_input_area.set_tags([])
        self.tag_input_area.setEnabled(False)

    def check_selection(self, label):
        """Shows copy button if text is selected in a label."""
        if label.hasSelectedText():
            self.copy_btn.show_at(QCursor.pos(), label.selectedText().strip())
        else:
            self.copy_btn.hide()

    def update_info(self, filename, info):
        """Updates the panel with new file information."""
        self.copy_btn.hide()
        
        def row(i, k, v):
            self.table.setItem(i, 0, QTableWidgetItem(k))
            self.table.setCellWidget(i, 1, SelectableLabel(str(v), self))

        row(0, "文件名", filename)
        ftype = info.get("type", "")
        row(1, "类型", "文件夹" if ftype == "FOLDER" else (info.get("ext", "").upper().replace(".", "") + " 文件"))
        sz = info.get("size", 0)
        row(2, "大小", f"{sz} B" if sz < 1024 else (f"{sz/1024:.1f} KB" if sz < 1048576 else f"{sz/1048576:.1f} MB"))
        row(3, "修改时间", format_time(info.get("mtime")))
        row(4, "创建时间", format_time(info.get("ctime")))
        row(5, "上次访问", format_time(info.get("atime")))
        row(6, "访问次数", f"{info.get('view_count', 0)} 次")
        r = info.get("rating", 0)
        row(7, "评级", "★" * r if r else "无")

        # Update the tags using the new widget
        self.current_tags = info.get("tags", [])
        self.tag_input_area.setEnabled(True)
        self.tag_input_area.set_tags(self.current_tags)

    def set_current_file(self, full_path):
        """Sets the file path for which to display metadata."""
        self.current_file_path = full_path

class FolderPanel(QWidget):
    sig_add_to_favorites = pyqtSignal(str)
    sig_set_auto_tag = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.tree = QTreeView()
        self.tree.setHeaderHidden(True)
        self.tree.setPalette(get_dark_palette())
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.tree)
    
    def show_context_menu(self, pos):
        index = self.tree.indexAt(pos)
        if not index.isValid():
            return
        
        model = self.tree.model()
        if not model:
            return
        
        # 获取文件路径
        file_path = model.filePath(index)
        if not file_path or not os.path.exists(file_path):
            return
        
        logging.critical(f">>> [文件夹面板] 右键菜单触发，路径: {file_path}")
        
        menu = QMenu(self)
        
        # 添加到收藏夹
        action_add_fav = menu.addAction("⭐ 添加到收藏夹")
        action_add_fav.triggered.connect(lambda: self.add_to_favorites(file_path))
        
        # 如果是文件夹，显示"设置自动标签"选项
        if os.path.isdir(file_path):
            menu.addSeparator()
            action_auto_tag = menu.addAction("🏷️ 设置自动标签...")
            def emit_auto_tag_signal():
                logging.critical(f"!!! [文件夹面板] 用户点击了 '设置自动标签'，正在发射信号，路径: {file_path}")
                self.sig_set_auto_tag.emit(file_path)
            action_auto_tag.triggered.connect(emit_auto_tag_signal)
        
        menu.addSeparator()
        
        # 在资源管理器中显示
        action_explore = menu.addAction("在资源管理器中显示")
        action_explore.triggered.connect(lambda: subprocess.run(['explorer', '/select,', file_path.replace("/", "\\")]))
        
        menu.exec(self.tree.viewport().mapToGlobal(pos))
    
    def add_to_favorites(self, path):
        logging.critical(f">>> [文件夹面板] 添加到收藏夹: {path}")
        self.sig_add_to_favorites.emit(path)

# ==================== FilterPanel ====================
class FilterTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        
        if item and item.parent():
            # Get the visual rect of the item
            visual_rect = self.visualItemRect(item)
            
            # Calculate checkbox region (typically the first ~20 pixels including indentation)
            checkbox_region = QRect(visual_rect.left(), visual_rect.top(), 20, visual_rect.height())
            
            # Check if click is in the checkbox region
            clicked_on_checkbox = checkbox_region.contains(event.pos())
            
            # Store the original check state
            original_check_state = item.checkState(0)
            
            # Let the default handler process the event
            super().mousePressEvent(event)
            
            # If user clicked outside checkbox and state hasn't changed, toggle it manually
            if not clicked_on_checkbox and original_check_state == item.checkState(0):
                new_state = Qt.CheckState.Checked if original_check_state == Qt.CheckState.Unchecked else Qt.CheckState.Unchecked
                item.setCheckState(0, new_state)
        else:
            super().mousePressEvent(event)

class FilterPanel(QWidget):
    # 发送 4 个列表: tags, ratings, types, colors
    sig_filter_changed = pyqtSignal(list, list, list, list)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tree = FilterTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(15)
        self.tree.setPalette(get_dark_palette())
        self.tree.itemChanged.connect(self.on_item_changed)
        layout.addWidget(self.tree)
        self._is_updating = False

    def load_filters(self, meta_data):
        self._is_updating = True
        self.tree.clear()
        
        if not meta_data:
            self._is_updating = False
            return

        files_map = meta_data.get("files", {})
        sub_folders = meta_data.get("sub_folders", {})
        
        stats = {
            "tags": {},
            "rating": {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            "type": {},
            "color": {} 
        }
        
        def process_item(name, info, is_folder=False):
            if is_folder:
                ftype_key = "FOLDER"
            else:
                if '.' in name:
                    ftype_key = name.split('.')[-1].upper()
                else:
                    ftype_key = name
            stats["type"][ftype_key] = stats["type"].get(ftype_key, 0) + 1
            
            r = info.get("rating", 0)
            stats["rating"][r] = stats["rating"].get(r, 0) + 1
            
            tags = info.get("tags", [])
            for t in tags: stats["tags"][t] = stats["tags"].get(t, 0) + 1

            c = str(info.get("color", "")).lower()
            if not c: c = "none"
            stats["color"][c] = stats["color"].get(c, 0) + 1

        for name, info in files_map.items(): process_item(name, info, is_folder=False)
        if isinstance(sub_folders, dict):
            for name, info in sub_folders.items(): process_item(name, info, is_folder=True)

        # 1. 标签
        if stats["tags"]:
            root = self._add_root("标签")
            for tag, count in sorted(stats["tags"].items()):
                self._add_child(root, f"{tag} ({count})", "tag", tag)
            root.setExpanded(True)

        # 2. 评级
        rating_root = None
        for r in range(5, -1, -1):
            count = stats["rating"].get(r, 0)
            if count > 0:
                if not rating_root: rating_root = self._add_root("评级")
                name = "无评级" if r == 0 else ("★" * r)
                self._add_child(rating_root, f"{name} ({count})", "rating", r)
        if rating_root: rating_root.setExpanded(True)

        # 3. 颜色标签
        color_order = ["red", "orange", "yellow", "green", "cyan", "blue", "purple", "grey", "none"]
        existing_colors = sorted(stats["color"].keys())
        sorted_colors = [c for c in color_order if c in stats["color"]] + [c for c in existing_colors if c not in color_order]
        
        color_root = None
        for c in sorted_colors:
            count = stats["color"].get(c, 0)
            if count > 0:
                if not color_root: color_root = self._add_root("颜色标签")
                
                # Use color `c` to create an icon
                item = self._add_child(color_root, f"({count})", "color", c)
                
                if c != "none":
                    pixmap = QPixmap(16, 16)
                    pixmap.fill(QColor(c))
                    item.setIcon(0, QIcon(pixmap))
                else:
                    # Optional: handle 'none' color differently if needed
                    item.setText(0, f"无颜色 ({count})")

        if color_root: color_root.setExpanded(True)

        # 4. 文件类型
        if stats["type"]:
            root = self._add_root("文件类型")
            for ftype_code, count in sorted(stats["type"].items()):
                if ftype_code == "FOLDER":
                    display_name = "文件夹"
                else:
                    display_name = ftype_code.lower()
                
                self._add_child(root, f"{display_name} ({count})", "type", ftype_code)
            root.setExpanded(True)

        self._is_updating = False

    def _add_root(self, text):
        item = QTreeWidgetItem(self.tree)
        item.setText(0, text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
        return item

    def _add_child(self, parent, text, category, value):
        item = QTreeWidgetItem(parent)
        item.setText(0, text)
        item.setCheckState(0, Qt.CheckState.Unchecked)
        item.setData(0, Qt.ItemDataRole.UserRole, {"cat": category, "val": value})
        return item

    def on_item_changed(self, item, column):
        if self._is_updating: return
        selected_tags = []
        selected_ratings = []
        selected_types = []
        selected_colors = []
        
        iterator = QTreeWidgetItemIterator(self.tree, QTreeWidgetItemIterator.IteratorFlag.Checked)
        while iterator.value():
            it = iterator.value()
            data = it.data(0, Qt.ItemDataRole.UserRole)
            if data:
                cat = data["cat"]
                val = data["val"]
                if cat == "tag": selected_tags.append(val)
                elif cat == "rating": selected_ratings.append(val)
                elif cat == "type": selected_types.append(val)
                elif cat == "color": selected_colors.append(val)
            iterator += 1
        
        self.sig_filter_changed.emit(selected_tags, selected_ratings, selected_types, selected_colors)