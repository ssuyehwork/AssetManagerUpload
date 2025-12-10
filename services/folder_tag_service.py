# G:\PYthon\AssetManager\services\folder_tag_service.py

from services.local_store import LocalStoreService
from services.tag_service import TagService
import os
import logging

class FolderTagService:
    @staticmethod
    def set_auto_tags(folder_path, tags_list, recursive=True):
        """
        设置自动标签配置，并立即应用到当前文件夹（及子文件夹）
        """
        # 1. 保存配置到 .am_meta.json
        LocalStoreService.set_folder_auto_tags(folder_path, tags_list)
        
        # 2. 递归应用标签
        if recursive and tags_list:
            FolderTagService._apply_recursive(folder_path, tags_list)

    @staticmethod
    def _apply_recursive(folder_path, tags_list):
        """递归遍历目录并添加标签"""
        # 遍历当前目录下的所有文件和文件夹
        for root, dirs, files in os.walk(folder_path):
            # 给文件打标签
            for file in files:
                if file == LocalStoreService.META_FILENAME: continue
                full_path = os.path.join(root, file)
                TagService.add_tags_batch(full_path, tags_list)
            
            # 给文件夹打标签
            for d in dirs:
                full_path = os.path.join(root, d)
                TagService.add_tags_batch(full_path, tags_list)

    @staticmethod
    def scan_and_apply_auto_tags(folder_path, meta_data):
        """
        【核心逻辑】供扫描线程调用。
        检查当前文件夹是否有自动标签配置，如果有，找出没有标签的新文件进行自动标记。
        """
        auto_tags = LocalStoreService.get_folder_auto_tags(folder_path)
        if not auto_tags:
            return False

        updated = False
        # 1. 检查文件
        files_map = meta_data.get("files", {})
        for filename, info in files_map.items():
            current_tags = info.get("tags", [])
            # 只要自动标签不在当前标签里，就追加
            missing_tags = [t for t in auto_tags if t not in current_tags]
            
            if missing_tags:
                full_path = os.path.join(folder_path, filename)
                # 直接调用 TagService 写入
                TagService.add_tags_batch(full_path, missing_tags)
                updated = True

        # 2. 检查子文件夹 (同理)
        sub_folders = meta_data.get("sub_folders", {})
        if isinstance(sub_folders, dict):
            for dirname, info in sub_folders.items():
                current_tags = info.get("tags", [])
                missing_tags = [t for t in auto_tags if t not in current_tags]
                if missing_tags:
                    full_path = os.path.join(folder_path, dirname)
                    TagService.add_tags_batch(full_path, missing_tags)
                    updated = True
                
        return updated