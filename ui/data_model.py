# G:\PYthon\AssetManager\ui\data_model.py

import os
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QIcon, QPixmap
from PyQt6.QtWidgets import QFileIconProvider
from PyQt6.QtCore import Qt, QFileInfo, QSize, QMimeData, QUrl

class AssetModel(QStandardItemModel):
    ROLE_FULL_PATH = Qt.ItemDataRole.UserRole + 1
    ROLE_META_DATA = Qt.ItemDataRole.UserRole + 2
    
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}

    def __init__(self):
        super().__init__()
        self.icon_provider = QFileIconProvider() 

    def mimeTypes(self):
        types = super().mimeTypes()
        types.append('text/uri-list')
        return types

    def mimeData(self, indexes):
        mime_data = super().mimeData(indexes)
        urls = []
        processed_paths = set()
        for index in indexes:
            if index.isValid():
                path = self.data(index, self.ROLE_FULL_PATH)
                if path and path not in processed_paths:
                    urls.append(QUrl.fromLocalFile(path))
                    processed_paths.add(path)
        if urls: mime_data.setUrls(urls)
        return mime_data

    def load_data(self, folder_path, meta_data):
        self.clear() 
        if not meta_data: return

        sub_folders = meta_data.get("sub_folders", {})
        files_info = meta_data.get("files", {})

        if isinstance(sub_folders, list):
            temp = {}
            for name in sub_folders: temp[name] = {}
            sub_folders = temp

        # === 【核心排序逻辑】定义 4 个桶 ===
        pinned_folders = []
        pinned_files = []
        normal_folders = []
        normal_files = []

        def process_item(name, info, is_folder):
            display_name = os.path.basename(name) if os.path.isabs(name) else name
            item = QStandardItem(display_name)
            
            if "full_path_override" in info: full_path = info["full_path_override"]
            else: full_path = os.path.join(folder_path, name)
            
            item.setData(full_path, self.ROLE_FULL_PATH)
            
            # 补全元数据
            meta = info.copy()
            if is_folder:
                meta.update({
                    "type": "FOLDER",
                    "pinned": info.get("pinned", False),
                    "file_count": info.get("file_count", 0), 
                    "rating": info.get("rating", 0), 
                    "color": info.get("color", ""),   
                    "tags": info.get("tags", []),
                    "ctime": info.get("ctime", 0),
                    "mtime": info.get("mtime", 0)
                })
                item.setIcon(self.icon_provider.icon(QFileIconProvider.IconType.Folder))
            else:
                _, ext = os.path.splitext(full_path)
                ext = ext.lower()
                if "type" not in meta: meta["type"] = ext.replace(".", "").upper() if ext else "FILE"
                if "ext" not in meta: meta["ext"] = ext
                
                if ext in self.IMAGE_EXTENSIONS and os.path.exists(full_path):
                    pixmap = QPixmap(full_path)
                    if not pixmap.isNull():
                        scaled = pixmap.scaled(QSize(256, 256), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        item.setIcon(QIcon(scaled))
                    else: item.setIcon(self.icon_provider.icon(QFileInfo(full_path)))
                else: item.setIcon(self.icon_provider.icon(QFileInfo(full_path)))

            item.setData(meta, self.ROLE_META_DATA)
            
            # 分桶
            is_pinned = meta.get("pinned", False)
            if is_pinned:
                if is_folder: pinned_folders.append(item)
                else: pinned_files.append(item)
            else:
                if is_folder: normal_folders.append(item)
                else: normal_files.append(item)

        # 遍历数据
        for dname, dinfo in sub_folders.items(): process_item(dname, dinfo, True)
        for fname, finfo in files_info.items(): process_item(fname, finfo, False)

        # === 【核心排序】依次添加：置顶文件夹 -> 置顶文件 -> 普通文件夹 -> 普通文件 ===
        # 桶内按名称简单排序
        pinned_folders.sort(key=lambda x: x.text())
        pinned_files.sort(key=lambda x: x.text())
        normal_folders.sort(key=lambda x: x.text())
        normal_files.sort(key=lambda x: x.text())

        for item in pinned_folders: self.appendRow(item)
        for item in pinned_files: self.appendRow(item)
        for item in normal_folders: self.appendRow(item)
        for item in normal_files: self.appendRow(item)

    def find_index_by_path(self, file_path):
        """Find the QModelIndex for a given full file path."""
        for row in range(self.rowCount()):
            index = self.index(row, 0)
            path_in_model = self.data(index, self.ROLE_FULL_PATH)
            if path_in_model == file_path:
                return index
        return Qt.QModelIndex()