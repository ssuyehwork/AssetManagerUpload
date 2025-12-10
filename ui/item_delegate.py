# G:\PYthon\AssetManager\ui\item_delegate.py

from PyQt6.QtWidgets import QStyledItemDelegate, QStyle
from PyQt6.QtCore import Qt, QRect, QPoint, QSize, QRectF, QPointF, QEvent
from PyQt6.QtGui import (
    QColor, QPen, QBrush, QFont, QIcon, QPainterPath, 
    QPainter, QPixmap, QPolygonF
)
import math 

from ui.data_model import AssetModel
from services.rating_service import RatingService

class AssetGridDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.radius = 6.0
        self.star_size = 14
        self.clear_icon_size = 14
        self.star_spacing = 4
        self.star_path = self._get_star_path(self.star_size / 2)

        self.color_map = {
            "red": "#ff4444", "orange": "#ff8800", "yellow": "#ffd700", 
            "green": "#44ff44", "cyan": "#00bcd4", "blue": "#4444ff", 
            "purple": "#bd93f9", "none": "transparent"
        }

    def paint(self, painter, option, index):
        try:
            meta = index.data(AssetModel.ROLE_META_DATA)
            if not isinstance(meta, dict): meta = {}
            
            filename = index.data(Qt.ItemDataRole.DisplayRole)
            if filename is None: filename = "Unknown"
            
            icon = index.data(Qt.ItemDataRole.DecorationRole)
            
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

            rect = option.rect
            draw_rect = rect.adjusted(6, 6, -6, -6)

            is_selected = option.state & QStyle.StateFlag.State_Selected
            is_hover = option.state & QStyle.StateFlag.State_MouseOver
            
            bg_color = QColor("#2b2b2b")
            if is_selected: bg_color = QColor("#383838") 
            elif is_hover: bg_color = QColor("#333333")
            
            path = QPainterPath()
            path.addRoundedRect(QRectF(draw_rect), self.radius, self.radius)
            painter.fillPath(path, bg_color)
            
            if is_selected:
                painter.setPen(QPen(QColor("#0078d7"), 2))
                painter.drawPath(path)

            painter.setClipPath(path)

            bottom_reserved = 70 
            available_h = draw_rect.height() - bottom_reserved
            if available_h < 0: available_h = 0
            
            img_rect = QRect(draw_rect.left() + 8, draw_rect.top() + 8, 
                            draw_rect.width() - 16, available_h)
            
            if isinstance(icon, QIcon) and not icon.isNull():
                base_pixmap = icon.pixmap(QSize(256, 256))
                if not base_pixmap.isNull():
                    scaled = base_pixmap.scaled(
                        img_rect.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    x = img_rect.left() + (img_rect.width() - scaled.width()) // 2
                    y = img_rect.top() + (img_rect.height() - scaled.height()) // 2
                    painter.drawPixmap(x, y, scaled)

            ftype = str(meta.get("type", "")).upper()
            if not ftype or ftype == "FILE":
                ext = str(meta.get("ext", ""))
                ftype = ext.replace(".", "").upper() if ext else "FILE"
            
            tag_bg = "#555"
            if ftype == "FOLDER": tag_bg = "#000"
            elif ftype in ["JPG", "PNG", "GIF", "BMP", "PSD"]: tag_bg = "#0078d7"
            elif ftype in ["PY", "JS", "HTML", "JSON", "AHK"]: tag_bg = "#e0aa00"
            
            self.draw_tag(painter, img_rect.topLeft(), ftype, tag_bg)

            # === 【核心修复】绘制置顶 Emoji (📌) ===
            if meta.get("pinned", False):
                # 绘制在右上角
                pin_rect = QRect(img_rect.right() - 24, img_rect.top(), 28, 28)
                
                # 字体设置 (Emoji 需要较大字号)
                f = painter.font()
                f.setPointSize(16) 
                painter.setFont(f)
                
                # 直接绘制文本，让系统负责渲染 Emoji 颜色和阴影
                painter.drawText(pin_rect, Qt.AlignmentFlag.AlignCenter, "📌")

            if ftype == "FOLDER":
                try:
                    cnt = int(meta.get("file_count", 0))
                    if cnt > 0: self.draw_badge(painter, img_rect.bottomRight(), str(cnt))
                except: pass

            star_y = draw_rect.bottom() - 24 - 20 - 4
            star_rect = QRect(draw_rect.left(), star_y, draw_rect.width(), 20)
            try:
                rating = int(meta.get("rating", 0))
                self.draw_star_rating(painter, star_rect, rating)
            except: pass

            text_height = 24
            bottom_margin = 4
            name_y = draw_rect.bottom() - text_height - bottom_margin
            name_rect = QRect(draw_rect.left(), name_y, draw_rect.width(), text_height)
            
            user_color = meta.get("color")
            text_color = QColor("#cccccc")
            
            if user_color and isinstance(user_color, str) and user_color.strip():
                try:
                    hex_c = self.color_map.get(user_color, user_color)
                    if QColor.isValidColor(hex_c):
                        fill_c = QColor(hex_c)
                        fill_c.setAlpha(200)
                        
                        c_path = QPainterPath()
                        c_rect = name_rect.adjusted(4, 2, -4, -2)
                        c_path.addRoundedRect(QRectF(c_rect), 4.0, 4.0)
                        painter.fillPath(c_path, fill_c)
                        
                        brightness = (fill_c.red()*299 + fill_c.green()*587 + fill_c.blue()*114)/1000
                        text_color = QColor("black") if brightness > 128 else QColor("white")
                except: pass

            painter.setPen(text_color)
            font = painter.font()
            font.setBold(True)
            font.setPointSize(9)
            painter.setFont(font)
            
            metrics = painter.fontMetrics()
            text_draw_rect = name_rect.adjusted(8, 0, -8, 0)
            elided_text = metrics.elidedText(filename, Qt.TextElideMode.ElideMiddle, text_draw_rect.width())
            painter.drawText(text_draw_rect, Qt.AlignmentFlag.AlignCenter, elided_text)

            painter.restore()
            
        except Exception as e:
            print(f"Paint Error: {e}")
            painter.restore()

    def draw_star_rating(self, painter, rect, rating):
        total_w = self.clear_icon_size + self.star_spacing + 5 * (self.star_size + self.star_spacing)
        start_x = rect.center().x() - (total_w / 2)
        center_y = rect.center().y()

        painter.save()
        cx = start_x + self.clear_icon_size / 2
        cy = center_y
        r = self.clear_icon_size / 2 - 2
        painter.setPen(QPen(QColor(100, 100, 100), 1.5))
        painter.setBrush(Qt.GlobalColor.transparent)
        painter.drawEllipse(QPointF(cx, cy), r, r)
        painter.drawLine(QPointF(cx - r + 1, cy + r - 1), QPointF(cx + r - 1, cy - r + 1))
        
        star_start_x = start_x + self.clear_icon_size + self.star_spacing * 2
        for i in range(1, 6):
            sx = star_start_x + (i - 1) * (self.star_size + self.star_spacing) + self.star_size/2
            sy = center_y
            painter.translate(sx, sy)
            if i <= rating:
                painter.setBrush(QColor(255, 200, 0))
                painter.setPen(QPen(QColor(200, 150, 0), 1))
            else:
                painter.setBrush(Qt.GlobalColor.transparent)
                painter.setPen(QPen(QColor(80, 80, 80), 1))
            painter.drawPath(self.star_path)
            painter.translate(-sx, -sy)
        painter.restore()

    def _get_star_path(self, radius):
        path = QPainterPath()
        points = []
        angle_off = -math.pi / 2 
        for i in range(5):
            x_out = radius * math.cos(angle_off + i * 2 * math.pi / 5)
            y_out = radius * math.sin(angle_off + i * 2 * math.pi / 5)
            points.append(QPointF(x_out, y_out))
            x_in = (radius * 0.4) * math.cos(angle_off + (i + 0.5) * 2 * math.pi / 5)
            y_in = (radius * 0.4) * math.sin(angle_off + (i + 0.5) * 2 * math.pi / 5)
            points.append(QPointF(x_in, y_in))
        path.addPolygon(QPolygonF(points))
        return path

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseButtonRelease:
            rect = option.rect
            draw_rect = rect.adjusted(6, 6, -6, -6)
            star_y = draw_rect.bottom() - 24 - 20 - 4
            star_rect = QRect(draw_rect.left(), star_y, draw_rect.width(), 20)
            
            click_pos = event.position().toPoint()
            if star_rect.contains(click_pos):
                total_w = self.clear_icon_size + self.star_spacing + 5 * (self.star_size + self.star_spacing)
                start_x = star_rect.center().x() - (total_w / 2)
                rel_x = click_pos.x() - start_x
                new_rating = -1
                if 0 <= rel_x <= self.clear_icon_size: new_rating = 0
                else:
                    star_area_start = self.clear_icon_size + self.star_spacing
                    if rel_x > star_area_start:
                        star_slot_w = self.star_size + self.star_spacing
                        star_idx = int((rel_x - star_area_start) / star_slot_w) + 1
                        if 1 <= star_idx <= 5: new_rating = star_idx
                if new_rating != -1:
                    full_path = index.data(AssetModel.ROLE_FULL_PATH)
                    if full_path:
                        updated = RatingService.set_rating(full_path, new_rating)
                        if updated: model.setData(index, updated, AssetModel.ROLE_META_DATA)
                    return True
        return super().editorEvent(event, model, option, index)

    def draw_tag(self, painter, pos, text, bg_color):
        try:
            painter.save()
            font = painter.font(); font.setPointSize(8); font.setBold(True); painter.setFont(font)
            fm = painter.fontMetrics()
            w = fm.horizontalAdvance(text) + 12; h = fm.height() + 4
            rect = QRect(pos.x(), pos.y(), w, h)
            painter.setBrush(QColor(bg_color)); painter.setPen(Qt.PenStyle.NoPen)
            path = QPainterPath(); path.addRoundedRect(QRectF(rect), 4.0, 4.0); painter.drawPath(path)
            painter.setPen(Qt.GlobalColor.white); painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
            painter.restore()
        except: painter.restore()

    def draw_badge(self, painter, bottom_right_pos, text):
        try:
            size = 22; rect = QRect(bottom_right_pos.x() - size - 6, bottom_right_pos.y() - size - 40, size, size)
            painter.save(); painter.setBrush(QColor("#2ecc71")); painter.setPen(Qt.PenStyle.NoPen); painter.drawEllipse(rect)
            painter.setPen(Qt.GlobalColor.white); font = painter.font(); font.setPointSize(8); font.setBold(True)
            painter.setFont(font); painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text); painter.restore()
        except: painter.restore()