# ============================================================================
# 🚗 AUTO-PARTS MARKETPLACE INFOGRAPHIC GENERATOR
# Система генерации инфографики в стиле карточек автозапчастей
# Версия 5.0 - с поддержкой профессиональных подложек и визуальных эффектов
# ============================================================================

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

warnings.filterwarnings('ignore')

# ============================================================================
# 🚗 КОНСТАНТЫ И НАСТРОЙКИ ДЛЯ АВТОЗАПЧАСТЕЙ
# ============================================================================

# Иконки для автозапчастей
AUTO_ICONS = {
    'engine': '🔧', 'brake': '🛑', 'filter': '🧹', 'battery': '🔋',
    'tire': '🌀', 'oil': '🛢️', 'lamp': '💡', 'suspension': '⚙️',
    'exhaust': '📯', 'cooling': '❄️', 'electrical': '⚡', 'interior': '🚗',
    'body': '🛞', 'transmission': '⚙️', 'fuel': '⛽', 'ac': '🌬️',
    'new': '🆕', 'best': '👑', 'stock': '📦', 'discount': '🔥',
    'fast': '⚡', 'quality': '✅', 'original': '🏭', 'analog': '🔀',
    'delivery': '🚚', 'pickup': '📍', 'warranty': '🛡️', 'install': '🔧',
    'rating': '⭐', 'review': '💬', 'compatible': '🔗', 'oem': '🏷️'
}

# Категории автозапчастей
AUTO_CATEGORIES = {
    'Двигатель': ['Масло', 'Фильтры', 'Ремни', 'Свечи', 'ТНВД'],
    'Тормоза': ['Колодки', 'Диски', 'Тормозная жидкость', 'Суппорта'],
    'Подвеска': ['Амортизаторы', 'Сайлентблоки', 'Пружины', 'Рычаги'],
    'Электрика': ['Аккумуляторы', 'Генераторы', 'Стартеры', 'Провода'],
    'Кузов': ['Фары', 'Зеркала', 'Щетки стеклоочистителя', 'Молдинги'],
    'Трансмиссия': ['Сцепление', 'Масло АКПП', 'ШРУСы', 'Подшипники'],
    'Охлаждение': ['Радиаторы', 'Помпы', 'Термостаты', 'Патрубки'],
    'Выхлопная': ['Глушители', 'Катализаторы', 'Коллекторы', 'Сажевые фильтры']
}

# Бренды автозапчастей
AUTO_BRANDS = [
    'Bosch', 'Mann', 'Mahle', 'Valeo', 'Febi', 'Bilstein',
    'KYB', 'Monroe', 'Brembo', 'ATE', 'NGK', 'Denso',
    'VAG', 'BMW', 'Mercedes', 'Toyota', 'Honda', 'Nissan',
    'Lada', 'GAZ', 'УАЗ', 'Hyundai', 'Kia', 'Ford'
]

# ============================================================================
# 🎨 ТИПЫ ДАННЫХ И КОНФИГУРАЦИЯ
# ============================================================================

class TemplateStyle(Enum):
    """Стили шаблонов для автозапчастей"""
    AUTO_MODERN = "auto_modern"       # Современный автостиль
    AUTO_PRO = "auto_pro"             # Профессиональный
    AUTO_BUDGET = "auto_budget"       # Бюджетный
    AUTO_PREMIUM = "auto_premium"     # Премиум
    AUTO_TECH = "auto_tech"           # Технологичный
    AUTO_STOCK = "auto_stock"         # Складской

class ColorPalette:
    """Цветовые палитры для авто-стилей"""
    PALETTES = {
        TemplateStyle.AUTO_MODERN: {
            'primary': (41, 128, 185),     # Синий (автомобильный)
            'secondary': (231, 76, 60),    # Красный (стоп-сигнал)
            'accent': (52, 152, 219),      # Светло-синий
            'background': (255, 255, 255), # Белый
            'card_bg': (245, 245, 245),    # Серый фон карточки
            'text': (44, 62, 80),          # Темно-серый
            'highlight': (241, 196, 15),   # Желтый (акцент)
            'danger': (231, 76, 60),       # Красный (скидка)
            'success': (46, 204, 113),     # Зеленый (в наличии)
            'border': (220, 220, 220)      # Серая рамка
        },
        TemplateStyle.AUTO_PRO: {
            'primary': (30, 30, 30),       # Черный (профессиональный)
            'secondary': (192, 57, 43),    # Красный (производитель)
            'accent': (52, 73, 94),        # Темно-синий
            'background': (250, 250, 250), # Светло-серый
            'card_bg': (255, 255, 255),    # Белый
            'text': (50, 50, 50),          # Темно-серый
            'highlight': (230, 126, 34),   # Оранжевый
            'danger': (192, 57, 43),
            'success': (39, 174, 96),
            'border': (200, 200, 200)
        },
        TemplateStyle.AUTO_PREMIUM: {
            'primary': (0, 0, 0),          # Черный (люкс)
            'secondary': (218, 165, 32),   # Золотой
            'accent': (120, 120, 120),     # Серый
            'background': (255, 255, 255), # Белый
            'card_bg': (255, 250, 240),    # Кремовый
            'text': (40, 40, 40),          # Черный текст
            'highlight': (218, 165, 32),   # Золотой
            'danger': (160, 64, 0),        # Коричневый
            'success': (46, 125, 50),      # Темно-зеленый
            'border': (218, 165, 32)       # Золотая рамка
        },
        TemplateStyle.AUTO_TECH: {
            'primary': (0, 100, 200),      # Техно-синий
            'secondary': (0, 200, 255),    # Неоново-синий
            'accent': (100, 100, 255),     # Фиолетовый
            'background': (15, 25, 40),    # Темно-синий фон
            'card_bg': (25, 35, 50),       # Карточка
            'text': (220, 220, 255),       # Светлый текст
            'highlight': (0, 255, 200),    # Неоново-зеленый
            'danger': (255, 50, 100),      # Неоново-красный
            'success': (0, 255, 150),      # Неоново-зеленый
            'border': (0, 150, 255)        # Синяя рамка
        }
    }

@dataclass
class AutoPartData:
    """Структура данных автозапчасти"""
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

    def __post_init__(self):
        if self.compatibility is None:
            self.compatibility = []
        if self.features is None:
            self.features = []
        if self.images is None:
            self.images = []

# ============================================================================
# 🎨 УЛУЧШЕННЫЙ ТЕКСТОВЫЙ ПРОЦЕССОР ДЛЯ АВТОЗАПЧАСТЕЙ
# ============================================================================

class AutoTextProcessor:
    """Специализированный процессор для автозапчастей"""
    
    def __init__(self, language: str = 'ru'):
        self.language = language
        self.icons = AUTO_ICONS
        
    def get_icon_for_category(self, category: str) -> str:
        """Получение иконки для категории"""
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
            'трансмиссия': '⚙️', 'сцеплен': '⚙️', 'коробк': '⚙️'
        }
        
        for key, icon in icon_map.items():
            if key in category_lower:
                return icon
        return '🔧'
    
    def format_price(self, price: str, currency: str = '₽') -> Dict:
        """Форматирование цены для автозапчастей"""
        try:
            # Очищаем цену от лишних символов
            clean_price = re.sub(r'[^\d]', '', price)
            numeric_price = int(clean_price) if clean_price else 0
            
            # Форматируем с пробелами для тысяч
            formatted = f"{numeric_price:,}".replace(',', ' ')
            
            return {
                'formatted': f"{formatted}{currency}",
                'numeric': numeric_price,
                'currency': currency
            }
        except:
            return {
                'formatted': f"0{currency}",
                'numeric': 0,
                'currency': currency
            }
    
    def create_compatibility_badge(self, car_models: List[str], max_models: int = 3) -> str:
        """Создание бейджа совместимости"""
        if not car_models:
            return "🚗 Совместимость уточняйте"
        
        models = car_models[:max_models]
        base_text = "🚗 " + ", ".join(models)
        
        if len(car_models) > max_models:
            base_text += f" +{len(car_models) - max_models}"
        
        return base_text
    
    def create_delivery_info(self, stock: str, delivery: str) -> Dict:
        """Создание информации о доставке"""
        stock_lower = stock.lower()
        
        if 'налич' in stock_lower or 'есть' in stock_lower or 'склад' in stock_lower:
            stock_icon = '📦'
            stock_color = 'success'
            stock_text = 'В наличии'
        elif 'под заказ' in stock_lower or 'заказ' in stock_lower:
            stock_icon = '📋'
            stock_color = 'warning'
            stock_text = 'Под заказ'
        else:
            stock_icon = '⏳'
            stock_color = 'danger'
            stock_text = 'Нет в наличии'
        
        # Парсим срок доставки
        delivery_days = 3
        delivery_match = re.search(r'(\d+)[\s\-]?(\d+)?', delivery)
        if delivery_match:
            if delivery_match.group(2):
                delivery_days = int(delivery_match.group(2))
            else:
                delivery_days = int(delivery_match.group(1))
        
        if delivery_days <= 1:
            delivery_icon = '⚡'
            delivery_text = 'Сегодня-завтра'
        elif delivery_days <= 3:
            delivery_icon = '🚚'
            delivery_text = '1-3 дня'
        else:
            delivery_icon = '📅'
            delivery_text = f'{delivery_days} дней'
        
        return {
            'stock': {
                'icon': stock_icon,
                'text': stock_text,
                'color': stock_color
            },
            'delivery': {
                'icon': delivery_icon,
                'text': delivery_text,
                'days': delivery_days
            }
        }
    
    def create_features_list(self, features: List[str], max_features: int = 5) -> List[str]:
        """Создание списка характеристик"""
        formatted = []
        for feature in features[:max_features]:
            icon = self._get_feature_icon(feature)
            formatted.append(f"{icon} {feature}")
        
        # Добавляем заглушки если характеристик мало
        placeholder_features = [
            "🔧 Легкая установка",
            "✅ Гарантия качества",
            "📦 Оригинальная упаковка",
            "🛡️ Официальная гарантия",
            "🏭 Проверенный производитель"
        ]
        
        while len(formatted) < 3:
            formatted.append(placeholder_features[len(formatted)])
        
        return formatted
    
    def _get_feature_icon(self, feature: str) -> str:
        """Определение иконки для характеристики"""
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
# 🎨 ГРАФИЧЕСКИЙ ГЕНЕРАТОР ДЛЯ АВТОЗАПЧАСТЕЙ (ИСПРАВЛЕННАЯ ВЕРСИЯ)
# ============================================================================

class AutoGraphicsGenerator:
    """Специализированный графический генератор для авто"""
    
    @staticmethod
    def create_rounded_rect(draw: ImageDraw.ImageDraw,
                           position: Tuple[int, int],
                           size: Tuple[int, int],
                           radius: int,
                           fill: Optional[Tuple[int, int, int]] = None,
                           outline: Optional[Tuple[int, int, int]] = None,
                           width: int = 1) -> None:
        """Рисует скругленный прямоугольник - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        x, y = position
        width_rect, height_rect = size
        
        # Создаем маску для скругленных углов
        if fill:
            # Рисуем основной прямоугольник
            draw.rectangle([x + radius, y,
                          x + width_rect - radius, y + height_rect],
                         fill=fill, outline=None)
            draw.rectangle([x, y + radius,
                          x + width_rect, y + height_rect - radius],
                         fill=fill, outline=None)
            
            # Рисуем скругленные углы
            draw.pieslice([x, y, x + radius * 2, y + radius * 2],
                        180, 270, fill=fill, outline=None)
            draw.pieslice([x + width_rect - radius * 2, y,
                         x + width_rect, y + radius * 2],
                        270, 360, fill=fill, outline=None)
            draw.pieslice([x, y + height_rect - radius * 2,
                         x + radius * 2, y + height_rect],
                        90, 180, fill=fill, outline=None)
            draw.pieslice([x + width_rect - radius * 2, y + height_rect - radius * 2,
                         x + width_rect, y + height_rect],
                        0, 90, fill=fill, outline=None)
        
        # Контур
        if outline:
            # Вертикальные линии
            draw.line([(x + radius, y), (x + width_rect - radius, y)],
                     fill=outline, width=width)
            draw.line([(x + radius, y + height_rect),
                      (x + width_rect - radius, y + height_rect)],
                     fill=outline, width=width)
            
            # Горизонтальные линии
            draw.line([(x, y + radius), (x, y + height_rect - radius)],
                     fill=outline, width=width)
            draw.line([(x + width_rect, y + radius),
                      (x + width_rect, y + height_rect - radius)],
                     fill=outline, width=width)
            
            # Дуги в углах
            draw.arc([x, y, x + radius * 2, y + radius * 2], 180, 270,
                    fill=outline, width=width)
            draw.arc([x + width_rect - radius * 2, y,
                     x + width_rect, y + radius * 2], 270, 360,
                    fill=outline, width=width)
            draw.arc([x, y + height_rect - radius * 2,
                     x + radius * 2, y + height_rect], 90, 180,
                    fill=outline, width=width)
            draw.arc([x + width_rect - radius * 2, y + height_rect - radius * 2,
                     x + width_rect, y + height_rect], 0, 90,
                    fill=outline, width=width)
    
    @staticmethod
    def create_price_badge(draw: ImageDraw.ImageDraw,
                          position: Tuple[int, int],
                          price_data: Dict,
                          colors: Dict) -> None:
        """Создает бейдж цены"""
        x, y = position
        
        # Фон бейджа
        AutoGraphicsGenerator.create_rounded_rect(
            draw, (x, y), (280, 70), 15,
            fill=colors.get('primary', (41, 128, 185)),
            outline=colors.get('border', (200, 200, 200))
        )
        
        # Цена - используем существующий шрифт
        font_large = ImageFont.load_default()
        price_text = price_data.get('current', '0 ₽')
        draw.text((x + 20, y + 15), price_text,
                 fill=(255, 255, 255), font=font_large)
        
        # Старая цена
        if price_data.get('old'):
            font_small = ImageFont.load_default()
            draw.text((x + 20, y + 45), price_data['old'],
                     fill=(200, 200, 200), font=font_small)
    
    @staticmethod
    def create_stock_badge(draw: ImageDraw.ImageDraw,
                          position: Tuple[int, int],
                          stock_data: Dict,
                          colors: Dict) -> None:
        """Создает бейдж наличия"""
        x, y = position
        
        # Цвет в зависимости от наличия
        if stock_data.get('color') == 'success':
            bg_color = colors.get('success', (46, 204, 113))
        elif stock_data.get('color') == 'warning':
            bg_color = colors.get('highlight', (241, 196, 15))
        else:
            bg_color = colors.get('danger', (231, 76, 60))
        
        # Бейдж
        AutoGraphicsGenerator.create_rounded_rect(
            draw, (x, y), (180, 40), 10,
            fill=bg_color,
            outline=None
        )
        
        text = f"{stock_data.get('icon', '📦')} {stock_data.get('text', 'В наличии')}"
        draw.text((x + 10, y + 10), text,
                 fill=(255, 255, 255))
    
    @staticmethod
    def create_car_compatibility(draw: ImageDraw.ImageDraw,
                                position: Tuple[int, int],
                                car_models: List[str],
                                colors: Dict) -> None:
        """Создает блок совместимости с автомобилями"""
        x, y = position
        
        # Фон блока
        AutoGraphicsGenerator.create_rounded_rect(
            draw, (x, y), (400, 60), 10,
            fill=colors.get('card_bg', (245, 245, 245)),
            outline=colors.get('border', (220, 220, 220))
        )
        
        # Иконка и текст
        icon = "🚗"
        models_text = ", ".join(car_models[:3])
        if len(car_models) > 3:
            models_text += f" +{len(car_models)-3}"
        
        text = f"{icon} Совместимость: {models_text}"
        draw.text((x + 15, y + 20), text,
                 fill=colors.get('text', (44, 62, 80)))

# ============================================================================
# 🎨 КЛАСС ДЛЯ СОЗДАНИЯ ПОДЛОЖКИ АВТОЗАПЧАСТЕЙ (ПОЛНАЯ ВЕРСИЯ)
# ============================================================================

class AutoBackgroundGenerator:
    """Генератор специализированных подложек для автозапчастей"""
    
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
        """
        Создание подложки для автозапчастей
        
        Args:
            size: Размер изображения (ширина, высота)
            bg_type: Тип подложки ['gradient', 'pattern', 'geometric', 'texture']
            theme: Тема оформления
            category: Категория запчасти (для тематических паттернов)
            
        Returns:
            PIL Image объект
        """
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
        """Создание градиентной подложки"""
        # Определяем цвета по теме
        if theme == 'auto_modern':
            colors = [(41, 128, 185), (52, 152, 219), (93, 173, 226)]  # Синие тона
        elif theme == 'auto_pro':
            colors = [(30, 30, 30), (52, 73, 94), (44, 62, 80)]  # Темные тона
        elif theme == 'auto_premium':
            colors = [(0, 0, 0), (50, 50, 50), (120, 120, 120)]  # Черно-серые
        elif theme == 'auto_tech':
            colors = [(15, 25, 40), (30, 45, 70), (50, 70, 100)]  # Техно синие
        else:
            colors = [(41, 128, 185), (52, 152, 219), (26, 188, 156)]  # Стандартные
        
        # Создаем новое изображение
        image = Image.new('RGB', (width, height), colors[0])
        draw = ImageDraw.Draw(image)
        
        # Рисуем линейный градиент
        for i in range(height):
            ratio = i / height
            r = int(colors[0][0] * (1 - ratio) + colors[1][0] * ratio)
            g = int(colors[0][1] * (1 - ratio) + colors[1][1] * ratio)
            b = int(colors[0][2] * (1 - ratio) + colors[1][2] * ratio)
            draw.line([(0, i), (width, i)], fill=(r, g, b))
        
        # Добавляем второй градиент под углом
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
        
        # Добавляем легкий шум
        image = self._add_texture_noise(image, intensity=3)
        
        return image
    
    def _create_pattern_background(self,
                                  width: int,
                                  height: int,
                                  category: str) -> Image.Image:
        """Создание тематического паттерна"""
        # Определяем функцию паттерна
        pattern_func = self.parts_patterns.get(category, self.parts_patterns['default'])
        
        # Создаем базовое изображение
        image = Image.new('RGB', (width, height), (245, 245, 245))
        draw = ImageDraw.Draw(image)
        
        # Рисуем паттерн
        pattern_func(draw, width, height)
        
        # Добавляем легкий градиент поверх
        overlay = self._create_gradient_background(width, height, 'auto_modern')
        overlay = overlay.convert('RGBA')
        
        # Устанавливаем прозрачность
        alpha = overlay.split()[3]
        alpha = alpha.point(lambda p: p * 0.3)  # 30% прозрачность
        overlay.putalpha(alpha)
        
        # Накладываем
        image = image.convert('RGBA')
        image = Image.alpha_composite(image, overlay)
        
        return image.convert('RGB')
    
    def _create_engine_pattern(self, draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
        """Паттерн для двигателя"""
        # Шестерни и механические элементы
        for x in range(0, width, 100):
            for y in range(0, height, 100):
                # Рисуем шестеренку
                center_x = x + 50
                center_y = y + 50
                
                # Круг шестеренки
                draw.ellipse([center_x - 20, center_y - 20,
                            center_x + 20, center_y + 20],
                           fill=(220, 220, 220), outline=(180, 180, 180))
                
                # Зубья шестеренки
                for angle in range(0, 360, 30):
                    rad = angle * np.pi / 180
                    x1 = center_x + 25 * np.cos(rad)
                    y1 = center_y + 25 * np.sin(rad)
                    
                    draw.ellipse([x1 - 5, y1 - 5, x1 + 5, y1 + 5],
                               fill=(200, 200, 200))
    
    def _create_brake_pattern(self, draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
        """Паттерн для тормозов"""
        # Тормозные диски и колодки
        for x in range(0, width, 120):
            for y in range(0, height, 120):
                # Тормозной диск
                draw.ellipse([x + 10, y + 10, x + 110, y + 110],
                           fill=(230, 230, 230), outline=(200, 200, 200))
                
                # Отверстия вентиляции
                for i in range(6):
                    angle = i * 60
                    rad = angle * np.pi / 180
                    hole_x = x + 60 + 35 * np.cos(rad)
                    hole_y = y + 60 + 35 * np.sin(rad)
                    
                    draw.ellipse([hole_x - 8, hole_y - 8, hole_x + 8, hole_y + 8],
                               fill=(210, 210, 210))
    
    def _create_wheel_pattern(self, draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
        """Паттерн для колес и шин"""
        for x in range(0, width, 150):
            for y in range(0, height, 150):
                # Протектор шины
                for i in range(8):
                    angle = i * 45
                    rad = angle * np.pi / 180
                    
                    # Рисуем элементы протектора
                    for r in [30, 40, 50]:
                        x1 = x + 75 + r * np.cos(rad)
                        y1 = y + 75 + r * np.sin(rad)
                        
                        if i % 2 == 0:
                            draw.rectangle([x1 - 3, y1 - 10, x1 + 3, y1 + 10],
                                         fill=(220, 220, 220))
                        else:
                            draw.ellipse([x1 - 5, y1 - 5, x1 + 5, y1 + 5],
                                       fill=(220, 220, 220))
    
    def _create_electric_pattern(self, draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
        """Паттерн для электрики"""
        for x in range(0, width, 80):
            for y in range(0, height, 80):
                # Электрические схемы
                draw.rectangle([x + 10, y + 10, x + 70, y + 70],
                             fill=(230, 230, 230), outline=(200, 200, 200))
                
                # Линии соединений
                draw.line([(x + 20, y + 20), (x + 60, y + 60)],
                         fill=(180, 180, 180), width=2)
                draw.line([(x + 60, y + 20), (x + 20, y + 60)],
                         fill=(180, 180, 180), width=2)
    
    def _create_suspension_pattern(self, draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
        """Паттерн для подвески"""
        for x in range(0, width, 100):
            for y in range(0, height, 100):
                # Амортизаторы
                draw.rectangle([x + 30, y + 10, x + 70, y + 90],
                             fill=(230, 230, 230), outline=(200, 200, 200))
                
                # Пружина
                for i in range(5):
                    y_pos = y + 20 + i * 15
                    draw.ellipse([x + 25, y_pos, x + 75, y_pos + 10],
                               fill=(210, 210, 210), outline=(190, 190, 190))
    
    def _create_geometric_background(self,
                                    width: int,
                                    height: int,
                                    theme: str) -> Image.Image:
        """Создание геометрической подложки"""
        # Создаем базовое изображение с градиентом
        image = self._create_gradient_background(width, height, theme)
        
        # Определяем цвета по теме
        if theme == 'auto_modern':
            colors = [(41, 128, 185), (52, 152, 219), (26, 188, 156)]
        elif theme == 'auto_pro':
            colors = [(30, 30, 30), (52, 73, 94), (44, 62, 80)]
        else:
            colors = [(41, 128, 185), (231, 76, 60), (241, 196, 15)]
        
        # Рисуем геометрические фигуры на прозрачном слое
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        for _ in range(25):
            color = random.choice(colors)
            
            # Случайная фигура
            shape_type = random.choice(['circle', 'rectangle', 'triangle'])
            
            x = random.randint(-50, width)
            y = random.randint(-50, height)
            size = random.randint(80, 300)
            alpha = random.randint(10, 40)  # Прозрачность
            
            # Добавляем альфа-канал к цвету
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
        
        # Размываем для мягкого эффекта
        overlay = overlay.filter(ImageFilter.GaussianBlur(radius=15))
        
        # Накладываем фигуры на градиент
        image = image.convert('RGBA')
        image = Image.alpha_composite(image, overlay)
        
        return image.convert('RGB')
    
    def _create_texture_background(self, width: int, height: int) -> Image.Image:
        """Создание текстурной подложки"""
        # Базовый градиент
        image = self._create_gradient_background(width, height, 'auto_modern')
        image = image.convert('RGBA')
        
        # Создаем текстуру шума
        noise = Image.effect_noise((width, height), 10)
        noise = noise.convert('RGBA')
        
        # Устанавливаем прозрачность
        alpha = noise.split()[3]
        alpha = alpha.point(lambda p: p * 25)  # 10% прозрачность (255 * 0.1 ≈ 25)
        noise.putalpha(alpha)
        
        # Накладываем текстуру
        image = Image.alpha_composite(image, noise)
        
        # Добавляем легкие царапины/потертости
        scratches = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        scratches_draw = ImageDraw.Draw(scratches)
        
        for _ in range(random.randint(5, 15)):
            x1 = random.randint(0, width)
            y1 = random.randint(0, height)
            length = random.randint(20, 100)
            angle = random.uniform(0, np.pi)
            
            x2 = int(x1 + length * np.cos(angle))
            y2 = int(y1 + length * np.sin(angle))
            
            scratches_draw.line([(x1, y1), (x2, y2)],
                              fill=(255, 255, 255, random.randint(3, 8)),
                              width=random.randint(1, 2))
        
        image = Image.alpha_composite(image, scratches)
        
        return image.convert('RGB')
    
    def _create_default_pattern(self, draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
        """Паттерн по умолчанию - сетка с точками"""
        # Сетка
        for x in range(0, width, 50):
            draw.line([(x, 0), (x, height)], fill=(220, 220, 220), width=1)
        for y in range(0, height, 50):
            draw.line([(0, y), (width, y)], fill=(220, 220, 220), width=1)
        
        # Точки на пересечениях
        for x in range(25, width, 50):
            for y in range(25, height, 50):
                draw.ellipse([x - 2, y - 2, x + 2, y + 2],
                           fill=(200, 200, 200))
    
    def _add_texture_noise(self, image: Image.Image, intensity: int = 10) -> Image.Image:
        """Добавление текстуры шума"""
        # Создаем слой шума
        noise_layer = Image.effect_noise(image.size, intensity)
        
        # Конвертируем в RGBA для смешивания
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        noise_layer = noise_layer.convert('RGBA')
        
        # Устанавливаем низкую прозрачность
        alpha = noise_layer.split()[3]
        alpha = alpha.point(lambda p: p * 25)  # 10% прозрачность
        noise_layer.putalpha(alpha)
        
        # Смешиваем
        result = Image.alpha_composite(image, noise_layer)
        
        return result.convert('RGB')
    
    def create_product_card_background(self,
                                      size: Tuple[int, int] = (800, 1200),
                                      style: str = 'auto_modern',
                                      with_logo_area: bool = True,
                                      with_text_area: bool = True) -> Image.Image:
        """
        Создание готовой подложки для карточки товара
        
        Args:
            size: Размер карточки
            style: Стиль оформления
            with_logo_area: Добавить область для логотипа
            with_text_area: Добавить область для текста
            
        Returns:
            Готовая подложка
        """
        width, height = size
        
        # Создаем основную подложку
        background = self.create_background(size, 'gradient', style)
        
        # Конвертируем в RGBA для работы с прозрачностью
        if background.mode != 'RGBA':
            background = background.convert('RGBA')
        
        draw = ImageDraw.Draw(background)
        
        # Добавляем декоративные элементы
        
        # 1. Верхняя полоса для бренда
        if with_logo_area:
            self._draw_logo_area(draw, width, height, style)
        
        # 2. Центральная область для изображения товара
        self._draw_product_area(draw, width, height, style)
        
        # 3. Нижняя область для текста
        if with_text_area:
            self._draw_text_area(draw, width, height, style)
        
        # 4. Декоративные уголки
        self._draw_corners(draw, width, height, style)
        
        return background.convert('RGB')
    
    def _draw_logo_area(self, draw: ImageDraw.ImageDraw, width: int, height: int, style: str) -> None:
        """Область для логотипа бренда"""
        # Цвет полосы
        if style == 'auto_premium':
            color = (218, 165, 32)  # Золотой
        elif style == 'auto_tech':
            color = (0, 200, 255)   # Неоновый
        else:
            color = (41, 128, 185)  # Синий
        
        # Декоративная полоса вверху
        draw.rectangle([0, 0, width, 5], fill=color)
        draw.rectangle([0, 5, width, 30], fill=color + (150,))  # 60% прозрачность
        
        # Декоративная линия
        line_color = color + (150,)
        draw.line([(0, 30), (width, 30)], fill=line_color, width=2)
    
    def _draw_product_area(self, draw: ImageDraw.ImageDraw, width: int, height: int, style: str) -> None:
        """Область для изображения товара"""
        # Светлый прямоугольник в центре
        center_x, center_y = width // 2, height // 2
        rect_width, rect_height = 600, 400
        
        if style == 'auto_premium':
            bg_color = (255, 250, 240)  # Кремовый
            border_color = (218, 165, 32)  # Золотой
        elif style == 'auto_pro':
            bg_color = (255, 255, 255)  # Белый
            border_color = (200, 200, 200)  # Серый
        else:
            bg_color = (250, 250, 250)  # Светло-серый
            border_color = (220, 220, 220)  # Светло-серый
        
        # Основной прямоугольник
        rect_x = center_x - rect_width // 2
        rect_y = center_y - rect_height // 2
        
        AutoGraphicsGenerator.create_rounded_rect(
            draw, (rect_x, rect_y), (rect_width, rect_height), 20,
            fill=bg_color,
            outline=border_color,
            width=2
        )
    
    def _draw_text_area(self, draw: ImageDraw.ImageDraw, width: int, height: int, style: str) -> None:
        """Область для текстовой информации"""
        # Полупрозрачная область снизу
        text_area_height = 300
        
        if style == 'auto_tech':
            bg_color = (25, 35, 50)  # Темно-синий
        else:
            bg_color = (255, 255, 255)  # Белый
        
        # Создаем прозрачный прямоугольник
        text_area = Image.new('RGBA', (width, text_area_height), bg_color + (180,))
        
        # Рисуем просто прямоугольник
        draw.rectangle([0, height - text_area_height, width, height],
                      fill=bg_color + (180,))
        
        # Разделительная линия
        draw.line([(0, height - text_area_height), (width, height - text_area_height)],
                 fill=(200, 200, 200, 150), width=1)
    
    def _draw_corners(self, draw: ImageDraw.ImageDraw, width: int, height: int, style: str) -> None:
        """Декоративные уголки"""
        corner_size = 20
        
        if style == 'auto_premium':
            corner_color = (218, 165, 32)  # Золотой
        elif style == 'auto_tech':
            corner_color = (0, 200, 255)   # Неоновый
        else:
            corner_color = (41, 128, 185)  # Синий
        
        # Левый верхний
        draw.line([(0, corner_size), (corner_size, 0)],
                 fill=corner_color + (200,), width=3)
        
        # Правый верхний
        draw.line([(width - corner_size, 0), (width, corner_size)],
                 fill=corner_color + (200,), width=3)
        
        # Левый нижний
        draw.line([(0, height - corner_size), (corner_size, height)],
                 fill=corner_color + (200,), width=3)
        
        # Правый нижний
        draw.line([(width - corner_size, height), (width, height - corner_size)],
                 fill=corner_color + (200,), width=3)

# ============================================================================
# 🎨 ШАБЛОНЫ ДЛЯ АВТОЗАПЧАСТЕЙ (ПОЛНАЯ ВЕРСИЯ)
# ============================================================================

class AutoTemplateFactory:
    """Фабрика шаблонов для автозапчастей"""
    
    @staticmethod
    def create_template(style: TemplateStyle,
                       size: Tuple[int, int] = (800, 1200)) -> List[Dict]:
        """Создает шаблон для автозапчастей"""
        
        templates = {
            TemplateStyle.AUTO_MODERN: AutoTemplateFactory._modern_template(size),
            TemplateStyle.AUTO_PRO: AutoTemplateFactory._pro_template(size),
            TemplateStyle.AUTO_PREMIUM: AutoTemplateFactory._premium_template(size),
            TemplateStyle.AUTO_TECH: AutoTemplateFactory._tech_template(size)
        }
        
        return templates.get(style, AutoTemplateFactory._modern_template(size))
    
    @staticmethod
    def _modern_template(size: Tuple[int, int]) -> List[Dict]:
        """Современный шаблон для маркетплейсов"""
        width, height = size
        
        return [
            # Шапка с брендом и категорией
            {
                'type': 'header',
                'position': (20, 20),
                'size': (width - 40, 60),
                'style': 'brand_header'
            },
            
            # Изображение товара
            {
                'type': 'image',
                'position': (40, 100),
                'size': (width - 80, 300),
                'style': 'product_image'
            },
            
            # Название товара
            {
                'type': 'title',
                'position': (40, 420),
                'size': (width - 80, 60),
                'style': 'product_title'
            },
            
            # OEM номер
            {
                'type': 'oem',
                'position': (40, 490),
                'size': (width - 80, 40),
                'style': 'oem_badge'
            },
            
            # Цена
            {
                'type': 'price',
                'position': (40, 540),
                'size': (width - 80, 80),
                'style': 'price_block'
            },
            
            # Наличие и доставка
            {
                'type': 'stock_delivery',
                'position': (40, 640),
                'size': (width - 80, 60),
                'style': 'stock_info'
            },
            
            # Совместимость
            {
                'type': 'compatibility',
                'position': (40, 720),
                'size': (width - 80, 80),
                'style': 'compatibility_block'
            },
            
            # Характеристики
            {
                'type': 'features',
                'position': (40, 820),
                'size': (width - 80, 200),
                'style': 'features_list'
            },
            
            # Рейтинг и отзывы
            {
                'type': 'rating',
                'position': (40, 1040),
                'size': (width - 80, 40),
                'style': 'rating_block'
            },
            
            # Футер с гарантией
            {
                'type': 'footer',
                'position': (20, height - 60),
                'size': (width - 40, 40),
                'style': 'footer_warranty'
            }
        ]
    
    @staticmethod
    def _pro_template(size: Tuple[int, int]) -> List[Dict]:
        """Профессиональный шаблон для автосервисов"""
        width, height = size
        
        return [
            # Минималистичная шапка
            {
                'type': 'header',
                'position': (0, 0),
                'size': (width, 50),
                'style': 'minimal_header'
            },
            
            # Большое изображение
            {
                'type': 'image',
                'position': (20, 60),
                'size': (width - 40, 350),
                'style': 'large_image'
            },
            
            # OEM и бренд
            {
                'type': 'oem_brand',
                'position': (20, 430),
                'size': (width - 40, 50),
                'style': 'oem_brand_row'
            },
            
            # Название
            {
                'type': 'title',
                'position': (20, 490),
                'size': (width - 40, 50),
                'style': 'pro_title'
            },
            
            # Технические характеристики
            {
                'type': 'specs',
                'position': (20, 560),
                'size': (width - 40, 200),
                'style': 'tech_specs'
            },
            
            # Цена для профессионалов
            {
                'type': 'price',
                'position': (20, 780),
                'size': (width - 40, 100),
                'style': 'pro_price'
            },
            
            # Наличие
            {
                'type': 'stock',
                'position': (20, 900),
                'size': (width - 40, 40),
                'style': 'stock_only'
            }
        ]
    
    @staticmethod
    def _premium_template(size: Tuple[int, int]) -> List[Dict]:
        """Премиум шаблон для оригинальных запчастей"""
        width, height = size
        
        return [
            # Золотая рамка
            {
                'type': 'golden_border',
                'position': (10, 10),
                'size': (width - 20, height - 20),
                'style': 'luxury_border'
            },
            
            # Изображение на темном фоне
            {
                'type': 'image',
                'position': (40, 40),
                'size': (width - 80, 400),
                'style': 'premium_image'
            },
            
            # Бренд
            {
                'type': 'brand',
                'position': (40, 460),
                'size': (width - 80, 50),
                'style': 'premium_brand'
            },
            
            # Название
            {
                'type': 'title',
                'position': (40, 520),
                'size': (width - 80, 60),
                'style': 'premium_title'
            },
            
            # OEM оригинал
            {
                'type': 'oem',
                'position': (40, 600),
                'size': (width - 80, 40),
                'style': 'original_oem'
            },
            
            # Цена
            {
                'type': 'price',
                'position': (40, 660),
                'size': (width - 80, 80),
                'style': 'premium_price'
            },
            
            # Гарантия оригинала
            {
                'type': 'warranty',
                'position': (40, 760),
                'size': (width - 80, 100),
                'style': 'original_warranty'
            }
        ]
    
    @staticmethod
    def _tech_template(size: Tuple[int, int]) -> List[Dict]:
        """Технологичный шаблон"""
        width, height = size
        
        return [
            # Техно-шапка
            {
                'type': 'header',
                'position': (0, 0),
                'size': (width, 80),
                'style': 'tech_header'
            },
            
            # Изображение с эффектом
            {
                'type': 'image',
                'position': (30, 100),
                'size': (width - 60, 350),
                'style': 'tech_image'
            },
            
            # Технические данные
            {
                'type': 'tech_specs',
                'position': (30, 470),
                'size': (width - 60, 200),
                'style': 'specs_grid'
            },
            
            # Совместимость
            {
                'type': 'compatibility',
                'position': (30, 690),
                'size': (width - 60, 100),
                'style': 'tech_compatibility'
            },
            
            # Цена и наличие
            {
                'type': 'price_stock',
                'position': (30, 810),
                'size': (width - 60, 120),
                'style': 'tech_price_stock'
            }
        ]

# ============================================================================
# 🎨 ОСНОВНОЙ ГЕНЕРАТОР АВТОЗАПЧАСТЕЙ (ПОЛНАЯ ВЕРСИЯ)
# ============================================================================

class AutoPartsInfographicGenerator:
    """Основной генератор инфографики для автозапчастей"""
    
    def __init__(self, style: TemplateStyle = TemplateStyle.AUTO_MODERN):
        self.style = style
        self.colors = ColorPalette.PALETTES[style]
        self.text_processor = AutoTextProcessor()
        self.graphics = AutoGraphicsGenerator()
        
    def generate(self, part_data: AutoPartData, output_path: str) -> str:
        """Генерация инфографики для автозапчасти"""
        
        # Размер карточки (как в маркетплейсах)
        width, height = 800, 1200
        
        # Создаем изображение
        image = Image.new('RGB', (width, height),
                         self.colors.get('background', (255, 255, 255)))
        draw = ImageDraw.Draw(image)
        
        # Получаем шаблон
        template = AutoTemplateFactory.create_template(self.style, (width, height))
        
        # Рендерим все блоки
        for block in template:
            self._render_block(image, draw, block, part_data)
        
        # Сохраняем
        image.save(output_path, 'PNG', quality=95)
        return output_path
    
    def _render_block(self, image: Image.Image, draw: ImageDraw.ImageDraw,
                     block: Dict, part_data: AutoPartData) -> None:
        """Рендеринг отдельного блока"""
        
        block_type = block['type']
        x, y = block['position']
        w, h = block['size']
        
        if block_type == 'header':
            self._render_header(draw, x, y, w, h, part_data)
        elif block_type == 'image':
            self._render_product_image(image, x, y, w, h, part_data)
        elif block_type == 'title':
            self._render_title(draw, x, y, w, h, part_data)
        elif block_type == 'price':
            self._render_price(draw, x, y, w, h, part_data)
        elif block_type == 'stock_delivery':
            self._render_stock_delivery(draw, x, y, w, h, part_data)
        elif block_type == 'compatibility':
            self._render_compatibility(draw, x, y, w, h, part_data)
        elif block_type == 'features':
            self._render_features(draw, x, y, w, h, part_data)
        elif block_type == 'rating':
            self._render_rating(draw, x, y, w, h, part_data)
        elif block_type == 'oem':
            self._render_oem(draw, x, y, w, h, part_data)
        elif block_type == 'footer':
            self._render_footer(draw, x, y, w, h, part_data)
    
    def _render_header(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, data: AutoPartData) -> None:
        """Рендеринг шапки с брендом и категорией"""
        # Фон шапки
        self.graphics.create_rounded_rect(
            draw, (x, y), (w, h), 10,
            fill=self.colors.get('card_bg', (245, 245, 245)),
            outline=self.colors.get('border', (220, 220, 220))
        )
        
        # Бренд
        brand_text = f"🏷️ {data.brand}" if data.brand else "🏷️ Производитель"
        draw.text((x + 15, y + 20), brand_text,
                 fill=self.colors.get('text', (44, 62, 80)))
        
        # Категория справа
        category_icon = self.text_processor.get_icon_for_category(data.category)
        category_text = f"{category_icon} {data.category}" if data.category else "🔧 Запчасть"
        
        # Используем доступный шрифт для измерения текста
        try:
            font = ImageFont.truetype("arial.ttf", 16) if os.path.exists("arial.ttf") else ImageFont.load_default()
        except:
            font = ImageFont.load_default()
            
        # Простая оценка ширины текста
        text_width = len(category_text) * 10
        text_x = x + w - text_width - 15
        
        draw.text((text_x, y + 20), category_text,
                 fill=self.colors.get('secondary', (231, 76, 60)), font=font)
    
    def _render_product_image(self, image: Image.Image, x: int, y: int, w: int, h: int, data: AutoPartData) -> None:
        """Рендеринг изображения товара"""
        # Рамка для изображения
        self.graphics.create_rounded_rect(
            ImageDraw.Draw(image), (x, y), (w, h), 15,
            fill=(250, 250, 250),
            outline=self.colors.get('border', (220, 220, 220))
        )
        
        # Заглушка изображения
        draw = ImageDraw.Draw(image)
        icon = self.text_processor.get_icon_for_category(data.category)
        text = f"{icon}\nИЗОБРАЖЕНИЕ\nАВТОЗАПЧАСТИ"
        
        # Центрируем текст
        lines = text.split('\n')
        line_height = 30
        total_height = len(lines) * line_height
        start_y = y + (h - total_height) // 2
        
        for i, line in enumerate(lines):
            text_width = len(line) * 10  # Примерная ширина символа
            text_x = x + (w - text_width) // 2
            text_y = start_y + i * line_height
            draw.text((text_x, text_y), line,
                     fill=self.colors.get('text', (100, 100, 100)))
    
    def _render_title(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, data: AutoPartData) -> None:
        """Рендеринг названия товара"""
        # Обрезаем длинное название
        title = data.name
        if len(title) > 50:
            title = title[:47] + "..."
        
        # Используем доступный шрифт
        try:
            font = ImageFont.truetype("arial.ttf", 24) if os.path.exists("arial.ttf") else ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        draw.text((x, y), title,
                 fill=self.colors.get('text', (44, 62, 80)), font=font)
    
    def _render_oem(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, data: AutoPartData) -> None:
        """Рендеринг OEM номера"""
        if data.oem:
            oem_text = f"🔢 OEM: {data.oem}"
            
            # Создаем бейдж OEM
            self.graphics.create_rounded_rect(
                draw, (x, y), (w, h), 5,
                fill=self.colors.get('card_bg', (245, 245, 245)),
                outline=self.colors.get('accent', (52, 152, 219))
            )
            
            draw.text((x + 10, y + 10), oem_text,
                     fill=self.colors.get('accent', (52, 152, 219)))
    
    def _render_price(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, data: AutoPartData) -> None:
        """Рендеринг блока цены"""
        # Форматируем цены
        current_price = self.text_processor.format_price(data.price)
        price_data = {
            'current': f"💰 {current_price['formatted']}",
            'old': None,
            'discount': None
        }
        
        if data.old_price:
            old_price = self.text_processor.format_price(data.old_price)
            price_data['old'] = f"~~{old_price['formatted']}~~"
            
            # Рассчитываем скидку
            if current_price['numeric'] > 0 and old_price['numeric'] > 0:
                discount = int((1 - current_price['numeric'] / old_price['numeric']) * 100)
                price_data['discount'] = f"-{discount}%"
        
        # Фон для цены
        self.graphics.create_rounded_rect(
            draw, (x, y), (w, h), 15,
            fill=self.colors.get('card_bg', (245, 245, 245)),
            outline=self.colors.get('border', (220, 220, 220))
        )
        
        # Текущая цена
        try:
            font_large = ImageFont.truetype("arial.ttf", 32) if os.path.exists("arial.ttf") else ImageFont.load_default()
        except:
            font_large = ImageFont.load_default()
        
        draw.text((x + 20, y + 20), price_data['current'],
                 fill=self.colors.get('primary', (41, 128, 185)), font=font_large)
        
        # Старая цена
        if price_data['old']:
            draw.text((x + 20, y + 60), price_data['old'],
                     fill=self.colors.get('secondary', (231, 76, 60)))
        
        # Скидка
        if price_data['discount']:
            # Бейдж скидки
            discount_width = 80
            self.graphics.create_rounded_rect(
                draw, (x + w - discount_width - 20, y + 20),
                (discount_width, 40), 10,
                fill=self.colors.get('danger', (231, 76, 60)),
                outline=None
            )
            
            draw.text((x + w - discount_width - 10, y + 30),
                     price_data['discount'],
                     fill=(255, 255, 255))
    
    def _render_stock_delivery(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, data: AutoPartData) -> None:
        """Рендеринг информации о наличии и доставке"""
        delivery_info = self.text_processor.create_delivery_info(
            data.stock, data.delivery
        )
        
        # Разделяем на две колонки
        col_width = w // 2
        
        # Наличие
        self.graphics.create_rounded_rect(
            draw, (x, y), (col_width - 10, h), 10,
            fill=self.colors.get('card_bg', (245, 245, 245)),
            outline=self.colors.get('border', (220, 220, 220))
        )
        
        stock_text = f"{delivery_info['stock']['icon']} {delivery_info['stock']['text']}"
        draw.text((x + 15, y + 20), stock_text,
                 fill=self.colors.get('success', (46, 204, 113)))
        
        # Доставка
        self.graphics.create_rounded_rect(
            draw, (x + col_width + 10, y), (col_width - 10, h), 10,
            fill=self.colors.get('card_bg', (245, 245, 245)),
            outline=self.colors.get('border', (220, 220, 220))
        )
        
        delivery_text = f"{delivery_info['delivery']['icon']} {delivery_info['delivery']['text']}"
        draw.text((x + col_width + 25, y + 20), delivery_text,
                 fill=self.colors.get('accent', (52, 152, 219)))
    
    def _render_compatibility(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, data: AutoPartData) -> None:
        """Рендеринг блока совместимости"""
        car_models = data.compatibility or []
        if data.car_model:
            car_models.insert(0, data.car_model)
        
        if not car_models:
            car_models = ["Уточняйте совместимость"]
        
        # Фон
        self.graphics.create_rounded_rect(
            draw, (x, y), (w, h), 10,
            fill=self.colors.get('card_bg', (245, 245, 245)),
            outline=self.colors.get('border', (220, 220, 220))
        )
        
        # Текст совместимости
        compatibility_text = self.text_processor.create_compatibility_badge(car_models)
        
        # Перенос строк при необходимости
        if len(compatibility_text) > 40:
            parts = textwrap.wrap(compatibility_text, width=40)
            for i, part in enumerate(parts[:2]):
                draw.text((x + 15, y + 15 + i * 25), part,
                         fill=self.colors.get('text', (44, 62, 80)))
        else:
            draw.text((x + 15, y + 25), compatibility_text,
                     fill=self.colors.get('text', (44, 62, 80)))
    
    def _render_features(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, data: AutoPartData) -> None:
        """Рендеринг характеристик"""
        features = data.features or [
            "Высокое качество материалов",
            "Сертифицированный производитель",
            "Гарантия соответствия"
        ]
        
        formatted_features = self.text_processor.create_features_list(features)
        
        # Фон
        self.graphics.create_rounded_rect(
            draw, (x, y), (w, h), 10,
            fill=self.colors.get('card_bg', (245, 245, 245)),
            outline=self.colors.get('border', (220, 220, 220))
        )
        
        # Заголовок
        draw.text((x + 15, y + 15), "📋 Основные характеристики:",
                 fill=self.colors.get('primary', (41, 128, 185)))
        
        # Список характеристик
        for i, feature in enumerate(formatted_features[:5]):
            feature_y = y + 45 + i * 30
            draw.text((x + 25, feature_y), feature,
                     fill=self.colors.get('text', (44, 62, 80)))
    
    def _render_rating(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, data: AutoPartData) -> None:
        """Рендеринг рейтинга"""
        rating = data.rating
        reviews = data.reviews
        
        # Звезды рейтинга
        stars_full = int(rating)
        stars_half = 1 if rating - stars_full >= 0.5 else 0
        stars_empty = 5 - stars_full - stars_half
        
        stars = '★' * stars_full + ('½' if stars_half else '') + '☆' * stars_empty
        
        rating_text = f"⭐ {rating:.1f} {stars}"
        if reviews > 0:
            rating_text += f" ({reviews} отзывов)"
        
        draw.text((x, y), rating_text,
                 fill=self.colors.get('highlight', (241, 196, 15)))
    
    def _render_footer(self, draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, data: AutoPartData) -> None:
        """Рендеринг футера"""
        warranty_text = f"🛡️ {data.warranty}"
        
        self.graphics.create_rounded_rect(
            draw, (x, y), (w, h), 10,
            fill=self.colors.get('card_bg', (245, 245, 245)),
            outline=self.colors.get('border', (220, 220, 220))
        )
        
        draw.text((x + 15, y + 12), warranty_text,
                 fill=self.colors.get('text', (44, 62, 80)))

# ============================================================================
# 🎨 УЛУЧШЕННЫЙ ГЕНЕРАТОР С ПОДЛОЖКОЙ (ПОЛНАЯ ВЕРСИЯ)
# ============================================================================

class EnhancedAutoPartsGenerator(AutoPartsInfographicGenerator):
    """Улучшенный генератор с поддержкой подложек"""
    
    def __init__(self, style: TemplateStyle = TemplateStyle.AUTO_MODERN):
        super().__init__(style)
        self.bg_generator = AutoBackgroundGenerator()
    
    def generate_with_background(self,
                                part_data: AutoPartData,
                                output_path: str,
                                bg_type: str = 'product_card') -> str:
        """
        Генерация инфографики с профессиональной подложкой
        
        Args:
            part_data: Данные автозапчасти
            output_path: Путь для сохранения
            bg_type: Тип подложки ['product_card', 'gradient', 'pattern', 'geometric']
        """
        
        width, height = 800, 1200
        
        # Создаем подложку
        if bg_type == 'product_card':
            background = self.bg_generator.create_product_card_background(
                size=(width, height),
                style=self.style.value
            )
        else:
            background = self.bg_generator.create_background(
                size=(width, height),
                bg_type=bg_type,
                theme=self.style.value,
                category=part_data.category
            )
        
        # Создаем основное изображение с прозрачным фоном
        foreground = Image.new('RGBA', (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(foreground)
        
        # Получаем шаблон
        template = AutoTemplateFactory.create_template(self.style, (width, height))
        
        # Рендерим все блоки на прозрачном фоне
        for block in template:
            self._render_block(foreground, draw, block, part_data)
        
        # Объединяем подложку и передний план
        if background.mode != 'RGBA':
            background = background.convert('RGBA')
        
        result = Image.alpha_composite(background, foreground)
        
        # Сохраняем
        result.save(output_path, 'PNG', quality=95)
        return output_path
    
    def create_background_only(self,
                              output_path: str,
                              size: Tuple[int, int] = (800, 1200),
                              bg_type: str = 'product_card') -> str:
        """
        Создание только подложки без контента
        
        Args:
            output_path: Путь для сохранения
            size: Размер изображения
            bg_type: Тип подложки
        """
        if bg_type == 'product_card':
            background = self.bg_generator.create_product_card_background(
                size=size,
                style=self.style.value
            )
        else:
            background = self.bg_generator.create_background(
                size=size,
                bg_type=bg_type,
                theme=self.style.value
            )
        
        background.save(output_path, 'PNG', quality=95)
        return output_path

# ============================================================================
# 🎨 СИСТЕМА ПАКЕТНОЙ ГЕНЕРАЦИИ (ПОЛНАЯ ВЕРСИЯ)
# ============================================================================

class AutoPartsBatchGenerator:
    """Система пакетной генерации инфографик для автозапчастей"""
    
    def __init__(self, template_style: TemplateStyle = TemplateStyle.AUTO_MODERN):
        self.template_style = template_style
        self.generator = AutoPartsInfographicGenerator(template_style)
        
    def generate_from_dataframe(self, df: pd.DataFrame, output_dir: str = 'auto_infographics') -> List[Dict]:
        """Генерация инфографик из DataFrame"""
        
        # Создаем директорию
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        results = []
        
        for idx, row in df.iterrows():
            try:
                # Преобразуем строку в AutoPartData
                part_data = self._row_to_part_data(row)
                
                # Генерируем имя файла
                filename = self._generate_filename(part_data, idx)
                output_path = Path(output_dir) / filename
                
                # Генерируем инфографику
                self.generator.generate(part_data, str(output_path))
                
                results.append({
                    'index': idx,
                    'filename': filename,
                    'path': str(output_path),
                    'success': True
                })
                
                print(f"✅ Создана инфографика: {filename}")
                
            except Exception as e:
                results.append({
                    'index': idx,
                    'error': str(e),
                    'success': False
                })
                print(f"❌ Ошибка в строке {idx}: {e}")
        
        return results
    
    def _row_to_part_data(self, row: pd.Series) -> AutoPartData:
        """Преобразование строки DataFrame в AutoPartData"""
        
        # Автоматическое определение полей
        data = {}
        
        for col in row.index:
            if pd.isna(row[col]):
                continue
                
            col_lower = col.lower()
            value = row[col]
            
            # Сопоставление полей
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
            elif any(word in col_lower for word in ['авто', 'модель', 'car', 'model']):
                data['car_model'] = str(value)
            elif any(word in col_lower for word in ['год', 'year', 'модельный год']):
                if 'от' in col_lower or 'с' in col_lower:
                    data['year_from'] = str(value)
                elif 'до' in col_lower or 'по' in col_lower:
                    data['year_to'] = str(value)
            elif any(word in col_lower for word in ['налич', 'stock', 'склад']):
                data['stock'] = str(value)
            elif any(word in col_lower for word in ['доставк', 'delivery', 'срок']):
                data['delivery'] = str(value)
            elif any(word in col_lower for word in ['гарант', 'warranty']):
                data['warranty'] = str(value)
            elif any(word in col_lower for word in ['рейтинг', 'rating']):
                try:
                    data['rating'] = float(value)
                except:
                    data['rating'] = 4.5
            elif any(word in col_lower for word in ['отзыв', 'review', 'feedback']):
                try:
                    data['reviews'] = int(value)
                except:
                    data['reviews'] = 0
            elif any(word in col_lower for word in ['совместим', 'compatib', 'подходит']):
                if isinstance(value, str):
                    data['compatibility'] = [v.strip() for v in value.split(',')]
                elif isinstance(value, list):
                    data['compatibility'] = value
            elif any(word in col_lower for word in ['характерист', 'feature', 'свойств', 'описан']):
                if isinstance(value, str):
                    data['features'] = [v.strip() for v in value.split(';')]
                elif isinstance(value, list):
                    data['features'] = value
        
        # Заполняем обязательные поля
        if 'name' not in data:
            data['name'] = f'Автозапчасть {row.name if hasattr(row, "name") else "unknown"}'
        if 'price' not in data:
            data['price'] = '1000'
        if 'brand' not in data:
            data['brand'] = random.choice(AUTO_BRANDS) if AUTO_BRANDS else 'Производитель'
        if 'category' not in data:
            data['category'] = random.choice(list(AUTO_CATEGORIES.keys()))
        
        return AutoPartData(**data)
    
    def _generate_filename(self, part_data: AutoPartData, idx: int) -> str:
        """Генерация имени файла"""
        # Используем OEM или название
        base_name = part_data.oem if part_data.oem else part_data.name
        
        # Очищаем имя файла
        safe_name = re.sub(r'[^\w\s-]', '', base_name)
        safe_name = re.sub(r'[-\s]+', '_', safe_name)
        safe_name = safe_name[:50]  # Ограничиваем длину
        
        return f"{safe_name}_{self.template_style.value}_{idx:04d}.png"

class EnhancedAutoPartsBatchGenerator(AutoPartsBatchGenerator):
    """Улучшенный пакетный генератор с подложками"""
    
    def generate_from_dataframe(self,
                               df: pd.DataFrame,
                               output_dir: str = 'auto_infographics',
                               use_background: bool = True,
                               background_type: str = 'product_card') -> List[Dict]:
        """Генерация инфографик с подложками"""
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        results = []
        enhanced_generator = EnhancedAutoPartsGenerator(self.template_style)
        
        for idx, row in df.iterrows():
            try:
                part_data = self._row_to_part_data(row)
                
                filename = self._generate_filename(part_data, idx)
                output_path = Path(output_dir) / filename
                
                if use_background:
                    enhanced_generator.generate_with_background(
                        part_data,
                        str(output_path),
                        bg_type=background_type
                    )
                else:
                    # Используем старый метод без подложки
                    self.generator.generate(part_data, str(output_path))
                
                results.append({
                    'index': idx,
                    'filename': filename,
                    'path': str(output_path),
                    'success': True,
                    'with_background': use_background
                })
                
                print(f"✅ Создана инфографика: {filename}")
                
            except Exception as e:
                results.append({
                    'index': idx,
                    'error': str(e),
                    'success': False
                })
                print(f"❌ Ошибка в строке {idx}: {e}")
        
        return results

# ============================================================================
# 🎨 ДОПОЛНИТЕЛЬНЫЕ ВИЗУАЛЬНЫЕ УЛУЧШЕНИЯ (НОВЫЕ ФУНКЦИИ)
# ============================================================================

class AdvancedVisualEffects:
    """Расширенные визуальные эффекты для карточек автозапчастей"""
    
    @staticmethod
    def add_3d_shadow(image: Image.Image, 
                     shadow_intensity: int = 15,
                     offset: Tuple[int, int] = (5, 5)) -> Image.Image:
        """Добавление 3D тени для карточки"""
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Создаем слой тени
        shadow = Image.new('RGBA', (image.width + 20, image.height + 20), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        
        # Рисуем скругленный прямоугольник для тени
        AutoGraphicsGenerator.create_rounded_rect(
            shadow_draw,
            (offset[0] + 10, offset[1] + 10),
            (image.width - 20, image.height - 20),
            radius=20,
            fill=(0, 0, 0, shadow_intensity)
        )
        
        # Размываем тень
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=10))
        
        # Собираем финальное изображение
        final_image = Image.new('RGBA', 
                              (image.width + 20, image.height + 20),
                              (255, 255, 255, 0))
        
        # Накладываем тень
        final_image.paste(shadow, (0, 0), shadow)
        # Накладываем основное изображение
        final_image.paste(image, (10, 10), image)
        
        return final_image
    
    @staticmethod
    def add_glossy_overlay(image: Image.Image, 
                          opacity: int = 30) -> Image.Image:
        """Добавление глянцевого эффекта"""
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Создаем градиент для глянца
        overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        height = image.height
        for y in range(height // 2):
            alpha = int(opacity * (1 - y / (height // 2)))
            overlay_draw.line([(0, y), (image.width, y)], 
                            fill=(255, 255, 255, alpha))
        
        # Размываем глянцевый слой
        overlay = overlay.filter(ImageFilter.GaussianBlur(radius=3))
        
        # Накладываем
        result = Image.alpha_composite(image, overlay)
        return result
    
    @staticmethod
    def create_price_badge_enhanced(price_data: Dict, 
                                   size: Tuple[int, int] = (300, 100),
                                   style: str = 'modern') -> Image.Image:
        """Создание улучшенного бейджа цены"""
        width, height = size
        badge = Image.new('RGBA', (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(badge)
        
        # Градиентный фон
        for i in range(height):
            ratio = i / height
            r = int(41 * (1 - ratio) + 52 * ratio)
            g = int(128 * (1 - ratio) + 152 * ratio)
            b = int(185 * (1 - ratio) + 219 * ratio)
            draw.line([(0, i), (width, i)], fill=(r, g, b, 255))
        
        # Скругленные углы
        AutoGraphicsGenerator.create_rounded_rect(
            draw, (0, 0), (width, height), 15,
            outline=(255, 255, 255, 150)
        )
        
        # Текст цены
        try:
            font_large = ImageFont.truetype("arial.ttf", 32) if os.path.exists("arial.ttf") else ImageFont.load_default()
        except:
            font_large = ImageFont.load_default()
        
        draw.text((width//2, height//2 - 20), 
                 price_data.get('current', '0 ₽'),
                 fill=(255, 255, 255),
                 font=font_large,
                 anchor='mm')
        
        # Скидка
        if price_data.get('discount'):
            discount_size = (80, 30)
            discount_img = Image.new('RGBA', discount_size, (231, 76, 60, 255))
            discount_draw = ImageDraw.Draw(discount_img)
            
            AutoGraphicsGenerator.create_rounded_rect(
                discount_draw, (0, 0), discount_size, 8,
                fill=(231, 76, 60, 255)
            )
            
            discount_draw.text((discount_size[0]//2, discount_size[1]//2),
                              price_data['discount'],
                              fill=(255, 255, 255),
                              anchor='mm')
            
            # Поворачиваем бейдж скидки
            discount_img = discount_img.rotate(15, expand=True)
            badge.paste(discount_img, (width-100, 10), discount_img)
        
        return badge

class AutoLabelGenerator:
    """Генератор стикеров и меток для автозапчастей"""
    
    @staticmethod
    def create_stock_sticker(stock_type: str, 
                            size: Tuple[int, int] = (200, 60)) -> Image.Image:
        """Создание стикера наличия"""
        width, height = size
        sticker = Image.new('RGBA', (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(sticker)
        
        # Цвет в зависимости от типа
        colors = {
            'in_stock': (46, 204, 113),    # Зеленый
            'on_order': (241, 196, 15),    # Желтый
            'out_of_stock': (231, 76, 60), # Красный
            'limited': (230, 126, 34)      # Оранжевый
        }
        
        color = colors.get(stock_type, colors['in_stock'])
        
        # Создаем фигурный стикер
        points = [
            (10, 0), (width-10, 0),
            (width, height//2),
            (width-10, height),
            (10, height),
            (0, height//2)
        ]
        
        draw.polygon(points, fill=color + (220,))
        
        # Текст
        texts = {
            'in_stock': '📦 В НАЛИЧИИ',
            'on_order': '📋 ПОД ЗАКАЗ',
            'out_of_stock': '⏳ НЕТ В НАЛИЧИИ',
            'limited': '⚠️ ОГРАНИЧЕННО'
        }
        
        text = texts.get(stock_type, '📦 В НАЛИЧИИ')
        draw.text((width//2, height//2), text,
                 fill=(255, 255, 255),
                 anchor='mm')
        
        return sticker

# ============================================================================
# 🎨 ГЕНЕРАТОР СРАВНИТЕЛЬНЫХ ТАБЛИЦ
# ============================================================================

class ComparisonTableGenerator:
    """Генератор сравнительных таблиц для автозапчастей"""
    
    @staticmethod
    def create_comparison_table(parts: List[AutoPartData],
                               size: Tuple[int, int] = (1200, 800)) -> Image.Image:
        """Создание сравнительной таблицы"""
        width, height = size
        image = Image.new('RGB', (width, height), (245, 245, 245))
        draw = ImageDraw.Draw(image)
        
        # Заголовок
        draw.text((width//2, 30), "СРАВНИТЕЛЬНАЯ ТАБЛИЦА АВТОЗАПЧАСТЕЙ",
                 fill=(41, 128, 185),
                 anchor='mt',
                 font=ImageFont.load_default())
        
        # Параметры таблицы
        num_parts = min(4, len(parts))  # Максимум 4 для наглядности
        col_width = width // (num_parts + 1)
        row_height = 50
        
        # Заголовки колонок
        headers = ["ПАРАМЕТР"] + [part.brand for part in parts[:num_parts]]
        
        for i, header in enumerate(headers):
            x = i * col_width + col_width // 2
            y = 80
            
            # Фон заголовка
            AutoGraphicsGenerator.create_rounded_rect(
                draw, (i*col_width + 10, y-20),
                (col_width - 20, 40), 8,
                fill=(52, 152, 219) if i == 0 else (41, 128, 185),
                outline=(255, 255, 255)
            )
            
            draw.text((x, y), header,
                     fill=(255, 255, 255),
                     anchor='mm')
        
        # Параметры для сравнения
        parameters = [
            ("Цена", lambda p: p.price),
            ("OEM", lambda p: p.oem[:10] if p.oem else "-"),
            ("Наличие", lambda p: p.stock),
            ("Доставка", lambda p: p.delivery),
            ("Гарантия", lambda p: p.warranty),
            ("Рейтинг", lambda p: str(p.rating))
        ]
        
        # Данные таблицы
        for row_idx, (param_name, param_func) in enumerate(parameters):
            row_y = 130 + row_idx * row_height
            
            for col_idx in range(num_parts + 1):
                x = col_idx * col_width + col_width // 2
                cell_y = row_y + row_height // 2
                
                if col_idx == 0:  # Название параметра
                    # Фон строки
                    AutoGraphicsGenerator.create_rounded_rect(
                        draw, (10, row_y),
                        (col_width - 20, row_height - 10), 5,
                        fill=(240, 240, 240),
                        outline=(220, 220, 220)
                    )
                    
                    draw.text((x, cell_y), param_name,
                             fill=(44, 62, 80),
                             anchor='mm')
                else:  # Значения
                    part = parts[col_idx - 1]
                    value = param_func(part)
                    
                    # Чередующийся фон
                    bg_color = (255, 255, 255) if row_idx % 2 == 0 else (250, 250, 250)
                    
                    AutoGraphicsGenerator.create_rounded_rect(
                        draw, (col_idx*col_width + 10, row_y),
                        (col_width - 20, row_height - 10), 5,
                        fill=bg_color,
                        outline=(220, 220, 220)
                    )
                    
                    # Особое оформление для цены
                    if param_name == "Цена":
                        price_color = (231, 76, 60)  # Красный для цены
                        draw.text((x, cell_y), value,
                                 fill=price_color,
                                 anchor='mm')
                    else:
                        draw.text((x, cell_y), str(value),
                                 fill=(80, 80, 80),
                                 anchor='mm')
        
        return image

# ============================================================================
# 🎨 ДЕМОНСТРАЦИОННЫЕ ДАННЫЕ И ПРИМЕРЫ (ПОЛНАЯ ВЕРСИЯ)
# ============================================================================

def create_auto_parts_demo_data() -> pd.DataFrame:
    """Создание демонстрационных данных автозапчастей"""
    
    data = {
        'Название': [
            'Тормозные колодки передние дисковые',
            'Масляный фильтр двигателя',
            'Аккумулятор 60Ач',
            'Свеча зажигания иридиевая',
            'Амортизатор передний газомаслянный',
            'Ремень ГРМ с роликами',
            'Лампа ближнего света H7',
            'Фильтр салона угольный',
            'Щетки стеклоочистителя',
            'Диск тормозной вентилируемый'
        ],
        'Бренд': [
            'Bosch', 'Mann', 'Varta', 'NGK', 'KYB',
            'Gates', 'Osram', 'Mann', 'Bosch', 'Brembo'
        ],
        'OEM': [
            '0986AB1234', 'HU925/3X', '574012078', 'LFR6AIX-11', '334339',
            'K015631XS', '64210H7B', 'CUK2939', 'A339S', '09.9762.80'
        ],
        'Цена': ['2890', '850', '5990', '450', '4250', '7800', '890', '1250', '1290', '3950'],
        'Старая цена': ['3490', '950', '6490', '550', '4800', '8500', '1050', '1450', '1490', '4500'],
        'Категория': [
            'Тормоза', 'Фильтры', 'Аккумуляторы', 'Двигатель', 'Подвеска',
            'Двигатель', 'Электрика', 'Фильтры', 'Кузов', 'Тормоза'
        ],
        'Модель авто': [
            'Toyota Camry', 'Volkswagen Golf', 'Lada Vesta', 'Kia Rio', 'Hyundai Solaris',
            'Ford Focus', 'BMW 3 Series', 'Skoda Octavia', 'Renault Logan', 'Chevrolet Cruze'
        ],
        'Наличие': [
            'В наличии', 'Под заказ', 'В наличии', 'В наличии', 'Под заказ',
            'В наличии', 'В наличии', 'В наличии', 'В наличии', 'Под заказ'
        ],
        'Доставка': [
            '1-2 дня', '3-5 дней', '1 день', '1-2 дня', '5-7 дней',
            '2-3 дня', '1 день', '1-2 дня', '1 день', '4-6 дней'
        ],
        'Гарантия': [
            '24 месяца', '12 месяцев', '18 месяцев', '12 месяцев', '24 месяца',
            '12 месяцев', '12 месяцев', '12 месяцев', '6 месяцев', '24 месяца'
        ],
        'Рейтинг': [4.7, 4.5, 4.8, 4.6, 4.9, 4.7, 4.4, 4.5, 4.3, 4.8],
        'Отзывы': [128, 45, 89, 234, 56, 78, 123, 67, 189, 42]
    }
    
    return pd.DataFrame(data)

def demonstrate_backgrounds() -> str:
    """Демонстрация различных подложек"""
    
    print("\n" + "="*70)
    print("🎨 ДЕМОНСТРАЦИЯ ПОДЛОЖЕК ДЛЯ АВТОЗАПЧАСТЕЙ")
    print("="*70)
    
    bg_generator = AutoBackgroundGenerator()
    
    # Создаем демо директорию
    output_dir = 'backgrounds_demo'
    Path(output_dir).mkdir(exist_ok=True)
    
    # Различные типы подложек
    bg_types = [
        ('product_card', 'Карточка товара'),
        ('gradient', 'Градиентная'),
        ('pattern', 'Паттерн'),
        ('geometric', 'Геометрическая'),
        ('texture', 'Текстурная')
    ]
    
    # Различные стили
    styles = ['auto_modern', 'auto_pro', 'auto_premium', 'auto_tech']
    
    for style in styles:
        print(f"\n🔄 Стиль: {style.upper()}")
        print("-" * 40)
        
        for bg_key, bg_name in bg_types:
            try:
                if bg_key == 'pattern':
                    bg = bg_generator.create_background(
                        size=(800, 600),
                        bg_type=bg_key,
                        theme=style,
                        category='engine'
                    )
                else:
                    bg = bg_generator.create_background(
                        size=(800, 600),
                        bg_type=bg_key,
                        theme=style
                    )
                
                filename = f"{output_dir}/{style}_{bg_key}.png"
                bg.save(filename, 'PNG', quality=95)
                print(f"  ✅ {bg_name}: {filename}")
                
            except Exception as e:
                print(f"  ❌ Ошибка {bg_name}: {e}")
    
    # Создаем несколько полноценных карточек товара
    print("\n🚗 СОЗДАНИЕ ПОЛНЫХ КАРТОЧЕК С ПОДЛОЖКОЙ:")
    print("-" * 40)
    
    # Создаем тестовые данные
    test_data = AutoPartData(
        name="Тормозные колодки Brembo",
        price="2890",
        old_price="3490",
        brand="Brembo",
        oem="09.9762.80",
        category="Тормоза",
        car_model="Toyota Camry",
        stock="В наличии",
        delivery="1-2 дня",
        warranty="24 месяца",
        rating=4.7,
        reviews=128
    )
    
    for style_enum in [TemplateStyle.AUTO_MODERN, TemplateStyle.AUTO_PRO,
                      TemplateStyle.AUTO_PREMIUM, TemplateStyle.AUTO_TECH]:
        try:
            generator = EnhancedAutoPartsGenerator(style_enum)
            
            filename = f"{output_dir}/full_card_{style_enum.value}.png"
            generator.generate_with_background(
                test_data,
                filename,
                bg_type='product_card'
            )
            
            print(f"  ✅ {style_enum.value}: {filename}")
            
        except Exception as e:
            print(f"  ❌ Ошибка {style_enum.value}: {e}")
    
    print(f"\n📁 Все примеры сохранены в папке: {output_dir}/")
    print("\n🎨 ТИПЫ ПОДЛОЖЕК:")
    print("  • product_card  - Готовая карточка товара")
    print("  • gradient      - Градиентный фон")
    print("  • pattern       - Тематический паттерн")
    print("  • geometric     - Геометрические фигуры")
    print("  • texture       - Текстурированный фон")
    
    return output_dir

def demo_generation() -> pd.DataFrame:
    """Демонстрация генерации инфографик"""
    
    print("\n" + "="*70)
    print("🚗 ГЕНЕРАТОР ИНФОГРАФИК ДЛЯ АВТОЗАПЧАСТЕЙ")
    print("="*70)
    
    # Создаем демо данные
    print("\n📊 Создание демонстрационных данных...")
    df_demo = create_auto_parts_demo_data()
    
    # Сохраняем в Excel
    demo_excel = 'auto_parts_demo.xlsx'
    try:
        df_demo.to_excel(demo_excel, index=False)
        print(f"✅ Демо данные сохранены в: {demo_excel}")
    except Exception as e:
        print(f"⚠️ Не удалось сохранить Excel: {e}")
        print("Продолжаем без сохранения Excel...")
    
    # Демонстрация подложек
    demonstrate_backgrounds()
    
    # Показываем доступные стили
    print("\n🎨 ДОСТУПНЫЕ СТИЛИ ШАБЛОНОВ:")
    print("-" * 40)
    
    styles = {
        TemplateStyle.AUTO_MODERN: "Современный (для маркетплейсов)",
        TemplateStyle.AUTO_PRO: "Профессиональный (для автосервисов)",
        TemplateStyle.AUTO_PREMIUM: "Премиум (оригинальные запчасти)",
        TemplateStyle.AUTO_TECH: "Технологичный (инновационные товары)"
    }
    
    for i, (style, desc) in enumerate(styles.items(), 1):
        print(f"{i}. {style.value.upper()}: {desc}")
    
    # Генерация в разных стилях
    print("\n🚀 ГЕНЕРАЦИЯ ИНФОГРАФИК В РАЗНЫХ СТИЛЯХ...")
    
    for style in [TemplateStyle.AUTO_MODERN, TemplateStyle.AUTO_PRO,
                  TemplateStyle.AUTO_PREMIUM, TemplateStyle.AUTO_TECH]:
        print(f"\n🔄 Генерация в стиле: {style.value.upper()}")
        
        try:
            # Генерация с подложками
            generator = EnhancedAutoPartsBatchGenerator(style)
            results = generator.generate_from_dataframe(
                df_demo.head(3),  # Ограничиваем для демо
                output_dir=f'output_{style.value}',
                use_background=True,
                background_type='product_card'
            )
            
            success_count = sum(1 for r in results if r['success'])
            print(f"   ✅ Успешно создано: {success_count} инфографик с подложками")
            print(f"   📁 Папка: output_{style.value}/")
            
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
    
    # Показываем пример данных
    print("\n📋 ПРИМЕР ДАННЫХ ДЛЯ ГЕНЕРАЦИИ:")
    print("-" * 40)
    print("Обязательные поля в Excel:")
    print("  - Название (название товара)")
    print("  - Цена (текущая цена)")
    print("  - Бренд (производитель)")
    print("\nРекомендуемые поля:")
    print("  - OEM (номер запчасти)")
    print("  - Старая цена (для отображения скидки)")
    print("  - Категория (тип запчасти)")
    print("  - Модель авто (совместимость)")
    print("  - Наличие (статус на складе)")
    print("  - Доставка (сроки доставки)")
    
    # Очистка
    if os.path.exists(demo_excel):
        try:
            os.remove(demo_excel)
            print(f"\n🧹 Удален временный файл: {demo_excel}")
        except:
            pass
    
    print("\n" + "="*70)
    print("✅ ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА!")
    print("="*70)
    
    return df_demo

def fix_pil_issues() -> None:
    """Функция для исправления совместимости с PIL"""
    
    print("\n" + "="*70)
    print("🔧 ИСПРАВЛЕНИЯ СОВМЕСТИМОСТИ С PIL")
    print("="*70)
    
    fixes = [
        "✅ Использование ImageDraw.Draw для каждого изображения",
        "✅ Конвертация режимов изображений при необходимости",
        "✅ Использование кортежей RGBA для прозрачности",
        "✅ Обработка границ и заливки отдельно",
        "✅ Использование Image.alpha_composite для наложения",
        "✅ Правильное указание fill и outline параметров",
        "✅ Использование ImageFilter для эффектов",
        "✅ Конвертация в RGB перед сохранением в PNG",
    ]
    
    for fix in fixes:
        print(fix)
    
    print("\n📝 ОСНОВНЫЕ ИСПРАВЛЕНИЯ В КОДЕ:")
    print("1. Все методы draw теперь используют правильные параметры fill/outline")
    print("2. Конвертация изображений в RGBA при работе с прозрачностью")
    print("3. Исправлено создание rounded_rect с отдельной отрисовкой")
    print("4. Использование paste с маской для наложения")
    print("5. Правильное указание alpha-канала в цветах")

def demonstrate_enhanced_visualization():
    """Демонстрация улучшенной визуализации"""
    
    print("\n" + "="*80)
    print("🎨 ДЕМОНСТРАЦИЯ УЛУЧШЕННОЙ ВИЗУАЛИЗАЦИИ АВТОЗАПЧАСТЕЙ")
    print("="*80)
    
    # Создаем тестовые данные
    test_parts = [
        AutoPartData(
            name="Тормозные колодки дисковые передние Brembo",
            price="2890",
            old_price="3490",
            brand="Brembo",
            oem="09.9762.80",
            category="Тормоза",
            car_model="Toyota Camry 2015-2020",
            stock="В наличии (10 шт)",
            delivery="1-2 дня",
            warranty="24 месяца",
            rating=4.7,
            reviews=128,
            features=[
                "Керамический состав",
                "Уменьшенная пыльность",
                "Увеличенный срок службы",
                "Сертификат ECE R90",
                "Подходит для всех сезонов"
            ]
        ),
        AutoPartData(
            name="Аккумулятор Varta Silver Dynamic 60Ah",
            price="5990",
            old_price="6490",
            brand="Varta",
            oem="574012078",
            category="Аккумуляторы",
            car_model="VW Golf, Passat, Tiguan",
            stock="В наличии (5 шт)",
            delivery="1 день",
            warranty="36 месяцев",
            rating=4.8,
            reviews=89,
            features=[
                "Технология Silver",
                "Не требует обслуживания",
                "Устойчив к глубоким разрядам",
                "Емкость 60 Ач",
                "Пусковой ток 540А"
            ]
        )
    ]
    
    # Создаем директорию для демо
    demo_dir = "enhanced_visualization_demo"
    Path(demo_dir).mkdir(exist_ok=True)
    
    # 1. Демонстрация стикеров
    print("\n1. 🏷️ ДЕМОНСТРАЦИЯ СТИКЕРОВ:")
    print("-" * 40)
    
    label_gen = AutoLabelGenerator()
    
    # Создаем все типы стикеров
    stock_types = ['in_stock', 'on_order', 'out_of_stock', 'limited']
    for stock_type in stock_types:
        try:
            sticker = label_gen.create_stock_sticker(stock_type)
            sticker_filename = f"{demo_dir}/sticker_{stock_type}.png"
            sticker.save(sticker_filename, 'PNG', quality=95)
            print(f"   ✅ Стикер {stock_type}: {sticker_filename}")
        except Exception as e:
            print(f"   ❌ Ошибка стикера {stock_type}: {e}")
    
    # 2. Демонстрация сравнительных таблиц
    print("\n2. 📊 СОЗДАНИЕ СРАВНИТЕЛЬНОЙ ТАБЛИЦЫ:")
    print("-" * 40)
    
    try:
        comparison = ComparisonTableGenerator()
        table_image = comparison.create_comparison_table(test_parts)
        
        table_filename = f"{demo_dir}/comparison_table.png"
        table_image.save(table_filename, 'PNG', quality=95)
        
        print(f"   ✅ Сравнительная таблица: {table_filename}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    print(f"\n📁 Все примеры сохранены в папке: {demo_dir}/")
    
    return demo_dir

# ============================================================================
# 🎨 ГЛАВНАЯ ФУНКЦИЯ (ПОЛНАЯ ВЕРСИЯ)
# ============================================================================

def main() -> None:
    """Основная функция для использования"""
    
    # Демонстрация исправлений PIL
    fix_pil_issues()
    
    # Демонстрация генерации
    demo_generation()
    
    # Демонстрация улучшенной визуализации
    demonstrate_enhanced_visualization()
    
    print("\n" + "="*70)
    print("📖 ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ:")
    print("="*70)
    
    print("""
1. ПОДГОТОВКА ДАННЫХ:
  - Создайте Excel файл с данными автозапчастей
  - Обязательные колонки: Название, Цена, Бренд
  - Рекомендуемые колонки: OEM, Старая цена, Категория

2. ГЕНЕРАЦИЯ ИНФОГРАФИК:
  ```python
  # Импортируйте необходимые классы
  from auto_infographic import EnhancedAutoPartsBatchGenerator, TemplateStyle
  import pandas as pd

  # Загрузите данные
  df = pd.read_excel('ваши_данные.xlsx')

  # Создайте генератор
  generator = EnhancedAutoPartsBatchGenerator(TemplateStyle.AUTO_MODERN)

  # Сгенерируйте инфографики с подложками
  results = generator.generate_from_dataframe(
      df,
      output_dir='мои_инфографики',
      use_background=True,
      background_type='product_card'
  )
