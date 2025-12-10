# G:\PYthon\AssetManager\main.py
import sys
import os
import signal
import time
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor

# === 配置日志系统 ===
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# === 单例模式：杀掉旧进程 ===
def kill_previous_instance():
    pid_file = "running.pid"
    try:
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())
            
            if old_pid != os.getpid():
                try:
                    os.kill(old_pid, signal.SIGTERM)
                    print(f"已检测到旧实例 (PID: {old_pid})，正在终止...")
                    time.sleep(0.5)
                except OSError:
                    pass
    except Exception as e:
        logging.error(f"检查单例失败: {e}")

    try:
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
    except Exception as e:
        logging.error(f"无法写入 PID 文件: {e}")

def exception_hook(exctype, value, traceback):
    logging.critical("发生未捕获的严重错误:", exc_info=(exctype, value, traceback))
    sys.__excepthook__(exctype, value, traceback)

sys.excepthook = exception_hook

from config import DB_PATH
from data.schema import init_tables
from ui.main_window import AssetManagerWindow
from ui.styles import DARK_THEME
# 【核心新增】
from services.startup_service import StartupService

def main():
    kill_previous_instance()

    print("=" * 50)
    print(f"正在启动 Ssuyeh_Bridge v1.3 (硬盘识别修复版)...")
    print(f"数据库路径锁定为: {DB_PATH}")
    
    try:
        init_tables()
    except Exception as e:
        logging.error(f"数据库初始化异常: {e}")
        return

    # 【核心新增】启动时扫描硬盘，注册卷ID
    try:
        print("正在同步硬盘信息...")
        StartupService.sync_drives()
    except Exception as e:
        logging.error(f"硬盘同步失败 (搜索功能可能受限): {e}")

    print("=" * 50)

    app = QApplication(sys.argv)
    
    # 全局深色调色板
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#1e1e1e"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#cccccc"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#252525"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#2a2a2a"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#333333"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#cccccc"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#cccccc"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#2d2d2d"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#cccccc"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Link, QColor("#0078d7"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#0078d7"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    
    app.setPalette(palette)
    app.setStyleSheet(DARK_THEME)
    
    font = app.font()
    font.setFamily("Microsoft YaHei")
    font.setPointSize(10)
    app.setFont(font)
    
    window = AssetManagerWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()