import sqlite3
from config import DB_PATH

class DBManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def get_connection(self):
        """获取数据库连接，设置 row_factory 以便像字典一样访问数据"""
        conn = sqlite3.connect(self.db_path)
        # 这一步很关键：让查询结果可以通过 row['name'] 访问，而不是 row[0]
        conn.row_factory = sqlite3.Row 
        return conn

# 单例模式：在其他地方直接导入这个实例
db = DBManager()