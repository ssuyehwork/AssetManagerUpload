# G:\PYthon\AssetManager\ui\main_window.py
import sys
import os
import ctypes
import subprocess
import logging
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QListView, QTreeView,
    QWidget, QVBoxLayout, QStackedWidget,
    QAbstractItemView, QFrame, QHeaderView, QStyle, QSizeGrip, 
    QMessageBox, QInputDialog, QMenu, QToolTip
)
from PyQt6.QtGui import QFileSystemModel, QAction, QIcon, QColor, QPalette, QCursor, QShortcut, QKeySequence
from PyQt6.QtCore import Qt, QSize, QDir, QPoint, QRect, QEvent, QThread, pyqtSignal, QFileSystemWatcher, QTimer, QByteArray

# 模块引用
from ui.styles import DARK_THEME
from ui.panels import FolderPanel, FavoritesPanel, MetadataPanel, FilterPanel
from ui.custom_widgets import CustomDockTitleBar, TitleBar, NavBar
from ui.data_model import AssetModel
from ui.filter_proxy import AssetFilterProxyModel
from ui.menus import AssetContextMenu
from ui.color_picker import ColorPickerDialog
from ui.item_delegate import AssetGridDelegate
from ui.dialogs import AutoTagDialog 

# 业务服务引用
from services.local_store import LocalStoreService
from services.asset_service import AssetService
from services.rating_service import RatingService
from services.color_label_service import ColorLabelService
from services.tag_service import TagService
from services.preference_service import PreferenceService
from services.pin_service import PinService
from services.folder_tag_service import FolderTagService

# === 后台数据加载线程 (支持递归) ===
class DataLoaderThread(QThread):
    sig_loaded = pyqtSignal(dict, str) 

    def __init__(self, folder_path, recursive=False, parent=None):
        super().__init__(parent)
        self.folder_path = folder_path
        self.recursive = recursive

    def run(self):
        try:
            if self.recursive:
                flat_files = {}
                count = 0
                max_files = 3000
                for root, dirs, files in os.walk(self.folder_path):
                    if count > max_files: break
                    for f in files:
                        full_path = os.path.join(root, f)
                        try:
                            stat = os.stat(full_path)
                            _, ext = os.path.splitext(f)
                            rel_path = os.path.relpath(full_path, self.folder_path)
                            flat_files[rel_path] = {
                                "size": stat.st_size,
                                "ctime": stat.st_ctime,
                                "mtime": stat.st_mtime,
                                "ext": ext.lower(),
                                "type": ext.replace(".", "").upper() if ext else "FILE",
                                "full_path_override": full_path
                            }
                            count += 1
                        except: pass
                meta_data = { "files": flat_files, "sub_folders": {} }
            else:
                meta_data = LocalStoreService.scan_and_update(self.folder_path)
                if meta_data:
                    try:
                        FolderTagService.scan_and_apply_auto_tags(self.folder_path, meta_data)
                        AssetService.sync_from_meta(self.folder_path, 1, meta_data)
                    except Exception as e:
                        logging.error(f"线程内数据库同步出错: {e}")
            self.sig_loaded.emit(meta_data if meta_data else {}, self.folder_path)
        except Exception as e:
            logging.error(f"后台加载线程崩溃: {e}")
            self.sig_loaded.emit({}, self.folder_path)

class AssetManagerWindow(QMainWindow):
    EDGE_NONE, EDGE_LEFT, EDGE_TOP, EDGE_RIGHT, EDGE_BOTTOM = 0, 1, 2, 4, 8
    EDGE_TOP_LEFT, EDGE_TOP_RIGHT, EDGE_BOTTOM_LEFT, EDGE_BOTTOM_RIGHT = 3, 6, 9, 12

    def __init__(self):
        super().__init__()
        
        self._copied_tags = [] 
        # 用于记录加载完成后需要自动选中的文件路径
        self.pending_select_path = None 
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setMouseTracking(True)
        self.setContentsMargins(4, 4, 4, 4)
        
        self.setWindowTitle("Ssuyeh_Bridge")
        self.resize(1300, 850)
        
        self.setDockOptions(
            QMainWindow.DockOption.AllowNestedDocks |
            QMainWindow.DockOption.AllowTabbedDocks |
            QMainWindow.DockOption.AnimatedDocks
        )
        self.history = []
        self.history_index = -1
        self.is_navigating_history = False
        
        self.view_settings = {
            "show_folders": True,       
            "show_hidden": False,       
            "recursive": False          
        }

        self.file_watcher = QFileSystemWatcher(self)
        self.file_watcher.directoryChanged.connect(self.on_directory_changed)
        self.current_watch_path = None
        
        self.refresh_timer = QTimer()
        self.refresh_timer.setInterval(1000) 
        self.refresh_timer.setSingleShot(True)
        self.refresh_timer.timeout.connect(self.execute_auto_refresh)
        
        self.fs_model = QFileSystemModel()
        self.fs_model.setRootPath("")
        self.fs_model.setFilter(QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot)
        
        self.asset_model = AssetModel()
        self.proxy_model = AssetFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.asset_model)
        self.proxy_model.setDynamicSortFilter(True)
        
        self.loader_thread = None
        
        self.setup_header()
        self.setup_central_widget()
        self.setup_docks()
        
        self.setup_shortcuts()
        
        self.nav_bar.sig_search_entered.connect(self.execute_global_search)
        self.nav_bar.sig_sort_changed.connect(self.handle_sort_changed)
        
        self.border_width = 6
        self.dragging_edge = self.EDGE_NONE
        self.drag_start_pos = QPoint()
        
        self.restore_window_state()

        start_path = os.getcwd()
        if os.path.exists(start_path):
            self.nav_bar.address_bar.setText(start_path)
            self.update_middle_column(start_path)

    def handle_sort_changed(self, sort_key):
        self.proxy_model.set_sort_mode(sort_key)

    def restore_window_state(self):
        geo_hex, state_hex = PreferenceService.get_window_layout()
        if geo_hex:
            self.restoreGeometry(QByteArray.fromHex(geo_hex.encode()))
        if state_hex:
            self.restoreState(QByteArray.fromHex(state_hex.encode()))

    def enterEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().enterEvent(event)

    def closeEvent(self, event):
        geo = self.saveGeometry().toHex().data().decode()
        state = self.saveState().toHex().data().decode()
        PreferenceService.save_window_layout(geo, state)
        event.accept()

    def on_directory_changed(self, path):
        if self.loader_thread and self.loader_thread.isRunning(): return
        if self.view_settings["recursive"]: return
        print(f"检测到变动 (防抖中): {path}")
        self.refresh_timer.start()

    def execute_auto_refresh(self):
        current_path = self.nav_bar.address_bar.text()
        print(f"执行自动刷新: {current_path}")
        self.update_middle_column(current_path, record_history=False, force_reload=True)

    def execute_global_search(self, keyword):
        keyword = keyword.strip()
        if not keyword: return
        print(f"正在全局搜索: {keyword}")
        self.pause_monitoring()
        self.panel_filter.tree.clear()
        self.asset_model.clear()
        self.setCursor(Qt.CursorShape.WaitCursor)
        results = AssetService.search_assets(keyword)
        files_data = {}
        for row in results:
            full_path = row["full_path"]
            row_type = row.get("type", "FILE").upper()
            files_data[full_path] = {
                "size": row.get("size", 0),
                "rating": row.get("rating", 0),
                "color": row.get("color", ""),
                "type": row_type,
                "full_path_override": full_path
            }
        meta_data = {"files": files_data, "sub_folders": {}}
        self.asset_model.load_data("SEARCH_RESULTS", meta_data)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        QToolTip.showText(self.nav_bar.search_bar.mapToGlobal(QPoint(0,0)), f"找到 {len(results)} 个结果")

    def pause_monitoring(self):
        if self.current_watch_path:
            self.file_watcher.removePath(self.current_watch_path)

    def resume_monitoring(self):
        if self.current_watch_path:
            self.file_watcher.addPath(self.current_watch_path)

    def setup_shortcuts(self):
        self._shortcut_refs = []
        def reg(key_str, callback, desc):
            seq = QKeySequence(key_str)
            shortcut = QShortcut(seq, self)
            shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
            shortcut.activated.connect(callback)
            self._shortcut_refs.append(shortcut)
            
        reg("Ctrl+0", lambda: self.apply_rating_to_selection(0), "清除星级")
        for i in range(1, 6):
            reg(f"Ctrl+{i}", lambda r=i: self.apply_rating_to_selection(r), f"设置 {i} 星")
            
        reg("Delete", lambda: self.handle_delete(permanently=False), "删除到回收站")
        reg("Shift+Delete", lambda: self.handle_delete(permanently=True), "永久删除")
        reg("Ctrl+W", self.close, "关闭程序")
        reg("F5", lambda: self.update_middle_column(self.nav_bar.address_bar.text(), force_reload=True), "刷新")

    def copy_tags(self):
        current_view = self.central_stack.currentWidget()
        selection_model = current_view.selectionModel()
        index = selection_model.currentIndex()
        if not index.isValid(): return
        source_index = self.proxy_model.mapToSource(index)
        meta = self.asset_model.data(source_index, AssetModel.ROLE_META_DATA)
        if meta and isinstance(meta, dict):
            tags = meta.get("tags", [])
            self._copied_tags = list(tags) 
            filename = self.asset_model.data(source_index, Qt.ItemDataRole.DisplayRole)
            print(f"已复制标签: {self._copied_tags} (来源: {filename})")
        else:
            self._copied_tags = []

    def paste_tags(self):
        if not self._copied_tags: return
        current_view = self.central_stack.currentWidget()
        selection_model = current_view.selectionModel()
        indexes = selection_model.selectedIndexes()
        if not indexes: return
        self.pause_monitoring()
        try:
            rows_processed = set()
            count = 0
            for index in indexes:
                source_index = self.proxy_model.mapToSource(index)
                if source_index.row() in rows_processed: continue
                rows_processed.add(source_index.row())
                full_path = self.asset_model.data(source_index, AssetModel.ROLE_FULL_PATH)
                if full_path:
                    new_info = TagService.add_tags_batch(full_path, self._copied_tags)
                    if new_info:
                        count += 1
                        self.asset_model.setData(source_index, new_info, AssetModel.ROLE_META_DATA)
                        if index == selection_model.currentIndex():
                            filename = self.asset_model.data(source_index, Qt.ItemDataRole.DisplayRole)
                            self.panel_meta.update_info(filename, new_info)
        finally:
            self.resume_monitoring()

    def handle_pin_file(self, full_path):
        self.pause_monitoring()
        try:
            new_info = PinService.toggle_pinned(full_path)
            if new_info:
                self.update_middle_column(self.nav_bar.address_bar.text(), record_history=False, force_reload=True)
        finally:
            self.resume_monitoring()

    # === 【核心修复】增加日志 + 移除成功弹窗 ===
    def open_auto_tag_dialog(self, folder_path):
        # 记录收到的信号参数
        logging.critical(f"!!! [主窗口] 收到 open_auto_tag_dialog 请求，目标: {folder_path}")
        
        if not folder_path or not os.path.exists(folder_path):
            logging.critical(f"!!! [主窗口] 路径无效或不存在: {folder_path}")
            return

        try:
            dialog = AutoTagDialog(folder_path, self)
            
            if dialog.exec():
                tags = dialog.result_tags
                self.pause_monitoring()
                try:
                    FolderTagService.set_auto_tags(folder_path, tags, recursive=True)
                    
                    current_view_path = self.nav_bar.address_bar.text()
                    if current_view_path == folder_path or folder_path in current_view_path:
                        self.update_middle_column(current_view_path, record_history=False, force_reload=True)
                    
                    # 成功后默默生效，不弹窗干扰
                    logging.critical(f"!!! [主窗口] 自动标签设置成功: {tags}")
                except Exception as e:
                    print(f"[ERROR] 保存设置时出错: {e}")
                    QMessageBox.critical(self, "错误", f"保存失败: {e}")
                finally:
                    self.resume_monitoring()
        except Exception as e:
            print(f"[CRITICAL ERROR] 打开弹窗时发生严重错误: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "程序错误", f"无法打开弹窗:\n{e}")

    def handle_delete(self, permanently=False):
        current_view = self.central_stack.currentWidget()
        selection_model = current_view.selectionModel()
        indexes = selection_model.selectedIndexes()
        if not indexes: return
        paths = set()
        for idx in indexes:
            src_idx = self.proxy_model.mapToSource(idx)
            path = self.asset_model.data(src_idx, AssetModel.ROLE_FULL_PATH)
            if path: paths.add(path)
        if not paths: return
        count = len(paths)
        files_str = "\n".join(list(paths)[:5])
        if count > 5: files_str += "\n..."
        title = "永久删除" if permanently else "删除文件"
        msg = f"确定要{'永久删除' if permanently else '将以下文件放入回收站'}吗？\n\n{files_str}\n\n(共 {count} 项)"
        reply = QMessageBox.question(self, title, msg, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            success_count = 0
            current_dir = self.nav_bar.address_bar.text()
            self.pause_monitoring()
            try:
                for path in paths:
                    ok, err = AssetService.delete_file(path, permanently)
                    if ok: success_count += 1
                    else: logging.error(f"删除失败 {path}: {err}")
                if success_count > 0:
                    self.update_middle_column(current_dir, record_history=False, force_reload=True)
            finally:
                self.resume_monitoring()

    def keyPressEvent(self, event):
        if not self.isActiveWindow():
            super().keyPressEvent(event)
            return
        key = event.key()
        modifiers = event.modifiers()
        if key == Qt.Key.Key_Backspace:
            self.go_up_directory()
            event.accept()
            return
        if modifiers == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
            if key == Qt.Key.Key_C:
                self.copy_tags()
                event.accept()
                return
            elif key == Qt.Key.Key_V:
                self.paste_tags()
                event.accept()
                return
        if (modifiers == Qt.KeyboardModifier.AltModifier or
            modifiers == (Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.KeypadModifier)):
            color_idx = -1
            if key in (Qt.Key.Key_0, Qt.Key.Key_0 + 0x10000000): color_idx = 0
            elif key in (Qt.Key.Key_1, Qt.Key.Key_1 + 0x10000000): color_idx = 1
            elif key in (Qt.Key.Key_2, Qt.Key.Key_2 + 0x10000000): color_idx = 2
            elif key in (Qt.Key.Key_3, Qt.Key.Key_3 + 0x10000000): color_idx = 3
            elif key in (Qt.Key.Key_4, Qt.Key.Key_4 + 0x10000000): color_idx = 4
            elif key in (Qt.Key.Key_5, Qt.Key.Key_5 + 0x10000000): color_idx = 5
            elif key in (Qt.Key.Key_6, Qt.Key.Key_6 + 0x10000000): color_idx = 6
            elif key in (Qt.Key.Key_7, Qt.Key.Key_7 + 0x10000000): color_idx = 7
            if color_idx != -1:
                self.apply_color_to_selection(color_idx)
                event.accept()
                return
        super().keyPressEvent(event)

    def apply_rating_to_selection(self, rating):
        self._batch_update_selection(lambda path: RatingService.set_rating(path, rating))

    def apply_color_to_selection(self, color_arg):
        target_color = ""
        if isinstance(color_arg, int): target_color = ColorLabelService.SHORTCUT_MAP.get(color_arg, "")
        elif isinstance(color_arg, str): target_color = color_arg
        self._batch_update_selection(lambda path: ColorLabelService.set_color(path, target_color))

    def _batch_update_selection(self, service_func):
        current_view = self.central_stack.currentWidget()
        if not current_view: return
        selection_model = current_view.selectionModel()
        if not selection_model: return
        indexes = selection_model.selectedIndexes()
        if not indexes: return
        self.pause_monitoring()
        try:
            rows_processed = set()
            count = 0
            for index in indexes:
                source_index = self.proxy_model.mapToSource(index) 
                if source_index.row() in rows_processed: continue
                rows_processed.add(source_index.row())
                full_path = self.asset_model.data(source_index, AssetModel.ROLE_FULL_PATH)
                if full_path:
                    new_info = service_func(full_path)
                    if new_info:
                        count += 1
                        self.asset_model.setData(source_index, new_info, AssetModel.ROLE_META_DATA)
                        if len(rows_processed) == 1:
                            filename = self.asset_model.data(source_index, Qt.ItemDataRole.DisplayRole)
                            self.panel_meta.update_info(filename, new_info)
        finally:
            self.resume_monitoring()

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.Wheel:
            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.KeyboardModifier.ControlModifier:
                angle = event.angleDelta().y()
                current_size = self.nav_bar.slider.value()
                step = 10 if angle > 0 else -10
                self.nav_bar.slider.setValue(current_size + step)
                return True
        return super().eventFilter(source, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            edge = self._check_edge(event.pos())
            if edge != self.EDGE_NONE:
                self.dragging_edge = edge
                self.drag_start_pos = event.globalPosition().toPoint()
                event.accept()
            else: super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.dragging_edge != self.EDGE_NONE:
            self.dragging_edge = self.EDGE_NONE
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging_edge != self.EDGE_NONE:
            self._resize_window(event.globalPosition().toPoint())
            event.accept()
            return
        edge = self._check_edge(event.pos())
        if edge != self.EDGE_NONE: self._update_cursor(edge)
        else: self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)

    def _check_edge(self, pos):
        r = self.rect()
        x, y = pos.x(), pos.y()
        w, h = r.width(), r.height()
        bw = self.border_width
        edge = self.EDGE_NONE
        if x < bw: edge |= self.EDGE_LEFT
        if x > w - bw: edge |= self.EDGE_RIGHT
        if y < bw: edge |= self.EDGE_TOP
        if y > h - bw: edge |= self.EDGE_BOTTOM
        return edge

    def _update_cursor(self, edge):
        if edge == self.EDGE_TOP_LEFT or edge == self.EDGE_BOTTOM_RIGHT: self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif edge == self.EDGE_TOP_RIGHT or edge == self.EDGE_BOTTOM_LEFT: self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif edge & (self.EDGE_LEFT | self.EDGE_RIGHT): self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif edge & (self.EDGE_TOP | self.EDGE_BOTTOM): self.setCursor(Qt.CursorShape.SizeVerCursor)

    def _resize_window(self, global_pos):
        diff = global_pos - self.drag_start_pos
        geo = self.geometry()
        if self.dragging_edge & self.EDGE_LEFT: geo.setLeft(geo.left() + diff.x())
        if self.dragging_edge & self.EDGE_RIGHT: geo.setRight(geo.right() + diff.x())
        if self.dragging_edge & self.EDGE_TOP: geo.setTop(geo.top() + diff.y())
        if self.dragging_edge & self.EDGE_BOTTOM: geo.setBottom(geo.bottom() + diff.y())
        self.setGeometry(geo)
        self.drag_start_pos = global_pos

    def setup_header(self):
        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)
        self.title_bar = TitleBar(self)
        self.title_bar.sig_win_min.connect(self.showMinimized)
        self.title_bar.sig_win_max.connect(self.toggle_maximize)
        self.title_bar.sig_win_close.connect(self.close)
        self.title_bar.sig_color.connect(self.show_color_picker)
        self.title_bar.sig_refresh.connect(lambda: self.update_middle_column(self.nav_bar.address_bar.text(), force_reload=True))
        self.title_bar.sig_pin.connect(self.toggle_topmost)
        self.title_bar.sig_new_folder.connect(self.create_new_folder)
        self.title_bar.sig_view_menu.connect(self.show_view_menu)
        self.nav_bar = NavBar(self)
        self.nav_bar.sig_back.connect(self.go_back)
        self.nav_bar.sig_fwd.connect(self.go_forward)
        self.nav_bar.sig_up.connect(self.go_up_directory)
        self.nav_bar.sig_view_grid.connect(lambda: self.switch_view("grid"))
        self.nav_bar.sig_view_list.connect(lambda: self.switch_view("list"))
        self.nav_bar.sig_zoom.connect(self.change_icon_size)
        self.nav_bar.sig_address_entered.connect(self.update_middle_column)
        header_layout.addWidget(self.title_bar)
        header_layout.addWidget(self.nav_bar)
        self.setMenuWidget(header_container)

    def show_view_menu(self):
        menu = QMenu(self)
        act_folders = QAction("显示文件夹", self)
        act_folders.setCheckable(True)
        act_folders.setChecked(self.view_settings["show_folders"])
        act_folders.triggered.connect(lambda c: self.toggle_view_setting("show_folders", c))
        menu.addAction(act_folders)
        act_hidden = QAction("显示隐藏文件", self)
        act_hidden.setCheckable(True)
        act_hidden.setChecked(self.view_settings["show_hidden"])
        act_hidden.triggered.connect(lambda c: self.toggle_view_setting("show_hidden", c))
        menu.addAction(act_hidden)
        menu.addSeparator()
        act_recursive = QAction("显示子文件夹中的项目 (递归)", self)
        act_recursive.setCheckable(True)
        act_recursive.setChecked(self.view_settings["recursive"])
        act_recursive.triggered.connect(lambda c: self.toggle_view_setting("recursive", c))
        menu.addAction(act_recursive)
        btn = self.title_bar.btn_view
        menu.exec(btn.mapToGlobal(QPoint(0, btn.height())))

    def toggle_view_setting(self, key, checked):
        self.view_settings[key] = checked
        self.update_middle_column(self.nav_bar.address_bar.text(), record_history=False, force_reload=True)

    def toggle_topmost(self, checked):
        try:
            hwnd = int(self.winId())
            target = -1 if checked else -2
            ctypes.windll.user32.SetWindowPos(hwnd, target, 0, 0, 0, 0, 0x0013)
        except Exception:
            current = self.windowFlags()
            if checked: self.setWindowFlags(current | Qt.WindowType.WindowStaysOnTopHint)
            else: self.setWindowFlags(current & ~Qt.WindowType.WindowStaysOnTopHint)
            self.show()

    def show_color_picker(self):
        dialog = ColorPickerDialog(self)
        dialog.exec()

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            self.title_bar.btn_max.setText("框")
        else:
            self.showMaximized()
            self.title_bar.btn_max.setText("恢复")

    def setup_central_widget(self):
        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)
        def common_config(view):
            view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
            view.setModel(self.proxy_model)
            view.setDragEnabled(True)
            view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            view.customContextMenuRequested.connect(self.show_context_menu)
            view.clicked.connect(self.on_asset_clicked)
            view.doubleClicked.connect(self.on_asset_double_clicked)
            # 关键：连接选择变化信号
            view.selectionModel().selectionChanged.connect(self.on_view_selection_changed)
            view.viewport().installEventFilter(self)
        self.grid_view = QListView()
        self.grid_view.setViewMode(QListView.ViewMode.IconMode)
        self.grid_view.setResizeMode(QListView.ResizeMode.Adjust)
        self.grid_view.setSpacing(12)
        self.grid_view.setUniformItemSizes(False)
        self.grid_view.setIconSize(QSize(120, 120))
        self.grid_view.setGridSize(QSize(160, 200))
        self.grid_delegate = AssetGridDelegate()
        self.grid_view.setItemDelegate(self.grid_delegate)
        common_config(self.grid_view)
        self.central_stack.addWidget(self.grid_view)
        self.list_view = QTreeView()
        self.list_view.setRootIsDecorated(False)
        self.list_view.setAlternatingRowColors(True)
        self.list_view.setSortingEnabled(True)
        p = self.list_view.palette()
        p.setColor(QPalette.ColorRole.Base, QColor("#1e1e1e"))
        p.setColor(QPalette.ColorRole.AlternateBase, QColor("#252525"))
        p.setColor(QPalette.ColorRole.Text, QColor("#e0e0e0"))
        self.list_view.setPalette(p)
        common_config(self.list_view)
        self.central_stack.addWidget(self.list_view)

    def update_middle_column(self, path, record_history=True, force_reload=False):
        path = str(path).strip().strip('"')
        if not os.path.exists(path): return

        current_display = self.nav_bar.address_bar.text()
        if current_display and os.path.abspath(path) != os.path.abspath(current_display):
            self.view_settings["recursive"] = False

        if record_history and not self.is_navigating_history:
            if not self.history or self.history[self.history_index] != path:
                if self.history_index < len(self.history) - 1:
                    self.history = self.history[:self.history_index+1]
                self.history.append(path)
                self.history_index += 1
        
        self.nav_bar.btn_back.setEnabled(self.history_index > 0)
        self.nav_bar.btn_fwd.setEnabled(self.history_index < len(self.history) - 1)
        self.nav_bar.address_bar.setText(path)

        if self.current_watch_path:
            self.file_watcher.removePath(self.current_watch_path)
            self.current_watch_path = None

        if self.loader_thread and self.loader_thread.isRunning():
            self.loader_thread.terminate()
            self.loader_thread.wait()

        self.setCursor(Qt.CursorShape.WaitCursor) 
        self.asset_model.clear() 
        
        is_recursive = self.view_settings["recursive"]
        self.loader_thread = DataLoaderThread(path, recursive=is_recursive, parent=self)
        self.loader_thread.sig_loaded.connect(self.on_folder_loaded)
        self.loader_thread.start()

    def on_folder_loaded(self, meta_data, path):
        if not meta_data: meta_data = {}
        if not self.view_settings["show_folders"]: meta_data["sub_folders"] = {}
        if not self.view_settings["show_hidden"]:
            if "files" in meta_data:
                meta_data["files"] = {k: v for k, v in meta_data["files"].items() if not k.startswith(".")}

        self.asset_model.load_data(path, meta_data)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.panel_filter.load_filters(meta_data)

        if path == self.nav_bar.address_bar.text() and not self.view_settings["recursive"]:
            self.file_watcher.addPath(path)
            self.current_watch_path = path

    def setup_docks(self):
        self.docks = {}
        def create_dock(name, widget_class, area):
            dock = QDockWidget(name, self)
            content = widget_class()
            dock.setWidget(content)
            dock.setObjectName(name)
            self.addDockWidget(area, dock)
            self.docks[name] = dock
            return dock, content
        self.dock_folder, self.panel_folder = create_dock("文件夹", FolderPanel, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.dock_fav, self.panel_fav = create_dock("收藏夹", FavoritesPanel, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.dock_meta, self.panel_meta = create_dock("元数据", MetadataPanel, Qt.DockWidgetArea.RightDockWidgetArea)
        self.dock_filter, self.panel_filter = create_dock("筛选器", FilterPanel, Qt.DockWidgetArea.RightDockWidgetArea)
        for dock in self.docks.values():
            title_bar = CustomDockTitleBar(dock, self.docks)
            dock.setTitleBarWidget(title_bar)
        self.splitDockWidget(self.dock_folder, self.dock_fav, Qt.Orientation.Vertical)
        self.splitDockWidget(self.dock_meta, self.dock_filter, Qt.Orientation.Vertical)
        self.panel_folder.tree.setModel(self.fs_model)
        for i in range(1, 4): self.panel_folder.tree.hideColumn(i)
        self.panel_folder.tree.clicked.connect(self.on_folder_clicked)
        self.panel_fav.list_view.sig_favorite_clicked.connect(self.on_favorite_clicked)
        
        # 连接收藏夹面板的信号
        self.panel_fav.list_view.sig_set_auto_tag.connect(self.open_auto_tag_dialog)

        # 【核心修复】连接文件夹面板的信号
        self.panel_folder.sig_add_to_favorites.connect(self.panel_fav.list_view.add_favorite)
        self.panel_folder.sig_set_auto_tag.connect(self.open_auto_tag_dialog)

        # The following signals are removed as TagInputArea handles its own logic internally
        # and emits a single signal `sig_tags_changed` which is handled within MetadataPanel.
        # self.panel_meta.sig_add_tag.connect(self.handle_add_tag_request)
        # self.panel_meta.sig_remove_tag.connect(self.handle_remove_tag_request)
        self.panel_meta.sig_tags_updated.connect(self.handle_tags_update)
        self.panel_filter.sig_filter_changed.connect(self.proxy_model.set_filter_conditions)

    def on_view_selection_changed(self, selected, deselected):
        """当视图中的选择发生变化时调用。"""
        current_view = self.central_stack.currentWidget()
        if not current_view: return
        
        selection_model = current_view.selectionModel()
        if not selection_model.hasSelection():
            # 如果没有项目被选中，则清空元数据面板
            self.panel_meta.clear_info()
        else:
            # 否则，像正常点击一样更新信息
            # （on_asset_clicked 会处理多选的情况，只更新当前活动项）
            current_index = selection_model.currentIndex()
            if current_index.isValid():
                self.on_asset_clicked(current_index)

    def handle_tags_update(self, file_path, new_tags_list):
        """
        Handles the tag update request from the MetadataPanel.
        This is the central point for saving tags, controlling the file watcher,
        and updating the main data model.
        """
        self.pause_monitoring()
        try:
            # Find the corresponding item in the model to get original tags
            source_index = self.asset_model.find_index_by_path(file_path)
            if not source_index.isValid():
                return

            original_meta = self.asset_model.data(source_index, AssetModel.ROLE_META_DATA)
            original_tags = set(original_meta.get("tags", []))
            new_tags = set(new_tags_list)

            tags_to_add = list(new_tags - original_tags)
            tags_to_remove = list(original_tags - new_tags)

            updated_info = None
            if tags_to_add:
                updated_info = TagService.add_tags_batch(file_path, tags_to_add)

            if tags_to_remove:
                updated_info = TagService.remove_tags_batch(file_path, tags_to_remove)

            # If any change happened, update the model and the metadata panel
            if updated_info:
                self.asset_model.setData(source_index, updated_info, AssetModel.ROLE_META_DATA)

                # Check if the updated item is still the one selected
                current_view = self.central_stack.currentWidget()
                selection_model = current_view.selectionModel()
                if selection_model.currentIndex() and self.proxy_model.mapToSource(selection_model.currentIndex()) == source_index:
                    filename = self.asset_model.data(source_index, Qt.ItemDataRole.DisplayRole)
                    self.panel_meta.update_info(filename, updated_info)

        finally:
            self.resume_monitoring()

    def on_favorite_clicked(self, path):
        path = str(path).strip()
        if not os.path.exists(path):
            self.panel_fav.list_view.remove_by_path(path)
            QToolTip.showText(QCursor.pos(), f"路径无效，已自动移除: {os.path.basename(path)}")
            return
            
        if os.path.isdir(path): self.update_middle_column(path)
        elif os.path.isfile(path): self.open_and_track(path)

    def on_folder_clicked(self, index):
        path = self.fs_model.filePath(index)
        self.panel_folder.tree.setExpanded(index, True)
        self.update_middle_column(path)

    def on_asset_clicked(self, index):
        source_index = self.proxy_model.mapToSource(index)
        info = self.asset_model.data(source_index, AssetModel.ROLE_META_DATA)
        full_path = self.asset_model.data(source_index, AssetModel.ROLE_FULL_PATH)
        filename = self.asset_model.data(source_index, Qt.ItemDataRole.DisplayRole)
        if info: 
            self.panel_meta.set_current_file(full_path)
            self.panel_meta.update_info(filename, info)

    def on_asset_double_clicked(self, index):
        source_index = self.proxy_model.mapToSource(index)
        full_path = self.asset_model.data(source_index, AssetModel.ROLE_FULL_PATH)
        if full_path:
            if os.path.isdir(full_path): self.update_middle_column(full_path)
            else: self.open_and_track(full_path)

    def switch_view(self, mode):
        if mode == "grid": self.central_stack.setCurrentWidget(self.grid_view)
        elif mode == "list": self.central_stack.setCurrentWidget(self.list_view)

    def change_icon_size(self, value):
        size = QSize(value, value)
        self.grid_view.setIconSize(size)
        self.grid_view.setGridSize(QSize(value + 20, value + 80))

    def go_back(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.is_navigating_history = True
            self.update_middle_column(self.history[self.history_index], record_history=False)
            self.is_navigating_history = False

    def go_forward(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.is_navigating_history = True
            self.update_middle_column(self.history[self.history_index], record_history=False)
            self.is_navigating_history = False

    def go_up_directory(self):
        current_path = self.nav_bar.address_bar.text()
        parent_path = os.path.dirname(current_path)
        if os.path.exists(parent_path): self.update_middle_column(parent_path)

    def create_new_folder(self):
        current_path = self.nav_bar.address_bar.text().strip()
        if not current_path or not os.path.isdir(current_path):
            QMessageBox.warning(self, "错误", "当前路径无效，无法创建文件夹。")
            return
        name, ok = QInputDialog.getText(self, "新建文件夹", "请输入文件夹名称:", text="新建文件夹")
        if ok and name:
            new_folder_path = os.path.join(current_path, name)
            self.pause_monitoring()
            try:
                os.mkdir(new_folder_path)
                self.update_middle_column(current_path, record_history=False, force_reload=True)
            except Exception as e:
                QMessageBox.critical(self, "创建失败", f"无法创建文件夹:\n{e}")
            finally:
                self.resume_monitoring()

    def reveal_current_folder(self):
        current_path = self.nav_bar.address_bar.text().strip()
        if current_path and os.path.exists(current_path):
            try: subprocess.Popen(f'explorer "{current_path}"')
            except Exception as e: print(f"打开资源管理器失败: {e}")

    def open_and_track(self, full_path):
        self.pause_monitoring()
        try:
            os.startfile(full_path)
            folder = os.path.dirname(full_path)
            fname = os.path.basename(full_path)
            updated = LocalStoreService.increment_view_count(folder, fname)
            if updated: self.panel_meta.update_info(fname, updated)
        except Exception as e:
            logging.error(f"打开文件失败 {full_path}: {e}")
        finally:
            self.resume_monitoring()

    def show_context_menu(self, pos):
        sender = self.sender()
        index = sender.indexAt(pos)
        if not index.isValid():
            self.show_empty_space_menu(pos, sender)
            return
        
        source_index = self.proxy_model.mapToSource(index)
        raw_data = self.asset_model.data(source_index, AssetModel.ROLE_FULL_PATH)
        full_path = str(raw_data) if isinstance(raw_data, str) else ""
        
        if not full_path: return
        
        callbacks = {
            "add_fav": lambda: self.panel_fav.list_view.add_favorite(full_path),
            "open": lambda: self.open_and_track(full_path),
            "set_rating": lambda r: self.apply_rating_to_selection(r),
            "set_color": lambda c: self.apply_color_to_selection(c),
            "toggle_pin": lambda: self.handle_pin_file(full_path),
            "delete": lambda: self.handle_delete(permanently=False),
            # 【新增回调】
            "set_auto_tag": lambda: self.open_auto_tag_dialog(full_path)
        }
        menu = AssetContextMenu(sender, callbacks=callbacks, file_path=full_path)
        menu.exec(sender.mapToGlobal(pos))

    def show_empty_space_menu(self, pos, sender):
        menu = QMenu(self)
        action_new = QAction("📂 新建文件夹", self)
        action_new.triggered.connect(self.create_new_folder)
        menu.addAction(action_new)
        menu.addSeparator()
        action_explore = QAction("在资源管理器中显示", self)
        action_explore.triggered.connect(self.reveal_current_folder)
        menu.addAction(action_explore)
        menu.addSeparator()
        action_refresh = QAction("刷新", self)
        action_refresh.triggered.connect(lambda: self.update_middle_column(self.nav_bar.address_bar.text(), force_reload=True))
        menu.addAction(action_refresh)
        menu.exec(sender.mapToGlobal(pos))