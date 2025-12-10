# G:\PYthon\AssetManager\services\color_label_service.py  
  
import os  
from services.local_store import LocalStoreService  
from services.asset_service import AssetService  
from services.preference_service import PreferenceService  
# 【新增】
import data_manager
  
class ColorLabelService:  
    SHORTCUT_MAP = {  
        1: "red", 2: "orange", 3: "yellow", 4: "green",  
        5: "cyan", 6: "blue", 7: "purple", 0: ""  
    }  
      
    @staticmethod  
    def get_recent_colors():  
        return PreferenceService.get_recent_colors()  
  
    @staticmethod  
    def set_color(full_path, color_name):  
        if not full_path or not os.path.exists(full_path):  
            return None  
          
        folder = os.path.dirname(full_path)  
        filename = os.path.basename(full_path)  
          
        # 1. 更新局部 JSON  
        updated_info = LocalStoreService.update_file_attr(folder, filename, "color", color_name)  
          
        if updated_info:  
            # 2. 更新数据库  
            AssetService.update_color(full_path, color_name)  
              
            if color_name:  
                # 3. 记录历史
                PreferenceService.add_recent_color(color_name)  
                # 4. 【新增】记录到全局 color_labels.json
                data_manager.record_color(color_name)
                  
            return updated_info  
          
        return None