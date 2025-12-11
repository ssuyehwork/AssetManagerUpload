import subprocess
import re
import sys

class WindowsDriveScanner:
    @staticmethod
    def get_physical_drives():
        """
        返回字典: { '物理序列号(UUID)': '当前盘符(如 C:)' }
        使用 wmic logicaldisk 获取卷序列号，这个是格式化时生成的唯一ID，
        比物理出厂序列号更适合作为分区的唯一标识。
        """
        if sys.platform != "win32":
            return {}

        drives = {}
        try:
            # 执行 CMD 命令获取盘符和序列号
            cmd = "wmic logicaldisk get Name, VolumeSerialNumber"
            # 隐藏 CMD 窗口 (防止弹黑框)
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            output = subprocess.check_output(cmd, startupinfo=startupinfo).decode('utf-8', errors='ignore')
            
            # 解析输出内容
            lines = output.strip().split('\n')
            for line in lines[1:]: # 跳过标题行
                parts = line.strip().split()
                if len(parts) >= 2:
                    serial = parts[-1].strip()  # 序列号
                    mount = parts[0].strip()    # 盘符 (C:)
                    
                    # 只有当两者都存在时才记录
                    if serial and mount:
                        drives[serial] = mount
        except Exception as e:
            print(f"硬件扫描错误: {e}")
            
        return drives