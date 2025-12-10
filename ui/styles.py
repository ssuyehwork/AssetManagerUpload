# G:\PYthon\AssetManager\ui\styles.py

DARK_THEME = """
/* =======================================================
   1. 全局架构
   ======================================================= */
QWidget {
    background-color: #252525;
    color: #cccccc;
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    font-size: 12px;
}

QMainWindow {
    background-color: #1e1e1e;
    border: 1px solid #000; 
}

/* 面板缝隙 (Splitter) - 2px 纯黑 */
QMainWindow::separator {
    background-color: #000000;
    width: 2px;
    height: 2px;
    border: none;
}
QMainWindow::separator:hover {
    background-color: #0078d7;
}

/* =======================================================
   【新增】Tooltip 样式 (不再是白色)
   ======================================================= */
QToolTip {
    background-color: #2b2b2b;       /* 深灰色背景 */
    color: #f0f0f0;                  /* 亮白色文字 */
    border: 1px solid #0078d7;       /* 蓝色边框，显眼 */
    padding: 4px;
    border-radius: 2px;
}

/* =======================================================
   2. 面板 (Docks)
   ======================================================= */
QDockWidget {
    color: #eeeeee;
    background-color: #252525;
    border: 3px solid #000000;
    titlebar-close-icon: url(close.png);
    margin: 1px; 
}

QDockWidget > QWidget {
    background-color: #252525;
    border: none; 
}

QFrame#DockTitleBar {
    background-color: #2d2d2d;
    border-bottom: 2px solid #000000;
}

QDockWidget QTreeView, QDockWidget QListView, QDockWidget QTableWidget {
    background-color: #252525;
    border: none; 
    outline: none;
}

/* =======================================================
   3. 中间内容区
   ======================================================= */
QStackedWidget {
    background-color: #2b2b2b; 
    border: none; 
}
QStackedWidget QListView, QStackedWidget QTreeView {
    background-color: #2b2b2b;
    border: none;
}

/* =======================================================
   4. 列表与表格 (通用)
   ======================================================= */
QTreeView, QListView, QTableWidget {
    background-color: #252525;
    alternate-background-color: #2a2a2a; 
    border: none;
    outline: none;
}
QTreeView::item, QListView::item, QTableWidget::item {
    padding: 4px; color: #ccc; border: none;
}
QTreeView::item:hover, QListView::item:hover {
    background-color: #3a3a3a;
}
QTreeView::item:selected, QListView::item:selected {
    background-color: #0078d7;
    color: white;
}
QTableWidget::item:selected {
    background-color: transparent !important;
    color: #ccc !important;
}

/* =======================================================
   5. 头部区域
   ======================================================= */
QFrame#TitleBar { background-color: #1f1f1f; border-bottom: 1px solid #000; }
QFrame#NavBar { background-color: #252525; border-bottom: 1px solid #000; }

QFrame#TitleBar QToolButton {
    background-color: transparent; border: none; border-radius: 0; color: #aaa;
}
QFrame#TitleBar QToolButton:hover { background-color: #333; color: white; }
QToolButton#BtnClose:hover { background-color: #e81123; color: white; }
QToolButton#BtnPin:checked { background-color: #383838; border: 1px solid #555; }

QToolButton#BtnBack, QToolButton#BtnFwd, QToolButton#BtnUp {
    background-color: transparent; border: none; color: #0078d7; font-size: 20px; font-weight: 900;
}
QToolButton#BtnBack:hover, QToolButton#BtnFwd:hover, QToolButton#BtnUp:hover {
    background-color: #333; color: #66b3ff; border-radius: 4px;
}
QToolButton#BtnBack:disabled, QToolButton#BtnFwd:disabled { color: #004578; }

QToolButton.ToolBtnBlue {
    background-color: transparent; border: none; color: #0078d7; font-weight: bold; border-radius: 3px;
}
QToolButton.ToolBtnBlue:hover { background-color: #333; color: #66b3ff; }
QToolButton.ToolBtnBlue:checked { background-color: #004578; color: white; }

/* =======================================================
   6. 其他
   ======================================================= */
QHeaderView::section {
    background-color: #2d2d2d; color: #bbb; padding: 5px; border: none; border-right: 1px solid #000; border-bottom: 1px solid #000;
}
QLineEdit#AddressBar {
    background-color: #1f1f1f; border: 1px solid #000; border-radius: 4px; color: #eee; padding: 4px 8px;
}
QScrollBar:vertical { background: #252525; width: 12px; }
QScrollBar::handle:vertical { background: #444; border-radius: 6px; min-height: 20px; margin: 2px; }
QScrollBar::handle:vertical:hover { background: #666; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QMenu { background-color: #2d2d2d; border: 1px solid #000; }
QMenu::item { color: #eee; }
QMenu::item:selected { background-color: #0078d7; }

QToolButton#PanelMenuBtn { background-color: transparent; border: none; color: #999; font-weight: bold; }
QToolButton#PanelMenuBtn:hover { color: white; background-color: #444; }

QDialog { background-color: #1e1e1e; border: 1px solid #333; }
QDialog QLabel { color: #ddd; background-color: transparent; }
QDialog QLineEdit { background-color: #252525; border: 1px solid #444; color: #fff; padding: 6px; }
QDialog QPushButton { background-color: #333; border: 1px solid #444; color: #eee; padding: 6px 12px; }

QPushButton#FloatCopyBtn {
    background-color: #0078d7; color: white; border: 1px solid #005a9e; border-radius: 4px; padding: 4px 8px; font-weight: bold; font-size: 11px;
}
QPushButton#FloatCopyBtn:hover { background-color: #006cc1; }
"""