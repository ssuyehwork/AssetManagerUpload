# G:\PYthon\AssetManager\data\schema.py

from core.db_manager import db

def init_tables():
    """初始化数据库表结构"""
    conn = db.get_connection()
    with conn:
        # 1. 硬盘卷表
        conn.execute('''CREATE TABLE IF NOT EXISTS volumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial_number TEXT UNIQUE NOT NULL, 
            name TEXT,
            mount_point TEXT,
            is_active INTEGER DEFAULT 0 
        )''')

        # 2. 资源表 (增加了 type 字段记录扩展名类型)
        conn.execute('''CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id INTEGER,
            volume_id INTEGER,
            name TEXT,
            path TEXT, 
            type TEXT, 
            size INTEGER,
            rating INTEGER DEFAULT 0,
            color TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(volume_id) REFERENCES volumes(id)
        )''')

        # 3. 标签表
        conn.execute('CREATE TABLE IF NOT EXISTS tags (id INTEGER PRIMARY KEY, name TEXT UNIQUE)')
        
        # 4. 资产-标签关联表
        conn.execute('''CREATE TABLE IF NOT EXISTS asset_tags (
            asset_id INTEGER, tag_id INTEGER, 
            PRIMARY KEY (asset_id, tag_id))''')

        # === 5. 【新增】收藏颜色表 (Global Color Palette) ===
        # hex_value: 颜色代码 (如 #FF5733)
        # name: 颜色名称 (可选，预留给未来功能)
        # added_at: 用于排序，让最近收藏的排在前面
        conn.execute('''CREATE TABLE IF NOT EXISTS saved_colors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hex_value TEXT UNIQUE NOT NULL,
            name TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
    
    conn.close()
    print("数据库结构校验完成 (已包含颜色库)。")