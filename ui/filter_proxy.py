# G:\PYthon\AssetManager\ui\filter_proxy.py

from PyQt6.QtCore import QSortFilterProxyModel, Qt
from ui.data_model import AssetModel

class AssetFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.checked_tags = set()
        self.checked_ratings = set()
        self.checked_types = set()
        self.checked_colors = set()
        self.sort_mode = "name_asc" 

    def set_filter_conditions(self, tags, ratings, types, colors):
        self.checked_tags = set(tags)
        self.checked_ratings = set(ratings)
        self.checked_types = set(types)
        self.checked_colors = set(colors)
        self.invalidateFilter()

    def set_sort_mode(self, mode):
        self.sort_mode = mode
        self.invalidate()
        # 强制视图保持升序，具体的顺序逻辑我们在 lessThan 里控制
        self.sort(0, Qt.SortOrder.AscendingOrder)

    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()
        if not model: return True
        index = model.index(source_row, 0, source_parent)
        meta = model.data(index, AssetModel.ROLE_META_DATA)
        if not meta: return True

        if self.checked_types:
            raw_type = str(meta.get("type", "FILE")).upper()
            if "sub_folders" in meta or meta.get("type") == "FOLDER": raw_type = "FOLDER"
            if raw_type not in self.checked_types: return False

        if self.checked_ratings:
            rating = int(meta.get("rating", 0))
            if rating not in self.checked_ratings: return False

        if self.checked_colors:
            color = str(meta.get("color", "")).lower() or "none"
            if color not in self.checked_colors: return False

        if self.checked_tags:
            file_tags = meta.get("tags", [])
            if not (set(file_tags) & self.checked_tags): return False

        return True

    def lessThan(self, left, right):
        """
        自定义排序逻辑
        """
        model = self.sourceModel()
        l_meta = model.data(left, AssetModel.ROLE_META_DATA)
        r_meta = model.data(right, AssetModel.ROLE_META_DATA)
        
        if not l_meta or not r_meta:
            return super().lessThan(left, right)

        # === 优先级 1：置顶 (Pinned) ===
        # 核心修复：我们要让置顶项(True) 排在 非置顶项(False) 前面。
        # 在升序中，小在前。所以我们要让 置顶 < 非置顶。
        # 也就是 True 应该被视为 "0"，False 视为 "1"。
        # 所以我们比较 (not pinned)。
        l_pinned = bool(l_meta.get("pinned", False))
        r_pinned = bool(r_meta.get("pinned", False))

        if l_pinned != r_pinned:
            # 如果左边置顶(True)，not l_pinned = False(0)
            # 右边没置顶(False)，not r_pinned = True(1)
            # 0 < 1，返回 True。左边排前面。完美。
            return (not l_pinned) < (not r_pinned)

        # === 优先级 2：文件夹永远在文件前面 ===
        l_is_dir = (l_meta.get("type") == "FOLDER")
        r_is_dir = (r_meta.get("type") == "FOLDER")
        
        if l_is_dir != r_is_dir:
            # 同理，文件夹(True)要排在文件(False)前面
            # 文件夹(0) < 文件(1)
            return (not l_is_dir) < (not r_is_dir)

        # === 优先级 3：根据 sort_mode 比较 ===
        mode = self.sort_mode
        reverse = "_desc" in mode
        key = mode.replace("_asc", "").replace("_desc", "")

        val_l = 0
        val_r = 0

        if key == "name":
            val_l = model.data(left, Qt.ItemDataRole.DisplayRole).lower()
            val_r = model.data(right, Qt.ItemDataRole.DisplayRole).lower()
        elif key == "size":
            val_l = l_meta.get("size", 0)
            val_r = r_meta.get("size", 0)
        elif key == "date":
            val_l = l_meta.get("mtime", 0)
            val_r = r_meta.get("mtime", 0)
        elif key == "rating":
            val_l = l_meta.get("rating", 0)
            val_r = r_meta.get("rating", 0)

        if reverse:
            return val_l > val_r
        else:
            return val_l < val_r