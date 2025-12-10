# G:\PYthon\AssetManager\services\local_store.py

import os
import json
import uuid
import time
import subprocess
import platform

class LocalStoreService:
    META_FILENAME = ".am_meta.json"

    @staticmethod
    def get_meta_path(folder_path):
        return os.path.join(folder_path, LocalStoreService.META_FILENAME)

    @staticmethod
    def _hide_file(file_path):
        if platform.system() == "Windows":
            try:
                subprocess.run(["attrib", "+h", file_path], check=False)
            except Exception:
                pass

    @staticmethod
    def load_local_meta(folder_path):
        meta_path = LocalStoreService.get_meta_path(folder_path)
        if not os.path.exists(meta_path):
            return None
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, PermissionError):
            return None

    @staticmethod
    def save_local_meta(folder_path, data):
        meta_path = LocalStoreService.get_meta_path(folder_path)
        try:
            if platform.system() == "Windows" and os.path.exists(meta_path):
                subprocess.run(["attrib", "-h", meta_path], check=False)
            
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            LocalStoreService._hide_file(meta_path)
        except Exception as e:
            print(f"JSON保存失败: {e}")

    # === 【新增】自动标签配置读写 ===
    @staticmethod
    def get_folder_auto_tags(folder_path):
        """获取文件夹配置的自动标签列表"""
        meta = LocalStoreService.load_local_meta(folder_path)
        if meta and "folder_info" in meta:
            return meta["folder_info"].get("auto_tags", [])
        return []

    @staticmethod
    def set_folder_auto_tags(folder_path, tags_list):
        """保存文件夹的自动标签配置"""
        meta = LocalStoreService.load_local_meta(folder_path)
        if not meta:
            # 如果没有 meta，先初始化一个结构
            meta = {
                "folder_info": {"uuid": str(uuid.uuid4()), "created_at": time.time()},
                "files": {},
                "sub_folders": {}
            }
        
        if "folder_info" not in meta:
            meta["folder_info"] = {}
            
        meta["folder_info"]["auto_tags"] = tags_list
        LocalStoreService.save_local_meta(folder_path, meta)
        return True

    @staticmethod
    def scan_and_update(folder_path):
        if not os.path.exists(folder_path): return None

        # 1. 扫描物理层
        try:
            with os.scandir(folder_path) as entries:
                real_files = {}
                real_dirs = {} 
                for entry in entries:
                    if entry.name == LocalStoreService.META_FILENAME: continue
                    
                    stat = entry.stat()
                    common_info = {
                        "ctime": stat.st_ctime,
                        "mtime": stat.st_mtime,
                        "atime": stat.st_atime,
                    }
                    
                    if entry.is_file():
                        _, ext = os.path.splitext(entry.name)
                        real_files[entry.name] = {
                            **common_info,
                            "size": stat.st_size,
                            "ext": ext.lower()
                        }
                    elif entry.is_dir():
                        real_dirs[entry.name] = {
                            **common_info,
                            "size": 0,
                            "type": "FOLDER"
                        }
        except PermissionError: return None

        # 2. 读取逻辑层
        old_meta = LocalStoreService.load_local_meta(folder_path)
        if old_meta is None:
            old_meta = {
                "folder_info": {"uuid": str(uuid.uuid4()), "created_at": time.time()},
                "files": {},
                "sub_folders": {}
            }
        
        old_files = old_meta.get("files", {})
        old_folders = old_meta.get("sub_folders", {})
        if isinstance(old_folders, list): old_folders = {}

        # 3. 合并数据 (Files)
        new_files_data = {}
        for name, phys_info in real_files.items():
            if name in old_files:
                stored = old_files[name]
                new_files_data[name] = {
                    **phys_info,
                    "tags": stored.get("tags", []),
                    "rating": stored.get("rating", 0),
                    "color": stored.get("color", ""),
                    "view_count": stored.get("view_count", 0),
                    "pinned": stored.get("pinned", False)
                }
            else:
                new_files_data[name] = {
                    **phys_info, "tags": [], "rating": 0, "color": "", "view_count": 0, "pinned": False
                }

        # 4. 合并数据 (Folders)
        new_folders_data = {}
        for name, phys_info in real_dirs.items():
            if name in old_folders:
                stored = old_folders[name]
                new_folders_data[name] = {
                    **phys_info,
                    "tags": stored.get("tags", []),
                    "rating": stored.get("rating", 0),
                    "color": stored.get("color", ""),
                    "view_count": stored.get("view_count", 0),
                    "pinned": stored.get("pinned", False),
                    "file_count": stored.get("file_count", 0) 
                }
            else:
                new_folders_data[name] = {
                    **phys_info, "tags": [], "rating": 0, "color": "", "view_count": 0, "pinned": False
                }

        new_meta = {
            "folder_info": old_meta.get("folder_info"),
            "stats": { 
                "file_count": len(new_files_data), 
                "dir_count": len(new_folders_data), 
                "last_scan": time.time() 
            },
            "files": new_files_data,
            "sub_folders": new_folders_data 
        }

        LocalStoreService.save_local_meta(folder_path, new_meta)
        return new_meta

    @staticmethod
    def increment_view_count(folder_path, filename):
        return LocalStoreService.update_file_attr(folder_path, filename, "view_count", lambda x: (x or 0) + 1)

    @staticmethod
    def update_file_attr(folder_path, filename, key, value):
        meta = LocalStoreService.load_local_meta(folder_path)
        if not meta: return None
        
        target_dict = None
        
        if "files" in meta and filename in meta["files"]:
            target_dict = meta["files"]
        elif "sub_folders" in meta and isinstance(meta["sub_folders"], dict) and filename in meta["sub_folders"]:
            target_dict = meta["sub_folders"]
            
        if target_dict:
            current_val = target_dict[filename].get(key)
            if callable(value):
                new_val = value(current_val)
            else:
                new_val = value
                
            target_dict[filename][key] = new_val
            LocalStoreService.save_local_meta(folder_path, meta)
            return target_dict[filename]
            
        return None