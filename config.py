# G:\PYthon\AssetManager\config.py  
  
import os  
  
# 获取项目根目录  
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  
  
# 1. 数据库路径  
DB_NAME = "assets_library.db"  
DB_PATH = os.path.join(BASE_DIR, DB_NAME)  
  
# 2. 【新增】用户偏好设置路径 (存储最近使用的颜色、标签等)  
PREFS_NAME = "user_prefs.json"  
PREFS_PATH = os.path.join(BASE_DIR, PREFS_NAME)  
  
# 3. 支持的文件格式  
SUPPORTED_EXTS = {  
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', # 图片  
    '.mp4', '.mov', '.avi', '.mkv',                           # 视频  
    '.mp3', '.wav',                                           # 音频  
    '.txt', '.md', '.json', '.xml', '.py', '.ahk', '.log'     # 文本/代码  
}  
