import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests
from io import BytesIO
import time
import os
import base64
from datetime import datetime
import zipfile
import json
import logging
import sys
import re
from concurrent.futures import ThreadPoolExecutor
import hashlib
import tempfile
from typing import Dict, List, Any, Optional, Tuple
import warnings

# ============================
# НАСТРОЙКА ПРИЛОЖЕНИЯ
# ============================
st.set_page_config(
    page_title="🎯 Генератор Инфографики PRO v7.0",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo',
        'Report a bug': 'https://github.com/your-repo/issues',
        'About': '# Генератор Инфографики PRO\nПрофессиональный инструмент для создания продающих карточек товаров!'
    }
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('infographic_generator.log')
    ]
)
logger = logging.getLogger(__name__)

# Отключение предупреждений
warnings.filterwarnings('ignore')

# ============================
# ИНИЦИАЛИЗАЦИЯ СЕССИИ
# ============================
def init_session_state():
    """Инициализация состояния сессии"""
    defaults = {
        'df': None,
        'processed_count': 0,
        'processing_stats': {
            'total': 0,
            'success': 0,
            'failed': 0,
            'start_time': None,
            'end_time': None
        },
        'current_template': 'modern_shop',
        'column_mapping': {},
        'output_dir': 'output_infographics',
        'batch_results': [],
        'image_cache': {},
        'font_cache': {},
        'uploaded_fonts': [],
        'preview_image': None,
        'uploaded_file_name': None,
        'export_settings': {
            'format': 'PNG',
            'quality': 95,
            'resize': True,
            'target_size': 1200
        },
        'processing_settings': {
            'batch_size': 50,
            'max_workers': 4,
            'timeout': 30,
            'retry_count': 3
        },
        'text_offset_settings': {
            'top_left': {'x_offset': 0, 'y_offset': 0},
            'top_right': {'x_offset': 0, 'y_offset': 0},
            'bottom_left': {'x_offset': 0, 'y_offset': 0},
            'bottom_right': {'x_offset': 0, 'y_offset': 0}
        },
        'image_overlay_settings': {
            'enabled': False,
            'position': 'center',
            'scale': 100,
            'opacity': 100,
            'x_offset': 0,
            'y_offset': 0,
            'max_width': 30,
            'max_height': 30
        },
        'symmetrical_offsets': False,
        'font_settings': {
            'main_font': 'system_arial',
            'bold_font': 'system_arial',
            'font_size_multiplier': 1.0,
            'auto_font_selection': True
        },
        'loaded_templates': {},
        'template_files': [],
        'editing_template': False,
        'editing_template_id': None,
        'editing_template_data': {},
        'background_settings': {
            'header_background': 'gradient_blue',
            'footer_background': 'gradient_dark',
            'main_background': 'white',
            'header_height': 15,
            'footer_height': 10,
            'corner_radius': 20,
            'shadow_enabled': True,
            'border_enabled': True,
            'border_color': '#e0e0e0',
            'border_width': 2
        },
        'template_categories': {
            'all': 'Все шаблоны',
            'ecommerce': '🛒 E-commerce',
            'social': '📱 Соцсети',
            'minimal': '🌀 Минимализм',
            'premium': '💎 Премиум',
            'creative': '🎨 Креативные',
            'sale': '⚡ Распродажа'
        },
        'current_category': 'all',
        'show_advanced_backgrounds': False,
        'custom_backgrounds': {
            'header': None,
            'footer': None,
            'main': None
        },
        'sales_elements': {
            'enabled': True,
            'badges': ['best_seller', 'free_shipping'],
            'urgency': True,
            'social_proof': True,
            'price_format': 'premium'
        },
        'template_preview_size': 400,
        'app_initialized': False,
        'template_cache_initialized': False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ============================
# БИБЛИОТЕКА ФОНОВ И ГРАДИЕНТОВ
# ============================
class BackgroundLibrary:
    """Библиотека фонов для шапок, футеров и основного контента"""
    
    @staticmethod
    def get_header_backgrounds() -> Dict[str, Dict]:
        """Фоны для шапок"""
        return {
            'gradient_blue': {
                'name': '🔵 Синий градиент',
                'type': 'gradient',
                'colors': [(30, 144, 255), (0, 102, 204)],
                'direction': 'horizontal'
            },
            'gradient_purple': {
                'name': '🟣 Фиолетовый градиент',
                'type': 'gradient',
                'colors': [(147, 112, 219), (102, 51, 153)],
                'direction': 'horizontal'
            },
            'gradient_green': {
                'name': '🟢 Зеленый градиент',
                'type': 'gradient',
                'colors': [(60, 179, 113), (34, 139, 34)],
                'direction': 'horizontal'
            },
            'gradient_red': {
                'name': '🔴 Красный градиент',
                'type': 'gradient',
                'colors': [(255, 99, 71), (220, 20, 60)],
                'direction': 'horizontal'
            },
            'gradient_gold': {
                'name': '⭐ Золотой градиент',
                'type': 'gradient',
                'colors': [(255, 215, 0), (218, 165, 32)],
                'direction': 'horizontal'
            },
            'solid_dark': {
                'name': '⚫ Темный',
                'type': 'solid',
                'color': (33, 37, 41)
            },
            'solid_light': {
                'name': '⚪ Светлый',
                'type': 'solid',
                'color': (248, 249, 250)
            },
            'transparent': {
                'name': '🔸 Прозрачный',
                'type': 'transparent',
                'color': (255, 255, 255, 0)
            },
            'pattern_dots': {
                'name': '⚫ Точки',
                'type': 'pattern',
                'color': (41, 128, 185),
                'pattern': 'dots'
            }
        }
    
    @staticmethod
    def get_footer_backgrounds() -> Dict[str, Dict]:
        """Фоны для футеров"""
        return {
            'gradient_dark': {
                'name': '🌑 Темный градиент',
                'type': 'gradient',
                'colors': [(33, 37, 41), (52, 58, 64)],
                'direction': 'horizontal'
            },
            'solid_dark': {
                'name': '⚫ Темный',
                'type': 'solid',
                'color': (33, 37, 41)
            },
            'solid_gray': {
                'name': '⚪ Серый',
                'type': 'solid',
                'color': (108, 117, 125)
            },
            'gradient_blue_dark': {
                'name': '🔵 Темно-синий',
                'type': 'gradient',
                'colors': [(13, 71, 161), (21, 101, 192)],
                'direction': 'horizontal'
            },
            'transparent': {
                'name': '🔸 Прозрачный',
                'type': 'transparent',
                'color': (255, 255, 255, 0)
            }
        }
    
    @staticmethod
    def get_main_backgrounds() -> Dict[str, Dict]:
        """Фоны для основного контента"""
        return {
            'white': {
                'name': '⚪ Белый',
                'type': 'solid',
                'color': (255, 255, 255)
            },
            'light_gray': {
                'name': '🌫️ Светло-серый',
                'type': 'solid',
                'color': (248, 249, 250)
            },
            'gradient_light': {
                'name': '☁️ Светлый градиент',
                'type': 'gradient',
                'colors': [(250, 250, 250), (240, 240, 240)],
                'direction': 'vertical'
            },
            'transparent': {
                'name': '🔸 Прозрачный',
                'type': 'transparent',
                'color': (255, 255, 255, 0)
            },
            'gradient_warm': {
                'name': '🧡 Теплый градиент',
                'type': 'gradient',
                'colors': [(255, 248, 225), (255, 243, 205)],
                'direction': 'vertical'
            },
            'gradient_cool': {
                'name': '💙 Холодный градиент',
                'type': 'gradient',
                'colors': [(225, 245, 254), (179, 229, 252)],
                'direction': 'vertical'
            },
            'pattern_grid': {
                'name': '🔲 Сетка',
                'type': 'pattern',
                'color': (233, 236, 239),
                'pattern': 'grid'
            }
        }
    
    @staticmethod
    def create_gradient_background(width: int, height: int, colors: List[Tuple],
                                  direction: str = 'horizontal') -> Image.Image:
        """Создание градиентного фона"""
        if not colors:
            colors = [(255, 255, 255), (240, 240, 240)]
        
        # Убедимся, что colors содержит хотя бы один цвет
        colors = list(colors)
        if len(colors) == 0:
            colors = [(255, 255, 255)]
        
        gradient = Image.new('RGB', (width, height), colors[0])
        draw = ImageDraw.Draw(gradient)
        
        if len(colors) == 1:
            return gradient
        
        if direction == 'horizontal':
            for x in range(width):
                ratio = x / max(width - 1, 1)
                r = int(colors[0][0] * (1 - ratio) + colors[1][0] * ratio)
                g = int(colors[0][1] * (1 - ratio) + colors[1][1] * ratio)
                b = int(colors[0][2] * (1 - ratio) + colors[1][2] * ratio)
                draw.line([(x, 0), (x, height)], fill=(r, g, b))
        else:  # vertical
            for y in range(height):
                ratio = y / max(height - 1, 1)
                r = int(colors[0][0] * (1 - ratio) + colors[1][0] * ratio)
                g = int(colors[0][1] * (1 - ratio) + colors[1][1] * ratio)
                b = int(colors[0][2] * (1 - ratio) + colors[1][2] * ratio)
                draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        return gradient
    
    @staticmethod
    def create_pattern_background(width: int, height: int, pattern_type: str,
                                 color: Tuple, **kwargs) -> Image.Image:
        """Создание фона с узором"""
        bg = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(bg)
        
        if pattern_type == 'dots':
            spacing = 20
            radius = 2
            
            for x in range(0, width, spacing):
                for y in range(0, height, spacing):
                    if (x // spacing + y // spacing) % 2 == 0:
                        draw.ellipse([x, y, x + radius * 2, y + radius * 2],
                                    fill=color, outline=color)
        
        elif pattern_type == 'grid':
            spacing = 20
            
            # Вертикальные линии
            for x in range(0, width, spacing):
                draw.line([(x, 0), (x, height)], fill=color, width=1)
            
            # Горизонтальные линии
            for y in range(0, height, spacing):
                draw.line([(0, y), (width, y)], fill=color, width=1)
        
        return bg
    
    @staticmethod
    def create_background(width: int, height: int, bg_config: Dict) -> Image.Image:
        """Создание фона по конфигурации"""
        bg_type = bg_config.get('type', 'solid')
        
        try:
            if bg_type == 'gradient':
                colors = bg_config.get('colors', [(255, 255, 255), (240, 240, 240)])
                direction = bg_config.get('direction', 'horizontal')
                return BackgroundLibrary.create_gradient_background(width, height, colors, direction)
            
            elif bg_type == 'pattern':
                pattern = bg_config.get('pattern', 'dots')
                color = bg_config.get('color', (200, 200, 200))
                return BackgroundLibrary.create_pattern_background(width, height, pattern, color)
            
            elif bg_type == 'transparent':
                return Image.new('RGBA', (width, height), (255, 255, 255, 0))
            
            else:  # solid или по умолчанию
                color = bg_config.get('color', (255, 255, 255))
                return Image.new('RGB', (width, height), color)
                
        except Exception as e:
            logger.error(f"Ошибка создания фона: {e}")
            return Image.new('RGB', (width, height), (255, 255, 255))
    
    @staticmethod
    def get_background_display_name(bg_key: str, bg_type: str = 'header') -> str:
        """Получение отображаемого имени фона"""
        if bg_type == 'header':
            backgrounds = BackgroundLibrary.get_header_backgrounds()
        elif bg_type == 'footer':
            backgrounds = BackgroundLibrary.get_footer_backgrounds()
        else:
            backgrounds = BackgroundLibrary.get_main_backgrounds()
        
        if bg_key in backgrounds:
            return backgrounds[bg_key].get('name', bg_key)
        return bg_key

# ============================
# СИСТЕМА ШАБЛОНОВ С ФОНАМИ
# ============================
class DynamicTemplateManager:
    """Класс для управления динамическими шаблонами с фонами"""
    
    TEMPLATES_DIR = "templates"
    
    BUILTIN_TEMPLATES = {
        "modern_shop": {
            "name": "🛒 MODERN SHOP",
            "description": "Современный шаблон для интернет-магазина",
            "category": "ecommerce",
            "layout": {
                "header_height": 15,
                "footer_height": 10,
                "corner_radius": 20,
                "shadow": True,
                "border": True
            },
            "backgrounds": {
                "header": "gradient_blue",
                "footer": "gradient_dark",
                "main": "white"
            },
            "text_positions": {
                "header_title": {"x": 0.5, "y": 0.5, "align": "center", "max_width": 0.8},
                "product_title": {"x": 0.5, "y": 0.15, "align": "center", "max_width": 0.8},
                "price_main": {"x": 0.5, "y": 0.3, "align": "center", "max_width": 0.8},
                "price_old": {"x": 0.5, "y": 0.25, "align": "center", "max_width": 0.8},
                "benefits": {"x": 0.05, "y": 0.45, "align": "left", "max_width": 0.45},
                "features": {"x": 0.55, "y": 0.45, "align": "left", "max_width": 0.4},
                "footer_text": {"x": 0.5, "y": 0.85, "align": "center", "max_width": 0.8}
            },
            "font_sizes": {
                "header_title": 28,
                "product_title": 42,
                "price_main": 56,
                "price_old": 24,
                "benefits": 20,
                "features": 18,
                "footer_text": 16
            },
            "colors": {
                "text": [255, 255, 255, 255],
                "shadow": [0, 0, 0, 180],
                "highlight": [255, 193, 7, 255],
                "price_main": [40, 167, 69, 255],
                "price_old": [108, 117, 125, 180]
            },
            "effects": {
                "shadow": True,
                "gradient": True,
                "rounded_corners": True
            }
        }
    }
    
    @staticmethod
    def ensure_templates_dir():
        """Создание директории для шаблонов если её нет"""
        try:
            # Создаем директорию если не существует
            os.makedirs(DynamicTemplateManager.TEMPLATES_DIR, exist_ok=True)
            
            # Создаем только один основной шаблон для быстрого старта
            template_id = "modern_shop"
            filepath = os.path.join(DynamicTemplateManager.TEMPLATES_DIR, f"{template_id}.json")
            
            if not os.path.exists(filepath):
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(DynamicTemplateManager.BUILTIN_TEMPLATES[template_id], f, ensure_ascii=False, indent=2)
            
            logger.info(f"Директория шаблонов готова: {DynamicTemplateManager.TEMPLATES_DIR}")
            return True
        except Exception as e:
            logger.error(f"Ошибка создания директории шаблонов: {e}")
            return False
    
    @staticmethod
    def load_template(template_id: str) -> Dict:
        """Загрузка шаблона по ID"""
        # Проверяем кэш
        if (st.session_state.get('loaded_templates') and
            template_id in st.session_state.loaded_templates):
            return st.session_state.loaded_templates[template_id]
        
        # Пытаемся загрузить из файла
        filepath = os.path.join(DynamicTemplateManager.TEMPLATES_DIR, f"{template_id}.json")
        
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                
                # Конвертируем цвета в tuple
                if 'colors' in template_data:
                    for color_key, color_value in template_data['colors'].items():
                        if isinstance(color_value, list):
                            template_data['colors'][color_key] = tuple(color_value)
                
                template_data['id'] = template_id
                
                # Сохраняем в кэш
                if 'loaded_templates' not in st.session_state:
                    st.session_state.loaded_templates = {}
                st.session_state.loaded_templates[template_id] = template_data
                
                return template_data
            except Exception as e:
                logger.error(f"Ошибка загрузки шаблона {template_id}: {e}")
        
        # Используем встроенный шаблон если файл не найден
        return DynamicTemplateManager.BUILTIN_TEMPLATES.get("modern_shop", {}).copy()
    
    @staticmethod
    def get_template_names() -> List[Tuple[str, str]]:
        """Получение списка всех доступных шаблонов"""
        template_names = []
        
        # Всегда добавляем встроенные шаблоны
        for template_id, template_data in DynamicTemplateManager.BUILTIN_TEMPLATES.items():
            display_name = template_data.get('name', template_id)
            template_names.append((template_id, display_name))
        
        return template_names
    
    @staticmethod
    def get_templates_by_category(category: str = "all") -> List[Tuple[str, str]]:
        """Получение шаблонов по категории"""
        template_names = []
        
        for template_id, template_data in DynamicTemplateManager.BUILTIN_TEMPLATES.items():
            if category == "all" or template_data.get("category") == category:
                display_name = template_data.get('name', template_id)
                template_names.append((template_id, display_name))
        
        return template_names
    
    @staticmethod
    def get_template_categories():
        """Получение категорий шаблонов"""
        return {
            'all': 'Все шаблоны',
            'ecommerce': '🛒 E-commerce',
            'social': '📱 Соцсети',
            'minimal': '🌀 Минимализм',
            'premium': '💎 Премиум',
            'creative': '🎨 Креативные',
            'sale': '⚡ Распродажа'
        }

# ============================
# УТИЛИТЫ ДЛЯ РАБОТЫ С ИЗОБРАЖЕНИЯМИ И ШРИФТАМИ
# ============================
class FontManager:
    """Класс для управления шрифтами"""
    
    @staticmethod
    def load_font_from_file(uploaded_file) -> Tuple[Optional[str], Optional[str]]:
        """Загрузка шрифта из файла"""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.ttf') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            try:
                # Пробуем загрузить шрифт для проверки
                font = ImageFont.truetype(tmp_path, 24)
                font_name = uploaded_file.name
                font_key = hashlib.md5(uploaded_file.getvalue()).hexdigest()[:16]
                
                if 'font_cache' not in st.session_state:
                    st.session_state.font_cache = {}
                if 'uploaded_fonts' not in st.session_state:
                    st.session_state.uploaded_fonts = []
                
                font_info = {
                    'name': font_name,
                    'path': tmp_path,
                    'key': font_key,
                    'size': 24
                }
                
                st.session_state.font_cache[font_key] = font_info
                
                existing_fonts = [f['key'] for f in st.session_state.uploaded_fonts]
                if font_key not in existing_fonts:
                    st.session_state.uploaded_fonts.append(font_info)
                
                logger.info(f"Шрифт '{font_name}' загружен")
                return font_key, font_name
            except Exception as e:
                logger.error(f"Ошибка проверки шрифта: {e}")
                try:
                    os.unlink(tmp_path)
                except:
                    pass
                return None, None
        except Exception as e:
            logger.error(f"Ошибка обработки файла шрифта: {e}")
            return None, None
    
    @staticmethod
    def get_font(font_key: str, size: int) -> ImageFont.FreeTypeFont:
        """Получение шрифта по ключу с указанным размером"""
        try:
            if (st.session_state.get('font_cache') and
                font_key in st.session_state.font_cache):
                font_info = st.session_state.font_cache[font_key]
                if os.path.exists(font_info['path']):
                    return ImageFont.truetype(font_info['path'], int(size))
        except Exception as e:
            logger.error(f"Ошибка получения шрифта {font_key}: {e}")
        
        return FontManager.load_system_font('system_arial', size)
    
    @staticmethod
    def get_available_fonts() -> List[Dict]:
        """Получение списка доступных шрифтов"""
        fonts = []
        
        system_fonts = [
            {"name": "Arial (системный)", "key": "system_arial", "type": "system"},
            {"name": "Helvetica (системный)", "key": "system_helvetica", "type": "system"},
            {"name": "Times New Roman (системный)", "key": "system_times", "type": "system"}
        ]
        
        if st.session_state.get('uploaded_fonts'):
            for font_info in st.session_state.uploaded_fonts:
                fonts.append({
                    "name": f"📁 {font_info['name']}",
                    "key": font_info['key'],
                    "type": "uploaded"
                })
        
        return system_fonts + fonts
    
    @staticmethod
    def load_system_font(font_name: str, size: int) -> ImageFont.FreeTypeFont:
        """Загрузка системного шрифта"""
        try:
            # Пробуем стандартные пути
            if font_name == "system_arial":
                try:
                    return ImageFont.truetype("arial.ttf", int(size))
                except:
                    return ImageFont.load_default()
            elif font_name == "system_helvetica":
                try:
                    return ImageFont.truetype("helvetica.ttf", int(size))
                except:
                    return ImageFont.load_default()
            elif font_name == "system_times":
                try:
                    return ImageFont.truetype("times.ttf", int(size))
                except:
                    return ImageFont.load_default()
            else:
                return ImageFont.load_default()
        except Exception as e:
            logger.error(f"Ошибка загрузки системного шрифта: {e}")
            return ImageFont.load_default()

class ImageProcessor:
    """Класс для обработки изображений с поддержкой фонов"""
    
    @staticmethod
    def load_image_from_url(url: str, timeout: int = 30, retries: int = 3) -> Optional[Image.Image]:
        """Загрузка изображения по URL с повторными попытками"""
        if not url or not isinstance(url, str) or not url.strip():
            return None
        
        url = url.strip()
        
        # Проверяем кэш
        if st.session_state.get('image_cache'):
            cache_key = hashlib.md5(url.encode()).hexdigest()
            if cache_key in st.session_state.image_cache:
                cached_img = st.session_state.image_cache[cache_key]
                if cached_img is not None:
                    return cached_img.copy()
        
        for attempt in range(retries + 1):
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                }
                
                response = requests.get(url, timeout=timeout, headers=headers)
                response.raise_for_status()
                
                content_type = response.headers.get('content-type', '').lower()
                if 'image' not in content_type:
                    logger.warning(f"URL не возвращает изображение: {content_type}")
                    if attempt == retries:
                        return None
                    time.sleep(1)
                    continue
                
                img = Image.open(BytesIO(response.content))
                
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Кэшируем
                if 'image_cache' not in st.session_state:
                    st.session_state.image_cache = {}
                cache_key = hashlib.md5(url.encode()).hexdigest()
                st.session_state.image_cache[cache_key] = img.copy()
                
                logger.info(f"Изображение загружено: {url}")
                return img
                
            except Exception as e:
                logger.error(f"Ошибка загрузки изображения {url}: {e}")
                if attempt == retries:
                    return None
                time.sleep(1)
        
        return None
    
    @staticmethod
    def create_template_canvas(width: int, height: int, template_id: str = "modern_shop") -> Image.Image:
        """Создание холста шаблона с фонами"""
        template = DynamicTemplateManager.load_template(template_id)
        layout = template.get("layout", {})
        backgrounds = template.get("backgrounds", {})
        
        header_height_percent = st.session_state.background_settings.get('header_height', 15)
        footer_height_percent = st.session_state.background_settings.get('footer_height', 10)
        
        header_height = int(height * header_height_percent / 100)
        footer_height = int(height * footer_height_percent / 100)
        main_height = height - header_height - footer_height
        
        # Создаем основной холст
        canvas = Image.new('RGBA', (width, height), (255, 255, 255, 0))
        
        # Создаем фоны для разных секций
        header_bg_key = st.session_state.background_settings.get('header_background', 'gradient_blue')
        footer_bg_key = st.session_state.background_settings.get('footer_background', 'gradient_dark')
        main_bg_key = st.session_state.background_settings.get('main_background', 'white')
        
        # Получаем конфигурации фонов
        header_bgs = BackgroundLibrary.get_header_backgrounds()
        footer_bgs = BackgroundLibrary.get_footer_backgrounds()
        main_bgs = BackgroundLibrary.get_main_backgrounds()
        
        # Создаем фоны
        if header_height > 0 and header_bg_key in header_bgs:
            header_bg = BackgroundLibrary.create_background(width, header_height, header_bgs[header_bg_key])
            canvas.paste(header_bg, (0, 0))
        
        if main_height > 0 and main_bg_key in main_bgs:
            main_bg = BackgroundLibrary.create_background(width, main_height, main_bgs[main_bg_key])
            canvas.paste(main_bg, (0, header_height))
        
        if footer_height > 0 and footer_bg_key in footer_bgs:
            footer_bg = BackgroundLibrary.create_background(width, footer_height, footer_bgs[footer_bg_key])
            canvas.paste(footer_bg, (0, header_height + main_height))
        
        # Добавляем скругленные углы если нужно
        corner_radius = st.session_state.background_settings.get('corner_radius', 20)
        if corner_radius > 0:
            canvas = ImageProcessor.add_rounded_corners(canvas, corner_radius)
        
        # Добавляем тень если нужно
        if st.session_state.background_settings.get('shadow_enabled', True):
            canvas = ImageProcessor.add_shadow_effect(canvas)
        
        # Добавляем рамку если нужно
        if st.session_state.background_settings.get('border_enabled', True):
            border_color = st.session_state.background_settings.get('border_color', '#e0e0e0')
            border_width = st.session_state.background_settings.get('border_width', 2)
            canvas = ImageProcessor.add_border(canvas, border_color, border_width)
        
        return canvas
    
    @staticmethod
    def add_rounded_corners(img: Image.Image, radius: int) -> Image.Image:
        """Добавление скругленных углов"""
        if radius <= 0:
            return img
        
        mask = Image.new('L', img.size, 0)
        draw = ImageDraw.Draw(mask)
        
        width, height = img.size
        
        # Рисуем закругленные углы
        draw.rectangle([0, radius, width, height - radius], fill=255)
        draw.rectangle([radius, 0, width - radius, height], fill=255)
        
        # Закругления
        draw.pieslice([0, 0, radius * 2, radius * 2], 180, 270, fill=255)
        draw.pieslice([width - radius * 2, 0, width, radius * 2], 270, 360, fill=255)
        draw.pieslice([0, height - radius * 2, radius * 2, height], 90, 180, fill=255)
        draw.pieslice([width - radius * 2, height - radius * 2, width, height], 0, 90, fill=255)
        
        result = Image.new('RGBA', img.size, (255, 255, 255, 0))
        result.paste(img, (0, 0), mask)
        
        return result
    
    @staticmethod
    def add_shadow_effect(img: Image.Image, shadow_size: int = 10) -> Image.Image:
        """Добавление эффекта тени"""
        width, height = img.size
        
        # Создаем изображение с тенью
        shadow = Image.new('RGBA', (width + shadow_size * 2, height + shadow_size * 2), (0, 0, 0, 0))
        
        # Добавляем саму картинку
        shadow.paste(img, (shadow_size, shadow_size), img)
        
        # Добавляем размытие для тени
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=shadow_size/2))
        
        return shadow
    
    @staticmethod
    def add_border(img: Image.Image, border_color: str, border_width: int = 2) -> Image.Image:
        """Добавление рамки"""
        width, height = img.size
        
        # Создаем новое изображение с рамкой
        border_img = Image.new('RGBA', (width + border_width * 2, height + border_width * 2), (255, 255, 255, 0))
        
        # Заполняем рамку цветом
        draw = ImageDraw.Draw(border_img)
        
        # Конвертируем цвет
        if border_color.startswith('#'):
            try:
                r = int(border_color[1:3], 16)
                g = int(border_color[3:5], 16)
                b = int(border_color[5:7], 16)
                border_rgba = (r, g, b, 255)
            except:
                border_rgba = (224, 224, 224, 255)
        else:
            border_rgba = (224, 224, 224, 255)
        
        # Рисуем рамку
        draw.rectangle([0, 0, width + border_width * 2, height + border_width * 2],
                      fill=border_rgba)
        
        # Вставляем основное изображение
        border_img.paste(img, (border_width, border_width), img)
        
        return border_img
    
    @staticmethod
    def add_text_to_image(img: Image.Image, text_data: Dict, template_id: str = "modern_shop") -> Image.Image:
        """Добавление текста на изображение по шаблону"""
        try:
            template = DynamicTemplateManager.load_template(template_id)
            draw = ImageDraw.Draw(img)
            
            # Настройки шрифта
            font_settings = st.session_state.get('font_settings', {})
            main_font_key = font_settings.get('main_font', 'system_arial')
            font_size_multiplier = font_settings.get('font_size_multiplier', 1.0)
            
            # Позиции текста из шаблона
            text_positions = template.get("text_positions", {})
            
            # Высота секций
            header_height = int(img.height * st.session_state.background_settings.get('header_height', 15) / 100)
            footer_height = int(img.height * st.session_state.background_settings.get('footer_height', 10) / 100)
            main_height = img.height - header_height - footer_height
            
            # Добавляем каждый текстовый блок
            for position_key, position_config in text_positions.items():
                if position_key in text_data and text_data[position_key]:
                    text = str(text_data[position_key])
                    
                    # Позиция
                    x = position_config.get("x", 0.5) * img.width
                    y = position_config.get("y", 0.5)
                    
                    # Определяем секцию
                    section = position_config.get("section", "main")
                    if section == "header":
                        y = y * header_height
                    elif section == "footer":
                        y = header_height + main_height + y * footer_height
                    else:
                        y = header_height + y * main_height
                    
                    # Применяем смещения
                    offset_key = position_key.lower().replace("_", " ")
                    if offset_key in st.session_state.text_offset_settings:
                        offset = st.session_state.text_offset_settings[offset_key]
                        x += offset.get('x_offset', 0) * img.width / 100
                        y += offset.get('y_offset', 0) * img.height / 100
                    
                    # Размер шрифта
                    font_sizes = template.get("font_sizes", {})
                    base_size = font_sizes.get(position_key, 24)
                    font_size = int(base_size * font_size_multiplier)
                    
                    # Загружаем шрифт
                    font = FontManager.load_system_font(main_font_key, font_size)
                    
                    # Цвет текста
                    colors = template.get("colors", {})
                    text_color = colors.get(position_key, colors.get('text', (0, 0, 0, 255)))
                    
                    # Выравнивание
                    align = position_config.get("align", "left")
                    
                    # Добавляем текст
                    if align == "center":
                        draw.text((x, y), text, font=font, fill=text_color, anchor="mm")
                    else:
                        draw.text((x, y), text, font=font, fill=text_color, align=align)
            
            return img
            
        except Exception as e:
            logger.error(f"Ошибка добавления текста: {e}")
            return img
    
    @staticmethod
    def add_image_overlay(background: Image.Image, overlay: Image.Image, settings: Dict) -> Image.Image:
        """Добавление наложения изображения"""
        try:
            result = background.copy()
            
            # Масштабируем наложение
            scale = settings.get('scale', 100) / 100
            max_width = settings.get('max_width', 30) * background.width / 100
            
            # Вычисляем размер
            overlay_ratio = overlay.width / overlay.height
            new_width = min(int(max_width * scale), background.width // 2)
            new_height = int(new_width / overlay_ratio)
            
            overlay_resized = overlay.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Позиционируем
            position = settings.get('position', 'center')
            
            if position == 'center':
                x = (background.width - new_width) // 2
                y = (background.height - new_height) // 2
            elif position == 'top_left':
                x = 10
                y = 10
            elif position == 'top_right':
                x = background.width - new_width - 10
                y = 10
            elif position == 'bottom_left':
                x = 10
                y = background.height - new_height - 10
            elif position == 'bottom_right':
                x = background.width - new_width - 10
                y = background.height - new_height - 10
            else:
                x = (background.width - new_width) // 2
                y = (background.height - new_height) // 2
            
            # Применяем смещения
            x += int(settings.get('x_offset', 0) * background.width / 100)
            y += int(settings.get('y_offset', 0) * background.height / 100)
            
            # Применяем прозрачность
            opacity = settings.get('opacity', 100)
            if opacity < 100:
                alpha = overlay_resized.split()[3]
                alpha = alpha.point(lambda p: p * opacity / 100)
                overlay_resized.putalpha(alpha)
            
            # Накладываем
            result.paste(overlay_resized, (x, y), overlay_resized)
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка наложения изображения: {e}")
            return background
    
    @staticmethod
    def resize_image(img: Image.Image, target_size: int = 1200) -> Image.Image:
        """Изменение размера изображения"""
        if img is None:
            return None
        
        # Определяем максимальную сторону
        max_side = max(img.width, img.height)
        
        if max_side > target_size:
            ratio = target_size / max_side
            new_width = int(img.width * ratio)
            new_height = int(img.height * ratio)
            
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return img
    
    @staticmethod
    def save_image(img: Image.Image, filepath: str, format: str = 'PNG', quality: int = 95) -> bool:
        """Сохранение изображения"""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            if format.upper() == 'JPEG':
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                img.save(filepath, 'JPEG', quality=quality, optimize=True)
            elif format.upper() == 'WEBP':
                img.save(filepath, 'WEBP', quality=quality)
            else:
                img.save(filepath, 'PNG')
            
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения: {e}")
            return False

# ============================
# УТИЛИТЫ ДЛЯ РАБОТЫ С EXCEL
# ============================
class ExcelProcessor:
    """Класс для обработки Excel файлов"""
    
    @staticmethod
    def read_excel_file(uploaded_file) -> Optional[pd.DataFrame]:
        """Чтение Excel файла"""
        try:
            if uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file, engine='openpyxl')
            elif uploaded_file.name.endswith('.xls'):
                df = pd.read_excel(uploaded_file, engine='xlrd')
            else:
                st.error("Неподдерживаемый формат файла")
                return None
            
            # Заменяем NaN на None
            df = df.where(pd.notnull(df), None)
            
            logger.info(f"Файл загружен: {uploaded_file.name}, строк: {len(df)}")
            return df
            
        except Exception as e:
            st.error(f"Ошибка чтения файла: {str(e)}")
            logger.error(f"Ошибка чтения Excel: {e}")
            return None
    
    @staticmethod
    def get_column_suggestions(df: pd.DataFrame) -> Dict:
        """Автоподбор колонок"""
        suggestions = {
            'top_left': None,
            'top_right': None,
            'bottom_left': None,
            'bottom_right': None,
            'image_url': None,
            'filename': None
        }
        
        if df is None or df.empty:
            return suggestions
        
        column_names = [str(col).lower() for col in df.columns]
        
        # Маппинг ключевых слов
        keyword_map = {
            'top_left': ['название', 'name', 'товар', 'product', 'title'],
            'top_right': ['цена', 'price', 'стоимость', 'руб'],
            'bottom_left': ['описание', 'description', 'характеристики', 'features'],
            'bottom_right': ['скидка', 'discount', 'акция', 'sale'],
            'image_url': ['url', 'ссылка', 'image', 'картинка', 'фото'],
            'filename': ['артикул', 'sku', 'код', 'id', 'номер']
        }
        
        for position, keywords in keyword_map.items():
            for col, col_lower in zip(df.columns, column_names):
                if any(keyword in col_lower for keyword in keywords):
                    suggestions[position] = col
                    break
        
        # Если не нашли подходящие колонки, используем первые
        for position in suggestions:
            if suggestions[position] is None and len(df.columns) > 0:
                suggestions[position] = df.columns[0]
        
        return suggestions
    
    @staticmethod
    def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Оптимизация DataFrame"""
        if df is None:
            return df
        
        # Удаляем строки без URL изображений
        if 'image_url' in st.session_state.column_mapping:
            image_col = st.session_state.column_mapping['image_url']
            if image_col in df.columns:
                initial_len = len(df)
                df = df[df[image_col].notna()].copy()
                removed = initial_len - len(df)
                if removed > 0:
                    logger.info(f"Удалено {removed} строк без URL изображений")
        
        return df

# ============================
# ОСНОВНОЙ ПРОЦЕССОР
# ============================
class InfographicGenerator:
    """Основной класс для генерации инфографики"""
    
    def __init__(self):
        self.image_processor = ImageProcessor()
    
    def process_single_row(self, row: pd.Series, row_index: int) -> Dict:
        """Обработка одной строки"""
        try:
            # Получаем данные из строки
            text_data = {}
            column_mapping = st.session_state.column_mapping
            
            for position in ['top_left', 'top_right', 'bottom_left', 'bottom_right']:
                if position in column_mapping:
                    col = column_mapping[position]
                    if col in row:
                        text_data[position] = str(row[col] or '')
                    else:
                        text_data[position] = ''
            
            # URL основного изображения
            image_url = ''
            if 'image_url' in column_mapping:
                col = column_mapping['image_url']
                if col in row:
                    image_url = str(row[col] or '')
            
            if not image_url:
                return {
                    'row_index': row_index,
                    'status': 'error',
                    'message': 'Нет URL изображения'
                }
            
            # URL изображения для наложения
            overlay_url = None
            if 'overlay_image_url' in column_mapping:
                col = column_mapping['overlay_image_url']
                if col in row:
                    overlay_url = str(row[col] or '')
                    if overlay_url.lower() in ['', 'nan', 'none']:
                        overlay_url = None
            
            # Имя файла
            filename = f"item_{row_index:04d}"
            if 'filename' in column_mapping:
                col = column_mapping['filename']
                if col in row:
                    filename_source = str(row[col] or '')
                    if filename_source and filename_source.lower() not in ['', 'nan', 'none']:
                        # Очищаем имя файла
                        filename = re.sub(r'[^\w\-_\. ]', '_', filename_source)
                        filename = re.sub(r'\s+', '_', filename)
                        filename = filename[:50]  # Ограничиваем длину
            
            # Загружаем основное изображение
            main_img = self.image_processor.load_image_from_url(
                image_url,
                timeout=st.session_state.processing_settings.get('timeout', 30)
            )
            
            if main_img is None:
                return {
                    'row_index': row_index,
                    'status': 'error',
                    'message': 'Не удалось загрузить изображение'
                }
            
            # Изменяем размер если нужно
            if st.session_state.export_settings.get('resize', True):
                target_size = st.session_state.export_settings.get('target_size', 1200)
                main_img = self.image_processor.resize_image(main_img, target_size)
            
            # Создаем холст шаблона
            canvas = self.image_processor.create_template_canvas(
                main_img.width, main_img.height,
                st.session_state.current_template
            )
            
            # Вставляем основное изображение
            header_height = int(main_img.height * st.session_state.background_settings.get('header_height', 15) / 100)
            final_img = canvas.copy()
            final_img.paste(main_img, (0, header_height))
            
            # Добавляем текст
            final_img = self.image_processor.add_text_to_image(
                final_img, text_data, st.session_state.current_template
            )
            
            # Добавляем наложение если есть
            if overlay_url and st.session_state.image_overlay_settings.get('enabled', False):
                overlay_img = self.image_processor.load_image_from_url(
                    overlay_url,
                    timeout=15
                )
                
                if overlay_img:
                    final_img = self.image_processor.add_image_overlay(
                        final_img,
                        overlay_img,
                        st.session_state.image_overlay_settings
                    )
            
            # Сохраняем
            output_dir = st.session_state.get('output_dir', 'output_infographics')
            format_ext = st.session_state.export_settings.get('format', 'PNG').lower()
            filepath = os.path.join(output_dir, f"{filename}.{format_ext}")
            
            success = self.image_processor.save_image(
                final_img,
                filepath,
                format=st.session_state.export_settings.get('format', 'PNG'),
                quality=st.session_state.export_settings.get('quality', 95)
            )
            
            if success:
                return {
                    'row_index': row_index,
                    'status': 'success',
                    'filename': filename,
                    'filepath': filepath
                }
            else:
                return {
                    'row_index': row_index,
                    'status': 'error',
                    'message': 'Ошибка сохранения'
                }
                
        except Exception as e:
            logger.error(f"Ошибка обработки строки {row_index}: {e}")
            return {
                'row_index': row_index,
                'status': 'error',
                'message': str(e)[:100]
            }
    
    def process_batch(self, df: pd.DataFrame, start_idx: int, end_idx: int) -> List[Dict]:
        """Пакетная обработка"""
        results = []
        total = end_idx - start_idx + 1
        
        if total <= 0:
            return results
        
        # Создаем выходную директорию
        output_dir = st.session_state.get('output_dir', 'output_infographics')
        os.makedirs(output_dir, exist_ok=True)
        
        # Настройки многопоточности
        max_workers = min(st.session_state.processing_settings.get('max_workers', 4), total)
        max_workers = max(1, max_workers)
        
        logger.info(f"Начало обработки {total} строк, потоков: {max_workers}")
        
        # Прогресс бар
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            
            # Запускаем задачи
            for idx in range(start_idx, end_idx + 1):
                if idx >= len(df):
                    continue
                row = df.iloc[idx]
                future = executor.submit(self.process_single_row, row, idx)
                futures.append((future, idx))
            
            # Обрабатываем результаты
            completed = 0
            for future, idx in futures:
                try:
                    result = future.result(timeout=st.session_state.processing_settings.get('timeout', 30))
                    results.append(result)
                    completed += 1
                    
                    # Обновляем прогресс
                    progress = completed / total
                    progress_bar.progress(progress)
                    
                    # Обновляем статус
                    success_count = sum(1 for r in results if r.get('status') == 'success')
                    status_text.text(f"Обработано: {completed}/{total} | Успешно: {success_count}")
                    
                except Exception as e:
                    logger.error(f"Ошибка в потоке для строки {idx}: {e}")
                    results.append({
                        'row_index': idx,
                        'status': 'error',
                        'message': f'Ошибка потока: {str(e)[:50]}'
                    })
        
        logger.info(f"Обработка завершена. Успешно: {sum(1 for r in results if r.get('status') == 'success')}/{total}")
        return results
    
    def create_zip_archive(self, results: List[Dict]) -> Optional[str]:
        """Создание ZIP архива"""
        try:
            output_dir = st.session_state.get('output_dir', 'output_infographics')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_path = os.path.join(output_dir, f"infographics_{timestamp}.zip")
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Добавляем успешные изображения
                for result in results:
                    if result.get('status') == 'success' and 'filepath' in result:
                        filepath = result['filepath']
                        if os.path.exists(filepath):
                            zipf.write(filepath, os.path.basename(filepath))
            
            logger.info(f"ZIP архив создан: {zip_path}")
            return zip_path
            
        except Exception as e:
            logger.error(f"Ошибка создания ZIP: {e}")
            return None

# ============================
# ИНТЕРФЕЙС ПОЛЬЗОВАТЕЛЯ
# ============================
class UIComponents:
    """Компоненты пользовательского интерфейса"""
    
    @staticmethod
    def render_sidebar():
        """Боковая панель"""
        with st.sidebar:
            st.title("⚙️ Настройки")
            
            # Загрузка файла
            st.subheader("📁 Загрузка данных")
            uploaded_file = st.file_uploader(
                "Выберите Excel файл",
                type=['xlsx', 'xls'],
                key="file_uploader"
            )
            
            if uploaded_file:
                if (st.session_state.get('uploaded_file_name') != uploaded_file.name or
                    st.session_state.get('df') is None):
                    
                    with st.spinner("Загрузка файла..."):
                        df = ExcelProcessor.read_excel_file(uploaded_file)
                        if df is not None:
                            st.session_state.df = df
                            st.session_state.uploaded_file_name = uploaded_file.name
                            
                            # Автоподбор колонок
                            suggestions = ExcelProcessor.get_column_suggestions(df)
                            st.session_state.column_mapping = suggestions
                            
                            st.success(f"✅ Загружено {len(df)} строк")
            
            # Предпросмотр данных
            if st.session_state.get('df') is not None:
                with st.expander("👁️ Предпросмотр данных"):
                    preview_rows = st.slider("Строк", 5, 50, 10)
                    st.dataframe(st.session_state.df.head(preview_rows))
            
            # Шаблоны
            st.subheader("🎨 Шаблон")
            template_names = DynamicTemplateManager.get_template_names()
            
            if template_names:
                template_options = [name for _, name in template_names]
                template_ids = [tid for tid, _ in template_names]
                
                current_template = st.session_state.get('current_template', 'modern_shop')
                current_index = template_ids.index(current_template) if current_template in template_ids else 0
                
                selected = st.selectbox(
                    "Выберите шаблон",
                    template_options,
                    index=current_index,
                    key="template_select"
                )
                
                selected_index = template_options.index(selected)
                st.session_state.current_template = template_ids[selected_index]
            
            # Фоны
            st.subheader("🎨 Фоны")
            
            # Шапка
            header_bgs = BackgroundLibrary.get_header_backgrounds()
            header_options = [bg['name'] for bg in header_bgs.values()]
            header_keys = list(header_bgs.keys())
            
            current_header = st.session_state.background_settings.get('header_background', 'gradient_blue')
            header_idx = header_keys.index(current_header) if current_header in header_keys else 0
            
            selected_header = st.selectbox(
                "Фон шапки",
                header_options,
                index=header_idx,
                key="header_bg"
            )
            st.session_state.background_settings['header_background'] = header_keys[header_options.index(selected_header)]
            
            # Основной фон
            main_bgs = BackgroundLibrary.get_main_backgrounds()
            main_options = [bg['name'] for bg in main_bgs.values()]
            main_keys = list(main_bgs.keys())
            
            current_main = st.session_state.background_settings.get('main_background', 'white')
            main_idx = main_keys.index(current_main) if current_main in main_keys else 0
            
            selected_main = st.selectbox(
                "Основной фон",
                main_options,
                index=main_idx,
                key="main_bg"
            )
            st.session_state.background_settings['main_background'] = main_keys[main_options.index(selected_main)]
            
            # Футер
            footer_bgs = BackgroundLibrary.get_footer_backgrounds()
            footer_options = [bg['name'] for bg in footer_bgs.values()]
            footer_keys = list(footer_bgs.keys())
            
            current_footer = st.session_state.background_settings.get('footer_background', 'gradient_dark')
            footer_idx = footer_keys.index(current_footer) if current_footer in footer_keys else 0
            
            selected_footer = st.selectbox(
                "Фон футера",
                footer_options,
                index=footer_idx,
                key="footer_bg"
            )
            st.session_state.background_settings['footer_background'] = footer_keys[footer_options.index(selected_footer)]
            
            # Размеры секций
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.background_settings['header_height'] = st.slider(
                    "Высота шапки (%)",
                    0, 40, 15,
                    key="header_height"
                )
            
            with col2:
                st.session_state.background_settings['footer_height'] = st.slider(
                    "Высота футера (%)",
                    0, 40, 10,
                    key="footer_height"
                )
            
            # Эффекты
            st.session_state.background_settings['corner_radius'] = st.slider(
                "Скругление углов",
                0, 50, 20,
                key="corner_radius"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.background_settings['shadow_enabled'] = st.checkbox(
                    "Тень",
                    value=True,
                    key="shadow"
                )
            
            with col2:
                st.session_state.background_settings['border_enabled'] = st.checkbox(
                    "Рамка",
                    value=True,
                    key="border"
                )
            
            if st.session_state.background_settings['border_enabled']:
                st.session_state.background_settings['border_color'] = st.color_picker(
                    "Цвет рамки",
                    value="#e0e0e0",
                    key="border_color"
                )
                st.session_state.background_settings['border_width'] = st.slider(
                    "Толщина",
                    1, 10, 2,
                    key="border_width"
                )
            
            # Настройки экспорта
            st.subheader("💾 Экспорт")
            
            col1, col2 = st.columns(2)
            with col1:
                format_ = st.selectbox(
                    "Формат",
                    ["PNG", "JPEG", "WebP"],
                    key="export_format"
                )
                st.session_state.export_settings['format'] = format_
            
            with col2:
                quality = st.slider(
                    "Качество",
                    50, 100, 95,
                    key="export_quality"
                )
                st.session_state.export_settings['quality'] = quality
            
            st.session_state.export_settings['resize'] = st.checkbox(
                "Изменять размер",
                value=True,
                key="resize"
            )
            
            if st.session_state.export_settings['resize']:
                st.session_state.export_settings['target_size'] = st.select_slider(
                    "Макс. размер",
                    options=[800, 1200, 1600, 2000],
                    value=1200,
                    key="target_size"
                )
            
            # Настройки обработки
            st.subheader("⚡ Обработка")
            
            col1, col2 = st.columns(2)
            with col1:
                batch_size = st.select_slider(
                    "Размер партии",
                    options=[10, 25, 50, 100],
                    value=50,
                    key="batch_size"
                )
                st.session_state.processing_settings['batch_size'] = batch_size
            
            with col2:
                max_workers = st.select_slider(
                    "Потоки",
                    options=[1, 2, 4, 6],
                    value=4,
                    key="max_workers"
                )
                st.session_state.processing_settings['max_workers'] = max_workers
            
            st.session_state.processing_settings['timeout'] = st.select_slider(
                "Таймаут (сек)",
                options=[10, 15, 30, 45],
                value=30,
                key="timeout"
            )
            
            st.divider()
            st.caption(f"Обработано: {st.session_state.get('processed_count', 0)}")
            st.caption("Версия: 7.0")
    
    @staticmethod
    def render_column_mapping():
        """Настройка маппинга колонок"""
        if st.session_state.get('df') is None:
            return
        
        st.subheader("📊 Настройка колонок")
        
        available_columns = st.session_state.df.columns.tolist()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Верхний левый
            top_left_default = st.session_state.column_mapping.get('top_left', available_columns[0])
            top_left_idx = available_columns.index(top_left_default) if top_left_default in available_columns else 0
            st.session_state.column_mapping['top_left'] = st.selectbox(
                "Верхний левый",
                available_columns,
                index=top_left_idx,
                key="col_top_left"
            )
            
            # Верхний правый
            top_right_default = st.session_state.column_mapping.get('top_right', available_columns[1] if len(available_columns) > 1 else available_columns[0])
            top_right_idx = available_columns.index(top_right_default) if top_right_default in available_columns else min(1, len(available_columns)-1)
            st.session_state.column_mapping['top_right'] = st.selectbox(
                "Верхний правый",
                available_columns,
                index=top_right_idx,
                key="col_top_right"
            )
            
            # URL изображения
            image_url_default = st.session_state.column_mapping.get('image_url', available_columns[2] if len(available_columns) > 2 else available_columns[0])
            image_url_idx = available_columns.index(image_url_default) if image_url_default in available_columns else min(2, len(available_columns)-1)
            st.session_state.column_mapping['image_url'] = st.selectbox(
                "URL изображения",
                available_columns,
                index=image_url_idx,
                key="col_image_url"
            )
        
        with col2:
            # Нижний левый
            bottom_left_default = st.session_state.column_mapping.get('bottom_left', available_columns[3] if len(available_columns) > 3 else available_columns[0])
            bottom_left_idx = available_columns.index(bottom_left_default) if bottom_left_default in available_columns else min(3, len(available_columns)-1)
            st.session_state.column_mapping['bottom_left'] = st.selectbox(
                "Нижний левый",
                available_columns,
                index=bottom_left_idx,
                key="col_bottom_left"
            )
            
            # Нижний правый
            bottom_right_default = st.session_state.column_mapping.get('bottom_right', available_columns[4] if len(available_columns) > 4 else available_columns[0])
            bottom_right_idx = available_columns.index(bottom_right_default) if bottom_right_default in available_columns else min(4, len(available_columns)-1)
            st.session_state.column_mapping['bottom_right'] = st.selectbox(
                "Нижний правый",
                available_columns,
                index=bottom_right_idx,
                key="col_bottom_right"
            )
            
            # Имя файла
            filename_default = st.session_state.column_mapping.get('filename', available_columns[0])
            filename_idx = available_columns.index(filename_default) if filename_default in available_columns else 0
            st.session_state.column_mapping['filename'] = st.selectbox(
                "Имя файла",
                available_columns,
                index=filename_idx,
                key="col_filename"
            )
        
        if st.button("🔍 Автоподбор", key="auto_map"):
            suggestions = ExcelProcessor.get_column_suggestions(st.session_state.df)
            st.session_state.column_mapping = suggestions
            st.success("✅ Колонки подобраны!")
            time.sleep(1)
            st.rerun()
    
    @staticmethod
    def render_font_settings():
        """Настройки шрифтов"""
        st.subheader("🔤 Шрифты")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Загрузка шрифтов
            uploaded_fonts = st.file_uploader(
                "Загрузите шрифты (.ttf)",
                type=['ttf', 'otf'],
                accept_multiple_files=True,
                key="font_uploader"
            )
            
            if uploaded_fonts:
                for font_file in uploaded_fonts:
                    with st.spinner(f"Загрузка {font_file.name}..."):
                        font_key, font_name = FontManager.load_font_from_file(font_file)
                        if font_key:
                            st.success(f"✅ {font_name}")
        
        with col2:
            # Выбор шрифтов
            available_fonts = FontManager.get_available_fonts()
            
            if available_fonts:
                font_options = [f["name"] for f in available_fonts]
                font_keys = [f["key"] for f in available_fonts]
                
                current_font = st.session_state.font_settings.get('main_font', 'system_arial')
                current_idx = font_keys.index(current_font) if current_font in font_keys else 0
                
                selected = st.selectbox(
                    "Основной шрифт",
                    font_options,
                    index=current_idx,
                    key="main_font"
                )
                
                st.session_state.font_settings['main_font'] = font_keys[font_options.index(selected)]
                
                st.session_state.font_settings['font_size_multiplier'] = st.slider(
                    "Размер шрифта",
                    0.5, 2.0, 1.0, 0.1,
                    key="font_size"
                )
    
    @staticmethod
    def render_text_offsets():
        """Смещения текста"""
        st.subheader("🎯 Смещение текста")
        
        symmetrical = st.checkbox(
            "Симметричные смещения",
            value=st.session_state.get('symmetrical_offsets', False),
            key="symmetrical"
        )
        st.session_state.symmetrical_offsets = symmetrical
        
        if symmetrical:
            col1, col2 = st.columns(2)
            with col1:
                x_offset = st.number_input(
                    "Смещение X (%)",
                    -100, 100, 0,
                    key="sym_x"
                )
            with col2:
                y_offset = st.number_input(
                    "Смещение Y (%)",
                    -100, 100, 0,
                    key="sym_y"
                )
            
            for key in ['top_left', 'top_right', 'bottom_left', 'bottom_right']:
                st.session_state.text_offset_settings[key] = {
                    'x_offset': x_offset,
                    'y_offset': y_offset
                }
        else:
            cols = st.columns(4)
            positions = ['top_left', 'top_right', 'bottom_left', 'bottom_right']
            labels = ['↖️ Верх. левый', '↗️ Верх. правый', '↙️ Низ. левый', '↘️ Низ. правый']
            
            for i, (pos, label) in enumerate(zip(positions, labels)):
                with cols[i]:
                    st.markdown(f"**{label}**")
                    x = st.number_input(
                        "X (%)",
                        -100, 100,
                        st.session_state.text_offset_settings[pos].get('x_offset', 0),
                        key=f"offset_x_{pos}"
                    )
                    y = st.number_input(
                        "Y (%)",
                        -100, 100,
                        st.session_state.text_offset_settings[pos].get('y_offset', 0),
                        key=f"offset_y_{pos}"
                    )
                    st.session_state.text_offset_settings[pos] = {
                        'x_offset': x,
                        'y_offset': y
                    }
        
        if st.button("🔄 Сбросить", key="reset_offsets"):
            for key in ['top_left', 'top_right', 'bottom_left', 'bottom_right']:
                st.session_state.text_offset_settings[key] = {
                    'x_offset': 0,
                    'y_offset': 0
                }
            st.rerun()
    
    @staticmethod
    def render_overlay_settings():
        """Настройки наложения"""
        st.subheader("🖼️ Наложение")
        
        enabled = st.checkbox(
            "Включить наложение",
            value=st.session_state.image_overlay_settings.get('enabled', False),
            key="overlay_enabled"
        )
        st.session_state.image_overlay_settings['enabled'] = enabled
        
        if enabled:
            # Выбор колонки с изображением для наложения
            if st.session_state.get('df') is not None:
                available_columns = st.session_state.df.columns.tolist()
                
                overlay_col = st.selectbox(
                    "Колонка с изображениями",
                    ["Не использовать"] + available_columns,
                    key="overlay_column"
                )
                
                if overlay_col != "Не использовать":
                    st.session_state.column_mapping['overlay_image_url'] = overlay_col
                elif 'overlay_image_url' in st.session_state.column_mapping:
                    del st.session_state.column_mapping['overlay_image_url']
            
            # Настройки наложения
            col1, col2 = st.columns(2)
            with col1:
                position = st.selectbox(
                    "Позиция",
                    ["center", "top_left", "top_right", "bottom_left", "bottom_right"],
                    key="overlay_position"
                )
                st.session_state.image_overlay_settings['position'] = position
                
                opacity = st.slider(
                    "Прозрачность (%)",
                    0, 100, 100,
                    key="overlay_opacity"
                )
                st.session_state.image_overlay_settings['opacity'] = opacity
            
            with col2:
                scale = st.slider(
                    "Масштаб (%)",
                    10, 200, 100,
                    key="overlay_scale"
                )
                st.session_state.image_overlay_settings['scale'] = scale
                
                max_width = st.slider(
                    "Макс. ширина (% от изображения)",
                    5, 100, 30,
                    key="overlay_max_width"
                )
                st.session_state.image_overlay_settings['max_width'] = max_width
            
            # Смещения
            col1, col2 = st.columns(2)
            with col1:
                x_offset = st.number_input(
                    "Смещение X (%)",
                    -100, 100, 0,
                    key="overlay_x"
                )
                st.session_state.image_overlay_settings['x_offset'] = x_offset
            
            with col2:
                y_offset = st.number_input(
                    "Смещение Y (%)",
                    -100, 100, 0,
                    key="overlay_y"
                )
                st.session_state.image_overlay_settings['y_offset'] = y_offset

    @staticmethod
    def render_preview_tab(generator):
        """Вкладка предпросмотра"""
        if st.session_state.get('df') is None:
            st.info("📥 Загрузите Excel файл в боковой панели для начала работы")
            return
        
        st.header("🎯 Предпросмотр")
        
        # Настройки
        UIComponents.render_font_settings()
        UIComponents.render_text_offsets()
        UIComponents.render_overlay_settings()
        UIComponents.render_column_mapping()
        
        # Тестирование
        st.subheader("🧪 Тестирование")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            test_row = st.number_input(
                "Номер строки для теста",
                0, len(st.session_state.df)-1, 0,
                key="test_row"
            )
        
        with col2:
            st.write("")
            st.write("")
            test_button = st.button("🚀 Запустить тест", type="primary", use_container_width=True)
        
        if test_button:
            with st.spinner("Выполнение теста..."):
                row = st.session_state.df.iloc[test_row]
                
                # Получаем данные
                text_data = {}
                for position in ['top_left', 'top_right', 'bottom_left', 'bottom_right']:
                    if position in st.session_state.column_mapping:
                        col = st.session_state.column_mapping[position]
                        if col in row:
                            text_data[position] = str(row[col] or '')
                
                # URL изображений
                image_url = ''
                if 'image_url' in st.session_state.column_mapping:
                    col = st.session_state.column_mapping['image_url']
                    if col in row:
                        image_url = str(row[col] or '')
                
                overlay_url = None
                if ('overlay_image_url' in st.session_state.column_mapping and
                    st.session_state.image_overlay_settings.get('enabled', False)):
                    col = st.session_state.column_mapping['overlay_image_url']
                    if col in row:
                        overlay_url = str(row[col] or '')
                        if overlay_url.lower() in ['', 'nan', 'none']:
                            overlay_url = None
                
                # Показываем данные
                with st.expander("📋 Данные строки"):
                    st.json(text_data)
                    st.write(f"**URL изображения:** {image_url[:100]}..." if len(image_url) > 100 else f"**URL изображения:** {image_url}")
                    if overlay_url:
                        st.write(f"**URL наложения:** {overlay_url[:100]}..." if len(overlay_url) > 100 else f"**URL наложения:** {overlay_url}")
                
                # Обработка
                if image_url:
                    # Загружаем изображение
                    img = generator.image_processor.load_image_from_url(image_url)
                    
                    if img:
                        # Изменяем размер
                        if st.session_state.export_settings.get('resize', True):
                            target_size = st.session_state.export_settings.get('target_size', 1200)
                            img = generator.image_processor.resize_image(img, target_size)
                        
                        # Создаем холст
                        canvas = generator.image_processor.create_template_canvas(
                            img.width, img.height,
                            st.session_state.current_template
                        )
                        
                        # Вставляем изображение
                        header_height = int(img.height * st.session_state.background_settings.get('header_height', 15) / 100)
                        final_img = canvas.copy()
                        final_img.paste(img, (0, header_height))
                        
                        # Добавляем текст
                        final_img = generator.image_processor.add_text_to_image(
                            final_img, text_data, st.session_state.current_template
                        )
                        
                        # Добавляем наложение
                        if overlay_url and st.session_state.image_overlay_settings.get('enabled', False):
                            overlay_img = generator.image_processor.load_image_from_url(overlay_url)
                            if overlay_img:
                                final_img = generator.image_processor.add_image_overlay(
                                    final_img,
                                    overlay_img,
                                    st.session_state.image_overlay_settings
                                )
                        
                        # Показываем результат
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("📷 Оригинал")
                            st.image(img, use_column_width=True)
                            st.caption(f"{img.width}×{img.height}")
                        
                        with col2:
                            st.subheader("🎨 Результат")
                            st.image(final_img, use_column_width=True)
                            st.caption(f"Шаблон: {st.session_state.current_template}")
                        
                        # Кнопка скачивания
                        buffered = BytesIO()
                        format_ = st.session_state.export_settings.get('format', 'PNG')
                        
                        if format_ == 'JPEG':
                            final_img.convert('RGB').save(buffered, format='JPEG',
                                                         quality=st.session_state.export_settings.get('quality', 95))
                            mime = 'image/jpeg'
                        elif format_ == 'WEBP':
                            final_img.save(buffered, format='WEBP',
                                         quality=st.session_state.export_settings.get('quality', 95))
                            mime = 'image/webp'
                        else:
                            final_img.save(buffered, format='PNG')
                            mime = 'image/png'
                        
                        st.download_button(
                            label="💾 Скачать тестовое изображение",
                            data=buffered.getvalue(),
                            file_name=f"test_{test_row}.{format_.lower()}",
                            mime=mime,
                            use_container_width=True
                        )
                        
                        st.session_state.preview_image = final_img
                    else:
                        st.error("❌ Не удалось загрузить изображение")
                else:
                    st.warning("⚠️ Нет URL изображения в выбранной строке")

    @staticmethod
    def render_processing_tab(generator):
        """Вкладка обработки"""
        if st.session_state.get('df') is None:
            st.info("📥 Загрузите Excel файл в боковой панели для начала работы")
            return
        
        st.header("⚡ Массовая обработка")
        
        # Оптимизируем данные
        df_optimized = ExcelProcessor.optimize_dataframe(st.session_state.df)
        total_rows = len(df_optimized)
        
        if total_rows == 0:
            st.error("❌ Нет данных для обработки")
            return
        
        # Показываем информацию
        st.info(f"📊 Готово к обработке: {total_rows} строк")
        
        # Настройки диапазона
        col1, col2, col3 = st.columns(3)
        with col1:
            start_idx = st.number_input(
                "Начать с",
                0, total_rows-1, 0,
                key="start_idx"
            )
        
        with col2:
            end_idx = st.number_input(
                "Закончить на",
                start_idx, total_rows-1,
                min(start_idx + st.session_state.processing_settings.get('batch_size', 50) - 1, total_rows-1),
                key="end_idx"
            )
        
        with col3:
            st.write("")
            st.write("")
            process_button = st.button(
                "🚀 Начать обработку",
                type="primary",
                use_container_width=True,
                key="process_button"
            )
        
        batch_size = end_idx - start_idx + 1
        if batch_size > 0:
            st.success(f"✅ Будет обработано: {batch_size} строк")
        
        # Обработка
        if process_button and batch_size > 0:
            # Статистика
            st.session_state.processing_stats = {
                'total': batch_size,
                'success': 0,
                'failed': 0,
                'start_time': datetime.now(),
                'end_time': None
            }
            
            # Прогресс
            progress_bar = st.progress(0)
            status_text = st.empty()
            results_placeholder = st.empty()
            
            with st.spinner("Запуск обработки..."):
                results = generator.process_batch(df_optimized, start_idx, end_idx)
            
            # Обновляем статистику
            success_count = sum(1 for r in results if r.get('status') == 'success')
            failed_count = len(results) - success_count
            
            st.session_state.processing_stats.update({
                'success': success_count,
                'failed': failed_count,
                'end_time': datetime.now()
            })
            
            st.session_state.processed_count += success_count
            st.session_state.batch_results = results
            
            # Результаты
            with results_placeholder.container():
                st.success(f"✅ Обработка завершена!")
                
                # Метрики
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Успешно", success_count,
                             delta=f"{success_count/batch_size*100:.1f}%" if batch_size > 0 else "0%")
                
                with col2:
                    st.metric("Ошибки", failed_count,
                             delta=f"-{failed_count}" if failed_count > 0 else None)
                
                with col3:
                    if st.session_state.processing_stats['start_time'] and st.session_state.processing_stats['end_time']:
                        duration = (st.session_state.processing_stats['end_time'] -
                                  st.session_state.processing_stats['start_time']).total_seconds()
                        st.metric("Время", f"{duration:.1f} сек",
                                 delta=f"{batch_size/duration:.1f}/сек" if duration > 0 else None)
                
                # Детали ошибок
                if failed_count > 0:
                    with st.expander("📋 Ошибки", expanded=False):
                        errors = [r for r in results if r.get('status') == 'error']
                        error_df = pd.DataFrame(errors)
                        if not error_df.empty:
                            st.dataframe(error_df[['row_index', 'message']])
                
                # Архив
                if success_count > 0:
                    with st.spinner("Создание архива..."):
                        zip_path = generator.create_zip_archive(results)
                        
                        if zip_path and os.path.exists(zip_path):
                            with open(zip_path, 'rb') as f:
                                st.download_button(
                                    label="📦 Скачать ZIP архив",
                                    data=f.read(),
                                    file_name=os.path.basename(zip_path),
                                    mime="application/zip",
                                    use_container_width=True
                                )
                            
                            zip_size = os.path.getsize(zip_path) / (1024 * 1024)
                            st.info(f"📦 Размер архива: {zip_size:.2f} MB")
                        else:
                            st.error("❌ Ошибка создания архива")

    @staticmethod
    def render_statistics_tab():
        """Вкладка статистики"""
        st.header("📊 Статистика")
        
        if st.session_state.get('processed_count', 0) == 0:
            st.info("📈 Статистика появится после обработки")
            return
        
        # Общая статистика
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Всего обработано", st.session_state.get('processed_count', 0))
        
        with col2:
            if st.session_state.get('batch_results'):
                success = sum(1 for r in st.session_state.batch_results if r.get('status') == 'success')
                total = len(st.session_state.batch_results)
                rate = (success / total * 100) if total > 0 else 0
                st.metric("Успешность", f"{rate:.1f}%")
        
        with col3:
            template = DynamicTemplateManager.load_template(st.session_state.current_template)
            template_name = template.get('name', 'Неизвестно')
            st.metric("Шаблон", template_name[:15])
        
        with col4:
            st.metric("Формат", st.session_state.export_settings.get('format', 'PNG'))
        
        # Детальная статистика
        if st.session_state.get('batch_results'):
            st.subheader("📈 Детали последней обработки")
            results_df = pd.DataFrame(st.session_state.batch_results)
            
            if 'status' in results_df.columns:
                status_counts = results_df['status'].value_counts()
                col1, col2 = st.columns(2)
                with col1:
                    st.bar_chart(status_counts)
                with col2:
                    st.dataframe(status_counts)
            
            # Время обработки
            if (st.session_state.processing_stats.get('start_time') and
                st.session_state.processing_stats.get('end_time')):
                duration = (st.session_state.processing_stats['end_time'] -
                          st.session_state.processing_stats['start_time']).total_seconds()
                
                if duration > 0 and len(results_df) > 0:
                    speed = len(results_df) / duration
                    st.metric("Скорость", f"{speed:.2f} изобр/сек")

    @staticmethod
    def render_templates_tab():
        """Вкладка шаблонов"""
        st.header("🎨 Шаблоны")
        
        # Категории
        categories = DynamicTemplateManager.get_template_categories()
        category_names = list(categories.values())
        category_keys = list(categories.keys())
        
        current_category = st.session_state.get('current_category', 'all')
        current_index = category_keys.index(current_category) if current_category in category_keys else 0
        
        selected_category_name = st.selectbox(
            "Категория",
            category_names,
            index=current_index,
            key="category_select"
        )
        
        selected_category = category_keys[category_names.index(selected_category_name)]
        st.session_state.current_category = selected_category
        
        # Шаблоны в категории
        template_names = DynamicTemplateManager.get_templates_by_category(selected_category)
        
        if not template_names:
            st.info("📝 Шаблоны не найдены")
            return
        
        # Показываем шаблоны в сетке
        cols_per_row = 3
        template_ids = [tid for tid, _ in template_names]
        template_display_names = [name for _, name in template_names]
        
        for i in range(0, len(template_names), cols_per_row):
            cols = st.columns(cols_per_row)
            for col_idx, col in enumerate(cols):
                idx = i + col_idx
                if idx < len(template_names):
                    with col:
                        template_id = template_ids[idx]
                        template_name = template_display_names[idx]
                        template_data = DynamicTemplateManager.load_template(template_id)
                        
                        # Создаем превью
                        preview_width = 300
                        preview_height = 225
                        
                        try:
                            preview = ImageProcessor.create_template_canvas(
                                preview_width, preview_height, template_id
                            )
                            
                            # Добавляем текст превью
                            draw = ImageDraw.Draw(preview)
                            font = FontManager.load_system_font('system_arial', 16)
                            text = template_data.get('name', template_id)
                            
                            # Вычисляем позицию для текста
                            try:
                                # PIL 9.x.x+
                                left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
                            except:
                                # PIL 8.x.x
                                left, top, right, bottom = draw.textsize(text, font=font)
                            
                            text_width = right - left
                            text_height = bottom - top
                            
                            # Центрируем текст
                            x = (preview_width - text_width) / 2
                            y = (preview_height - text_height) / 2
                            
                            # Добавляем фон для текста
                            padding = 5
                            draw.rectangle([
                                x - padding,
                                y - padding,
                                x + text_width + padding,
                                y + text_height + padding
                            ], fill=(255, 255, 255, 200))
                            
                            # Рисуем текст
                            draw.text((x, y), text, font=font, fill=(0, 0, 0, 255))
                            
                            # Показываем превью
                            st.image(preview, use_column_width=True)
                            st.caption(template_data.get('description', 'Без описания'))
                            
                            # Кнопка выбора
                            if st.button(f"Выбрать {template_name}",
                                       key=f"select_{template_id}",
                                       use_container_width=True):
                                st.session_state.current_template = template_id
                                st.success(f"✅ Выбран шаблон: {template_name}")
                                st.rerun()
                                
                        except Exception as e:
                            st.error(f"Ошибка создания превью: {e}")

# ============================
# ОСНОВНОЙ КОД ПРИЛОЖЕНИЯ
# ============================
def initialize_application():
    """Инициализация приложения"""
    try:
        # Инициализация состояния
        init_session_state()
        
        # Создаем необходимые директории
        os.makedirs("templates", exist_ok=True)
        os.makedirs("output_infographics", exist_ok=True)
        
        # Инициализация шаблонов
        if not st.session_state.get('template_cache_initialized', False):
            with st.spinner("🔄 Инициализация шаблонов..."):
                DynamicTemplateManager.ensure_templates_dir()
                
                # Загружаем основной шаблон в кэш
                st.session_state.loaded_templates = {
                    'modern_shop': DynamicTemplateManager.BUILTIN_TEMPLATES['modern_shop']
                }
                
                st.session_state.template_cache_initialized = True
        
        # Устанавливаем флаг инициализации
        st.session_state.app_initialized = True
        return True
        
    except Exception as e:
        logger.error(f"Ошибка инициализации: {e}")
        st.error(f"Ошибка инициализации приложения: {str(e)}")
        return False

def show_main_interface():
    """Показать основной интерфейс"""
    # Заголовок
    st.title("🚀 Генератор Инфографики PRO v7.0")
    st.markdown("---")
    
    # Создаем табы
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Предпросмотр",
        "⚡ Обработка",
        "📊 Статистика",
        "🎨 Шаблоны"
    ])
    
    # Инициализируем генератор
    generator = InfographicGenerator()
    
    # Боковая панель
    UIComponents.render_sidebar()
    
    # Содержимое табов
    with tab1:
        UIComponents.render_preview_tab(generator)
    
    with tab2:
        UIComponents.render_processing_tab(generator)
    
    with tab3:
        UIComponents.render_statistics_tab()
    
    with tab4:
        UIComponents.render_templates_tab()

def main():
    """Основная функция приложения"""
    try:
        # Проверяем инициализацию
        if not st.session_state.get('app_initialized', False):
            # Показываем загрузку
            st.markdown("""
            <div style="text-align: center; padding: 100px;">
                <h1>🎯 Генератор Инфографики PRO</h1>
                <p>Инициализация системы...</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Инициализируем
            success = initialize_application()
            
            if success:
                st.rerun()
            else:
                st.error("❌ Не удалось инициализировать приложение")
                return
        else:
            # Показываем основной интерфейс
            show_main_interface()
            
    except Exception as e:
        # Критическая ошибка
        st.error(f"❌ Критическая ошибка: {str(e)}")
        logger.error(f"Ошибка в main: {e}")

# ============================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ============================
if __name__ == "__main__":
    main()
