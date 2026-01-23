import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageOps
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
from pathlib import Path
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
        'template_preview_size': 400
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

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
                "text": (255, 255, 255, 255),
                "shadow": (0, 0, 0, 180),
                "highlight": (255, 193, 7, 255),
                "price_main": (40, 167, 69, 255),
                "price_old": (108, 117, 125, 180)
            },
            "effects": {
                "shadow": True,
                "gradient": True,
                "rounded_corners": True
            }
        },
        
        "flash_sale_pro": {
            "name": "⚡ FLASH SALE PRO",
            "description": "Профессиональный шаблон для распродаж",
            "category": "sale",
            "layout": {
                "header_height": 20,
                "footer_height": 15,
                "corner_radius": 15,
                "shadow": True,
                "border": False
            },
            "backgrounds": {
                "header": "gradient_red",
                "footer": "gradient_dark",
                "main": "gradient_warm"
            },
            "text_positions": {
                "sale_badge": {"x": 0.5, "y": 0.5, "align": "center", "max_width": 0.9},
                "product_title": {"x": 0.5, "y": 0.15, "align": "center", "max_width": 0.9},
                "old_price": {"x": 0.3, "y": 0.3, "align": "right", "max_width": 0.4},
                "new_price": {"x": 0.7, "y": 0.3, "align": "left", "max_width": 0.4},
                "discount_badge": {"x": 0.5, "y": 0.25, "align": "center", "max_width": 0.4},
                "timer": {"x": 0.5, "y": 0.45, "align": "center", "max_width": 0.8},
                "stock_info": {"x": 0.5, "y": 0.55, "align": "center", "max_width": 0.8},
                "cta_button": {"x": 0.5, "y": 0.7, "align": "center", "max_width": 0.9},
                "footer_note": {"x": 0.5, "y": 0.5, "align": "center", "max_width": 0.9}
            },
            "font_sizes": {
                "sale_badge": 38,
                "product_title": 36,
                "old_price": 32,
                "new_price": 52,
                "discount_badge": 28,
                "timer": 38,
                "stock_info": 24,
                "cta_button": 32,
                "footer_note": 18
            },
            "colors": {
                "text": (255, 255, 255, 255),
                "shadow": (0, 0, 0, 200),
                "new_price": (40, 167, 69, 255),
                "discount_badge": (220, 53, 69, 255),
                "cta_button": (255, 193, 7, 255)
            },
            "effects": {
                "shadow": True,
                "glow": True,
                "animation": True
            }
        },
        
        "instagram_post": {
            "name": "📱 INSTAGRAM POST",
            "description": "Оптимизированный шаблон для Instagram",
            "category": "social",
            "layout": {
                "header_height": 0,
                "footer_height": 25,
                "corner_radius": 0,
                "shadow": False,
                "border": False
            },
            "backgrounds": {
                "header": "transparent",
                "footer": "solid_dark",
                "main": "white"
            },
            "text_positions": {
                "main_title": {"x": 0.05, "y": 0.05, "align": "left", "max_width": 0.9},
                "price": {"x": 0.95, "y": 0.05, "align": "right", "max_width": 0.4},
                "description": {"x": 0.05, "y": 0.15, "align": "left", "max_width": 0.9},
                "hashtags": {"x": 0.05, "y": 0.85, "align": "left", "max_width": 0.9},
                "cta": {"x": 0.5, "y": 0.5, "align": "center", "max_width": 0.8}
            },
            "font_sizes": {
                "main_title": 32,
                "price": 28,
                "description": 20,
                "hashtags": 18,
                "cta": 24
            },
            "colors": {
                "text": (33, 37, 41, 255),
                "shadow": (0, 0, 0, 150),
                "price": (40, 167, 69, 255),
                "hashtags": (173, 181, 189, 255)
            },
            "effects": {
                "shadow": False,
                "modern": True
            }
        },
        
        "luxury_gold": {
            "name": "💎 LUXURY GOLD",
            "description": "Роскошный шаблон для премиум товаров",
            "category": "premium",
            "layout": {
                "header_height": 12,
                "footer_height": 8,
                "corner_radius": 30,
                "shadow": True,
                "border": True
            },
            "backgrounds": {
                "header": "gradient_gold",
                "footer": "solid_dark",
                "main": "gradient_light"
            },
            "text_positions": {
                "brand_name": {"x": 0.5, "y": 0.5, "align": "center", "max_width": 0.7},
                "product_title": {"x": 0.5, "y": 0.15, "align": "center", "max_width": 0.8},
                "price": {"x": 0.5, "y": 0.3, "align": "center", "max_width": 0.8},
                "features": {"x": 0.5, "y": 0.45, "align": "center", "max_width": 0.8},
                "exclusive_badge": {"x": 0.5, "y": 0.7, "align": "center", "max_width": 0.6},
                "footer_text": {"x": 0.5, "y": 0.5, "align": "center", "max_width": 0.8}
            },
            "font_sizes": {
                "brand_name": 24,
                "product_title": 38,
                "price": 44,
                "features": 22,
                "exclusive_badge": 26,
                "footer_text": 18
            },
            "colors": {
                "text": (33, 37, 41, 255),
                "shadow": (0, 0, 0, 180),
                "price": (218, 165, 32, 255),
                "exclusive_badge": (192, 156, 26, 255)
            },
            "effects": {
                "shadow": True,
                "gold_border": True,
                "vignette": True
            }
        },
        
        "minimal_white": {
            "name": "🌀 MINIMAL WHITE",
            "description": "Чистый минималистичный дизайн",
            "category": "minimal",
            "layout": {
                "header_height": 0,
                "footer_height": 0,
                "corner_radius": 0,
                "shadow": False,
                "border": False
            },
            "backgrounds": {
                "header": "transparent",
                "footer": "transparent",
                "main": "white"
            },
            "text_positions": {
                "product_title": {"x": 0.5, "y": 0.1, "align": "center", "max_width": 0.8},
                "price": {"x": 0.5, "y": 0.25, "align": "center", "max_width": 0.8},
                "description": {"x": 0.5, "y": 0.4, "align": "center", "max_width": 0.7}
            },
            "font_sizes": {
                "product_title": 36,
                "price": 32,
                "description": 20
            },
            "colors": {
                "text": (33, 37, 41, 255),
                "shadow": (0, 0, 0, 0),
                "price": (108, 117, 125, 255)
            },
            "effects": {
                "shadow": False,
                "border": False
            }
        },
        
        "creative_abstract": {
            "name": "🎨 CREATIVE ABSTRACT",
            "description": "Креативный шаблон с абстрактным дизайном",
            "category": "creative",
            "layout": {
                "header_height": 18,
                "footer_height": 12,
                "corner_radius": 25,
                "shadow": True,
                "border": True
            },
            "backgrounds": {
                "header": "gradient_purple",
                "footer": "gradient_dark",
                "main": "light_gray"
            },
            "text_positions": {
                "creative_title": {"x": 0.5, "y": 0.5, "align": "center", "max_width": 0.8},
                "product_name": {"x": 0.5, "y": 0.15, "align": "center", "max_width": 0.8},
                "creative_price": {"x": 0.5, "y": 0.3, "align": "center", "max_width": 0.8},
                "tagline": {"x": 0.5, "y": 0.45, "align": "center", "max_width": 0.7},
                "features": {"x": 0.5, "y": 0.6, "align": "center", "max_width": 0.8},
                "footer_cta": {"x": 0.5, "y": 0.5, "align": "center", "max_width": 0.8}
            },
            "font_sizes": {
                "creative_title": 32,
                "product_name": 40,
                "creative_price": 48,
                "tagline": 24,
                "features": 20,
                "footer_cta": 22
            },
            "colors": {
                "text": (255, 255, 255, 255),
                "shadow": (0, 0, 0, 200),
                "creative_price": (147, 112, 219, 255),
                "tagline": (108, 117, 125, 255)
            },
            "effects": {
                "shadow": True,
                "abstract": True,
                "gradient_text": True
            }
        },
        
        "marketplace_card": {
            "name": "🏪 MARKETPLACE CARD",
            "description": "Карточка товара для маркетплейсов",
            "category": "ecommerce",
            "layout": {
                "header_height": 10,
                "footer_height": 20,
                "corner_radius": 10,
                "shadow": True,
                "border": True
            },
            "backgrounds": {
                "header": "solid_light",
                "footer": "solid_gray",
                "main": "white"
            },
            "text_positions": {
                "category": {"x": 0.05, "y": 0.5, "align": "left", "max_width": 0.4},
                "product_title": {"x": 0.05, "y": 0.1, "align": "left", "max_width": 0.9},
                "rating": {"x": 0.05, "y": 0.25, "align": "left", "max_width": 0.4},
                "price": {"x": 0.05, "y": 0.35, "align": "left", "max_width": 0.4},
                "delivery": {"x": 0.05, "y": 0.5, "align": "left", "max_width": 0.4},
                "button": {"x": 0.95, "y": 0.5, "align": "right", "max_width": 0.4}
            },
            "font_sizes": {
                "category": 14,
                "product_title": 24,
                "rating": 18,
                "price": 28,
                "delivery": 16,
                "button": 20
            },
            "colors": {
                "text": (33, 37, 41, 255),
                "shadow": (0, 0, 0, 180),
                "price": (40, 167, 69, 255),
                "button": (0, 123, 255, 255)
            },
            "effects": {
                "shadow": True,
                "button_effect": True
            }
        },
        
        "youtube_thumbnail": {
            "name": "📺 YOUTUBE THUMBNAIL",
            "description": "Шаблон для миниатюр YouTube",
            "category": "social",
            "layout": {
                "header_height": 35,
                "footer_height": 20,
                "corner_radius": 10,
                "shadow": True,
                "border": False
            },
            "backgrounds": {
                "header": "gradient_red",
                "footer": "solid_dark",
                "main": "white"
            },
            "text_positions": {
                "video_title": {"x": 0.5, "y": 0.5, "align": "center", "max_width": 0.9},
                "product_highlight": {"x": 0.5, "y": 0.2, "align": "center", "max_width": 0.9},
                "price_reveal": {"x": 0.5, "y": 0.5, "align": "center", "max_width": 0.8},
                "shocking_fact": {"x": 0.5, "y": 0.8, "align": "center", "max_width": 0.9},
                "cta_youtube": {"x": 0.5, "y": 0.5, "align": "center", "max_width": 0.8}
            },
            "font_sizes": {
                "video_title": 44,
                "product_highlight": 36,
                "price_reveal": 52,
                "shocking_fact": 28,
                "cta_youtube": 26
            },
            "colors": {
                "text": (255, 255, 255, 255),
                "shadow": (0, 0, 0, 200),
                "price_reveal": (220, 53, 69, 255),
                "shocking_fact": (255, 193, 7, 255)
            },
            "effects": {
                "shadow": True,
                "youtube_style": True,
                "attention_grabber": True
            }
        }
    }
    
    @staticmethod
    def ensure_templates_dir():
        """Создание директории для шаблонов если её нет"""
        try:
            os.makedirs(DynamicTemplateManager.TEMPLATES_DIR, exist_ok=True)
            
            for template_id, template_data in DynamicTemplateManager.BUILTIN_TEMPLATES.items():
                filepath = os.path.join(DynamicTemplateManager.TEMPLATES_DIR, f"{template_id}.json")
                if not os.path.exists(filepath):
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(template_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Директория шаблонов создана: {DynamicTemplateManager.TEMPLATES_DIR}")
        except Exception as e:
            logger.error(f"Ошибка создания директории шаблонов: {e}")
    
    @staticmethod
    def scan_template_files():
        """Сканирование директории с шаблонами"""
        DynamicTemplateManager.ensure_templates_dir()
        
        template_files = []
        try:
            if os.path.exists(DynamicTemplateManager.TEMPLATES_DIR):
                for file in os.listdir(DynamicTemplateManager.TEMPLATES_DIR):
                    if file.endswith('.json'):
                        template_id = os.path.splitext(file)[0]
                        filepath = os.path.join(DynamicTemplateManager.TEMPLATES_DIR, file)
                        
                        if os.path.isfile(filepath):
                            template_files.append({
                                'id': template_id,
                                'path': filepath,
                                'name': file
                            })
        except Exception as e:
            logger.error(f"Ошибка сканирования шаблонов: {e}")
        
        st.session_state.template_files = template_files
        return template_files
    
    @staticmethod
    def load_template(template_id: str) -> Dict:
        """Загрузка шаблона по ID"""
        if (st.session_state.get('loaded_templates') and 
            template_id in st.session_state.loaded_templates):
            return st.session_state.loaded_templates[template_id]
        
        filepath = os.path.join(DynamicTemplateManager.TEMPLATES_DIR, f"{template_id}.json")
        
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                
                if 'colors' in template_data:
                    for color_key, color_value in template_data['colors'].items():
                        if isinstance(color_value, list):
                            template_data['colors'][color_key] = tuple(color_value)
                
                if 'id' not in template_data:
                    template_data['id'] = template_id
                
                if 'loaded_templates' not in st.session_state:
                    st.session_state.loaded_templates = {}
                st.session_state.loaded_templates[template_id] = template_data
                
                return template_data
            except Exception as e:
                logger.error(f"Ошибка загрузки шаблона {template_id}: {e}")
        
        return DynamicTemplateManager.BUILTIN_TEMPLATES.get("modern_shop", {}).copy()
    
    @staticmethod
    def get_template_names() -> List[Tuple[str, str]]:
        """Получение списка всех доступных шаблонов"""
        template_files = DynamicTemplateManager.scan_template_files()
        template_names = []
        
        for template_id, template_data in DynamicTemplateManager.BUILTIN_TEMPLATES.items():
            display_name = template_data.get('name', template_id)
            template_names.append((template_id, display_name))
        
        for template_info in template_files:
            template_id = template_info['id']
            if template_id not in DynamicTemplateManager.BUILTIN_TEMPLATES:
                template_data = DynamicTemplateManager.load_template(template_id)
                display_name = template_data.get('name', template_id)
                template_names.append((template_id, display_name))
        
        if not template_names:
            template_names = [("modern_shop", "🛒 MODERN SHOP")]
        
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
    def save_template(template_id: str, template_data: Dict) -> bool:
        """Сохранение шаблона в файл"""
        try:
            filepath = os.path.join(DynamicTemplateManager.TEMPLATES_DIR, f"{template_id}.json")
            
            save_data = template_data.copy()
            
            if 'colors' in save_data:
                for color_key, color_value in save_data['colors'].items():
                    if isinstance(color_value, tuple):
                        save_data['colors'][color_key] = list(color_value)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2, default=str)
            
            if 'loaded_templates' not in st.session_state:
                st.session_state.loaded_templates = {}
            st.session_state.loaded_templates[template_id] = template_data
            
            logger.info(f"Шаблон {template_id} сохранен")
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения шаблона {template_id}: {e}")
            st.error(f"Ошибка сохранения шаблона: {e}")
            return False
    
    @staticmethod
    def validate_template(template_data: Dict) -> Tuple[bool, List[str], List[str]]:
        """Валидация структуры шаблона"""
        errors = []
        warnings = []
        
        required_fields = ['name']
        for field in required_fields:
            if field not in template_data:
                errors.append(f"Отсутствует обязательное поле: {field}")
        
        if 'text_positions' in template_data:
            text_positions = template_data['text_positions']
            if not isinstance(text_positions, dict):
                errors.append("text_positions должен быть словарем")
            else:
                for pos_key, pos_data in text_positions.items():
                    if not isinstance(pos_data, dict):
                        errors.append(f"Позиция '{pos_key}' должна быть словарем")
                    else:
                        required_pos_fields = ['x', 'y']
                        for field in required_pos_fields:
                            if field not in pos_data:
                                errors.append(f"Позиция '{pos_key}' не имеет поля '{field}'")
                            else:
                                value = pos_data[field]
                                try:
                                    float_value = float(value)
                                    if float_value < 0 or float_value > 1:
                                        warnings.append(f"Позиция '{pos_key}': {field} обычно должен быть между 0 и 1")
                                except (ValueError, TypeError):
                                    errors.append(f"Позиция '{pos_key}': {field} должен быть числом")
        
        return len(errors) == 0, errors, warnings

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
                
                if 'font_cache' not in st.session_state:
                    st.session_state.font_cache = {}
                if 'uploaded_fonts' not in st.session_state:
                    st.session_state.uploaded_fonts = []
                
                font_info = {
                    'name': font_name,
                    'path': tmp_path,
                    'key': font_key,
                    'size': 24,
                    'file_size': len(uploaded_file.getvalue())
                }
                
                st.session_state.font_cache[font_key] = font_info
                
                existing_fonts = [f['key'] for f in st.session_state.uploaded_fonts]
                if font_key not in existing_fonts:
                    st.session_state.uploaded_fonts.append(font_info)
                
                logger.info(f"Шрифт '{font_name}' загружен (ключ: {font_key})")
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
            font_paths = {
                "system_arial": [
                    "C:/Windows/Fonts/arial.ttf",
                    "C:/Windows/Fonts/Arial.ttf",
                    "/System/Library/Fonts/Supplemental/Arial.ttf",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
                ],
                "system_helvetica": [
                    "/System/Library/Fonts/Helvetica.ttc",
                    "/System/Library/Fonts/Helvetica Neue.ttc",
                    "C:/Windows/Fonts/arial.ttf"
                ],
                "system_times": [
                    "C:/Windows/Fonts/times.ttf",
                    "C:/Windows/Fonts/Times New Roman.ttf",
                    "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
                ]
            }
            
            if font_name in font_paths:
                for path in font_paths[font_name]:
                    if os.path.exists(path):
                        return ImageFont.truetype(path, int(size))
            
            try:
                return ImageFont.truetype("arial", int(size))
            except:
                return ImageFont.load_default()
                
        except Exception as e:
            logger.error(f"Ошибка загрузки системного шрифта {font_name}: {e}")
            try:
                return ImageFont.load_default()
            except:
                return ImageFont.load_default()

class ImageProcessor:
    """Класс для обработки изображений с поддержкой фонов"""
    
    @staticmethod
    def load_image_from_url(url: str, timeout: int = 30, retries: int = 3, use_cache: bool = True) -> Optional[Image.Image]:
        """Загрузка изображения по URL с повторными попытками"""
        if not url or not isinstance(url, str) or not url.strip():
            return None
        
        url = url.strip()
        
        if use_cache and st.session_state.get('image_cache'):
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
                    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Referer': 'https://www.google.com/'
                }
                
                response = requests.get(url, timeout=timeout, headers=headers, stream=True)
                response.raise_for_status()
                
                content_type = response.headers.get('content-type', '').lower()
                if 'image' not in content_type:
                    logger.warning(f"URL не возвращает изображение: {content_type}")
                    if attempt == retries:
                        return None
                    time.sleep(1)
                    continue
                
                img_data = BytesIO()
                for chunk in response.iter_content(chunk_size=8192):
                    img_data.write(chunk)
                
                img_data.seek(0)
                img = Image.open(img_data)
                
                if img.mode != 'RGBA':
                    if img.mode == 'P' and 'transparency' in img.info:
                        img = img.convert('RGBA')
                    elif img.mode == 'LA':
                        img = img.convert('RGBA')
                    else:
                        img = img.convert('RGBA')
                
                if use_cache:
                    if 'image_cache' not in st.session_state:
                        st.session_state.image_cache = {}
                    cache_key = hashlib.md5(url.encode()).hexdigest()
                    st.session_state.image_cache[cache_key] = img.copy()
                
                logger.info(f"Изображение загружено: {url} ({img.width}x{img.height})")
                return img
                
            except requests.exceptions.Timeout:
                logger.warning(f"Таймаут при загрузке {url}, попытка {attempt + 1}/{retries + 1}")
                if attempt == retries:
                    return None
                time.sleep(2)
            except requests.exceptions.ConnectionError:
                logger.warning(f"Ошибка соединения {url}, попытка {attempt + 1}/{retries + 1}")
                if attempt == retries:
                    return None
                time.sleep(2)
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
        
        header_height_percent = layout.get("header_height", 15)
        footer_height_percent = layout.get("footer_height", 10)
        
        header_height = int(height * header_height_percent / 100)
        footer_height = int(height * footer_height_percent / 100)
        main_height = height - header_height - footer_height
        
        canvas = Image.new('RGBA', (width, height), (255, 255, 255, 0))
        bg_library = BackgroundLibrary()
        
        header_bg_key = st.session_state.background_settings.get('header_background', 
                                                               backgrounds.get('header', 'gradient_blue'))
        footer_bg_key = st.session_state.background_settings.get('footer_background', 
                                                               backgrounds.get('footer', 'gradient_dark'))
        main_bg_key = st.session_state.background_settings.get('main_background', 
                                                             backgrounds.get('main', 'white'))
        
        header_bg_config = {}
        if header_bg_key in BackgroundLibrary.get_header_backgrounds():
            header_bg_config = BackgroundLibrary.get_header_backgrounds()[header_bg_key]
        else:
            header_bg_config = {"type": "solid", "color": (255, 255, 255)}
        
        footer_bg_config = {}
        if footer_bg_key in BackgroundLibrary.get_footer_backgrounds():
            footer_bg_config = BackgroundLibrary.get_footer_backgrounds()[footer_bg_key]
        else:
            footer_bg_config = {"type": "solid", "color": (33, 37, 41)}
        
        main_bg_config = {}
        if main_bg_key in BackgroundLibrary.get_main_backgrounds():
            main_bg_config = BackgroundLibrary.get_main_backgrounds()[main_bg_key]
        else:
            main_bg_config = {"type": "solid", "color": (255, 255, 255)}
        
        if header_height > 0:
            header_bg = bg_library.create_background(width, header_height, header_bg_config)
            canvas.paste(header_bg, (0, 0))
        
        if main_height > 0:
            main_bg = bg_library.create_background(width, main_height, main_bg_config)
            canvas.paste(main_bg, (0, header_height))
        
        if footer_height > 0:
            footer_bg = bg_library.create_background(width, footer_height, footer_bg_config)
            canvas.paste(footer_bg, (0, header_height + main_height))
        
        corner_radius = st.session_state.background_settings.get('corner_radius', 
                                                               layout.get('corner_radius', 0))
        if corner_radius > 0 and layout.get('rounded_corners', True):
            canvas = ImageProcessor.add_rounded_corners(canvas, corner_radius)
        
        if layout.get('shadow', False) and st.session_state.background_settings.get('shadow_enabled', True):
            canvas = ImageProcessor.add_shadow_effect(canvas)
        
        if layout.get('border', False) and st.session_state.background_settings.get('border_enabled', True):
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
        
        draw.pieslice([0, 0, radius * 2, radius * 2], 180, 270, fill=255)
        draw.pieslice([width - radius * 2, 0, width, radius * 2], 270, 360, fill=255)
        draw.pieslice([0, height - radius * 2, radius * 2, height], 90, 180, fill=255)
        draw.pieslice([width - radius * 2, height - radius * 2, width, height], 0, 90, fill=255)
        
        draw.rectangle([radius, 0, width - radius, height], fill=255)
        draw.rectangle([0, radius, width, height - radius], fill=255)
        
        result = Image.new('RGBA', img.size, (255, 255, 255, 0))
        result.paste(img, (0, 0), mask)
        
        return result
    
    @staticmethod
    def add_shadow_effect(img: Image.Image, shadow_size: int = 10, shadow_color: Tuple = (0, 0, 0, 100)) -> Image.Image:
        """Добавление эффекта тени"""
        width, height = img.size
        
        shadow = Image.new('RGBA', (width + shadow_size * 2, height + shadow_size * 2), (0, 0, 0, 0))
        shadow.paste(img, (shadow_size, shadow_size), img)
        
        for i in range(shadow_size):
            alpha = int(shadow_color[3] * (i + 1) / shadow_size)
            shadow_with_alpha = Image.new('RGBA', shadow.size, (0, 0, 0, 0))
            shadow_with_alpha.paste((shadow_color[0], shadow_color[1], shadow_color[2], alpha), 
                                   [i, i, width + shadow_size * 2 - i, height + shadow_size * 2 - i])
            shadow = Image.alpha_composite(shadow, shadow_with_alpha)
        
        return shadow
    
    @staticmethod
    def add_border(img: Image.Image, border_color: str, border_width: int = 2) -> Image.Image:
        """Добавление рамки"""
        width, height = img.size
        
        border_img = Image.new('RGBA', (width + border_width * 2, height + border_width * 2), 
                             (255, 255, 255, 0))
        
        if border_color.startswith('#'):
            try:
                border_rgb = tuple(int(border_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                border_rgba = border_rgb + (255,)
            except:
                border_rgba = (224, 224, 224, 255)
        else:
            border_rgba = (224, 224, 224, 255)
        
        draw = ImageDraw.Draw(border_img)
        draw.rectangle([0, 0, width + border_width * 2, height + border_width * 2], 
                      fill=border_rgba)
        
        border_img.paste(img, (border_width, border_width), img)
        
        return border_img
    
    @staticmethod
    def add_text_to_image(img: Image.Image, text_data: Dict, template_id: str = "modern_shop", 
                         text_offsets: Optional[Dict] = None, font_settings: Optional[Dict] = None) -> Image.Image:
        """Добавление текста на изображение по шаблону"""
        if img is None:
            return None
        
        try:
            template = DynamicTemplateManager.load_template(template_id)
            if not template:
                template = DynamicTemplateManager.BUILTIN_TEMPLATES["modern_shop"]
            
            draw = ImageDraw.Draw(img)
            
            if font_settings is None:
                font_settings = st.session_state.get('font_settings', {})
            
            if text_offsets is None:
                text_offsets = st.session_state.get('text_offset_settings', {})
            
            layout = template.get("layout", {})
            header_height_percent = layout.get("header_height", 15)
            footer_height_percent = layout.get("footer_height", 10)
            
            header_height = int(img.height * header_height_percent / 100)
            footer_height = int(img.height * footer_height_percent / 100)
            main_height = img.height - header_height - footer_height
            
            text_positions = template.get("text_positions", {})
            
            for position_key, position_data in text_positions.items():
                if position_key in text_data and text_data[position_key]:
                    text = str(text_data[position_key])
                    if not text.strip():
                        continue
                    
                    base_x = position_data.get("x", 0.5) * img.width
                    base_y = position_data.get("y", 0.5)
                    
                    section = position_data.get("section", "main")
                    if section == "header":
                        base_y = base_y * header_height
                    elif section == "footer":
                        base_y = header_height + main_height + base_y * footer_height
                    else:  # main
                        base_y = header_height + base_y * main_height
                    
                    if position_key in text_offsets:
                        offset_x = text_offsets[position_key].get('x_offset', 0)
                        offset_y = text_offsets[position_key].get('y_offset', 0)
                        
                        if abs(offset_x) <= 100:
                            base_x += offset_x * img.width / 100
                        else:
                            base_x += offset_x
                            
                        if abs(offset_y) <= 100:
                            base_y += offset_y * img.height / 100
                        else:
                            base_y += offset_y
                    
                    x = int(base_x)
                    y = int(base_y)
                    
                    font_sizes = template.get("font_sizes", {})
                    base_font_size = font_sizes.get(position_key, 24)
                    font_size_multiplier = font_settings.get('font_size_multiplier', 1.0)
                    font_size = int(base_font_size * font_size_multiplier)
                    
                    main_font_key = font_settings.get('main_font', 'system_arial')
                    bold_font_key = font_settings.get('bold_font', main_font_key)
                    
                    if position_key in ["product_title", "price_main", "sale_badge", "video_title"]:
                        font_key = bold_font_key
                    else:
                        font_key = main_font_key
                    
                    try:
                        if font_key.startswith('system_'):
                            font = FontManager.load_system_font(font_key, font_size)
                        else:
                            font = FontManager.get_font(font_key, font_size)
                    except:
                        font = FontManager.load_system_font('system_arial', font_size)
                    
                    color_key = position_key if position_key in template.get("colors", {}) else "text"
                    text_color = template.get("colors", {}).get(color_key, (255, 255, 255, 255))
                    
                    if template.get("effects", {}).get("shadow", True):
                        shadow_color = template.get("colors", {}).get("shadow", (0, 0, 0, 180))
                        shadow_offset = 2
                        anchor = "mm" if position_data.get("align") == "center" else None
                        
                        if anchor == "mm":
                            draw.text((x + shadow_offset, y + shadow_offset), text, 
                                     font=font, fill=shadow_color, anchor=anchor)
                        else:
                            draw.text((x + shadow_offset, y + shadow_offset), text, 
                                     font=font, fill=shadow_color,
                                     align=position_data.get("align", "left"))
                    
                    anchor = "mm" if position_data.get("align") == "center" else None
                    
                    if anchor == "mm":
                        draw.text((x, y), text, font=font, fill=text_color, anchor=anchor)
                    else:
                        draw.text((x, y), text, font=font, fill=text_color,
                                 align=position_data.get("align", "left"))
            
            return img
            
        except Exception as e:
            logger.error(f"Ошибка добавления текста к изображению: {e}")
            return img
    
    @staticmethod
    def add_image_overlay(background_img: Image.Image, overlay_img: Image.Image, 
                         overlay_settings: Dict) -> Image.Image:
        """Добавление изображения поверх основного"""
        if background_img is None or overlay_img is None:
            return background_img
        
        try:
            result_img = background_img.copy()
            
            max_width_px = int(background_img.width * overlay_settings.get('max_width', 30) / 100)
            max_height_px = int(background_img.height * overlay_settings.get('max_height', 30) / 100)
            
            scale = overlay_settings.get('scale', 100) / 100
            width_ratio = max_width_px / overlay_img.width
            height_ratio = max_height_px / overlay_img.height
            overlay_ratio = min(width_ratio, height_ratio) * scale
            
            new_width = int(overlay_img.width * overlay_ratio)
            new_height = int(overlay_img.height * overlay_ratio)
            
            if new_width > 0 and new_height > 0:
                overlay_resized = overlay_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                opacity = overlay_settings.get('opacity', 100)
                if opacity < 100 and overlay_resized.mode == 'RGBA':
                    overlay_resized = ImageProcessor.apply_opacity(overlay_resized, opacity)
                
                position = overlay_settings.get('position', 'center')
                
                if position == 'center':
                    x = (background_img.width - new_width) // 2
                    y = (background_img.height - new_height) // 2
                elif position == 'top_left':
                    x = 0
                    y = 0
                elif position == 'top_right':
                    x = background_img.width - new_width
                    y = 0
                elif position == 'bottom_left':
                    x = 0
                    y = background_img.height - new_height
                elif position == 'bottom_right':
                    x = background_img.width - new_width
                    y = background_img.height - new_height
                else:
                    x = (background_img.width - new_width) // 2
                    y = (background_img.height - new_height) // 2
                
                x += int(overlay_settings.get('x_offset', 0) * background_img.width / 100)
                y += int(overlay_settings.get('y_offset', 0) * background_img.height / 100)
                
                x = max(0, min(x, background_img.width - new_width))
                y = max(0, min(y, background_img.height - new_height))
                
                if overlay_resized.mode != 'RGBA':
                    overlay_resized = overlay_resized.convert('RGBA')
                
                result_img.paste(overlay_resized, (x, y), overlay_resized)
            
            return result_img
            
        except Exception as e:
            logger.error(f"Ошибка при наложении изображения: {e}")
            return background_img
    
    @staticmethod
    def apply_opacity(img: Image.Image, opacity: int) -> Image.Image:
        """Применение прозрачности к изображению"""
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        alpha = img.split()[3]
        alpha = alpha.point(lambda p: p * opacity / 100)
        
        img.putalpha(alpha)
        return img
    
    @staticmethod
    def resize_image(img: Image.Image, target_size: int = 1200) -> Image.Image:
        """Изменение размера изображения с сохранением пропорций"""
        if img is None:
            return None
        
        max_dimension = max(img.width, img.height)
        
        if max_dimension > target_size:
            ratio = target_size / max_dimension
            new_width = int(img.width * ratio)
            new_height = int(img.height * ratio)
            
            try:
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            except AttributeError:
                img = img.resize((new_width, new_height), Image.LANCZOS)
        
        return img
    
    @staticmethod
    def save_image(img: Image.Image, filepath: str, format: str = 'PNG', quality: int = 95) -> bool:
        """Сохранение изображения в файл"""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            format_upper = format.upper()
            save_kwargs = {'optimize': True}
            
            if format_upper == 'JPEG' or format_upper == 'JPG':
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                save_kwargs['quality'] = quality
                img.save(filepath, 'JPEG', **save_kwargs)
            elif format_upper == 'WEBP':
                save_kwargs['quality'] = quality
                img.save(filepath, 'WEBP', **save_kwargs)
            else:
                img.save(filepath, 'PNG', **save_kwargs)
            
            logger.info(f"Изображение сохранено: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения {filepath}: {e}")
            return False

# ============================
# УТИЛИТЫ ДЛЯ РАБОТЫ С EXCEL
# ============================
class ExcelProcessor:
    """Класс для обработки Excel файлов"""
    
    @staticmethod
    def read_excel_file(uploaded_file) -> Optional[pd.DataFrame]:
        """Чтение Excel файла с автоматическим определением формата"""
        try:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            if file_extension == 'xlsx':
                df = pd.read_excel(uploaded_file, engine='openpyxl')
            elif file_extension == 'xls':
                try:
                    df = pd.read_excel(uploaded_file, engine='xlrd')
                except:
                    df = pd.read_excel(uploaded_file, engine='openpyxl')
            else:
                st.error(f"❌ Неподдерживаемый формат файла: {file_extension}")
                return None
            
            df = df.replace({np.nan: None, '': None})
            
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).replace('nan', None).replace('None', None)
            
            logger.info(f"Загружен файл: {uploaded_file.name}, строк: {len(df)}, колонок: {len(df.columns)}")
            return df
            
        except Exception as e:
            st.error(f"❌ Ошибка чтения файла: {str(e)}")
            logger.error(f"Ошибка чтения Excel: {e}")
            return None
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame, required_columns: Optional[List] = None) -> Tuple[bool, str]:
        """Валидация структуры DataFrame"""
        if df is None:
            return False, "DataFrame не загружен"
        if df.empty:
            return False, "DataFrame пустой"
        
        if required_columns:
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return False, f"Отсутствуют колонки: {missing_columns}"
        
        return True, "DataFrame валиден"
    
    @staticmethod
    def get_column_suggestions(df: pd.DataFrame) -> Dict:
        """Автоматическое предложение колонок для маппинга"""
        suggestions = {
            'top_left': None,
            'top_right': None,
            'bottom_left': None,
            'bottom_right': None,
            'image_url': None,
            'overlay_image_url': None,
            'filename': None
        }
        
        if df is None or df.empty:
            return suggestions
        
        column_names = [str(col).lower() for col in df.columns]
        
        keyword_mapping = {
            'top_left': ['название', 'name', 'товар', 'product', 'title', 'имя', 'наименование'],
            'top_right': ['цена', 'price', 'стоимость', 'руб', 'р.', 'сумма', 'стоимост'],
            'bottom_left': ['характеристики', 'spec', 'описание', 'description', 'детали', 'features', 'param'],
            'bottom_right': ['скидка', 'discount', 'акция', 'sale', 'распродажа', 'экономия', 'bonus'],
            'image_url': ['url', 'ссылка', 'image', 'картинка', 'фото', 'photo', 'основное', 'img', 'picture'],
            'overlay_image_url': ['лого', 'logo', 'бренд', 'brand', 'дополнительно', 'additional', 'наложение', 'overlay', 'стикер', 'sticker', 'watermark'],
            'filename': ['артикул', 'sku', 'код', 'id', 'номер', 'article']
        }
        
        for position, keywords in keyword_mapping.items():
            for col_name, col_name_lower in zip(df.columns, column_names):
                for keyword in keywords:
                    if keyword in col_name_lower:
                        suggestions[position] = col_name
                        break
                if suggestions[position]:
                    break
        
        if not suggestions['filename'] and len(df.columns) > 0:
            suggestions['filename'] = df.columns[0]
        
        return suggestions
    
    @staticmethod
    def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Оптимизация DataFrame для ускорения обработки"""
        if df is None or df.empty:
            return df
        
        df_optimized = df.copy()
        
        if 'image_url' in st.session_state.column_mapping:
            image_col = st.session_state.column_mapping['image_url']
            if image_col in df_optimized.columns:
                initial_count = len(df_optimized)
                df_optimized = df_optimized[df_optimized[image_col].notna() & 
                                           (df_optimized[image_col] != '') &
                                           (df_optimized[image_col] != 'None')].copy()
                removed_count = initial_count - len(df_optimized)
                if removed_count > 0:
                    logger.info(f"Удалено {removed_count} строк без URL изображений")
        
        return df_optimized

# ============================
# ОСНОВНОЙ ПРОЦЕССОР
# ============================
class InfographicGenerator:
    """Основной класс для генерации инфографики"""
    
    def __init__(self):
        self.image_processor = ImageProcessor()
        self.excel_processor = ExcelProcessor()
    
    def process_single_row(self, row: pd.Series, column_mapping: Dict, template_id: str, 
                          export_settings: Dict, row_index: int = 0, 
                          text_offsets: Optional[Dict] = None, 
                          overlay_settings: Optional[Dict] = None, 
                          font_settings: Optional[Dict] = None) -> Dict:
        """Обработка одной строки данных"""
        try:
            text_data = {}
            for position in ['top_left', 'top_right', 'bottom_left', 'bottom_right']:
                if position in column_mapping and column_mapping[position] in row:
                    text_data[position] = str(row[column_mapping[position]] or '')
                else:
                    text_data[position] = ''
            
            image_url = ''
            if 'image_url' in column_mapping and column_mapping['image_url'] in row:
                image_url = str(row[column_mapping['image_url']] or '')
            
            if not image_url or image_url.lower() in ['none', 'nan', '']:
                return {
                    'row_index': row_index,
                    'status': 'error',
                    'message': 'Отсутствует URL основного изображения',
                    'filename': f"row_{row_index:04d}"
                }
            
            overlay_image_url = None
            if ('overlay_image_url' in column_mapping and 
                column_mapping['overlay_image_url'] in row):
                overlay_image_url = str(row[column_mapping['overlay_image_url']] or '')
                if overlay_image_url.lower() in ['none', 'nan', '']:
                    overlay_image_url = None
            
            filename_source = ''
            if 'filename' in column_mapping and column_mapping['filename'] in row:
                filename_source = str(row[column_mapping['filename']] or '')
            
            filename = self.generate_filename(filename_source, row_index)
            
            export_settings_local = export_settings.copy()
            if 'prefix' in export_settings_local and export_settings_local['prefix']:
                filename = f"{export_settings_local['prefix']}_{filename}"
            if 'suffix' in export_settings_local and export_settings_local['suffix']:
                filename = f"{filename}_{export_settings_local['suffix']}"
            
            main_img = self.image_processor.load_image_from_url(
                image_url,
                timeout=export_settings_local.get('timeout', 30),
                retries=export_settings_local.get('retry_count', 3)
            )
            
            if main_img is None:
                return {
                    'row_index': row_index,
                    'status': 'error',
                    'message': 'Не удалось загрузить основное изображение',
                    'filename': filename
                }
            
            if export_settings_local.get('resize', True):
                target_size = export_settings_local.get('target_size', 1200)
                main_img = self.image_processor.resize_image(main_img, target_size)
            
            template_canvas = self.image_processor.create_template_canvas(
                main_img.width, main_img.height, template_id
            )
            
            final_img = template_canvas.copy()
            
            main_img_position = (0, 
                               int(template_canvas.height * st.session_state.background_settings.get('header_height', 15) / 100))
            final_img.paste(main_img, main_img_position)
            
            processed_img = self.image_processor.add_text_to_image(
                final_img,
                text_data,
                template_id,
                text_offsets=text_offsets,
                font_settings=font_settings
            )
            
            if (overlay_settings and overlay_settings.get('enabled', False) and 
                overlay_image_url and overlay_image_url.startswith(('http://', 'https://'))):
                
                overlay_img = self.image_processor.load_image_from_url(overlay_image_url, timeout=15, retries=2)
                if overlay_img:
                    processed_img = self.image_processor.add_image_overlay(
                        processed_img,
                        overlay_img,
                        overlay_settings
                    )
            
            output_dir = st.session_state.get('output_dir', 'output_infographics')
            format_ext = export_settings_local.get('format', 'PNG').lower()
            filepath = os.path.join(output_dir, f"{filename}.{format_ext}")
            
            success = self.image_processor.save_image(
                processed_img,
                filepath,
                format=export_settings_local.get('format', 'PNG'),
                quality=export_settings_local.get('quality', 95)
            )
            
            if success:
                return {
                    'row_index': row_index,
                    'status': 'success',
                    'filename': filename,
                    'filepath': filepath,
                    'image_url': image_url,
                    'overlay_image_url': overlay_image_url
                }
            else:
                return {
                    'row_index': row_index,
                    'status': 'error',
                    'message': 'Ошибка сохранения файла',
                    'filename': filename
                }
                
        except Exception as e:
            logger.error(f"Ошибка обработки строки {row_index}: {e}")
            return {
                'row_index': row_index,
                'status': 'error',
                'message': str(e)[:200],
                'filename': f"row_{row_index:04d}"
            }
    
    def generate_filename(self, source: str, index: int) -> str:
        """Генерация имени файла из исходной строки"""
        if not source or str(source).lower() in ['none', 'nan', '']:
            return f"item_{index:06d}"
        
        filename = re.sub(r'[<>:"/\\|?*]', '', str(source))
        filename = re.sub(r'\s+', '_', filename.strip())
        filename = filename[:100]
        
        if not filename:
            filename = f"item_{index:06d}"
        
        return filename
    
    def process_batch(self, df: pd.DataFrame, start_idx: int, end_idx: int, 
                     column_mapping: Dict, template_id: str, export_settings: Dict,
                     processing_settings: Dict, text_offsets: Optional[Dict] = None,
                     overlay_settings: Optional[Dict] = None, 
                     font_settings: Optional[Dict] = None) -> List[Dict]:
        """Пакетная обработка данных"""
        results = []
        total_rows = min(end_idx, len(df) - 1) - start_idx + 1
        
        if total_rows <= 0:
            return results
        
        output_dir = st.session_state.get('output_dir', 'output_infographics')
        os.makedirs(output_dir, exist_ok=True)
        
        max_workers = min(processing_settings.get('max_workers', 4), total_rows, 8)
        max_workers = max(1, max_workers)
        
        logger.info(f"Начало обработки {total_rows} строк, потоков: {max_workers}")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            
            for idx in range(start_idx, min(end_idx + 1, len(df))):
                row = df.iloc[idx]
                future = executor.submit(
                    self.process_single_row,
                    row,
                    column_mapping,
                    template_id,
                    export_settings,
                    idx,
                    text_offsets,
                    overlay_settings,
                    font_settings
                )
                futures[future] = idx
            
            completed = 0
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=processing_settings.get('timeout', 30) * 2)
                    results.append(result)
                    completed += 1
                    
                    progress = completed / total_rows
                    if 'progress_bar' in st.session_state:
                        st.session_state.progress_bar.progress(progress)
                    
                    if 'status_text' in st.session_state:
                        success_count = sum(1 for r in results if r.get('status') == 'success')
                        st.session_state.status_text.text(
                            f"Обработано: {completed}/{total_rows} | "
                            f"Успешно: {success_count} | "
                            f"Ошибок: {completed - success_count}"
                        )
                        
                except Exception as e:
                    idx = futures.get(future, completed)
                    logger.error(f"Ошибка в потоке обработки строки {idx}: {e}")
                    results.append({
                        'row_index': idx,
                        'status': 'error',
                        'message': f'Ошибка потока: {str(e)[:100]}',
                        'filename': f"row_{idx:04d}"
                    })
                    completed += 1
        
        logger.info(f"Обработка завершена. Успешно: {sum(1 for r in results if r.get('status') == 'success')}/{total_rows}")
        return results
    
    def create_zip_archive(self, results: List[Dict], batch_name: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """Создание ZIP архива с результатами"""
        if not batch_name:
            batch_name = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        zip_filename = f"infographics_{batch_name}.zip"
        output_dir = st.session_state.get('output_dir', 'output_infographics')
        zip_path = os.path.join(output_dir, zip_filename)
        
        try:
            results_df = pd.DataFrame(results)
            csv_path = os.path.join(output_dir, f"results_{batch_name}.csv")
            results_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for result in results:
                    if result.get('status') == 'success' and 'filepath' in result:
                        filepath = result['filepath']
                        if os.path.exists(filepath):
                            arcname = os.path.basename(filepath)
                            zipf.write(filepath, arcname)
                
                zipf.write(csv_path, os.path.basename(csv_path))
            
            logger.info(f"ZIP архив создан: {zip_path} ({os.path.getsize(zip_path) / 1024:.1f} KB)")
            return zip_path, csv_path
            
        except Exception as e:
            logger.error(f"Ошибка создания ZIP архива: {e}")
            return None, None

# ============================
# ИНТЕРФЕЙС ПОЛЬЗОВАТЕЛЯ
# ============================
class UIComponents:
    """Класс для компонентов пользовательского интерфейса"""
    
    @staticmethod
    def render_sidebar():
        """Отрисовка боковой панели"""
        with st.sidebar:
            st.title("⚙️ Настройки")
            
            st.subheader("📁 Загрузка данных")
            uploaded_file = st.file_uploader(
                "Выберите Excel файл",
                type=['xlsx', 'xls'],
                help="Файл должен содержать данные о товарах",
                key="sidebar_file_uploader_1"
            )
            
            if uploaded_file:
                if (st.session_state.get('uploaded_file_name') != uploaded_file.name or
                    st.session_state.get('df') is None):
                    
                    with st.spinner("Загрузка файла..."):
                        df = ExcelProcessor.read_excel_file(uploaded_file)
                        if df is not None:
                            st.session_state.df = df
                            st.session_state.uploaded_file_name = uploaded_file.name
                            
                            suggestions = ExcelProcessor.get_column_suggestions(df)
                            st.session_state.column_mapping = suggestions
                            
                            st.success(f"✅ Загружено {len(df)} строк, {len(df.columns)} колонок")
            
            with st.expander("👁️ Предпросмотр данных", expanded=False):
                if st.session_state.get('df') is not None:
                    preview_rows = st.slider(
                        "Строк для предпросмотра", 
                        5, 50, 10,
                        key="sidebar_preview_rows_2"
                    )
                    st.dataframe(st.session_state.df.head(preview_rows), use_container_width=True)
            
            st.subheader("🎨 Выбор шаблона")
            
            template_names = DynamicTemplateManager.get_template_names()
            
            if not template_names:
                st.warning("Не найдено шаблонов. Будет создан стандартный шаблон.")
                template_names = [("modern_shop", "🛒 MODERN SHOP")]
            
            display_options = []
            template_map = {}
            
            for template_id, display_name in template_names:
                display_text = f"{display_name}"
                display_options.append(display_text)
                template_map[display_text] = template_id
            
            current_template = st.session_state.get('current_template', 'modern_shop')
            current_display = None
            
            for display_text, template_id in template_map.items():
                if template_id == current_template:
                    current_display = display_text
                    break
            
            if not current_display and display_options:
                current_display = display_options[0]
                current_template = template_map[current_display]
            
            selected_display = st.selectbox(
                "Шаблон инфографики",
                options=display_options,
                index=display_options.index(current_display) if current_display in display_options else 0,
                key="sidebar_template_select_3"
            )
            
            selected_template = template_map.get(selected_display, 'modern_shop')
            
            if selected_template != st.session_state.current_template:
                st.session_state.current_template = selected_template
                st.rerun()
            
            template_data = DynamicTemplateManager.load_template(selected_template)
            if template_data:
                st.caption(f"**Название:** {template_data.get('name', 'Без названия')}")
                if template_data.get('description'):
                    st.caption(f"**Описание:** {template_data.get('description')}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Обновить", key="sidebar_refresh_4", use_container_width=True):
                    DynamicTemplateManager.scan_template_files()
                    st.rerun()
            
            with col2:
                if st.button("📝 Создать", key="sidebar_create_5", use_container_width=True):
                    st.session_state.editing_template = True
                    st.session_state.editing_template_id = None
                    st.session_state.editing_template_data = {}
                    st.rerun()
            
            st.subheader("🎨 Настройки фонов")
            
            header_bgs = BackgroundLibrary.get_header_backgrounds()
            header_options = {bg['name']: key for key, bg in header_bgs.items()}
            selected_header_name = st.selectbox(
                "Фон шапки",
                options=list(header_options.keys()),
                index=list(header_options.values()).index(
                    st.session_state.background_settings.get('header_background', 'gradient_blue')
                ) if st.session_state.background_settings.get('header_background') in header_options.values() else 0,
                key="sidebar_header_bg_6"
            )
            st.session_state.background_settings['header_background'] = header_options[selected_header_name]
            
            main_bgs = BackgroundLibrary.get_main_backgrounds()
            main_options = {bg['name']: key for key, bg in main_bgs.items()}
            selected_main_name = st.selectbox(
                "Фон основного",
                options=list(main_options.keys()),
                index=list(main_options.values()).index(
                    st.session_state.background_settings.get('main_background', 'white')
                ) if st.session_state.background_settings.get('main_background') in main_options.values() else 0,
                key="sidebar_main_bg_7"
            )
            st.session_state.background_settings['main_background'] = main_options[selected_main_name]
            
            footer_bgs = BackgroundLibrary.get_footer_backgrounds()
            footer_options = {bg['name']: key for key, bg in footer_bgs.items()}
            selected_footer_name = st.selectbox(
                "Фон футера",
                options=list(footer_options.keys()),
                index=list(footer_options.values()).index(
                    st.session_state.background_settings.get('footer_background', 'gradient_dark')
                ) if st.session_state.background_settings.get('footer_background') in footer_options.values() else 0,
                key="sidebar_footer_bg_8"
            )
            st.session_state.background_settings['footer_background'] = footer_options[selected_footer_name]
            
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.background_settings['header_height'] = st.slider(
                    "Высота шапки (%)",
                    0, 40,
                    st.session_state.background_settings.get('header_height', 15),
                    key="sidebar_header_height_9"
                )
            
            with col2:
                st.session_state.background_settings['footer_height'] = st.slider(
                    "Высота футера (%)",
                    0, 40,
                    st.session_state.background_settings.get('footer_height', 10),
                    key="sidebar_footer_height_10"
                )
            
            st.session_state.background_settings['corner_radius'] = st.slider(
                "Скругление углов",
                0, 50,
                st.session_state.background_settings.get('corner_radius', 20),
                key="sidebar_corner_radius_11"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.background_settings['shadow_enabled'] = st.checkbox(
                    "Тень",
                    value=st.session_state.background_settings.get('shadow_enabled', True),
                    key="sidebar_shadow_12"
                )
            
            with col2:
                st.session_state.background_settings['border_enabled'] = st.checkbox(
                    "Рамка",
                    value=st.session_state.background_settings.get('border_enabled', True),
                    key="sidebar_border_13"
                )
            
            st.subheader("💾 Настройки экспорта")
            col1, col2 = st.columns(2)
            with col1:
                export_format = st.selectbox(
                    "Формат",
                    ["PNG", "JPEG", "WebP"],
                    index=["PNG", "JPEG", "WebP"].index(
                        st.session_state.export_settings.get('format', 'PNG')
                    ),
                    key="sidebar_export_format_14"
                )
                st.session_state.export_settings['format'] = export_format
            
            with col2:
                quality = st.slider(
                    "Качество",
                    50, 100,
                    st.session_state.export_settings.get('quality', 95),
                    key="sidebar_export_quality_15"
                )
                st.session_state.export_settings['quality'] = quality
            
            resize_checkbox = st.checkbox(
                "Изменять размер",
                st.session_state.export_settings.get('resize', True),
                key="sidebar_resize_checkbox_16"
            )
            st.session_state.export_settings['resize'] = resize_checkbox
            
            if st.session_state.export_settings['resize']:
                target_size = st.select_slider(
                    "Целевой размер",
                    options=[800, 1200, 1600, 2000],
                    value=st.session_state.export_settings.get('target_size', 1200),
                    key="sidebar_target_size_17"
                )
                st.session_state.export_settings['target_size'] = target_size
            
            st.subheader("⚡ Настройки обработки")
            col1, col2 = st.columns(2)
            with col1:
                batch_size = st.select_slider(
                    "Размер партии",
                    options=[10, 25, 50, 100, 200],
                    value=st.session_state.processing_settings.get('batch_size', 50),
                    key="sidebar_batch_size_18"
                )
                st.session_state.processing_settings['batch_size'] = batch_size
            
            with col2:
                max_workers = st.select_slider(
                    "Потоки",
                    options=[1, 2, 4, 6, 8],
                    value=st.session_state.processing_settings.get('max_workers', 4),
                    key="sidebar_max_workers_19"
                )
                st.session_state.processing_settings['max_workers'] = max_workers
            
            timeout_input = st.select_slider(
                "Таймаут (сек)",
                options=[10, 15, 30, 45, 60],
                value=st.session_state.processing_settings.get('timeout', 30),
                key="sidebar_timeout_20"
            )
            st.session_state.processing_settings['timeout'] = timeout_input
            
            retry_count = st.select_slider(
                "Повторные попытки",
                options=[0, 1, 2, 3, 5],
                value=st.session_state.processing_settings.get('retry_count', 3),
                key="sidebar_retry_count_21"
            )
            st.session_state.processing_settings['retry_count'] = retry_count
            
            st.divider()
            st.caption(f"Обработано: {st.session_state.get('processed_count', 0)} изображений")
            st.caption(f"Шаблонов: {len(template_names)}")
            st.caption(f"Версия: 7.0 PRO")
    
    @staticmethod
    def render_background_settings():
        """Настройки фонов"""
        st.subheader("🎨 Настройки фонов")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 🎩 Шапка")
            header_bgs = BackgroundLibrary.get_header_backgrounds()
            
            header_preview = st.selectbox(
                "Фон шапки",
                options=[bg['name'] for bg in header_bgs.values()],
                index=list(header_bgs.keys()).index(
                    st.session_state.background_settings.get('header_background', 'gradient_blue')
                ) if st.session_state.background_settings.get('header_background') in header_bgs else 0,
                key="bg_header_select_22"
            )
            
            for key, bg in header_bgs.items():
                if bg['name'] == header_preview:
                    st.session_state.background_settings['header_background'] = key
                    break
            
            st.session_state.background_settings['header_height'] = st.slider(
                "Высота шапки (%)",
                0, 40,
                st.session_state.background_settings.get('header_height', 15),
                key="bg_header_height_23"
            )
            
            header_bg_config = header_bgs.get(st.session_state.background_settings['header_background'], {})
            if header_bg_config.get('type') == 'gradient':
                colors = header_bg_config.get('colors', [(30, 144, 255), (0, 102, 204)])
                color1 = f"rgb{colors[0]}" if len(colors) > 0 else "rgb(30, 144, 255)"
                color2 = f"rgb{colors[1]}" if len(colors) > 1 else "rgb(0, 102, 204)"
                st.markdown(f'<div style="height: 20px; background: linear-gradient(to right, {color1}, {color2}); border-radius: 5px; margin: 5px 0;"></div>', 
                           unsafe_allow_html=True)
        
        with col2:
            st.markdown("### 🖼️ Основное")
            main_bgs = BackgroundLibrary.get_main_backgrounds()
            
            main_preview = st.selectbox(
                "Фон основного",
                options=[bg['name'] for bg in main_bgs.values()],
                index=list(main_bgs.keys()).index(
                    st.session_state.background_settings.get('main_background', 'white')
                ) if st.session_state.background_settings.get('main_background') in main_bgs else 0,
                key="bg_main_select_24"
            )
            
            for key, bg in main_bgs.items():
                if bg['name'] == main_preview:
                    st.session_state.background_settings['main_background'] = key
                    break
            
            main_bg_config = main_bgs.get(st.session_state.background_settings['main_background'], {})
            if main_bg_config.get('type') == 'gradient':
                colors = main_bg_config.get('colors', [(250, 250, 250), (240, 240, 240)])
                color1 = f"rgb{colors[0]}" if len(colors) > 0 else "rgb(250, 250, 250)"
                color2 = f"rgb{colors[1]}" if len(colors) > 1 else "rgb(240, 240, 240)"
                st.markdown(f'<div style="height: 20px; background: linear-gradient(to bottom, {color1}, {color2}); border-radius: 5px; margin: 5px 0;"></div>', 
                           unsafe_allow_html=True)
            elif main_bg_config.get('type') == 'solid':
                color = main_bg_config.get('color', (255, 255, 255))
                st.markdown(f'<div style="height: 20px; background: rgb{color}; border-radius: 5px; margin: 5px 0;"></div>', 
                           unsafe_allow_html=True)
        
        with col3:
            st.markdown("### 👣 Футер")
            footer_bgs = BackgroundLibrary.get_footer_backgrounds()
            
            footer_preview = st.selectbox(
                "Фон футера",
                options=[bg['name'] for bg in footer_bgs.values()],
                index=list(footer_bgs.keys()).index(
                    st.session_state.background_settings.get('footer_background', 'gradient_dark')
                ) if st.session_state.background_settings.get('footer_background') in footer_bgs else 0,
                key="bg_footer_select_25"
            )
            
            for key, bg in footer_bgs.items():
                if bg['name'] == footer_preview:
                    st.session_state.background_settings['footer_background'] = key
                    break
            
            st.session_state.background_settings['footer_height'] = st.slider(
                "Высота футера (%)",
                0, 40,
                st.session_state.background_settings.get('footer_height', 10),
                key="bg_footer_height_26"
            )
            
            footer_bg_config = footer_bgs.get(st.session_state.background_settings['footer_background'], {})
            if footer_bg_config.get('type') == 'gradient':
                colors = footer_bg_config.get('colors', [(33, 37, 41), (52, 58, 64)])
                color1 = f"rgb{colors[0]}" if len(colors) > 0 else "rgb(33, 37, 41)"
                color2 = f"rgb{colors[1]}" if len(colors) > 1 else "rgb(52, 58, 64)"
                st.markdown(f'<div style="height: 20px; background: linear-gradient(to right, {color1}, {color2}); border-radius: 5px; margin: 5px 0;"></div>', 
                           unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("🎛️ Дополнительные настройки")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.session_state.background_settings['corner_radius'] = st.slider(
                "Скругление углов",
                0, 50,
                st.session_state.background_settings.get('corner_radius', 20),
                key="bg_corner_radius_27"
            )
        
        with col2:
            st.session_state.background_settings['shadow_enabled'] = st.checkbox(
                "Эффект тени",
                value=st.session_state.background_settings.get('shadow_enabled', True),
                key="bg_shadow_28"
            )
        
        with col3:
            st.session_state.background_settings['border_enabled'] = st.checkbox(
                "Рамка",
                value=st.session_state.background_settings.get('border_enabled', True),
                key="bg_border_29"
            )
        
        if st.session_state.background_settings['border_enabled']:
            col1, col2 = st.columns(2)
            with col1:
                border_color = st.color_picker(
                    "Цвет рамки",
                    value=st.session_state.background_settings.get('border_color', '#e0e0e0'),
                    key="bg_border_color_30"
                )
                st.session_state.background_settings['border_color'] = border_color
            
            with col2:
                st.session_state.background_settings['border_width'] = st.slider(
                    "Толщина рамки",
                    1, 10,
                    st.session_state.background_settings.get('border_width', 2),
                    key="bg_border_width_31"
                )
        
        st.info("💡 **Совет:** Используйте контрастные цвета для шапки и футера для лучшего визуального восприятия.")
    
    @staticmethod
    def render_template_preview():
        """Предпросмотр шаблонов с фонами"""
        st.subheader("👁️ Предпросмотр шаблонов")
        
        categories = DynamicTemplateManager.get_template_categories()
        selected_category = st.selectbox(
            "Категория шаблонов",
            options=list(categories.values()),
            index=list(categories.values()).index(
                categories.get(st.session_state.current_category, 'Все шаблоны')
            ),
            key="template_category_select_32"
        )
        
        for key, value in categories.items():
            if value == selected_category:
                st.session_state.current_category = key
                break
        
        template_names = DynamicTemplateManager.get_templates_by_category(st.session_state.current_category)
        
        if not template_names:
            st.info("📝 Шаблоны не найдены в выбранной категории.")
            return
        
        cols = st.columns(3)
        
        for idx, (template_id, display_name) in enumerate(template_names[:6]):
            with cols[idx % 3]:
                template_data = DynamicTemplateManager.load_template(template_id)
                
                with st.container():
                    st.markdown(f"### {display_name}")
                    st.caption(template_data.get('description', 'Без описания'))
                    
                    preview_size = st.session_state.get('template_preview_size', 400)
                    preview_width = preview_size
                    preview_height = int(preview_size * 0.75)
                    
                    try:
                        preview_canvas = ImageProcessor.create_template_canvas(
                            preview_width, preview_height, template_id
                        )
                        
                        draw = ImageDraw.Draw(preview_canvas)
                        
                        layout = template_data.get("layout", {})
                        header_height = int(preview_height * layout.get("header_height", 15) / 100)
                        footer_height = int(preview_height * layout.get("footer_height", 10) / 100)
                        main_height = preview_height - header_height - footer_height
                        
                        text_positions = template_data.get("text_positions", {})
                        
                        for pos_key, pos_data in text_positions.items():
                            x = pos_data.get("x", 0.5) * preview_width
                            y = pos_data.get("y", 0.5)
                            
                            section = pos_data.get("section", "main")
                            if section == "header":
                                y = y * header_height
                            elif section == "footer":
                                y = header_height + main_height + y * footer_height
                            else:
                                y = header_height + y * main_height
                            
                            draw.ellipse([x-3, y-3, x+3, y+3], fill='red')
                        
                        st.image(preview_canvas, use_container_width=True)
                        
                        if st.button(f"Выбрать {display_name}", 
                                   key=f"select_template_{template_id}_{idx}",
                                   use_container_width=True):
                            st.session_state.current_template = template_id
                            st.success(f"Выбран шаблон: {display_name}")
                            st.rerun()
                    
                    except Exception as e:
                        st.error(f"Ошибка создания превью: {e}")
        
        if len(template_names) > 6:
            st.info(f"📋 И еще {len(template_names) - 6} шаблонов в этой категории...")
    
    @staticmethod
    def render_column_mapping():
        """Настройка маппинга колонок"""
        if st.session_state.get('df') is not None:
            st.subheader("📊 Настройка маппинга колонок")
            st.info("Выберите, какие колонки из файла соответствуют элементам инфографики")
            
            available_columns = st.session_state.df.columns.tolist()
            
            if not available_columns:
                st.error("В файле нет колонок!")
                return
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.session_state.column_mapping['top_left'] = st.selectbox(
                    "Верхний левый угол (Название)",
                    available_columns,
                    index=available_columns.index(
                        st.session_state.column_mapping.get('top_left', available_columns[0])
                    ) if st.session_state.column_mapping.get('top_left') in available_columns else 0,
                    key="mapping_top_left_33"
                )
                st.session_state.column_mapping['top_right'] = st.selectbox(
                    "Верхний правый угол (Цена)",
                    available_columns,
                    index=available_columns.index(
                        st.session_state.column_mapping.get('top_right', available_columns[1])
                    ) if st.session_state.column_mapping.get('top_right') in available_columns and len(available_columns) > 1 else min(1, len(available_columns)-1),
                    key="mapping_top_right_34"
                )
                st.session_state.column_mapping['image_url'] = st.selectbox(
                    "URL основного изображения",
                    available_columns,
                    index=available_columns.index(
                        st.session_state.column_mapping.get('image_url', available_columns[2])
                    ) if st.session_state.column_mapping.get('image_url') in available_columns and len(available_columns) > 2 else min(2, len(available_columns)-1),
                    key="mapping_image_url_35"
                )
            
            with col2:
                st.session_state.column_mapping['bottom_left'] = st.selectbox(
                    "Нижний левый угол (Характеристики)",
                    available_columns,
                    index=available_columns.index(
                        st.session_state.column_mapping.get('bottom_left', available_columns[3])
                    ) if st.session_state.column_mapping.get('bottom_left') in available_columns and len(available_columns) > 3 else min(3, len(available_columns)-1),
                    key="mapping_bottom_left_36"
                )
                st.session_state.column_mapping['bottom_right'] = st.selectbox(
                    "Нижний правый угол (Скидка/Детали)",
                    available_columns,
                    index=available_columns.index(
                        st.session_state.column_mapping.get('bottom_right', available_columns[4])
                    ) if st.session_state.column_mapping.get('bottom_right') in available_columns and len(available_columns) > 4 else min(4, len(available_columns)-1),
                    key="mapping_bottom_right_37"
                )
                st.session_state.column_mapping['filename'] = st.selectbox(
                    "Имена файлов (источник)",
                    available_columns,
                    index=available_columns.index(
                        st.session_state.column_mapping.get('filename', available_columns[0])
                    ) if st.session_state.column_mapping.get('filename') in available_columns else 0,
                    key="mapping_filename_38"
                )
            
            st.subheader("🖼️ Изображение для наложения")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                overlay_image_column = st.selectbox(
                    "Колонка с изображениями для наложения",
                    ["Не использовать"] + available_columns,
                    index=0 if st.session_state.column_mapping.get('overlay_image_url') not in available_columns else 
                          available_columns.index(st.session_state.column_mapping.get('overlay_image_url')) + 1,
                    key="mapping_overlay_image_39"
                )
                
                if overlay_image_column != "Не использовать":
                    st.session_state.column_mapping['overlay_image_url'] = overlay_image_column
                elif 'overlay_image_url' in st.session_state.column_mapping:
                    del st.session_state.column_mapping['overlay_image_url']
            
            with col2:
                st.session_state.image_overlay_settings['enabled'] = st.checkbox(
                    "Включить наложение",
                    value=st.session_state.image_overlay_settings.get('enabled', False),
                    key="mapping_enable_overlay_40"
                )
            
            if st.button("🔍 Автоподбор колонок", type="secondary", key="auto_map_41"):
                suggestions = ExcelProcessor.get_column_suggestions(st.session_state.df)
                st.session_state.column_mapping = suggestions
                st.success("✅ Колонки автоматически подобраны!")
                time.sleep(1)
                st.rerun()
    
    @staticmethod
    def render_font_settings():
        """Настройки шрифтов"""
        st.subheader("🔤 Настройки шрифтов")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Загрузка шрифтов**")
            
            uploaded_fonts = st.file_uploader(
                "Загрузите файлы шрифтов (.ttf, .otf)",
                type=['ttf', 'otf'],
                accept_multiple_files=True,
                help="Загрузите свои шрифты для использования в инфографике",
                key="font_uploader_42"
            )
            
            if uploaded_fonts:
                for font_file in uploaded_fonts:
                    with st.spinner(f"Загрузка {font_file.name}..."):
                        font_key, font_name = FontManager.load_font_from_file(font_file)
                        if font_key:
                            st.success(f"✅ Шрифт '{font_name}' загружен")
                        else:
                            st.error(f"❌ Ошибка загрузки шрифта '{font_file.name}'")
            
            if st.session_state.get('uploaded_fonts'):
                st.markdown("**Загруженные шрифты:**")
                for font_info in st.session_state.uploaded_fonts:
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.caption(f"📁 {font_info['name']}")
                    with col_b:
                        if st.button("🗑️", key=f"delete_font_{font_info['key']}_43"):
                            if font_info['key'] in st.session_state.font_cache:
                                del st.session_state.font_cache[font_info['key']]
                            
                            st.session_state.uploaded_fonts = [
                                f for f in st.session_state.uploaded_fonts 
                                if f['key'] != font_info['key']
                            ]
                            st.rerun()
        
        with col2:
            st.markdown("**Выбор шрифтов**")
            
            available_fonts = FontManager.get_available_fonts()
            
            if available_fonts:
                font_options = [f["name"] for f in available_fonts]
                font_keys = [f["key"] for f in available_fonts]
                
                current_main_font = st.session_state.font_settings.get('main_font', 'system_arial')
                current_main_index = font_keys.index(current_main_font) if current_main_font in font_keys else 0
                
                main_font_name = st.selectbox(
                    "Основной шрифт",
                    font_options,
                    index=current_main_index,
                    key="main_font_select_44"
                )
                
                if main_font_name:
                    selected_index = font_options.index(main_font_name)
                    st.session_state.font_settings['main_font'] = font_keys[selected_index]
                
                current_bold_font = st.session_state.font_settings.get('bold_font', 'system_arial')
                current_bold_index = font_keys.index(current_bold_font) if current_bold_font in font_keys else 0
                
                bold_font_name = st.selectbox(
                    "Жирный шрифт (для заголовков)",
                    ["Тот же что основной"] + font_options,
                    index=0 if current_bold_font == current_main_font else current_bold_index + 1,
                    key="bold_font_select_45"
                )
                
                if bold_font_name == "Тот же что основной":
                    st.session_state.font_settings['bold_font'] = st.session_state.font_settings['main_font']
                elif bold_font_name:
                    selected_index = font_options.index(bold_font_name)
                    st.session_state.font_settings['bold_font'] = font_keys[selected_index]
                
                font_size_multiplier = st.slider(
                    "Множитель размера шрифта",
                    0.5, 2.0, 0.1,
                    st.session_state.font_settings.get('font_size_multiplier', 1.0),
                    key="font_size_multiplier_46"
                )
                st.session_state.font_settings['font_size_multiplier'] = font_size_multiplier
    
    @staticmethod
    def render_text_offset_settings():
        """Настройки смещения текста"""
        if st.session_state.get('df') is not None:
            st.subheader("🎯 Настройки смещения текста")
            st.info("Регулируйте положение текста на изображении")
            
            col1, col2 = st.columns(2)
            with col1:
                symmetrical = st.checkbox(
                    "🔄 Симметричные смещения для всех углов",
                    value=st.session_state.get('symmetrical_offsets', False),
                    help="При включении все углы будут иметь одинаковые смещения",
                    key="symmetrical_offsets_47"
                )
                st.session_state.symmetrical_offsets = symmetrical
            
            with col2:
                if symmetrical:
                    st.info("⚠️ Режим симметричных смещений активен")
            
            cols = st.columns(4)
            
            with cols[0]:
                st.markdown("**↖️ Верхний левый**")
                if not symmetrical:
                    x_offset = st.number_input(
                        "Смещение X (%)",
                        -100, 100,
                        st.session_state.text_offset_settings['top_left'].get('x_offset', 0),
                        key="top_left_x_48"
                    )
                    y_offset = st.number_input(
                        "Смещение Y (%)",
                        -100, 100,
                        st.session_state.text_offset_settings['top_left'].get('y_offset', 0),
                        key="top_left_y_49"
                    )
                    st.session_state.text_offset_settings['top_left'] = {
                        'x_offset': x_offset,
                        'y_offset': y_offset
                    }
                else:
                    st.info("Настройки применяются ко всем углам")
            
            with cols[1]:
                st.markdown("**↗️ Верхний правый**")
                if not symmetrical:
                    x_offset = st.number_input(
                        "Смещение X (%)",
                        -100, 100,
                        st.session_state.text_offset_settings['top_right'].get('x_offset', 0),
                        key="top_right_x_50"
                    )
                    y_offset = st.number_input(
                        "Смещение Y (%)",
                        -100, 100,
                        st.session_state.text_offset_settings['top_right'].get('y_offset', 0),
                        key="top_right_y_51"
                    )
                    st.session_state.text_offset_settings['top_right'] = {
                        'x_offset': x_offset,
                        'y_offset': y_offset
                    }
                else:
                    st.caption(f"X: {st.session_state.text_offset_settings['top_left'].get('x_offset', 0)}%")
                    st.caption(f"Y: {st.session_state.text_offset_settings['top_left'].get('y_offset', 0)}%")
            
            with cols[2]:
                st.markdown("**↙️ Нижний левый**")
                if not symmetrical:
                    x_offset = st.number_input(
                        "Смещение X (%)",
                        -100, 100,
                        st.session_state.text_offset_settings['bottom_left'].get('x_offset', 0),
                        key="bottom_left_x_52"
                    )
                    y_offset = st.number_input(
                        "Смещение Y (%)",
                        -100, 100,
                        st.session_state.text_offset_settings['bottom_left'].get('y_offset', 0),
                        key="bottom_left_y_53"
                    )
                    st.session_state.text_offset_settings['bottom_left'] = {
                        'x_offset': x_offset,
                        'y_offset': y_offset
                    }
                else:
                    st.caption(f"X: {st.session_state.text_offset_settings['top_left'].get('x_offset', 0)}%")
                    st.caption(f"Y: {st.session_state.text_offset_settings['top_left'].get('y_offset', 0)}%")
            
            with cols[3]:
                st.markdown("**↘️ Нижний правый**")
                if not symmetrical:
                    x_offset = st.number_input(
                        "Смещение X (%)",
                        -100, 100,
                        st.session_state.text_offset_settings['bottom_right'].get('x_offset', 0),
                        key="bottom_right_x_54"
                    )
                    y_offset = st.number_input(
                        "Смещение Y (%)",
                        -100, 100,
                        st.session_state.text_offset_settings['bottom_right'].get('y_offset', 0),
                        key="bottom_right_y_55"
                    )
                    st.session_state.text_offset_settings['bottom_right'] = {
                        'x_offset': x_offset,
                        'y_offset': y_offset
                    }
                else:
                    st.caption(f"X: {st.session_state.text_offset_settings['top_left'].get('x_offset', 0)}%")
                    st.caption(f"Y: {st.session_state.text_offset_settings['top_left'].get('y_offset', 0)}%")
            
            if symmetrical:
                st.markdown("---")
                st.subheader("🔄 Общие настройки для всех углов")
                
                col1, col2 = st.columns(2)
                with col1:
                    common_x_offset = st.number_input(
                        "Общее смещение по X (%)",
                        -100, 100,
                        st.session_state.text_offset_settings['top_left'].get('x_offset', 0),
                        key="common_x_56"
                    )
                with col2:
                    common_y_offset = st.number_input(
                        "Общее смещение по Y (%)",
                        -100, 100,
                        st.session_state.text_offset_settings['top_left'].get('y_offset', 0),
                        key="common_y_57"
                    )
                
                st.session_state.text_offset_settings = {
                    'top_left': {'x_offset': common_x_offset, 'y_offset': common_y_offset},
                    'top_right': {'x_offset': common_x_offset, 'y_offset': common_y_offset},
                    'bottom_left': {'x_offset': common_x_offset, 'y_offset': common_y_offset},
                    'bottom_right': {'x_offset': common_x_offset, 'y_offset': common_y_offset}
                }
            
            st.caption("💡 Положительные значения смещают текст вправо/вниз, отрицательные - влево/вверх")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Сбросить смещения", type="secondary", key="reset_offsets_58", use_container_width=True):
                    st.session_state.text_offset_settings = {
                        'top_left': {'x_offset': 0, 'y_offset': 0},
                        'top_right': {'x_offset': 0, 'y_offset': 0},
                        'bottom_left': {'x_offset': 0, 'y_offset': 0},
                        'bottom_right': {'x_offset': 0, 'y_offset': 0}
                    }
                    st.rerun()
            
            with col2:
                if not symmetrical:
                    if st.button("📐 Сделать симметричными", type="secondary", key="make_symmetrical_59", use_container_width=True):
                        top_left_settings = st.session_state.text_offset_settings['top_left']
                        st.session_state.text_offset_settings = {
                            'top_left': top_left_settings,
                            'top_right': top_left_settings.copy(),
                            'bottom_left': top_left_settings.copy(),
                            'bottom_right': top_left_settings.copy()
                        }
                        st.success("✅ Настройки применены ко всем углам!")
                        st.rerun()
    
    @staticmethod
    def render_image_overlay_settings():
        """Настройки наложения изображений"""
        if st.session_state.get('df') is not None and st.session_state.image_overlay_settings.get('enabled', False):
            st.subheader("🖼️ Настройки наложения изображений")
            st.info("Настройте параметры для дополнительных изображений (логотипы, стикеры и т.д.)")
            
            col1, col2 = st.columns(2)
            with col1:
                position = st.selectbox(
                    "Позиция на изображении",
                    ["center", "top_left", "top_right", "bottom_left", "bottom_right"],
                    index=["center", "top_left", "top_right", "bottom_left", "bottom_right"].index(
                        st.session_state.image_overlay_settings.get('position', 'center')
                    ),
                    key="overlay_position_60"
                )
                st.session_state.image_overlay_settings['position'] = position
            
            with col2:
                opacity = st.slider(
                    "Прозрачность (%)",
                    0, 100,
                    st.session_state.image_overlay_settings.get('opacity', 100),
                    key="overlay_opacity_61"
                )
                st.session_state.image_overlay_settings['opacity'] = opacity
            
            col1, col2 = st.columns(2)
            with col1:
                scale = st.slider(
                    "Масштаб (%)",
                    10, 200,
                    st.session_state.image_overlay_settings.get('scale', 100),
                    key="overlay_scale_62"
                )
                st.session_state.image_overlay_settings['scale'] = scale
            
            with col2:
                max_width = st.slider(
                    "Макс. ширина (% от основного)",
                    5, 100,
                    st.session_state.image_overlay_settings.get('max_width', 30),
                    key="overlay_max_width_63"
                )
                st.session_state.image_overlay_settings['max_width'] = max_width
            
            col1, col2 = st.columns(2)
            with col1:
                x_offset = st.number_input(
                    "Смещение по X (%)",
                    -100, 100,
                    st.session_state.image_overlay_settings.get('x_offset', 0),
                    key="overlay_x_offset_64"
                )
                st.session_state.image_overlay_settings['x_offset'] = x_offset
            
            with col2:
                y_offset = st.number_input(
                    "Смещение по Y (%)",
                    -100, 100,
                    st.session_state.image_overlay_settings.get('y_offset', 0),
                    key="overlay_y_offset_65"
                )
                st.session_state.image_overlay_settings['y_offset'] = y_offset
    
    @staticmethod
    def render_preview_tab(generator):
        """Вкладка предпросмотра"""
        if st.session_state.get('df') is None:
            st.info("📥 Загрузите Excel файл в боковой панели для начала работы")
            return
        
        st.header("🎯 Предпросмотр и тестирование")
        
        UIComponents.render_font_settings()
        UIComponents.render_text_offset_settings()
        UIComponents.render_image_overlay_settings()
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            test_row_idx = st.number_input(
                "Номер строки для тестирования",
                min_value=0,
                max_value=len(st.session_state.df)-1,
                value=min(0, len(st.session_state.df)-1),
                key="preview_test_row_66"
            )
        with col2:
            timeout = st.select_slider(
                "Таймаут (сек)",
                options=[5, 10, 15, 30, 60],
                value=st.session_state.export_settings.get('timeout', 30),
                key="preview_timeout_67"
            )
        with col3:
            st.write("")
            st.write("")
            test_button = st.button("🚀 Запустить тест", type="primary", key="preview_test_button_68", use_container_width=True)
        
        if test_button and test_row_idx < len(st.session_state.df):
            with st.spinner("Выполнение теста..."):
                row = st.session_state.df.iloc[test_row_idx]
                
                text_data = {}
                for position in ['top_left', 'top_right', 'bottom_left', 'bottom_right']:
                    col = st.session_state.column_mapping.get(position)
                    if col and col in row:
                        text_data[position] = str(row[col] or '')
                    else:
                        text_data[position] = ''
                
                image_url = ''
                if 'image_url' in st.session_state.column_mapping:
                    col = st.session_state.column_mapping['image_url']
                    if col in row:
                        image_url = str(row[col] or '')
                
                overlay_image_url = None
                if ('overlay_image_url' in st.session_state.column_mapping and 
                    st.session_state.column_mapping['overlay_image_url'] in row):
                    overlay_image_url = str(row[st.session_state.column_mapping['overlay_image_url']] or '')
                    if overlay_image_url.lower() in ['none', 'nan', '']:
                        overlay_image_url = None
                
                with st.expander("📋 Исходные данные строки"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.json(text_data, expanded=False)
                    with col2:
                        st.code(f"Основное изображение:\n{image_url[:100]}..." if len(image_url) > 100 else f"Основное изображение:\n{image_url}")
                        if overlay_image_url:
                            st.code(f"Изображение наложения:\n{overlay_image_url[:100]}..." if len(overlay_image_url) > 100 else f"Изображение наложения:\n{overlay_image_url}")
                
                if image_url and image_url.startswith(('http://', 'https://')):
                    img = generator.image_processor.load_image_from_url(image_url, timeout)
                    
                    if img:
                        if st.session_state.get('symmetrical_offsets', False):
                            st.success(f"**🔄 Симметричные смещения:** X: {st.session_state.text_offset_settings['top_left'].get('x_offset', 0)}%, Y: {st.session_state.text_offset_settings['top_left'].get('y_offset', 0)}%")
                        else:
                            offset_info = "\n".join([
                                f"{pos}: X={offsets.get('x_offset', 0)}%, Y={offsets.get('y_offset', 0)}%"
                                for pos, offsets in st.session_state.text_offset_settings.items()
                            ])
                            st.info(f"**Применяемые смещения текста:**\n{offset_info}")
                        
                        if st.session_state.image_overlay_settings.get('enabled', False):
                            st.info(f"**Наложение изображений:** Включено, позиция: {st.session_state.image_overlay_settings.get('position', 'center')}")
                        
                        if st.session_state.export_settings.get('resize', True):
                            target_size = st.session_state.export_settings.get('target_size', 1200)
                            img = generator.image_processor.resize_image(img, target_size)
                        
                        template_canvas = generator.image_processor.create_template_canvas(
                            img.width, img.height, st.session_state.current_template
                        )
                        
                        final_img = template_canvas.copy()
                        
                        header_height = int(img.height * st.session_state.background_settings.get('header_height', 15) / 100)
                        final_img.paste(img, (0, header_height))
                        
                        processed_img = generator.image_processor.add_text_to_image(
                            final_img,
                            text_data,
                            st.session_state.current_template,
                            text_offsets=st.session_state.text_offset_settings,
                            font_settings=st.session_state.font_settings
                        )
                        
                        if (st.session_state.image_overlay_settings.get('enabled', False) and 
                            overlay_image_url and overlay_image_url.startswith(('http://', 'https://', 'data:'))):
                            
                            overlay_img = generator.image_processor.load_image_from_url(overlay_image_url, timeout=15, retries=2)
                            if overlay_img:
                                processed_img = generator.image_processor.add_image_overlay(
                                    processed_img,
                                    overlay_img,
                                    st.session_state.image_overlay_settings
                                )
                                st.success("✅ Изображение наложения добавлено")
                            else:
                                st.warning("⚠️ Не удалось загрузить изображение для наложения")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("📷 Оригинал")
                            st.image(img, use_column_width=True)
                            st.caption(f"Размер: {img.width}×{img.height}, Формат: {img.format or 'Неизвестно'}")
                        with col2:
                            st.subheader("🎨 С инфографикой")
                            st.image(processed_img, use_column_width=True)
                            st.caption(f"Шаблон: {st.session_state.current_template}")
                            
                            show_grid = st.checkbox("Показать сетку позиций", value=False, key="preview_show_grid_69")
                            if show_grid:
                                grid_img = processed_img.copy()
                                draw = ImageDraw.Draw(grid_img)
                                template = DynamicTemplateManager.load_template(st.session_state.current_template)
                                
                                text_positions = template.get("text_positions", {})
                                
                                for position_key, position_data in text_positions.items():
                                    base_x = position_data.get("x", 0.5) * grid_img.width
                                    base_y = position_data.get("y", 0.5)
                                    
                                    layout = template.get("layout", {})
                                    header_height_percent = layout.get("header_height", 15)
                                    footer_height_percent = layout.get("footer_height", 10)
                                    
                                    header_height_px = int(grid_img.height * header_height_percent / 100)
                                    footer_height_px = int(grid_img.height * footer_height_percent / 100)
                                    main_height_px = grid_img.height - header_height_px - footer_height_px
                                    
                                    section = position_data.get("section", "main")
                                    if section == "header":
                                        base_y = base_y * header_height_px
                                    elif section == "footer":
                                        base_y = header_height_px + main_height_px + base_y * footer_height_px
                                    else:
                                        base_y = header_height_px + base_y * main_height_px
                                    
                                    x = int(base_x)
                                    y = int(base_y)
                                    
                                    draw.ellipse([x-5, y-5, x+5, y+5], fill='red')
                                    draw.text((x+10, y-10), position_key, fill='red', 
                                             font=FontManager.load_system_font('system_arial', 12))
                                
                                st.image(grid_img, use_container_width=True, caption="Сетка позиций текста (красные точки)")
                        
                        buffered = BytesIO()
                        format_ext = st.session_state.export_settings.get('format', 'PNG').lower()
                        
                        if st.session_state.export_settings['format'] == 'JPEG':
                            processed_img.convert('RGB').save(
                                buffered,
                                format='JPEG',
                                quality=st.session_state.export_settings.get('quality', 95)
                            )
                            mime_type = 'image/jpeg'
                        elif st.session_state.export_settings['format'] == 'WEBP':
                            processed_img.save(
                                buffered,
                                format='WEBP',
                                quality=st.session_state.export_settings.get('quality', 95)
                            )
                            mime_type = 'image/webp'
                        else:
                            processed_img.save(buffered, format='PNG')
                            mime_type = 'image/png'
                        
                        st.download_button(
                            label="💾 Скачать тестовое изображение",
                            data=buffered.getvalue(),
                            file_name=f"test_preview_{test_row_idx}.{format_ext}",
                            mime=mime_type,
                            key="preview_download_70",
                            use_container_width=True
                        )
                        
                        st.session_state.preview_image = processed_img
                    else:
                        st.error("❌ Не удалось загрузить изображение. Проверьте URL и подключение к интернету.")
                else:
                    st.warning("⚠️ Некорректный URL основного изображения")
    
    @staticmethod
    def render_processing_tab(generator):
        """Вкладка обработки"""
        if st.session_state.get('df') is None:
            st.info("📥 Загрузите Excel файл в боковой панели для начала работы")
            return
        
        st.header("⚡ Массовая обработка")
        
        df_optimized = ExcelProcessor.optimize_dataframe(st.session_state.df)
        total_rows = len(df_optimized)
        
        if total_rows == 0:
            st.error("❌ Нет данных для обработки. Проверьте наличие URL изображений в файле.")
            return
        
        if st.session_state.get('symmetrical_offsets', False):
            st.success(f"**🔄 Будут применены симметричные смещения:** X: {st.session_state.text_offset_settings['top_left'].get('x_offset', 0)}%, Y: {st.session_state.text_offset_settings['top_left'].get('y_offset', 0)}%")
        else:
            offset_info = "\n".join([
                f"{pos}: X={offsets.get('x_offset', 0)}%, Y={offsets.get('y_offset', 0)}%"
                for pos, offsets in st.session_state.text_offset_settings.items()
            ])
            st.info(f"**Будут применены смещения текста:**\n{offset_info}")
        
        if st.session_state.image_overlay_settings.get('enabled', False):
            st.info(f"**🖼️ Наложение изображений:** Включено, позиция: {st.session_state.image_overlay_settings.get('position', 'center')}")
        
        if st.session_state.font_settings.get('main_font'):
            available_fonts = FontManager.get_available_fonts()
            font_name = next((f["name"] for f in available_fonts if f["key"] == st.session_state.font_settings['main_font']), "Системный шрифт")
            st.info(f"**🔤 Шрифт:** {font_name}, множитель: {st.session_state.font_settings.get('font_size_multiplier', 1.0)}")
        
        st.info(f"📊 Готово к обработке: {total_rows} строк")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            start_idx = st.number_input(
                "Начать с строки",
                0, total_rows-1, 0,
                key="processing_start_idx_71"
            )
        with col2:
            end_idx = st.number_input(
                "Закончить на строке",
                start_idx, total_rows-1,
                min(start_idx + st.session_state.processing_settings.get('batch_size', 50) - 1, total_rows-1),
                key="processing_end_idx_72"
            )
        with col3:
            st.write("")
            st.write("")
            process_button = st.button(
                "🔄 Начать обработку", 
                type="primary", 
                use_container_width=True,
                key="processing_button_73"
            )
        
        batch_size = end_idx - start_idx + 1
        if batch_size > 0:
            st.success(f"✅ Будет обработано: {batch_size} строк")
        
        if process_button and batch_size > 0:
            st.session_state.processing_stats = {
                'total': batch_size,
                'success': 0,
                'failed': 0,
                'start_time': datetime.now(),
                'end_time': None
            }
            
            progress_bar = st.progress(0, text="Начало обработки...")
            status_text = st.empty()
            results_placeholder = st.empty()
            
            st.session_state.progress_bar = progress_bar
            st.session_state.status_text = status_text
            
            with st.spinner("Запуск обработки..."):
                results = generator.process_batch(
                    df_optimized,
                    start_idx,
                    end_idx,
                    st.session_state.column_mapping,
                    st.session_state.current_template,
                    {
                        **st.session_state.export_settings,
                        'timeout': st.session_state.processing_settings.get('timeout', 30),
                        'retry_count': st.session_state.processing_settings.get('retry_count', 3)
                    },
                    st.session_state.processing_settings,
                    text_offsets=st.session_state.text_offset_settings,
                    overlay_settings=st.session_state.image_overlay_settings if st.session_state.image_overlay_settings.get('enabled', False) else None,
                    font_settings=st.session_state.font_settings
                )
            
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
                    st.metric("Успешно", success_count, delta=f"{success_count/batch_size*100:.1f}%" if batch_size > 0 else "0%")
                with col2:
                    st.metric("С ошибками", failed_count, delta=f"-{failed_count}" if failed_count > 0 else None)
                with col3:
                    if st.session_state.processing_stats['start_time'] and st.session_state.processing_stats['end_time']:
                        duration = (
                            st.session_state.processing_stats['end_time'] -
                            st.session_state.processing_stats['start_time']
                        ).total_seconds()
                        st.metric("Время", f"{duration:.1f} сек", delta=f"{batch_size/duration:.1f}/сек" if duration > 0 else None)
                
                if failed_count > 0:
                    with st.expander("📋 Детали ошибок", expanded=False):
                        error_results = [r for r in results if r.get('status') == 'error']
                        error_df = pd.DataFrame(error_results)
                        if not error_df.empty:
                            st.dataframe(error_df[['row_index', 'message']], use_container_width=True)
                
                if success_count > 0:
                    with st.spinner("Создание архива..."):
                        zip_path, csv_path = generator.create_zip_archive(results)
                        
                        if zip_path and os.path.exists(zip_path):
                            col1, col2 = st.columns(2)
                            with col1:
                                with open(zip_path, 'rb') as f:
                                    st.download_button(
                                        label="📦 Скачать ZIP архив",
                                        data=f.read(),
                                        file_name=os.path.basename(zip_path),
                                        mime="application/zip",
                                        use_container_width=True,
                                        key="processing_zip_74"
                                    )
                            with col2:
                                with open(csv_path, 'rb') as f:
                                    st.download_button(
                                        label="📊 Скачать отчет (CSV)",
                                        data=f.read(),
                                        file_name=os.path.basename(csv_path),
                                        mime="text/csv",
                                        use_container_width=True,
                                        key="processing_csv_75"
                                    )
                            
                            zip_size = os.path.getsize(zip_path) / (1024 * 1024)
                            st.info(f"📦 Размер архива: {zip_size:.2f} MB, файлов: {success_count}")
                        else:
                            st.error("❌ Ошибка создания архива")
    
    @staticmethod
    def render_statistics_tab():
        """Вкладка статистики"""
        st.header("📊 Статистика и аналитика")
        
        if st.session_state.get('processed_count', 0) == 0:
            st.info("📈 Статистика появится после обработки данных")
            return
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Всего обработано", st.session_state.get('processed_count', 0))
        with col2:
            if st.session_state.get('batch_results'):
                success_count = sum(1 for r in st.session_state.batch_results if r.get('status') == 'success')
                total_count = len(st.session_state.batch_results)
                success_rate = (success_count / total_count * 100) if total_count > 0 else 0
                st.metric("Успешность", f"{success_rate:.1f}%")
        with col3:
            template_name = DynamicTemplateManager.load_template(st.session_state.current_template).get('name', 'Неизвестно')
            st.metric("Текущий шаблон", template_name[:15] + "..." if len(template_name) > 15 else template_name)
        with col4:
            st.metric("Формат экспорта", st.session_state.export_settings.get('format', 'PNG'))
        
        show_settings = st.checkbox("Показать текущие настройки", value=False, key="stats_show_settings_76")
        if show_settings:
            st.subheader("⚙️ Текущие настройки")
            
            if st.session_state.get('symmetrical_offsets', False):
                st.success("🔄 Режим симметричных смещений активен")
                st.write(f"**Общие смещения:** X: {st.session_state.text_offset_settings['top_left'].get('x_offset', 0)}%, Y: {st.session_state.text_offset_settings['top_left'].get('y_offset', 0)}%")
            else:
                offset_df = pd.DataFrame(st.session_state.text_offset_settings).T
                st.write("**Смещения текста:**")
                st.dataframe(offset_df, use_container_width=True)
            
            if st.session_state.image_overlay_settings.get('enabled', False):
                st.write(f"**Наложение изображений:** Включено")
                st.write(f"Позиция: {st.session_state.image_overlay_settings.get('position', 'center')}, Прозрачность: {st.session_state.image_overlay_settings.get('opacity', 100)}%")
            
            if st.session_state.font_settings.get('main_font'):
                available_fonts = FontManager.get_available_fonts()
                font_name = next((f["name"] for f in available_fonts if f["key"] == st.session_state.font_settings['main_font']), "Системный шрифт")
                st.write(f"**Шрифт:** {font_name}, Множитель размера: {st.session_state.font_settings.get('font_size_multiplier', 1.0)}")
        
        if st.session_state.get('batch_results'):
            st.subheader("📈 Детальная статистика последней обработки")
            results_df = pd.DataFrame(st.session_state.batch_results)
            
            if 'status' in results_df.columns:
                status_counts = results_df['status'].value_counts()
                col1, col2 = st.columns(2)
                with col1:
                    st.bar_chart(status_counts)
                with col2:
                    st.dataframe(status_counts, use_container_width=True)
            
            if (st.session_state.processing_stats.get('start_time') and
                st.session_state.processing_stats.get('end_time')):
                duration = (
                    st.session_state.processing_stats['end_time'] -
                    st.session_state.processing_stats['start_time']
                ).total_seconds()
                
                if duration > 0 and len(results_df) > 0:
                    speed = len(results_df) / duration
                    st.metric("Скорость обработки", f"{speed:.2f} изобр/сек")

# ============================
# ОСНОВНОЙ КОД ПРИЛОЖЕНИЯ
# ============================
import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageOps
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
from pathlib import Path
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
        'template_preview_size': 400
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

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
                "text": (255, 255, 255, 255),
                "shadow": (0, 0, 0, 180),
                "highlight": (255, 193, 7, 255),
                "price_main": (40, 167, 69, 255),
                "price_old": (108, 117, 125, 180)
            },
            "effects": {
                "shadow": True,
                "gradient": True,
                "rounded_corners": True
            }
        },
        
        "flash_sale_pro": {
            "name": "⚡ FLASH SALE PRO",
            "description": "Профессиональный шаблон для распродаж",
            "category": "sale",
            "layout": {
                "header_height": 20,
                "footer_height": 15,
                "corner_radius": 15,
                "shadow": True,
                "border": False
            },
            "backgrounds": {
                "header": "gradient_red",
                "footer": "gradient_dark",
                "main": "gradient_warm"
            },
            "text_positions": {
                "sale_badge": {"x": 0.5, "y": 0.5, "align": "center", "max_width": 0.9},
                "product_title": {"x": 0.5, "y": 0.15, "align": "center", "max_width": 0.9},
                "old_price": {"x": 0.3, "y": 0.3, "align": "right", "max_width": 0.4},
                "new_price": {"x": 0.7, "y": 0.3, "align": "left", "max_width": 0.4},
                "discount_badge": {"x": 0.5, "y": 0.25, "align": "center", "max_width": 0.4},
                "timer": {"x": 0.5, "y": 0.45, "align": "center", "max_width": 0.8},
                "stock_info": {"x": 0.5, "y": 0.55, "align": "center", "max_width": 0.8},
                "cta_button": {"x": 0.5, "y": 0.7, "align": "center", "max_width": 0.9},
                "footer_note": {"x": 0.5, "y": 0.5, "align": "center", "max_width": 0.9}
            },
            "font_sizes": {
                "sale_badge": 38,
                "product_title": 36,
                "old_price": 32,
                "new_price": 52,
                "discount_badge": 28,
                "timer": 38,
                "stock_info": 24,
                "cta_button": 32,
                "footer_note": 18
            },
            "colors": {
                "text": (255, 255, 255, 255),
                "shadow": (0, 0, 0, 200),
                "new_price": (40, 167, 69, 255),
                "discount_badge": (220, 53, 69, 255),
                "cta_button": (255, 193, 7, 255)
            },
            "effects": {
                "shadow": True,
                "glow": True,
                "animation": True
            }
        },
        
        "instagram_post": {
            "name": "📱 INSTAGRAM POST",
            "description": "Оптимизированный шаблон для Instagram",
            "category": "social",
            "layout": {
                "header_height": 0,
                "footer_height": 25,
                "corner_radius": 0,
                "shadow": False,
                "border": False
            },
            "backgrounds": {
                "header": "transparent",
                "footer": "solid_dark",
                "main": "white"
            },
            "text_positions": {
                "main_title": {"x": 0.05, "y": 0.05, "align": "left", "max_width": 0.9},
                "price": {"x": 0.95, "y": 0.05, "align": "right", "max_width": 0.4},
                "description": {"x": 0.05, "y": 0.15, "align": "left", "max_width": 0.9},
                "hashtags": {"x": 0.05, "y": 0.85, "align": "left", "max_width": 0.9},
                "cta": {"x": 0.5, "y": 0.5, "align": "center", "max_width": 0.8}
            },
            "font_sizes": {
                "main_title": 32,
                "price": 28,
                "description": 20,
                "hashtags": 18,
                "cta": 24
            },
            "colors": {
                "text": (33, 37, 41, 255),
                "shadow": (0, 0, 0, 150),
                "price": (40, 167, 69, 255),
                "hashtags": (173, 181, 189, 255)
            },
            "effects": {
                "shadow": False,
                "modern": True
            }
        },
        
        "luxury_gold": {
            "name": "💎 LUXURY GOLD",
            "description": "Роскошный шаблон для премиум товаров",
            "category": "premium",
            "layout": {
                "header_height": 12,
                "footer_height": 8,
                "corner_radius": 30,
                "shadow": True,
                "border": True
            },
            "backgrounds": {
                "header": "gradient_gold",
                "footer": "solid_dark",
                "main": "gradient_light"
            },
            "text_positions": {
                "brand_name": {"x": 0.5, "y": 0.5, "align": "center", "max_width": 0.7},
                "product_title": {"x": 0.5, "y": 0.15, "align": "center", "max_width": 0.8},
                "price": {"x": 0.5, "y": 0.3, "align": "center", "max_width": 0.8},
                "features": {"x": 0.5, "y": 0.45, "align": "center", "max_width": 0.8},
                "exclusive_badge": {"x": 0.5, "y": 0.7, "align": "center", "max_width": 0.6},
                "footer_text": {"x": 0.5, "y": 0.5, "align": "center", "max_width": 0.8}
            },
            "font_sizes": {
                "brand_name": 24,
                "product_title": 38,
                "price": 44,
                "features": 22,
                "exclusive_badge": 26,
                "footer_text": 18
            },
            "colors": {
                "text": (33, 37, 41, 255),
                "shadow": (0, 0, 0, 180),
                "price": (218, 165, 32, 255),
                "exclusive_badge": (192, 156, 26, 255)
            },
            "effects": {
                "shadow": True,
                "gold_border": True,
                "vignette": True
            }
        },
        
        "minimal_white": {
            "name": "🌀 MINIMAL WHITE",
            "description": "Чистый минималистичный дизайн",
            "category": "minimal",
            "layout": {
                "header_height": 0,
                "footer_height": 0,
                "corner_radius": 0,
                "shadow": False,
                "border": False
            },
            "backgrounds": {
                "header": "transparent",
                "footer": "transparent",
                "main": "white"
            },
            "text_positions": {
                "product_title": {"x": 0.5, "y": 0.1, "align": "center", "max_width": 0.8},
                "price": {"x": 0.5, "y": 0.25, "align": "center", "max_width": 0.8},
                "description": {"x": 0.5, "y": 0.4, "align": "center", "max_width": 0.7}
            },
            "font_sizes": {
                "product_title": 36,
                "price": 32,
                "description": 20
            },
            "colors": {
                "text": (33, 37, 41, 255),
                "shadow": (0, 0, 0, 0),
                "price": (108, 117, 125, 255)
            },
            "effects": {
                "shadow": False,
                "border": False
            }
        },
        
        "creative_abstract": {
            "name": "🎨 CREATIVE ABSTRACT",
            "description": "Креативный шаблон с абстрактным дизайном",
            "category": "creative",
            "layout": {
                "header_height": 18,
                "footer_height": 12,
                "corner_radius": 25,
                "shadow": True,
                "border": True
            },
            "backgrounds": {
                "header": "gradient_purple",
                "footer": "gradient_dark",
                "main": "light_gray"
            },
            "text_positions": {
                "creative_title": {"x": 0.5, "y": 0.5, "align": "center", "max_width": 0.8},
                "product_name": {"x": 0.5, "y": 0.15, "align": "center", "max_width": 0.8},
                "creative_price": {"x": 0.5, "y": 0.3, "align": "center", "max_width": 0.8},
                "tagline": {"x": 0.5, "y": 0.45, "align": "center", "max_width": 0.7},
                "features": {"x": 0.5, "y": 0.6, "align": "center", "max_width": 0.8},
                "footer_cta": {"x": 0.5, "y": 0.5, "align": "center", "max_width": 0.8}
            },
            "font_sizes": {
                "creative_title": 32,
                "product_name": 40,
                "creative_price": 48,
                "tagline": 24,
                "features": 20,
                "footer_cta": 22
            },
            "colors": {
                "text": (255, 255, 255, 255),
                "shadow": (0, 0, 0, 200),
                "creative_price": (147, 112, 219, 255),
                "tagline": (108, 117, 125, 255)
            },
            "effects": {
                "shadow": True,
                "abstract": True,
                "gradient_text": True
            }
        },
        
        "marketplace_card": {
            "name": "🏪 MARKETPLACE CARD",
            "description": "Карточка товара для маркетплейсов",
            "category": "ecommerce",
            "layout": {
                "header_height": 10,
                "footer_height": 20,
                "corner_radius": 10,
                "shadow": True,
                "border": True
            },
            "backgrounds": {
                "header": "solid_light",
                "footer": "solid_gray",
                "main": "white"
            },
            "text_positions": {
                "category": {"x": 0.05, "y": 0.5, "align": "left", "max_width": 0.4},
                "product_title": {"x": 0.05, "y": 0.1, "align": "left", "max_width": 0.9},
                "rating": {"x": 0.05, "y": 0.25, "align": "left", "max_width": 0.4},
                "price": {"x": 0.05, "y": 0.35, "align": "left", "max_width": 0.4},
                "delivery": {"x": 0.05, "y": 0.5, "align": "left", "max_width": 0.4},
                "button": {"x": 0.95, "y": 0.5, "align": "right", "max_width": 0.4}
            },
            "font_sizes": {
                "category": 14,
                "product_title": 24,
                "rating": 18,
                "price": 28,
                "delivery": 16,
                "button": 20
            },
            "colors": {
                "text": (33, 37, 41, 255),
                "shadow": (0, 0, 0, 180),
                "price": (40, 167, 69, 255),
                "button": (0, 123, 255, 255)
            },
            "effects": {
                "shadow": True,
                "button_effect": True
            }
        },
        
        "youtube_thumbnail": {
            "name": "📺 YOUTUBE THUMBNAIL",
            "description": "Шаблон для миниатюр YouTube",
            "category": "social",
            "layout": {
                "header_height": 35,
                "footer_height": 20,
                "corner_radius": 10,
                "shadow": True,
                "border": False
            },
            "backgrounds": {
                "header": "gradient_red",
                "footer": "solid_dark",
                "main": "white"
            },
            "text_positions": {
                "video_title": {"x": 0.5, "y": 0.5, "align": "center", "max_width": 0.9},
                "product_highlight": {"x": 0.5, "y": 0.2, "align": "center", "max_width": 0.9},
                "price_reveal": {"x": 0.5, "y": 0.5, "align": "center", "max_width": 0.8},
                "shocking_fact": {"x": 0.5, "y": 0.8, "align": "center", "max_width": 0.9},
                "cta_youtube": {"x": 0.5, "y": 0.5, "align": "center", "max_width": 0.8}
            },
            "font_sizes": {
                "video_title": 44,
                "product_highlight": 36,
                "price_reveal": 52,
                "shocking_fact": 28,
                "cta_youtube": 26
            },
            "colors": {
                "text": (255, 255, 255, 255),
                "shadow": (0, 0, 0, 200),
                "price_reveal": (220, 53, 69, 255),
                "shocking_fact": (255, 193, 7, 255)
            },
            "effects": {
                "shadow": True,
                "youtube_style": True,
                "attention_grabber": True
            }
        }
    }
    
    @staticmethod
    def ensure_templates_dir():
        """Создание директории для шаблонов если её нет"""
        try:
            os.makedirs(DynamicTemplateManager.TEMPLATES_DIR, exist_ok=True)
            
            for template_id, template_data in DynamicTemplateManager.BUILTIN_TEMPLATES.items():
                filepath = os.path.join(DynamicTemplateManager.TEMPLATES_DIR, f"{template_id}.json")
                if not os.path.exists(filepath):
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(template_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Директория шаблонов создана: {DynamicTemplateManager.TEMPLATES_DIR}")
        except Exception as e:
            logger.error(f"Ошибка создания директории шаблонов: {e}")
    
    @staticmethod
    def scan_template_files():
        """Сканирование директории с шаблонами"""
        DynamicTemplateManager.ensure_templates_dir()
        
        template_files = []
        try:
            if os.path.exists(DynamicTemplateManager.TEMPLATES_DIR):
                for file in os.listdir(DynamicTemplateManager.TEMPLATES_DIR):
                    if file.endswith('.json'):
                        template_id = os.path.splitext(file)[0]
                        filepath = os.path.join(DynamicTemplateManager.TEMPLATES_DIR, file)
                        
                        if os.path.isfile(filepath):
                            template_files.append({
                                'id': template_id,
                                'path': filepath,
                                'name': file
                            })
        except Exception as e:
            logger.error(f"Ошибка сканирования шаблонов: {e}")
        
        st.session_state.template_files = template_files
        return template_files
    
    @staticmethod
    def load_template(template_id: str) -> Dict:
        """Загрузка шаблона по ID"""
        if (st.session_state.get('loaded_templates') and 
            template_id in st.session_state.loaded_templates):
            return st.session_state.loaded_templates[template_id]
        
        filepath = os.path.join(DynamicTemplateManager.TEMPLATES_DIR, f"{template_id}.json")
        
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                
                if 'colors' in template_data:
                    for color_key, color_value in template_data['colors'].items():
                        if isinstance(color_value, list):
                            template_data['colors'][color_key] = tuple(color_value)
                
                if 'id' not in template_data:
                    template_data['id'] = template_id
                
                if 'loaded_templates' not in st.session_state:
                    st.session_state.loaded_templates = {}
                st.session_state.loaded_templates[template_id] = template_data
                
                return template_data
            except Exception as e:
                logger.error(f"Ошибка загрузки шаблона {template_id}: {e}")
        
        return DynamicTemplateManager.BUILTIN_TEMPLATES.get("modern_shop", {}).copy()
    
    @staticmethod
    def get_template_names() -> List[Tuple[str, str]]:
        """Получение списка всех доступных шаблонов"""
        template_files = DynamicTemplateManager.scan_template_files()
        template_names = []
        
        for template_id, template_data in DynamicTemplateManager.BUILTIN_TEMPLATES.items():
            display_name = template_data.get('name', template_id)
            template_names.append((template_id, display_name))
        
        for template_info in template_files:
            template_id = template_info['id']
            if template_id not in DynamicTemplateManager.BUILTIN_TEMPLATES:
                template_data = DynamicTemplateManager.load_template(template_id)
                display_name = template_data.get('name', template_id)
                template_names.append((template_id, display_name))
        
        if not template_names:
            template_names = [("modern_shop", "🛒 MODERN SHOP")]
        
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
    def save_template(template_id: str, template_data: Dict) -> bool:
        """Сохранение шаблона в файл"""
        try:
            filepath = os.path.join(DynamicTemplateManager.TEMPLATES_DIR, f"{template_id}.json")
            
            save_data = template_data.copy()
            
            if 'colors' in save_data:
                for color_key, color_value in save_data['colors'].items():
                    if isinstance(color_value, tuple):
                        save_data['colors'][color_key] = list(color_value)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2, default=str)
            
            if 'loaded_templates' not in st.session_state:
                st.session_state.loaded_templates = {}
            st.session_state.loaded_templates[template_id] = template_data
            
            logger.info(f"Шаблон {template_id} сохранен")
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения шаблона {template_id}: {e}")
            st.error(f"Ошибка сохранения шаблона: {e}")
            return False
    
    @staticmethod
    def validate_template(template_data: Dict) -> Tuple[bool, List[str], List[str]]:
        """Валидация структуры шаблона"""
        errors = []
        warnings = []
        
        required_fields = ['name']
        for field in required_fields:
            if field not in template_data:
                errors.append(f"Отсутствует обязательное поле: {field}")
        
        if 'text_positions' in template_data:
            text_positions = template_data['text_positions']
            if not isinstance(text_positions, dict):
                errors.append("text_positions должен быть словарем")
            else:
                for pos_key, pos_data in text_positions.items():
                    if not isinstance(pos_data, dict):
                        errors.append(f"Позиция '{pos_key}' должна быть словарем")
                    else:
                        required_pos_fields = ['x', 'y']
                        for field in required_pos_fields:
                            if field not in pos_data:
                                errors.append(f"Позиция '{pos_key}' не имеет поля '{field}'")
                            else:
                                value = pos_data[field]
                                try:
                                    float_value = float(value)
                                    if float_value < 0 or float_value > 1:
                                        warnings.append(f"Позиция '{pos_key}': {field} обычно должен быть между 0 и 1")
                                except (ValueError, TypeError):
                                    errors.append(f"Позиция '{pos_key}': {field} должен быть числом")
        
        return len(errors) == 0, errors, warnings

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
                
                if 'font_cache' not in st.session_state:
                    st.session_state.font_cache = {}
                if 'uploaded_fonts' not in st.session_state:
                    st.session_state.uploaded_fonts = []
                
                font_info = {
                    'name': font_name,
                    'path': tmp_path,
                    'key': font_key,
                    'size': 24,
                    'file_size': len(uploaded_file.getvalue())
                }
                
                st.session_state.font_cache[font_key] = font_info
                
                existing_fonts = [f['key'] for f in st.session_state.uploaded_fonts]
                if font_key not in existing_fonts:
                    st.session_state.uploaded_fonts.append(font_info)
                
                logger.info(f"Шрифт '{font_name}' загружен (ключ: {font_key})")
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
            font_paths = {
                "system_arial": [
                    "C:/Windows/Fonts/arial.ttf",
                    "C:/Windows/Fonts/Arial.ttf",
                    "/System/Library/Fonts/Supplemental/Arial.ttf",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
                ],
                "system_helvetica": [
                    "/System/Library/Fonts/Helvetica.ttc",
                    "/System/Library/Fonts/Helvetica Neue.ttc",
                    "C:/Windows/Fonts/arial.ttf"
                ],
                "system_times": [
                    "C:/Windows/Fonts/times.ttf",
                    "C:/Windows/Fonts/Times New Roman.ttf",
                    "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
                ]
            }
            
            if font_name in font_paths:
                for path in font_paths[font_name]:
                    if os.path.exists(path):
                        return ImageFont.truetype(path, int(size))
            
            try:
                return ImageFont.truetype("arial", int(size))
            except:
                return ImageFont.load_default()
                
        except Exception as e:
            logger.error(f"Ошибка загрузки системного шрифта {font_name}: {e}")
            try:
                return ImageFont.load_default()
            except:
                return ImageFont.load_default()

class ImageProcessor:
    """Класс для обработки изображений с поддержкой фонов"""
    
    @staticmethod
    def load_image_from_url(url: str, timeout: int = 30, retries: int = 3, use_cache: bool = True) -> Optional[Image.Image]:
        """Загрузка изображения по URL с повторными попытками"""
        if not url or not isinstance(url, str) or not url.strip():
            return None
        
        url = url.strip()
        
        if use_cache and st.session_state.get('image_cache'):
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
                    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Referer': 'https://www.google.com/'
                }
                
                response = requests.get(url, timeout=timeout, headers=headers, stream=True)
                response.raise_for_status()
                
                content_type = response.headers.get('content-type', '').lower()
                if 'image' not in content_type:
                    logger.warning(f"URL не возвращает изображение: {content_type}")
                    if attempt == retries:
                        return None
                    time.sleep(1)
                    continue
                
                img_data = BytesIO()
                for chunk in response.iter_content(chunk_size=8192):
                    img_data.write(chunk)
                
                img_data.seek(0)
                img = Image.open(img_data)
                
                if img.mode != 'RGBA':
                    if img.mode == 'P' and 'transparency' in img.info:
                        img = img.convert('RGBA')
                    elif img.mode == 'LA':
                        img = img.convert('RGBA')
                    else:
                        img = img.convert('RGBA')
                
                if use_cache:
                    if 'image_cache' not in st.session_state:
                        st.session_state.image_cache = {}
                    cache_key = hashlib.md5(url.encode()).hexdigest()
                    st.session_state.image_cache[cache_key] = img.copy()
                
                logger.info(f"Изображение загружено: {url} ({img.width}x{img.height})")
                return img
                
            except requests.exceptions.Timeout:
                logger.warning(f"Таймаут при загрузке {url}, попытка {attempt + 1}/{retries + 1}")
                if attempt == retries:
                    return None
                time.sleep(2)
            except requests.exceptions.ConnectionError:
                logger.warning(f"Ошибка соединения {url}, попытка {attempt + 1}/{retries + 1}")
                if attempt == retries:
                    return None
                time.sleep(2)
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
        
        header_height_percent = layout.get("header_height", 15)
        footer_height_percent = layout.get("footer_height", 10)
        
        header_height = int(height * header_height_percent / 100)
        footer_height = int(height * footer_height_percent / 100)
        main_height = height - header_height - footer_height
        
        canvas = Image.new('RGBA', (width, height), (255, 255, 255, 0))
        bg_library = BackgroundLibrary()
        
        header_bg_key = st.session_state.background_settings.get('header_background', 
                                                               backgrounds.get('header', 'gradient_blue'))
        footer_bg_key = st.session_state.background_settings.get('footer_background', 
                                                               backgrounds.get('footer', 'gradient_dark'))
        main_bg_key = st.session_state.background_settings.get('main_background', 
                                                             backgrounds.get('main', 'white'))
        
        header_bg_config = {}
        if header_bg_key in BackgroundLibrary.get_header_backgrounds():
            header_bg_config = BackgroundLibrary.get_header_backgrounds()[header_bg_key]
        else:
            header_bg_config = {"type": "solid", "color": (255, 255, 255)}
        
        footer_bg_config = {}
        if footer_bg_key in BackgroundLibrary.get_footer_backgrounds():
            footer_bg_config = BackgroundLibrary.get_footer_backgrounds()[footer_bg_key]
        else:
            footer_bg_config = {"type": "solid", "color": (33, 37, 41)}
        
        main_bg_config = {}
        if main_bg_key in BackgroundLibrary.get_main_backgrounds():
            main_bg_config = BackgroundLibrary.get_main_backgrounds()[main_bg_key]
        else:
            main_bg_config = {"type": "solid", "color": (255, 255, 255)}
        
        if header_height > 0:
            header_bg = bg_library.create_background(width, header_height, header_bg_config)
            canvas.paste(header_bg, (0, 0))
        
        if main_height > 0:
            main_bg = bg_library.create_background(width, main_height, main_bg_config)
            canvas.paste(main_bg, (0, header_height))
        
        if footer_height > 0:
            footer_bg = bg_library.create_background(width, footer_height, footer_bg_config)
            canvas.paste(footer_bg, (0, header_height + main_height))
        
        corner_radius = st.session_state.background_settings.get('corner_radius', 
                                                               layout.get('corner_radius', 0))
        if corner_radius > 0 and layout.get('rounded_corners', True):
            canvas = ImageProcessor.add_rounded_corners(canvas, corner_radius)
        
        if layout.get('shadow', False) and st.session_state.background_settings.get('shadow_enabled', True):
            canvas = ImageProcessor.add_shadow_effect(canvas)
        
        if layout.get('border', False) and st.session_state.background_settings.get('border_enabled', True):
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
        
        draw.pieslice([0, 0, radius * 2, radius * 2], 180, 270, fill=255)
        draw.pieslice([width - radius * 2, 0, width, radius * 2], 270, 360, fill=255)
        draw.pieslice([0, height - radius * 2, radius * 2, height], 90, 180, fill=255)
        draw.pieslice([width - radius * 2, height - radius * 2, width, height], 0, 90, fill=255)
        
        draw.rectangle([radius, 0, width - radius, height], fill=255)
        draw.rectangle([0, radius, width, height - radius], fill=255)
        
        result = Image.new('RGBA', img.size, (255, 255, 255, 0))
        result.paste(img, (0, 0), mask)
        
        return result
    
    @staticmethod
    def add_shadow_effect(img: Image.Image, shadow_size: int = 10, shadow_color: Tuple = (0, 0, 0, 100)) -> Image.Image:
        """Добавление эффекта тени"""
        width, height = img.size
        
        shadow = Image.new('RGBA', (width + shadow_size * 2, height + shadow_size * 2), (0, 0, 0, 0))
        shadow.paste(img, (shadow_size, shadow_size), img)
        
        for i in range(shadow_size):
            alpha = int(shadow_color[3] * (i + 1) / shadow_size)
            shadow_with_alpha = Image.new('RGBA', shadow.size, (0, 0, 0, 0))
            shadow_with_alpha.paste((shadow_color[0], shadow_color[1], shadow_color[2], alpha), 
                                   [i, i, width + shadow_size * 2 - i, height + shadow_size * 2 - i])
            shadow = Image.alpha_composite(shadow, shadow_with_alpha)
        
        return shadow
    
    @staticmethod
    def add_border(img: Image.Image, border_color: str, border_width: int = 2) -> Image.Image:
        """Добавление рамки"""
        width, height = img.size
        
        border_img = Image.new('RGBA', (width + border_width * 2, height + border_width * 2), 
                             (255, 255, 255, 0))
        
        if border_color.startswith('#'):
            try:
                border_rgb = tuple(int(border_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                border_rgba = border_rgb + (255,)
            except:
                border_rgba = (224, 224, 224, 255)
        else:
            border_rgba = (224, 224, 224, 255)
        
        draw = ImageDraw.Draw(border_img)
        draw.rectangle([0, 0, width + border_width * 2, height + border_width * 2], 
                      fill=border_rgba)
        
        border_img.paste(img, (border_width, border_width), img)
        
        return border_img
    
    @staticmethod
    def add_text_to_image(img: Image.Image, text_data: Dict, template_id: str = "modern_shop", 
                         text_offsets: Optional[Dict] = None, font_settings: Optional[Dict] = None) -> Image.Image:
        """Добавление текста на изображение по шаблону"""
        if img is None:
            return None
        
        try:
            template = DynamicTemplateManager.load_template(template_id)
            if not template:
                template = DynamicTemplateManager.BUILTIN_TEMPLATES["modern_shop"]
            
            draw = ImageDraw.Draw(img)
            
            if font_settings is None:
                font_settings = st.session_state.get('font_settings', {})
            
            if text_offsets is None:
                text_offsets = st.session_state.get('text_offset_settings', {})
            
            layout = template.get("layout", {})
            header_height_percent = layout.get("header_height", 15)
            footer_height_percent = layout.get("footer_height", 10)
            
            header_height = int(img.height * header_height_percent / 100)
            footer_height = int(img.height * footer_height_percent / 100)
            main_height = img.height - header_height - footer_height
            
            text_positions = template.get("text_positions", {})
            
            for position_key, position_data in text_positions.items():
                if position_key in text_data and text_data[position_key]:
                    text = str(text_data[position_key])
                    if not text.strip():
                        continue
                    
                    base_x = position_data.get("x", 0.5) * img.width
                    base_y = position_data.get("y", 0.5)
                    
                    section = position_data.get("section", "main")
                    if section == "header":
                        base_y = base_y * header_height
                    elif section == "footer":
                        base_y = header_height + main_height + base_y * footer_height
                    else:  # main
                        base_y = header_height + base_y * main_height
                    
                    if position_key in text_offsets:
                        offset_x = text_offsets[position_key].get('x_offset', 0)
                        offset_y = text_offsets[position_key].get('y_offset', 0)
                        
                        if abs(offset_x) <= 100:
                            base_x += offset_x * img.width / 100
                        else:
                            base_x += offset_x
                            
                        if abs(offset_y) <= 100:
                            base_y += offset_y * img.height / 100
                        else:
                            base_y += offset_y
                    
                    x = int(base_x)
                    y = int(base_y)
                    
                    font_sizes = template.get("font_sizes", {})
                    base_font_size = font_sizes.get(position_key, 24)
                    font_size_multiplier = font_settings.get('font_size_multiplier', 1.0)
                    font_size = int(base_font_size * font_size_multiplier)
                    
                    main_font_key = font_settings.get('main_font', 'system_arial')
                    bold_font_key = font_settings.get('bold_font', main_font_key)
                    
                    if position_key in ["product_title", "price_main", "sale_badge", "video_title"]:
                        font_key = bold_font_key
                    else:
                        font_key = main_font_key
                    
                    try:
                        if font_key.startswith('system_'):
                            font = FontManager.load_system_font(font_key, font_size)
                        else:
                            font = FontManager.get_font(font_key, font_size)
                    except:
                        font = FontManager.load_system_font('system_arial', font_size)
                    
                    color_key = position_key if position_key in template.get("colors", {}) else "text"
                    text_color = template.get("colors", {}).get(color_key, (255, 255, 255, 255))
                    
                    if template.get("effects", {}).get("shadow", True):
                        shadow_color = template.get("colors", {}).get("shadow", (0, 0, 0, 180))
                        shadow_offset = 2
                        anchor = "mm" if position_data.get("align") == "center" else None
                        
                        if anchor == "mm":
                            draw.text((x + shadow_offset, y + shadow_offset), text, 
                                     font=font, fill=shadow_color, anchor=anchor)
                        else:
                            draw.text((x + shadow_offset, y + shadow_offset), text, 
                                     font=font, fill=shadow_color,
                                     align=position_data.get("align", "left"))
                    
                    anchor = "mm" if position_data.get("align") == "center" else None
                    
                    if anchor == "mm":
                        draw.text((x, y), text, font=font, fill=text_color, anchor=anchor)
                    else:
                        draw.text((x, y), text, font=font, fill=text_color,
                                 align=position_data.get("align", "left"))
            
            return img
            
        except Exception as e:
            logger.error(f"Ошибка добавления текста к изображению: {e}")
            return img
    
    @staticmethod
    def add_image_overlay(background_img: Image.Image, overlay_img: Image.Image, 
                         overlay_settings: Dict) -> Image.Image:
        """Добавление изображения поверх основного"""
        if background_img is None or overlay_img is None:
            return background_img
        
        try:
            result_img = background_img.copy()
            
            max_width_px = int(background_img.width * overlay_settings.get('max_width', 30) / 100)
            max_height_px = int(background_img.height * overlay_settings.get('max_height', 30) / 100)
            
            scale = overlay_settings.get('scale', 100) / 100
            width_ratio = max_width_px / overlay_img.width
            height_ratio = max_height_px / overlay_img.height
            overlay_ratio = min(width_ratio, height_ratio) * scale
            
            new_width = int(overlay_img.width * overlay_ratio)
            new_height = int(overlay_img.height * overlay_ratio)
            
            if new_width > 0 and new_height > 0:
                overlay_resized = overlay_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                opacity = overlay_settings.get('opacity', 100)
                if opacity < 100 and overlay_resized.mode == 'RGBA':
                    overlay_resized = ImageProcessor.apply_opacity(overlay_resized, opacity)
                
                position = overlay_settings.get('position', 'center')
                
                if position == 'center':
                    x = (background_img.width - new_width) // 2
                    y = (background_img.height - new_height) // 2
                elif position == 'top_left':
                    x = 0
                    y = 0
                elif position == 'top_right':
                    x = background_img.width - new_width
                    y = 0
                elif position == 'bottom_left':
                    x = 0
                    y = background_img.height - new_height
                elif position == 'bottom_right':
                    x = background_img.width - new_width
                    y = background_img.height - new_height
                else:
                    x = (background_img.width - new_width) // 2
                    y = (background_img.height - new_height) // 2
                
                x += int(overlay_settings.get('x_offset', 0) * background_img.width / 100)
                y += int(overlay_settings.get('y_offset', 0) * background_img.height / 100)
                
                x = max(0, min(x, background_img.width - new_width))
                y = max(0, min(y, background_img.height - new_height))
                
                if overlay_resized.mode != 'RGBA':
                    overlay_resized = overlay_resized.convert('RGBA')
                
                result_img.paste(overlay_resized, (x, y), overlay_resized)
            
            return result_img
            
        except Exception as e:
            logger.error(f"Ошибка при наложении изображения: {e}")
            return background_img
    
    @staticmethod
    def apply_opacity(img: Image.Image, opacity: int) -> Image.Image:
        """Применение прозрачности к изображению"""
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        alpha = img.split()[3]
        alpha = alpha.point(lambda p: p * opacity / 100)
        
        img.putalpha(alpha)
        return img
    
    @staticmethod
    def resize_image(img: Image.Image, target_size: int = 1200) -> Image.Image:
        """Изменение размера изображения с сохранением пропорций"""
        if img is None:
            return None
        
        max_dimension = max(img.width, img.height)
        
        if max_dimension > target_size:
            ratio = target_size / max_dimension
            new_width = int(img.width * ratio)
            new_height = int(img.height * ratio)
            
            try:
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            except AttributeError:
                img = img.resize((new_width, new_height), Image.LANCZOS)
        
        return img
    
    @staticmethod
    def save_image(img: Image.Image, filepath: str, format: str = 'PNG', quality: int = 95) -> bool:
        """Сохранение изображения в файл"""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            format_upper = format.upper()
            save_kwargs = {'optimize': True}
            
            if format_upper == 'JPEG' or format_upper == 'JPG':
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                save_kwargs['quality'] = quality
                img.save(filepath, 'JPEG', **save_kwargs)
            elif format_upper == 'WEBP':
                save_kwargs['quality'] = quality
                img.save(filepath, 'WEBP', **save_kwargs)
            else:
                img.save(filepath, 'PNG', **save_kwargs)
            
            logger.info(f"Изображение сохранено: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения {filepath}: {e}")
            return False

# ============================
# УТИЛИТЫ ДЛЯ РАБОТЫ С EXCEL
# ============================
class ExcelProcessor:
    """Класс для обработки Excel файлов"""
    
    @staticmethod
    def read_excel_file(uploaded_file) -> Optional[pd.DataFrame]:
        """Чтение Excel файла с автоматическим определением формата"""
        try:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            if file_extension == 'xlsx':
                df = pd.read_excel(uploaded_file, engine='openpyxl')
            elif file_extension == 'xls':
                try:
                    df = pd.read_excel(uploaded_file, engine='xlrd')
                except:
                    df = pd.read_excel(uploaded_file, engine='openpyxl')
            else:
                st.error(f"❌ Неподдерживаемый формат файла: {file_extension}")
                return None
            
            df = df.replace({np.nan: None, '': None})
            
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).replace('nan', None).replace('None', None)
            
            logger.info(f"Загружен файл: {uploaded_file.name}, строк: {len(df)}, колонок: {len(df.columns)}")
            return df
            
        except Exception as e:
            st.error(f"❌ Ошибка чтения файла: {str(e)}")
            logger.error(f"Ошибка чтения Excel: {e}")
            return None
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame, required_columns: Optional[List] = None) -> Tuple[bool, str]:
        """Валидация структуры DataFrame"""
        if df is None:
            return False, "DataFrame не загружен"
        if df.empty:
            return False, "DataFrame пустой"
        
        if required_columns:
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return False, f"Отсутствуют колонки: {missing_columns}"
        
        return True, "DataFrame валиден"
    
    @staticmethod
    def get_column_suggestions(df: pd.DataFrame) -> Dict:
        """Автоматическое предложение колонок для маппинга"""
        suggestions = {
            'top_left': None,
            'top_right': None,
            'bottom_left': None,
            'bottom_right': None,
            'image_url': None,
            'overlay_image_url': None,
            'filename': None
        }
        
        if df is None or df.empty:
            return suggestions
        
        column_names = [str(col).lower() for col in df.columns]
        
        keyword_mapping = {
            'top_left': ['название', 'name', 'товар', 'product', 'title', 'имя', 'наименование'],
            'top_right': ['цена', 'price', 'стоимость', 'руб', 'р.', 'сумма', 'стоимост'],
            'bottom_left': ['характеристики', 'spec', 'описание', 'description', 'детали', 'features', 'param'],
            'bottom_right': ['скидка', 'discount', 'акция', 'sale', 'распродажа', 'экономия', 'bonus'],
            'image_url': ['url', 'ссылка', 'image', 'картинка', 'фото', 'photo', 'основное', 'img', 'picture'],
            'overlay_image_url': ['лого', 'logo', 'бренд', 'brand', 'дополнительно', 'additional', 'наложение', 'overlay', 'стикер', 'sticker', 'watermark'],
            'filename': ['артикул', 'sku', 'код', 'id', 'номер', 'article']
        }
        
        for position, keywords in keyword_mapping.items():
            for col_name, col_name_lower in zip(df.columns, column_names):
                for keyword in keywords:
                    if keyword in col_name_lower:
                        suggestions[position] = col_name
                        break
                if suggestions[position]:
                    break
        
        if not suggestions['filename'] and len(df.columns) > 0:
            suggestions['filename'] = df.columns[0]
        
        return suggestions
    
    @staticmethod
    def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Оптимизация DataFrame для ускорения обработки"""
        if df is None or df.empty:
            return df
        
        df_optimized = df.copy()
        
        if 'image_url' in st.session_state.column_mapping:
            image_col = st.session_state.column_mapping['image_url']
            if image_col in df_optimized.columns:
                initial_count = len(df_optimized)
                df_optimized = df_optimized[df_optimized[image_col].notna() & 
                                           (df_optimized[image_col] != '') &
                                           (df_optimized[image_col] != 'None')].copy()
                removed_count = initial_count - len(df_optimized)
                if removed_count > 0:
                    logger.info(f"Удалено {removed_count} строк без URL изображений")
        
        return df_optimized

# ============================
# ОСНОВНОЙ ПРОЦЕССОР
# ============================
class InfographicGenerator:
    """Основной класс для генерации инфографики"""
    
    def __init__(self):
        self.image_processor = ImageProcessor()
        self.excel_processor = ExcelProcessor()
    
    def process_single_row(self, row: pd.Series, column_mapping: Dict, template_id: str, 
                          export_settings: Dict, row_index: int = 0, 
                          text_offsets: Optional[Dict] = None, 
                          overlay_settings: Optional[Dict] = None, 
                          font_settings: Optional[Dict] = None) -> Dict:
        """Обработка одной строки данных"""
        try:
            text_data = {}
            for position in ['top_left', 'top_right', 'bottom_left', 'bottom_right']:
                if position in column_mapping and column_mapping[position] in row:
                    text_data[position] = str(row[column_mapping[position]] or '')
                else:
                    text_data[position] = ''
            
            image_url = ''
            if 'image_url' in column_mapping and column_mapping['image_url'] in row:
                image_url = str(row[column_mapping['image_url']] or '')
            
            if not image_url or image_url.lower() in ['none', 'nan', '']:
                return {
                    'row_index': row_index,
                    'status': 'error',
                    'message': 'Отсутствует URL основного изображения',
                    'filename': f"row_{row_index:04d}"
                }
            
            overlay_image_url = None
            if ('overlay_image_url' in column_mapping and 
                column_mapping['overlay_image_url'] in row):
                overlay_image_url = str(row[column_mapping['overlay_image_url']] or '')
                if overlay_image_url.lower() in ['none', 'nan', '']:
                    overlay_image_url = None
            
            filename_source = ''
            if 'filename' in column_mapping and column_mapping['filename'] in row:
                filename_source = str(row[column_mapping['filename']] or '')
            
            filename = self.generate_filename(filename_source, row_index)
            
            export_settings_local = export_settings.copy()
            if 'prefix' in export_settings_local and export_settings_local['prefix']:
                filename = f"{export_settings_local['prefix']}_{filename}"
            if 'suffix' in export_settings_local and export_settings_local['suffix']:
                filename = f"{filename}_{export_settings_local['suffix']}"
            
            main_img = self.image_processor.load_image_from_url(
                image_url,
                timeout=export_settings_local.get('timeout', 30),
                retries=export_settings_local.get('retry_count', 3)
            )
            
            if main_img is None:
                return {
                    'row_index': row_index,
                    'status': 'error',
                    'message': 'Не удалось загрузить основное изображение',
                    'filename': filename
                }
            
            if export_settings_local.get('resize', True):
                target_size = export_settings_local.get('target_size', 1200)
                main_img = self.image_processor.resize_image(main_img, target_size)
            
            template_canvas = self.image_processor.create_template_canvas(
                main_img.width, main_img.height, template_id
            )
            
            final_img = template_canvas.copy()
            
            main_img_position = (0, 
                               int(template_canvas.height * st.session_state.background_settings.get('header_height', 15) / 100))
            final_img.paste(main_img, main_img_position)
            
            processed_img = self.image_processor.add_text_to_image(
                final_img,
                text_data,
                template_id,
                text_offsets=text_offsets,
                font_settings=font_settings
            )
            
            if (overlay_settings and overlay_settings.get('enabled', False) and 
                overlay_image_url and overlay_image_url.startswith(('http://', 'https://'))):
                
                overlay_img = self.image_processor.load_image_from_url(overlay_image_url, timeout=15, retries=2)
                if overlay_img:
                    processed_img = self.image_processor.add_image_overlay(
                        processed_img,
                        overlay_img,
                        overlay_settings
                    )
            
            output_dir = st.session_state.get('output_dir', 'output_infographics')
            format_ext = export_settings_local.get('format', 'PNG').lower()
            filepath = os.path.join(output_dir, f"{filename}.{format_ext}")
            
            success = self.image_processor.save_image(
                processed_img,
                filepath,
                format=export_settings_local.get('format', 'PNG'),
                quality=export_settings_local.get('quality', 95)
            )
            
            if success:
                return {
                    'row_index': row_index,
                    'status': 'success',
                    'filename': filename,
                    'filepath': filepath,
                    'image_url': image_url,
                    'overlay_image_url': overlay_image_url
                }
            else:
                return {
                    'row_index': row_index,
                    'status': 'error',
                    'message': 'Ошибка сохранения файла',
                    'filename': filename
                }
                
        except Exception as e:
            logger.error(f"Ошибка обработки строки {row_index}: {e}")
            return {
                'row_index': row_index,
                'status': 'error',
                'message': str(e)[:200],
                'filename': f"row_{row_index:04d}"
            }
    
    def generate_filename(self, source: str, index: int) -> str:
        """Генерация имени файла из исходной строки"""
        if not source or str(source).lower() in ['none', 'nan', '']:
            return f"item_{index:06d}"
        
        filename = re.sub(r'[<>:"/\\|?*]', '', str(source))
        filename = re.sub(r'\s+', '_', filename.strip())
        filename = filename[:100]
        
        if not filename:
            filename = f"item_{index:06d}"
        
        return filename
    
    def process_batch(self, df: pd.DataFrame, start_idx: int, end_idx: int, 
                     column_mapping: Dict, template_id: str, export_settings: Dict,
                     processing_settings: Dict, text_offsets: Optional[Dict] = None,
                     overlay_settings: Optional[Dict] = None, 
                     font_settings: Optional[Dict] = None) -> List[Dict]:
        """Пакетная обработка данных"""
        results = []
        total_rows = min(end_idx, len(df) - 1) - start_idx + 1
        
        if total_rows <= 0:
            return results
        
        output_dir = st.session_state.get('output_dir', 'output_infographics')
        os.makedirs(output_dir, exist_ok=True)
        
        max_workers = min(processing_settings.get('max_workers', 4), total_rows, 8)
        max_workers = max(1, max_workers)
        
        logger.info(f"Начало обработки {total_rows} строк, потоков: {max_workers}")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            
            for idx in range(start_idx, min(end_idx + 1, len(df))):
                row = df.iloc[idx]
                future = executor.submit(
                    self.process_single_row,
                    row,
                    column_mapping,
                    template_id,
                    export_settings,
                    idx,
                    text_offsets,
                    overlay_settings,
                    font_settings
                )
                futures[future] = idx
            
            completed = 0
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=processing_settings.get('timeout', 30) * 2)
                    results.append(result)
                    completed += 1
                    
                    progress = completed / total_rows
                    if 'progress_bar' in st.session_state:
                        st.session_state.progress_bar.progress(progress)
                    
                    if 'status_text' in st.session_state:
                        success_count = sum(1 for r in results if r.get('status') == 'success')
                        st.session_state.status_text.text(
                            f"Обработано: {completed}/{total_rows} | "
                            f"Успешно: {success_count} | "
                            f"Ошибок: {completed - success_count}"
                        )
                        
                except Exception as e:
                    idx = futures.get(future, completed)
                    logger.error(f"Ошибка в потоке обработки строки {idx}: {e}")
                    results.append({
                        'row_index': idx,
                        'status': 'error',
                        'message': f'Ошибка потока: {str(e)[:100]}',
                        'filename': f"row_{idx:04d}"
                    })
                    completed += 1
        
        logger.info(f"Обработка завершена. Успешно: {sum(1 for r in results if r.get('status') == 'success')}/{total_rows}")
        return results
    
    def create_zip_archive(self, results: List[Dict], batch_name: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """Создание ZIP архива с результатами"""
        if not batch_name:
            batch_name = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        zip_filename = f"infographics_{batch_name}.zip"
        output_dir = st.session_state.get('output_dir', 'output_infographics')
        zip_path = os.path.join(output_dir, zip_filename)
        
        try:
            results_df = pd.DataFrame(results)
            csv_path = os.path.join(output_dir, f"results_{batch_name}.csv")
            results_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for result in results:
                    if result.get('status') == 'success' and 'filepath' in result:
                        filepath = result['filepath']
                        if os.path.exists(filepath):
                            arcname = os.path.basename(filepath)
                            zipf.write(filepath, arcname)
                
                zipf.write(csv_path, os.path.basename(csv_path))
            
            logger.info(f"ZIP архив создан: {zip_path} ({os.path.getsize(zip_path) / 1024:.1f} KB)")
            return zip_path, csv_path
            
        except Exception as e:
            logger.error(f"Ошибка создания ZIP архива: {e}")
            return None, None

# ============================
# ИНТЕРФЕЙС ПОЛЬЗОВАТЕЛЯ
# ============================
class UIComponents:
    """Класс для компонентов пользовательского интерфейса"""
    
    @staticmethod
    def render_sidebar():
        """Отрисовка боковой панели"""
        with st.sidebar:
            st.title("⚙️ Настройки")
            
            st.subheader("📁 Загрузка данных")
            uploaded_file = st.file_uploader(
                "Выберите Excel файл",
                type=['xlsx', 'xls'],
                help="Файл должен содержать данные о товарах",
                key="sidebar_file_uploader_1"
            )
            
            if uploaded_file:
                if (st.session_state.get('uploaded_file_name') != uploaded_file.name or
                    st.session_state.get('df') is None):
                    
                    with st.spinner("Загрузка файла..."):
                        df = ExcelProcessor.read_excel_file(uploaded_file)
                        if df is not None:
                            st.session_state.df = df
                            st.session_state.uploaded_file_name = uploaded_file.name
                            
                            suggestions = ExcelProcessor.get_column_suggestions(df)
                            st.session_state.column_mapping = suggestions
                            
                            st.success(f"✅ Загружено {len(df)} строк, {len(df.columns)} колонок")
            
            with st.expander("👁️ Предпросмотр данных", expanded=False):
                if st.session_state.get('df') is not None:
                    preview_rows = st.slider(
                        "Строк для предпросмотра", 
                        5, 50, 10,
                        key="sidebar_preview_rows_2"
                    )
                    st.dataframe(st.session_state.df.head(preview_rows), use_container_width=True)
            
            st.subheader("🎨 Выбор шаблона")
            
            template_names = DynamicTemplateManager.get_template_names()
            
            if not template_names:
                st.warning("Не найдено шаблонов. Будет создан стандартный шаблон.")
                template_names = [("modern_shop", "🛒 MODERN SHOP")]
            
            display_options = []
            template_map = {}
            
            for template_id, display_name in template_names:
                display_text = f"{display_name}"
                display_options.append(display_text)
                template_map[display_text] = template_id
            
            current_template = st.session_state.get('current_template', 'modern_shop')
            current_display = None
            
            for display_text, template_id in template_map.items():
                if template_id == current_template:
                    current_display = display_text
                    break
            
            if not current_display and display_options:
                current_display = display_options[0]
                current_template = template_map[current_display]
            
            selected_display = st.selectbox(
                "Шаблон инфографики",
                options=display_options,
                index=display_options.index(current_display) if current_display in display_options else 0,
                key="sidebar_template_select_3"
            )
            
            selected_template = template_map.get(selected_display, 'modern_shop')
            
            if selected_template != st.session_state.current_template:
                st.session_state.current_template = selected_template
                st.rerun()
            
            template_data = DynamicTemplateManager.load_template(selected_template)
            if template_data:
                st.caption(f"**Название:** {template_data.get('name', 'Без названия')}")
                if template_data.get('description'):
                    st.caption(f"**Описание:** {template_data.get('description')}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Обновить", key="sidebar_refresh_4", use_container_width=True):
                    DynamicTemplateManager.scan_template_files()
                    st.rerun()
            
            with col2:
                if st.button("📝 Создать", key="sidebar_create_5", use_container_width=True):
                    st.session_state.editing_template = True
                    st.session_state.editing_template_id = None
                    st.session_state.editing_template_data = {}
                    st.rerun()
            
            st.subheader("🎨 Настройки фонов")
            
            header_bgs = BackgroundLibrary.get_header_backgrounds()
            header_options = {bg['name']: key for key, bg in header_bgs.items()}
            selected_header_name = st.selectbox(
                "Фон шапки",
                options=list(header_options.keys()),
                index=list(header_options.values()).index(
                    st.session_state.background_settings.get('header_background', 'gradient_blue')
                ) if st.session_state.background_settings.get('header_background') in header_options.values() else 0,
                key="sidebar_header_bg_6"
            )
            st.session_state.background_settings['header_background'] = header_options[selected_header_name]
            
            main_bgs = BackgroundLibrary.get_main_backgrounds()
            main_options = {bg['name']: key for key, bg in main_bgs.items()}
            selected_main_name = st.selectbox(
                "Фон основного",
                options=list(main_options.keys()),
                index=list(main_options.values()).index(
                    st.session_state.background_settings.get('main_background', 'white')
                ) if st.session_state.background_settings.get('main_background') in main_options.values() else 0,
                key="sidebar_main_bg_7"
            )
            st.session_state.background_settings['main_background'] = main_options[selected_main_name]
            
            footer_bgs = BackgroundLibrary.get_footer_backgrounds()
            footer_options = {bg['name']: key for key, bg in footer_bgs.items()}
            selected_footer_name = st.selectbox(
                "Фон футера",
                options=list(footer_options.keys()),
                index=list(footer_options.values()).index(
                    st.session_state.background_settings.get('footer_background', 'gradient_dark')
                ) if st.session_state.background_settings.get('footer_background') in footer_options.values() else 0,
                key="sidebar_footer_bg_8"
            )
            st.session_state.background_settings['footer_background'] = footer_options[selected_footer_name]
            
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.background_settings['header_height'] = st.slider(
                    "Высота шапки (%)",
                    0, 40,
                    st.session_state.background_settings.get('header_height', 15),
                    key="sidebar_header_height_9"
                )
            
            with col2:
                st.session_state.background_settings['footer_height'] = st.slider(
                    "Высота футера (%)",
                    0, 40,
                    st.session_state.background_settings.get('footer_height', 10),
                    key="sidebar_footer_height_10"
                )
            
            st.session_state.background_settings['corner_radius'] = st.slider(
                "Скругление углов",
                0, 50,
                st.session_state.background_settings.get('corner_radius', 20),
                key="sidebar_corner_radius_11"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.background_settings['shadow_enabled'] = st.checkbox(
                    "Тень",
                    value=st.session_state.background_settings.get('shadow_enabled', True),
                    key="sidebar_shadow_12"
                )
            
            with col2:
                st.session_state.background_settings['border_enabled'] = st.checkbox(
                    "Рамка",
                    value=st.session_state.background_settings.get('border_enabled', True),
                    key="sidebar_border_13"
                )
            
            st.subheader("💾 Настройки экспорта")
            col1, col2 = st.columns(2)
            with col1:
                export_format = st.selectbox(
                    "Формат",
                    ["PNG", "JPEG", "WebP"],
                    index=["PNG", "JPEG", "WebP"].index(
                        st.session_state.export_settings.get('format', 'PNG')
                    ),
                    key="sidebar_export_format_14"
                )
                st.session_state.export_settings['format'] = export_format
            
            with col2:
                quality = st.slider(
                    "Качество",
                    50, 100,
                    st.session_state.export_settings.get('quality', 95),
                    key="sidebar_export_quality_15"
                )
                st.session_state.export_settings['quality'] = quality
            
            resize_checkbox = st.checkbox(
                "Изменять размер",
                st.session_state.export_settings.get('resize', True),
                key="sidebar_resize_checkbox_16"
            )
            st.session_state.export_settings['resize'] = resize_checkbox
            
            if st.session_state.export_settings['resize']:
                target_size = st.select_slider(
                    "Целевой размер",
                    options=[800, 1200, 1600, 2000],
                    value=st.session_state.export_settings.get('target_size', 1200),
                    key="sidebar_target_size_17"
                )
                st.session_state.export_settings['target_size'] = target_size
            
            st.subheader("⚡ Настройки обработки")
            col1, col2 = st.columns(2)
            with col1:
                batch_size = st.select_slider(
                    "Размер партии",
                    options=[10, 25, 50, 100, 200],
                    value=st.session_state.processing_settings.get('batch_size', 50),
                    key="sidebar_batch_size_18"
                )
                st.session_state.processing_settings['batch_size'] = batch_size
            
            with col2:
                max_workers = st.select_slider(
                    "Потоки",
                    options=[1, 2, 4, 6, 8],
                    value=st.session_state.processing_settings.get('max_workers', 4),
                    key="sidebar_max_workers_19"
                )
                st.session_state.processing_settings['max_workers'] = max_workers
            
            timeout_input = st.select_slider(
                "Таймаут (сек)",
                options=[10, 15, 30, 45, 60],
                value=st.session_state.processing_settings.get('timeout', 30),
                key="sidebar_timeout_20"
            )
            st.session_state.processing_settings['timeout'] = timeout_input
            
            retry_count = st.select_slider(
                "Повторные попытки",
                options=[0, 1, 2, 3, 5],
                value=st.session_state.processing_settings.get('retry_count', 3),
                key="sidebar_retry_count_21"
            )
            st.session_state.processing_settings['retry_count'] = retry_count
            
            st.divider()
            st.caption(f"Обработано: {st.session_state.get('processed_count', 0)} изображений")
            st.caption(f"Шаблонов: {len(template_names)}")
            st.caption(f"Версия: 7.0 PRO")
    
    @staticmethod
    def render_background_settings():
        """Настройки фонов"""
        st.subheader("🎨 Настройки фонов")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 🎩 Шапка")
            header_bgs = BackgroundLibrary.get_header_backgrounds()
            
            header_preview = st.selectbox(
                "Фон шапки",
                options=[bg['name'] for bg in header_bgs.values()],
                index=list(header_bgs.keys()).index(
                    st.session_state.background_settings.get('header_background', 'gradient_blue')
                ) if st.session_state.background_settings.get('header_background') in header_bgs else 0,
                key="bg_header_select_22"
            )
            
            for key, bg in header_bgs.items():
                if bg['name'] == header_preview:
                    st.session_state.background_settings['header_background'] = key
                    break
            
            st.session_state.background_settings['header_height'] = st.slider(
                "Высота шапки (%)",
                0, 40,
                st.session_state.background_settings.get('header_height', 15),
                key="bg_header_height_23"
            )
            
            header_bg_config = header_bgs.get(st.session_state.background_settings['header_background'], {})
            if header_bg_config.get('type') == 'gradient':
                colors = header_bg_config.get('colors', [(30, 144, 255), (0, 102, 204)])
                color1 = f"rgb{colors[0]}" if len(colors) > 0 else "rgb(30, 144, 255)"
                color2 = f"rgb{colors[1]}" if len(colors) > 1 else "rgb(0, 102, 204)"
                st.markdown(f'<div style="height: 20px; background: linear-gradient(to right, {color1}, {color2}); border-radius: 5px; margin: 5px 0;"></div>', 
                           unsafe_allow_html=True)
        
        with col2:
            st.markdown("### 🖼️ Основное")
            main_bgs = BackgroundLibrary.get_main_backgrounds()
            
            main_preview = st.selectbox(
                "Фон основного",
                options=[bg['name'] for bg in main_bgs.values()],
                index=list(main_bgs.keys()).index(
                    st.session_state.background_settings.get('main_background', 'white')
                ) if st.session_state.background_settings.get('main_background') in main_bgs else 0,
                key="bg_main_select_24"
            )
            
            for key, bg in main_bgs.items():
                if bg['name'] == main_preview:
                    st.session_state.background_settings['main_background'] = key
                    break
            
            main_bg_config = main_bgs.get(st.session_state.background_settings['main_background'], {})
            if main_bg_config.get('type') == 'gradient':
                colors = main_bg_config.get('colors', [(250, 250, 250), (240, 240, 240)])
                color1 = f"rgb{colors[0]}" if len(colors) > 0 else "rgb(250, 250, 250)"
                color2 = f"rgb{colors[1]}" if len(colors) > 1 else "rgb(240, 240, 240)"
                st.markdown(f'<div style="height: 20px; background: linear-gradient(to bottom, {color1}, {color2}); border-radius: 5px; margin: 5px 0;"></div>', 
                           unsafe_allow_html=True)
            elif main_bg_config.get('type') == 'solid':
                color = main_bg_config.get('color', (255, 255, 255))
                st.markdown(f'<div style="height: 20px; background: rgb{color}; border-radius: 5px; margin: 5px 0;"></div>', 
                           unsafe_allow_html=True)
        
        with col3:
            st.markdown("### 👣 Футер")
            footer_bgs = BackgroundLibrary.get_footer_backgrounds()
            
            footer_preview = st.selectbox(
                "Фон футера",
                options=[bg['name'] for bg in footer_bgs.values()],
                index=list(footer_bgs.keys()).index(
                    st.session_state.background_settings.get('footer_background', 'gradient_dark')
                ) if st.session_state.background_settings.get('footer_background') in footer_bgs else 0,
                key="bg_footer_select_25"
            )
            
            for key, bg in footer_bgs.items():
                if bg['name'] == footer_preview:
                    st.session_state.background_settings['footer_background'] = key
                    break
            
            st.session_state.background_settings['footer_height'] = st.slider(
                "Высота футера (%)",
                0, 40,
                st.session_state.background_settings.get('footer_height', 10),
                key="bg_footer_height_26"
            )
            
            footer_bg_config = footer_bgs.get(st.session_state.background_settings['footer_background'], {})
            if footer_bg_config.get('type') == 'gradient':
                colors = footer_bg_config.get('colors', [(33, 37, 41), (52, 58, 64)])
                color1 = f"rgb{colors[0]}" if len(colors) > 0 else "rgb(33, 37, 41)"
                color2 = f"rgb{colors[1]}" if len(colors) > 1 else "rgb(52, 58, 64)"
                st.markdown(f'<div style="height: 20px; background: linear-gradient(to right, {color1}, {color2}); border-radius: 5px; margin: 5px 0;"></div>', 
                           unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("🎛️ Дополнительные настройки")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.session_state.background_settings['corner_radius'] = st.slider(
                "Скругление углов",
                0, 50,
                st.session_state.background_settings.get('corner_radius', 20),
                key="bg_corner_radius_27"
            )
        
        with col2:
            st.session_state.background_settings['shadow_enabled'] = st.checkbox(
                "Эффект тени",
                value=st.session_state.background_settings.get('shadow_enabled', True),
                key="bg_shadow_28"
            )
        
        with col3:
            st.session_state.background_settings['border_enabled'] = st.checkbox(
                "Рамка",
                value=st.session_state.background_settings.get('border_enabled', True),
                key="bg_border_29"
            )
        
        if st.session_state.background_settings['border_enabled']:
            col1, col2 = st.columns(2)
            with col1:
                border_color = st.color_picker(
                    "Цвет рамки",
                    value=st.session_state.background_settings.get('border_color', '#e0e0e0'),
                    key="bg_border_color_30"
                )
                st.session_state.background_settings['border_color'] = border_color
            
            with col2:
                st.session_state.background_settings['border_width'] = st.slider(
                    "Толщина рамки",
                    1, 10,
                    st.session_state.background_settings.get('border_width', 2),
                    key="bg_border_width_31"
                )
        
        st.info("💡 **Совет:** Используйте контрастные цвета для шапки и футера для лучшего визуального восприятия.")
    
    @staticmethod
    def render_template_preview():
        """Предпросмотр шаблонов с фонами"""
        st.subheader("👁️ Предпросмотр шаблонов")
        
        categories = DynamicTemplateManager.get_template_categories()
        selected_category = st.selectbox(
            "Категория шаблонов",
            options=list(categories.values()),
            index=list(categories.values()).index(
                categories.get(st.session_state.current_category, 'Все шаблоны')
            ),
            key="template_category_select_32"
        )
        
        for key, value in categories.items():
            if value == selected_category:
                st.session_state.current_category = key
                break
        
        template_names = DynamicTemplateManager.get_templates_by_category(st.session_state.current_category)
        
        if not template_names:
            st.info("📝 Шаблоны не найдены в выбранной категории.")
            return
        
        cols = st.columns(3)
        
        for idx, (template_id, display_name) in enumerate(template_names[:6]):
            with cols[idx % 3]:
                template_data = DynamicTemplateManager.load_template(template_id)
                
                with st.container():
                    st.markdown(f"### {display_name}")
                    st.caption(template_data.get('description', 'Без описания'))
                    
                    preview_size = st.session_state.get('template_preview_size', 400)
                    preview_width = preview_size
                    preview_height = int(preview_size * 0.75)
                    
                    try:
                        preview_canvas = ImageProcessor.create_template_canvas(
                            preview_width, preview_height, template_id
                        )
                        
                        draw = ImageDraw.Draw(preview_canvas)
                        
                        layout = template_data.get("layout", {})
                        header_height = int(preview_height * layout.get("header_height", 15) / 100)
                        footer_height = int(preview_height * layout.get("footer_height", 10) / 100)
                        main_height = preview_height - header_height - footer_height
                        
                        text_positions = template_data.get("text_positions", {})
                        
                        for pos_key, pos_data in text_positions.items():
                            x = pos_data.get("x", 0.5) * preview_width
                            y = pos_data.get("y", 0.5)
                            
                            section = pos_data.get("section", "main")
                            if section == "header":
                                y = y * header_height
                            elif section == "footer":
                                y = header_height + main_height + y * footer_height
                            else:
                                y = header_height + y * main_height
                            
                            draw.ellipse([x-3, y-3, x+3, y+3], fill='red')
                        
                        st.image(preview_canvas, use_container_width=True)
                        
                        if st.button(f"Выбрать {display_name}", 
                                   key=f"select_template_{template_id}_{idx}",
                                   use_container_width=True):
                            st.session_state.current_template = template_id
                            st.success(f"Выбран шаблон: {display_name}")
                            st.rerun()
                    
                    except Exception as e:
                        st.error(f"Ошибка создания превью: {e}")
        
        if len(template_names) > 6:
            st.info(f"📋 И еще {len(template_names) - 6} шаблонов в этой категории...")
    
    @staticmethod
    def render_column_mapping():
        """Настройка маппинга колонок"""
        if st.session_state.get('df') is not None:
            st.subheader("📊 Настройка маппинга колонок")
            st.info("Выберите, какие колонки из файла соответствуют элементам инфографики")
            
            available_columns = st.session_state.df.columns.tolist()
            
            if not available_columns:
                st.error("В файле нет колонок!")
                return
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.session_state.column_mapping['top_left'] = st.selectbox(
                    "Верхний левый угол (Название)",
                    available_columns,
                    index=available_columns.index(
                        st.session_state.column_mapping.get('top_left', available_columns[0])
                    ) if st.session_state.column_mapping.get('top_left') in available_columns else 0,
                    key="mapping_top_left_33"
                )
                st.session_state.column_mapping['top_right'] = st.selectbox(
                    "Верхний правый угол (Цена)",
                    available_columns,
                    index=available_columns.index(
                        st.session_state.column_mapping.get('top_right', available_columns[1])
                    ) if st.session_state.column_mapping.get('top_right') in available_columns and len(available_columns) > 1 else min(1, len(available_columns)-1),
                    key="mapping_top_right_34"
                )
                st.session_state.column_mapping['image_url'] = st.selectbox(
                    "URL основного изображения",
                    available_columns,
                    index=available_columns.index(
                        st.session_state.column_mapping.get('image_url', available_columns[2])
                    ) if st.session_state.column_mapping.get('image_url') in available_columns and len(available_columns) > 2 else min(2, len(available_columns)-1),
                    key="mapping_image_url_35"
                )
            
            with col2:
                st.session_state.column_mapping['bottom_left'] = st.selectbox(
                    "Нижний левый угол (Характеристики)",
                    available_columns,
                    index=available_columns.index(
                        st.session_state.column_mapping.get('bottom_left', available_columns[3])
                    ) if st.session_state.column_mapping.get('bottom_left') in available_columns and len(available_columns) > 3 else min(3, len(available_columns)-1),
                    key="mapping_bottom_left_36"
                )
                st.session_state.column_mapping['bottom_right'] = st.selectbox(
                    "Нижний правый угол (Скидка/Детали)",
                    available_columns,
                    index=available_columns.index(
                        st.session_state.column_mapping.get('bottom_right', available_columns[4])
                    ) if st.session_state.column_mapping.get('bottom_right') in available_columns and len(available_columns) > 4 else min(4, len(available_columns)-1),
                    key="mapping_bottom_right_37"
                )
                st.session_state.column_mapping['filename'] = st.selectbox(
                    "Имена файлов (источник)",
                    available_columns,
                    index=available_columns.index(
                        st.session_state.column_mapping.get('filename', available_columns[0])
                    ) if st.session_state.column_mapping.get('filename') in available_columns else 0,
                    key="mapping_filename_38"
                )
            
            st.subheader("🖼️ Изображение для наложения")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                overlay_image_column = st.selectbox(
                    "Колонка с изображениями для наложения",
                    ["Не использовать"] + available_columns,
                    index=0 if st.session_state.column_mapping.get('overlay_image_url') not in available_columns else 
                          available_columns.index(st.session_state.column_mapping.get('overlay_image_url')) + 1,
                    key="mapping_overlay_image_39"
                )
                
                if overlay_image_column != "Не использовать":
                    st.session_state.column_mapping['overlay_image_url'] = overlay_image_column
                elif 'overlay_image_url' in st.session_state.column_mapping:
                    del st.session_state.column_mapping['overlay_image_url']
            
            with col2:
                st.session_state.image_overlay_settings['enabled'] = st.checkbox(
                    "Включить наложение",
                    value=st.session_state.image_overlay_settings.get('enabled', False),
                    key="mapping_enable_overlay_40"
                )
            
            if st.button("🔍 Автоподбор колонок", type="secondary", key="auto_map_41"):
                suggestions = ExcelProcessor.get_column_suggestions(st.session_state.df)
                st.session_state.column_mapping = suggestions
                st.success("✅ Колонки автоматически подобраны!")
                time.sleep(1)
                st.rerun()
    
    @staticmethod
    def render_font_settings():
        """Настройки шрифтов"""
        st.subheader("🔤 Настройки шрифтов")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Загрузка шрифтов**")
            
            uploaded_fonts = st.file_uploader(
                "Загрузите файлы шрифтов (.ttf, .otf)",
                type=['ttf', 'otf'],
                accept_multiple_files=True,
                help="Загрузите свои шрифты для использования в инфографике",
                key="font_uploader_42"
            )
            
            if uploaded_fonts:
                for font_file in uploaded_fonts:
                    with st.spinner(f"Загрузка {font_file.name}..."):
                        font_key, font_name = FontManager.load_font_from_file(font_file)
                        if font_key:
                            st.success(f"✅ Шрифт '{font_name}' загружен")
                        else:
                            st.error(f"❌ Ошибка загрузки шрифта '{font_file.name}'")
            
            if st.session_state.get('uploaded_fonts'):
                st.markdown("**Загруженные шрифты:**")
                for font_info in st.session_state.uploaded_fonts:
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.caption(f"📁 {font_info['name']}")
                    with col_b:
                        if st.button("🗑️", key=f"delete_font_{font_info['key']}_43"):
                            if font_info['key'] in st.session_state.font_cache:
                                del st.session_state.font_cache[font_info['key']]
                            
                            st.session_state.uploaded_fonts = [
                                f for f in st.session_state.uploaded_fonts 
                                if f['key'] != font_info['key']
                            ]
                            st.rerun()
        
        with col2:
            st.markdown("**Выбор шрифтов**")
            
            available_fonts = FontManager.get_available_fonts()
            
            if available_fonts:
                font_options = [f["name"] for f in available_fonts]
                font_keys = [f["key"] for f in available_fonts]
                
                current_main_font = st.session_state.font_settings.get('main_font', 'system_arial')
                current_main_index = font_keys.index(current_main_font) if current_main_font in font_keys else 0
                
                main_font_name = st.selectbox(
                    "Основной шрифт",
                    font_options,
                    index=current_main_index,
                    key="main_font_select_44"
                )
                
                if main_font_name:
                    selected_index = font_options.index(main_font_name)
                    st.session_state.font_settings['main_font'] = font_keys[selected_index]
                
                current_bold_font = st.session_state.font_settings.get('bold_font', 'system_arial')
                current_bold_index = font_keys.index(current_bold_font) if current_bold_font in font_keys else 0
                
                bold_font_name = st.selectbox(
                    "Жирный шрифт (для заголовков)",
                    ["Тот же что основной"] + font_options,
                    index=0 if current_bold_font == current_main_font else current_bold_index + 1,
                    key="bold_font_select_45"
                )
                
                if bold_font_name == "Тот же что основной":
                    st.session_state.font_settings['bold_font'] = st.session_state.font_settings['main_font']
                elif bold_font_name:
                    selected_index = font_options.index(bold_font_name)
                    st.session_state.font_settings['bold_font'] = font_keys[selected_index]
                
                font_size_multiplier = st.slider(
                    "Множитель размера шрифта",
                    0.5, 2.0, 0.1,
                    st.session_state.font_settings.get('font_size_multiplier', 1.0),
                    key="font_size_multiplier_46"
                )
                st.session_state.font_settings['font_size_multiplier'] = font_size_multiplier
    
    @staticmethod
    def render_text_offset_settings():
        """Настройки смещения текста"""
        if st.session_state.get('df') is not None:
            st.subheader("🎯 Настройки смещения текста")
            st.info("Регулируйте положение текста на изображении")
            
            col1, col2 = st.columns(2)
            with col1:
                symmetrical = st.checkbox(
                    "🔄 Симметричные смещения для всех углов",
                    value=st.session_state.get('symmetrical_offsets', False),
                    help="При включении все углы будут иметь одинаковые смещения",
                    key="symmetrical_offsets_47"
                )
                st.session_state.symmetrical_offsets = symmetrical
            
            with col2:
                if symmetrical:
                    st.info("⚠️ Режим симметричных смещений активен")
            
            cols = st.columns(4)
            
            with cols[0]:
                st.markdown("**↖️ Верхний левый**")
                if not symmetrical:
                    x_offset = st.number_input(
                        "Смещение X (%)",
                        -100, 100,
                        st.session_state.text_offset_settings['top_left'].get('x_offset', 0),
                        key="top_left_x_48"
                    )
                    y_offset = st.number_input(
                        "Смещение Y (%)",
                        -100, 100,
                        st.session_state.text_offset_settings['top_left'].get('y_offset', 0),
                        key="top_left_y_49"
                    )
                    st.session_state.text_offset_settings['top_left'] = {
                        'x_offset': x_offset,
                        'y_offset': y_offset
                    }
                else:
                    st.info("Настройки применяются ко всем углам")
            
            with cols[1]:
                st.markdown("**↗️ Верхний правый**")
                if not symmetrical:
                    x_offset = st.number_input(
                        "Смещение X (%)",
                        -100, 100,
                        st.session_state.text_offset_settings['top_right'].get('x_offset', 0),
                        key="top_right_x_50"
                    )
                    y_offset = st.number_input(
                        "Смещение Y (%)",
                        -100, 100,
                        st.session_state.text_offset_settings['top_right'].get('y_offset', 0),
                        key="top_right_y_51"
                    )
                    st.session_state.text_offset_settings['top_right'] = {
                        'x_offset': x_offset,
                        'y_offset': y_offset
                    }
                else:
                    st.caption(f"X: {st.session_state.text_offset_settings['top_left'].get('x_offset', 0)}%")
                    st.caption(f"Y: {st.session_state.text_offset_settings['top_left'].get('y_offset', 0)}%")
            
            with cols[2]:
                st.markdown("**↙️ Нижний левый**")
                if not symmetrical:
                    x_offset = st.number_input(
                        "Смещение X (%)",
                        -100, 100,
                        st.session_state.text_offset_settings['bottom_left'].get('x_offset', 0),
                        key="bottom_left_x_52"
                    )
                    y_offset = st.number_input(
                        "Смещение Y (%)",
                        -100, 100,
                        st.session_state.text_offset_settings['bottom_left'].get('y_offset', 0),
                        key="bottom_left_y_53"
                    )
                    st.session_state.text_offset_settings['bottom_left'] = {
                        'x_offset': x_offset,
                        'y_offset': y_offset
                    }
                else:
                    st.caption(f"X: {st.session_state.text_offset_settings['top_left'].get('x_offset', 0)}%")
                    st.caption(f"Y: {st.session_state.text_offset_settings['top_left'].get('y_offset', 0)}%")
            
            with cols[3]:
                st.markdown("**↘️ Нижний правый**")
                if not symmetrical:
                    x_offset = st.number_input(
                        "Смещение X (%)",
                        -100, 100,
                        st.session_state.text_offset_settings['bottom_right'].get('x_offset', 0),
                        key="bottom_right_x_54"
                    )
                    y_offset = st.number_input(
                        "Смещение Y (%)",
                        -100, 100,
                        st.session_state.text_offset_settings['bottom_right'].get('y_offset', 0),
                        key="bottom_right_y_55"
                    )
                    st.session_state.text_offset_settings['bottom_right'] = {
                        'x_offset': x_offset,
                        'y_offset': y_offset
                    }
                else:
                    st.caption(f"X: {st.session_state.text_offset_settings['top_left'].get('x_offset', 0)}%")
                    st.caption(f"Y: {st.session_state.text_offset_settings['top_left'].get('y_offset', 0)}%")
            
            if symmetrical:
                st.markdown("---")
                st.subheader("🔄 Общие настройки для всех углов")
                
                col1, col2 = st.columns(2)
                with col1:
                    common_x_offset = st.number_input(
                        "Общее смещение по X (%)",
                        -100, 100,
                        st.session_state.text_offset_settings['top_left'].get('x_offset', 0),
                        key="common_x_56"
                    )
                with col2:
                    common_y_offset = st.number_input(
                        "Общее смещение по Y (%)",
                        -100, 100,
                        st.session_state.text_offset_settings['top_left'].get('y_offset', 0),
                        key="common_y_57"
                    )
                
                st.session_state.text_offset_settings = {
                    'top_left': {'x_offset': common_x_offset, 'y_offset': common_y_offset},
                    'top_right': {'x_offset': common_x_offset, 'y_offset': common_y_offset},
                    'bottom_left': {'x_offset': common_x_offset, 'y_offset': common_y_offset},
                    'bottom_right': {'x_offset': common_x_offset, 'y_offset': common_y_offset}
                }
            
            st.caption("💡 Положительные значения смещают текст вправо/вниз, отрицательные - влево/вверх")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Сбросить смещения", type="secondary", key="reset_offsets_58", use_container_width=True):
                    st.session_state.text_offset_settings = {
                        'top_left': {'x_offset': 0, 'y_offset': 0},
                        'top_right': {'x_offset': 0, 'y_offset': 0},
                        'bottom_left': {'x_offset': 0, 'y_offset': 0},
                        'bottom_right': {'x_offset': 0, 'y_offset': 0}
                    }
                    st.rerun()
            
            with col2:
                if not symmetrical:
                    if st.button("📐 Сделать симметричными", type="secondary", key="make_symmetrical_59", use_container_width=True):
                        top_left_settings = st.session_state.text_offset_settings['top_left']
                        st.session_state.text_offset_settings = {
                            'top_left': top_left_settings,
                            'top_right': top_left_settings.copy(),
                            'bottom_left': top_left_settings.copy(),
                            'bottom_right': top_left_settings.copy()
                        }
                        st.success("✅ Настройки применены ко всем углам!")
                        st.rerun()
    
    @staticmethod
    def render_image_overlay_settings():
        """Настройки наложения изображений"""
        if st.session_state.get('df') is not None and st.session_state.image_overlay_settings.get('enabled', False):
            st.subheader("🖼️ Настройки наложения изображений")
            st.info("Настройте параметры для дополнительных изображений (логотипы, стикеры и т.д.)")
            
            col1, col2 = st.columns(2)
            with col1:
                position = st.selectbox(
                    "Позиция на изображении",
                    ["center", "top_left", "top_right", "bottom_left", "bottom_right"],
                    index=["center", "top_left", "top_right", "bottom_left", "bottom_right"].index(
                        st.session_state.image_overlay_settings.get('position', 'center')
                    ),
                    key="overlay_position_60"
                )
                st.session_state.image_overlay_settings['position'] = position
            
            with col2:
                opacity = st.slider(
                    "Прозрачность (%)",
                    0, 100,
                    st.session_state.image_overlay_settings.get('opacity', 100),
                    key="overlay_opacity_61"
                )
                st.session_state.image_overlay_settings['opacity'] = opacity
            
            col1, col2 = st.columns(2)
            with col1:
                scale = st.slider(
                    "Масштаб (%)",
                    10, 200,
                    st.session_state.image_overlay_settings.get('scale', 100),
                    key="overlay_scale_62"
                )
                st.session_state.image_overlay_settings['scale'] = scale
            
            with col2:
                max_width = st.slider(
                    "Макс. ширина (% от основного)",
                    5, 100,
                    st.session_state.image_overlay_settings.get('max_width', 30),
                    key="overlay_max_width_63"
                )
                st.session_state.image_overlay_settings['max_width'] = max_width
            
            col1, col2 = st.columns(2)
            with col1:
                x_offset = st.number_input(
                    "Смещение по X (%)",
                    -100, 100,
                    st.session_state.image_overlay_settings.get('x_offset', 0),
                    key="overlay_x_offset_64"
                )
                st.session_state.image_overlay_settings['x_offset'] = x_offset
            
            with col2:
                y_offset = st.number_input(
                    "Смещение по Y (%)",
                    -100, 100,
                    st.session_state.image_overlay_settings.get('y_offset', 0),
                    key="overlay_y_offset_65"
                )
                st.session_state.image_overlay_settings['y_offset'] = y_offset
    
    @staticmethod
    def render_preview_tab(generator):
        """Вкладка предпросмотра"""
        if st.session_state.get('df') is None:
            st.info("📥 Загрузите Excel файл в боковой панели для начала работы")
            return
        
        st.header("🎯 Предпросмотр и тестирование")
        
        UIComponents.render_font_settings()
        UIComponents.render_text_offset_settings()
        UIComponents.render_image_overlay_settings()
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            test_row_idx = st.number_input(
                "Номер строки для тестирования",
                min_value=0,
                max_value=len(st.session_state.df)-1,
                value=min(0, len(st.session_state.df)-1),
                key="preview_test_row_66"
            )
        with col2:
            timeout = st.select_slider(
                "Таймаут (сек)",
                options=[5, 10, 15, 30, 60],
                value=st.session_state.export_settings.get('timeout', 30),
                key="preview_timeout_67"
            )
        with col3:
            st.write("")
            st.write("")
            test_button = st.button("🚀 Запустить тест", type="primary", key="preview_test_button_68", use_container_width=True)
        
        if test_button and test_row_idx < len(st.session_state.df):
            with st.spinner("Выполнение теста..."):
                row = st.session_state.df.iloc[test_row_idx]
                
                text_data = {}
                for position in ['top_left', 'top_right', 'bottom_left', 'bottom_right']:
                    col = st.session_state.column_mapping.get(position)
                    if col and col in row:
                        text_data[position] = str(row[col] or '')
                    else:
                        text_data[position] = ''
                
                image_url = ''
                if 'image_url' in st.session_state.column_mapping:
                    col = st.session_state.column_mapping['image_url']
                    if col in row:
                        image_url = str(row[col] or '')
                
                overlay_image_url = None
                if ('overlay_image_url' in st.session_state.column_mapping and 
                    st.session_state.column_mapping['overlay_image_url'] in row):
                    overlay_image_url = str(row[st.session_state.column_mapping['overlay_image_url']] or '')
                    if overlay_image_url.lower() in ['none', 'nan', '']:
                        overlay_image_url = None
                
                with st.expander("📋 Исходные данные строки"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.json(text_data, expanded=False)
                    with col2:
                        st.code(f"Основное изображение:\n{image_url[:100]}..." if len(image_url) > 100 else f"Основное изображение:\n{image_url}")
                        if overlay_image_url:
                            st.code(f"Изображение наложения:\n{overlay_image_url[:100]}..." if len(overlay_image_url) > 100 else f"Изображение наложения:\n{overlay_image_url}")
                
                if image_url and image_url.startswith(('http://', 'https://')):
                    img = generator.image_processor.load_image_from_url(image_url, timeout)
                    
                    if img:
                        if st.session_state.get('symmetrical_offsets', False):
                            st.success(f"**🔄 Симметричные смещения:** X: {st.session_state.text_offset_settings['top_left'].get('x_offset', 0)}%, Y: {st.session_state.text_offset_settings['top_left'].get('y_offset', 0)}%")
                        else:
                            offset_info = "\n".join([
                                f"{pos}: X={offsets.get('x_offset', 0)}%, Y={offsets.get('y_offset', 0)}%"
                                for pos, offsets in st.session_state.text_offset_settings.items()
                            ])
                            st.info(f"**Применяемые смещения текста:**\n{offset_info}")
                        
                        if st.session_state.image_overlay_settings.get('enabled', False):
                            st.info(f"**Наложение изображений:** Включено, позиция: {st.session_state.image_overlay_settings.get('position', 'center')}")
                        
                        if st.session_state.export_settings.get('resize', True):
                            target_size = st.session_state.export_settings.get('target_size', 1200)
                            img = generator.image_processor.resize_image(img, target_size)
                        
                        template_canvas = generator.image_processor.create_template_canvas(
                            img.width, img.height, st.session_state.current_template
                        )
                        
                        final_img = template_canvas.copy()
                        
                        header_height = int(img.height * st.session_state.background_settings.get('header_height', 15) / 100)
                        final_img.paste(img, (0, header_height))
                        
                        processed_img = generator.image_processor.add_text_to_image(
                            final_img,
                            text_data,
                            st.session_state.current_template,
                            text_offsets=st.session_state.text_offset_settings,
                            font_settings=st.session_state.font_settings
                        )
                        
                        if (st.session_state.image_overlay_settings.get('enabled', False) and 
                            overlay_image_url and overlay_image_url.startswith(('http://', 'https://', 'data:'))):
                            
                            overlay_img = generator.image_processor.load_image_from_url(overlay_image_url, timeout=15, retries=2)
                            if overlay_img:
                                processed_img = generator.image_processor.add_image_overlay(
                                    processed_img,
                                    overlay_img,
                                    st.session_state.image_overlay_settings
                                )
                                st.success("✅ Изображение наложения добавлено")
                            else:
                                st.warning("⚠️ Не удалось загрузить изображение для наложения")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("📷 Оригинал")
                            st.image(img, use_column_width=True)
                            st.caption(f"Размер: {img.width}×{img.height}, Формат: {img.format or 'Неизвестно'}")
                        with col2:
                            st.subheader("🎨 С инфографикой")
                            st.image(processed_img, use_column_width=True)
                            st.caption(f"Шаблон: {st.session_state.current_template}")
                            
                            show_grid = st.checkbox("Показать сетку позиций", value=False, key="preview_show_grid_69")
                            if show_grid:
                                grid_img = processed_img.copy()
                                draw = ImageDraw.Draw(grid_img)
                                template = DynamicTemplateManager.load_template(st.session_state.current_template)
                                
                                text_positions = template.get("text_positions", {})
                                
                                for position_key, position_data in text_positions.items():
                                    base_x = position_data.get("x", 0.5) * grid_img.width
                                    base_y = position_data.get("y", 0.5)
                                    
                                    layout = template.get("layout", {})
                                    header_height_percent = layout.get("header_height", 15)
                                    footer_height_percent = layout.get("footer_height", 10)
                                    
                                    header_height_px = int(grid_img.height * header_height_percent / 100)
                                    footer_height_px = int(grid_img.height * footer_height_percent / 100)
                                    main_height_px = grid_img.height - header_height_px - footer_height_px
                                    
                                    section = position_data.get("section", "main")
                                    if section == "header":
                                        base_y = base_y * header_height_px
                                    elif section == "footer":
                                        base_y = header_height_px + main_height_px + base_y * footer_height_px
                                    else:
                                        base_y = header_height_px + base_y * main_height_px
                                    
                                    x = int(base_x)
                                    y = int(base_y)
                                    
                                    draw.ellipse([x-5, y-5, x+5, y+5], fill='red')
                                    draw.text((x+10, y-10), position_key, fill='red', 
                                             font=FontManager.load_system_font('system_arial', 12))
                                
                                st.image(grid_img, use_container_width=True, caption="Сетка позиций текста (красные точки)")
                        
                        buffered = BytesIO()
                        format_ext = st.session_state.export_settings.get('format', 'PNG').lower()
                        
                        if st.session_state.export_settings['format'] == 'JPEG':
                            processed_img.convert('RGB').save(
                                buffered,
                                format='JPEG',
                                quality=st.session_state.export_settings.get('quality', 95)
                            )
                            mime_type = 'image/jpeg'
                        elif st.session_state.export_settings['format'] == 'WEBP':
                            processed_img.save(
                                buffered,
                                format='WEBP',
                                quality=st.session_state.export_settings.get('quality', 95)
                            )
                            mime_type = 'image/webp'
                        else:
                            processed_img.save(buffered, format='PNG')
                            mime_type = 'image/png'
                        
                        st.download_button(
                            label="💾 Скачать тестовое изображение",
                            data=buffered.getvalue(),
                            file_name=f"test_preview_{test_row_idx}.{format_ext}",
                            mime=mime_type,
                            key="preview_download_70",
                            use_container_width=True
                        )
                        
                        st.session_state.preview_image = processed_img
                    else:
                        st.error("❌ Не удалось загрузить изображение. Проверьте URL и подключение к интернету.")
                else:
                    st.warning("⚠️ Некорректный URL основного изображения")
    
    @staticmethod
    def render_processing_tab(generator):
        """Вкладка обработки"""
        if st.session_state.get('df') is None:
            st.info("📥 Загрузите Excel файл в боковой панели для начала работы")
            return
        
        st.header("⚡ Массовая обработка")
        
        df_optimized = ExcelProcessor.optimize_dataframe(st.session_state.df)
        total_rows = len(df_optimized)
        
        if total_rows == 0:
            st.error("❌ Нет данных для обработки. Проверьте наличие URL изображений в файле.")
            return
        
        if st.session_state.get('symmetrical_offsets', False):
            st.success(f"**🔄 Будут применены симметричные смещения:** X: {st.session_state.text_offset_settings['top_left'].get('x_offset', 0)}%, Y: {st.session_state.text_offset_settings['top_left'].get('y_offset', 0)}%")
        else:
            offset_info = "\n".join([
                f"{pos}: X={offsets.get('x_offset', 0)}%, Y={offsets.get('y_offset', 0)}%"
                for pos, offsets in st.session_state.text_offset_settings.items()
            ])
            st.info(f"**Будут применены смещения текста:**\n{offset_info}")
        
        if st.session_state.image_overlay_settings.get('enabled', False):
            st.info(f"**🖼️ Наложение изображений:** Включено, позиция: {st.session_state.image_overlay_settings.get('position', 'center')}")
        
        if st.session_state.font_settings.get('main_font'):
            available_fonts = FontManager.get_available_fonts()
            font_name = next((f["name"] for f in available_fonts if f["key"] == st.session_state.font_settings['main_font']), "Системный шрифт")
            st.info(f"**🔤 Шрифт:** {font_name}, множитель: {st.session_state.font_settings.get('font_size_multiplier', 1.0)}")
        
        st.info(f"📊 Готово к обработке: {total_rows} строк")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            start_idx = st.number_input(
                "Начать с строки",
                0, total_rows-1, 0,
                key="processing_start_idx_71"
            )
        with col2:
            end_idx = st.number_input(
                "Закончить на строке",
                start_idx, total_rows-1,
                min(start_idx + st.session_state.processing_settings.get('batch_size', 50) - 1, total_rows-1),
                key="processing_end_idx_72"
            )
        with col3:
            st.write("")
            st.write("")
            process_button = st.button(
                "🔄 Начать обработку", 
                type="primary", 
                use_container_width=True,
                key="processing_button_73"
            )
        
        batch_size = end_idx - start_idx + 1
        if batch_size > 0:
            st.success(f"✅ Будет обработано: {batch_size} строк")
        
        if process_button and batch_size > 0:
            st.session_state.processing_stats = {
                'total': batch_size,
                'success': 0,
                'failed': 0,
                'start_time': datetime.now(),
                'end_time': None
            }
            
            progress_bar = st.progress(0, text="Начало обработки...")
            status_text = st.empty()
            results_placeholder = st.empty()
            
            st.session_state.progress_bar = progress_bar
            st.session_state.status_text = status_text
            
            with st.spinner("Запуск обработки..."):
                results = generator.process_batch(
                    df_optimized,
                    start_idx,
                    end_idx,
                    st.session_state.column_mapping,
                    st.session_state.current_template,
                    {
                        **st.session_state.export_settings,
                        'timeout': st.session_state.processing_settings.get('timeout', 30),
                        'retry_count': st.session_state.processing_settings.get('retry_count', 3)
                    },
                    st.session_state.processing_settings,
                    text_offsets=st.session_state.text_offset_settings,
                    overlay_settings=st.session_state.image_overlay_settings if st.session_state.image_overlay_settings.get('enabled', False) else None,
                    font_settings=st.session_state.font_settings
                )
            
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
                    st.metric("Успешно", success_count, delta=f"{success_count/batch_size*100:.1f}%" if batch_size > 0 else "0%")
                with col2:
                    st.metric("С ошибками", failed_count, delta=f"-{failed_count}" if failed_count > 0 else None)
                with col3:
                    if st.session_state.processing_stats['start_time'] and st.session_state.processing_stats['end_time']:
                        duration = (
                            st.session_state.processing_stats['end_time'] -
                            st.session_state.processing_stats['start_time']
                        ).total_seconds()
                        st.metric("Время", f"{duration:.1f} сек", delta=f"{batch_size/duration:.1f}/сек" if duration > 0 else None)
                
                if failed_count > 0:
                    with st.expander("📋 Детали ошибок", expanded=False):
                        error_results = [r for r in results if r.get('status') == 'error']
                        error_df = pd.DataFrame(error_results)
                        if not error_df.empty:
                            st.dataframe(error_df[['row_index', 'message']], use_container_width=True)
                
                if success_count > 0:
                    with st.spinner("Создание архива..."):
                        zip_path, csv_path = generator.create_zip_archive(results)
                        
                        if zip_path and os.path.exists(zip_path):
                            col1, col2 = st.columns(2)
                            with col1:
                                with open(zip_path, 'rb') as f:
                                    st.download_button(
                                        label="📦 Скачать ZIP архив",
                                        data=f.read(),
                                        file_name=os.path.basename(zip_path),
                                        mime="application/zip",
                                        use_container_width=True,
                                        key="processing_zip_74"
                                    )
                            with col2:
                                with open(csv_path, 'rb') as f:
                                    st.download_button(
                                        label="📊 Скачать отчет (CSV)",
                                        data=f.read(),
                                        file_name=os.path.basename(csv_path),
                                        mime="text/csv",
                                        use_container_width=True,
                                        key="processing_csv_75"
                                    )
                            
                            zip_size = os.path.getsize(zip_path) / (1024 * 1024)
                            st.info(f"📦 Размер архива: {zip_size:.2f} MB, файлов: {success_count}")
                        else:
                            st.error("❌ Ошибка создания архива")
    
    @staticmethod
    def render_statistics_tab():
        """Вкладка статистики"""
        st.header("📊 Статистика и аналитика")
        
        if st.session_state.get('processed_count', 0) == 0:
            st.info("📈 Статистика появится после обработки данных")
            return
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Всего обработано", st.session_state.get('processed_count', 0))
        with col2:
            if st.session_state.get('batch_results'):
                success_count = sum(1 for r in st.session_state.batch_results if r.get('status') == 'success')
                total_count = len(st.session_state.batch_results)
                success_rate = (success_count / total_count * 100) if total_count > 0 else 0
                st.metric("Успешность", f"{success_rate:.1f}%")
        with col3:
            template_name = DynamicTemplateManager.load_template(st.session_state.current_template).get('name', 'Неизвестно')
            st.metric("Текущий шаблон", template_name[:15] + "..." if len(template_name) > 15 else template_name)
        with col4:
            st.metric("Формат экспорта", st.session_state.export_settings.get('format', 'PNG'))
        
        show_settings = st.checkbox("Показать текущие настройки", value=False, key="stats_show_settings_76")
        if show_settings:
            st.subheader("⚙️ Текущие настройки")
            
            if st.session_state.get('symmetrical_offsets', False):
                st.success("🔄 Режим симметричных смещений активен")
                st.write(f"**Общие смещения:** X: {st.session_state.text_offset_settings['top_left'].get('x_offset', 0)}%, Y: {st.session_state.text_offset_settings['top_left'].get('y_offset', 0)}%")
            else:
                offset_df = pd.DataFrame(st.session_state.text_offset_settings).T
                st.write("**Смещения текста:**")
                st.dataframe(offset_df, use_container_width=True)
            
            if st.session_state.image_overlay_settings.get('enabled', False):
                st.write(f"**Наложение изображений:** Включено")
                st.write(f"Позиция: {st.session_state.image_overlay_settings.get('position', 'center')}, Прозрачность: {st.session_state.image_overlay_settings.get('opacity', 100)}%")
            
            if st.session_state.font_settings.get('main_font'):
                available_fonts = FontManager.get_available_fonts()
                font_name = next((f["name"] for f in available_fonts if f["key"] == st.session_state.font_settings['main_font']), "Системный шрифт")
                st.write(f"**Шрифт:** {font_name}, Множитель размера: {st.session_state.font_settings.get('font_size_multiplier', 1.0)}")
        
        if st.session_state.get('batch_results'):
            st.subheader("📈 Детальная статистика последней обработки")
            results_df = pd.DataFrame(st.session_state.batch_results)
            
            if 'status' in results_df.columns:
                status_counts = results_df['status'].value_counts()
                col1, col2 = st.columns(2)
                with col1:
                    st.bar_chart(status_counts)
                with col2:
                    st.dataframe(status_counts, use_container_width=True)
            
            if (st.session_state.processing_stats.get('start_time') and
                st.session_state.processing_stats.get('end_time')):
                duration = (
                    st.session_state.processing_stats['end_time'] -
                    st.session_state.processing_stats['start_time']
                ).total_seconds()
                
                if duration > 0 and len(results_df) > 0:
                    speed = len(results_df) / duration
                    st.metric("Скорость обработки", f"{speed:.2f} изобр/сек")

# ============================
# ОСНОВНОЙ КОД ПРИЛОЖЕНИЯ
# ============================
def main():
    """Основная функция приложения"""
    try:
        init_session_state()
        
        try:
            DynamicTemplateManager.ensure_templates_dir()
        except Exception as e:
            logger.error(f"Ошибка инициализации шаблонов: {e}")
            st.error("Ошибка инициализации системы шаблонов")
        
        st.title("🚀 Генератор Инфографики PRO v7.0")  # Закрывающая скобка добавлена здесь
    except Exception as e:
        logger.error(f"Ошибка в функции main: {e}")
