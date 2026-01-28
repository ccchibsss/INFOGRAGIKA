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
import uuid

# ============================
# НАСТРОЙКА ПРИЛОЖЕНИЯ
# ============================
st.set_page_config(
    page_title="🎯 Генератор Инфографики PRO v9.0",
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
        'local_save_path': None,
        'use_column_a_for_filenames': True,
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
            'sale': '⚡ Распродажа',
            'custom': '🔧 Пользовательские'
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
        'current_batch_index': 0,
        'custom_templates': {},
        'template_editor_active': False,
        'template_editor_data': {
            'name': 'Новый шаблон',
            'description': 'Описание шаблона',
            'category': 'custom',
            'layout': {
                'width': 1200,
                'height': 800,
                'header_height': 15,
                'footer_height': 10,
                'corner_radius': 20,
                'shadow': True,
                'border': True
            },
            'backgrounds': {
                'header': 'gradient_blue',
                'footer': 'gradient_dark',
                'main': 'white'
            },
            'blocks': [],
            'effects': {
                'shadow': True,
                'gradient': True,
                'rounded_corners': True
            }
        }
    }
    
    for key, default_value in defaults.items():
        if not hasattr(st.session_state, key):
            safe_set_session_state(key, default_value)
        elif getattr(st.session_state, key) is None:
            safe_set_session_state(key, default_value)
        elif key == 'column_mapping' and (not isinstance(st.session_state.column_mapping, dict) or len(st.session_state.column_mapping) == 0):
            safe_set_session_state(key, default_value)

# ============================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ФАЙЛОВ
# ============================
def get_safe_filename(text, max_length=100):
    """Создание безопасного имени файла из текста"""
    if pd.isna(text) or not text:
        return "unnamed"
    
    text = str(text).strip()
    safe_text = re.sub(r'[<>:"/\\|?*]', '_', text)
    safe_text = re.sub(r'\s+', '_', safe_text)
    safe_text = re.sub(r'_+', '_', safe_text)
    
    if len(safe_text) > max_length:
        if '.' in safe_text:
            name, ext = safe_text.rsplit('.', 1)
            safe_text = name[:max_length-len(ext)-1] + '.' + ext
        else:
            safe_text = safe_text[:max_length]
    
    return safe_text

def setup_local_save_path(selected_path=None):
    """Настройка пути для локального сохранения"""
    if selected_path is None:
        default_paths = [
            os.path.join(os.path.expanduser("~"), "Desktop", "Инфографики"),
            os.path.join(os.path.expanduser("~"), "Documents", "Инфографики"),
            os.path.join(os.getcwd(), "output_infographics")
        ]
        
        for path in default_paths:
            try:
                os.makedirs(path, exist_ok=True)
                if os.access(path, os.W_OK):
                    return path
            except:
                continue
        
        return os.getcwd()
    else:
        try:
            os.makedirs(selected_path, exist_ok=True)
            if os.access(selected_path, os.W_OK):
                return selected_path
            else:
                st.warning(f"Нет прав на запись в папку: {selected_path}")
                return os.getcwd()
        except Exception as e:
            st.error(f"Ошибка создания папки: {e}")
            return os.getcwd()

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
# СИСТЕМА ШАБЛОНОВ С ФОНАМИ И КАСТОМИЗАЦИЕЙ
# ============================
class DynamicTemplateManager:
    """Класс для управления динамическими шаблонами с фонами"""
    
    TEMPLATES_DIR = "templates"
    CUSTOM_TEMPLATES_DIR = "custom_templates"
    
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
            },
            "blocks": [
                {
                    "id": "block_1",
                    "name": "Название товара",
                    "type": "text",
                    "section": "main",
                    "position": {"x": 0.05, "y": 0.15},
                    "align": "left",
                    "max_width": 0.4,
                    "font_size": 32,
                    "color": [0, 0, 0, 255],
                    "column_mapping": "top_left"
                },
                {
                    "id": "block_2",
                    "name": "Цена",
                    "type": "text",
                    "section": "main",
                    "position": {"x": 0.95, "y": 0.15},
                    "align": "right",
                    "max_width": 0.4,
                    "font_size": 28,
                    "color": [0, 0, 0, 255],
                    "column_mapping": "top_right"
                },
                {
                    "id": "block_3",
                    "name": "Описание",
                    "type": "text",
                    "section": "main",
                    "position": {"x": 0.05, "y": 0.85},
                    "align": "left",
                    "max_width": 0.4,
                    "font_size": 24,
                    "color": [0, 0, 0, 255],
                    "column_mapping": "bottom_left"
                },
                {
                    "id": "block_4",
                    "name": "Скидка",
                    "type": "text",
                    "section": "main",
                    "position": {"x": 0.95, "y": 0.85},
                    "align": "right",
                    "max_width": 0.4,
                    "font_size": 20,
                    "color": [0, 0, 0, 255],
                    "column_mapping": "bottom_right"
                },
                {
                    "id": "block_5",
                    "name": "Категория",
                    "type": "text",
                    "section": "header",
                    "position": {"x": 0.05, "y": 0.5},
                    "align": "left",
                    "max_width": 0.4,
                    "font_size": 24,
                    "color": [255, 255, 255, 255],
                    "column_mapping": "header_left"
                },
                {
                    "id": "block_6",
                    "name": "Бренд",
                    "type": "text",
                    "section": "header",
                    "position": {"x": 0.95, "y": 0.5},
                    "align": "right",
                    "max_width": 0.4,
                    "font_size": 20,
                    "color": [255, 255, 255, 255],
                    "column_mapping": "header_right"
                },
                {
                    "id": "block_7",
                    "name": "Доставка",
                    "type": "text",
                    "section": "footer",
                    "position": {"x": 0.05, "y": 0.5},
                    "align": "left",
                    "max_width": 0.4,
                    "font_size": 18,
                    "color": [255, 255, 255, 255],
                    "column_mapping": "footer_left"
                },
                {
                    "id": "block_8",
                    "name": "Рейтинг",
                    "type": "text",
                    "section": "footer",
                    "position": {"x": 0.95, "y": 0.5},
                    "align": "right",
                    "max_width": 0.4,
                    "font_size": 16,
                    "color": [255, 255, 255, 255],
                    "column_mapping": "footer_right"
                }
            ]
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
        """Создание директорий для шаблонов если их нет"""
        try:
            os.makedirs(DynamicTemplateManager.TEMPLATES_DIR, exist_ok=True)
            os.makedirs(DynamicTemplateManager.CUSTOM_TEMPLATES_DIR, exist_ok=True)
            
            for template_id in DynamicTemplateManager.BUILTIN_TEMPLATES.keys():
                filepath = os.path.join(DynamicTemplateManager.TEMPLATES_DIR, f"{template_id}.json")
                
                if not os.path.exists(filepath):
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(DynamicTemplateManager.BUILTIN_TEMPLATES[template_id], f, ensure_ascii=False, indent=2)
            
            logger.info(f"Директории шаблонов готовы: {DynamicTemplateManager.TEMPLATES_DIR}, {DynamicTemplateManager.CUSTOM_TEMPLATES_DIR}")
            return True
        except Exception as e:
            logger.error(f"Ошибка создания директорий шаблонов: {e}")
            return False
    
    @staticmethod
    def load_template(template_id: str) -> Dict:
        """Загрузка шаблона по ID"""
        if (hasattr(st.session_state, 'loaded_templates') and
            st.session_state.loaded_templates and
            template_id in st.session_state.loaded_templates):
            return st.session_state.loaded_templates[template_id]
        
        builtin_path = os.path.join(DynamicTemplateManager.TEMPLATES_DIR, f"{template_id}.json")
        custom_path = os.path.join(DynamicTemplateManager.CUSTOM_TEMPLATES_DIR, f"{template_id}.json")
        
        if os.path.exists(builtin_path):
            filepath = builtin_path
        elif os.path.exists(custom_path):
            filepath = custom_path
        else:
            if template_id in DynamicTemplateManager.BUILTIN_TEMPLATES:
                template_data = DynamicTemplateManager.BUILTIN_TEMPLATES[template_id].copy()
                template_data['id'] = template_id
                
                if not hasattr(st.session_state, 'loaded_templates'):
                    st.session_state.loaded_templates = {}
                st.session_state.loaded_templates[template_id] = template_data
                
                return template_data
            else:
                return DynamicTemplateManager.get_default_template()
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            if 'colors' in template_data:
                for color_key, color_value in template_data['colors'].items():
                    if isinstance(color_value, list):
                        template_data['colors'][color_key] = tuple(color_value)
            
            template_data['id'] = template_id
            
            if 'blocks' not in template_data:
                template_data['blocks'] = DynamicTemplateManager.convert_positions_to_blocks(template_data)
            
            if not hasattr(st.session_state, 'loaded_templates'):
                st.session_state.loaded_templates = {}
            st.session_state.loaded_templates[template_id] = template_data
            
            return template_data
        except Exception as e:
            logger.error(f"Ошибка загрузки шаблона {template_id}: {e}")
            return DynamicTemplateManager.get_default_template()
    
    @staticmethod
    def convert_positions_to_blocks(template_data: Dict) -> List[Dict]:
        """Конвертация старых позиций в блоки"""
        blocks = []
        
        if 'text_positions' in template_data:
            for position_key, position_data in template_data['text_positions'].items():
                block = {
                    "id": f"block_{position_key}",
                    "name": position_key.replace('_', ' ').title(),
                    "type": "text",
                    "section": position_data.get('section', 'main'),
                    "position": {"x": position_data.get('x', 0.5), "y": position_data.get('y', 0.5)},
                    "align": position_data.get('align', 'center'),
                    "max_width": position_data.get('max_width', 0.8),
                    "font_size": template_data.get('font_sizes', {}).get(position_key, 24),
                    "color": template_data.get('colors', {}).get(position_key, [0, 0, 0, 255]),
                    "column_mapping": position_key
                }
                blocks.append(block)
        
        return blocks
    
    @staticmethod
    def get_default_template() -> Dict:
        """Получение шаблона по умолчанию"""
        default_template = DynamicTemplateManager.BUILTIN_TEMPLATES.get("modern_shop", {}).copy()
        default_template['id'] = 'default'
        return default_template
    
    @staticmethod
    def get_template_names() -> List[Tuple[str, str]]:
        """Получение списка всех доступных шаблонов"""
        template_names = []
        
        for template_id, template_data in DynamicTemplateManager.BUILTIN_TEMPLATES.items():
            display_name = template_data.get('name', template_id)
            template_names.append((template_id, display_name))
        
        custom_templates = DynamicTemplateManager.load_custom_templates()
        for template_id, template_data in custom_templates.items():
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
        
        if category == "all" or category == "custom":
            custom_templates = DynamicTemplateManager.load_custom_templates()
            for template_id, template_data in custom_templates.items():
                if category == "all" or template_data.get("category") == category:
                    display_name = template_data.get('name', template_id)
                    template_names.append((template_id, display_name))
        
        return template_names
    
    @staticmethod
    def load_custom_templates() -> Dict:
        """Загрузка пользовательских шаблонов"""
        custom_templates = {}
        
        try:
            if os.path.exists(DynamicTemplateManager.CUSTOM_TEMPLATES_DIR):
                for filename in os.listdir(DynamicTemplateManager.CUSTOM_TEMPLATES_DIR):
                    if filename.endswith('.json'):
                        template_id = filename[:-5]
                        filepath = os.path.join(DynamicTemplateManager.CUSTOM_TEMPLATES_DIR, filename)
                        
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                template_data = json.load(f)
                            
                            custom_templates[template_id] = template_data
                        except Exception as e:
                            logger.error(f"Ошибка загрузки пользовательского шаблона {filename}: {e}")
        except Exception as e:
            logger.error(f"Ошибка чтения директории пользовательских шаблонов: {e}")
        
        if hasattr(st.session_state, 'custom_templates'):
            custom_templates.update(st.session_state.custom_templates)
        
        return custom_templates
    
    @staticmethod
    def save_custom_template(template_data: Dict) -> str:
        """Сохранение пользовательского шаблона"""
        try:
            template_id = template_data.get('id')
            if not template_id:
                template_id = f"custom_{uuid.uuid4().hex[:8]}"
                template_data['id'] = template_id
            
            if 'category' not in template_data:
                template_data['category'] = 'custom'
            
            filepath = os.path.join(DynamicTemplateManager.CUSTOM_TEMPLATES_DIR, f"{template_id}.json")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, ensure_ascii=False, indent=2)
            
            if not hasattr(st.session_state, 'custom_templates'):
                st.session_state.custom_templates = {}
            
            st.session_state.custom_templates[template_id] = template_data
            
            if not hasattr(st.session_state, 'loaded_templates'):
                st.session_state.loaded_templates = {}
            
            st.session_state.loaded_templates[template_id] = template_data
            
            logger.info(f"Пользовательский шаблон сохранен: {template_id}")
            return template_id
            
        except Exception as e:
            logger.error(f"Ошибка сохранения пользовательского шаблона: {e}")
            return None
    
    @staticmethod
    def delete_custom_template(template_id: str) -> bool:
        """Удаление пользовательского шаблона"""
        try:
            filepath = os.path.join(DynamicTemplateManager.CUSTOM_TEMPLATES_DIR, f"{template_id}.json")
            
            if os.path.exists(filepath):
                os.remove(filepath)
            
            if hasattr(st.session_state, 'custom_templates') and template_id in st.session_state.custom_templates:
                del st.session_state.custom_templates[template_id]
            
            if hasattr(st.session_state, 'loaded_templates') and template_id in st.session_state.loaded_templates:
                del st.session_state.loaded_templates[template_id]
            
            logger.info(f"Пользовательский шаблон удален: {template_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления пользовательского шаблона: {e}")
            return False
    
    @staticmethod
    def duplicate_template(template_id: str, new_name: str) -> str:
        """Дублирование шаблона"""
        try:
            template = DynamicTemplateManager.load_template(template_id)
            
            new_template = template.copy()
            new_template['id'] = f"custom_{uuid.uuid4().hex[:8]}"
            new_template['name'] = new_name
            new_template['description'] = f"Копия {template.get('name', template_id)}"
            new_template['category'] = 'custom'
            
            return DynamicTemplateManager.save_custom_template(new_template)
            
        except Exception as e:
            logger.error(f"Ошибка дублирования шаблона: {e}")
            return None
    
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
            'sale': '⚡ Распродажа',
            'custom': '🔧 Пользовательские'
        }

# ============================
# РЕДАКТОР ШАБЛОНОВ
# ============================
class TemplateEditor:
    """Класс для редактирования шаблонов"""
    
    @staticmethod
    def render_template_editor():
        """Интерфейс редактора шаблонов"""
        st.header("🔧 Редактор шаблонов")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            tab1, tab2, tab3, tab4 = st.tabs(["📝 Основное", "🎨 Внешний вид", "🧱 Блоки", "👁️ Предпросмотр"])
            
            with tab1:
                TemplateEditor.render_basic_settings()
            
            with tab2:
                TemplateEditor.render_appearance_settings()
            
            with tab3:
                TemplateEditor.render_blocks_editor()
            
            with tab4:
                TemplateEditor.render_template_preview()
        
        with col2:
            TemplateEditor.render_template_actions()
    
    @staticmethod
    def render_basic_settings():
        """Настройки основных параметров шаблона"""
        st.subheader("📝 Основные параметры")
        
        editor_data = st.session_state.template_editor_data
        
        editor_data['name'] = st.text_input(
            "Название шаблона",
            value=editor_data.get('name', 'Новый шаблон'),
            key="template_name"
        )
        
        editor_data['description'] = st.text_area(
            "Описание шаблона",
            value=editor_data.get('description', 'Описание шаблона'),
            key="template_description"
        )
        
        categories = DynamicTemplateManager.get_template_categories()
        category_options = list(categories.values())
        category_keys = list(categories.keys())
        
        current_category = editor_data.get('category', 'custom')
        current_index = category_keys.index(current_category) if current_category in category_keys else 0
        
        selected_category = st.selectbox(
            "Категория",
            category_options,
            index=current_index,
            key="template_category"
        )
        
        editor_data['category'] = category_keys[category_options.index(selected_category)]
        
        st.subheader("📐 Размеры")
        
        col1, col2 = st.columns(2)
        
        with col1:
            editor_data['layout']['width'] = st.number_input(
                "Ширина (px)",
                min_value=400,
                max_value=4000,
                value=editor_data['layout'].get('width', 1200),
                step=100,
                key="template_width"
            )
        
        with col2:
            editor_data['layout']['height'] = st.number_input(
                "Высота (px)",
                min_value=300,
                max_value=4000,
                value=editor_data['layout'].get('height', 800),
                step=100,
                key="template_height"
            )
    
    @staticmethod
    def render_appearance_settings():
        """Настройки внешнего вида шаблона"""
        st.subheader("🎨 Внешний вид")
        
        editor_data = st.session_state.template_editor_data
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Заголовок**")
            editor_data['layout']['header_height'] = st.slider(
                "Высота шапки (%)",
                0, 40,
                editor_data['layout'].get('header_height', 15),
                key="editor_header_height"
            )
            
            header_bgs = BackgroundLibrary.get_header_backgrounds()
            header_options = [bg['name'] for bg in header_bgs.values()]
            header_keys = list(header_bgs.keys())
            
            current_header = editor_data['backgrounds'].get('header_background', 'gradient_blue')
            if isinstance(current_header, dict):
                current_header = 'gradient_blue'
            
            header_idx = header_keys.index(current_header) if current_header in header_keys else 0
            
            selected_header = st.selectbox(
                "Фон шапки",
                header_options,
                index=header_idx,
                key="editor_header_bg"
            )
            
            editor_data['backgrounds']['header'] = header_keys[header_options.index(selected_header)]
        
        with col2:
            st.markdown("**Подвал**")
            editor_data['layout']['footer_height'] = st.slider(
                "Высота футера (%)",
                0, 40,
                editor_data['layout'].get('footer_height', 10),
                key="editor_footer_height"
            )
            
            footer_bgs = BackgroundLibrary.get_footer_backgrounds()
            footer_options = [bg['name'] for bg in footer_bgs.values()]
            footer_keys = list(footer_bgs.keys())
            
            current_footer = editor_data['backgrounds'].get('footer_background', 'gradient_dark')
            if isinstance(current_footer, dict):
                current_footer = 'gradient_dark'
            
            footer_idx = footer_keys.index(current_footer) if current_footer in footer_keys else 0
            
            selected_footer = st.selectbox(
                "Фон футера",
                footer_options,
                index=footer_idx,
                key="editor_footer_bg"
            )
            
            editor_data['backgrounds']['footer'] = footer_keys[footer_options.index(selected_footer)]
        
        st.markdown("**Основная область**")
        main_bgs = BackgroundLibrary.get_main_backgrounds()
        main_options = [bg['name'] for bg in main_bgs.values()]
        main_keys = list(main_bgs.keys())
        
        current_main = editor_data['backgrounds'].get('main_background', 'white')
        if isinstance(current_main, dict):
            current_main = 'white'
        
        main_idx = main_keys.index(current_main) if current_main in main_keys else 0
        
        selected_main = st.selectbox(
            "Основной фон",
            main_options,
            index=main_idx,
            key="editor_main_bg"
        )
        
        editor_data['backgrounds']['main'] = main_keys[main_options.index(selected_main)]
        
        st.subheader("🎭 Эффекты")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            editor_data['layout']['corner_radius'] = st.slider(
                "Скругление углов",
                0, 50,
                editor_data['layout'].get('corner_radius', 20),
                key="editor_corner_radius"
            )
        
        with col2:
            editor_data['layout']['shadow'] = st.checkbox(
                "Тень",
                value=editor_data['layout'].get('shadow', True),
                key="editor_shadow"
            )
        
        with col3:
            editor_data['layout']['border'] = st.checkbox(
                "Рамка",
                value=editor_data['layout'].get('border', True),
                key="editor_border"
            )
    
    @staticmethod
    def render_blocks_editor():
        """Редактор блоков"""
        st.subheader("🧱 Блоки текста")
        
        editor_data = st.session_state.template_editor_data
        
        if 'blocks' not in editor_data:
            editor_data['blocks'] = []
        
        blocks = editor_data['blocks']
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info(f"Всего блоков: {len(blocks)}")
        
        with col2:
            if st.button("➕ Добавить блок", key="add_block"):
                new_block = {
                    "id": f"block_{uuid.uuid4().hex[:8]}",
                    "name": f"Блок {len(blocks) + 1}",
                    "type": "text",
                    "section": "main",
                    "position": {"x": 0.5, "y": 0.5},
                    "align": "center",
                    "max_width": 0.8,
                    "font_size": 24,
                    "color": [0, 0, 0, 255],
                    "column_mapping": f"custom_{len(blocks) + 1}"
                }
                blocks.append(new_block)
                st.rerun()
        
        for i, block in enumerate(blocks):
            with st.expander(f"📝 {block.get('name', f'Блок {i+1}')}", expanded=i==0):
                col1, col2 = st.columns(2)
                
                with col1:
                    block['name'] = st.text_input(
                        "Название блока",
                        value=block.get('name', f'Блок {i+1}'),
                        key=f"block_name_{i}"
                    )
                    
                    block_type = st.selectbox(
                        "Тип блока",
                        ["text", "badge", "icon"],
                        index=["text", "badge", "icon"].index(block.get('type', 'text')),
                        key=f"block_type_{i}"
                    )
                    block['type'] = block_type
                    
                    sections = ["header", "main", "footer"]
                    current_section = block.get('section', 'main')
                    section_idx = sections.index(current_section) if current_section in sections else 1
                    
                    block['section'] = st.selectbox(
                        "Раздел",
                        sections,
                        index=section_idx,
                        key=f"block_section_{i}"
                    )
                
                with col2:
                    st.markdown("**Позиция**")
                    
                    col_x, col_y = st.columns(2)
                    
                    with col_x:
                        block['position']['x'] = st.slider(
                            "X (%)",
                            0.0, 1.0,
                            block['position'].get('x', 0.5),
                            0.01,
                            key=f"block_x_{i}"
                        )
                    
                    with col_y:
                        block['position']['y'] = st.slider(
                            "Y (%)",
                            0.0, 1.0,
                            block['position'].get('y', 0.5),
                            0.01,
                            key=f"block_y_{i}"
                        )
                    
                    align_options = ["left", "center", "right"]
                    current_align = block.get('align', 'center')
                    align_idx = align_options.index(current_align) if current_align in align_options else 1
                    
                    block['align'] = st.selectbox(
                        "Выравнивание",
                        align_options,
                        index=align_idx,
                        key=f"block_align_{i}"
                    )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    block['max_width'] = st.slider(
                        "Макс. ширина (%)",
                        0.1, 1.0,
                        block.get('max_width', 0.8),
                        0.05,
                        key=f"block_max_width_{i}"
                    )
                    
                    block['font_size'] = st.number_input(
                        "Размер шрифта",
                        8, 100,
                        block.get('font_size', 24),
                        key=f"block_font_size_{i}"
                    )
                
                with col2:
                    color = block.get('color', [0, 0, 0, 255])
                    if isinstance(color, list) and len(color) == 4:
                        hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                    else:
                        hex_color = "#000000"
                    
                    new_color = st.color_picker(
                        "Цвет текста",
                        value=hex_color,
                        key=f"block_color_{i}"
                    )
                    
                    if new_color.startswith('#'):
                        r = int(new_color[1:3], 16)
                        g = int(new_color[3:5], 16)
                        b = int(new_color[5:7], 16)
                        block['color'] = [r, g, b, 255]
                
                block['column_mapping'] = st.text_input(
                    "ID для маппинга колонок",
                    value=block.get('column_mapping', f"custom_{i+1}"),
                    key=f"block_mapping_{i}",
                    help="Этот ID будет использоваться для привязки колонок из Excel"
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("⬆️ Вверх", key=f"move_up_{i}"):
                        if i > 0:
                            blocks[i], blocks[i-1] = blocks[i-1], blocks[i]
                            st.rerun()
                
                with col2:
                    if st.button("🗑️ Удалить", key=f"delete_block_{i}", type="secondary"):
                        blocks.pop(i)
                        st.rerun()
    
    @staticmethod
    def render_template_preview():
        """Предпросмотр шаблона"""
        st.subheader("👁️ Предпросмотр шаблона")
        
        editor_data = st.session_state.template_editor_data
        
        preview_width = 600
        preview_height = int(preview_width * editor_data['layout']['height'] / editor_data['layout']['width'])
        
        try:
            canvas = ImageProcessor.create_template_canvas(
                preview_width,
                preview_height,
                "modern_shop"  # Базовый шаблон для структуры
            )
            
            draw = ImageDraw.Draw(canvas)
            
            header_height = int(preview_height * editor_data['layout']['header_height'] / 100)
            footer_height = int(preview_height * editor_data['layout']['footer_height'] / 100)
            main_height = preview_height - header_height - footer_height
            
            draw.rectangle([0, 0, preview_width, header_height], outline=(255, 0, 0), width=2)
            draw.rectangle([0, header_height, preview_width, header_height + main_height], outline=(0, 255, 0), width=2)
            draw.rectangle([0, header_height + main_height, preview_width, preview_height], outline=(0, 0, 255), width=2)
            
            font = FontManager.load_system_font('system_arial', 14)
            
            draw.text((10, 10), "ШАПКА", font=font, fill=(255, 255, 255))
            draw.text((10, header_height + 10), "ОСНОВНОЕ", font=font, fill=(255, 255, 255))
            draw.text((10, header_height + main_height + 10), "ПОДВАЛ", font=font, fill=(255, 255, 255))
            
            blocks = editor_data.get('blocks', [])
            for block in blocks:
                section = block.get('section', 'main')
                
                if section == 'header':
                    section_y = 0
                    section_height = header_height
                elif section == 'footer':
                    section_y = header_height + main_height
                    section_height = footer_height
                else:
                    section_y = header_height
                    section_height = main_height
                
                x = block['position']['x'] * preview_width
                y = section_y + (block['position']['y'] * section_height)
                
                max_width = block.get('max_width', 0.8) * preview_width
                
                draw.rectangle(
                    [x - 5, y - 5, x + max_width + 5, y + 30],
                    fill=(255, 255, 255, 180),
                    outline=(0, 0, 0)
                )
                
                block_font = FontManager.load_system_font('system_arial', 12)
                draw.text((x, y), block.get('name', 'Блок'), font=block_font, fill=(0, 0, 0))
                
                draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 0, 0))
            
            st.image(canvas, caption="Предпросмотр шаблона", width='stretch')
            
            st.info(f"**Размер:** {editor_data['layout']['width']}×{editor_data['layout']['height']} px")
            st.info(f"**Блоков:** {len(blocks)}")
            
        except Exception as e:
            st.error(f"Ошибка создания предпросмотра: {e}")
    
    @staticmethod
    def render_template_actions():
        """Действия с шаблоном"""
        st.subheader("💾 Действия")
        
        editor_data = st.session_state.template_editor_data
        
        if st.button("💾 Сохранить шаблон", type="primary", use_container_width=True):
            template_id = DynamicTemplateManager.save_custom_template(editor_data)
            if template_id:
                st.success(f"✅ Шаблон сохранен: {editor_data['name']}")
                st.session_state.template_editor_active = False
                st.rerun()
            else:
                st.error("❌ Ошибка сохранения шаблона")
        
        st.divider()
        
        st.subheader("📂 Загрузить шаблон")
        
        template_names = DynamicTemplateManager.get_template_names()
        template_options = [name for _, name in template_names]
        template_ids = [tid for tid, _ in template_names]
        
        selected_template = st.selectbox(
            "Выберите шаблон для загрузки",
            ["Новый шаблон"] + template_options,
            key="load_template_select"
        )
        
        if selected_template != "Новый шаблон":
            selected_index = template_options.index(selected_template)
            template_id = template_ids[selected_index]
            
            if st.button("📥 Загрузить", use_container_width=True):
                template = DynamicTemplateManager.load_template(template_id)
                st.session_state.template_editor_data = template.copy()
                st.success(f"✅ Шаблон загружен: {template['name']}")
                st.rerun()
        
        st.divider()
        
        if st.button("🔄 Создать новый", use_container_width=True):
            st.session_state.template_editor_data = {
                'name': 'Новый шаблон',
                'description': 'Описание шаблона',
                'category': 'custom',
                'layout': {
                    'width': 1200,
                    'height': 800,
                    'header_height': 15,
                    'footer_height': 10,
                    'corner_radius': 20,
                    'shadow': True,
                    'border': True
                },
                'backgrounds': {
                    'header': 'gradient_blue',
                    'footer': 'gradient_dark',
                    'main': 'white'
                },
                'blocks': [],
                'effects': {
                    'shadow': True,
                    'gradient': True,
                    'rounded_corners': True
                }
            }
            st.rerun()
        
        if st.button("📤 Экспорт в JSON", use_container_width=True):
            template_json = json.dumps(editor_data, ensure_ascii=False, indent=2)
            st.download_button(
                label="⬇️ Скачать JSON",
                data=template_json,
                file_name=f"{editor_data['name'].replace(' ', '_')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        uploaded_file = st.file_uploader(
            "📥 Импорт из JSON",
            type=['json'],
            key="import_template"
        )
        
        if uploaded_file:
            try:
                template_data = json.load(uploaded_file)
                st.session_state.template_editor_data = template_data
                st.success("✅ Шаблон загружен из файла")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Ошибка загрузки файла: {e}")
        
        if st.button("🚪 Выйти из редактора", type="secondary", use_container_width=True):
            st.session_state.template_editor_active = False
            st.rerun()

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
            try:
                content = uploaded_file.getvalue()[:50]
                if b'PK' in content:
                    return 'xlsx'
                elif b'\xD0\xCF\x11\xE0' in content:
                    return 'xls'
            except:
                pass
            return 'xlsx'
    
    @staticmethod
    def read_excel_with_fallback(uploaded_file) -> Optional[pd.DataFrame]:
        """Чтение Excel файла с несколькими попытками и обработкой ошибок"""
        try:
            uploaded_file.seek(0)
            file_format = AdvancedExcelProcessor.detect_excel_format(uploaded_file)
            
            if file_format in ['xlsx', 'xlsm']:
                try:
                    df = pd.read_excel(
                        uploaded_file,
                        engine='openpyxl',
                        dtype=str,
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
            
            df = AdvancedExcelProcessor.clean_dataframe(df)
            
            logger.info(f"Файл успешно загружен: {uploaded_file.name}, строк: {len(df)}, колонок: {len(df.columns)}")
            return df
            
        except Exception as e:
            logger.error(f"Критическая ошибка чтения Excel: {e}")
            st.error(f"Ошибка чтения файла: {str(e)}")
            
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
        
        df = df.copy()
        df.columns = [str(col).strip() for col in df.columns]
        df = df.fillna('')
        
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].apply(lambda x: str(x).strip() if isinstance(x, str) else x)
        
        initial_len = len(df)
        df = df[df.astype(str).ne('').any(axis=1)].copy()
        removed_rows = initial_len - len(df)
        
        if removed_rows > 0:
            logger.info(f"Удалено {removed_rows} полностью пустых строк")
        
        initial_len = len(df)
        df = df.drop_duplicates().copy()
        removed_duplicates = initial_len - len(df)
        
        if removed_duplicates > 0:
            logger.info(f"Удалено {removed_duplicates} дубликатов")
        
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
        
        for col in df.columns:
            non_empty_count = df[col].astype(bool).sum()
            empty_count = len(df) - non_empty_count
            
            if empty_count > 0:
                validation_result['empty_cells'] += empty_count
            
            if any(keyword in str(col).lower() for keyword in ['url', 'link', 'image', 'фото', 'картинка', 'ссылка']):
                validation_result['url_columns'].append(col)
                
                url_samples = df[col].head(5).dropna().tolist()
                valid_urls = 0
                for url in url_samples:
                    if isinstance(url, str) and len(url) > 10:
                        if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                            valid_urls += 1
                
                if valid_urls == 0 and len(url_samples) > 0:
                    validation_result['warnings'].append(f"Колонка '{col}' может не содержать валидные URL изображений")
        
        required_keywords = ['url', 'image', 'name', 'title', 'product']
        found_keywords = []
        
        for col in df.columns:
            col_lower = str(col).lower()
            for keyword in required_keywords:
                if keyword in col_lower and col not in found_keywords:
                    found_keywords.append(col)
        
        if len(found_keywords) == 0:
            validation_result['warnings'].append("Не найдены колонки с URL или названиями товаров")
        
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
            'confidence': {}
        }
        
        if df is None or df.empty:
            return suggestions
        
        column_stats = {}
        
        for col in df.columns:
            col_str = str(col).lower()
            col_data = df[col].dropna().astype(str)
            
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
            
            url_patterns = ['.jpg', '.jpeg', '.png', '.webp', 'http://', 'https://', 'www.']
            url_count = sum(any(pattern in val.lower() for pattern in url_patterns) 
                          for val in col_data.head(20))
            
            if url_count > 5:
                stats['has_urls'] = True
                stats['keywords'].extend(['url', 'image'])
            
            price_patterns = ['$', '€', '₽', 'руб', 'грн', 'цена', 'price', 'стоимость']
            price_count = sum(any(pattern in val.lower() for pattern in price_patterns) 
                            for val in col_data.head(20))
            
            try:
                numeric_data = pd.to_numeric(col_data.str.replace(r'[^\d.]', '', regex=True), errors='coerce')
                numeric_percentage = (numeric_data.notna().sum() / len(col_data)) * 100
                if numeric_percentage > 50:
                    stats['has_numbers'] = True
                    stats['keywords'].extend(['price', 'number', 'numeric'])
            except:
                pass
            
            text_keywords = ['название', 'name', 'title', 'товар', 'product', 'описание', 'description']
            text_match = any(keyword in col_str for keyword in text_keywords)
            
            if text_match or stats['avg_length'] > 20:
                stats['has_text'] = True
                stats['keywords'].extend(['text', 'name', 'description'])
            
            column_stats[col] = stats
        
        for col, stats in column_stats.items():
            col_lower = str(col).lower()
            confidence = 0
            
            if stats['has_urls']:
                suggestions['image_url'] = col
                suggestions['confidence']['image_url'] = 90
            elif any(keyword in col_lower for keyword in ['url', 'link', 'image', 'фото', 'картинка']):
                suggestions['image_url'] = col
                suggestions['confidence']['image_url'] = 70
            
            if any(keyword in col_lower for keyword in ['название', 'name', 'title', 'товар', 'product']):
                suggestions['top_left'] = col
                suggestions['confidence']['top_left'] = 85
            elif stats['has_text'] and stats['unique_count'] > len(df) * 0.7:
                suggestions['top_left'] = col
                suggestions['confidence']['top_left'] = 60
            
            if any(keyword in col_lower for keyword in ['цена', 'price', 'стоимость', 'руб', '$', '€']):
                suggestions['top_right'] = col
                suggestions['confidence']['top_right'] = 80
            elif stats['has_numbers'] and stats['unique_count'] < len(df) * 0.3:
                suggestions['top_right'] = col
                suggestions['confidence']['top_right'] = 65
            
            if any(keyword in col_lower for keyword in ['описание', 'description', 'характеристики', 'features', 'детали']):
                suggestions['bottom_left'] = col
                suggestions['confidence']['bottom_left'] = 75
            elif stats['has_text'] and stats['avg_length'] > 50:
                suggestions['bottom_left'] = col
                suggestions['confidence']['bottom_left'] = 55
            
            if any(keyword in col_lower for keyword in ['скидка', 'discount', 'акция', 'sale', 'распродажа']):
                suggestions['bottom_right'] = col
                suggestions['confidence']['bottom_right'] = 70
            
            if any(keyword in col_lower for keyword in ['артикул', 'sku', 'код', 'id', 'номер', 'article']):
                suggestions['filename'] = col
                suggestions['confidence']['filename'] = 85
            elif stats['unique_count'] == len(df) and stats['max_length'] < 20:
                suggestions['filename'] = col
                suggestions['confidence']['filename'] = 60
            
            if any(keyword in col_lower for keyword in ['тег', 'tag', 'категория', 'category', 'раздел', 'section']):
                suggestions['header_left'] = col
                suggestions['confidence']['header_left'] = 75
            
            if any(keyword in col_lower for keyword in ['бренд', 'brand', 'производитель', 'manufacturer', 'марка']):
                suggestions['header_right'] = col
                suggestions['confidence']['header_right'] = 75
            
            if any(keyword in col_lower for keyword in ['доставка', 'delivery', 'срок', 'term', 'время', 'time']):
                suggestions['footer_left'] = col
                suggestions['confidence']['footer_left'] = 70
            
            if any(keyword in col_lower for keyword in ['рейтинг', 'rating', 'отзывы', 'reviews', 'оценка', 'score']):
                suggestions['footer_right'] = col
                suggestions['confidence']['footer_right'] = 70
        
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
            st.dataframe(column_df, width='stretch')
        
        with st.expander("⚠️ Выявленные проблемы"):
            problems = []
            
            for col in df.columns:
                if df[col].isna().all() or (df[col].astype(str).str.strip() == '').all():
                    problems.append(f"Колонка '{col}' полностью пустая")
            
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
        df_filtered = df.copy()
        
        def is_valid_url(url):
            if pd.isna(url) or not isinstance(url, str):
                return False
            
            url_str = url.strip()
            
            if len(url_str) < 10:
                return False
            
            valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tiff']
            has_extension = any(url_str.lower().endswith(ext) for ext in valid_extensions)
            
            has_protocol = url_str.startswith(('http://', 'https://', '//', 'www.'))
            
            has_domain = '.' in url_str and len(url_str.split('.')[-1]) >= 2
            
            return (has_extension or has_protocol) and has_domain
        
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
                
                if not hasattr(st.session_state, 'font_cache'):
                    st.session_state.font_cache = {}
                
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
        
        if len(url) < 10 or not (url.startswith('http') or url.startswith('//') or '.' in url):
            logger.warning(f"Некорректный URL: {url}")
            return None
        
        if url.startswith('//'):
            url = 'https:' + url
        elif url.startswith('www.'):
            url = 'https://' + url
        elif not url.startswith('http'):
            url = 'https://' + url
        
        if hasattr(st.session_state, 'image_cache') and st.session_state.image_cache:
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
                    'Referer': 'https://www.google.com/'
                }
                
                response = requests.get(url, timeout=timeout, headers=headers, verify=True)
                response.raise_for_status()
                
                content_type = response.headers.get('content-type', '').lower()
                if 'image' not in content_type:
                    if len(response.content) < 100:
                        logger.warning(f"Слишком маленький ответ: {len(response.content)} байт")
                        continue
                    
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
                time.sleep(1 * (attempt + 1))
            
            except Exception as e:
                logger.error(f"Неожиданная ошибка при загрузке {url[:50]}...: {e}")
                if attempt == retries:
                    return None
                time.sleep(1)
        
        return None
    
    @staticmethod
    def create_template_canvas(width: int, height: int, template_id: str = "modern_shop") -> Image.Image:
        """Создание холста шаблона с фонами"""
        try:
            template = DynamicTemplateManager.load_template(template_id)
            layout = template.get("layout", {})
            
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
            
            header_height_percent = max(0, min(background_settings.get('header_height', 15), 100))
            footer_height_percent = max(0, min(background_settings.get('footer_height', 10), 100 - header_height_percent))
            
            header_height = int(height * header_height_percent / 100)
            footer_height = int(height * footer_height_percent / 100)
            main_height = height - header_height - footer_height
            
            if main_height < 0:
                main_height = 0
                header_height = int(height * 0.7)
                footer_height = height - header_height
            
            canvas = Image.new('RGBA', (width, height), (255, 255, 255, 0))
            
            header_bg_key = background_settings.get('header_background', 'gradient_blue')
            footer_bg_key = background_settings.get('footer_background', 'gradient_dark')
            main_bg_key = background_settings.get('main_background', 'white')
            
            header_bgs = BackgroundLibrary.get_header_backgrounds()
            footer_bgs = BackgroundLibrary.get_footer_backgrounds()
            main_bgs = BackgroundLibrary.get_main_backgrounds()
            
            if header_height > 0 and header_bg_key in header_bgs:
                try:
                    header_bg = BackgroundLibrary.create_background(width, header_height, header_bgs[header_bg_key])
                    canvas.paste(header_bg, (0, 0))
                except Exception as e:
                    logger.error(f"Ошибка создания фона шапки: {e}")
                    header_bg = Image.new('RGB', (width, header_height), (30, 144, 255))
                    canvas.paste(header_bg, (0, 0))
            
            if main_height > 0 and main_bg_key in main_bgs:
                try:
                    main_bg = BackgroundLibrary.create_background(width, main_height, main_bgs[main_bg_key])
                    canvas.paste(main_bg, (0, header_height))
                except Exception as e:
                    logger.error(f"Ошибка создания основного фона: {e}")
                    main_bg = Image.new('RGB', (width, main_height), (255, 255, 255))
                    canvas.paste(main_bg, (0, header_height))
            
            if footer_height > 0 and footer_bg_key in footer_bgs:
                try:
                    footer_bg = BackgroundLibrary.create_background(width, footer_height, footer_bgs[footer_bg_key])
                    footer_y = header_height + main_height
                    if footer_y + footer_height > height:
                        footer_y = height - footer_height
                    canvas.paste(footer_bg, (0, footer_y))
                except Exception as e:
                    logger.error(f"Ошибка создания фона футера: {e}")
                    footer_bg = Image.new('RGB', (width, footer_height), (33, 37, 41))
                    footer_y = header_height + main_height
                    if footer_y + footer_height > height:
                        footer_y = height - footer_height
                    canvas.paste(footer_bg, (0, footer_y))
            
            corner_radius = background_settings.get('corner_radius', 20)
            if corner_radius > 0:
                min_side = min(width, height)
                radius = min(corner_radius, min_side // 2)
                try:
                    canvas = ImageProcessor.add_rounded_corners(canvas, radius)
                except Exception as e:
                    logger.error(f"Ошибка добавления скругленных углов: {e}")
            
            if background_settings.get('shadow_enabled', True):
                try:
                    canvas = ImageProcessor.add_shadow_effect(canvas)
                except Exception as e:
                    logger.error(f"Ошибка добавления тени: {e}")
            
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
            return Image.new('RGBA', (width, height), (255, 255, 255, 255))
    
    @staticmethod
    def get_template_content_area(canvas: Image.Image) -> Tuple[int, int, int, int]:
        """Определяет область содержимого в шаблоне"""
        try:
            if canvas.mode != 'RGBA':
                canvas = canvas.convert('RGBA')
            
            alpha = canvas.getchannel('A')
            opaque_pixels = []
            
            for y in range(canvas.height):
                for x in range(canvas.width):
                    if alpha.getpixel((x, y)) > 0:
                        opaque_pixels.append((x, y))
            
            if not opaque_pixels:
                return 0, 0, canvas.width, canvas.height
            
            x_coords = [p[0] for p in opaque_pixels]
            y_coords = [p[1] for p in opaque_pixels]
            
            x1 = min(x_coords)
            y1 = min(y_coords)
            x2 = max(x_coords)
            y2 = max(y_coords)
            
            padding = 10
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(canvas.width, x2 + padding)
            y2 = min(canvas.height, y2 + padding)
            
            return x1, y1, x2, y2
            
        except Exception as e:
            logger.error(f"Ошибка определения области содержимого: {e}")
            return 0, 0, canvas.width, canvas.height
    
    @staticmethod
    def add_rounded_corners(img: Image.Image, radius: int) -> Image.Image:
        """Добавление скругленных углов"""
        if radius <= 0:
            return img
        
        mask = Image.new('L', img.size, 0)
        draw = ImageDraw.Draw(mask)
        
        width, height = img.size
        
        draw.rectangle([0, radius, width, height - radius], fill=255)
        draw.rectangle([radius, 0, width - radius, height], fill=255)
        
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
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        shadow_size = min(shadow_size, 15)
        shadow_width = img.width + shadow_size * 2
        shadow_height = img.height + shadow_size * 2
        shadow = Image.new('RGBA', (shadow_width, shadow_height), (0, 0, 0, 0))
        
        shadow_base = Image.new('RGBA', (img.width, img.height), (0, 0, 0, 80))
        shadow.paste(shadow_base, (shadow_size, shadow_size))
        
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=shadow_size/2))
        
        final_img = Image.new('RGBA', (shadow_width, shadow_height), (255, 255, 255, 0))
        final_img.paste(shadow, (0, 0), shadow)
        
        final_img.paste(img, (shadow_size, shadow_size), img)
        
        return final_img
    
    @staticmethod
    def add_border(img: Image.Image, border_color: str, border_width: int = 2) -> Image.Image:
        """Добавление рамки внутри изображения"""
        width, height = img.size
        border_width = min(border_width, min(width, height) // 20)
        
        border_img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
        border_img.paste(img, (0, 0))
        
        draw = ImageDraw.Draw(border_img)
        
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
        
        draw.rectangle([0, 0, width-1, height-1], outline=border_rgba, width=border_width)
        
        return border_img
    
    @staticmethod
    def add_text_to_image(img: Image.Image, text_data: Dict, template_id: str = "modern_shop") -> Image.Image:
        """Добавление текста на изображение по шаблону"""
        try:
            template = DynamicTemplateManager.load_template(template_id)
            draw = ImageDraw.Draw(img)
            
            font_settings = safe_get_session_state('font_settings', {})
            main_font_key = font_settings.get('main_font', 'system_arial')
            font_size_multiplier = font_settings.get('font_size_multiplier', 1.0)
            
            text_positions = template.get("text_positions", {})
            blocks = template.get("blocks", [])
            
            if not blocks and text_positions:
                blocks = DynamicTemplateManager.convert_positions_to_blocks(template)
            
            background_settings = safe_get_session_state('background_settings', {})
            header_height_percent = max(0, min(background_settings.get('header_height', 15), 100))
            footer_height_percent = max(0, min(background_settings.get('footer_height', 10), 100 - header_height_percent))
            
            header_height = int(img.height * header_height_percent / 100)
            footer_height = int(img.height * footer_height_percent / 100)
            main_height = img.height - header_height - footer_height
            
            if main_height < 0:
                main_height = img.height - header_height
                footer_height = 0
            
            safe_margin = 10
            header_safe_top = safe_margin
            header_safe_bottom = header_height - safe_margin
            
            main_safe_top = header_height + safe_margin
            main_safe_bottom = header_height + main_height - safe_margin
            
            footer_safe_top = header_height + main_height + safe_margin
            footer_safe_bottom = img.height - safe_margin
            
            filled_positions = []
            for block in blocks:
                column_mapping = block.get('column_mapping')
                if column_mapping and column_mapping in text_data and text_data[column_mapping]:
                    text = str(text_data[column_mapping]).strip()
                    if text and text.lower() not in ['nan', 'none', 'null', '']:
                        filled_positions.append(block)
            
            if not filled_positions:
                return img
            
            for block in filled_positions:
                column_mapping = block.get('column_mapping')
                text = str(text_data.get(column_mapping, '')).strip()
                
                if not text or text.lower() in ['nan', 'none', 'null', '']:
                    continue
                
                section = block.get("section", "main")
                
                x_percent = max(0.0, min(1.0, block.get("position", {}).get("x", 0.5)))
                y_percent = max(0.0, min(1.0, block.get("position", {}).get("y", 0.5)))
                
                if section == "header":
                    if header_height > 10:
                        section_y_range = header_safe_bottom - header_safe_top
                        if section_y_range > 0:
                            y = header_safe_top + (y_percent * section_y_range)
                        else:
                            y = header_safe_top
                        
                        y = max(header_safe_top, min(y, header_safe_bottom))
                    else:
                        continue
                
                elif section == "footer":
                    if footer_height > 10:
                        section_y_range = footer_safe_bottom - footer_safe_top
                        if section_y_range > 0:
                            y = footer_safe_top + (y_percent * section_y_range)
                        else:
                            y = footer_safe_top
                        
                        y = max(footer_safe_top, min(y, footer_safe_bottom))
                    else:
                        continue
                
                else:
                    section_y_range = main_safe_bottom - main_safe_top
                    if section_y_range > 0:
                        y = main_safe_top + (y_percent * section_y_range)
                    else:
                        y = main_safe_top
                    
                    y = max(main_safe_top, min(y, main_safe_bottom))
                
                x = x_percent * img.width
                
                text_offset_settings = safe_get_session_state('text_offset_settings', {})
                if column_mapping in text_offset_settings:
                    offset = text_offset_settings[column_mapping]
                    x += offset.get('x_offset', 0) * img.width / 100
                    y += offset.get('y_offset', 0) * img.height / 100
                
                safe_left = safe_margin
                safe_right = img.width - safe_margin
                
                x = max(safe_left, min(x, safe_right))
                
                align = block.get("align", "center")
                
                base_size = block.get('font_size', 24)
                
                font_size_settings = safe_get_session_state('font_size_settings', {})
                size_percentage = font_size_settings.get(column_mapping, 100) / 100.0
                
                font_size_multiplier = font_settings.get('font_size_multiplier', 1.0)
                
                font_size = int(base_size * size_percentage * font_size_multiplier)
                
                min_font_size = 8
                max_font_size = min(img.width, img.height) // 10
                font_size = max(min_font_size, min(font_size, max_font_size))
                
                try:
                    font = FontManager.get_font(main_font_key, font_size)
                except:
                    font = FontManager.load_system_font('system_arial', font_size)
                
                color = block.get('color', [0, 0, 0, 255])
                if isinstance(color, list):
                    text_color = tuple(color)
                else:
                    text_color = (0, 0, 0, 255)
                
                try:
                    if hasattr(draw, 'textbbox'):
                        bbox = draw.textbbox((0, 0), text, font=font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                    else:
                        text_width, text_height = draw.textsize(text, font=font)
                    
                    max_width_percent = block.get('max_width', 0.8)
                    max_pixels = max_width_percent * img.width
                    
                    if text_width > max_pixels:
                        scale_factor = max_pixels / text_width
                        new_font_size = int(font_size * scale_factor * 0.9)
                        if new_font_size >= min_font_size:
                            font_size = new_font_size
                            try:
                                font = FontManager.get_font(main_font_key, font_size)
                            except:
                                font = FontManager.load_system_font('system_arial', font_size)
                            
                            if hasattr(draw, 'textbbox'):
                                bbox = draw.textbbox((0, 0), text, font=font)
                                text_width = bbox[2] - bbox[0]
                                text_height = bbox[3] - bbox[1]
                            else:
                                text_width, text_height = draw.textsize(text, font=font)
                    
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
                    
                    else:
                        if x + text_width > safe_right:
                            x = safe_right - text_width
                        if x < safe_left:
                            x = safe_left
                    
                    if y - text_height/2 < safe_margin:
                        y = safe_margin + text_height/2
                    if y + text_height/2 > img.height - safe_margin:
                        y = img.height - safe_margin - text_height/2
                    
                except Exception as e:
                    logger.warning(f"Ошибка проверки размера текста '{text}': {e}")
                
                try:
                    if align == "center":
                        draw.text((x, y), text, font=font, fill=text_color, anchor="mm")
                    elif align == "right":
                        draw.text((x, y), text, font=font, fill=text_color, anchor="rm")
                    else:
                        draw.text((x, y), text, font=font, fill=text_color, anchor="lm")
                    
                    logger.debug(f"Текст добавлен: {column_mapping} = '{text[:30]}...' at ({x:.1f},{y:.1f}), размер: {font_size}")
                    
                except Exception as e:
                    logger.error(f"Ошибка добавления текста '{text[:30]}...': {e}")
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
            
            scale = settings.get('scale', 100) / 100
            max_width_percent = settings.get('max_width', 30)
            max_height_percent = settings.get('max_height', 30)
            
            max_width = max_width_percent * background.width / 100
            max_height = max_height_percent * background.height / 100
            
            overlay_ratio = overlay.width / overlay.height
            new_width = min(int(max_width * scale), background.width // 2)
            new_height = int(new_width / overlay_ratio)
            
            if new_height > max_height:
                new_height = int(max_height)
                new_width = int(new_height * overlay_ratio)
            
            new_width = max(10, new_width)
            new_height = max(10, new_height)
            
            overlay_resized = overlay.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
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
            
            x += int(settings.get('x_offset', 0) * background.width / 100)
            y += int(settings.get('y_offset', 0) * background.height / 100)
            
            x = max(0, min(x, background.width - new_width))
            y = max(0, min(y, background.height - new_height))
            
            opacity = settings.get('opacity', 100)
            if opacity < 100:
                alpha = overlay_resized.split()[3]
                alpha = alpha.point(lambda p: p * opacity / 100)
                overlay_resized.putalpha(alpha)
            
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
# ОСНОВНОЙ ПРОЦЕССОР С ЛОКАЛЬНЫМ СОХРАНЕНИЕМ
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
        
        if 'image_url' in column_mapping and column_mapping['image_url']:
            url_col = column_mapping['image_url']
            if url_col in row:
                url = row[url_col]
                if pd.isna(url) or not isinstance(url, str) or len(str(url).strip()) < 10:
                    validation['is_valid'] = False
                    validation['errors'].append(f"Невалидный URL: {url}")
        
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
            column_mapping = safe_get_session_state('column_mapping', {})
            validation = self.validate_row_data(row, column_mapping)
            
            if not validation['is_valid']:
                return {
                    'row_index': row_index,
                    'status': 'error',
                    'message': f"Валидация не пройдена: {', '.join(validation['errors'])}",
                    'validation_warnings': validation['warnings']
                }
            
            if validation['warnings']:
                logger.warning(f"Строка {row_index}: {', '.join(validation['warnings'])}")
            
            return self.process_single_row(row, row_index)
            
        except Exception as e:
            logger.error(f"Ошибка валидации строки {row_index}: {e}")
            return {
                'row_index': row_index,
                'status': 'error',
                'message': f"Ошибка валидации: {str(e)}"
            }
    
    def process_single_row(self, row: pd.Series, row_index: int) -> Dict:
        """Обработка одной строки с сохранением в локальную папку"""
        try:
            ensure_session_state_initialized()
            
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
            
            column_mapping = safe_get_session_state('column_mapping', {})
            
            image_url = None
            url_column_name = None
            if 'image_url' in column_mapping and column_mapping['image_url']:
                url_column_name = column_mapping['image_url']
            
            if url_column_name and url_column_name in row_dict:
                url_value = row_dict.get(url_column_name)
                
                if url_value is not None and pd.notna(url_value):
                    url_str = str(url_value).strip()
                    
                    if url_str and len(url_str) > 5:
                        is_valid_url = (
                            url_str.startswith('http://') or 
                            url_str.startswith('https://') or
                            url_str.startswith('//') or
                            url_str.startswith('www.') or
                            '.' in url_str and any(ext in url_str.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif'])
                        )
                        
                        if is_valid_url:
                            if url_str.startswith('//'):
                                image_url = 'https:' + url_str
                            elif url_str.startswith('www.'):
                                image_url = 'https://' + url_str
                            else:
                                image_url = url_str
            
            if not image_url:
                return {
                    'row_index': row_index,
                    'status': 'error',
                    'message': f'Нет URL изображения в колонке "{url_column_name}"'
                }
            
            template = DynamicTemplateManager.load_template(st.session_state.current_template)
            blocks = template.get('blocks', [])
            
            text_data = {}
            for block in blocks:
                column_key = block.get('column_mapping')
                if column_key:
                    if column_key in column_mapping and column_mapping[column_key]:
                        col = column_mapping[column_key]
                        if col in row_dict:
                            value = row_dict[col]
                            if pd.isna(value):
                                text_data[column_key] = ''
                            else:
                                text_data[column_key] = str(value)
                        else:
                            text_data[column_key] = ''
                    else:
                        text_data[column_key] = ''
            
            overlay_url = None
            if ('overlay_image_url' in column_mapping and 
                column_mapping['overlay_image_url']):
                col = column_mapping['overlay_image_url']
                if col in row_dict and pd.notna(row_dict[col]):
                    overlay_url = str(row_dict[col]).strip()
                    if not overlay_url or overlay_url.lower() in ['nan', 'none', '']:
                        overlay_url = None
            
            # ГЕНЕРАЦИЯ ИМЕНИ ФАЙЛА
            filename = f"item_{row_index:04d}"
            
            # Получаем первую колонку DataFrame
            first_column = None
            if hasattr(st.session_state, 'df') and st.session_state.df is not None:
                first_column = st.session_state.df.columns[0] if len(st.session_state.df.columns) > 0 else None
            
            # Используем столбец A для имени файла если включена опция
            use_column_a = safe_get_session_state('use_column_a_for_filenames', True)
            
            if use_column_a and first_column and first_column in row_dict:
                filename_source = row_dict.get(first_column)
                if filename_source is not None and pd.notna(filename_source):
                    filename = get_safe_filename(filename_source)
            else:
                # Используем колонку filename из настроек
                if 'filename' in column_mapping and column_mapping['filename']:
                    col = column_mapping['filename']
                    if col in row_dict and pd.notna(row_dict[col]):
                        filename_source = str(row_dict[col]).strip()
                        if filename_source:
                            filename = get_safe_filename(filename_source)
            
            # ПУТЬ ДЛЯ СОХРАНЕНИЯ
            output_dir = safe_get_session_state('local_save_path', safe_get_session_state('output_dir', 'output_infographics'))
            
            processing_settings = safe_get_session_state('processing_settings', {})
            timeout = processing_settings.get('timeout', 30)
            retries = processing_settings.get('retry_count', 3)
            
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
            
            export_settings = safe_get_session_state('export_settings', {})
            
            if export_settings.get('resize', True):
                target_size = export_settings.get('target_size', 1200)
                main_img = self.image_processor.resize_image(main_img, target_size)
            
            current_template = safe_get_session_state('current_template', 'modern_shop')
            
            canvas = self.image_processor.create_template_canvas(
                main_img.width, main_img.height, current_template
            )
            
            background_settings = safe_get_session_state('background_settings', {})
            header_height_percent = max(0, min(background_settings.get('header_height', 15), 100))
            header_height = int(main_img.height * header_height_percent / 100)
            
            footer_height_percent = max(0, min(background_settings.get('footer_height', 10), 100 - header_height_percent))
            footer_height = int(main_img.height * footer_height_percent / 100)
            main_height = main_img.height - header_height - footer_height
            
            if main_height <= 0:
                main_height = main_img.height - header_height
                if main_height <= 0:
                    main_height = main_img.height
            
            final_img = canvas.copy()
            
            if main_img.height > main_height:
                scale_ratio = main_height / main_img.height
                new_width = int(main_img.width * scale_ratio)
                new_height = main_height
                main_img_resized = main_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            else:
                main_img_resized = main_img
            
            if main_img_resized.width < canvas.width:
                x_offset = (canvas.width - main_img_resized.width) // 2
            else:
                scale_ratio = canvas.width / main_img_resized.width
                if scale_ratio < 1:
                    new_width = canvas.width
                    new_height = int(main_img_resized.height * scale_ratio)
                    main_img_resized = main_img_resized.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    x_offset = 0
                else:
                    x_offset = 0
            
            y_offset = header_height
            if y_offset + main_img_resized.height > canvas.height:
                y_offset = max(0, canvas.height - main_img_resized.height)
            
            if x_offset + main_img_resized.width > canvas.width:
                x_offset = max(0, canvas.width - main_img_resized.width)
            
            final_img.paste(main_img_resized, (x_offset, y_offset))
            
            final_img = self.image_processor.add_text_to_image(
                final_img, text_data, current_template
            )
            
            image_overlay_settings = safe_get_session_state('image_overlay_settings', {})
            if overlay_url and image_overlay_settings.get('enabled', False):
                overlay_img = self.image_processor.load_image_from_url(overlay_url, timeout=15)
                
                if overlay_img:
                    final_img = self.image_processor.add_image_overlay(
                        final_img,
                        overlay_img,
                        image_overlay_settings
                    )
            
            # СОХРАНЕНИЕ В ЛОКАЛЬНУЮ ПАПКУ
            format_ext = export_settings.get('format', 'PNG').lower()
            
            # Проверяем уникальность имени файла
            base_filename = filename
            counter = 1
            while True:
                filepath = os.path.join(output_dir, f"{filename}.{format_ext}")
                if not os.path.exists(filepath):
                    break
                filename = f"{base_filename}_{counter}"
                counter += 1
                if counter > 100:
                    filename = f"{base_filename}_{row_index}"
                    break
            
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
                    'url': image_url[:50] + '...',
                    'used_column_a_name': use_column_a and first_column is not None
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
        
        output_dir = safe_get_session_state('local_save_path', safe_get_session_state('output_dir', 'output_infographics'))
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Используется папка для сохранения: {output_dir}")
            
            if not os.access(output_dir, os.W_OK):
                st.error(f"❌ Нет прав на запись в папку: {output_dir}")
                return results
                
        except Exception as e:
            logger.error(f"Ошибка создания папки {output_dir}: {e}")
            st.error(f"❌ Ошибка создания папки: {e}")
            return results
        
        processing_settings = safe_get_session_state('processing_settings', {})
        max_workers = min(processing_settings.get('max_workers', 4), total)
        max_workers = max(1, max_workers)
        
        logger.info(f"Начало обработки {total} строк, потоков: {max_workers}, сохранение в: {output_dir}")
        
        stats = {
            'total': total,
            'success': 0,
            'no_url': 0,
            'load_failed': 0,
            'other_errors': 0
        }
        
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
            
            for idx in range(start_idx, end_idx + 1):
                future = executor.submit(process_wrapper, idx)
                futures.append(future)
            
            completed = 0
            error_messages = []
            
            for future in as_completed(futures):
                try:
                    timeout = processing_settings.get('timeout', 30) + 10
                    result = future.result(timeout=timeout)
                    results.append(result)
                    completed += 1
                    
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
                        
                        if len(error_messages) < 10:
                            error_messages.append(f"Строка {result.get('row_index')}: {result.get('message')}")
                    
                    progress = completed / total
                    progress_bar.progress(progress)
                    
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
        
        logger.info(f"Обработка завершена. Статистика: {stats}. Сохранено в: {output_dir}")
        
        if error_messages:
            with st.expander("📋 Подробности ошибок", expanded=False):
                for error in error_messages:
                    st.error(error)
        
        st.info(f"📁 Файлы сохранены в: `{output_dir}`")
        
        try:
            if os.name == 'nt':
                os.startfile(output_dir)
            elif os.name == 'posix':
                import subprocess
                subprocess.Popen(['xdg-open', output_dir])
        except:
            pass
        
        st.session_state.batch_results = results
        return results
    
    def create_zip_archive(self, results: List[Dict]) -> Optional[str]:
        """Создание ZIP архива"""
        try:
            output_dir = safe_get_session_state('local_save_path', safe_get_session_state('output_dir', 'output_infographics'))
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_path = os.path.join(output_dir, f"infographics_{timestamp}.zip")
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                added_count = 0
                for result in results:
                    if result.get('status') == 'success' and 'filepath' in result:
                        filepath = result['filepath']
                        if os.path.exists(filepath):
                            arcname = os.path.relpath(filepath, output_dir)
                            zipf.write(filepath, arcname)
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
        """Боковая панель с настройками сохранения"""
        with st.sidebar:
            st.title("⚙️ Настройки")
            
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
                        df = AdvancedExcelProcessor.read_excel_with_fallback(uploaded_file)
                        
                        if df is not None:
                            st.session_state.df = df
                            st.session_state.uploaded_file_name = uploaded_file.name
                            
                            validation = AdvancedExcelProcessor.validate_dataframe(df)
                            suggestions = AdvancedExcelProcessor.get_intelligent_column_suggestions(df)
                            
                            for key in suggestions:
                                if suggestions[key] and key != 'confidence':
                                    st.session_state.column_mapping[key] = suggestions[key]
                            
                            if validation['warnings']:
                                with st.expander("⚠️ Предупреждения", expanded=True):
                                    for warning in validation['warnings']:
                                        st.warning(warning)
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Строк", validation['total_rows'])
                            with col2:
                                st.metric("Колонок", validation['total_columns'])
                            with col3:
                                st.metric("URL колонок", len(validation['url_columns']))
                            
                            st.success(f"✅ Файл загружен успешно!")
                            
                            if validation['warnings'] and any('URL' in warning for warning in validation['warnings']):
                                if st.button("🚫 Автофильтрация невалидных URL", type="secondary"):
                                    url_col = st.session_state.column_mapping.get('image_url')
                                    if url_col:
                                        df_filtered = AdvancedExcelProcessor.filter_invalid_urls(df, url_col)
                                        st.session_state.df = df_filtered
                                        st.success(f"Осталось {len(df_filtered)} строк после фильтрации")
                                        st.rerun()
            
            if st.session_state.df is not None:
                with st.expander("👁️ Предпросмотр данных"):
                    preview_rows = st.slider("Строк", 5, 50, 10, key="preview_rows")
                    st.dataframe(st.session_state.df.head(preview_rows), width='stretch')
            
            st.subheader("💾 Локальное сохранение")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                save_path_input = st.text_input(
                    "Путь для сохранения файлов",
                    value=st.session_state.get('local_save_path', 
                                              os.path.join(os.path.expanduser("~"), "Desktop", "Инфографики")),
                    key="save_path_input"
                )
            
            with col2:
                st.write("")
                if st.button("📁 Выбрать папку", key="browse_folder"):
                    predefined_paths = [
                        os.path.join(os.path.expanduser("~"), "Desktop", "Инфографики"),
                        os.path.join(os.path.expanduser("~"), "Documents", "Инфографики"),
                        os.path.join(os.path.expanduser("~"), "Downloads", "Инфографики"),
                        os.path.join(os.getcwd(), "output_infographics")
                    ]
                    
                    selected_path = st.selectbox(
                        "Выберите папку",
                        predefined_paths,
                        key="folder_selector"
                    )
                    
                    if selected_path:
                        st.session_state.local_save_path = selected_path
                        st.session_state.save_path_input = selected_path
                        st.rerun()
            
            if save_path_input:
                try:
                    os.makedirs(save_path_input, exist_ok=True)
                    if os.access(save_path_input, os.W_OK):
                        st.session_state.local_save_path = save_path_input
                        st.success(f"✅ Папка доступна: {save_path_input}")
                    else:
                        st.error(f"❌ Нет прав на запись в папку")
                except Exception as e:
                    st.error(f"❌ Ошибка доступа к папке: {e}")
            
            st.session_state.use_column_a_for_filenames = st.checkbox(
                "📝 Использовать названия из первого столбца (A) для имен файлов",
                value=st.session_state.get('use_column_a_for_filenames', True),
                key="use_column_a"
            )
            
            if st.session_state.use_column_a_for_filenames and st.session_state.df is not None:
                first_column = st.session_state.df.columns[0] if len(st.session_state.df.columns) > 0 else "Нет столбца"
                st.info(f"📋 Первый столбец: **{first_column}**")
            
            if st.session_state.get('local_save_path'):
                try:
                    if os.name == 'nt':
                        import ctypes
                        free_bytes = ctypes.c_ulonglong(0)
                        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                            ctypes.c_wchar_p(st.session_state.local_save_path), 
                            None, None, ctypes.pointer(free_bytes)
                        )
                        free_gb = free_bytes.value / (1024**3)
                    else:
                        stat = os.statvfs(st.session_state.local_save_path)
                        free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
                    
                    st.caption(f"💾 Свободно: {free_gb:.1f} GB")
                except:
                    pass
            
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
            
            st.subheader("🎨 Фоны")
            
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
            
            col1, col2 = st.columns(2)
            with col1:
                header_height = st.slider(
                    "Высота шапки (%)",
                    5, 40, st.session_state.background_settings.get('header_height', 15),
                    key="header_height"
                )
                st.session_state.background_settings['header_height'] = min(header_height, 100)
            
            with col2:
                footer_height = st.slider(
                    "Высота футера (%)",
                    5, 40, st.session_state.background_settings.get('footer_height', 10),
                    key="footer_height"
                )
                st.session_state.background_settings['footer_height'] = min(footer_height, 100 - header_height)
            
            corner_radius = st.slider(
                "Скругление углов",
                0, 50, st.session_state.background_settings.get('corner_radius', 20),
                key="corner_radius"
            )
            st.session_state.background_settings['corner_radius'] = corner_radius
            
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.background_settings['shadow_enabled'] = st.checkbox(
                    "Тень",
                    value=st.session_state.background_settings.get('shadow_enabled', True),
                    key="shadow"
                )
            
            with col2:
                st.session_state.background_settings['border_enabled'] = st.checkbox(
                    "Рамка",
                    value=st.session_state.background_settings.get('border_enabled', True),
                    key="border"
                )
            
            if st.session_state.background_settings.get('border_enabled', True):
                st.session_state.background_settings['border_color'] = st.color_picker(
                    "Цвет рамки",
                    value=st.session_state.background_settings.get('border_color', '#e0e0e0'),
                    key="border_color"
                )
                border_width = st.slider(
                    "Толщина",
                    1, 10, st.session_state.background_settings.get('border_width', 2),
                    key="border_width"
                )
                st.session_state.background_settings['border_width'] = min(border_width, 10)
            
            st.subheader("💾 Формат экспорта")
            
            col1, col2 = st.columns(2)
            with col1:
                format_ = st.selectbox(
                    "Формат",
                    ["PNG", "JPEG", "WebP"],
                    index=["PNG", "JPEG", "WebP"].index(st.session_state.export_settings.get('format', 'PNG')) 
                    if st.session_state.export_settings.get('format') in ["PNG", "JPEG", "WebP"] else 0,
                    key="export_format"
                )
                st.session_state.export_settings['format'] = format_
            
            with col2:
                quality = st.slider(
                    "Качество",
                    50, 100, st.session_state.export_settings.get('quality', 95),
                    key="export_quality"
                )
                st.session_state.export_settings['quality'] = quality
            
            st.session_state.export_settings['resize'] = st.checkbox(
                "Изменять размер",
                value=st.session_state.export_settings.get('resize', True),
                key="resize"
            )
            
            if st.session_state.export_settings.get('resize', True):
                st.session_state.export_settings['target_size'] = st.select_slider(
                    "Макс. размер",
                    options=[800, 1200, 1600, 2000],
                    value=st.session_state.export_settings.get('target_size', 1200),
                    key="target_size"
                )
            
            st.subheader("⚡ Обработка")
            
            col1, col2 = st.columns(2)
            with col1:
                batch_size = st.select_slider(
                    "Размер партии",
                    options=[10, 25, 50, 100],
                    value=st.session_state.processing_settings.get('batch_size', 50),
                    key="batch_size"
                )
                st.session_state.processing_settings['batch_size'] = batch_size
            
            with col2:
                max_workers = st.select_slider(
                    "Потоки",
                    options=[1, 2, 4, 6],
                    value=st.session_state.processing_settings.get('max_workers', 4),
                    key="max_workers"
                )
                st.session_state.processing_settings['max_workers'] = max_workers
            
            st.session_state.processing_settings['timeout'] = st.select_slider(
                "Таймаут (сек)",
                options=[10, 15, 30, 45],
                value=st.session_state.processing_settings.get('timeout', 30),
                key="timeout"
            )
            
            st.divider()
            processed_count = safe_get_session_state('processed_count', 0)
            st.caption(f"Обработано: {processed_count}")
            st.caption("Версия: 9.0 (с редактором шаблонов)")
    
    @staticmethod
    def render_column_mapping():
        """Настройка маппинга колонок"""
        if st.session_state.df is None:
            return
        
        st.subheader("📊 Настройка колонок")
        
        if len(st.session_state.df.columns) > 0:
            first_column = st.session_state.df.columns[0]
            st.info(f"📝 **Столбец A (первый столбец):** `{first_column}` - будет использоваться для имен файлов")
        
        available_columns = st.session_state.df.columns.tolist()
        
        template = DynamicTemplateManager.load_template(st.session_state.current_template)
        blocks = template.get('blocks', [])
        
        if not blocks:
            # Используем старый интерфейс для совместимости
            col1, col2 = st.columns(2)
            
            with col1:
                top_left_default = st.session_state.column_mapping.get('top_left')
                top_left_idx = available_columns.index(top_left_default) if top_left_default in available_columns else 0
                st.session_state.column_mapping['top_left'] = st.selectbox(
                    "Верхний левый (основной)",
                    available_columns,
                    index=top_left_idx,
                    key="col_top_left"
                )
                
                top_right_default = st.session_state.column_mapping.get('top_right')
                top_right_idx = available_columns.index(top_right_default) if top_right_default in available_columns else min(1, len(available_columns)-1)
                st.session_state.column_mapping['top_right'] = st.selectbox(
                    "Верхний правый (основной)",
                    available_columns,
                    index=top_right_idx,
                    key="col_top_right"
                )
                
                bottom_left_default = st.session_state.column_mapping.get('bottom_left')
                bottom_left_idx = available_columns.index(bottom_left_default) if bottom_left_default in available_columns else min(2, len(available_columns)-1)
                st.session_state.column_mapping['bottom_left'] = st.selectbox(
                    "Нижний левый (основной)",
                    available_columns,
                    index=bottom_left_idx,
                    key="col_bottom_left"
                )
                
                bottom_right_default = st.session_state.column_mapping.get('bottom_right')
                bottom_right_idx = available_columns.index(bottom_right_default) if bottom_right_default in available_columns else min(3, len(available_columns)-1)
                st.session_state.column_mapping['bottom_right'] = st.selectbox(
                    "Нижний правый (основной)",
                    available_columns,
                    index=bottom_right_idx,
                    key="col_bottom_right"
                )
            
            with col2:
                header_left_default = st.session_state.column_mapping.get('header_left')
                header_left_idx = available_columns.index(header_left_default) if header_left_default in available_columns else min(4, len(available_columns)-1)
                st.session_state.column_mapping['header_left'] = st.selectbox(
                    "Левый (шапка)",
                    available_columns,
                    index=header_left_idx,
                    key="col_header_left"
                )
                
                header_right_default = st.session_state.column_mapping.get('header_right')
                header_right_idx = available_columns.index(header_right_default) if header_right_default in available_columns else min(5, len(available_columns)-1)
                st.session_state.column_mapping['header_right'] = st.selectbox(
                    "Правый (шапка)",
                    available_columns,
                    index=header_right_idx,
                    key="col_header_right"
                )
                
                footer_left_default = st.session_state.column_mapping.get('footer_left')
                footer_left_idx = available_columns.index(footer_left_default) if footer_left_default in available_columns else min(6, len(available_columns)-1)
                st.session_state.column_mapping['footer_left'] = st.selectbox(
                    "Левый (футер)",
                    available_columns,
                    index=footer_left_idx,
                    key="col_footer_left"
                )
                
                footer_right_default = st.session_state.column_mapping.get('footer_right')
                footer_right_idx = available_columns.index(footer_right_default) if footer_right_default in available_columns else min(7, len(available_columns)-1)
                st.session_state.column_mapping['footer_right'] = st.selectbox(
                    "Правый (футер)",
                    available_columns,
                    index=footer_right_idx,
                    key="col_footer_right"
                )
                
                image_url_default = st.session_state.column_mapping.get('image_url')
                image_url_idx = available_columns.index(image_url_default) if image_url_default in available_columns else min(8, len(available_columns)-1)
                st.session_state.column_mapping['image_url'] = st.selectbox(
                    "URL изображения",
                    available_columns,
                    index=image_url_idx,
                    key="col_image_url"
                )
                
                filename_default = st.session_state.column_mapping.get('filename')
                filename_idx = available_columns.index(filename_default) if filename_default in available_columns else 0
                st.session_state.column_mapping['filename'] = st.selectbox(
                    "Имя файла (запасное)",
                    available_columns,
                    index=filename_idx,
                    key="col_filename"
                )
        else:
            # Новый интерфейс для шаблонов с блоками
            st.info(f"📋 Шаблон содержит {len(blocks)} блоков")
            
            for i, block in enumerate(blocks):
                block_name = block.get('name', f'Блок {i+1}')
                column_mapping_key = block.get('column_mapping', f'block_{i+1}')
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    default_col = st.session_state.column_mapping.get(column_mapping_key)
                    col_idx = available_columns.index(default_col) if default_col in available_columns else 0
                    
                    st.session_state.column_mapping[column_mapping_key] = st.selectbox(
                        f"{block_name} ({block.get('section', 'main')})",
                        available_columns,
                        index=col_idx,
                        key=f"col_block_{i}"
                    )
                
                with col2:
                    section = block.get('section', 'main')
                    section_icon = "📌" if section == "header" else ("📄" if section == "main" else "📊")
                    st.caption(f"{section_icon} {section}")
        
        if st.button("🔍 Автоподбор", key="auto_map"):
            suggestions = AdvancedExcelProcessor.get_intelligent_column_suggestions(st.session_state.df)
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
                    "Общий размер шрифта",
                    0.5, 2.0, st.session_state.font_settings.get('font_size_multiplier', 1.0), 0.1,
                    key="font_size"
                )
    
    @staticmethod
    def render_text_offsets():
        """Смещения текста"""
        st.subheader("🎯 Смещение текста")
        
        template = DynamicTemplateManager.load_template(st.session_state.current_template)
        blocks = template.get('blocks', [])
        
        if not blocks:
            # Старый интерфейс для совместимости
            symmetrical = st.checkbox(
                "Симметричные смещения",
                value=st.session_state.get('symmetrical_offsets', False),
                key="symmetrical_offsets"
            )
            st.session_state.symmetrical_offsets = symmetrical
            
            if symmetrical:
                col1, col2 = st.columns(2)
                with col1:
                    x_offset = st.number_input(
                        "Смещение X (%)",
                        -100, 100, st.session_state.text_offset_settings.get('top_left', {}).get('x_offset', 0),
                        key="sym_x"
                    )
                with col2:
                    y_offset = st.number_input(
                        "Смещение Y (%)",
                        -100, 100, st.session_state.text_offset_settings.get('top_left', {}).get('y_offset', 0),
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
                            st.session_state.text_offset_settings.get(pos, {}).get('x_offset', 0),
                            key=f"offset_x_{pos}"
                        )
                        y = st.number_input(
                            "Y (%)",
                            -100, 100,
                            st.session_state.text_offset_settings.get(pos, {}).get('y_offset', 0),
                            key=f"offset_y_{pos}"
                        )
                        st.session_state.text_offset_settings[pos] = {
                            'x_offset': x,
                            'y_offset': y
                        }
                
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
                            st.session_state.text_offset_settings.get(pos, {}).get('x_offset', 0),
                            key=f"offset_x_{pos}"
                        )
                        y = st.number_input(
                            "Y (%)",
                            -100, 100,
                            st.session_state.text_offset_settings.get(pos, {}).get('y_offset', 0),
                            key=f"offset_y_{pos}"
                        )
                        st.session_state.text_offset_settings[pos] = {
                            'x_offset': x,
                            'y_offset': y
                        }
                
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
                            st.session_state.text_offset_settings.get(pos, {}).get('x_offset', 0),
                            key=f"offset_x_{pos}"
                        )
                        y = st.number_input(
                            "Y (%)",
                            -100, 100,
                            st.session_state.text_offset_settings.get(pos, {}).get('y_offset', 0),
                            key=f"offset_y_{pos}"
                        )
                        st.session_state.text_offset_settings[pos] = {
                            'x_offset': x,
                            'y_offset': y
                        }
        else:
            # Новый интерфейс для шаблонов с блоками
            st.info(f"Настройте смещение для каждого блока")
            
            for i, block in enumerate(blocks):
                block_name = block.get('name', f'Блок {i+1}')
                column_mapping_key = block.get('column_mapping', f'block_{i+1}')
                
                with st.expander(f"🎯 {block_name}", expanded=i < 3):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        x = st.number_input(
                            "Смещение X (%)",
                            -100, 100,
                            st.session_state.text_offset_settings.get(column_mapping_key, {}).get('x_offset', 0),
                            key=f"offset_x_{column_mapping_key}"
                        )
                    
                    with col2:
                        y = st.number_input(
                            "Смещение Y (%)",
                            -100, 100,
                            st.session_state.text_offset_settings.get(column_mapping_key, {}).get('y_offset', 0),
                            key=f"offset_y_{column_mapping_key}"
                        )
                    
                    st.session_state.text_offset_settings[column_mapping_key] = {
                        'x_offset': x,
                        'y_offset': y
                    }
        
        if st.button("🔄 Сбросить смещения", key="reset_offsets"):
            for key in st.session_state.text_offset_settings.keys():
                st.session_state.text_offset_settings[key] = {
                    'x_offset': 0,
                    'y_offset': 0
                }
            st.rerun()
    
    @staticmethod
    def render_font_sizes():
        """Настройки размера текста"""
        st.subheader("🔠 Размер текста")
        
        template = DynamicTemplateManager.load_template(st.session_state.current_template)
        blocks = template.get('blocks', [])
        
        if not blocks:
            # Старый интерфейс для совместимости
            symmetrical = st.checkbox(
                "Одинаковый размер для всех полей",
                value=st.session_state.get('symmetrical_font_sizes', False),
                key="symmetrical_font_sizes"
            )
            st.session_state.symmetrical_font_sizes = symmetrical
            
            if symmetrical:
                size_percentage = st.slider(
                    "Размер текста (%)",
                    50, 200, st.session_state.font_size_settings.get('top_left', 100),
                    key="sym_font_size"
                )
                
                for key in ['top_left', 'top_right', 'bottom_left', 'bottom_right',
                           'header_left', 'header_right', 'footer_left', 'footer_right']:
                    st.session_state.font_size_settings[key] = size_percentage
            else:
                st.info("Настройте размер для каждого текстового поля отдельно")
                
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
                            st.session_state.font_size_settings.get(pos, 100),
                            key=f"font_size_{pos}"
                        )
                        st.session_state.font_size_settings[pos] = size
                
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
                            st.session_state.font_size_settings.get(pos, 100),
                            key=f"font_size_{pos}"
                        )
                        st.session_state.font_size_settings[pos] = size
                
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
                            st.session_state.font_size_settings.get(pos, 100),
                            key=f"font_size_{pos}"
                        )
                        st.session_state.font_size_settings[pos] = size
        else:
            # Новый интерфейс для шаблонов с блоками
            st.info(f"Настройте размер для каждого блока")
            
            for i, block in enumerate(blocks):
                block_name = block.get('name', f'Блок {i+1}')
                column_mapping_key = block.get('column_mapping', f'block_{i+1}')
                
                with st.expander(f"🔠 {block_name}", expanded=i < 3):
                    size = st.slider(
                        "Размер текста (%)",
                        50, 200,
                        st.session_state.font_size_settings.get(column_mapping_key, 100),
                        key=f"font_size_{column_mapping_key}"
                    )
                    st.session_state.font_size_settings[column_mapping_key] = size
        
        if st.button("🔄 Сбросить размеры", key="reset_font_sizes"):
            for key in st.session_state.font_size_settings.keys():
                st.session_state.font_size_settings[key] = 100
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
            
            col1, col2 = st.columns(2)
            with col1:
                position = st.selectbox(
                    "Позиция",
                    ["center", "top_left", "top_right", "bottom_left", "bottom_right"],
                    index=["center", "top_left", "top_right", "bottom_left", "bottom_right"].index(
                        st.session_state.image_overlay_settings.get('position', 'center')
                    ) if st.session_state.image_overlay_settings.get('position') in ["center", "top_left", "top_right", "bottom_left", "bottom_right"] else 0,
                    key="overlay_position"
                )
                st.session_state.image_overlay_settings['position'] = position
                
                opacity = st.slider(
                    "Прозрачность (%)",
                    0, 100, st.session_state.image_overlay_settings.get('opacity', 100),
                    key="overlay_opacity"
                )
                st.session_state.image_overlay_settings['opacity'] = opacity
            
            with col2:
                scale = st.slider(
                    "Масштаб (%)",
                    10, 200, st.session_state.image_overlay_settings.get('scale', 100),
                    key="overlay_scale"
                )
                st.session_state.image_overlay_settings['scale'] = scale
                
                max_width = st.slider(
                    "Макс. ширина (% от изображения)",
                    5, 100, st.session_state.image_overlay_settings.get('max_width', 30),
                    key="overlay_max_width"
                )
                st.session_state.image_overlay_settings['max_width'] = max_width
            
            col1, col2 = st.columns(2)
            with col1:
                x_offset = st.number_input(
                    "Смещение X (%)",
                    -100, 100, st.session_state.image_overlay_settings.get('x_offset', 0),
                    key="overlay_x"
                )
                st.session_state.image_overlay_settings['x_offset'] = x_offset
            
            with col2:
                y_offset = st.number_input(
                    "Смещение Y (%)",
                    -100, 100, st.session_state.image_overlay_settings.get('y_offset', 0),
                    key="overlay_y"
                )
                st.session_state.image_overlay_settings['y_offset'] = y_offset
    
    @staticmethod
    def render_template_preview():
        """Предпросмотр границ шаблона"""
        st.subheader("📐 Предпросмотр границ шаблона")
        
        test_width = 600
        test_height = 400
        
        current_template = safe_get_session_state('current_template', 'modern_shop')
        canvas = ImageProcessor.create_template_canvas(test_width, test_height, current_template)
        
        border_img = canvas.copy()
        draw = ImageDraw.Draw(border_img)
        
        content_area = ImageProcessor.get_template_content_area(canvas)
        x1, y1, x2, y2 = content_area
        
        draw.rectangle([x1, y1, x2, y2], outline=(255, 0, 0, 200), width=3)
        
        font = FontManager.load_system_font('system_arial', 14)
        draw.text((10, 10), f"Шаблон: {current_template}", font=font, fill=(255, 255, 255, 255))
        draw.text((10, 30), f"Границы: ({x1},{y1})-({x2},{y2})", font=font, fill=(255, 255, 255, 255))
        draw.text((10, 50), f"Размер: {test_width}x{test_height}", font=font, fill=(255, 255, 255, 255))
        
        col1, col2 = st.columns(2)
        with col1:
            st.image(canvas, caption="Шаблон без границ", width='stretch')
        with col2:
            st.image(border_img, caption="Шаблон с границами содержимого", width='stretch')
    
    @staticmethod
    def render_preview_tab(generator):
        """Вкладка предпросмотра"""
        if st.session_state.df is None:
            st.info("📥 Загрузите Excel файл в боковой панели для начала работы")
            return
        
        st.header("🎯 Предпросмотр")
        
        if st.session_state.get('local_save_path'):
            st.info(f"📁 **Файлы будут сохранены в:** `{st.session_state.local_save_path}`")
        
        UIComponents.render_template_preview()
        
        UIComponents.render_font_settings()
        UIComponents.render_text_offsets()
        UIComponents.render_font_sizes()
        UIComponents.render_overlay_settings()
        UIComponents.render_column_mapping()
        
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
            test_button = st.button("🚀 Запустить тест", type="primary", width='stretch')
        
        if test_button:
            with st.spinner("Выполнение теста..."):
                row = st.session_state.df.iloc[test_row]
                
                template = DynamicTemplateManager.load_template(st.session_state.current_template)
                blocks = template.get('blocks', [])
                
                text_data = {}
                for block in blocks:
                    column_key = block.get('column_mapping')
                    if column_key and column_key in st.session_state.column_mapping:
                        col = st.session_state.column_mapping[column_key]
                        if col in row:
                            text_data[column_key] = str(row[col] or '')
                
                image_url = ''
                if st.session_state.column_mapping.get('image_url'):
                    col = st.session_state.column_mapping['image_url']
                    if col in row:
                        image_url = str(row[col] or '')
                
                overlay_url = None
                if (st.session_state.column_mapping.get('overlay_image_url') and
                    st.session_state.image_overlay_settings.get('enabled', False)):
                    col = st.session_state.column_mapping['overlay_image_url']
                    if col in row:
                        overlay_url = str(row[col] or '')
                        if overlay_url.lower() in ['', 'nan', 'none']:
                            overlay_url = None
                
                with st.expander("📋 Данные строки"):
                    st.json(text_data)
                    st.write(f"**URL изображения:** {image_url[:100]}..." if len(image_url) > 100 else f"**URL изображения:** {image_url}")
                    if overlay_url:
                        st.write(f"**URL наложения:** {overlay_url[:100]}..." if len(overlay_url) > 100 else f"**URL наложения:** {overlay_url}")
                    
                    if st.session_state.use_column_a_for_filenames:
                        first_column = st.session_state.df.columns[0]
                        filename_from_column_a = get_safe_filename(row.get(first_column, ''))
                        st.write(f"**Имя файла (из столбца A):** `{filename_from_column_a}`")
                
                if image_url:
                    img = generator.image_processor.load_image_from_url(image_url)
                    
                    if img:
                        if st.session_state.export_settings.get('resize', True):
                            target_size = st.session_state.export_settings.get('target_size', 1200)
                            img = ImageProcessor.resize_image(img, target_size)
                        
                        canvas = generator.image_processor.create_template_canvas(
                            img.width, img.height,
                            st.session_state.current_template
                        )
                        
                        background_settings = st.session_state.background_settings
                        header_height = int(img.height * background_settings.get('header_height', 15) / 100)
                        
                        footer_height = int(img.height * background_settings.get('footer_height', 10) / 100)
                        main_height = img.height - header_height - footer_height
                        
                        if main_height <= 0:
                            main_height = img.height - header_height
                            if main_height <= 0:
                                main_height = img.height
                        
                        if img.height > main_height:
                            scale_ratio = main_height / img.height
                            new_width = int(img.width * scale_ratio)
                            new_height = main_height
                            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        else:
                            img_resized = img
                        
                        x_offset = (canvas.width - img_resized.width) // 2
                        y_offset = header_height
                        
                        final_img = canvas.copy()
                        final_img.paste(img_resized, (x_offset, y_offset))
                        
                        final_img = generator.image_processor.add_text_to_image(
                            final_img, text_data, st.session_state.current_template
                        )
                        
                        if overlay_url and st.session_state.image_overlay_settings.get('enabled', False):
                            overlay_img = generator.image_processor.load_image_from_url(overlay_url)
                            if overlay_img:
                                final_img = generator.image_processor.add_image_overlay(
                                    final_img,
                                    overlay_img,
                                    st.session_state.image_overlay_settings
                                )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("📷 Оригинал")
                            st.image(img, width='stretch')
                            st.caption(f"{img.width}×{img.height}")
                        
                        with col2:
                            st.subheader("🎨 Результат")
                            st.image(final_img, width='stretch')
                            st.caption(f"Шаблон: {st.session_state.current_template}")
                        
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
                        
                        test_filename = f"test_{test_row}"
                        if st.session_state.use_column_a_for_filenames:
                            first_column = st.session_state.df.columns[0]
                            filename_from_column_a = get_safe_filename(row.get(first_column, ''))
                            if filename_from_column_a and filename_from_column_a != "unnamed":
                                test_filename = filename_from_column_a
                        
                        st.download_button(
                            label="💾 Скачать тестовое изображение",
                            data=buffered.getvalue(),
                            file_name=f"{test_filename}.{format_.lower()}",
                            mime=mime,
                            width='stretch'
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
        
        if st.session_state.get('local_save_path'):
            st.success(f"📁 **Файлы будут сохранены в:** `{st.session_state.local_save_path}`")
            
            try:
                if not os.access(st.session_state.local_save_path, os.W_OK):
                    st.error(f"❌ **Нет прав на запись в папку!** Выберите другую папку в настройках.")
            except:
                st.warning("⚠️ Не удалось проверить права доступа к папке")
        else:
            st.error("❌ **Не выбрана папка для сохранения!** Укажите путь в настройках.")
            return
        
        df_optimized = AdvancedExcelProcessor.clean_dataframe(st.session_state.df)
        total_rows = len(df_optimized)
        
        if total_rows == 0:
            st.error("❌ Нет данных для обработки")
            return
        
        st.info(f"📊 Готово к обработке: {total_rows} строк")
        
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
                width='stretch'
            )
        
        batch_size = end_idx - start_idx + 1
        if batch_size > 0:
            st.success(f"✅ Будет обработано: {batch_size} строк")
        
        if st.session_state.use_column_a_for_filenames:
            first_column = df_optimized.columns[0]
            sample_names = []
            
            for i in range(min(3, len(df_optimized))):
                name = df_optimized.iloc[i].get(first_column)
                if name is not None and pd.notna(name):
                    safe_name = get_safe_filename(name)
                    sample_names.append(safe_name)
            
            if sample_names:
                st.info(f"📝 **Примеры имен файлов:** {', '.join(sample_names)}...")
        
        if process_button and batch_size > 0:
            st.session_state.processing_stats = {
                'total': batch_size,
                'success': 0,
                'failed': 0,
                'start_time': datetime.now(),
                'end_time': None
            }
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            results_placeholder = st.empty()
            
            with st.spinner("Запуск обработки..."):
                results = generator.process_batch(df_optimized, start_idx, end_idx)
            
            success_count = sum(1 for r in results if r.get('status') == 'success')
            failed_count = len(results) - success_count
            
            st.session_state.processing_stats.update({
                'success': success_count,
                'failed': failed_count,
                'end_time': datetime.now()
            })
            
            st.session_state.processed_count += success_count
            st.session_state.batch_results = results
            
            with results_placeholder.container():
                st.success(f"✅ Обработка завершена!")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Успешно", success_count,
                             delta=f"{success_count/batch_size*100:.1f}%" if batch_size > 0 else "0%")
                
                with col2:
                    st.metric("Ошибки", failed_count,
                             delta=f"-{failed_count}" if failed_count > 0 else None)
                
                with col3:
                    if st.session_state.processing_stats.get('start_time') and st.session_state.processing_stats.get('end_time'):
                        duration = (st.session_state.processing_stats['end_time'] -
                                  st.session_state.processing_stats['start_time']).total_seconds()
                        st.metric("Время", f"{duration:.1f} сек",
                                 delta=f"{batch_size/duration:.1f}/сек" if duration > 0 else None)
                
                if failed_count > 0:
                    with st.expander("📋 Ошибки", expanded=False):
                        errors = [r for r in results if r.get('status') == 'error']
                        error_df = pd.DataFrame(errors)
                        if not error_df.empty:
                            st.dataframe(error_df[['row_index', 'message']], width='stretch')
                
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
                                    width='stretch'
                                )
                            
                            zip_size = os.path.getsize(zip_path) / (1024 * 1024)
                            st.info(f"📦 Размер архива: {zip_size:.2f} MB")
                        else:
                            st.error("❌ Ошибка создания архива")
                
                if success_count > 0:
                    st.info(f"✅ Файлы сохранены в папке: `{st.session_state.local_save_path}`")
    
    @staticmethod
    def render_statistics_tab():
        """Вкладка статистики"""
        st.header("📊 Статистика")
        
        processed_count = safe_get_session_state('processed_count', 0)
        if processed_count == 0:
            st.info("📈 Статистика появится после обработки")
            return
        
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
            st.metric("Формат", st.session_state.export_settings.get('format', 'PNG'))
        
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
                    st.dataframe(status_counts, width='stretch')
            
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
        
        template_names = DynamicTemplateManager.get_templates_by_category(selected_category)
        
        if not template_names:
            st.info("📝 Шаблоны не найдены")
            return
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
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
                            
                            preview_width = 300
                            preview_height = 225
                            
                            try:
                                preview = ImageProcessor.create_template_canvas(
                                    preview_width, preview_height, template_id
                                )
                                
                                draw = ImageDraw.Draw(preview)
                                font = FontManager.load_system_font('system_arial', 16)
                                text = template_data.get('name', template_id)
                                
                                try:
                                    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
                                except:
                                    left, top, right, bottom = draw.textsize(text, font=font)
                                
                                text_width = right - left
                                text_height = bottom - top
                                
                                x = (preview_width - text_width) / 2
                                y = (preview_height - text_height) / 2
                                
                                padding = 5
                                draw.rectangle([
                                    x - padding,
                                    y - padding,
                                    x + text_width + padding,
                                    y + text_height + padding
                                ], fill=(255, 255, 255, 200))
                                
                                draw.text((x, y), text, font=font, fill=(0, 0, 0, 255))
                                
                                st.image(preview, width='stretch')
                                st.caption(template_data.get('description', 'Без описания'))
                                
                                if st.button(f"Выбрать {template_name}",
                                           key=f"select_{template_id}"):
                                    st.session_state.current_template = template_id
                                    st.success(f"✅ Выбран шаблон: {template_name}")
                                    st.rerun()
                                    
                            except Exception as e:
                                st.error(f"Ошибка создания превью: {e}")
        
        with col2:
            st.subheader("🔧 Действия")
            
            if st.button("➕ Создать шаблон", use_container_width=True):
                st.session_state.template_editor_active = True
                st.rerun()
            
            st.divider()
            
            st.subheader("📂 Пользовательские")
            
            custom_templates = DynamicTemplateManager.load_custom_templates()
            if custom_templates:
                for template_id, template_data in custom_templates.items():
                    template_name = template_data.get('name', template_id)
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.caption(template_name[:20])
                    
                    with col2:
                        if st.button("🗑️", key=f"delete_{template_id}"):
                            if DynamicTemplateManager.delete_custom_template(template_id):
                                st.success(f"✅ Шаблон удален: {template_name}")
                                st.rerun()
            else:
                st.caption("Нет пользовательских шаблонов")
    
    @staticmethod
    def render_template_editor_tab():
        """Вкладка редактора шаблонов"""
        TemplateEditor.render_template_editor()

# ============================
# ОСНОВНОЙ КОД ПРИЛОЖЕНИЯ
# ============================
def initialize_application():
    """Инициализация приложения"""
    try:
        ensure_session_state_initialized()
        
        os.makedirs("templates", exist_ok=True)
        os.makedirs("custom_templates", exist_ok=True)
        
        if not st.session_state.get('template_cache_initialized', False):
            with st.spinner("🔄 Инициализация шаблонов..."):
                DynamicTemplateManager.ensure_templates_dir()
                
                st.session_state.loaded_templates = {}
                for template_id in DynamicTemplateManager.BUILTIN_TEMPLATES.keys():
                    st.session_state.loaded_templates[template_id] = DynamicTemplateManager.BUILTIN_TEMPLATES[template_id]
                
                st.session_state.template_cache_initialized = True
        
        if not st.session_state.get('local_save_path'):
            default_path = os.path.join(os.path.expanduser("~"), "Desktop", "Инфографики")
            try:
                os.makedirs(default_path, exist_ok=True)
                if os.access(default_path, os.W_OK):
                    st.session_state.local_save_path = default_path
            except:
                st.session_state.local_save_path = os.getcwd()
        
        st.session_state.app_initialized = True
        return True
        
    except Exception as e:
        logger.error(f"Ошибка инициализации: {e}")
        st.error(f"Ошибка инициализации приложения: {str(e)}")
        return False

def show_main_interface():
    """Показать основной интерфейс"""
    ensure_session_state_initialized()
    
    st.title("🚀 Генератор Инфографики PRO v9.0")
    st.markdown("---")
    
    st.caption("🆕 Версия 9.0: Добавлен редактор пользовательских шаблонов с блоками текста")
    
    if st.session_state.template_editor_active:
        UIComponents.render_template_editor_tab()
        return
    
    tab_names = [
        "📊 Анализ данных",
        "🎯 Предпросмотр",
        "⚡ Обработка",
        "📈 Статистика",
        "🎨 Шаблоны"
    ]
    
    if st.session_state.get('template_editor_active', False):
        tab_names.append("🔧 Редактор шаблонов")
    
    tabs = st.tabs(tab_names)
    
    generator = InfographicGenerator()
    
    UIComponents.render_sidebar()
    
    with tabs[0]:
        UIComponents.render_data_quality_tab()
    
    with tabs[1]:
        UIComponents.render_preview_tab(generator)
    
    with tabs[2]:
        UIComponents.render_processing_tab(generator)
    
    with tabs[3]:
        UIComponents.render_statistics_tab()
    
    with tabs[4]:
        UIComponents.render_templates_tab()

def main():
    """Основная функция приложения"""
    try:
        if not hasattr(st.session_state, 'app_initialized') or not st.session_state.app_initialized:
            st.markdown("""
            <div style="text-align: center; padding: 100px;">
                <h1>🎯 Генератор Инфографики PRO v9.0</h1>
                <p>Инициализация системы...</p>
            </div>
            """, unsafe_allow_html=True)
            
            success = initialize_application()
            
            if success:
                st.rerun()
            else:
                st.error("❌ Не удалось инициализировать приложение")
                return
        else:
            show_main_interface()
            
    except Exception as e:
        st.error(f"❌ Критическая ошибка: {str(e)}")
        logger.error(f"Ошибка в main: {e}")

# ============================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ============================
if __name__ == "__main__":
    main()
