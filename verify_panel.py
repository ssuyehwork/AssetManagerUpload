
import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow
from ui.panels import MetadataPanel
from services.tag_service import TagService

# --- Mock Data ---
# 伪造一个文件路径和元数据，用于测试
TEST_FILE_PATH = os.path.abspath("fake_file.txt")
TEST_META_INFO = {
    "type": "FILE",
    "ext": ".txt",
    "size": 1024,
    "mtime": 1672531200,
    "ctime": 1672531200,
    "atime": 1672531200,
    "view_count": 5,
    "rating": 3,
    "tags": ["existing-tag-1", "existing-tag-2"]
}

# --- Mock Services ---
# 创建一个虚假的 TagService，避免真实的文件操作
class MockTagService:
    @staticmethod
    def add_tags_batch(file_path, tags_to_add):
        print(f">>> MOCK: Adding tags {tags_to_add} to {file_path}")
        TEST_META_INFO["tags"].extend(tags_to_add)
        return TEST_META_INFO

    @staticmethod
    def remove_tag(file_path, tag_to_remove):
        print(f">>> MOCK: Removing tag '{tag_to_remove}' from {file_path}")
        if tag_to_remove in TEST_META_INFO["tags"]:
            TEST_META_INFO["tags"].remove(tag_to_remove)
        return TEST_META_INFO

# 替换真实服务
TagService.add_tags_batch = MockTagService.add_tags_batch
TagService.remove_tag = MockTagService.remove_tag

def main():
    print(">>> [verify_panel.py] Starting isolated MetadataPanel test.")

    # 1. 创建一个最小化的 QApplication
    app = QApplication(sys.argv)

    # 2. 创建一个主窗口来容纳面板
    main_window = QMainWindow()
    main_window.setWindowTitle("MetadataPanel Isolated Test")
    main_window.setGeometry(100, 100, 400, 600)

    # 3. 实例化 MetadataPanel
    print(">>> Instantiating MetadataPanel...")
    panel = MetadataPanel()
    print("    - OK")

    # 4. 模拟真实使用场景
    print(f">>> Simulating file selection: {TEST_FILE_PATH}")
    panel.set_current_file(TEST_FILE_PATH)
    panel.update_info("fake_file.txt", TEST_META_INFO)
    print("    - Panel is now populated with mock data and enabled.")

    # 5. 将面板设置为中心控件并显示
    main_window.setCentralWidget(panel)
    main_window.show()

    print(">>> [verify_panel.py] Test setup complete. Window is now showing.")
    print(">>> Please click on the 'Add Tag...' area to test the popup.")

    sys.exit(app.exec())

if __name__ == "__main__":
    # 创建一个虚假的空文件，以确保 os.path.abspath 能正常工作
    with open("fake_file.txt", "w") as f:
        pass
    main()
