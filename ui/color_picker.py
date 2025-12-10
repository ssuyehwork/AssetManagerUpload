# G:\PYthon\AssetManager\ui\color_picker.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, 
    QPushButton, QLineEdit, QFrame, QColorDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from services.color_service import ColorService

class ColorButton(QPushButton):
    """
    圆形的颜色按钮
    """
    colorClicked = pyqtSignal(str)

    def __init__(self, color_hex, size=28): # 默认大小调整为 28，配合间隔
        super().__init__()
        self.color_hex = color_hex
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # === 核心修复 ===
        # 使用 setFixedSize 强制锁定大小
        self.setFixedSize(size, size)
        
        # 在样式表中显式覆盖全局的 min-width 设置
        # 强制 padding 为 0，确保是正圆
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color_hex};
                border: 1px solid #555;
                border-radius: {size // 2}px;
                min-width: {size}px;  /* 强制覆盖全局最小宽度 */
                max-width: {size}px;
                min-height: {size}px;
                max-height: {size}px;
                padding: 0px;         /* 清除内边距 */
                margin: 0px;
            }}
            QPushButton:hover {{
                border: 2px solid #fff; /* 悬停高亮白边 */
            }}
        """)
        self.clicked.connect(lambda: self.colorClicked.emit(self.color_hex))

class ColorPickerDialog(QDialog):
    colorSelected = pyqtSignal(str) 

    def __init__(self, parent=None, initial_color="#FFFFFF"):
        super().__init__(parent)
        self.setWindowTitle("颜色选择")
        self.setFixedSize(380, 520) # 稍微加高一点，防止拥挤
        self.current_color = initial_color
        
        # 预设颜色 (两行，每行8个)
        self.preset_colors = [
            "#FFADAD", "#FFD6A5", "#FDFFB6", "#CAFFBF", "#9BF6FF", "#A0C4FF", "#BDB2FF", "#FFC6FF",
            "#FF4D6D", "#FF9E00", "#06D6A0", "#118AB2", "#073B4C", "#EF476F", "#7209B7", "#3A0CA3"
        ]

        self.setup_ui()
        self.update_ui_state()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25) # 增加边距

        # 1. 推荐颜色
        lbl_preset = QLabel("🎨 推荐颜色")
        lbl_preset.setStyleSheet("font-weight: bold; color: #eba049; font-size: 13px;")
        layout.addWidget(lbl_preset)

        # 使用 GridLayout，并严格控制间距
        grid_preset = QGridLayout()
        grid_preset.setSpacing(12) # 按钮之间的空隙
        grid_preset.setContentsMargins(0, 5, 0, 5) # 上下留一点白
        
        for i, hex_code in enumerate(self.preset_colors):
            # 这里的 size=32 是圆直径
            btn = ColorButton(hex_code, size=32) 
            btn.colorClicked.connect(self.set_current_color)
            grid_preset.addWidget(btn, i // 8, i % 8)
            
        layout.addLayout(grid_preset)

        # 2. 已收藏
        layout.addSpacing(5)
        lbl_saved = QLabel("⭐ 已收藏 / 最近使用")
        lbl_saved.setStyleSheet("font-weight: bold; color: #aaaaaa; font-size: 13px;")
        layout.addWidget(lbl_saved)

        self.saved_layout = QGridLayout()
        self.saved_layout.setSpacing(12)
        self.saved_layout.setContentsMargins(0, 5, 0, 5)
        self.refresh_saved_colors() 
        layout.addLayout(self.saved_layout)

        layout.addStretch()

        # 3. 自定义
        lbl_custom = QLabel("✏ 自定义")
        lbl_custom.setStyleSheet("font-weight: bold; color: #aaaaaa;")
        layout.addWidget(lbl_custom)

        custom_box = QHBoxLayout()
        
        # Hex 输入框
        self.txt_hex = QLineEdit()
        self.txt_hex.setPlaceholderText("#RRGGBB")
        self.txt_hex.setMaxLength(7)
        self.txt_hex.textChanged.connect(self.on_hex_changed)
        custom_box.addWidget(self.txt_hex)

        # 预览色块
        self.preview_frame = QFrame()
        self.preview_frame.setFixedSize(30, 30)
        custom_box.addWidget(self.preview_frame)

        # 星标按钮
        self.btn_star = QPushButton("★") 
        self.btn_star.setFixedSize(32, 32)
        self.btn_star.setCheckable(True)
        self.btn_star.setToolTip("收藏此颜色")
        self.btn_star.setStyleSheet("""
            QPushButton { 
                background-color: #333; 
                color: #666; 
                border: 1px solid #444; 
                border-radius: 4px;
                font-size: 18px; 
                padding: 0px;
                min-width: 32px; /* 覆盖全局 */
            }
            QPushButton:checked { 
                color: #f5c518; 
                border: 1px solid #f5c518; 
            }
            QPushButton:hover { background-color: #444; }
        """)
        self.btn_star.clicked.connect(self.toggle_favorite)
        custom_box.addWidget(self.btn_star)

        # 调色板
        btn_palette = QPushButton("调色板")
        btn_palette.clicked.connect(self.open_system_picker)
        custom_box.addWidget(btn_palette)

        layout.addLayout(custom_box)

        # 4. 底部
        layout.addSpacing(15)
        bottom_box = QHBoxLayout()
        
        btn_clear = QPushButton("清除")
        btn_clear.setStyleSheet("""
            QPushButton {
                color: #ff6b6b; 
                border: 1px solid #ff6b6b; 
                background: transparent;
            }
            QPushButton:hover { background: #331111; }
        """)
        btn_clear.clicked.connect(lambda: self.done(0))
        
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        
        btn_ok = QPushButton("确定")
        btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #0078d7; 
                color: white; 
                border: 1px solid #005a9e; 
                font-weight: bold;
            }
            QPushButton:hover { background-color: #006cc1; }
        """)
        btn_ok.clicked.connect(self.accept_selection)

        bottom_box.addWidget(btn_clear)
        bottom_box.addStretch()
        bottom_box.addWidget(btn_cancel)
        bottom_box.addWidget(btn_ok)
        
        layout.addLayout(bottom_box)

    def refresh_saved_colors(self):
        for i in reversed(range(self.saved_layout.count())): 
            item = self.saved_layout.itemAt(i)
            if item.widget(): item.widget().setParent(None)
            
        colors = ColorService.get_all_colors()
        for i, hex_code in enumerate(colors[:16]): # 最多显示16个
            btn = ColorButton(hex_code, size=32)
            btn.colorClicked.connect(self.set_current_color)
            self.saved_layout.addWidget(btn, i // 8, i % 8)

    def set_current_color(self, hex_code):
        self.current_color = hex_code.upper()
        self.update_ui_state()

    def update_ui_state(self):
        self.txt_hex.setText(self.current_color)
        self.preview_frame.setStyleSheet(f"background-color: {self.current_color}; border: 1px solid #555; border-radius: 4px;")
        is_saved = ColorService.is_color_saved(self.current_color)
        self.btn_star.setChecked(is_saved)

    def on_hex_changed(self, text):
        if len(text) == 7 and text.startswith("#"):
            self.current_color = text.upper()
            self.preview_frame.setStyleSheet(f"background-color: {self.current_color}; border: 1px solid #555; border-radius: 4px;")
            self.btn_star.setChecked(ColorService.is_color_saved(self.current_color))

    def toggle_favorite(self):
        hex_val = self.txt_hex.text().upper()
        if not hex_val.startswith("#") or len(hex_val) != 7: return

        if self.btn_star.isChecked():
            if ColorService.add_color(hex_val): self.refresh_saved_colors()
        else:
            ColorService.remove_color(hex_val)
            self.refresh_saved_colors()

    def open_system_picker(self):
        col = QColorDialog.getColor(QColor(self.current_color), self, "选择颜色")
        if col.isValid():
            self.set_current_color(col.name().upper())

    def accept_selection(self):
        self.colorSelected.emit(self.current_color)
        self.accept()