# G:\PYthon\AssetManager\services\asset_service.py

from core.db_manager import db
import os
import shutil
import ctypes
from ctypes import wintypes
import logging

class CTypesTrash:
    FO_DELETE = 3
    FOF_ALLOWUNDO = 64
    FOF_NOCONFIRMATION = 16
    FOF_SILENT = 4

    class SHFILEOPSTRUCTW(ctypes.Structure):
        _fields_ = [
            ("hwnd", wintypes.HWND),
            ("wFunc", wintypes.UINT),
            ("pFrom", wintypes.LPCWSTR),
            ("pTo", wintypes.LPCWSTR),
            ("fFlags", wintypes.WORD),
            ("fAnyOperationsAborted", wintypes.BOOL),
            ("hNameMappings", wintypes.LPVOID),
            ("lpszProgressTitle", wintypes.LPCWSTR),
        ]

    @staticmethod
    def move_to_trash(path):
        path = os.path.abspath(path)
        pFrom = path + "\0\0"
        fileop = CTypesTrash.SHFILEOPSTRUCTW()
        fileop.hwnd = 0
        fileop.wFunc = CTypesTrash.FO_DELETE
        fileop.pFrom = pFrom
        fileop.pTo = None
        fileop.fFlags = CTypesTrash.FOF_ALLOWUNDO | CTypesTrash.FOF_NOCONFIRMATION
        result = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(fileop))
        if result != 0:
            raise OSError(f"无法移动到回收站，错误代码: {result}")
        if fileop.fAnyOperationsAborted:
            raise OSError("操作被用户取消")

class AssetService:
    # === 【核心新增】根据路径获取/创建卷ID ===
    @staticmethod
    def get_volume_id_by_path(path):
        conn = db.get_connection()
        try:
            abs_path = os.path.abspath(path)
            drive, _ = os.path.splitdrive(abs_path)
            if not drive: return 1 # 默认 fallback
            
            drive = drive.upper()
            
            # 1. 尝试查找
            cur = conn.execute('SELECT id FROM volumes WHERE mount_point = ?', (drive,))
            row = cur.fetchone()
            if row: return row[0]
            
            # 2. 如果没找到，自动注册一个新的
            with conn:
                cur = conn.execute('INSERT INTO volumes (mount_point, is_active, name, serial_number) VALUES (?, 1, ?, ?)', 
                                   (drive, "自动发现硬盘", f"AUTO_{drive}"))
                return cur.lastrowid
        except Exception as e:
            logging.error(f"获取卷ID失败: {e}")
            return 1
        finally:
            conn.close()

    @staticmethod
    def sync_from_meta(folder_path, volume_id, meta_data):
        if not meta_data: return
        conn = db.get_connection()
        
        files_map = meta_data.get("files", {})
        sub_folders = meta_data.get("sub_folders", {})
        
        try:
            with conn:
                for filename, info in files_map.items():
                    full_path = os.path.join(folder_path, filename)
                    raw_ext = info.get("ext", "")
                    file_type = raw_ext.replace(".", "").upper() if raw_ext else "FILE"
                    cursor = conn.execute('''
                        INSERT OR REPLACE INTO assets 
                        (volume_id, name, path, type, size, rating, color)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (volume_id, filename, full_path, file_type, 
                          info.get("size", 0), info.get("rating", 0), info.get("color", "")))
                    asset_id = cursor.lastrowid
                    tags = info.get("tags", [])
                    if tags and asset_id:
                        AssetService._sync_tags_for_asset(conn, asset_id, tags)

                dir_items = sub_folders.items() if isinstance(sub_folders, dict) else []
                for folder_name, info in dir_items:
                    full_path = os.path.join(folder_path, folder_name)
                    rating = info.get("rating", 0) if isinstance(info, dict) else 0
                    color = info.get("color", "") if isinstance(info, dict) else ""
                    cursor = conn.execute('''
                        INSERT OR REPLACE INTO assets 
                        (volume_id, name, path, type, size, rating, color)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (volume_id, folder_name, full_path, "FOLDER", 
                          0, rating, color))
                    asset_id = cursor.lastrowid
                    tags = info.get("tags", []) if isinstance(info, dict) else []
                    if tags and asset_id:
                        AssetService._sync_tags_for_asset(conn, asset_id, tags)
        except Exception as e:
            logging.error(f"数据库同步失败: {folder_path} - {e}")
        finally:
            conn.close()

    @staticmethod
    def _sync_tags_for_asset(conn, asset_id, tags_list):
        conn.execute('DELETE FROM asset_tags WHERE asset_id = ?', (asset_id,))
        for tag in tags_list:
            tag = tag.strip()
            if not tag: continue
            conn.execute('INSERT OR IGNORE INTO tags (name) VALUES (?)', (tag,))
            cur = conn.execute('SELECT id FROM tags WHERE name = ?', (tag,))
            row = cur.fetchone()
            if row: conn.execute('INSERT INTO asset_tags (asset_id, tag_id) VALUES (?, ?)', (asset_id, row[0]))

    @staticmethod
    def update_tags(full_path, tags_list):
        conn = db.get_connection()
        try:
            with conn:
                cur = conn.execute('SELECT id FROM assets WHERE path = ?', (full_path,))
                row = cur.fetchone()
                if row: AssetService._sync_tags_for_asset(conn, row[0], tags_list)
        except Exception as e: logging.error(f"数据库标签更新失败: {e}")
        finally: conn.close()

    @staticmethod
    def search_assets(keyword=""):
        conn = db.get_connection()
        # 修复：确保 volumes 关联正确
        sql = '''
            SELECT DISTINCT a.id, a.name, a.path as full_path, v.name as drive_name, a.type, a.rating, a.size, a.color
            FROM assets a
            JOIN volumes v ON a.volume_id = v.id
            LEFT JOIN asset_tags at ON a.id = at.asset_id
            LEFT JOIN tags t ON at.tag_id = t.id
            WHERE v.is_active = 1 
        '''
        params = []
        if keyword:
            sql += " AND (a.name LIKE ? OR a.type LIKE ? OR t.name LIKE ?)"
            like_kw = f'%{keyword}%'
            params.append(like_kw)
            params.append(like_kw)
            params.append(like_kw)
        else:
            sql += " LIMIT 500"

        try:
            cursor = conn.execute(sql, params)
            results = [dict(row) for row in cursor.fetchall()]
            return results
        except Exception as e:
            logging.error(f"搜索失败: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def update_rating(full_path, rating):
        conn = db.get_connection()
        try:
            with conn: conn.execute('UPDATE assets SET rating = ? WHERE path = ?', (rating, full_path))
        except: pass
        finally: conn.close()

    @staticmethod
    def update_color(full_path, color_name):
        conn = db.get_connection()
        try:
            with conn: conn.execute('UPDATE assets SET color = ? WHERE path = ?', (color_name, full_path))
        except: pass
        finally: conn.close()

    @staticmethod
    def delete_file(full_path, permanently=False):
        if not os.path.exists(full_path): return False, "文件不存在"
        try:
            if permanently:
                if os.path.isdir(full_path): shutil.rmtree(full_path)
                else: os.remove(full_path)
            else:
                CTypesTrash.move_to_trash(full_path)
            AssetService.remove_from_db(full_path)
            return True, "成功"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def remove_from_db(full_path):
        conn = db.get_connection()
        try:
            with conn: conn.execute('DELETE FROM assets WHERE path = ?', (full_path,))
        except: pass
        finally: conn.close()