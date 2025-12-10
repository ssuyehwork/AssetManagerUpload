# G:\PYthon\AssetManager\services\rating_service.py

import os
from services.local_store import LocalStoreService
from services.asset_service import AssetService

class RatingService:
    """
    专门负责标记星级的功能模块
    """

    @staticmethod
    def set_rating(full_path, rating):
        """
        设置文件的星级 (0-5)
        同时更新：局部 JSON 和 全局数据库
        返回：更新后的完整元数据(dict)，方便 UI 刷新
        """
        if not full_path or not os.path.exists(full_path):
            return None
        
        # 限制范围 0-5
        rating = max(0, min(5, int(rating)))
        
        folder = os.path.dirname(full_path)
        filename = os.path.basename(full_path)
        
        # 1. 更新局部隐藏文件 (.am_meta.json)
        updated_info = LocalStoreService.update_file_attr(folder, filename, "rating", rating)
        
        # 2. 更新全局数据库 (assets_library.db)
        AssetService.update_rating(full_path, rating)
        
        return updated_info