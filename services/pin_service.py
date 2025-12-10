# G:\PYthon\AssetManager\services\pin_service.py

import os
from services.local_store import LocalStoreService

class PinService:
    @staticmethod
    def set_pinned(full_path, is_pinned):
        """
        设置文件的置顶状态
        """
        if not full_path or not os.path.exists(full_path):
            return None
        
        folder = os.path.dirname(full_path)
        filename = os.path.basename(full_path)
        
        # 更新局部 JSON (.am_meta.json)
        # 注意：pinned 属性只存在于 JSON 中，数据库目前没有该字段，仅影响当前文件夹视图
        updated_info = LocalStoreService.update_file_attr(folder, filename, "pinned", bool(is_pinned))
        
        return updated_info

    @staticmethod
    def toggle_pinned(full_path):
        """
        切换置顶状态
        """
        if not full_path or not os.path.exists(full_path):
            return None
            
        folder = os.path.dirname(full_path)
        filename = os.path.basename(full_path)
        
        # 读取当前状态并取反
        def toggle_logic(current_val):
            return not bool(current_val)

        return LocalStoreService.update_file_attr(folder, filename, "pinned", toggle_logic)