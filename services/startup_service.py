from core.db_manager import db
from core.drive_scanner import WindowsDriveScanner

class StartupService:
    @staticmethod
    def sync_drives():
        """
        核心逻辑：
        1. 扫描当前 Windows 挂载的硬盘。
        2. 将数据库所有硬盘设为 '离线'。
        3. 匹配上的硬盘设为 '在线' 并更新盘符。
        """
        print("正在进行沉浸式硬件同步...")
        
        # 1. 获取物理数据
        current_map = WindowsDriveScanner.get_physical_drives() 
        # 结果示例: {'A1B2-C3D4': 'E:', 'X9Y8-Z7W6': 'F:'}

        conn = db.get_connection()
        with conn:
            # 2. 重置状态：先假设所有硬盘都拔了
            conn.execute("UPDATE volumes SET is_active = 0")

            # 3. 激活存在的硬盘
            for serial, mount_point in current_map.items():
                # 尝试更新现有记录
                cursor = conn.execute('''
                    UPDATE volumes 
                    SET mount_point = ?, is_active = 1 
                    WHERE serial_number = ?
                ''', (mount_point, serial))

                # 如果这是个新硬盘（数据库里没记录），则自动注册
                if cursor.rowcount == 0:
                    conn.execute('''
                        INSERT INTO volumes (serial_number, mount_point, is_active, name)
                        VALUES (?, ?, 1, '新发现硬盘')
                    ''', (serial, mount_point))
                    print(f"  [+] 新硬盘注册: {mount_point} ({serial})")
                else:
                    print(f"  [v] 硬盘已激活: {mount_point} ({serial})")
        
        conn.close()
        print("同步完成。系统进入沉浸模式。")