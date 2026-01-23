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
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import tempfile
from typing import Dict, List, Any, Optional, Tuple
import warnings
import random

# ============================
# НАСТРОЙКА ПРИЛОЖЕНИЯ
# ============================
st.set_page_config(
    page_title="🎯 Генератор Инфографики PRO v8.1",
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
# УТИЛИТЫ ДЛЯ БЕЗОПАСНОГО ДОСТУПА К SESSION_STATE
# ============================
def safe_get_session_state(key, default=None):
    """Безопасное получение значения из session_state"""
    try:
        if hasattr(st.session_state, key):
            value = getattr(st.session_state, key)
            if value is not None:
                return value
    except Exception as e:
        logger.warning(f"Ошибка получения {key} из session_state: {e}")
    
    # Если ключа нет или значение None, создаем дефолтное значение
    return default

def safe_set_session_state(key, value):
    """Безопасное установка значения в session_state"""
    try:
        setattr(st.session_state, key, value)
    except Exception as e:
        logger.error(f"Ошибка установки {key} в session_state: {e}")

def ensure_session_state_initialized():
    """Гарантирует инициализацию всех необходимых атрибутов session_state"""
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
        'column_mapping': {
            'top_left': None,
            'top_right': None,
            'bottom_left': None,
            'bottom_right': None,
            'image_url': None,
            'filename': None,
            'overlay_image_url': None,
            'header_left': None,
            'header_right': None,
            'footer_left': None,
            'footer_right': None
        },
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
            'bottom_right': {'x_offset': 0, 'y_offset': 0},
            'header_left': {'x_offset': 0, 'y_offset': 0},
            'header_right': {'x_offset': 0, 'y_offset': 0},
            'footer_left': {'x_offset': 0, 'y_offset': 0},
            'footer_right': {'x_offset': 0, 'y_offset': 0}
        },
        'font_size_settings': {
            'top_left': 100,
            'top_right': 100,
            'bottom_left': 100,
            'bottom_right': 100,
            'header_left': 100,
            'header_right': 100,
            'footer_left': 100,
            'footer_right': 100
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
        'symmetrical_font_sizes': False,
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
        'template_cache_initialized': False,
        'current_batch': None,
        'current_batch_index': 0
    }
    
    for key, default_value in defaults.items():
        if not hasattr(st.session_state, key):
            safe_set_session_state(key, default_value)
        elif getattr(st.session_state, key) is None:
            safe_set_session_state(key, default_value)
        elif key == 'column_mapping' and (not isinstance(st.session_state.column_mapping, dict) or len(st.session_state.column_mapping) == 0):
            safe_set_session_state(key, default_value)

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
            
            for x in range(0, width, spacing):
                draw.line([(x, 0), (x, height)], fill=color, width=1)
            
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
                "top_left": {"x": 0.05, "y": 0.15, "align": "left", "max_width": 0.4, "section": "main"},
                "top_right": {"x": 0.95, "y": 0.15, "align": "right", "max_width": 0.4, "section": "main"},
                "bottom_left": {"x": 0.05, "y": 0.85, "align": "left", "max_width": 0.4, "section": "main"},
                "bottom_right": {"x": 0.95, "y": 0.85, "align": "right", "max_width": 0.4, "section": "main"},
                "header_left": {"x": 0.05, "y": 0.5, "align": "left", "max_width": 0.4, "section": "header"},
                "header_right": {"x": 0.95, "y": 0.5, "align": "right", "max_width": 0.4, "section": "header"},
                "footer_left": {"x": 0.05, "y": 0.5, "align": "left", "max_width": 0.4, "section": "footer"},
                "footer_right": {"x": 0.95, "y": 0.5, "align": "right", "max_width": 0.4, "section": "footer"}
            },
            "font_sizes": {
                "top_left": 32,
                "top_right": 28,
                "bottom_left": 24,
                "bottom_right": 20,
                "header_left": 24,
                "header_right": 20,
                "footer_left": 18,
                "footer_right": 16
            },
            "colors": {
                "top_left": [0, 0, 0, 255],
                "top_right": [0, 0, 0, 255],
                "bottom_left": [0, 0, 0, 255],
                "bottom_right": [0, 0, 0, 255],
                "header_left": [255, 255, 255, 255],
                "header_right": [255, 255, 255, 255],
                "footer_left": [255, 255, 255, 255],
                "footer_right": [255, 255, 255, 255]
            },
            "effects": {
                "shadow": True,
                "gradient": True,
                "rounded_corners": True
            }
        },
        "minimal_white": {
            "name": "🌀 MINIMAL WHITE",
            "description": "Минималистичный белый шаблон",
            "category": "minimal",
            "layout": {
                "header_height": 0,
                "footer_height": 0,
                "corner_radius": 10,
                "shadow": False,
                "border": True
            },
            "backgrounds": {
                "header": "transparent",
                "footer": "transparent",
                "main": "white"
            },
            "text_positions": {
                "top_left": {"x": 0.5, "y": 0.2, "align": "center", "max_width": 0.8, "section": "main"},
                "top_right": {"x": 0.5, "y": 0.35, "align": "center", "max_width": 0.8, "section": "main"},
                "bottom_left": {"x": 0.5, "y": 0.65, "align": "center", "max_width": 0.8, "section": "main"},
                "bottom_right": {"x": 0.5, "y": 0.8, "align": "center", "max_width": 0.8, "section": "main"},
                "header_left": {"x": 0.05, "y": 0.5, "align": "left", "max_width": 0.4, "section": "header"},
                "header_right": {"x": 0.95, "y": 0.5, "align": "right", "max_width": 0.4, "section": "header"},
                "footer_left": {"x": 0.05, "y": 0.5, "align": "left", "max_width": 0.4, "section": "footer"},
                "footer_right": {"x": 0.95, "y": 0.5, "align": "right", "max_width": 0.4, "section": "footer"}
            },
            "font_sizes": {
                "top_left": 36,
                "top_right": 30,
                "bottom_left": 22,
                "bottom_right": 18,
                "header_left": 20,
                "header_right": 18,
                "footer_left": 16,
                "footer_right": 14
            },
            "colors": {
                "top_left": [33, 37, 41, 255],
                "top_right": [52, 58, 64, 255],
                "bottom_left": [108, 117, 125, 255],
                "bottom_right": [73, 80, 87, 255],
                "header_left": [33, 37, 41, 255],
                "header_right": [52, 58, 64, 255],
                "footer_left": [108, 117, 125, 255],
                "footer_right": [73, 80, 87, 255]
            },
            "effects": {
                "shadow": False,
                "gradient": False,
                "rounded_corners": True
            }
        },
        "premium_gold": {
            "name": "💎 PREMIUM GOLD",
            "description": "Премиум шаблон с золотыми элементами",
            "category": "premium",
            "layout": {
                "header_height": 20,
                "footer_height": 15,
                "corner_radius": 30,
                "shadow": True,
                "border": True
            },
            "backgrounds": {
                "header": "gradient_gold",
                "footer": "solid_dark",
                "main": "gradient_warm"
            },
            "text_positions": {
                "top_left": {"x": 0.05, "y": 0.1, "align": "left", "max_width": 0.4, "section": "header"},
                "top_right": {"x": 0.95, "y": 0.1, "align": "right", "max_width": 0.4, "section": "header"},
                "bottom_left": {"x": 0.05, "y": 0.6, "align": "left", "max_width": 0.45, "section": "main"},
                "bottom_right": {"x": 0.95, "y": 0.6, "align": "right", "max_width": 0.45, "section": "main"},
                "header_left": {"x": 0.05, "y": 0.5, "align": "left", "max_width": 0.4, "section": "header"},
                "header_right": {"x": 0.95, "y": 0.5, "align": "right", "max_width": 0.4, "section": "header"},
                "footer_left": {"x": 0.05, "y": 0.5, "align": "left", "max_width": 0.4, "section": "footer"},
                "footer_right": {"x": 0.95, "y": 0.5, "align": "right", "max_width": 0.4, "section": "footer"}
            },
            "font_sizes": {
                "top_left": 40,
                "top_right": 48,
                "bottom_left": 22,
                "bottom_right": 22,
                "header_left": 28,
                "header_right": 24,
                "footer_left": 20,
                "footer_right": 18
            },
            "colors": {
                "top_left": [255, 255, 255, 255],
                "top_right": [218, 165, 32, 255],
                "bottom_left": [33, 37, 41, 255],
                "bottom_right": [33, 37, 41, 255],
                "header_left": [255, 255, 255, 255],
                "header_right": [218, 165, 32, 255],
                "footer_left": [255, 255, 255, 255],
                "footer_right": [255, 255, 255, 255]
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
            os.makedirs(DynamicTemplateManager.TEMPLATES_DIR, exist_ok=True)
            
            for template_id in DynamicTemplateManager.BUILTIN_TEMPLATES.keys():
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
        if (hasattr(st.session_state, 'loaded_templates') and
            st.session_state.loaded_templates and
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
                if not hasattr(st.session_state, 'loaded_templates'):
                    st.session_state.loaded_templates = {}
                st.session_state.loaded_templates[template_id] = template_data
                
                return template_data
            except Exception as e:
                logger.error(f"Ошибка загрузки шаблона {template_id}: {e}")
        
        # Используем встроенный шаблон если файл не найден
        if template_id in DynamicTemplateManager.BUILTIN_TEMPLATES:
            return DynamicTemplateManager.BUILTIN_TEMPLATES[template_id].copy()
        
        return DynamicTemplateManager.BUILTIN_TEMPLATES.get("modern_shop", {}).copy()
    
    @staticmethod
    def get_template_names() -> List[Tuple[str, str]]:
        """Получение списка всех доступных шаблонов"""
        template_names = []
        
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
# УЛУЧШЕННЫЙ ПРОЦЕССОР EXCEL
# ============================
class AdvancedExcelProcessor:
    """Улучшенный класс для обработки Excel файлов"""
    
    @staticmethod
    def detect_excel_format(uploaded_file) -> str:
        """Определение формата Excel файла"""
        file_name = uploaded_file.name.lower()
        
        if file_name.endswith('.xlsx'):
            return 'xlsx'
        elif file_name.endswith('.xls'):
            return 'xls'
        elif file_name.endswith('.xlsm'):
            return 'xlsm'
        elif file_name.endswith('.xlsb'):
            return 'xlsb'
        elif file_name.endswith('.ods'):
            return 'ods'
        elif file_name.endswith('.csv'):
            return 'csv'
        else:
            # Пытаемся определить по содержимому
            try:
                content = uploaded_file.getvalue()[:50]
                if b'PK' in content:  # ZIP signature (xlsx, xlsm)
                    return 'xlsx'
                elif b'\xD0\xCF\x11\xE0' in content:  # OLE2 signature (xls)
                    return 'xls'
            except:
                pass
            return 'xlsx'  # По умолчанию
    
    @staticmethod
    def read_excel_with_fallback(uploaded_file) -> Optional[pd.DataFrame]:
        """Чтение Excel файла с несколькими попытками и обработкой ошибок"""
        try:
            # Сбрасываем позицию файла
            uploaded_file.seek(0)
            
            # Определяем формат
            file_format = AdvancedExcelProcessor.detect_excel_format(uploaded_file)
            
            # Чтение в зависимости от формата
            if file_format in ['xlsx', 'xlsm']:
                try:
                    df = pd.read_excel(
                        uploaded_file,
                        engine='openpyxl',
                        dtype=str,  # Читаем все как строку
                        na_values=['', 'NA', 'NaN', 'NULL', 'None', 'null'],
                        keep_default_na=False
                    )
                except Exception as e:
                    logger.warning(f"Openpyxl не сработал: {e}, пробуем xlrd")
                    uploaded_file.seek(0)
                    df = pd.read_excel(
                        uploaded_file,
                        engine='xlrd',
                        dtype=str
                    )
            
            elif file_format == 'xls':
                try:
                    df = pd.read_excel(
                        uploaded_file,
                        engine='xlrd',
                        dtype=str
                    )
                except Exception as e:
                    logger.warning(f"Xlrd не сработал: {e}, пробуем openpyxl")
                    uploaded_file.seek(0)
                    df = pd.read_excel(
                        uploaded_file,
                        engine='openpyxl',
                        dtype=str
                    )
            
            elif file_format == 'ods':
                try:
                    # Для ODS используем odfpy
                    import odf
                    df = pd.read_excel(
                        uploaded_file,
                        engine='odf',
                        dtype=str
                    )
                except ImportError:
                    st.error("Для чтения ODS файлов установите odfpy: pip install odfpy")
                    return None
            
            elif file_format == 'csv':
                try:
                    uploaded_file.seek(0)
                    # Пробуем разные кодировки
                    encodings = ['utf-8', 'cp1251', 'latin1', 'iso-8859-1']
                    for encoding in encodings:
                        try:
                            uploaded_file.seek(0)
                            df = pd.read_csv(uploaded_file, dtype=str, encoding=encoding)
                            logger.info(f"CSV прочитан с кодировкой {encoding}")
                            break
                        except UnicodeDecodeError:
                            continue
                except Exception as e:
                    logger.error(f"Ошибка чтения CSV: {e}")
                    return None
            
            else:
                # Пробуем все доступные движки
                engines = ['openpyxl', 'xlrd', 'odf']
                for engine in engines:
                    try:
                        uploaded_file.seek(0)
                        df = pd.read_excel(uploaded_file, engine=engine, dtype=str)
                        logger.info(f"Успешно прочитано с помощью {engine}")
                        break
                    except Exception as e:
                        logger.warning(f"Движок {engine} не сработал: {e}")
                        df = None
                
                if df is None:
                    raise Exception("Не удалось прочитать файл ни одним из движков")
            
            # Базовая очистка данных
            df = AdvancedExcelProcessor.clean_dataframe(df)
            
            logger.info(f"Файл успешно загружен: {uploaded_file.name}, строк: {len(df)}, колонок: {len(df.columns)}")
            return df
            
        except Exception as e:
            logger.error(f"Критическая ошибка чтения Excel: {e}")
            st.error(f"Ошибка чтения файла: {str(e)}")
            
            # Попробуем CSV как запасной вариант
            try:
                uploaded_file.seek(0)
                if uploaded_file.name.endswith(('.csv', '.txt')):
                    df = pd.read_csv(uploaded_file, dtype=str, encoding='utf-8')
                    df = AdvancedExcelProcessor.clean_dataframe(df)
                    st.info("Файл прочитан как CSV")
                    return df
            except:
                pass
            
            return None
    
    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Очистка и нормализация DataFrame"""
        if df is None or df.empty:
            return pd.DataFrame()
        
        # Создаем копию для безопасности
        df = df.copy()
        
        # 1. Убираем пробелы в именах колонок
        df.columns = [str(col).strip() for col in df.columns]
        
        # 2. Заменяем NaN и None на пустые строки
        df = df.fillna('')
        
        # 3. Убираем лишние пробелы в строковых данных
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].apply(lambda x: str(x).strip() if isinstance(x, str) else x)
        
        # 4. Удаляем полностью пустые строки
        initial_len = len(df)
        df = df[df.astype(str).ne('').any(axis=1)].copy()
        removed_rows = initial_len - len(df)
        
        if removed_rows > 0:
            logger.info(f"Удалено {removed_rows} полностью пустых строк")
        
        # 5. Удаляем дубликаты
        initial_len = len(df)
        df = df.drop_duplicates().copy()
        removed_duplicates = initial_len - len(df)
        
        if removed_duplicates > 0:
            logger.info(f"Удалено {removed_duplicates} дубликатов")
        
        # 6. Сброс индекса
        df = df.reset_index(drop=True)
        
        return df
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> Dict:
        """Валидация DataFrame и проверка качества данных"""
        validation_result = {
            'is_valid': True,
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'empty_cells': 0,
            'url_columns': [],
            'warnings': [],
            'errors': []
        }
        
        if df is None or df.empty:
            validation_result.update({
                'is_valid': False,
                'errors': ['DataFrame пустой']
            })
            return validation_result
        
        # Проверяем наличие данных в колонках
        for col in df.columns:
            non_empty_count = df[col].astype(bool).sum()
            empty_count = len(df) - non_empty_count
            
            if empty_count > 0:
                validation_result['empty_cells'] += empty_count
            
            # Автоопределение колонок с URL
            if any(keyword in str(col).lower() for keyword in ['url', 'link', 'image', 'фото', 'картинка', 'ссылка']):
                validation_result['url_columns'].append(col)
                
                # Проверяем URL на валидность
                url_samples = df[col].head(5).dropna().tolist()
                valid_urls = 0
                for url in url_samples:
                    if isinstance(url, str) and len(url) > 10:
                        if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                            valid_urls += 1
                
                if valid_urls == 0 and len(url_samples) > 0:
                    validation_result['warnings'].append(f"Колонка '{col}' может не содержать валидные URL изображений")
        
        # Проверяем наличие критических колонок
        required_keywords = ['url', 'image', 'name', 'title', 'product']
        found_keywords = []
        
        for col in df.columns:
            col_lower = str(col).lower()
            for keyword in required_keywords:
                if keyword in col_lower and col not in found_keywords:
                    found_keywords.append(col)
        
        if len(found_keywords) == 0:
            validation_result['warnings'].append("Не найдены колонки с URL или названиями товаров")
        
        # Проверка на слишком большие файлы
        if len(df) > 10000:
            validation_result['warnings'].append(f"Файл содержит {len(df)} строк. Рекомендуется разбить на части.")
        
        if len(df.columns) > 50:
            validation_result['warnings'].append(f"Файл содержит {len(df.columns)} колонок. Возможно есть лишние данные.")
        
        return validation_result
    
    @staticmethod
    def get_intelligent_column_suggestions(df: pd.DataFrame) -> Dict:
        """Интеллектуальный подбор колонок с машинным обучением"""
        suggestions = {
            'top_left': None,
            'top_right': None,
            'bottom_left': None,
            'bottom_right': None,
            'image_url': None,
            'filename': None,
            'overlay_image_url': None,
            'header_left': None,
            'header_right': None,
            'footer_left': None,
            'footer_right': None,
            'confidence': {}  # Уверенность в каждом предположении
        }
        
        if df is None or df.empty:
            return suggestions
        
        # Анализируем каждую колонку
        column_stats = {}
        
        for col in df.columns:
            col_str = str(col).lower()
            col_data = df[col].dropna().astype(str)
            
            # Собираем статистику
            stats = {
                'name': col,
                'original_name': col,
                'has_urls': False,
                'has_text': False,
                'has_numbers': False,
                'has_dates': False,
                'unique_count': col_data.nunique(),
                'max_length': col_data.str.len().max() if not col_data.empty else 0,
                'avg_length': col_data.str.len().mean() if not col_data.empty else 0,
                'keywords': []
            }
            
            # Проверяем на URL
            url_patterns = ['.jpg', '.jpeg', '.png', '.webp', 'http://', 'https://', 'www.']
            url_count = sum(any(pattern in val.lower() for pattern in url_patterns) 
                          for val in col_data.head(20))
            
            if url_count > 5:
                stats['has_urls'] = True
                stats['keywords'].extend(['url', 'image'])
            
            # Проверяем на числа (цены)
            price_patterns = ['$', '€', '₽', 'руб', 'грн', 'цена', 'price', 'стоимость']
            price_count = sum(any(pattern in val.lower() for pattern in price_patterns) 
                            for val in col_data.head(20))
            
            # Пробуем преобразовать в числа
            try:
                numeric_data = pd.to_numeric(col_data.str.replace(r'[^\d.]', '', regex=True), errors='coerce')
                numeric_percentage = (numeric_data.notna().sum() / len(col_data)) * 100
                if numeric_percentage > 50:
                    stats['has_numbers'] = True
                    stats['keywords'].extend(['price', 'number', 'numeric'])
            except:
                pass
            
            # Проверяем на текст (названия)
            text_keywords = ['название', 'name', 'title', 'товар', 'product', 'описание', 'description']
            text_match = any(keyword in col_str for keyword in text_keywords)
            
            if text_match or stats['avg_length'] > 20:
                stats['has_text'] = True
                stats['keywords'].extend(['text', 'name', 'description'])
            
            column_stats[col] = stats
        
        # Интеллектуальный маппинг
        for col, stats in column_stats.items():
            col_lower = str(col).lower()
            confidence = 0
            
            # Определяем image_url
            if stats['has_urls']:
                suggestions['image_url'] = col
                suggestions['confidence']['image_url'] = 90
            elif any(keyword in col_lower for keyword in ['url', 'link', 'image', 'фото', 'картинка']):
                suggestions['image_url'] = col
                suggestions['confidence']['image_url'] = 70
            
            # Определяем top_left (обычно название)
            if any(keyword in col_lower for keyword in ['название', 'name', 'title', 'товар', 'product']):
                suggestions['top_left'] = col
                suggestions['confidence']['top_left'] = 85
            elif stats['has_text'] and stats['unique_count'] > len(df) * 0.7:
                suggestions['top_left'] = col
                suggestions['confidence']['top_left'] = 60
            
            # Определяем top_right (обычно цена)
            if any(keyword in col_lower for keyword in ['цена', 'price', 'стоимость', 'руб', '$', '€']):
                suggestions['top_right'] = col
                suggestions['confidence']['top_right'] = 80
            elif stats['has_numbers'] and stats['unique_count'] < len(df) * 0.3:
                suggestions['top_right'] = col
                suggestions['confidence']['top_right'] = 65
            
            # Определяем bottom_left (описание)
            if any(keyword in col_lower for keyword in ['описание', 'description', 'характеристики', 'features', 'детали']):
                suggestions['bottom_left'] = col
                suggestions['confidence']['bottom_left'] = 75
            elif stats['has_text'] and stats['avg_length'] > 50:
                suggestions['bottom_left'] = col
                suggestions['confidence']['bottom_left'] = 55
            
            # Определяем bottom_right (скидка, акция)
            if any(keyword in col_lower for keyword in ['скидка', 'discount', 'акция', 'sale', 'распродажа']):
                suggestions['bottom_right'] = col
                suggestions['confidence']['bottom_right'] = 70
            
            # Определяем filename (артикул, код)
            if any(keyword in col_lower for keyword in ['артикул', 'sku', 'код', 'id', 'номер', 'article']):
                suggestions['filename'] = col
                suggestions['confidence']['filename'] = 85
            elif stats['unique_count'] == len(df) and stats['max_length'] < 20:
                suggestions['filename'] = col
                suggestions['confidence']['filename'] = 60
            
            # Определяем header_left (тег, категория)
            if any(keyword in col_lower for keyword in ['тег', 'tag', 'категория', 'category', 'раздел', 'section']):
                suggestions['header_left'] = col
                suggestions['confidence']['header_left'] = 75
            
            # Определяем header_right (бренд, производитель)
            if any(keyword in col_lower for keyword in ['бренд', 'brand', 'производитель', 'manufacturer', 'марка']):
                suggestions['header_right'] = col
                suggestions['confidence']['header_right'] = 75
            
            # Определяем footer_left (доставка, сроки)
            if any(keyword in col_lower for keyword in ['доставка', 'delivery', 'срок', 'term', 'время', 'time']):
                suggestions['footer_left'] = col
                suggestions['confidence']['footer_left'] = 70
            
            # Определяем footer_right (рейтинг, отзывы)
            if any(keyword in col_lower for keyword in ['рейтинг', 'rating', 'отзывы', 'reviews', 'оценка', 'score']):
                suggestions['footer_right'] = col
                suggestions['confidence']['footer_right'] = 70
        
        # Заполняем пропущенные значения первыми подходящими колонками
        all_positions = ['top_left', 'top_right', 'bottom_left', 'bottom_right', 'filename', 
                        'header_left', 'header_right', 'footer_left', 'footer_right']
        
        for position in all_positions:
            if suggestions[position] is None:
                for col, stats in column_stats.items():
                    if col not in suggestions.values():
                        suggestions[position] = col
                        suggestions['confidence'][position] = 30
                        break
        
        return suggestions
    
    @staticmethod
    def preview_data_quality(df: pd.DataFrame) -> None:
        """Визуализация качества данных"""
        if df is None or df.empty:
            return
        
        st.subheader("📊 Анализ качества данных")
        
        # Основные метрики
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Всего строк", len(df))
        
        with col2:
            st.metric("Всего колонок", len(df.columns))
        
        with col3:
            non_empty = df.astype(bool).sum().sum()
            total_cells = len(df) * len(df.columns)
            fill_rate = (non_empty / total_cells * 100) if total_cells > 0 else 0
            st.metric("Заполненность", f"{fill_rate:.1f}%")
        
        with col4:
            duplicates = len(df) - len(df.drop_duplicates())
            st.metric("Дубликаты", duplicates)
        
        # Детальный анализ
        with st.expander("🔍 Детальный анализ колонок"):
            column_info = []
            
            for col in df.columns:
                col_data = df[col].dropna()
                
                info = {
                    'Колонка': col,
                    'Тип данных': str(df[col].dtype),
                    'Не пустых': len(col_data),
                    'Уникальных': col_data.nunique(),
                    'Заполненность': f"{(len(col_data) / len(df) * 100):.1f}%",
                    'Примеры': ', '.join(str(x) for x in col_data.head(3).tolist() if x) or 'Нет данных'
                }
                column_info.append(info)
            
            column_df = pd.DataFrame(column_info)
            st.dataframe(column_df, use_container_width=True)
        
        # Поиск проблем
        with st.expander("⚠️ Выявленные проблемы"):
            problems = []
            
            # Проверка на пустые колонки
            for col in df.columns:
                if df[col].isna().all() or (df[col].astype(str).str.strip() == '').all():
                    problems.append(f"Колонка '{col}' полностью пустая")
            
            # Проверка на дубликаты в ключевых колонках
            for col in df.columns:
                if any(keyword in str(col).lower() for keyword in ['id', 'sku', 'артикул', 'код']):
                    if df[col].duplicated().any():
                        problems.append(f"Колонка '{col}' содержит дубликаты")
            
            if problems:
                for problem in problems:
                    st.warning(problem)
            else:
                st.success("Критических проблем не обнаружено")
    
    @staticmethod
    def filter_invalid_urls(df: pd.DataFrame, url_column: str) -> pd.DataFrame:
        """Фильтрация строк с невалидными URL"""
        if df is None or url_column not in df.columns:
            return df
        
        initial_len = len(df)
        
        # Копируем DataFrame
        df_filtered = df.copy()
        
        # Функция проверки URL
        def is_valid_url(url):
            if pd.isna(url) or not isinstance(url, str):
                return False
            
            url_str = url.strip()
            
            # Минимальная длина
            if len(url_str) < 10:
                return False
            
            # Проверяем расширения файлов
            valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tiff']
            has_extension = any(url_str.lower().endswith(ext) for ext in valid_extensions)
            
            # Проверяем наличие протокола или стандартных паттернов
            has_protocol = url_str.startswith(('http://', 'https://', '//', 'www.'))
            
            # Проверяем на наличие домена
            has_domain = '.' in url_str and len(url_str.split('.')[-1]) >= 2
            
            return (has_extension or has_protocol) and has_domain
        
        # Фильтруем строки
        mask = df_filtered[url_column].apply(is_valid_url)
        df_filtered = df_filtered[mask].copy()
        
        removed_count = initial_len - len(df_filtered)
        
        if removed_count > 0:
            logger.info(f"Удалено {removed_count} строк с невалидными URL")
            st.warning(f"⚠️ Удалено {removed_count} строк с невалидными URL")
        
        return df_filtered
    
    @staticmethod
    def split_large_dataset(df: pd.DataFrame, max_rows: int = 1000) -> List[pd.DataFrame]:
        """Разделение больших наборов данных на части"""
        if len(df) <= max_rows:
            return [df]
        
        chunks = []
        total_chunks = (len(df) + max_rows - 1) // max_rows
        
        for i in range(total_chunks):
            start_idx = i * max_rows
            end_idx = min((i + 1) * max_rows, len(df))
            chunk = df.iloc[start_idx:end_idx].copy()
            chunks.append(chunk)
        
        logger.info(f"Набор данных разделен на {len(chunks)} частей по {max_rows} строк")
        st.info(f"📁 Данные разделены на {len(chunks)} файлов по {max_rows} строк")
        
        return chunks

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
                font = ImageFont.truetype(tmp_path, 24)
                font_name = uploaded_file.name
                font_key = hashlib.md5(uploaded_file.getvalue()).hexdigest()[:16]
                
                # Гарантируем инициализацию font_cache
                if not hasattr(st.session_state, 'font_cache'):
                    st.session_state.font_cache = {}
                
                # Гарантируем инициализацию uploaded_fonts
                if not hasattr(st.session_state, 'uploaded_fonts'):
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
            if (hasattr(st.session_state, 'font_cache') and
                st.session_state.font_cache and
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
        
        if hasattr(st.session_state, 'uploaded_fonts') and st.session_state.uploaded_fonts:
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
        if not url or not isinstance(url, str):
            return None
        
        url = url.strip()
        
        # Проверяем валидность URL
        if len(url) < 10 or not (url.startswith('http') or url.startswith('//') or '.' in url):
            logger.warning(f"Некорректный URL: {url}")
            return None
        
        # Нормализация URL
        if url.startswith('//'):
            url = 'https:' + url
        elif url.startswith('www.'):
            url = 'https://' + url
        elif not url.startswith('http'):
            url = 'https://' + url
        
        # Проверяем кэш
        if hasattr(st.session_state, 'image_cache') and st.session_state.image_cache:
            cache_key = hashlib.md5(url.encode()).hexdigest()
            if cache_key in st.session_state.image_cache:
                cached_img = st.session_state.image_cache[cache_key]
                if cached_img is not None:
                    return cached_img.copy()
        
        # Пытаемся загрузить
        for attempt in range(retries + 1):
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                    'Referer': 'https://www.google.com/'
                }
                
                # Добавляем таймаут для медленных соединений
                response = requests.get(url, timeout=timeout, headers=headers, verify=True)
                response.raise_for_status()
                
                # Проверяем, что это изображение
                content_type = response.headers.get('content-type', '').lower()
                if 'image' not in content_type:
                    # Иногда серверы не отправляют content-type, проверяем по содержимому
                    if len(response.content) < 100:
                        logger.warning(f"Слишком маленький ответ: {len(response.content)} байт")
                        continue
                    
                    # Пробуем определить по первым байтам
                    magic_numbers = {
                        b'\xff\xd8\xff': 'jpeg',
                        b'\x89PNG': 'png',
                        b'GIF8': 'gif',
                        b'RIFF': 'webp'
                    }
                    
                    is_image = False
                    content_start = response.content[:20]
                    for magic in magic_numbers:
                        if content_start.startswith(magic):
                            is_image = True
                            break
                    
                    if not is_image:
                        logger.warning(f"Не изображение: content-type={content_type}")
                        continue
                
                img = Image.open(BytesIO(response.content))
                
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Кэшируем
                if not hasattr(st.session_state, 'image_cache'):
                    st.session_state.image_cache = {}
                
                cache_key = hashlib.md5(url.encode()).hexdigest()
                st.session_state.image_cache[cache_key] = img.copy()
                
                logger.info(f"Изображение загружено: {url[:50]}...")
                return img
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Ошибка сети при загрузке {url[:50]}...: {e}")
                if attempt == retries:
                    return None
                time.sleep(1 * (attempt + 1))  # Экспоненциальная задержка
            
            except Exception as e:
                logger.error(f"Неожиданная ошибка при загрузке {url[:50]}...: {e}")
                if attempt == retries:
                    return None
                time.sleep(1)
        
        return None
    
    @staticmethod
    def create_template_canvas(width: int, height: int, template_id: str = "modern_shop") -> Image.Image:
        """Создание холста шаблона с фонами - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        try:
            template = DynamicTemplateManager.load_template(template_id)
            layout = template.get("layout", {})
            
            # Гарантируем наличие background_settings
            if not hasattr(st.session_state, 'background_settings'):
                st.session_state.background_settings = {
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
                }
            
            background_settings = st.session_state.background_settings
            
            # === КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Гарантируем, что шаблон не выходит за границы ===
            # Вычисляем высоты секций в пикселях
            header_height_percent = max(0, min(background_settings.get('header_height', 15), 100))
            footer_height_percent = max(0, min(background_settings.get('footer_height', 10), 100 - header_height_percent))
            
            # Преобразуем проценты в пиксели
            header_height = int(height * header_height_percent / 100)
            footer_height = int(height * footer_height_percent / 100)
            main_height = height - header_height - footer_height
            
            # Гарантируем, что main_height не отрицательный
            if main_height < 0:
                main_height = 0
                header_height = int(height * 0.7)  # Перераспределяем
                footer_height = height - header_height
            
            # Создаем основной холст с прозрачным фоном
            canvas = Image.new('RGBA', (width, height), (255, 255, 255, 0))
            
            # Создаем фоны для разных секций
            header_bg_key = background_settings.get('header_background', 'gradient_blue')
            footer_bg_key = background_settings.get('footer_background', 'gradient_dark')
            main_bg_key = background_settings.get('main_background', 'white')
            
            # Получаем конфигурации фонов
            header_bgs = BackgroundLibrary.get_header_backgrounds()
            footer_bgs = BackgroundLibrary.get_footer_backgrounds()
            main_bgs = BackgroundLibrary.get_main_backgrounds()
            
            # Создаем и вставляем фоны с учетом границ
            if header_height > 0 and header_bg_key in header_bgs:
                try:
                    header_bg = BackgroundLibrary.create_background(width, header_height, header_bgs[header_bg_key])
                    # Ограничиваем позицию вставки
                    canvas.paste(header_bg, (0, 0))
                except Exception as e:
                    logger.error(f"Ошибка создания фона шапки: {e}")
                    # Создаем простой фон в случае ошибки
                    header_bg = Image.new('RGB', (width, header_height), (30, 144, 255))
                    canvas.paste(header_bg, (0, 0))
            
            if main_height > 0 and main_bg_key in main_bgs:
                try:
                    main_bg = BackgroundLibrary.create_background(width, main_height, main_bgs[main_bg_key])
                    # Ограничиваем позицию вставки
                    canvas.paste(main_bg, (0, header_height))
                except Exception as e:
                    logger.error(f"Ошибка создания основного фона: {e}")
                    # Создаем простой фон в случае ошибки
                    main_bg = Image.new('RGB', (width, main_height), (255, 255, 255))
                    canvas.paste(main_bg, (0, header_height))
            
            if footer_height > 0 and footer_bg_key in footer_bgs:
                try:
                    footer_bg = BackgroundLibrary.create_background(width, footer_height, footer_bgs[footer_bg_key])
                    # Вычисляем позицию с учетом границ
                    footer_y = header_height + main_height
                    if footer_y + footer_height > height:
                        footer_y = height - footer_height  # Корректируем позицию
                    canvas.paste(footer_bg, (0, footer_y))
                except Exception as e:
                    logger.error(f"Ошибка создания фона футера: {e}")
                    # Создаем простой фон в случае ошибки
                    footer_bg = Image.new('RGB', (width, footer_height), (33, 37, 41))
                    footer_y = header_height + main_height
                    if footer_y + footer_height > height:
                        footer_y = height - footer_height
                    canvas.paste(footer_bg, (0, footer_y))
            
            # Добавляем скругленные углы если нужно
            corner_radius = background_settings.get('corner_radius', 20)
            if corner_radius > 0:
                # Ограничиваем радиус, чтобы не превышал половину меньшей стороны
                min_side = min(width, height)
                radius = min(corner_radius, min_side // 2)
                try:
                    canvas = ImageProcessor.add_rounded_corners(canvas, radius)
                except Exception as e:
                    logger.error(f"Ошибка добавления скругленных углов: {e}")
            
            # Добавляем тень если нужно (создаем новое изображение с тенью)
            if background_settings.get('shadow_enabled', True):
                try:
                    canvas = ImageProcessor.add_shadow_effect(canvas)
                except Exception as e:
                    logger.error(f"Ошибка добавления тени: {e}")
            
            # Добавляем рамку если нужно (внутри границ)
            if background_settings.get('border_enabled', True):
                try:
                    border_color = background_settings.get('border_color', '#e0e0e0')
                    border_width = background_settings.get('border_width', 2)
                    canvas = ImageProcessor.add_border(canvas, border_color, border_width)
                except Exception as e:
                    logger.error(f"Ошибка добавления рамки: {e}")
            
            logger.debug(f"Создан шаблон: {width}x{height}, шапка: {header_height}, основной: {main_height}, футер: {footer_height}")
            return canvas
            
        except Exception as e:
            logger.error(f"Критическая ошибка создания шаблона: {e}")
            # Возвращаем простой белый холст в случае ошибки
            return Image.new('RGBA', (width, height), (255, 255, 255, 255))
    
    @staticmethod
    def get_template_content_area(canvas: Image.Image) -> Tuple[int, int, int, int]:
        """Определяет область содержимого в шаблоне (где можно разместить изображение)"""
        try:
            if canvas.mode != 'RGBA':
                canvas = canvas.convert('RGBA')
            
            # Получаем альфа-канал
            alpha = canvas.getchannel('A')
            
            # Находим все непрозрачные пиксели
            opaque_pixels = []
            for y in range(canvas.height):
                for x in range(canvas.width):
                    if alpha.getpixel((x, y)) > 0:
                        opaque_pixels.append((x, y))
            
            if not opaque_pixels:
                # Если нет непрозрачных пикселей, возвращаем весь холст
                return 0, 0, canvas.width, canvas.height
            
            # Находим границы
            x_coords = [p[0] for p in opaque_pixels]
            y_coords = [p[1] for p in opaque_pixels]
            
            x1 = min(x_coords)
            y1 = min(y_coords)
            x2 = max(x_coords)
            y2 = max(y_coords)
            
            # Добавляем отступы от краев
            padding = 10
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(canvas.width, x2 + padding)
            y2 = min(canvas.height, y2 + padding)
            
            return x1, y1, x2, y2
            
        except Exception as e:
            logger.error(f"Ошибка определения области содержимого: {e}")
            # Возвращаем весь холст в случае ошибки
            return 0, 0, canvas.width, canvas.height
    
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
        """Добавление эффекта тени - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Уменьшаем размер тени для лучшего вида
        shadow_size = min(shadow_size, 15)
        
        # Создаем изображение для тени с прозрачным фоном
        shadow_width = img.width + shadow_size * 2
        shadow_height = img.height + shadow_size * 2
        shadow = Image.new('RGBA', (shadow_width, shadow_height), (0, 0, 0, 0))
        
        # Создаем черную тень (альфа канал для размытия)
        shadow_base = Image.new('RGBA', (img.width, img.height), (0, 0, 0, 80))
        
        # Вставляем тень со смещением (центрируем)
        shadow.paste(shadow_base, (shadow_size, shadow_size))
        
        # Применяем размытие - ВАЖНО: размываем всё изображение тени
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=shadow_size/2))
        
        # Создаем финальное изображение с тенью
        final_img = Image.new('RGBA', (shadow_width, shadow_height), (255, 255, 255, 0))
        
        # Вставляем тень
        final_img.paste(shadow, (0, 0), shadow)
        
        # Вставляем оригинальное изображение поверх тени - ЦЕНТРИРУЕМ
        final_img.paste(img, (shadow_size, shadow_size), img)
        
        return final_img
    
    @staticmethod
    def add_border(img: Image.Image, border_color: str, border_width: int = 2) -> Image.Image:
        """Добавление рамки внутри изображения"""
        width, height = img.size
        
        # Ограничиваем ширину рамки
        border_width = min(border_width, min(width, height) // 20)
        
        # Создаем новое изображение с рамкой (того же размера)
        border_img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
        
        # Копируем оригинальное изображение
        border_img.paste(img, (0, 0))
        
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
        
        # Рисуем рамку внутри изображения
        draw.rectangle([0, 0, width-1, height-1], outline=border_rgba, width=border_width)
        
        return border_img
    
    @staticmethod
    def add_text_to_image(img: Image.Image, text_data: Dict, template_id: str = "modern_shop") -> Image.Image:
        """Добавление текста на изображение по шаблону - ИСПРАВЛЕННАЯ ВЕРСИЯ С ДОПОЛНИТЕЛЬНЫМИ ПОЛЯМИ"""
        try:
            # Загружаем шаблон
            template = DynamicTemplateManager.load_template(template_id)
            draw = ImageDraw.Draw(img)
            
            # Настройки шрифта
            font_settings = safe_get_session_state('font_settings', {})
            main_font_key = font_settings.get('main_font', 'system_arial')
            font_size_multiplier = font_settings.get('font_size_multiplier', 1.0)
            
            # Позиции текста из шаблона
            text_positions = template.get("text_positions", {})
            
            # Высота секций в процентах
            background_settings = safe_get_session_state('background_settings', {})
            header_height_percent = max(0, min(background_settings.get('header_height', 15), 100))
            footer_height_percent = max(0, min(background_settings.get('footer_height', 10), 100 - header_height_percent))
            
            # Преобразуем проценты в пиксели
            header_height = int(img.height * header_height_percent / 100)
            footer_height = int(img.height * footer_height_percent / 100)
            main_height = img.height - header_height - footer_height
            
            # Гарантируем положительные значения
            if main_height < 0:
                main_height = img.height - header_height
                footer_height = 0
            
            # === ИСПРАВЛЕНИЕ: Определяем безопасные границы для каждой секции ===
            safe_margin = 10  # Минимальный отступ от краев
            
            # Границы для шапки
            header_safe_top = safe_margin
            header_safe_bottom = header_height - safe_margin
            
            # Границы для основной секции
            main_safe_top = header_height + safe_margin
            main_safe_bottom = header_height + main_height - safe_margin
            
            # Границы для футера
            footer_safe_top = header_height + main_height + safe_margin
            footer_safe_bottom = img.height - safe_margin
            
            # === КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Добавляем текст во все позиции, включая шапку и футер ===
            # Список всех возможных позиций текста
            all_positions = ['top_left', 'top_right', 'bottom_left', 'bottom_right',
                           'header_left', 'header_right', 'footer_left', 'footer_right']
            
            # Сначала определяем какие позиции текста заполнены
            filled_positions = []
            for position_key in all_positions:
                if position_key in text_data and text_data[position_key]:
                    text = str(text_data[position_key]).strip()
                    if text and text.lower() not in ['nan', 'none', 'null', '']:
                        filled_positions.append(position_key)
            
            if not filled_positions:
                return img  # Нет текста для добавления
            
            # Добавляем каждый текстовый блок
            for position_key in filled_positions:
                text = str(text_data[position_key]).strip()
                
                # Получаем конфигурацию позиции или используем значения по умолчанию
                if position_key in text_positions:
                    position_config = text_positions[position_key]
                else:
                    # Значения по умолчанию с учетом безопасности
                    if position_key == 'top_left':
                        position_config = {"x": 0.05, "y": 0.15, "align": "left", "max_width": 0.4, "section": "main"}
                    elif position_key == 'top_right':
                        position_config = {"x": 0.95, "y": 0.15, "align": "right", "max_width": 0.4, "section": "main"}
                    elif position_key == 'bottom_left':
                        position_config = {"x": 0.05, "y": 0.85, "align": "left", "max_width": 0.4, "section": "main"}
                    elif position_key == 'bottom_right':
                        position_config = {"x": 0.95, "y": 0.85, "align": "right", "max_width": 0.4, "section": "main"}
                    elif position_key == 'header_left':
                        position_config = {"x": 0.05, "y": 0.5, "align": "left", "max_width": 0.4, "section": "header"}
                    elif position_key == 'header_right':
                        position_config = {"x": 0.95, "y": 0.5, "align": "right", "max_width": 0.4, "section": "header"}
                    elif position_key == 'footer_left':
                        position_config = {"x": 0.05, "y": 0.5, "align": "left", "max_width": 0.4, "section": "footer"}
                    elif position_key == 'footer_right':
                        position_config = {"x": 0.95, "y": 0.5, "align": "right", "max_width": 0.4, "section": "footer"}
                    else:
                        position_config = {"x": 0.5, "y": 0.5, "align": "center", "max_width": 0.8, "section": "main"}
                
                # Определяем секцию
                section = position_config.get("section", "main")
                
                # Коэффициенты позиции (0.0-1.0)
                x_percent = max(0.0, min(1.0, position_config.get("x", 0.5)))
                y_percent = max(0.0, min(1.0, position_config.get("y", 0.5)))
                
                # === ИСПРАВЛЕНИЕ: Правильное вычисление позиции для каждой секции ===
                if section == "header":
                    if header_height > 10:  # Только если шапка достаточно большая
                        # Вычисляем позицию внутри шапки
                        section_y_range = header_safe_bottom - header_safe_top
                        if section_y_range > 0:
                            y = header_safe_top + (y_percent * section_y_range)
                        else:
                            y = header_safe_top
                        
                        # Ограничиваем по вертикали в пределах шапки
                        y = max(header_safe_top, min(y, header_safe_bottom))
                    else:
                        # Если шапка маленькая, пропускаем текст в шапке
                        continue
                
                elif section == "footer":
                    if footer_height > 10:  # Только если футер достаточно большой
                        # Вычисляем позицию внутри футера
                        section_y_range = footer_safe_bottom - footer_safe_top
                        if section_y_range > 0:
                            y = footer_safe_top + (y_percent * section_y_range)
                        else:
                            y = footer_safe_top
                        
                        # Ограничиваем по вертикали в пределах футера
                        y = max(footer_safe_top, min(y, footer_safe_bottom))
                    else:
                        # Если футер маленький, пропускаем текст в футере
                        continue
                
                else:  # section == "main" или по умолчанию
                    # Вычисляем позицию внутри основной секции
                    section_y_range = main_safe_bottom - main_safe_top
                    if section_y_range > 0:
                        y = main_safe_top + (y_percent * section_y_range)
                    else:
                        y = main_safe_top
                    
                    # Ограничиваем по вертикали в пределах основной секции
                    y = max(main_safe_top, min(y, main_safe_bottom))
                
                # Вычисляем горизонтальную позицию
                x = x_percent * img.width
                
                # Применяем смещения из настроек
                text_offset_settings = safe_get_session_state('text_offset_settings', {})
                if position_key in text_offset_settings:
                    offset = text_offset_settings[position_key]
                    x += offset.get('x_offset', 0) * img.width / 100
                    y += offset.get('y_offset', 0) * img.height / 100
                
                # === ИСПРАВЛЕНИЕ: Гарантируем, что текст не выходит за границы ===
                # Определяем безопасные границы по горизонтали
                safe_left = safe_margin
                safe_right = img.width - safe_margin
                
                # Ограничиваем позицию безопасными границами
                x = max(safe_left, min(x, safe_right))
                
                # Определяем выравнивание
                align = position_config.get("align", "center")
                
                # === ДОПОЛНЕНИЕ: Получаем настройки размера шрифта ===
                # Базовый размер из шаблона
                font_sizes = template.get("font_sizes", {})
                base_size = font_sizes.get(position_key, 24)
                
                # Настройки масштаба шрифта из session_state
                font_size_settings = safe_get_session_state('font_size_settings', {})
                size_percentage = font_size_settings.get(position_key, 100) / 100.0
                
                # Общий множитель размера шрифта
                font_size_multiplier = font_settings.get('font_size_multiplier', 1.0)
                
                # Вычисляем итоговый размер шрифта
                font_size = int(base_size * size_percentage * font_size_multiplier)
                
                # Динамический размер шрифта с ограничениями
                min_font_size = 8
                max_font_size = min(img.width, img.height) // 10
                font_size = max(min_font_size, min(font_size, max_font_size))
                
                # Загружаем шрифт
                try:
                    font = FontManager.get_font(main_font_key, font_size)
                except:
                    font = FontManager.load_system_font('system_arial', font_size)
                
                # Цвет текста
                colors = template.get("colors", {})
                if position_key in colors:
                    text_color = colors[position_key]
                    if isinstance(text_color, list):
                        text_color = tuple(text_color)
                else:
                    text_color = (0, 0, 0, 255)  # Черный по умолчанию
                
                # Проверяем размер текста
                try:
                    # Получаем размеры текста (для разных версий PIL)
                    if hasattr(draw, 'textbbox'):  # PIL 9.x.x+
                        bbox = draw.textbbox((0, 0), text, font=font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                    else:  # PIL 8.x.x
                        text_width, text_height = draw.textsize(text, font=font)
                    
                    # Корректируем позицию в зависимости от выравнивания
                    if align == "center":
                        half_width = text_width // 2
                        if x - half_width < safe_left:
                            x = safe_left + half_width
                        elif x + half_width > safe_right:
                            x = safe_right - half_width
                    
                    elif align == "right":
                        if x - text_width < safe_left:
                            x = safe_left + text_width
                        if x > safe_right:
                            x = safe_right
                    
                    else:  # left
                        if x + text_width > safe_right:
                            x = safe_right - text_width
                        if x < safe_left:
                            x = safe_left
                    
                    # Проверяем вертикальные границы
                    if y - text_height/2 < safe_margin:
                        y = safe_margin + text_height/2
                    if y + text_height/2 > img.height - safe_margin:
                        y = img.height - safe_margin - text_height/2
                    
                except Exception as e:
                    logger.warning(f"Ошибка проверки размера текста '{text}': {e}")
                
                # === ВАЖНОЕ ИСПРАВЛЕНИЕ: Добавляем текст с правильным anchor ===
                try:
                    if align == "center":
                        # anchor="mm" - центр текста по x и y
                        draw.text((x, y), text, font=font, fill=text_color, anchor="mm")
                    elif align == "right":
                        # anchor="rm" - правый край по x, центр по y
                        draw.text((x, y), text, font=font, fill=text_color, anchor="rm")
                    else:  # left
                        # anchor="lm" - левый край по x, центр по y
                        draw.text((x, y), text, font=font, fill=text_color, anchor="lm")
                    
                    logger.debug(f"Текст добавлен: {position_key} = '{text[:30]}...' at ({x:.1f},{y:.1f}), размер: {font_size}")
                    
                except Exception as e:
                    logger.error(f"Ошибка добавления текста '{text[:30]}...': {e}")
                    # Пробуем альтернативный метод
                    try:
                        draw.text((x, y), text, font=font, fill=text_color)
                    except:
                        pass
            
            return img
            
        except Exception as e:
            logger.error(f"Критическая ошибка добавления текста: {e}")
            return img
    
    @staticmethod
    def add_image_overlay(background: Image.Image, overlay: Image.Image, settings: Dict) -> Image.Image:
        """Добавление наложения изображения"""
        try:
            result = background.copy()
            
            # Масштабируем наложение
            scale = settings.get('scale', 100) / 100
            max_width_percent = settings.get('max_width', 30)
            max_height_percent = settings.get('max_height', 30)
            
            max_width = max_width_percent * background.width / 100
            max_height = max_height_percent * background.height / 100
            
            # Вычисляем размер
            overlay_ratio = overlay.width / overlay.height
            new_width = min(int(max_width * scale), background.width // 2)
            new_height = int(new_width / overlay_ratio)
            
            # Ограничиваем высоту
            if new_height > max_height:
                new_height = int(max_height)
                new_width = int(new_height * overlay_ratio)
            
            # Ограничиваем минимальный размер
            new_width = max(10, new_width)
            new_height = max(10, new_height)
            
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
            
            # Ограничиваем позицию, чтобы не выходило за границы
            x = max(0, min(x, background.width - new_width))
            y = max(0, min(y, background.height - new_height))
            
            # Применяем прозрачность
            opacity = settings.get('opacity', 100)
            if opacity < 100:
                alpha = overlay_resized.split()[3]
                alpha = alpha.point(lambda p: p * opacity / 100)
                overlay_resized.putalpha(alpha)
            
            # Накладываем
            result.paste(overlay_resized, (int(x), int(y)), overlay_resized)
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка наложения изображения: {e}")
            return background
    
    @staticmethod
    def resize_image(img: Image.Image, target_size: int = 1200) -> Image.Image:
        """Изменение размера изображения с сохранением пропорций"""
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
# ОСНОВНОЙ ПРОЦЕССОР С ПРАВИЛЬНЫМИ ГРАНИЦАМИ ШАБЛОНА
# ============================
class InfographicGenerator:
    """Основной класс для генерации инфографики"""
    
    def __init__(self):
        self.image_processor = ImageProcessor()
    
    @staticmethod
    def validate_row_data(row: pd.Series, column_mapping: Dict) -> Dict:
        """Валидация данных строки перед обработкой"""
        validation = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Проверка URL изображения
        if 'image_url' in column_mapping and column_mapping['image_url']:
            url_col = column_mapping['image_url']
            if url_col in row:
                url = row[url_col]
                if pd.isna(url) or not isinstance(url, str) or len(str(url).strip()) < 10:
                    validation['is_valid'] = False
                    validation['errors'].append(f"Невалидный URL: {url}")
        
        # Проверка обязательных полей
        for position in ['top_left', 'filename']:
            if position in column_mapping and column_mapping[position]:
                col = column_mapping[position]
                if col in row:
                    value = row[col]
                    if pd.isna(value) or (isinstance(value, str) and len(value.strip()) == 0):
                        validation['warnings'].append(f"Пустое поле: {position} ({col})")
        
        return validation
    
    def process_single_row_with_validation(self, row: pd.Series, row_index: int) -> Dict:
        """Обработка строки с предварительной валидацией"""
        try:
            # Валидация данных
            column_mapping = safe_get_session_state('column_mapping', {})
            validation = self.validate_row_data(row, column_mapping)
            
            if not validation['is_valid']:
                return {
                    'row_index': row_index,
                    'status': 'error',
                    'message': f"Валидация не пройдена: {', '.join(validation['errors'])}",
                    'validation_warnings': validation['warnings']
                }
            
            # Если есть предупреждения, логируем их
            if validation['warnings']:
                logger.warning(f"Строка {row_index}: {', '.join(validation['warnings'])}")
            
            # Продолжаем обычную обработку
            return self.process_single_row(row, row_index)
            
        except Exception as e:
            logger.error(f"Ошибка валидации строки {row_index}: {e}")
            return {
                'row_index': row_index,
                'status': 'error',
                'message': f"Ошибка валидации: {str(e)}"
            }
    
    def process_single_row(self, row: pd.Series, row_index: int) -> Dict:
        """Обработка одной строки - ИСПРАВЛЕННАЯ ВЕРСИЯ С ПРАВИЛЬНЫМИ ГРАНИЦАМИ"""
        try:
            # Гарантируем инициализацию всех необходимых атрибутов
            ensure_session_state_initialized()
            
            # === КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Преобразуем pd.Series в словарь для безопасности ===
            row_dict = {}
            try:
                if hasattr(row, 'to_dict'):
                    row_dict = row.to_dict()
                else:
                    for col in row.index:
                        row_dict[col] = row[col]
            except Exception as e:
                logger.warning(f"Ошибка преобразования строки {row_index} в словарь: {e}")
                row_dict = dict(row)
            
            # Получаем column_mapping безопасно
            column_mapping = safe_get_session_state('column_mapping', {})
            
            # === ИСПРАВЛЕННАЯ ПРОВЕРКА URL ИЗОБРАЖЕНИЯ ===
            image_url = None
            
            # Получаем имя колонки с URL
            url_column_name = None
            if 'image_url' in column_mapping and column_mapping['image_url']:
                url_column_name = column_mapping['image_url']
            
            if url_column_name and url_column_name in row_dict:
                # Получаем значение из словаря
                url_value = row_dict.get(url_column_name)
                
                # Проверяем и очищаем значение
                if url_value is not None and pd.notna(url_value):
                    url_str = str(url_value).strip()
                    
                    # Расширенная проверка URL
                    if url_str and len(url_str) > 5:
                        # Проверяем различные форматы URL
                        is_valid_url = (
                            url_str.startswith('http://') or 
                            url_str.startswith('https://') or
                            url_str.startswith('//') or
                            url_str.startswith('www.') or
                            '.' in url_str and any(ext in url_str.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif'])
                        )
                        
                        if is_valid_url:
                            # Нормализуем URL
                            if url_str.startswith('//'):
                                image_url = 'https:' + url_str
                            elif url_str.startswith('www.'):
                                image_url = 'https://' + url_str
                            else:
                                image_url = url_str
            
            # Если URL нет - возвращаем ошибку
            if not image_url:
                return {
                    'row_index': row_index,
                    'status': 'error',
                    'message': f'Нет URL изображения в колонке "{url_column_name}"'
                }
            
            # Получаем данные из строки - ВСЕ 8 ПОЛЕЙ
            text_data = {}
            all_positions = ['top_left', 'top_right', 'bottom_left', 'bottom_right',
                           'header_left', 'header_right', 'footer_left', 'footer_right']
            
            for position in all_positions:
                if position in column_mapping and column_mapping[position]:
                    col = column_mapping[position]
                    if col in row_dict:
                        value = row_dict[col]
                        if pd.isna(value):
                            text_data[position] = ''
                        else:
                            text_data[position] = str(value)
                    else:
                        text_data[position] = ''
                else:
                    text_data[position] = ''
            
            # URL изображения для наложения
            overlay_url = None
            if ('overlay_image_url' in column_mapping and 
                column_mapping['overlay_image_url']):
                col = column_mapping['overlay_image_url']
                if col in row_dict and pd.notna(row_dict[col]):
                    overlay_url = str(row_dict[col]).strip()
                    if not overlay_url or overlay_url.lower() in ['nan', 'none', '']:
                        overlay_url = None
            
            # Имя файла
            filename = f"item_{row_index:04d}"
            if 'filename' in column_mapping and column_mapping['filename']:
                col = column_mapping['filename']
                if col in row_dict and pd.notna(row_dict[col]):
                    filename_source = str(row_dict[col]).strip()
                    if filename_source:
                        filename = re.sub(r'[^\w\-_\. ]', '_', filename_source)
                        filename = re.sub(r'\s+', '_', filename)
                        filename = filename[:50]
            
            # Получаем настройки обработки
            processing_settings = safe_get_session_state('processing_settings', {})
            timeout = processing_settings.get('timeout', 30)
            retries = processing_settings.get('retry_count', 3)
            
            # Загружаем основное изображение
            logger.debug(f"Загрузка изображения для строки {row_index}: {image_url[:50]}...")
            main_img = self.image_processor.load_image_from_url(
                image_url, 
                timeout=timeout,
                retries=retries
            )
            
            if main_img is None:
                return {
                    'row_index': row_index,
                    'status': 'error',
                    'message': f'Не удалось загрузить изображение из URL',
                    'url': image_url[:100]
                }
            
            # Получаем настройки экспорта
            export_settings = safe_get_session_state('export_settings', {})
            
            # Изменяем размер если нужно
            if export_settings.get('resize', True):
                target_size = export_settings.get('target_size', 1200)
                main_img = self.image_processor.resize_image(main_img, target_size)
            
            # === КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Правильное совмещение изображения и шаблона ===
            # Получаем текущий шаблон
            current_template = safe_get_session_state('current_template', 'modern_shop')
            
            # Создаем холст шаблона ТОЧНОГО РАЗМЕРА изображения
            canvas = self.image_processor.create_template_canvas(
                main_img.width, main_img.height, current_template
            )
            
            # Получаем настройки фона
            background_settings = safe_get_session_state('background_settings', {})
            header_height_percent = max(0, min(background_settings.get('header_height', 15), 100))
            header_height = int(main_img.height * header_height_percent / 100)
            
            # === ИСПРАВЛЕНИЕ: Вставляем изображение в ОСНОВНУЮ СЕКЦИЮ шаблона ===
            # Вычисляем позицию для основного изображения
            footer_height_percent = max(0, min(background_settings.get('footer_height', 10), 100 - header_height_percent))
            footer_height = int(main_img.height * footer_height_percent / 100)
            main_height = main_img.height - header_height - footer_height
            
            # Гарантируем, что основная секция существует
            if main_height <= 0:
                main_height = main_img.height - header_height
                if main_height <= 0:
                    main_height = main_img.height  # Если нет шапки/футера, используем всю высоту
            
            # Создаем финальное изображение
            final_img = canvas.copy()
            
            # Масштабируем основное изображение, чтобы оно поместилось в основную секцию
            if main_img.height > main_height:
                # Если изображение выше основной секции, масштабируем по высоте
                scale_ratio = main_height / main_img.height
                new_width = int(main_img.width * scale_ratio)
                new_height = main_height
                main_img_resized = main_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            else:
                main_img_resized = main_img
            
            # Центрируем изображение по горизонтали в основной секции
            if main_img_resized.width < canvas.width:
                x_offset = (canvas.width - main_img_resized.width) // 2
            else:
                # Если изображение шире холста, обрезаем или масштабируем
                scale_ratio = canvas.width / main_img_resized.width
                if scale_ratio < 1:
                    new_width = canvas.width
                    new_height = int(main_img_resized.height * scale_ratio)
                    main_img_resized = main_img_resized.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    x_offset = 0
                else:
                    x_offset = 0
            
            # Вставляем изображение в основную секцию
            y_offset = header_height
            # Гарантируем, что не выходим за границы
            if y_offset + main_img_resized.height > canvas.height:
                y_offset = max(0, canvas.height - main_img_resized.height)
            
            if x_offset + main_img_resized.width > canvas.width:
                x_offset = max(0, canvas.width - main_img_resized.width)
            
            final_img.paste(main_img_resized, (x_offset, y_offset))
            
            # Добавляем текст (теперь 8 полей вместо 4)
            final_img = self.image_processor.add_text_to_image(
                final_img, text_data, current_template
            )
            
            # Добавляем наложение если есть
            image_overlay_settings = safe_get_session_state('image_overlay_settings', {})
            if overlay_url and image_overlay_settings.get('enabled', False):
                overlay_img = self.image_processor.load_image_from_url(overlay_url, timeout=15)
                
                if overlay_img:
                    final_img = self.image_processor.add_image_overlay(
                        final_img,
                        overlay_img,
                        image_overlay_settings
                    )
            
            # Сохраняем
            output_dir = safe_get_session_state('output_dir', 'output_infographics')
            format_ext = export_settings.get('format', 'PNG').lower()
            filepath = os.path.join(output_dir, f"{filename}.{format_ext}")
            
            success = self.image_processor.save_image(
                final_img,
                filepath,
                format=export_settings.get('format', 'PNG'),
                quality=export_settings.get('quality', 95)
            )
            
            if success:
                logger.info(f"Успешно обработана строка {row_index}: {filename}")
                return {
                    'row_index': row_index,
                    'status': 'success',
                    'filename': filename,
                    'filepath': filepath,
                    'url': image_url[:50] + '...'
                }
            else:
                return {
                    'row_index': row_index,
                    'status': 'error',
                    'message': 'Ошибка сохранения файла'
                }
                
        except Exception as e:
            logger.error(f"Критическая ошибка обработки строки {row_index}: {e}")
            return {
                'row_index': row_index,
                'status': 'error',
                'message': f'Критическая ошибка: {str(e)[:100]}'
            }
    
    def process_batch(self, df: pd.DataFrame, start_idx: int, end_idx: int) -> List[Dict]:
        """Пакетная обработка"""
        results = []
        total = end_idx - start_idx + 1
        
        if total <= 0:
            return results
        
        # Создаем выходную директорию
        output_dir = safe_get_session_state('output_dir', 'output_infographics')
        os.makedirs(output_dir, exist_ok=True)
        
        # Настройки многопоточности
        processing_settings = safe_get_session_state('processing_settings', {})
        max_workers = min(processing_settings.get('max_workers', 4), total)
        max_workers = max(1, max_workers)
        
        logger.info(f"Начало обработки {total} строк, потоков: {max_workers}")
        
        # Собираем статистику ошибок
        stats = {
            'total': total,
            'success': 0,
            'no_url': 0,
            'load_failed': 0,
            'other_errors': 0
        }
        
        # Прогресс бар
        progress_bar = st.progress(0)
        status_text = st.empty()
        stats_text = st.empty()
        
        def process_wrapper(idx):
            """Обертка для обработки одной строки"""
            try:
                if idx >= len(df):
                    return {
                        'row_index': idx,
                        'status': 'error',
                        'message': 'Индекс вне диапазона'
                    }
                
                row = df.iloc[idx]
                return self.process_single_row_with_validation(row, idx)
            except Exception as e:
                logger.error(f"Ошибка в process_wrapper для строки {idx}: {e}")
                return {
                    'row_index': idx,
                    'status': 'error',
                    'message': f'Ошибка обертки: {str(e)[:50]}'
                }
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            
            # Запускаем задачи
            for idx in range(start_idx, end_idx + 1):
                future = executor.submit(process_wrapper, idx)
                futures.append(future)
            
            # Обрабатываем результаты по мере завершения
            completed = 0
            error_messages = []
            
            for future in as_completed(futures):
                try:
                    timeout = processing_settings.get('timeout', 30) + 10
                    result = future.result(timeout=timeout)
                    results.append(result)
                    completed += 1
                    
                    # Обновляем статистику
                    if result.get('status') == 'success':
                        stats['success'] += 1
                    else:
                        msg = result.get('message', '').lower()
                        if 'нет url' in msg:
                            stats['no_url'] += 1
                        elif 'не удалось загрузить' in msg:
                            stats['load_failed'] += 1
                        else:
                            stats['other_errors'] += 1
                        
                        # Сохраняем сообщения об ошибках
                        if len(error_messages) < 10:
                            error_messages.append(f"Строка {result.get('row_index')}: {result.get('message')}")
                    
                    # Обновляем прогресс
                    progress = completed / total
                    progress_bar.progress(progress)
                    
                    # Обновляем статус
                    status_text.text(f"Обработано: {completed}/{total}")
                    stats_text.text(
                        f"✅ Успешно: {stats['success']} | "
                        f"❌ Без URL: {stats['no_url']} | "
                        f"⚠️ Ошибки загрузки: {stats['load_failed']} | "
                        f"💥 Прочие ошибки: {stats['other_errors']}"
                    )
                    
                except Exception as e:
                    logger.error(f"Ошибка при получении результата: {e}")
                    stats['other_errors'] += 1
                    completed += 1
        
        # Итоговая статистика
        logger.info(f"Обработка завершена. Статистика: {stats}")
        
        # Показываем сводку по ошибкам
        if error_messages:
            with st.expander("📋 Подробности ошибок", expanded=False):
                for error in error_messages:
                    st.error(error)
        
        st.session_state.batch_results = results
        return results
    
    def create_zip_archive(self, results: List[Dict]) -> Optional[str]:
        """Создание ZIP архива"""
        try:
            output_dir = safe_get_session_state('output_dir', 'output_infographics')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_path = os.path.join(output_dir, f"infographics_{timestamp}.zip")
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Добавляем успешные изображения
                added_count = 0
                for result in results:
                    if result.get('status') == 'success' and 'filepath' in result:
                        filepath = result['filepath']
                        if os.path.exists(filepath):
                            zipf.write(filepath, os.path.basename(filepath))
                            added_count += 1
                
                logger.info(f"В архив добавлено {added_count} файлов")
            
            if added_count > 0:
                logger.info(f"ZIP архив создан: {zip_path}")
                return zip_path
            else:
                logger.warning("Не найдено файлов для добавления в архив")
                return None
                
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
            
            # Улучшенная загрузка файла
            st.subheader("📁 Загрузка данных")
            
            col1, col2 = st.columns(2)
            with col1:
                uploaded_file = st.file_uploader(
                    "Выберите файл",
                    type=['xlsx', 'xls', 'xlsm', 'xlsb', 'ods', 'csv'],
                    key="file_uploader",
                    label_visibility="collapsed"
                )
            
            with col2:
                if uploaded_file:
                    file_type = uploaded_file.name.split('.')[-1].upper()
                    st.info(f"📄 {file_type}")
            
            if uploaded_file:
                ensure_session_state_initialized()
                
                if (st.session_state.uploaded_file_name != uploaded_file.name or
                    st.session_state.df is None):
                    
                    with st.spinner(f"Загрузка {uploaded_file.name}..."):
                        # Используем улучшенный процессор
                        df = AdvancedExcelProcessor.read_excel_with_fallback(uploaded_file)
                        
                        if df is not None:
                            st.session_state.df = df
                            st.session_state.uploaded_file_name = uploaded_file.name
                            
                            # Валидация данных
                            validation = AdvancedExcelProcessor.validate_dataframe(df)
                            
                            # Интеллектуальный подбор колонок
                            suggestions = AdvancedExcelProcessor.get_intelligent_column_suggestions(df)
                            
                            # Обновляем column_mapping с учетом уверенности
                            for key in suggestions:
                                if suggestions[key] and key != 'confidence':
                                    st.session_state.column_mapping[key] = suggestions[key]
                            
                            # Показываем результаты валидации
                            if validation['warnings']:
                                with st.expander("⚠️ Предупреждения", expanded=True):
                                    for warning in validation['warnings']:
                                        st.warning(warning)
                            
                            # Статистика
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Строк", validation['total_rows'])
                            with col2:
                                st.metric("Колонок", validation['total_columns'])
                            with col3:
                                st.metric("URL колонок", len(validation['url_columns']))
                            
                            st.success(f"✅ Файл загружен успешно!")
                            
                            # Автофильтрация URL если есть подозрения
                            if validation['warnings'] and any('URL' in warning for warning in validation['warnings']):
                                if st.button("🚫 Автофильтрация невалидных URL", type="secondary"):
                                    url_col = st.session_state.column_mapping['image_url']
                                    if url_col:
                                        df_filtered = AdvancedExcelProcessor.filter_invalid_urls(df, url_col)
                                        st.session_state.df = df_filtered
                                        st.success(f"Осталось {len(df_filtered)} строк после фильтрации")
                                        st.rerun()
            
            # Предпросмотр данных
            if st.session_state.df is not None:
                with st.expander("👁️ Предпросмотр данных"):
                    preview_rows = st.slider("Строк", 5, 50, 10, key="preview_rows")
                    st.dataframe(st.session_state.df.head(preview_rows))
            
            # Шаблоны
            st.subheader("🎨 Шаблон")
            template_names = DynamicTemplateManager.get_template_names()
            
            if template_names:
                template_options = [name for _, name in template_names]
                template_ids = [tid for tid, _ in template_names]
                
                current_template = st.session_state.current_template
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
            
            current_header = st.session_state.background_settings['header_background']
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
            
            current_main = st.session_state.background_settings['main_background']
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
            
            current_footer = st.session_state.background_settings['footer_background']
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
                header_height = st.slider(
                    "Высота шапки (%)",
                    5, 40, 15,
                    key="header_height"
                )
                st.session_state.background_settings['header_height'] = min(header_height, 100)
            
            with col2:
                footer_height = st.slider(
                    "Высота футера (%)",
                    5, 40, 10,
                    key="footer_height"
                )
                st.session_state.background_settings['footer_height'] = min(footer_height, 100 - header_height)
            
            # Эффекты
            corner_radius = st.slider(
                "Скругление углов",
                0, 50, 20,
                key="corner_radius"
            )
            st.session_state.background_settings['corner_radius'] = corner_radius
            
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
                border_width = st.slider(
                    "Толщина",
                    1, 10, 2,
                    key="border_width"
                )
                st.session_state.background_settings['border_width'] = min(border_width, 10)
            
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
            processed_count = safe_get_session_state('processed_count', 0)
            st.caption(f"Обработано: {processed_count}")
            st.caption("Версия: 8.1")
    
    @staticmethod
    def render_column_mapping():
        """Настройка маппинга колонок"""
        if st.session_state.df is None:
            return
        
        st.subheader("📊 Настройка колонок")
        
        available_columns = st.session_state.df.columns.tolist()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Верхний левый (основная секция)
            top_left_default = st.session_state.column_mapping['top_left']
            top_left_idx = available_columns.index(top_left_default) if top_left_default in available_columns else 0
            st.session_state.column_mapping['top_left'] = st.selectbox(
                "Верхний левый (основной)",
                available_columns,
                index=top_left_idx,
                key="col_top_left"
            )
            
            # Верхний правый (основная секция)
            top_right_default = st.session_state.column_mapping['top_right']
            top_right_idx = available_columns.index(top_right_default) if top_right_default in available_columns else min(1, len(available_columns)-1)
            st.session_state.column_mapping['top_right'] = st.selectbox(
                "Верхний правый (основной)",
                available_columns,
                index=top_right_idx,
                key="col_top_right"
            )
            
            # Нижний левый (основная секция)
            bottom_left_default = st.session_state.column_mapping['bottom_left']
            bottom_left_idx = available_columns.index(bottom_left_default) if bottom_left_default in available_columns else min(2, len(available_columns)-1)
            st.session_state.column_mapping['bottom_left'] = st.selectbox(
                "Нижний левый (основной)",
                available_columns,
                index=bottom_left_idx,
                key="col_bottom_left"
            )
            
            # Нижний правый (основная секция)
            bottom_right_default = st.session_state.column_mapping['bottom_right']
            bottom_right_idx = available_columns.index(bottom_right_default) if bottom_right_default in available_columns else min(3, len(available_columns)-1)
            st.session_state.column_mapping['bottom_right'] = st.selectbox(
                "Нижний правый (основной)",
                available_columns,
                index=bottom_right_idx,
                key="col_bottom_right"
            )
        
        with col2:
            # Левый верхний (шапка)
            header_left_default = st.session_state.column_mapping['header_left']
            header_left_idx = available_columns.index(header_left_default) if header_left_default in available_columns else min(4, len(available_columns)-1)
            st.session_state.column_mapping['header_left'] = st.selectbox(
                "Левый (шапка)",
                available_columns,
                index=header_left_idx,
                key="col_header_left"
            )
            
            # Правый верхний (шапка)
            header_right_default = st.session_state.column_mapping['header_right']
            header_right_idx = available_columns.index(header_right_default) if header_right_default in available_columns else min(5, len(available_columns)-1)
            st.session_state.column_mapping['header_right'] = st.selectbox(
                "Правый (шапка)",
                available_columns,
                index=header_right_idx,
                key="col_header_right"
            )
            
            # Левый нижний (футер)
            footer_left_default = st.session_state.column_mapping['footer_left']
            footer_left_idx = available_columns.index(footer_left_default) if footer_left_default in available_columns else min(6, len(available_columns)-1)
            st.session_state.column_mapping['footer_left'] = st.selectbox(
                "Левый (футер)",
                available_columns,
                index=footer_left_idx,
                key="col_footer_left"
            )
            
            # Правый нижний (футер)
            footer_right_default = st.session_state.column_mapping['footer_right']
            footer_right_idx = available_columns.index(footer_right_default) if footer_right_default in available_columns else min(7, len(available_columns)-1)
            st.session_state.column_mapping['footer_right'] = st.selectbox(
                "Правый (футер)",
                available_columns,
                index=footer_right_idx,
                key="col_footer_right"
            )
            
            # URL изображения
            image_url_default = st.session_state.column_mapping['image_url']
            image_url_idx = available_columns.index(image_url_default) if image_url_default in available_columns else min(8, len(available_columns)-1)
            st.session_state.column_mapping['image_url'] = st.selectbox(
                "URL изображения",
                available_columns,
                index=image_url_idx,
                key="col_image_url"
            )
            
            # Имя файла
            filename_default = st.session_state.column_mapping['filename']
            filename_idx = available_columns.index(filename_default) if filename_default in available_columns else 0
            st.session_state.column_mapping['filename'] = st.selectbox(
                "Имя файла",
                available_columns,
                index=filename_idx,
                key="col_filename"
            )
        
        if st.button("🔍 Автоподбор", key="auto_map"):
            suggestions = AdvancedExcelProcessor.get_intelligent_column_suggestions(st.session_state.df)
            # Обновляем все ключи
            for key in suggestions:
                if key != 'confidence' and suggestions[key]:
                    st.session_state.column_mapping[key] = suggestions[key]
            st.success("✅ Колонки подобраны!")
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
                
                current_font = st.session_state.font_settings['main_font']
                current_idx = font_keys.index(current_font) if current_font in font_keys else 0
                
                selected = st.selectbox(
                    "Основной шрифт",
                    font_options,
                    index=current_idx,
                    key="main_font"
                )
                
                st.session_state.font_settings['main_font'] = font_keys[font_options.index(selected)]
                
                st.session_state.font_settings['font_size_multiplier'] = st.slider(
                    "Общий размер шрифта",
                    0.5, 2.0, 1.0, 0.1,
                    key="font_size"
                )
    
    @staticmethod
    def render_text_offsets():
        """Смещения текста"""
        st.subheader("🎯 Смещение текста")
        
        symmetrical = st.checkbox(
            "Симметричные смещения",
            value=st.session_state.symmetrical_offsets,
            key="symmetrical_offsets"
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
            
            for key in ['top_left', 'top_right', 'bottom_left', 'bottom_right',
                       'header_left', 'header_right', 'footer_left', 'footer_right']:
                st.session_state.text_offset_settings[key] = {
                    'x_offset': x_offset,
                    'y_offset': y_offset
                }
        else:
            st.info("Настройте смещение для каждого текстового поля отдельно")
            
            # Основная секция
            st.markdown("**Основная секция:**")
            cols = st.columns(4)
            positions = ['top_left', 'top_right', 'bottom_left', 'bottom_right']
            labels = ['↖️ Верх. левый', '↗️ Верх. правый', '↙️ Низ. левый', '↘️ Низ. правый']
            
            for i, (pos, label) in enumerate(zip(positions, labels)):
                with cols[i]:
                    st.markdown(f"**{label}**")
                    x = st.number_input(
                        "X (%)",
                        -100, 100,
                        st.session_state.text_offset_settings[pos]['x_offset'],
                        key=f"offset_x_{pos}"
                    )
                    y = st.number_input(
                        "Y (%)",
                        -100, 100,
                        st.session_state.text_offset_settings[pos]['y_offset'],
                        key=f"offset_y_{pos}"
                    )
                    st.session_state.text_offset_settings[pos] = {
                        'x_offset': x,
                        'y_offset': y
                    }
            
            # Шапка
            st.markdown("**Шапка:**")
            cols = st.columns(2)
            header_positions = ['header_left', 'header_right']
            header_labels = ['⬅️ Левый (шапка)', '➡️ Правый (шапка)']
            
            for i, (pos, label) in enumerate(zip(header_positions, header_labels)):
                with cols[i]:
                    st.markdown(f"**{label}**")
                    x = st.number_input(
                        "X (%)",
                        -100, 100,
                        st.session_state.text_offset_settings[pos]['x_offset'],
                        key=f"offset_x_{pos}"
                    )
                    y = st.number_input(
                        "Y (%)",
                        -100, 100,
                        st.session_state.text_offset_settings[pos]['y_offset'],
                        key=f"offset_y_{pos}"
                    )
                    st.session_state.text_offset_settings[pos] = {
                        'x_offset': x,
                        'y_offset': y
                    }
            
            # Футер
            st.markdown("**Футер:**")
            cols = st.columns(2)
            footer_positions = ['footer_left', 'footer_right']
            footer_labels = ['⬅️ Левый (футер)', '➡️ Правый (футер)']
            
            for i, (pos, label) in enumerate(zip(footer_positions, footer_labels)):
                with cols[i]:
                    st.markdown(f"**{label}**")
                    x = st.number_input(
                        "X (%)",
                        -100, 100,
                        st.session_state.text_offset_settings[pos]['x_offset'],
                        key=f"offset_x_{pos}"
                    )
                    y = st.number_input(
                        "Y (%)",
                        -100, 100,
                        st.session_state.text_offset_settings[pos]['y_offset'],
                        key=f"offset_y_{pos}"
                    )
                    st.session_state.text_offset_settings[pos] = {
                        'x_offset': x,
                        'y_offset': y
                    }
        
        if st.button("🔄 Сбросить смещения", key="reset_offsets"):
            for key in ['top_left', 'top_right', 'bottom_left', 'bottom_right',
                       'header_left', 'header_right', 'footer_left', 'footer_right']:
                st.session_state.text_offset_settings[key] = {
                    'x_offset': 0,
                    'y_offset': 0
                }
            st.rerun()
    
    @staticmethod
    def render_font_sizes():
        """Настройки размера текста"""
        st.subheader("🔠 Размер текста")
        
        symmetrical = st.checkbox(
            "Одинаковый размер для всех полей",
            value=st.session_state.symmetrical_font_sizes,
            key="symmetrical_font_sizes"
        )
        st.session_state.symmetrical_font_sizes = symmetrical
        
        if symmetrical:
            size_percentage = st.slider(
                "Размер текста (%)",
                50, 200, 100,
                key="sym_font_size"
            )
            
            for key in ['top_left', 'top_right', 'bottom_left', 'bottom_right',
                       'header_left', 'header_right', 'footer_left', 'footer_right']:
                st.session_state.font_size_settings[key] = size_percentage
        else:
            st.info("Настройте размер для каждого текстового поля отдельно")
            
            # Основная секция
            st.markdown("**Основная секция:**")
            cols = st.columns(4)
            positions = ['top_left', 'top_right', 'bottom_left', 'bottom_right']
            labels = ['↖️ Верх. левый', '↗️ Верх. правый', '↙️ Низ. левый', '↘️ Низ. правый']
            
            for i, (pos, label) in enumerate(zip(positions, labels)):
                with cols[i]:
                    st.markdown(f"**{label}**")
                    size = st.slider(
                        "Размер (%)",
                        50, 200,
                        st.session_state.font_size_settings[pos],
                        key=f"font_size_{pos}"
                    )
                    st.session_state.font_size_settings[pos] = size
            
            # Шапка
            st.markdown("**Шапка:**")
            cols = st.columns(2)
            header_positions = ['header_left', 'header_right']
            header_labels = ['⬅️ Левый (шапка)', '➡️ Правый (шапка)']
            
            for i, (pos, label) in enumerate(zip(header_positions, header_labels)):
                with cols[i]:
                    st.markdown(f"**{label}**")
                    size = st.slider(
                        "Размер (%)",
                        50, 200,
                        st.session_state.font_size_settings[pos],
                        key=f"font_size_{pos}"
                    )
                    st.session_state.font_size_settings[pos] = size
            
            # Футер
            st.markdown("**Футер:**")
            cols = st.columns(2)
            footer_positions = ['footer_left', 'footer_right']
            footer_labels = ['⬅️ Левый (футер)', '➡️ Правый (футер)']
            
            for i, (pos, label) in enumerate(zip(footer_positions, footer_labels)):
                with cols[i]:
                    st.markdown(f"**{label}**")
                    size = st.slider(
                        "Размер (%)",
                        50, 200,
                        st.session_state.font_size_settings[pos],
                        key=f"font_size_{pos}"
                    )
                    st.session_state.font_size_settings[pos] = size
        
        if st.button("🔄 Сбросить размеры", key="reset_font_sizes"):
            for key in ['top_left', 'top_right', 'bottom_left', 'bottom_right',
                       'header_left', 'header_right', 'footer_left', 'footer_right']:
                st.session_state.font_size_settings[key] = 100
            st.rerun()
    
    @staticmethod
    def render_overlay_settings():
        """Настройки наложения"""
        st.subheader("🖼️ Наложение")
        
        enabled = st.checkbox(
            "Включить наложение",
            value=st.session_state.image_overlay_settings['enabled'],
            key="overlay_enabled"
        )
        st.session_state.image_overlay_settings['enabled'] = enabled
        
        if enabled:
            # Выбор колонки с изображением для наложения
            if st.session_state.df is not None:
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
    def render_template_preview():
        """Предпросмотр границ шаблона"""
        st.subheader("📐 Предпросмотр границ шаблона")
        
        # Создаем тестовое изображение
        test_width = 600
        test_height = 400
        
        # Создаем шаблон
        current_template = safe_get_session_state('current_template', 'modern_shop')
        canvas = ImageProcessor.create_template_canvas(test_width, test_height, current_template)
        
        # Создаем изображение с границами
        border_img = canvas.copy()
        draw = ImageDraw.Draw(border_img)
        
        # Определяем область содержимого
        content_area = ImageProcessor.get_template_content_area(canvas)
        x1, y1, x2, y2 = content_area
        
        # Рисуем границы
        draw.rectangle([x1, y1, x2, y2], outline=(255, 0, 0, 200), width=3)
        
        # Добавляем подписи
        font = FontManager.load_system_font('system_arial', 14)
        draw.text((10, 10), f"Шаблон: {current_template}", font=font, fill=(255, 255, 255, 255))
        draw.text((10, 30), f"Границы: ({x1},{y1})-({x2},{y2})", font=font, fill=(255, 255, 255, 255))
        draw.text((10, 50), f"Размер: {test_width}x{test_height}", font=font, fill=(255, 255, 255, 255))
        
        col1, col2 = st.columns(2)
        with col1:
            st.image(canvas, caption="Шаблон без границ", use_column_width=True)
        with col2:
            st.image(border_img, caption="Шаблон с границами содержимого", use_column_width=True)
    
    @staticmethod
    def render_preview_tab(generator):
        """Вкладка предпросмотра"""
        if st.session_state.df is None:
            st.info("📥 Загрузите Excel файл в боковой панели для начала работы")
            return
        
        st.header("🎯 Предпросмотр")
        
        # Предпросмотр границ шаблона
        UIComponents.render_template_preview()
        
        # Настройки
        UIComponents.render_font_settings()
        UIComponents.render_text_offsets()
        UIComponents.render_font_sizes()  # НОВОЕ: настройка размера текста
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
                
                # Получаем данные - ВСЕ 8 ПОЛЕЙ
                text_data = {}
                all_positions = ['top_left', 'top_right', 'bottom_left', 'bottom_right',
                               'header_left', 'header_right', 'footer_left', 'footer_right']
                
                for position in all_positions:
                    if st.session_state.column_mapping[position]:
                        col = st.session_state.column_mapping[position]
                        if col in row:
                            text_data[position] = str(row[col] or '')
                
                # URL изображений
                image_url = ''
                if st.session_state.column_mapping['image_url']:
                    col = st.session_state.column_mapping['image_url']
                    if col in row:
                        image_url = str(row[col] or '')
                
                overlay_url = None
                if (st.session_state.column_mapping.get('overlay_image_url') and
                    st.session_state.image_overlay_settings['enabled']):
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
                        if st.session_state.export_settings['resize']:
                            target_size = st.session_state.export_settings['target_size']
                            img = ImageProcessor.resize_image(img, target_size)
                        
                        # Создаем холст
                        canvas = generator.image_processor.create_template_canvas(
                            img.width, img.height,
                            st.session_state.current_template
                        )
                        
                        # Получаем настройки фона
                        background_settings = st.session_state.background_settings
                        header_height = int(img.height * background_settings.get('header_height', 15) / 100)
                        
                        # Вставляем изображение в основную секцию
                        footer_height = int(img.height * background_settings.get('footer_height', 10) / 100)
                        main_height = img.height - header_height - footer_height
                        
                        if main_height <= 0:
                            main_height = img.height - header_height
                            if main_height <= 0:
                                main_height = img.height
                        
                        # Масштабируем изображение для основной секции
                        if img.height > main_height:
                            scale_ratio = main_height / img.height
                            new_width = int(img.width * scale_ratio)
                            new_height = main_height
                            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        else:
                            img_resized = img
                        
                        # Центрируем
                        x_offset = (canvas.width - img_resized.width) // 2
                        y_offset = header_height
                        
                        final_img = canvas.copy()
                        final_img.paste(img_resized, (x_offset, y_offset))
                        
                        # Добавляем текст (теперь 8 полей вместо 4)
                        final_img = generator.image_processor.add_text_to_image(
                            final_img, text_data, st.session_state.current_template
                        )
                        
                        # Добавляем наложение
                        if overlay_url and st.session_state.image_overlay_settings['enabled']:
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
                        format_ = st.session_state.export_settings['format']
                        
                        if format_ == 'JPEG':
                            final_img.convert('RGB').save(buffered, format='JPEG',
                                                         quality=st.session_state.export_settings['quality'])
                            mime = 'image/jpeg'
                        elif format_ == 'WEBP':
                            final_img.save(buffered, format='WEBP',
                                         quality=st.session_state.export_settings['quality'])
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
        if st.session_state.df is None:
            st.info("📥 Загрузите Excel файл в боковой панели для начала работы")
            return
        
        st.header("⚡ Массовая обработка")
        
        # Используем улучшенный процессор для оптимизации данных
        df_optimized = AdvancedExcelProcessor.clean_dataframe(st.session_state.df)
        total_rows = len(df_optimized)
        
        if total_rows == 0:
            st.error("❌ Нет данных для обработки")
            return
        
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
                min(start_idx + st.session_state.processing_settings['batch_size'] - 1, total_rows-1),
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
        
        processed_count = safe_get_session_state('processed_count', 0)
        if processed_count == 0:
            st.info("📈 Статистика появится после обработки")
            return
        
        # Общая статистика
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Всего обработано", processed_count)
        
        with col2:
            batch_results = safe_get_session_state('batch_results', [])
            if batch_results:
                success = sum(1 for r in batch_results if r.get('status') == 'success')
                total = len(batch_results)
                rate = (success / total * 100) if total > 0 else 0
                st.metric("Успешность", f"{rate:.1f}%")
        
        with col3:
            template = DynamicTemplateManager.load_template(st.session_state.current_template)
            template_name = template.get('name', 'Неизвестно')
            st.metric("Шаблон", template_name[:15])
        
        with col4:
            st.metric("Формат", st.session_state.export_settings['format'])
        
        # Детальная статистика
        batch_results = safe_get_session_state('batch_results', [])
        if batch_results:
            st.subheader("📈 Детали последней обработки")
            results_df = pd.DataFrame(batch_results)
            
            if 'status' in results_df.columns:
                status_counts = results_df['status'].value_counts()
                col1, col2 = st.columns(2)
                with col1:
                    st.bar_chart(status_counts)
                with col2:
                    st.dataframe(status_counts)
            
            # Время обработки
            processing_stats = safe_get_session_state('processing_stats', {})
            if (processing_stats.get('start_time') and
                processing_stats.get('end_time')):
                duration = (processing_stats['end_time'] -
                          processing_stats['start_time']).total_seconds()
                
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
        
        current_category = st.session_state.current_category
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
    
    @staticmethod
    def render_data_quality_tab():
        """Вкладка анализа качества данных"""
        if st.session_state.df is None:
            st.info("📥 Загрузите Excel файл для анализа")
            return
        
        st.header("📊 Анализ качества данных")
        
        # Используем улучшенный процессор
        df = st.session_state.df
        
        # Показываем анализ качества
        AdvancedExcelProcessor.preview_data_quality(df)
        
        # Фильтрация данных
        st.subheader("🔍 Фильтрация данных")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚫 Удалить строки без URL", use_container_width=True):
                if 'image_url' in st.session_state.column_mapping:
                    url_col = st.session_state.column_mapping['image_url']
                    if url_col and url_col in df.columns:
                        initial_len = len(df)
                        df_filtered = AdvancedExcelProcessor.filter_invalid_urls(df, url_col)
                        st.session_state.df = df_filtered
                        removed = initial_len - len(df_filtered)
                        if removed > 0:
                            st.success(f"✅ Удалено {removed} строк без валидных URL")
                        else:
                            st.info("Не найдено строк с невалидными URL")
                        st.rerun()
        
        with col2:
            if st.button("🧹 Автоочистка данных", use_container_width=True):
                df_cleaned = AdvancedExcelProcessor.clean_dataframe(df)
                st.session_state.df = df_cleaned
                st.success("✅ Данные очищены")
                st.rerun()
        
        # Экспорт исправленных данных
        st.subheader("💾 Экспорт данных")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Скачать исправленные данные", use_container_width=True):
                # Создаем временный Excel файл
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    st.session_state.df.to_excel(writer, index=False, sheet_name='Data')
                
                output.seek(0)
                
                st.download_button(
                    label="⬇️ Скачать Excel",
                    data=output.getvalue(),
                    file_name=f"cleaned_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        with col2:
            # Экспорт проблемных строк
            if st.button("📋 Экспорт проблемных строк", use_container_width=True):
                if 'image_url' in st.session_state.column_mapping:
                    url_col = st.session_state.column_mapping['image_url']
                    if url_col and url_col in df.columns:
                        # Находим строки без валидных URL
                        def is_invalid_url(url):
                            if pd.isna(url) or not isinstance(url, str):
                                return True
                            url_str = url.strip()
                            return len(url_str) < 10 or not any(ext in url_str.lower() 
                                                             for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif'])
                        
                        invalid_mask = df[url_col].apply(is_invalid_url)
                        invalid_df = df[invalid_mask].copy()
                        
                        if not invalid_df.empty:
                            output = BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                invalid_df.to_excel(writer, index=False, sheet_name='Invalid_URLs')
                            
                            output.seek(0)
                            
                            st.download_button(
                                label="⬇️ Скачать проблемные строки",
                                data=output.getvalue(),
                                file_name=f"invalid_urls_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                        else:
                            st.info("Нет проблемных строк")

# ============================
# ОСНОВНОЙ КОД ПРИЛОЖЕНИЯ
# ============================
def initialize_application():
    """Инициализация приложения"""
    try:
        # Гарантируем инициализацию всех атрибутов session_state
        ensure_session_state_initialized()
        
        # Создаем необходимые директории
        os.makedirs("templates", exist_ok=True)
        os.makedirs("output_infographics", exist_ok=True)
        
        # Инициализация шаблонов
        if not st.session_state.template_cache_initialized:
            with st.spinner("🔄 Инициализация шаблонов..."):
                DynamicTemplateManager.ensure_templates_dir()
                
                # Загружаем шаблоны в кэш
                st.session_state.loaded_templates = {}
                for template_id in DynamicTemplateManager.BUILTIN_TEMPLATES.keys():
                    st.session_state.loaded_templates[template_id] = DynamicTemplateManager.BUILTIN_TEMPLATES[template_id]
                
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
    # Гарантируем инициализацию перед показом интерфейса
    ensure_session_state_initialized()
    
    # Заголовок
    st.title("🚀 Генератор Инфографики PRO v8.1")
    st.markdown("---")
    
    # Создаем табы
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Анализ данных",
        "🎯 Предпросмотр",
        "⚡ Обработка",
        "📈 Статистика",
        "🎨 Шаблоны"
    ])
    
    # Инициализируем генератор
    generator = InfographicGenerator()
    
    # Боковая панель
    UIComponents.render_sidebar()
    
    # Содержимое табов
    with tab1:
        UIComponents.render_data_quality_tab()
    
    with tab2:
        UIComponents.render_preview_tab(generator)
    
    with tab3:
        UIComponents.render_processing_tab(generator)
    
    with tab4:
        UIComponents.render_statistics_tab()
    
    with tab5:
        UIComponents.render_templates_tab()

def main():
    """Основная функция приложения"""
    try:
        # Проверяем инициализацию
        if not hasattr(st.session_state, 'app_initialized') or not st.session_state.app_initialized:
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
