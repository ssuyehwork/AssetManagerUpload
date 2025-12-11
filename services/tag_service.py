# G:\PYthon\AssetManager\services\tag_service.py

import os
from services.local_store import LocalStoreService
from services.preference_service import PreferenceService
from services.asset_service import AssetService # 【新增引用】
import data_manager 

class TagService:
    @staticmethod
    def add_tag(full_path, tag_name):
        if not full_path or not os.path.exists(full_path) or not tag_name:
            return None
        
        tag_name = tag_name.strip()
        folder = os.path.dirname(full_path)
        filename = os.path.basename(full_path)
        
        def update_logic(old_tags):
            if not isinstance(old_tags, list): old_tags = []
            if tag_name not in old_tags:
                old_tags.append(tag_name)
            return old_tags

        updated_info = LocalStoreService.update_file_attr(folder, filename, "tags", update_logic)
        
        if updated_info:
            new_tags = updated_info.get("tags", [])
            # 1. 存入历史记录
            PreferenceService.add_recent_tag(tag_name)
            # 2. 存入全局 tags.json
            data_manager.add_tag(tag_name)
            # 3. 【核心】同步到数据库
            AssetService.update_tags(full_path, new_tags)
            
        return updated_info

    @staticmethod
    def add_tags_batch(full_path, tag_list):
        if not full_path or not os.path.exists(full_path) or not tag_list:
            return None
        
        folder = os.path.dirname(full_path)
        filename = os.path.basename(full_path)
        
        def update_logic(old_tags):
            if not isinstance(old_tags, list): old_tags = []
            for t in tag_list:
                t = str(t).strip()
                if t and t not in old_tags:
                    old_tags.append(t)
            return old_tags

        updated_info = LocalStoreService.update_file_attr(folder, filename, "tags", update_logic)
        
        if updated_info:
            new_tags = updated_info.get("tags", [])
            for t in tag_list:
                t = str(t).strip()
                if t:
                    PreferenceService.add_recent_tag(t)
                    data_manager.add_tag(t)
            # 【核心】同步到数据库
            AssetService.update_tags(full_path, new_tags)
                
        return updated_info

    @staticmethod
    def remove_tag(full_path, tag_name):
        if not full_path or not os.path.exists(full_path) or not tag_name:
            return None
            
        folder = os.path.dirname(full_path)
        filename = os.path.basename(full_path)
        
        def update_logic(old_tags):
            if isinstance(old_tags, list) and tag_name in old_tags:
                old_tags.remove(tag_name)
            return old_tags

        updated_info = LocalStoreService.update_file_attr(folder, filename, "tags", update_logic)
        
        if updated_info:
            new_tags = updated_info.get("tags", [])
            # 【核心】同步到数据库
            AssetService.update_tags(full_path, new_tags)

        return updated_info

    @staticmethod
    def add_tags_batch(full_path, tag_list):
        if not full_path or not os.path.exists(full_path) or not tag_list:
            return None
        
        folder = os.path.dirname(full_path)
        filename = os.path.basename(full_path)
        
        def update_logic(old_tags):
            if not isinstance(old_tags, list): old_tags = []
            for t in tag_list:
                t = str(t).strip()
                if t and t not in old_tags:
                    old_tags.append(t)
            return old_tags

        updated_info = LocalStoreService.update_file_attr(folder, filename, "tags", update_logic)
        
        if updated_info:
            new_tags = updated_info.get("tags", [])
            for t in tag_list:
                t = str(t).strip()
                if t:
                    PreferenceService.add_recent_tag(t)
                    data_manager.add_tag(t)
            # 【核心】同步到数据库
            AssetService.update_tags(full_path, new_tags)
                
        return updated_info

    @staticmethod
    def remove_tags_batch(full_path, tag_list):
        if not full_path or not os.path.exists(full_path) or not tag_list:
            return None
        
        folder = os.path.dirname(full_path)
        filename = os.path.basename(full_path)
        
        def update_logic(old_tags):
            if not isinstance(old_tags, list):
                return []
            
            tags_to_remove_set = set(tag_list)
            
            # 使用列表推导式过滤掉要删除的标签
            new_tags_list = [t for t in old_tags if t not in tags_to_remove_set]
            
            return new_tags_list

        updated_info = LocalStoreService.update_file_attr(folder, filename, "tags", update_logic)
        
        if updated_info:
            new_tags = updated_info.get("tags", [])
            # 【核心】同步到数据库
            AssetService.update_tags(full_path, new_tags)
                
        return updated_info