# G:\PYthon\AssetManager\services\color_service.py

from core.db_manager import db
import time

class ColorService:
    """
    颜色管理服务
    负责管理用户的全局调色板（收藏的颜色）
    """

    @staticmethod
    def add_color(hex_value, name=None):
        """收藏一个颜色"""
        hex_value = hex_value.upper() # 强制大写
        conn = db.get_connection()
        try:
            with conn:
                # 使用 INSERT OR IGNORE 避免重复收藏同一个颜色报错
                conn.execute('''
                    INSERT OR IGNORE INTO saved_colors (hex_value, name, added_at)
                    VALUES (?, ?, ?)
                ''', (hex_value, name, time.time()))
            return True
        except Exception as e:
            print(f"收藏颜色失败: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def remove_color(hex_value):
        """取消收藏颜色"""
        conn = db.get_connection()
        try:
            with conn:
                conn.execute('DELETE FROM saved_colors WHERE hex_value = ?', (hex_value.upper(),))
        finally:
            conn.close()

    @staticmethod
    def get_all_colors():
        """获取所有收藏的颜色，按时间倒序排列"""
        conn = db.get_connection()
        try:
            cursor = conn.execute('SELECT hex_value, name FROM saved_colors ORDER BY added_at DESC')
            # 返回列表: ['#FF0000', '#00FF00', ...]
            return [row['hex_value'] for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def is_color_saved(hex_value):
        """检查某个颜色是否已收藏"""
        conn = db.get_connection()
        try:
            cursor = conn.execute('SELECT 1 FROM saved_colors WHERE hex_value = ?', (hex_value.upper(),))
            return cursor.fetchone() is not None
        finally:
            conn.close()