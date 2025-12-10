# G:\PYthon\AssetManager\data_manager.py
import os
import json
from config import BASE_DIR

# ==================== 文件路径 ====================
FAVORITES_FILE = os.path.join(BASE_DIR, "favorites.json")
TAGS_FILE = os.path.join(BASE_DIR, "tags.json")
COLOR_LABELS_FILE = os.path.join(BASE_DIR, "color_labels.json")

# ==================== 基础读写工具 ====================
def _load_json(filepath, default=None):
    if default is None:
        default = []
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return default

def _save_json(filepath, data):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存失败 {filepath}: {e}")

# ==================== 1. 收藏夹管理 ====================
def get_favorites():
    return _load_json(FAVORITES_FILE, [])

def add_favorite(path):
    path = os.path.normpath(path)
    favs = get_favorites()
    if path not in favs:
        favs.append(path)
        _save_json(FAVORITES_FILE, favs)

def remove_favorite(path):
    path = os.path.normpath(path)
    favs = get_favorites()
    if path in favs:
        favs.remove(path)
        _save_json(FAVORITES_FILE, favs)

def is_favorite(path):
    return os.path.normpath(path) in get_favorites()

# ==================== 2. 标签管理 ====================
def get_all_tags():
    return _load_json(TAGS_FILE, [])

def add_tag(tag_name):
    tag_name = str(tag_name).strip()
    if not tag_name:
        return
    tags = get_all_tags()
    if tag_name not in tags:
        tags.append(tag_name)
        tags.sort()
        _save_json(TAGS_FILE, tags)

def remove_tag(tag_name):
    tags = get_all_tags()
    if tag_name in tags:
        tags.remove(tag_name)
        _save_json(TAGS_FILE, tags)

# ==================== 3. 【核心新增】颜色标签管理 ====================
def get_all_colors():
    """获取所有记录过的颜色"""
    return _load_json(COLOR_LABELS_FILE, [])

def record_color(color_val):
    """
    记录一个使用过的颜色 (可以是 'red' 也可以是 '#FF0000')
    供 ColorLabelService 调用
    """
    color_val = str(color_val).strip()
    if not color_val: return
    
    colors = get_all_colors()
    
    # 兼容性处理：确保列表里都是字符串
    simple_colors = []
    for c in colors:
        if isinstance(c, dict):
            simple_colors.append(c.get("color", ""))
        else:
            simple_colors.append(c)
    
    if color_val not in simple_colors:
        simple_colors.append(color_val)
        _save_json(COLOR_LABELS_FILE, simple_colors)