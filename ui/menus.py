# G:\PYthon\AssetManager\ui\menus.py
  
import os  
import subprocess  
import shutil  
from PyQt6.QtWidgets import QMenu, QApplication  
from PyQt6.QtGui import QAction, QIcon, QColor, QPixmap, QPainter  
from PyQt6.QtCore import Qt, QUrl, QPoint, QSize
  
from services.color_service import ColorService  
from services.color_label_service import ColorLabelService  

class BaseContextMenu(QMenu):  
    def __init__(self, parent=None):  
        super().__init__(parent)  
        self.setCursor(Qt.CursorShape.ArrowCursor)
        # 【关键】删除了之前乱加的样式表，恢复系统原生漂亮外观
        # 也不设置 setIconSize，让系统自动适应
  
class AssetContextMenu(BaseContextMenu):  
    def __init__(self, parent=None, file_path="", is_recursive=False, callbacks=None):  
        super().__init__(parent)  
        self.file_path = file_path  
        self.is_recursive = is_recursive 
        self.callbacks = callbacks or {}   
        self.init_menu()  
  
    def init_menu(self):  
        # 1. 打开  
        action_open = QAction("📂 打开", self)  
        action_open.triggered.connect(self.callbacks.get("open", lambda: None))  
        self.addAction(action_open)  
        self.add_open_with_menu()  
        
        self.addSeparator()  

        if self.is_recursive:
            action_reveal_bridge = QAction("🔍 在 Ssuyeh_Bridge 中显示", self)
            action_reveal_bridge.triggered.connect(self.callbacks.get("reveal_in_bridge", lambda: None))
            self.addAction(action_reveal_bridge)
            self.addSeparator()
  
        # 2. 星级  
        menu_rating = self.addMenu("⭐ 设置星级")
        for i in range(5, 0, -1):  
            action = QAction("★" * i, self)  
            action.triggered.connect(lambda checked, r=i: self.callbacks.get("set_rating", lambda x: None)(r))  
            menu_rating.addAction(action)  
        action_no_rate = QAction("❌ 无星级", self)  
        action_no_rate.triggered.connect(lambda: self.callbacks.get("set_rating", lambda x: None)(0))  
        menu_rating.addAction(action_no_rate)  
  
        # 3. 颜色标签  
        self.add_color_menu()  
  
        self.addSeparator()  
          
        # 4. 其他操作  
        action_pin = QAction("📌 置顶/取消置顶", self)  
        action_pin.triggered.connect(self.callbacks.get("toggle_pin", lambda: None))
        self.addAction(action_pin)  
  
        if os.path.isdir(self.file_path):
            action_auto_tag = QAction("🏷️ 设置自动标签...", self)
            action_auto_tag.triggered.connect(self.callbacks.get("set_auto_tag", lambda: None))
            self.addAction(action_auto_tag)

        action_copy = QAction("📄 复制文件", self)  
        action_copy.triggered.connect(self.copy_file_to_clipboard)  
        self.addAction(action_copy)  
          
        self.addSeparator()  
          
        action_reveal = QAction("📂 在资源管理器中显示", self)  
        action_reveal.triggered.connect(self.reveal_in_explorer)  
        self.addAction(action_reveal)  
          
        action_copy_path = QAction("🔗 复制路径", self)  
        action_copy_path.triggered.connect(self.copy_path_to_clipboard)  
        self.addAction(action_copy_path)  
  
        self.addSeparator()  
          
        action_fav = QAction("★ 添加到收藏夹", self)  
        action_fav.triggered.connect(self.callbacks.get("add_fav", lambda: None))  
        self.addAction(action_fav)  
          
        action_del = QAction("🗑️ 删除", self)  
        action_del.triggered.connect(self.callbacks.get("delete", lambda: None))
        self.addAction(action_del)  
  
    def add_color_menu(self):  
        menu_color = self.addMenu("🎨 颜色标签")
        
        # 【关键】只对颜色子菜单应用图标放大的微调，不改变背景和边框
        # 这样不会破坏原生的美感，只会撑大图标区域
        big_icon_style = "QMenu::icon { width: 24px; height: 24px; }"
        menu_color.setStyleSheet(big_icon_style)
        
        menu_recent = menu_color.addMenu("🕒 最近使用")  
        menu_recent.setStyleSheet(big_icon_style)
        
        recent_colors = ColorLabelService.get_recent_colors()  
          
        if recent_colors:  
            for color_name in recent_colors:  
                hex_display = color_name  
                if not color_name.startswith("#"):  
                    hex_map = { "red": "#ff4444", "orange": "#ff8800", "yellow": "#ffd700", "green": "#44ff44", "cyan": "#00bcd4", "blue": "#4444ff", "purple": "#bd93f9", "grey": "#888888" }  
                    hex_display = hex_map.get(color_name, "#ffffff")  
                action = QAction("        ", self)
                action.setIcon(self._create_big_circle_icon(hex_display))  
                action.setToolTip(color_name)
                action.triggered.connect(lambda checked, c=color_name: self.callbacks.get("set_color", lambda x: None)(c))  
                menu_recent.addAction(action)  
        else:  
            act = QAction("无记录", self)  
            act.setEnabled(False)  
            menu_recent.addAction(act)  
  
        menu_saved = menu_color.addMenu("⭐ 收藏库")  
        menu_saved.setStyleSheet(big_icon_style)
        
        saved_colors = ColorService.get_all_colors()  
        if saved_colors:  
            for hex_code in saved_colors:  
                action = QAction("        ", self)  
                action.setIcon(self._create_big_circle_icon(hex_code))  
                action.setToolTip(hex_code)
                action.triggered.connect(lambda checked, c=hex_code: self.callbacks.get("set_color", lambda x: None)(c))  
                menu_saved.addAction(action)  
        else:  
            act = QAction("无收藏", self)  
            act.setEnabled(False)  
            menu_saved.addAction(act)  
  
        menu_color.addSeparator()  
  
        common_colors = [ ("红色", "red", "#ff4444"), ("橙色", "orange", "#ff8800"), ("黄色", "yellow", "#ffd700"), ("绿色", "green", "#44ff44"), ("青色", "cyan", "#00bcd4"), ("蓝色", "blue", "#4444ff"), ("紫色", "purple", "#bd93f9") ]  
          
        for name, code, hex_c in common_colors:  
            action = QAction(name, self)  
            action.setIcon(self._create_big_circle_icon(hex_c))  
            action.triggered.connect(lambda checked, c=code: self.callbacks.get("set_color", lambda x: None)(c))  
            menu_color.addAction(action)  
              
        menu_color.addSeparator()  
        action_no_color = QAction("❌ 清除颜色", self)  
        action_no_color.triggered.connect(lambda: self.callbacks.get("set_color", lambda x: None)(""))  
        menu_color.addAction(action_no_color)  
  
    # === 【大图标生成逻辑】 ===
    def _create_big_circle_icon(self, hex_color):  
        # 这里的 32 和 24 决定了清晰度和圆的大小
        size = 32 
        pixmap = QPixmap(size, size)  
        pixmap.fill(Qt.GlobalColor.transparent)  
        painter = QPainter(pixmap)  
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)  
        try:  
            col = QColor(hex_color)  
            if not col.isValid(): col = QColor("#ffffff")  
            painter.setBrush(col)  
        except: painter.setBrush(QColor("#ffffff"))  
        painter.setPen(Qt.PenStyle.NoPen)  
        
        # 绘制半径为 11 的圆 (直径22)，在 32x32 的画布中居中
        # 这个尺寸配合上面的 QMenu::icon { width: 24px } 显示效果最佳
        radius = 11
        center = size // 2
        painter.drawEllipse(QPoint(center, center), radius, radius)  
        painter.end()  
        return QIcon(pixmap)

    def _create_color_icon(self, hex_color):
        return self._create_big_circle_icon(hex_color)

    def _create_color_swatch_icon(self, hex_color):
        return self._create_big_circle_icon(hex_color)
  
    def add_open_with_menu(self):  
        menu = self.addMenu("🗃️ 打开方式")  
        apps = self._get_recommended_apps()  
        for app_name, app_exe in apps:  
            if shutil.which(app_exe):  
                action = QAction(f"用 {app_name} 打开", self)  
                action.triggered.connect(lambda checked, exe=app_exe: self.run_app(exe))  
                menu.addAction(action)  
        if apps: menu.addSeparator()  
        action_choose = QAction("选择其他应用...", self)  
        action_choose.triggered.connect(self.open_system_picker)  
        menu.addAction(action_choose)  
  
    def _get_recommended_apps(self):  
        if not self.file_path: return []  
        _, ext = os.path.splitext(self.file_path)  
        ext = ext.lower()  
        apps = []  
        if ext in ['.txt', '.py', '.json', '.xml', '.log', '.md', '.ahk']:  
            apps.append(("记事本", "notepad"))  
            apps.append(("VS Code", "code"))  
        elif ext in ['.jpg', '.png', '.bmp', '.gif']:  
            apps.append(("画图", "mspaint"))  
        elif ext in ['.mp4', '.avi', '.mov']:  
            apps.append(("播放器", "wmplayer"))  
        return apps  
  
    def run_app(self, exe):  
        try: subprocess.Popen([exe, self.file_path])  
        except: pass  
  
    def open_system_picker(self):  
        if not self.file_path: return  
        try: subprocess.Popen(['rundll32', 'shell32.dll,OpenAs_RunDLL', self.file_path])  
        except: pass  
  
    def reveal_in_explorer(self):  
        if self.file_path:  
            try: subprocess.run(['explorer', '/select,', self.file_path])  
            except: pass  
  
    def copy_path_to_clipboard(self):  
        if self.file_path: QApplication.clipboard().setText(self.file_path)  
  
    def copy_file_to_clipboard(self):  
        if self.file_path:  
            data = QApplication.clipboard().mimeData()  
            data.setUrls([QUrl.fromLocalFile(self.file_path)])  
            QApplication.clipboard().setMimeData(data)  
  
class FavoriteContextMenu(BaseContextMenu):  
    def __init__(self, parent=None, callbacks=None):  
        super().__init__(parent)  
        self.callbacks = callbacks or {}  
        self.init_menu()  
    def init_menu(self):  
        action_remove = QAction("从收藏夹中移去", self)  
        action_remove.triggered.connect(self.callbacks.get("remove", lambda: None))  
        self.addAction(action_remove)  
        self.addSeparator()  
        action_reveal = QAction("在“资源管理器”中显示", self)  
        action_reveal.triggered.connect(self.callbacks.get("reveal", lambda: None))  
        self.addAction(action_reveal)