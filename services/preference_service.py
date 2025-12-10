# G:\PYthon\AssetManager\services\preference_service.py

import os
import json
import time
from config import PREFS_PATH

class PreferenceService:
    MAX_HISTORY_COUNT = 20

    @staticmethod
    def _load_prefs():
        if not os.path.exists(PREFS_PATH): return {}
        try:
            with open(PREFS_PATH, 'r', encoding='utf-8') as f: return json.load(f)
        except: return {}

    @staticmethod
    def _save_prefs(data):
        try:
            with open(PREFS_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except: pass

    @staticmethod
    def _add_to_history(key, value):
        data = PreferenceService._load_prefs()
        history = data.get(key, [])
        cleaned = []
        for item in history:
            if isinstance(item, dict): cleaned.append(item)
            elif isinstance(item, str): cleaned.append({"val": item, "time": 0})
        cleaned = [x for x in cleaned if x["val"] != value]
        cleaned.insert(0, {"val": value, "time": time.time()})
        if len(cleaned) > PreferenceService.MAX_HISTORY_COUNT: cleaned = cleaned[:PreferenceService.MAX_HISTORY_COUNT]
        data[key] = cleaned
        PreferenceService._save_prefs(data)

    # === 【新增】删除历史记录 ===
    @staticmethod
    def remove_search_history(keyword):
        data = PreferenceService._load_prefs()
        history = data.get("search_history", [])
        # 过滤掉要删除的
        new_history = [
            x for x in history 
            if (isinstance(x, dict) and x["val"] != keyword) or (isinstance(x, str) and x != keyword)
        ]
        data["search_history"] = new_history
        PreferenceService._save_prefs(data)
        
        # 返回新的纯文本列表供界面刷新
        result = []
        for item in new_history:
            if isinstance(item, dict): result.append(item.get("val"))
            elif isinstance(item, str): result.append(item)
        return result

    # === 窗口布局 ===
    @staticmethod
    def save_window_layout(geometry_hex, state_hex):
        data = PreferenceService._load_prefs()
        data["window_geometry"] = geometry_hex
        data["window_state"] = state_hex
        PreferenceService._save_prefs(data)

    @staticmethod
    def get_window_layout():
        data = PreferenceService._load_prefs()
        return data.get("window_geometry"), data.get("window_state")

    # === 颜色 ===
    @staticmethod
    def get_recent_colors():
        data = PreferenceService._load_prefs()
        raw = data.get("recent_colors", [])
        return [x["val"] if isinstance(x, dict) else x for x in raw]

    @staticmethod
    def add_recent_color(color_name):
        if color_name.startswith("#"): color_name = color_name.upper()
        PreferenceService._add_to_history("recent_colors", color_name)

    # === 标签 ===
    @staticmethod
    def get_recent_tags():
        data = PreferenceService._load_prefs()
        history = data.get("recent_tags", [])
        result = []
        for item in history:
            if isinstance(item, dict): result.append(item.get("val"))
            elif isinstance(item, str): result.append(item)
        return [str(r) for r in result if r]

    @staticmethod
    def add_recent_tag(tag_name):
        if tag_name: PreferenceService._add_to_history("recent_tags", tag_name.strip())

    # === 搜索历史 ===
    @staticmethod
    def get_search_history():
        data = PreferenceService._load_prefs()
        history = data.get("search_history", [])
        result = []
        for item in history:
            if isinstance(item, dict): result.append(item.get("val"))
            elif isinstance(item, str): result.append(item)
        return [str(r) for r in result if r]

    @staticmethod
    def add_search_history(keyword):
        if keyword: PreferenceService._add_to_history("search_history", keyword.strip())