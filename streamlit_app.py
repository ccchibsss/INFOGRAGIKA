# ============================================================================
# 🚗 AUTO-PARTS HYBRID INFOGRAPHIC GENERATOR v8.0 - Streamlit Version
# ============================================================================

import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Union, Tuple, Any
from pathlib import Path
import warnings
import textwrap
import random
from enum import Enum
from dataclasses import dataclass
import json
import math
import io
import base64

warnings.filterwarnings('ignore')

# ============================================================================
# 🚗 КОНСТАНТЫ И НАСТРОЙКИ ДЛЯ АВТОЗАПЧАСТЕЙ
# ============================================================================

AUTO_ICONS = {
    'engine': '🔧', 'brake': '🛑', 'filter': '🧹', 'battery': '🔋',
    'tire': '🌀', 'oil': '🛢️', 'lamp': '💡', 'suspension': '⚙️',
    'exhaust': '📯', 'cooling': '❄️', 'electrical': '⚡', 'interior': '🚗',
    'body': '🛞', 'transmission': '⚙️', 'fuel': '⛽', 'ac': '🌬️',
    'new': '🆕', 'best': '👑', 'stock': '📦', 'discount': '🔥',
    'fast': '⚡', 'quality': '✅', 'original': '🏭', 'analog': '🔀',
    'delivery': '🚚', 'pickup': '📍', 'warranty': '🛡️', 'install': '🔧',
    'rating': '⭐', 'review': '💬', 'compatible': '🔗', 'oem': '🏷️',
    'calendar': '📅', 'clock': '⏰', 'location': '📍', 'phone': '📞',
    'car': '🚘', 'truck': '🚛', 'motorcycle': '🏍️', 'tools': '🛠️',
    'warning': '⚠️', 'info': 'ℹ️', 'check': '✓', 'certificate': '📜'
}

AUTO_CATEGORIES = {
    'Двигатель': ['Масло', 'Фильтры', 'Ремни', 'Свечи', 'ТНВД', 'Поршни', 'Клапаны'],
    'Тормоза': ['Колодки', 'Диски', 'Тормозная жидкость', 'Суппорта', 'Тормозные шланги'],
    'Подвеска': ['Амортизаторы', 'Сайлентблоки', 'Пружины', 'Рычаги', 'Шаровые опоры'],
    'Электрика': ['Аккумуляторы', 'Генераторы', 'Стартеры', 'Провода', 'Реле', 'Предохранители'],
    'Кузов': ['Фары', 'Зеркала', 'Щетки стеклоочистителя', 'Молдинги', 'Бампера', 'Капоты'],
    'Трансмиссия': ['Сцепление', 'Масло АКПП', 'ШРУСы', 'Подшипники', 'Карданные валы'],
    'Охлаждение': ['Радиаторы', 'Помпы', 'Термостаты', 'Патрубки', 'Вентиляторы'],
    'Выхлопная': ['Глушители', 'Коллекторы', 'Сажевые фильтры', 'Кислородные датчики']
}

AUTO_BRANDS = [
    'Bosch', 'Mann', 'Mahle', 'Valeo', 'Febi', 'Bilstein',
    'KYB', 'Monroe', 'Brembo', 'ATE', 'NGK', 'Denso',
    'VAG', 'BMW', 'Mercedes', 'Toyota', 'Honda', 'Nissan',
    'Lada', 'GAZ', 'УАЗ', 'Hyundai', 'Kia', 'Ford',
    'Gates', 'Osram', 'Varta', 'Lynx', 'Profit', 'AutoParts'
]

# ============================================================================
# 🎨 ТИПЫ ДАННЫХ И КОНФИГУРАЦИЯ
# ============================================================================

class TemplateStyle(Enum):
    AUTO_MODERN = "auto_modern"
    AUTO_PRO = "auto_pro"
    AUTO_BUDGET = "auto_budget"
    AUTO_PREMIUM = "auto_premium"
    AUTO_TECH = "auto_tech"
    AUTO_STOCK = "auto_stock"
    AUTO_LUXURY = "auto_luxury"

class ColorPalette:
    PALETTES = {
        TemplateStyle.AUTO_MODERN: {
            'primary': (41, 128, 185), 'secondary': (231, 76, 60),
            'accent': (52, 152, 219), 'background': (255, 255, 255),
            'card_bg': (245, 245, 245), 'text': (44, 62, 80),
            'highlight': (241, 196, 15), 'danger': (231, 76, 60),
            'success': (46, 204, 113), 'border': (220, 220, 220)
        },
        TemplateStyle.AUTO_PRO: {
            'primary': (30, 30, 30), 'secondary': (192, 57, 43),
            'accent': (52, 73, 94), 'background': (250, 250, 250),
            'card_bg': (255, 255, 255), 'text': (50, 50, 50),
            'highlight': (230, 126, 34), 'danger': (192, 57, 43),
            'success': (39, 174, 96), 'border': (200, 200, 200)
        },
        TemplateStyle.AUTO_PREMIUM: {
            'primary': (0, 0, 0), 'secondary': (218, 165, 32),
            'accent': (120, 120, 120), 'background': (255, 255, 255),
            'card_bg': (255, 250, 240), 'text': (40, 40, 40),
            'highlight': (218, 165, 32), 'danger': (160, 64, 0),
            'success': (46, 125, 50), 'border': (218, 165, 32)
        },
        TemplateStyle.AUTO_TECH: {
            'primary': (0, 100, 200), 'secondary': (0, 200, 255),
            'accent': (100, 100, 255), 'background': (15, 25, 40),
            'card_bg': (25, 35, 50), 'text': (220, 220, 255),
            'highlight': (0, 255, 200), 'danger': (255, 50, 100),
            'success': (0, 255, 150), 'border': (0, 150, 255)
        },
        TemplateStyle.AUTO_LUXURY: {
            'primary': (20, 20, 20), 'secondary': (184, 134, 11),
            'accent': (139, 69, 19), 'background': (248, 248, 255),
            'card_bg': (255, 255, 255), 'text': (30, 30, 30),
            'highlight': (184, 134, 11), 'danger': (139, 0, 0),
            'success': (34, 139, 34), 'border': (184, 134, 11)
        }
    }

@dataclass
class AutoPartData:
    name: str
    price: str
    old_price: Optional[str] = None
    brand: str = ""
    oem: str = ""
    category: str = ""
    car_model: str = ""
    year_from: str = ""
    year_to: str = ""
    stock: str = "В наличии"
    delivery: str = "1-3 дня"
    warranty: str = "12 месяцев"
    rating: float = 4.5
    reviews: int = 0
    compatibility: List[str] = None
    features: List[str] = None
    images: List[str] = None
    description: str = ""
    weight: str = ""
    dimensions: str = ""
    country: str = ""

    def __post_init__(self):
        if self.compatibility is None:
            self.compatibility = []
        if self.features is None:
            self.features = []
        if self.images is None:
            self.images = []
        if not self.oem:
            self.oem = self._generate_oem()
    
    def _generate_oem(self) -> str:
        letters = random.choice(['AB', 'CD', 'EF', 'GH', 'IJ'])
        numbers = f"{random.randint(1000, 9999):04d}"
        suffix = random.choice(['A', 'B', 'C', 'D', 'X'])
        return f"{letters}{numbers}{suffix}"

# ============================================================================
# 🎨 ТЕКСТОВЫЙ ПРОЦЕССОР
# ============================================================================

class AutoTextProcessor:
    def __init__(self, language: str = 'ru'):
        self.language = language
        self.icons = AUTO_ICONS
        
    def get_icon_for_category(self, category: str) -> str:
        category_lower = category.lower()
        icon_map = {
            'двигатель': '🔧', 'двига': '🔧', 'мотор': '🔧',
            'тормоз': '🛑', 'колодк': '🛑', 'диск': '🛑',
            'фильтр': '🧹', 'масл': '🛢️', 'смазк': '🛢️',
            'аккумулятор': '🔋', 'батаре': '🔋',
            'шина': '🌀', 'колес': '🌀', 'резин': '🌀',
            'фара': '💡', 'ламп': '💡', 'свет': '💡',
            'подвеск': '⚙️', 'амортизатор': '⚙️',
            'выхлоп': '📯', 'глушител': '📯',
            'охлажден': '❄️', 'радиатор': '❄️',
            'электрик': '⚡', 'провод': '⚡',
            'кузов': '🚗', 'двер': '🚗', 'капот': '🚗',
            'трансмиссия': '⚙️', 'сцеплен': '⚙️', 'коробк': '⚙️',
            'топливо': '⛽', 'бензин': '⛽', 'дизель': '⛽',
            'кондиционер': '🌬️', 'климат': '🌬️'
        }
        
        for key, icon in icon_map.items():
            if key in category_lower:
                return icon
        return '🔧'
    
    def format_price(self, price: str, currency: str = '₽') -> Dict:
        try:
            clean_price = re.sub(r'[^\d]', '', str(price))
            numeric_price = int(clean_price) if clean_price else 0
            formatted = f"{numeric_price:,}".replace(',', ' ')
            
            return {
                'formatted': f"{formatted}{currency}",
                'numeric': numeric_price,
                'currency': currency
            }
        except Exception as e:
            return {
                'formatted': f"0{currency}",
                'numeric': 0,
                'currency': currency
            }
    
    def create_compatibility_badge(self, car_models: List[str], max_models: int = 3) -> str:
        if not car_models:
            return "🚗 Совместимость уточняйте"
        
        models = car_models[:max_models]
        base_text = "🚗 " + ", ".join(models)
        
        if len(car_models) > max_models:
            base_text += f" +{len(car_models) - max_models}"
        
        return base_text
    
    def create_delivery_info(self, stock: str, delivery: str) -> Dict:
        stock_lower = stock.lower()
        
        if 'налич' in stock_lower or 'есть' in stock_lower or 'склад' in stock_lower:
            stock_icon = '📦'; stock_color = 'success'; stock_text = 'В наличии'
        elif 'под заказ' in stock_lower or 'заказ' in stock_lower:
            stock_icon = '📋'; stock_color = 'warning'; stock_text = 'Под заказ'
        else:
            stock_icon = '⏳'; stock_color = 'danger'; stock_text = 'Нет в наличии'
        
        delivery_days = 3
        delivery_match = re.search(r'(\d+)[\s\-]?(\d+)?', delivery)
        if delivery_match:
            if delivery_match.group(2):
                delivery_days = int(delivery_match.group(2))
            else:
                delivery_days = int(delivery_match.group(1))
        
        if delivery_days <= 1:
            delivery_icon = '⚡'; delivery_text = 'Сегодня-завтра'
        elif delivery_days <= 3:
            delivery_icon = '🚚'; delivery_text = '1-3 дня'
        else:
            delivery_icon = '📅'; delivery_text = f'{delivery_days} дней'
        
        return {
            'stock': {'icon': stock_icon, 'text': stock_text, 'color': stock_color},
            'delivery': {'icon': delivery_icon, 'text': delivery_text, 'days': delivery_days}
        }
    
    def create_features_list(self, features: List[str], max_features: int = 5) -> List[str]:
        formatted = []
        for feature in features[:max_features]:
            icon = self._get_feature_icon(feature)
            formatted.append(f"{icon} {feature}")
        
        placeholder_features = [
            "🔧 Легкая установка", "✅ Гарантия качества",
            "📦 Оригинальная упаковка", "🛡️ Официальная гарантия",
            "🏭 Проверенный производитель"
        ]
        
        while len(formatted) < 3:
            formatted.append(placeholder_features[len(formatted)])
        
        return formatted
    
    def _get_feature_icon(self, feature: str) -> str:
        feature_lower = feature.lower()
        
        if any(word in feature_lower for word in ['гарант', 'warrant']):
            return '🛡️'
        elif any(word in feature_lower for word in ['установк', 'монтаж', 'устан']):
            return '🔧'
        elif any(word in feature_lower for word in ['оригин', 'original', 'oem']):
            return '🏭'
        elif any(word in feature_lower for word in ['аналог', 'замен']):
            return '🔀'
        elif any(word in feature_lower for word in ['качеств', 'quality']):
            return '✅'
        elif any(word in feature_lower for word in ['произво', 'произв', 'brand']):
            return '🏷️'
        elif any(word in feature_lower for word in ['сертиф', 'сертификат']):
            return '📋'
        elif any(word in feature_lower for word in ['размер', 'разм']):
            return '📏'
        elif any(word in feature_lower for word in ['вес', 'weight']):
            return '⚖️'
        elif any(word in feature_lower for word in ['цвет', 'color']):
            return '🎨'
        elif any(word in feature_lower for word in ['материал', 'material']):
            return '🧱'
        
        return '✅'

# ============================================================================
# 🎨 УЛУЧШЕННЫЙ ГРАФИЧЕСКИЙ ГЕНЕРАТОР
# ============================================================================

class AutoGraphicsGenerator:
    @staticmethod
    def create_rounded_rect(draw: ImageDraw.ImageDraw,
                           position: Tuple[int, int],
                           size: Tuple[int, int],
                           radius: int,
                           fill: Optional[Tuple[int, int, int]] = None,
                           outline: Optional[Tuple[int, int, int]] = None,
                           width: int = 1) -> None:
        x, y = position
        width_rect, height_rect = size
        
        # Рисуем основную прямоугольную часть
        draw.rectangle([x + radius, y, x + width_rect - radius, y + height_rect],
                      fill=fill, outline=None)
        draw.rectangle([x, y + radius, x + width_rect, y + height_rect - radius],
                      fill=fill, outline=None)
        
        # Рисуем закругленные углы
        if fill:
            # Левый верхний
            draw.pieslice([x, y, x + radius * 2, y + radius * 2], 
                         180, 270, fill=fill, outline=None)
            # Правый верхний
            draw.pieslice([x + width_rect - radius * 2, y, x + width_rect, y + radius * 2], 
                         270, 360, fill=fill, outline=None)
            # Левый нижний
            draw.pieslice([x, y + height_rect - radius * 2, x + radius * 2, y + height_rect], 
                         90, 180, fill=fill, outline=None)
            # Правый нижний
            draw.pieslice([x + width_rect - radius * 2, y + height_rect - radius * 2, 
                         x + width_rect, y + height_rect], 
                         0, 90, fill=fill, outline=None)
        
        # Рисуем контур
        if outline:
            # Верхняя линия
            draw.line([(x + radius, y), (x + width_rect - radius, y)], 
                     fill=outline, width=width)
            # Нижняя линия
            draw.line([(x + radius, y + height_rect), (x + width_rect - radius, y + height_rect)], 
                     fill=outline, width=width)
            # Левая линия
            draw.line([(x, y + radius), (x, y + height_rect - radius)], 
                     fill=outline, width=width)
            # Правая линия
            draw.line([(x + width_rect, y + radius), (x + width_rect, y + height_rect - radius)], 
                     fill=outline, width=width)
            
            # Угловые дуги
            draw.arc([x, y, x + radius * 2, y + radius * 2], 180, 270, fill=outline)
            draw.arc([x + width_rect - radius * 2, y, x + width_rect, y + radius * 2], 
                    270, 360, fill=outline)
            draw.arc([x, y + height_rect - radius * 2, x + radius * 2, y + height_rect], 
                    90, 180, fill=outline)
            draw.arc([x + width_rect - radius * 2, y + height_rect - radius * 2, 
                     x + width_rect, y + height_rect], 0, 90, fill=outline)
    
    @staticmethod
    def create_price_badge(draw: ImageDraw.ImageDraw,
                          position: Tuple[int, int],
                          price_data: Dict,
                          colors: Dict) -> None:
        x, y = position
        
        # Создаем фон для ценника
        AutoGraphicsGenerator.create_rounded_rect(
            draw, (x, y), (280, 70), 15,
            fill=colors.get('primary', (41, 128, 185)),
            outline=colors.get('border', (200, 200, 200))
        )
        
        # Пытаемся загрузить шрифт
        try:
            font_large = ImageFont.truetype("arial.ttf", 28) if os.path.exists("arial.ttf") else ImageFont.load_default()
            font_small = ImageFont.truetype("arial.ttf", 16) if os.path.exists("arial.ttf") else ImageFont.load_default()
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Текущая цена
        price_text = price_data.get('current', '0 ₽')
        draw.text((x + 20, y + 15), price_text,
                 fill=(255, 255, 255), font=font_large)
        
        # Старая цена (если есть)
        if price_data.get('old'):
            draw.text((x + 20, y + 45), price_data['old'],
                     fill=(200, 200, 200), font=font_small)
    
    @staticmethod
    def create_stock_badge(draw: ImageDraw.ImageDraw,
                          position: Tuple[int, int],
                          stock_data: Dict,
                          colors: Dict) -> None:
        x, y = position
        
        # Выбираем цвет в зависимости от статуса
        if stock_data.get('color') == 'success':
            bg_color = colors.get('success', (46, 204, 113))
        elif stock_data.get('color') == 'warning':
            bg_color = colors.get('highlight', (241, 196, 15))
        else:
            bg_color = colors.get('danger', (231, 76, 60))
        
        # Создаем бейдж
        AutoGraphicsGenerator.create_rounded_rect(
            draw, (x, y), (180, 40), 10,
            fill=bg_color,
            outline=None
        )
        
        # Загружаем шрифт
        try:
            font = ImageFont.truetype("arial.ttf", 16) if os.path.exists("arial.ttf") else ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # Текст бейджа
        text = f"{stock_data.get('icon', '📦')} {stock_data.get('text', 'В наличии')}"
        draw.text((x + 10, y + 10), text,
                 fill=(255, 255, 255), font=font)

# ============================================================================
# 🎨 ГЕНЕРАТОР ПОДЛОЖЕК
# ============================================================================

class AutoBackgroundGenerator:
    def __init__(self):
        self.parts_patterns = {
            'engine': self._create_engine_pattern,
            'brake': self._create_brake_pattern,
            'wheel': self._create_wheel_pattern,
            'electric': self._create_electric_pattern,
            'suspension': self._create_suspension_pattern,
            'default': self._create_default_pattern
        }
    
    def create_background(self,
                         size: Tuple[int, int] = (1200, 800),
                         bg_type: str = 'gradient',
                         theme: str = 'auto_modern',
                         category: str = None) -> Image.Image:
        width, height = size
        
        if bg_type == 'gradient':
            return self._create_gradient_background(width, height, theme)
        elif bg_type == 'pattern':
            return self._create_pattern_background(width, height, category or 'default')
        elif bg_type == 'geometric':
            return self._create_geometric_background(width, height, theme)
        elif bg_type == 'texture':
            return self._create_texture_background(width, height)
        else:
            return self._create_gradient_background(width, height, theme)
    
    def _create_gradient_background(self,
                                   width: int,
                                   height: int,
                                   theme: str = 'auto_modern') -> Image.Image:
        # Цвета для разных тем
        if theme == 'auto_modern':
            colors = [(41, 128, 185), (52, 152, 219), (93, 173, 226)]
        elif theme == 'auto_pro':
            colors = [(30, 30, 30), (52, 73, 94), (44, 62, 80)]
        elif theme == 'auto_premium':
            colors = [(0, 0, 0), (50, 50, 50), (120, 120, 120)]
        elif theme == 'auto_tech':
            colors = [(15, 25, 40), (30, 45, 70), (50, 70, 100)]
        else:
            colors = [(41, 128, 185), (52, 152, 219), (26, 188, 156)]
        
        # Создаем изображение с градиентом
        image = Image.new('RGB', (width, height), colors[0])
        draw = ImageDraw.Draw(image)
        
        # Вертикальный градиент
        for i in range(height):
            ratio = i / height
            r = int(colors[0][0] * (1 - ratio) + colors[1][0] * ratio)
            g = int(colors[0][1] * (1 - ratio) + colors[1][1] * ratio)
            b = int(colors[0][2] * (1 - ratio) + colors[1][2] * ratio)
            draw.line([(0, i), (width, i)], fill=(r, g, b))
        
        # Горизонтальный градиент (оверлей)
        overlay = Image.new('RGB', (width, height), (0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        
        for i in range(width):
            ratio = i / width
            r = int(colors[1][0] * (1 - ratio) + colors[2][0] * ratio)
            g = int(colors[1][1] * (1 - ratio) + colors[2][1] * ratio)
            b = int(colors[1][2] * (1 - ratio) + colors[2][2] * ratio)
            draw_overlay.line([(i, 0), (i, height)], fill=(r, g, b))
        
        # Смешиваем градиенты
        image = Image.blend(image, overlay, alpha=0.5)
        
        # Добавляем текстуру
        image = self._add_texture_noise(image, intensity=3)
        
        return image
    
    def _create_pattern_background(self,
                                  width: int,
                                  height: int,
                                  category: str) -> Image.Image:
        pattern_func = self.parts_patterns.get(category, self.parts_patterns['default'])
        
        image = Image.new('RGB', (width, height), (245, 245, 245))
        draw = ImageDraw.Draw(image)
        
        pattern_func(draw, width, height)
        
        # Добавляем легкий градиент поверх паттерна
        overlay = self._create_gradient_background(width, height, 'auto_modern')
        overlay = overlay.convert('RGBA')
        
        # Устанавливаем прозрачность
        overlay_alpha = overlay.split()[3] if len(overlay.split()) > 3 else Image.new('L', overlay.size, 255)
        overlay_alpha = overlay_alpha.point(lambda p: int(p * 0.3))
        
        overlay_rgb = overlay.convert('RGB')
        overlay_final = Image.merge('RGBA', (overlay_rgb.split() + (overlay_alpha,)))
        
        image = image.convert('RGBA')
        image = Image.alpha_composite(image, overlay_final)
        
        return image.convert('RGB')
    
    def _create_engine_pattern(self, draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
        for x in range(0, width, 100):
            for y in range(0, height, 100):
                center_x = x + 50
                center_y = y + 50
                
                # Шестеренка
                draw.ellipse([center_x - 20, center_y - 20,
                            center_x + 20, center_y + 20],
                           fill=(220, 220, 220), outline=(180, 180, 180))
                
                # Зубья шестеренки
                for angle in range(0, 360, 30):
                    rad = angle * math.pi / 180
                    x1 = center_x + 25 * math.cos(rad)
                    y1 = center_y + 25 * math.sin(rad)
                    
                    draw.ellipse([x1 - 5, y1 - 5, x1 + 5, y1 + 5],
                               fill=(200, 200, 200))
    
    def _create_brake_pattern(self, draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
        for x in range(0, width, 120):
            for y in range(0, height, 120):
                # Тормозной диск
                draw.ellipse([x + 10, y + 10, x + 110, y + 110],
                           fill=(230, 230, 230), outline=(200, 200, 200))
                
                # Отверстия для крепления
                for i in range(6):
                    angle = i * 60
                    rad = angle * math.pi / 180
                    hole_x = x + 60 + 35 * math.cos(rad)
                    hole_y = y + 60 + 35 * math.sin(rad)
                    
                    draw.ellipse([hole_x - 8, hole_y - 8, hole_x + 8, hole_y + 8],
                               fill=(210, 210, 210))
    
    def _create_wheel_pattern(self, draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
        for x in range(0, width, 150):
            for y in range(0, height, 150):
                # Спицы колеса
                for i in range(8):
                    angle = i * 45
                    rad = angle * math.pi / 180
                    
                    for r in [30, 40, 50]:
                        x1 = x + 75 + r * math.cos(rad)
                        y1 = y + 75 + r * math.sin(rad)
                        
                        if i % 2 == 0:
                            draw.rectangle([x1 - 3, y1 - 10, x1 + 3, y1 + 10],
                                         fill=(220, 220, 220))
                        else:
                            draw.ellipse([x1 - 5, y1 - 5, x1 + 5, y1 + 5],
                                       fill=(220, 220, 220))
    
    def _create_electric_pattern(self, draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
        for x in range(0, width, 80):
            for y in range(0, height, 80):
                # Электрическая схема
                draw.rectangle([x + 10, y + 10, x + 70, y + 70],
                             fill=(230, 230, 230), outline=(200, 200, 200))
                
                # Диагонали
                draw.line([(x + 20, y + 20), (x + 60, y + 60)],
                         fill=(180, 180, 180), width=2)
                draw.line([(x + 60, y + 20), (x + 20, y + 60)],
                         fill=(180, 180, 180), width=2)
    
    def _create_suspension_pattern(self, draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
        for x in range(0, width, 100):
            for y in range(0, height, 100):
                # Амортизатор
                draw.rectangle([x + 30, y + 10, x + 70, y + 90],
                             fill=(230, 230, 230), outline=(200, 200, 200))
                
                # Пружины
                for i in range(5):
                    y_pos = y + 20 + i * 15
                    draw.ellipse([x + 25, y_pos, x + 75, y_pos + 10],
                               fill=(210, 210, 210), outline=(190, 190, 190))
    
    def _create_default_pattern(self, draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
        # Простая сетка
        for x in range(0, width, 50):
            draw.line([(x, 0), (x, height)], fill=(220, 220, 220), width=1)
        for y in range(0, height, 50):
            draw.line([(0, y), (width, y)], fill=(220, 220, 220), width=1)
        
        # Точки на пересечениях
        for x in range(25, width, 50):
            for y in range(25, height, 50):
                draw.ellipse([x - 2, y - 2, x + 2, y + 2],
                           fill=(200, 200, 200))
    
    def _create_geometric_background(self,
                                    width: int,
                                    height: int,
                                    theme: str) -> Image.Image:
        image = self._create_gradient_background(width, height, theme)
        
        # Цвета для геометрических фигур
        if theme == 'auto_modern':
            colors = [(41, 128, 185), (52, 152, 219), (26, 188, 156)]
        elif theme == 'auto_pro':
            colors = [(30, 30, 30), (52, 73, 94), (44, 62, 80)]
        else:
            colors = [(41, 128, 185), (231, 76, 60), (241, 196, 15)]
        
        # Создаем оверлей с геометрическими фигурами
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        for _ in range(25):
            color = random.choice(colors)
            shape_type = random.choice(['circle', 'rectangle', 'triangle'])
            
            x = random.randint(-50, width)
            y = random.randint(-50, height)
            size = random.randint(80, 300)
            alpha = random.randint(10, 40)
            color_with_alpha = color + (alpha,)
            
            if shape_type == 'circle':
                draw.ellipse([x, y, x + size, y + size],
                           fill=color_with_alpha)
            elif shape_type == 'rectangle':
                draw.rectangle([x, y, x + size, y + size//2],
                             fill=color_with_alpha)
            elif shape_type == 'triangle':
                draw.polygon([(x, y + size),
                            (x + size//2, y),
                            (x + size, y + size)],
                           fill=color_with_alpha)
        
        # Размываем оверлей
        overlay = overlay.filter(ImageFilter.GaussianBlur(radius=15))
        
        image = image.convert('RGBA')
        image = Image.alpha_composite(image, overlay)
        
        return image.convert('RGB')
    
    def _create_texture_background(self, width: int, height: int) -> Image.Image:
        image = self._create_gradient_background(width, height, 'auto_modern')
        image = image.convert('RGBA')
        
        # Добавляем шум
        noise = Image.effect_noise((width, height), 10)
        noise = noise.convert('RGBA')
        
        # Устанавливаем альфа-канал для шума
        noise_alpha = noise.split()[3] if len(noise.split()) > 3 else Image.new('L', noise.size, 255)
        noise_alpha = noise_alpha.point(lambda p: int(p * 0.1))
        
        noise_rgb = noise.convert('RGB')
        noise_final = Image.merge('RGBA', (noise_rgb.split() + (noise_alpha,)))
        
        image = Image.alpha_composite(image, noise_final)
        
        # Добавляем царапины
        scratches = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        scratches_draw = ImageDraw.Draw(scratches)
        
        for _ in range(random.randint(5, 15)):
            x1 = random.randint(0, width)
            y1 = random.randint(0, height)
            length = random.randint(20, 100)
            angle = random.uniform(0, math.pi)
            
            x2 = int(x1 + length * math.cos(angle))
            y2 = int(y1 + length * math.sin(angle))
            
            scratches_draw.line([(x1, y1), (x2, y2)],
                              fill=(255, 255, 255, random.randint(3, 8)),
                              width=random.randint(1, 2))
        
        image = Image.alpha_composite(image, scratches)
        
        return image.convert('RGB')
    
    def _add_texture_noise(self, image: Image.Image, intensity: int = 10) -> Image.Image:
        noise_layer = Image.effect_noise(image.size, intensity)
        
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        noise_layer = noise_layer.convert('RGBA')
        
        # Устанавливаем альфа-канал
        noise_alpha = noise_layer.split()[3] if len(noise_layer.split()) > 3 else Image.new('L', noise_layer.size, 255)
        noise_alpha = noise_alpha.point(lambda p: int(p * 0.25))
        
        noise_rgb = noise_layer.convert('RGB')
        noise_final = Image.merge('RGBA', (noise_rgb.split() + (noise_alpha,)))
        
        result = Image.alpha_composite(image, noise_final)
        
        return result.convert('RGB')
    
    def create_product_card_background(self,
                                      size: Tuple[int, int] = (800, 1200),
                                      style: str = 'auto_modern',
                                      with_logo_area: bool = True,
                                      with_text_area: bool = True) -> Image.Image:
        width, height = size
        
        background = self.create_background(size, 'gradient', style)
        
        if background.mode != 'RGBA':
            background = background.convert('RGBA')
        
        draw = ImageDraw.Draw(background)
        
        if with_logo_area:
            self._draw_logo_area(draw, width, height, style)
        
        self._draw_product_area(draw, width, height, style)
        
        if with_text_area:
            self._draw_text_area(draw, width, height, style)
        
        self._draw_corners(draw, width, height, style)
        
        return background.convert('RGB')
    
    def _draw_logo_area(self, draw: ImageDraw.ImageDraw, width: int, height: int, style: str) -> None:
        if style == 'auto_premium':
            color = (218, 165, 32)
        elif style == 'auto_tech':
            color = (0, 200, 255)
        else:
            color = (41, 128, 185)
        
        draw.rectangle([0, 0, width, 5], fill=color)
        draw.rectangle([0, 5, width, 30], fill=color)
        
        line_color = color
        draw.line([(0, 30), (width, 30)], fill=line_color, width=2)
    
    def _draw_product_area(self, draw: ImageDraw.ImageDraw, width: int, height: int, style: str) -> None:
        center_x, center_y = width // 2, height // 2
        rect_width, rect_height = 600, 400
        
        if style == 'auto_premium':
            bg_color = (255, 250, 240); border_color = (218, 165, 32)
        elif style == 'auto_pro':
            bg_color = (255, 255, 255); border_color = (200, 200, 200)
        else:
            bg_color = (250, 250, 250); border_color = (220, 220, 220)
        
        rect_x = center_x - rect_width // 2
        rect_y = center_y - rect_height // 2
        
        AutoGraphicsGenerator.create_rounded_rect(
            draw, (rect_x, rect_y), (rect_width, rect_height), 20,
            fill=bg_color,
            outline=border_color,
            width=2
        )
    
    def _draw_text_area(self, draw: ImageDraw.ImageDraw, width: int, height: int, style: str) -> Image.Image:
        text_area_height = 300
        
        if style == 'auto_tech':
            bg_color = (25, 35, 50, 180)
        else:
            bg_color = (255, 255, 255, 180)
        
        # Создаем полупрозрачный прямоугольник
        text_area = Image.new('RGBA', (width, text_area_height), bg_color)
        background_area = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        background_area.paste(text_area, (0, height - text_area_height))
        
        # Накладываем на основной фон
        temp_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        temp_img.paste(background, (0, 0))
        temp_img = Image.alpha_composite(temp_img, background_area)
        
        draw = ImageDraw.Draw(temp_img)
        
        draw.line([(0, height - text_area_height), (width, height - text_area_height)],
                 fill=(200, 200, 200, 150), width=1)
        
        return temp_img.convert('RGB')
    
    def _draw_corners(self, draw: ImageDraw.ImageDraw, width: int, height: int, style: str) -> None:
        corner_size = 20
        
        if style == 'auto_premium':
            corner_color = (218, 165, 32)
        elif style == 'auto_tech':
            corner_color = (0, 200, 255)
        else:
            corner_color = (41, 128, 185)
        
        draw.line([(0, corner_size), (corner_size, 0)],
                 fill=corner_color, width=3)
        draw.line([(width - corner_size, 0), (width, corner_size)],
                 fill=corner_color, width=3)
        draw.line([(0, height - corner_size), (corner_size, height)],
                 fill=corner_color, width=3)
        draw.line([(width - corner_size, height), (width, height - corner_size)],
                 fill=corner_color, width=3)

# ============================================================================
# 🎯 ГИБРИДНЫЙ МЕНЕДЖЕР ШАБЛОНОВ
# ============================================================================

class HybridTemplateManager:
    """Управление готовыми графическими шаблонами и их автоматической настройкой"""
    
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """Загрузка графических шаблонов из папки"""
        self.templates_dir.mkdir(exist_ok=True)
        template_files = list(self.templates_dir.glob("*.png")) + list(self.templates_dir.glob("*.jpg"))
        
        if not template_files:
            print(f"⚠️ В папке {self.templates_dir} нет шаблонов")
            print("   Создаю базовые шаблоны...")
            self._create_default_templates()
            template_files = list(self.templates_dir.glob("*.png"))
        
        for template_file in template_files:
            template_name = template_file.stem
            try:
                template_img = Image.open(template_file)
                self.templates[template_name] = {
                    'image': template_img,
                    'size': template_img.size,
                    'zones': self._detect_zones(template_img)
                }
                print(f"✅ Загружен шаблон: {template_name} ({template_img.size})")
            except Exception as e:
                print(f"❌ Ошибка загрузки шаблона {template_name}: {e}")
    
    def _create_default_templates(self):
        """Создание базовых шаблонов если их нет"""
        bg_generator = AutoBackgroundGenerator()
        
        # Шаблон для тормозов
        brake_bg = bg_generator.create_product_card_background(
            size=(800, 1200), style='auto_modern'
        )
        brake_bg.save(self.templates_dir / "brake_template.png")
        
        # Шаблон для двигателя
        engine_bg = bg_generator.create_product_card_background(
            size=(800, 1200), style='auto_pro'
        )
        engine_bg.save(self.templates_dir / "engine_template.png")
        
        # Шаблон для электроники
        electric_bg = bg_generator.create_product_card_background(
            size=(800, 1200), style='auto_tech'
        )
        electric_bg.save(self.templates_dir / "electrical_template.png")
        
        # Шаблон по умолчанию
        default_bg = bg_generator.create_product_card_background(
            size=(800, 1200), style='auto_premium'
        )
        default_bg.save(self.templates_dir / "default_template.png")
    
    def _detect_zones(self, template_img: Image.Image) -> Dict:
        """Автоматическое определение зон размещения контента"""
        width, height = template_img.size
        
        # Базовые зоны для автозапчастей
        zones = {
            'product_image': {'x1': width//4, 'y1': height//10, 'x2': 3*width//4, 'y2': height//3},
            'title': {'x1': width//10, 'y1': height//3 + 20, 'x2': 9*width//10, 'y2': height//3 + 80},
            'price': {'x1': width//10, 'y1': 2*height//3, 'x2': 3*width//10, 'y2': 2*height//3 + 60},
            'oem': {'x1': 4*width//10, 'y1': 2*height//3, 'x2': 6*width//10, 'y2': 2*height//3 + 40},
            'features': {'x1': width//10, 'y1': 2*height//3 + 100, 'x2': 9*width//10, 'y2': 8*height//9}
        }
        
        return zones
    
    def apply_template(self, template_name: str, part_data: Dict, user_texts: Dict = None) -> Image.Image:
        """Применение шаблона с данными"""
        if template_name not in self.templates:
            raise ValueError(f"Шаблон {template_name} не найден")
        
        template = self.templates[template_name]
        result = template['image'].copy()
        zones = template['zones']
        
        # Конвертируем в RGBA если нужно
        if result.mode != 'RGBA':
            result = result.convert('RGBA')
        
        draw = ImageDraw.Draw(result)
        
        # Заголовок
        if user_texts and 'title' in user_texts:
            title = user_texts['title']
        else:
            title = part_data.get('name', 'Название запчасти')
        
        self._draw_text_in_zone(draw, zones['title'], title, font_size=28)
        
        # Цена
        price = part_data.get('price', 'Цена не указана')
        self._draw_text_in_zone(draw, zones['price'], f"💰 {price} ₽", font_size=32, color=(231, 76, 60))
        
        # OEM номер
        if part_data.get('oem'):
            self._draw_text_in_zone(draw, zones['oem'], f"🔢 OEM: {part_data['oem']}", font_size=18)
        
        # Характеристики
        if user_texts and 'features' in user_texts:
            features = user_texts['features']
        else:
            features = part_data.get('features', ['Высокое качество', 'Гарантия производителя'])
        
        self._draw_features_list(draw, zones['features'], features)
        
        return result
    
    def _draw_text_in_zone(self, draw, zone: Dict, text: str, font_size: int = 24, 
                          color: Tuple = (0, 0, 0)):
        """Рисование текста в указанной зоне"""
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # Автоперенос текста
        max_chars = (zone['x2'] - zone['x1']) // (font_size // 2)
        lines = self._wrap_text(text, max_chars)
        
        line_height = int(font_size * 1.2)
        y = zone['y1']
        
        for line in lines:
            # Используем textbbox для измерения текста
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = zone['x1'] + (zone['x2'] - zone['x1'] - text_width) // 2
            draw.text((x, y), line, font=font, fill=color)
            y += line_height
    
    def _wrap_text(self, text: str, max_chars: int) -> List[str]:
        """Перенос текста"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            if len(' '.join(current_line + [word])) <= max_chars:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _draw_features_list(self, draw, zone: Dict, features: List[str]):
        """Рисование списка характеристик"""
        y = zone['y1']
        x = zone['x1']
        
        try:
            font = ImageFont.truetype("arial.ttf", 18)
        except:
            font = ImageFont.load_default()
        
        for feature in features[:5]:  # Ограничиваем 5 пунктами
            bullet_text = f"• {feature}"
            draw.text((x, y), bullet_text, fill=(50, 50, 50), font=font)
            y += 30

# ============================================================================
# 🎯 МОДУЛЬ РАБОТЫ С ВНЕШНИМИ ДАННЫМИ
# ============================================================================

class DataBridge:
    """Мост между Excel, пользовательским вводом и генерацией"""
    
    def __init__(self):
        self.text_processor = AutoTextProcessor()
    
    def prepare_hybrid_data(self, excel_path: str, manual_texts_path: str = None) -> List[Dict]:
        """Подготовка данных из Excel с возможностью ручного редактирования текстов"""
        try:
            df = pd.read_excel(excel_path)
        except Exception as e:
            print(f"❌ Ошибка чтения Excel файла: {e}")
            # Создаем демо данные
            df = self._create_demo_data()
        
        products = []
        
        # Загрузка ручных правок, если есть
        manual_texts = {}
        if manual_texts_path and os.path.exists(manual_texts_path):
            manual_texts = self._load_manual_texts(manual_texts_path)
        
        for idx, row in df.iterrows():
            # Автоматическое извлечение данных из Excel
            auto_data = self._extract_from_excel_row(row)
            
            # Добавление ручных правок, если есть
            product_id = auto_data.get('oem') or str(idx)
            if product_id in manual_texts:
                auto_data.update(manual_texts[product_id])
            
            products.append(auto_data)
        
        return products
    
    def _create_demo_data(self) -> pd.DataFrame:
        """Создание демо данных если Excel файл не найден"""
        data = {
            'Название': [
                'Тормозные колодки передние дисковые',
                'Масляный фильтр двигателя',
                'Аккумулятор 60Ач'
            ],
            'Цена': ['2890', '850', '5990'],
            'Бренд': ['Brembo', 'Mann', 'Varta'],
            'OEM': ['09.9762.80', 'HU925/3X', '574012078'],
            'Категория': ['Тормоза', 'Фильтры', 'Аккумуляторы'],
            'Характеристики': [
                'Керамический состав; Уменьшенная пыльность',
                'Высокая фильтрация; Прочный корпус',
                'Технология AGM; Не требует обслуживания'
            ]
        }
        return pd.DataFrame(data)
    
    def _extract_from_excel_row(self, row) -> Dict:
        """Извлечение данных из строки Excel"""
        data = {}
        
        for col in row.index:
            if pd.isna(row[col]):
                continue
                
            col_lower = str(col).lower()
            value = row[col]
            
            if any(word in col_lower for word in ['назван', 'name', 'товар', 'артикул']):
                data['name'] = str(value)
            elif any(word in col_lower for word in ['цена', 'price', 'стоимость']):
                data['price'] = str(value)
            elif any(word in col_lower for word in ['старая', 'old', 'бывшая', 'розничная']):
                data['old_price'] = str(value)
            elif any(word in col_lower for word in ['бренд', 'brand', 'производитель']):
                data['brand'] = str(value)
            elif any(word in col_lower for word in ['oem', 'номер', 'код', 'артикул']):
                data['oem'] = str(value)
            elif any(word in col_lower for word in ['категор', 'category', 'тип']):
                data['category'] = str(value)
            elif any(word in col_lower for word in ['характерист', 'feature', 'свойств', 'описан']):
                if isinstance(value, str):
                    data['features'] = [v.strip() for v in str(value).split(';') if v.strip()]
                elif isinstance(value, list):
                    data['features'] = value
        
        # Заполняем обязательные поля если их нет
        if 'name' not in data:
            data['name'] = f'Автозапчасть {row.name if hasattr(row, "name") else "unknown"}'
        if 'price' not in data:
            data['price'] = '1000'
        if 'brand' not in data:
            data['brand'] = random.choice(AUTO_BRANDS) if AUTO_BRANDS else 'Производитель'
        if 'category' not in data:
            data['category'] = random.choice(list(AUTO_CATEGORIES.keys()))
        if 'features' not in data:
            data['features'] = ['Высокое качество', 'Гарантия производителя']
        
        return data
    
    def _load_manual_texts(self, path: str) -> Dict:
        """Загрузка ручных правок из JSON"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def save_manual_texts(self, data: Dict, path: str):
        """Сохранение ручных правок в JSON"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

# ============================================================================
# 🎯 ГЛАВНЫЙ ГИБРИДНЫЙ ГЕНЕРАТОР
# ============================================================================

class HybridInfographicGenerator:
    """Основной класс для гибридной генерации"""
    
    def __init__(self, templates_dir: str = "templates"):
        self.template_manager = HybridTemplateManager(templates_dir)
        self.data_bridge = DataBridge()
        self.text_processor = AutoTextProcessor()
    
    def generate_single(self, product_data: Dict, template_name: str = None) -> Image.Image:
        """Генерация одной инфографики"""
        if not template_name:
            template_name = self._select_template(product_data)
        
        user_texts = {
            'title': self._optimize_title(product_data['name'], product_data.get('category', '')),
            'features': product_data.get('features', [])
        }
        
        result_image = self.template_manager.apply_template(
            template_name, product_data, user_texts
        )
        
        # Добавление автоматически сгенерированных элементов
        result_image = self._enhance_with_auto_elements(result_image, product_data)
        
        return result_image
    
    def generate_from_excel(self, excel_path: str, output_dir: str = "hybrid_output", 
                           use_templates: bool = True, manual_texts_path: str = None):
        """Основной метод генерации из Excel с гибридным подходом"""
        
        # 1. Подготовка данных
        print("📊 Загрузка данных из Excel...")
        products = self.data_bridge.prepare_hybrid_data(excel_path, manual_texts_path)
        
        # 2. Создание выходной папки
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        results = []
        
        # 3. Генерация для каждого продукта
        for idx, product in enumerate(products):
            try:
                print(f"\n🔄 Обработка товара {idx+1}/{len(products)}: {product.get('name', 'Без названия')}")
                
                if use_templates and self.template_manager.templates:
                    # Гибридный режим: шаблоны + автоматическая генерация
                    template_name = self._select_template(product)
                    output_file = output_path / f"template_{product.get('oem', idx)}_{template_name}.png"
                    
                    result_image = self.generate_single(product, template_name)
                    result_image.save(str(output_file), 'PNG', quality=95)
                    
                    print(f"  ✅ Шаблонный режим: {output_file}")
                    
                else:
                    # Полностью автоматический режим
                    output_file = output_path / f"auto_{product.get('oem', idx)}.png"
                    
                    # Создаем AutoPartData для совместимости
                    auto_part_data = AutoPartData(
                        name=product['name'],
                        price=product['price'],
                        old_price=product.get('old_price'),
                        brand=product['brand'],
                        oem=product['oem'],
                        category=product['category'],
                        features=product['features']
                    )
                    
                    # Используем упрощенный генератор
                    simple_gen = SimpleAutoPartsGenerator()
                    simple_gen.generate_simple_card(product, str(output_file))
                    print(f"  ✅ Автоматический режим: {output_file}")
                
                results.append({
                    'index': idx,
                    'product': product.get('name'),
                    'file': output_file.name,
                    'success': True
                })
                
            except Exception as e:
                print(f"  ❌ Ошибка: {e}")
                results.append({
                    'index': idx,
                    'error': str(e),
                    'success': False
                })
        
        # 4. Генерация отчета
        self._generate_report(results, output_path)
        
        return results
    
    def _select_template(self, product: Dict) -> str:
        """Выбор подходящего шаблона на основе категории товара"""
        category = product.get('category', '').lower()
        
        # Сопоставление категорий с шаблонами
        category_to_template = {
            'тормоз': 'brake_template',
            'двигатель': 'engine_template',
            'подвеск': 'suspension_template',
            'электрик': 'electrical_template',
            'кузов': 'body_template',
            'аккумулятор': 'battery_template',
            'фильтр': 'default_template'
        }
        
        for key, template in category_to_template.items():
            if key in category:
                if template in self.template_manager.templates:
                    return template
        
        # Возвращаем первый доступный шаблон
        if self.template_manager.templates:
            return list(self.template_manager.templates.keys())[0]
        
        return 'default_template'
    
    def _optimize_title(self, title: str, category: str) -> str:
        """Простая оптимизация заголовка"""
        optimizers = [
            lambda t: f"⚡ {t} ⚡ Лучшая цена!",
            lambda t: f"🔥 {t} 🔥 Со скидкой!",
            lambda t: f"👑 Премиум {t} | Гарантия",
            lambda t: f"🚗 {t} | Оригинал | Быстрая доставка"
        ]
        
        return random.choice(optimizers)(title)
    
    def _enhance_with_auto_elements(self, image: Image.Image, product: Dict) -> Image.Image:
        """Улучшение шаблонного изображения автоматическими элементами"""
        draw = ImageDraw.Draw(image)
        width, height = image.size
        
        # Добавление автоматически сгенерированных бейджей
        badges = [
            f"🚚 Доставка 1-3 дня",
            f"🛡️ Гарантия 12 мес",
            f"📦 В наличии"
        ]
        
        # Рисуем бейджи в правом верхнем углу
        y_offset = 20
        for badge in badges[:3]:
            self._draw_badge(draw, width - 200, y_offset, badge)
            y_offset += 40
        
        return image
    
    def _draw_badge(self, draw, x: int, y: int, text: str):
        """Рисование информационного бейджа"""
        badge_color = (52, 152, 219)
        
        # Оценка размера текста
        try:
            font = ImageFont.truetype("arial.ttf", 14)
        except:
            font = ImageFont.load_default()
        
        # Измеряем текст
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        badge_width = text_width + 20
        badge_height = text_height + 10
        
        # Рисуем закругленный прямоугольник для бейджа
        AutoGraphicsGenerator.create_rounded_rect(
            draw, (x, y), (badge_width, badge_height), 8,
            fill=badge_color,
            outline=(255, 255, 255)
        )
        
        # Текст в бейдже
        draw.text((x + 10, y + 5), text, fill=(255, 255, 255), font=font)
    
    def _generate_report(self, results: List, output_path: Path):
        """Генерация отчета о выполнении"""
        success_count = sum(1 for r in results if r['success'])
        total_count = len(results)
        
        report_text = f"""
{'='*60}
📊 ОТЧЕТ ПО ГИБРИДНОЙ ГЕНЕРАЦИИ ИНФОГРАФИКИ
{'='*60}

Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Всего товаров: {total_count}
Успешно обработано: {success_count}
Ошибок: {total_count - success_count}

УСПЕШНЫЕ ГЕНЕРАЦИИ:
{'-'*40}
"""
        
        for result in results:
            if result['success']:
                report_text += f"• {result.get('product', 'Без названия')} -> {result['file']}\n"
        
        if total_count - success_count > 0:
            report_text += f"""
ОШИБКИ:
{'-'*40}
"""
            for result in results:
                if not result['success']:
                    report_text += f"• Товар #{result['index']}: {result.get('error', 'Неизвестная ошибка')}\n"
        
        # Сохранение отчета
        report_file = output_path / "generation_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print(f"\n📊 Отчет сохранен: {report_file}")

# ============================================================================
# 🎯 ИНТЕРФЕЙС РУЧНОГО РЕДАКТИРОВАНИЯ
# ============================================================================

class ManualEditor:
    """Интерфейс для ручного редактирования текстов перед генерацией"""
    
    @staticmethod
    def create_editable_csv(df: pd.DataFrame, output_csv: str = "texts_to_edit.csv"):
        """Создание CSV файла для ручного редактирования текстов"""
        # Создаем структуру для редактирования
        editable_data = []
        
        for idx, row in df.iterrows():
            product_id = row.get('OEM') if 'OEM' in row.columns else f"product_{idx}"
            
            # Извлекаем характеристики
            features = []
            if 'Характеристики' in row:
                features_text = str(row['Характеристики'])
                if ';' in features_text:
                    features = [f.strip() for f in features_text.split(';') if f.strip()]
                else:
                    features = [features_text]
            
            editable_data.append({
                'product_id': product_id,
                'original_title': row.get('Название', '') if 'Название' in row else row.get('name', ''),
                'edited_title': '',
                'original_features': '; '.join(features),
                'edited_features': '',
                'additional_text': ''
            })
        
        editable_df = pd.DataFrame(editable_data)
        editable_df.to_csv(output_csv, index=False, encoding='utf-8')
        
        return output_csv
    
    @staticmethod
    def convert_csv_to_json(csv_path: str, json_path: str = "manual_texts.json"):
        """Конвертация отредактированного CSV в JSON для генератора"""
        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
        except:
            print("❌ Не удалось прочитать CSV файл")
            return None
        
        manual_texts = {}
        
        for _, row in df.iterrows():
            product_id = row['product_id']
            
            # Только если есть редактирования
            if pd.notna(row['edited_title']) and str(row['edited_title']).strip():
                manual_texts[product_id] = {
                    'title': str(row['edited_title']).strip()
                }
                
                if pd.notna(row['edited_features']) and str(row['edited_features']).strip():
                    features = [f.strip() for f in str(row['edited_features']).split(';') if f.strip()]
                    if features:
                        manual_texts[product_id]['features'] = features
        
        # Сохранение в JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(manual_texts, f, ensure_ascii=False, indent=2)
        
        return json_path

# ============================================================================
# 🎯 ОСНОВНОЙ ГЕНЕРАТОР (УПРОЩЕННЫЙ ДЛЯ ГИБРИДНОГО ПОДХОДА)
# ============================================================================

class SimpleAutoPartsGenerator:
    """Упрощенный генератор для гибридного подхода"""
    
    def __init__(self, style: str = 'auto_modern'):
        self.style = style
        self.text_processor = AutoTextProcessor()
        self.graphics = AutoGraphicsGenerator()
        
    def generate_simple_card(self, part_data: Dict, output_path: str = None) -> Image.Image:
        """Создание простой карточки товара"""
        width, height = 800, 1200
        
        # Создаем фоновое изображение
        bg_generator = AutoBackgroundGenerator()
        image = bg_generator.create_product_card_background((width, height), self.style)
        
        draw = ImageDraw.Draw(image)
        
        # Заголовок
        title = part_data.get('name', 'Название товара')
        self._draw_title(draw, title, width, height)
        
        # Цена
        price = part_data.get('price', '0')
        self._draw_price(draw, price, part_data.get('old_price'), width, height)
        
        # Бренд и OEM
        brand = part_data.get('brand', '')
        oem = part_data.get('oem', '')
        self._draw_brand_oem(draw, brand, oem, width, height)
        
        # Характеристики
        features = part_data.get('features', [])
        self._draw_features(draw, features, width, height)
        
        # Сохраняем если указан путь
        if output_path:
            image.save(output_path, 'PNG', quality=95)
        
        return image
    
    def _draw_title(self, draw, title: str, width: int, height: int):
        """Рисование заголовка"""
        try:
            font = ImageFont.truetype("arial.ttf", 28)
        except:
            font = ImageFont.load_default()
        
        # Переносим текст
        lines = []
        words = title.split()
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] < width - 100:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Рисуем линии
        y = height // 4
        for line in lines[:3]:  # Ограничиваем 3 строками
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            draw.text((x, y), line, fill=(0, 0, 0), font=font)
            y += 40
    
    def _draw_price(self, draw, price: str, old_price: str, width: int, height: int):
        """Рисование цены"""
        try:
            font_large = ImageFont.truetype("arial.ttf", 36)
            font_small = ImageFont.truetype("arial.ttf", 20)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Текущая цена
        price_text = f"{price} ₽"
        bbox = draw.textbbox((0, 0), price_text, font=font_large)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        y = height // 2
        
        draw.text((x, y), price_text, fill=(231, 76, 60), font=font_large)
        
        # Старая цена (если есть)
        if old_price:
            old_price_text = f"{old_price} ₽"
            bbox = draw.textbbox((0, 0), old_price_text, font=font_small)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            
            # Зачеркнутая цена
            draw.text((x, y + 50), old_price_text, fill=(150, 150, 150), font=font_small)
            draw.line([(x, y + 65), (x + text_width, y + 65)], fill=(150, 150, 150), width=2)
    
    def _draw_brand_oem(self, draw, brand: str, oem: str, width: int, height: int):
        """Рисование бренда и OEM"""
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        y = height // 2 + 120
        
        if brand:
            brand_text = f"🏷️ {brand}"
            bbox = draw.textbbox((0, 0), brand_text, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            draw.text((x, y), brand_text, fill=(52, 152, 219), font=font)
            y += 40
        
        if oem:
            oem_text = f"🔢 OEM: {oem}"
            bbox = draw.textbbox((0, 0), oem_text, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            draw.text((x, y), oem_text, fill=(100, 100, 100), font=font)
    
    def _draw_features(self, draw, features: List[str], width: int, height: int):
        """Рисование характеристик"""
        try:
            font = ImageFont.truetype("arial.ttf", 18)
        except:
            font = ImageFont.load_default()
        
        y = height // 2 + 220
        x = width // 4
        
        for feature in features[:5]:  # Ограничиваем 5 пунктами
            feature_text = f"✓ {feature}"
            draw.text((x, y), feature_text, fill=(50, 50, 50), font=font)
            y += 35

# ============================================================================
# 🎯 ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ STREAMLIT
# ============================================================================

def create_demo_data():
    """Создание демо данных"""
    demo_data = {
        'Название': [
            'Тормозные колодки передние дисковые Brembo',
            'Масляный фильтр двигателя Mann',
            'Аккумулятор Varta Silver Dynamic 60Ah'
        ],
        'Цена': ['2890', '850', '5990'],
        'Старая цена': ['3290', '', '6500'],
        'Бренд': ['Brembo', 'Mann', 'Varta'],
        'OEM': ['09.9762.80', 'HU925/3X', '574012078'],
        'Категория': ['Тормоза', 'Фильтры', 'Аккумуляторы'],
        'Характеристики': [
            'Керамический состав; Уменьшенная пыльность; Долгий срок службы',
            'Высокая фильтрация; Прочный корпус; Легкая установка',
            'Технология AGM; Не требует обслуживания; Пусковой ток 540А'
        ],
        'Наличие': ['В наличии', 'Под заказ', 'В наличии'],
        'Доставка': ['1-2 дня', '3-5 дней', '1 день']
    }
    
    return pd.DataFrame(demo_data)

def get_image_download_link(img: Image.Image, filename: str = "infographic.png", caption: str = "Скачать изображение"):
    """Генерация ссылки для скачивания изображения"""
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    href = f'<a href="data:file/png;base64,{img_str}" download="{filename}">{caption}</a>'
    return href

def save_uploaded_file(uploaded_file, folder: str = "uploads"):
    """Сохранение загруженного файла"""
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, uploaded_file.name)
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path

# ============================================================================
# 🎯 STREAMLIT ИНТЕРФЕЙС
# ============================================================================

def main():
    st.set_page_config(
        page_title="Auto-Parts Infographic Generator",
        page_icon="🚗",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Стили CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #3498db;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #3498db;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #28a745;
        margin-bottom: 1rem;
    }
    .product-card {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Заголовок
    st.markdown('<h1 class="main-header">🚗 Auto-Parts Hybrid Infographic Generator v8.0</h1>', unsafe_allow_html=True)
    st.markdown('<div class="info-box">🎯 Гибридный подход: Шаблоны + Автоматическая сборка. Создавайте профессиональные инфографики для автозапчастей за секунды!</div>', unsafe_allow_html=True)
    
    # Сайдбар
    with st.sidebar:
        st.header("⚙️ Настройки")
        
        mode = st.radio(
            "Режим работы:",
            ["📁 Обработка Excel файла", "✏️ Ручное создание", "🔄 Пакетная обработка"]
        )
        
        st.markdown("---")
        st.header("🎨 Стиль инфографики")
        
        style = st.selectbox(
            "Выберите стиль:",
            ["auto_modern", "auto_pro", "auto_premium", "auto_tech", "auto_luxury"]
        )
        
        use_templates = st.checkbox("Использовать графические шаблоны", value=True)
        
        if use_templates:
            templates_dir = "templates"
            template_files = list(Path(templates_dir).glob("*.png")) + list(Path(templates_dir).glob("*.jpg"))
            
            if template_files:
                template_names = [f.stem for f in template_files]
                selected_template = st.selectbox("Выберите шаблон:", template_names)
            else:
                st.warning("Шаблоны не найдены. Создайте базовые шаблоны.")
                if st.button("Создать базовые шаблоны"):
                    bg_generator = AutoBackgroundGenerator()
                    styles = ['auto_modern', 'auto_pro', 'auto_premium', 'auto_tech']
                    for s in styles:
                        template = bg_generator.create_product_card_background(
                            size=(800, 1200), style=s
                        )
                        Path(templates_dir).mkdir(exist_ok=True)
                        template.save(f"{templates_dir}/{s}_template.png")
                    st.success("Базовые шаблоны созданы!")
        
        st.markdown("---")
        st.header("📦 Экспорт")
        
        export_format = st.radio(
            "Формат экспорта:",
            ["PNG (рекомендуется)", "JPG"]
        )
        
        export_quality = st.slider("Качество изображения:", 50, 100, 95)
    
    # Основной контент
    if mode == "📁 Обработка Excel файла":
        st.markdown('<h2 class="sub-header">📊 Загрузка Excel файла</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            uploaded_file = st.file_uploader("Загрузите Excel файл с данными", type=['xlsx', 'xls'])
            
            if uploaded_file:
                file_path = save_uploaded_file(uploaded_file)
                st.success(f"Файл загружен: {uploaded_file.name}")
                
                # Чтение данных
                try:
                    df = pd.read_excel(file_path)
                    st.dataframe(df.head(), use_container_width=True)
                    
                    # Показываем статистику
                    st.info(f"Загружено {len(df)} товаров")
                    
                except Exception as e:
                    st.error(f"Ошибка чтения файла: {e}")
                    st.info("Используем демо данные")
                    df = create_demo_data()
                    st.dataframe(df, use_container_width=True)
            else:
                st.info("Загрузите Excel файл или используйте демо данные")
                if st.button("Использовать демо данные"):
                    df = create_demo_data()
                    st.dataframe(df, use_container_width=True)
        
        with col2:
            if 'df' in locals():
                st.markdown('<h3 class="sub-header">⚙️ Настройка обработки</h3>', unsafe_allow_html=True)
                
                # Выбор режима обработки
                processing_mode = st.radio(
                    "Режим обработки:",
                    ["🎨 Использовать шаблоны", "⚡ Быстрая генерация", "✏️ Ручное редактирование текстов"]
                )
                
                output_dir = st.text_input("Папка для результатов:", value="output_infographics")
                
                if st.button("🚀 Начать генерацию", type="primary", use_container_width=True):
                    with st.spinner("Генерация инфографик..."):
                        try:
                            generator = HybridInfographicGenerator("templates")
                            
                            if processing_mode == "✏️ Ручное редактирование текстов":
                                # Создаем CSV для редактирования
                                csv_file = "editable_texts.csv"
                                ManualEditor.create_editable_csv(df, csv_file)
                                
                                st.download_button(
                                    label="📥 Скачать CSV для редактирования",
                                    data=pd.read_csv(csv_file).to_csv(index=False).encode('utf-8'),
                                    file_name="editable_texts.csv",
                                    mime="text/csv"
                                )
                                
                                st.info("Отредактируйте CSV файл и загрузите его обратно")
                                edited_csv = st.file_uploader("Загрузите отредактированный CSV", type=['csv'])
                                
                                if edited_csv:
                                    edited_path = save_uploaded_file(edited_csv, "edited")
                                    json_file = ManualEditor.convert_csv_to_json(edited_path)
                                    
                                    results = generator.generate_from_excel(
                                        file_path,
                                        output_dir=output_dir,
                                        use_templates=(processing_mode != "⚡ Быстрая генерация"),
                                        manual_texts_path=json_file
                                    )
                            else:
                                results = generator.generate_from_excel(
                                    file_path,
                                    output_dir=output_dir,
                                    use_templates=(processing_mode != "⚡ Быстрая генерация")
                                )
                            
                            # Показываем результаты
                            success_count = sum(1 for r in results if r['success'])
                            st.success(f"✅ Успешно создано: {success_count} инфографик")
                            st.info(f"📁 Результаты сохранены в папке: {output_dir}/")
                            
                            # Показываем превью
                            st.markdown('<h3 class="sub-header">📸 Превью результатов</h3>', unsafe_allow_html=True)
                            
                            # Загружаем первые 3 изображения для показа
                            output_files = list(Path(output_dir).glob("*.png"))
                            if output_files:
                                cols = st.columns(min(3, len(output_files)))
                                for idx, file in enumerate(output_files[:3]):
                                    with cols[idx]:
                                        img = Image.open(file)
                                        st.image(img, caption=file.name, use_column_width=True)
                                        st.markdown(get_image_download_link(img, file.name, "📥 Скачать"), unsafe_allow_html=True)
                            
                        except Exception as e:
                            st.error(f"Ошибка при генерации: {e}")
    
    elif mode == "✏️ Ручное создание":
        st.markdown('<h2 class="sub-header">✏️ Создание инфографики вручную</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            
            # Поля для ввода данных
            product_name = st.text_input("Название товара:", value="Тормозные колодки передние")
            
            col_price1, col_price2 = st.columns(2)
            with col_price1:
                price = st.text_input("Цена:", value="2890")
            with col_price2:
                old_price = st.text_input("Старая цена (опционально):", value="3290")
            
            brand = st.text_input("Бренд:", value="Brembo")
            oem = st.text_input("OEM номер:", value="09.9762.80")
            category = st.selectbox("Категория:", list(AUTO_CATEGORIES.keys()))
            
            # Характеристики
            st.markdown("**Характеристики:**")
            features = []
            for i in range(5):
                feature = st.text_input(f"Характеристика {i+1}:", value=["Керамический состав", "Уменьшенная пыльность", "Долгий срок службы", "", ""][i])
                if feature:
                    features.append(feature)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            if st.button("🔄 Сгенерировать инфографику", type="primary", use_container_width=True):
                with st.spinner("Создаю инфографику..."):
                    try:
                        # Создаем данные продукта
                        product_data = {
                            'name': product_name,
                            'price': price,
                            'old_price': old_price if old_price else None,
                            'brand': brand,
                            'oem': oem,
                            'category': category,
                            'features': features
                        }
                        
                        # Выбираем генератор
                        if use_templates:
                            generator = HybridInfographicGenerator("templates")
                            template_name = selected_template if 'selected_template' in locals() else 'default_template'
                            result_img = generator.generate_single(product_data, template_name)
                        else:
                            generator = SimpleAutoPartsGenerator(style)
                            result_img = generator.generate_simple_card(product_data)
                        
                        # Показываем результат
                        st.markdown('<div class="success-box">✅ Инфографика создана!</div>', unsafe_allow_html=True)
                        st.image(result_img, use_column_width=True)
                        
                        # Кнопка скачивания
                        st.markdown(get_image_download_link(result_img, f"infographic_{oem}.png", "📥 Скачать инфографику"), unsafe_allow_html=True)
                        
                        # Сохранение
                        if st.button("💾 Сохранить в папку"):
                            output_dir = "manual_output"
                            Path(output_dir).mkdir(exist_ok=True)
                            output_path = f"{output_dir}/{product_name[:20]}_{oem}.png"
                            result_img.save(output_path, "PNG", quality=export_quality)
                            st.success(f"Сохранено: {output_path}")
                    
                    except Exception as e:
                        st.error(f"Ошибка при генерации: {e}")
    
    elif mode == "🔄 Пакетная обработка":
        st.markdown('<h2 class="sub-header">📁 Пакетная обработка файлов</h2>', unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader(
            "Загрузите несколько Excel файлов",
            type=['xlsx', 'xls'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            st.success(f"Загружено файлов: {len(uploaded_files)}")
            
            if st.button("🚀 Начать пакетную обработку", type="primary", use_container_width=True):
                with st.spinner("Обрабатываю файлы..."):
                    all_results = []
                    
                    for uploaded_file in uploaded_files:
                        try:
                            file_path = save_uploaded_file(uploaded_file, "batch_uploads")
                            output_dir = f"batch_output_{uploaded_file.name.split('.')[0]}"
                            
                            generator = HybridInfographicGenerator("templates")
                            results = generator.generate_from_excel(
                                file_path,
                                output_dir=output_dir,
                                use_templates=use_templates
                            )
                            
                            success_count = sum(1 for r in results if r['success'])
                            all_results.append({
                                'file': uploaded_file.name,
                                'total': len(results),
                                'success': success_count,
                                'output_dir': output_dir
                            })
                            
                        except Exception as e:
                            st.error(f"Ошибка обработки {uploaded_file.name}: {e}")
                    
                    # Сводный отчет
                    st.markdown('<div class="success-box">📊 Сводный отчет по пакетной обработке</div>', unsafe_allow_html=True)
                    
                    total_files = len(all_results)
                    total_products = sum(r.get('total', 0) for r in all_results)
                    total_success = sum(r.get('success', 0) for r in all_results)
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("📁 Файлов", total_files)
                    col2.metric("📊 Товаров", total_products)
                    col3.metric("✅ Успешно", total_success)
                    
                    st.markdown("**Папки с результатами:**")
                    for result in all_results:
                        st.write(f"• **{result['output_dir']}/** - {result['file']} ({result['success']}/{result['total']})")
        
        else:
            st.info("Загрузите Excel файлы для пакетной обработки")
    
    # Информация о системе
    with st.expander("ℹ️ О программе"):
        st.markdown("""
        **Auto-Parts Hybrid Infographic Generator v8.0**
        
        Возможности:
        - 📊 Загрузка данных из Excel
        - 🎨 Гибридный подход: шаблоны + автоматическая генерация
        - ✏️ Ручное редактирование текстов
        - 📁 Пакетная обработка
        - 🚀 Быстрая генерация инфографик
        
        Поддерживаемые форматы:
        - Вход: Excel (.xlsx, .xls)
        - Выход: PNG, JPG
        
        Требования:
        - pandas
        - Pillow (PIL)
        - openpyxl
        """)
        
        # Проверка библиотек
        st.markdown("**Проверка установленных библиотек:**")
        col1, col2, col3 = st.columns(3)
        
        try:
            import pandas
            col1.success("✅ pandas")
        except:
            col1.error("❌ pandas")
        
        try:
            from PIL import Image
            col2.success("✅ Pillow")
        except:
            col2.error("❌ Pillow")
        
        try:
            import openpyxl
            col3.success("✅ openpyxl")
        except:
            col3.error("❌ openpyxl")

# ============================================================================
# 🎯 ТОЧКА ВХОДА
# ============================================================================

if __name__ == "__main__":
    main()
