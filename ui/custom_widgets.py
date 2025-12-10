# G:\PYthon\AssetManager\ui\custom_widgets.py

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QToolButton, QMenu, QFrame, 
    QLineEdit, QSlider, QButtonGroup, QStyle, QApplication
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPoint
from PyQt6.QtGui import QAction

class CustomDockTitleBar(QFrame):
    def __init__(self, dock_widget, all_docks_dict, parent=None):
        super().__init__(parent)
        self.setObjectName("DockTitleBar")
        self.dock_widget = dock_widget
        self.all_docks_dict = all_docks_dict
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(8, 2, 4, 2)
        self.layout.setSpacing(0)

        self.title_label = QLabel(dock_widget.windowTitle())
        self.title_label.setStyleSheet("font-weight: 600; color: #999; font-size: 11px;")
        self.layout.addWidget(self.title_label)
        self.layout.addStretch()

        self.menu_btn = QToolButton()
        self.menu_btn.setText("≡") 
        self.menu_btn.setObjectName("PanelMenuBtn")
        self.menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.menu_btn.setFixedSize(24, 20) 
        self.menu_btn.clicked.connect(self.show_panel_menu)
        self.layout.addWidget(self.menu_btn)

    def show_panel_menu(self):
        menu = QMenu(self)
        for name, dock in self.all_docks_dict.items():
            action = QAction(name, self)
            action.setCheckable(True)
            action.setChecked(dock.isVisible())
            action.triggered.connect(lambda checked, d=dock: d.setVisible(checked))
            menu.addAction(action)
        menu.exec(self.menu_btn.mapToGlobal(QPoint(0, self.menu_btn.height())))

class TitleBar(QFrame):
    sig_win_min = pyqtSignal()
    sig_win_max = pyqtSignal()
    sig_win_close = pyqtSignal()
    sig_refresh = pyqtSignal()
    sig_trash = pyqtSignal()
    sig_pin = pyqtSignal(bool)
    sig_color = pyqtSignal()
    sig_settings = pyqtSignal()
    sig_new_folder = pyqtSignal()
    sig_view_menu = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TitleBar")
        self.setFixedHeight(34)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setSpacing(4)

        self.lbl_icon = QLabel("💾")
        self.lbl_title = QLabel(" Ssuyeh_Bridge")
        self.lbl_title.setStyleSheet("font-weight: bold; color: #ccc; font-size: 13px;")
        layout.addWidget(self.lbl_icon)
        layout.addWidget(self.lbl_title)
        
        layout.addStretch()

        self.btn_new_folder = self._create_btn("📁", "新建文件夹")
        self.btn_new_folder.clicked.connect(self.sig_new_folder.emit)
        layout.addWidget(self.btn_new_folder)

        self.btn_refresh = self._create_btn("🔄", "刷新")
        self.btn_refresh.clicked.connect(self.sig_refresh.emit)
        layout.addWidget(self.btn_refresh)

        self.btn_trash = self._create_btn("🗑️", "回收站")
        self.btn_trash.clicked.connect(self.sig_trash.emit)
        layout.addWidget(self.btn_trash)

        self.btn_pin = self._create_btn("📌", "窗口置顶")
        self.btn_pin.setCheckable(True)
        self.btn_pin.setObjectName("BtnPin")
        self.btn_pin.toggled.connect(self.sig_pin.emit)
        layout.addWidget(self.btn_pin)

        self.btn_color = self._create_btn("🎨", "颜色库")
        self.btn_color.clicked.connect(self.sig_color.emit)
        layout.addWidget(self.btn_color)

        self.btn_view = self._create_btn("👁", "视图选项")
        self.btn_view.clicked.connect(self.sig_view_menu.emit)
        layout.addWidget(self.btn_view)

        self.btn_settings = self._create_btn("📖", "设置")
        self.btn_settings.clicked.connect(self.sig_settings.emit)
        layout.addWidget(self.btn_settings)

        lbl_sep = QLabel("|")
        lbl_sep.setObjectName("VLine")
        lbl_sep.setStyleSheet("color: #555; padding: 0 6px;")
        layout.addWidget(lbl_sep)

        self.btn_min = self._create_btn("—", "最小化", width=46)
        self.btn_max = self._create_btn("□", "最大化", width=46)
        self.btn_close = self._create_btn("✕", "关闭", width=46)
        self.btn_close.setObjectName("BtnClose") 

        self.btn_min.clicked.connect(self.sig_win_min.emit)
        self.btn_max.clicked.connect(self.sig_win_max.emit)
        self.btn_close.clicked.connect(self.sig_win_close.emit)

        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_max)
        layout.addWidget(self.btn_close)

    def _create_btn(self, text, tip, width=32):
        btn = QToolButton()
        btn.setText(text)
        btn.setToolTip(tip)
        btn.setFixedSize(width, 32)
        btn.setProperty("class", "TitleBtn") 
        return btn

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.window().windowHandle().startSystemMove()
            event.accept()

    def mouseDoubleClickEvent(self, event):
        self.sig_win_max.emit()

class NavBar(QFrame):
    sig_back = pyqtSignal()
    sig_fwd = pyqtSignal()
    sig_up = pyqtSignal()
    sig_view_grid = pyqtSignal()
    sig_view_list = pyqtSignal()
    sig_zoom = pyqtSignal(int)
    sig_address_entered = pyqtSignal(str)
    sig_search_entered = pyqtSignal(str)
    # 【核心修复】定义排序信号
    sig_sort_changed = pyqtSignal(str) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NavBar")
        self.setFixedHeight(40)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(10)

        self.btn_back = self._create_nav_btn("◀", "后退", "BtnBack")
        self.btn_back.clicked.connect(self.sig_back.emit)

        self.btn_fwd = self._create_nav_btn("▶", "前进", "BtnFwd")
        self.btn_fwd.clicked.connect(self.sig_fwd.emit)

        self.btn_up = self._create_nav_btn("▲", "上一级", "BtnUp")
        self.btn_up.clicked.connect(self.sig_up.emit)

        layout.addWidget(self.btn_back)
        layout.addWidget(self.btn_fwd)
        layout.addWidget(self.btn_up)

        # 地址栏
        self.address_bar = QLineEdit()
        self.address_bar.setObjectName("AddressBar")
        self.address_bar.setPlaceholderText("输入路径...")
        self.address_bar.returnPressed.connect(lambda: self.sig_address_entered.emit(self.address_bar.text()))
        layout.addWidget(self.address_bar, 3) 

        # 搜索框
        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("AddressBar") 
        self.search_bar.setPlaceholderText("搜索...")
        self.search_bar.returnPressed.connect(lambda: self.sig_search_entered.emit(self.search_bar.text()))
        layout.addWidget(self.search_bar, 1)

        layout.addSpacing(10)
        self.btn_grp = QButtonGroup(self)
        self.btn_grp.setExclusive(True)
        
        # 视图切换按钮
        self.btn_grid = self._create_tool_btn("⊞", "网格视图")
        self.btn_grid.setProperty("class", "ToolBtnBlue") 
        self.btn_grid.setCheckable(True)
        self.btn_grid.setChecked(True)
        self.btn_grid.clicked.connect(self.sig_view_grid.emit)
        
        self.btn_list = self._create_tool_btn("☰", "列表视图")
        self.btn_list.setProperty("class", "ToolBtnBlue")
        self.btn_list.setCheckable(True)
        self.btn_list.clicked.connect(self.sig_view_list.emit)
        
        self.btn_grp.addButton(self.btn_grid)
        self.btn_grp.addButton(self.btn_list)
        
        layout.addWidget(self.btn_grid)
        layout.addWidget(self.btn_list)

        # 【核心新增】排序按钮
        self.btn_sort = self._create_tool_btn("⇅", "排序")
        self.btn_sort.setProperty("class", "ToolBtnBlue")
        self.btn_sort.clicked.connect(self.show_sort_menu)
        layout.addWidget(self.btn_sort)

        layout.addSpacing(5)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(80, 256)
        self.slider.setValue(120)
        self.slider.setFixedWidth(100)
        self.slider.valueChanged.connect(self.sig_zoom.emit)
        layout.addWidget(self.slider)

    def show_sort_menu(self):
        menu = QMenu(self)
        
        actions = [
            ("名称 (A-Z)", "name_asc"),
            ("名称 (Z-A)", "name_desc"),
            ("修改日期 (最新)", "date_desc"),
            ("修改日期 (最旧)", "date_asc"),
            ("大小 (大-小)", "size_desc"),
            ("大小 (小-大)", "size_asc"),
            ("评级 (高-低)", "rating_desc"),
            ("评级 (低-高)", "rating_asc")
        ]
        
        for text, key in actions:
            act = QAction(text, self)
            act.triggered.connect(lambda checked, k=key: self.sig_sort_changed.emit(k))
            menu.addAction(act)
            
        menu.exec(self.btn_sort.mapToGlobal(QPoint(0, self.btn_sort.height())))

    def _create_nav_btn(self, text, tip, obj_name):
        btn = QToolButton()
        btn.setText(text)
        btn.setToolTip(tip)
        btn.setObjectName(obj_name) 
        btn.setFixedSize(30, 30)
        return btn

    def _create_tool_btn(self, text, tip):
        btn = QToolButton()
        btn.setText(text)
        btn.setToolTip(tip)
        btn.setFixedSize(28, 28)
        return btn