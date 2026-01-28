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
    page_title="🎯 Генератор Инфографики PRO v10.0",
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
            'product_name': None,
            'price': None,
            'old_price': None,
            'discount': None,
            'description': None,
            'features': None,
            'rating': None,
            'reviews': None,
            'image_url': None,
            'filename': None,
            'sku': None,
            'brand': None,
            'category': None,
            'shipping': None,
            'warranty': None,
            'availability': None
        },
        'output_dir': 'output_infographics',
        'local_save_path': None,
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
        'font_settings': {
            'main_font': 'system_arial',
            'bold_font': 'system_arial',
            'font_size_multiplier': 1.0
        },
        'loaded_templates': {},
        'template_files': [],
        'editing_template': False,
        'editing_template_id': None,
        'editing_template_data': {},
        'background_settings': {
            'background_color': '#FFFFFF',
            'border_color': '#E0E0E0',
            'border_width': 2,
            'corner_radius': 20,
            'shadow_enabled': True,
            'gradient_enabled': False,
            'gradient_color': '#4A90E2',
            'gradient_direction': 'horizontal'
        },
        'template_categories': {
            'all': 'Все шаблоны',
            'amazon': '🛒 Amazon',
            'wildberries': '📦 Wildberries',
            'ozon': '📊 Ozon',
            'yandex': '🎯 Яндекс.Маркет',
            'social': '📱 Соцсети',
            'minimal': '🌀 Минимализм',
            'premium': '💎 Премиум',
            'sale': '⚡ Распродажа'
        },
        'current_category': 'all',
        'app_initialized': False,
        'template_cache_initialized': False,
        'current_batch': None,
        'current_batch_index': 0,
        'custom_templates': {},
        'template_editor_active': False,
        'text_elements': {},
        'smart_text_processing': True,
        'text_auto_adjust': True,
        'current_preview_row': 0
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
# ТЕКСТОВЫЙ ПРОЦЕССОР ДЛЯ УМНОЙ ОБРАБОТКИ
# ============================
class TextProcessor:
    """Умная обработка текста для маркетплейсов"""
    
    @staticmethod
    def process_product_name(text: str) -> str:
        """Обработка названия товара"""
        if not text or pd.isna(text):
            return ""
        
        text = str(text).strip()
        
        # Удаление лишних пробелов
        text = re.sub(r'\s+', ' ', text)
        
        # Ограничение длины
        if len(text) > 200:
            text = text[:197] + "..."
        
        return text
    
    @staticmethod
    def process_price(text: str) -> str:
        """Обработка цены"""
        if not text or pd.isna(text):
            return ""
        
        text = str(text).strip()
        
        # Извлечение чисел
        numbers = re.findall(r'\d+[.,]?\d*', text)
        if numbers:
            # Форматирование числа
            try:
                num = float(numbers[0].replace(',', '.'))
                formatted = f"{num:,.0f}".replace(",", " ").replace(".", ",")
                
                # Добавление валюты если не указана
                if 'руб' not in text.lower() and '₽' not in text and 'р.' not in text.lower():
                    formatted = f"{formatted} ₽"
                
                return formatted
            except:
                return text
        return text
    
    @staticmethod
    def process_discount(text: str) -> str:
        """Обработка скидки"""
        if not text or pd.isna(text):
            return ""
        
        text = str(text).strip()
        
        # Поиск процентов
        percentages = re.findall(r'\d+\s*%', text)
        if percentages:
            return percentages[0]
        
        # Поиск чисел
        numbers = re.findall(r'\d+', text)
        if numbers:
            return f"-{numbers[0]}%"
        
        return text
    
    @staticmethod
    def process_description(text: str, max_length: int = 150) -> str:
        """Обработка описания"""
        if not text or pd.isna(text):
            return ""
        
        text = str(text).strip()
        
        # Удаление HTML тегов
        text = re.sub(r'<[^>]+>', '', text)
        
        # Удаление лишних пробелов
        text = re.sub(r'\s+', ' ', text)
        
        # Сокращение длинных текстов
        if len(text) > max_length:
            # Ищем последнюю точку до max_length
            cutoff = text[:max_length]
            last_period = cutoff.rfind('.')
            last_exclamation = cutoff.rfind('!')
            last_question = cutoff.rfind('?')
            
            last_punctuation = max(last_period, last_exclamation, last_question)
            
            if last_punctuation > 0:
                text = text[:last_punctuation + 1]
            else:
                text = text[:max_length - 3] + "..."
        
        return text
    
    @staticmethod
    def process_rating(text: str) -> str:
        """Обработка рейтинга"""
        if not text or pd.isna(text):
            return "5.0"
        
        text = str(text).strip()
        
        # Поиск чисел с плавающей точкой
        numbers = re.findall(r'\d+[.,]\d+|\d+', text)
        if numbers:
            try:
                rating = float(numbers[0].replace(',', '.'))
                rating = max(0, min(5, rating))  # Ограничение 0-5
                return f"{rating:.1f} ⭐"
            except:
                return "5.0 ⭐"
        
        return "5.0 ⭐"
    
    @staticmethod
    def process_features(text: str) -> List[str]:
        """Обработка характеристик в список"""
        if not text or pd.isna(text):
            return []
        
        text = str(text).strip()
        
        # Разделение по различным разделителям
        separators = [';', '|', '\n', '•', '-']
        
        for sep in separators:
            if sep in text:
                features = [f.strip() for f in text.split(sep) if f.strip()]
                if features:
                    return features[:5]  # Ограничиваем 5 пунктами
        
        # Если нет разделителей, пытаемся разбить по длине
        if len(text) > 100:
            # Разбиваем на предложения
            sentences = re.split(r'[.!?]+', text)
            features = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
            return features[:5]
        
        return [text[:100]]
    
    @staticmethod
    def smart_process_text(field_type: str, text: str) -> str:
        """Умная обработка текста в зависимости от типа поля"""
        processors = {
            'product_name': TextProcessor.process_product_name,
            'price': TextProcessor.process_price,
            'old_price': TextProcessor.process_price,
            'discount': TextProcessor.process_discount,
            'description': TextProcessor.process_description,
            'rating': TextProcessor.process_rating,
        }
        
        if field_type in processors:
            return processors[field_type](text)
        else:
            return str(text).strip() if text and not pd.isna(text) else ""

# ============================
# СИСТЕМА ШАБЛОНОВ ДЛЯ МАРКЕТПЛЕЙСОВ
# ============================
class MarketplaceTemplateManager:
    """Менеджер шаблонов для маркетплейсов"""
    
    MARKETPLACE_TEMPLATES = {
        "amazon_style": {
            "name": "🛒 Amazon Style",
            "description": "Стиль Amazon с оранжевыми акцентами",
            "category": "amazon",
            "layout": {
                "width": 1200,
                "height": 800,
                "product_image_size": {"width": 600, "height": 600},
                "text_area_width": 500,
                "margin": 50
            },
            "colors": {
                "background": "#FFFFFF",
                "primary": "#FF9900",  # Amazon orange
                "secondary": "#232F3E",  # Amazon dark blue
                "text_primary": "#0F1111",
                "text_secondary": "#565959",
                "accent": "#CC0C39"  # Sale red
            },
            "text_elements": {
                "product_name": {
                    "position": {"x": 650, "y": 50},
                    "font_size": 36,
                    "font_weight": "bold",
                    "color": "#0F1111",
                    "max_width": 500,
                    "max_lines": 2
                },
                "rating": {
                    "position": {"x": 650, "y": 120},
                    "font_size": 24,
                    "color": "#FF9900"
                },
                "price_main": {
                    "position": {"x": 650, "y": 180},
                    "font_size": 48,
                    "font_weight": "bold",
                    "color": "#CC0C39"
                },
                "price_old": {
                    "position": {"x": 650, "y": 240},
                    "font_size": 24,
                    "color": "#565959",
                    "strikethrough": True
                },
                "discount_badge": {
                    "position": {"x": 850, "y": 180},
                    "font_size": 32,
                    "background_color": "#CC0C39",
                    "text_color": "#FFFFFF",
                    "padding": 10,
                    "corner_radius": 5
                },
                "features": {
                    "position": {"x": 650, "y": 300},
                    "font_size": 20,
                    "color": "#0F1111",
                    "line_spacing": 10,
                    "max_lines": 5
                },
                "shipping": {
                    "position": {"x": 650, "y": 500},
                    "font_size": 20,
                    "color": "#232F3E",
                    "icon": "🚚"
                },
                "warranty": {
                    "position": {"x": 650, "y": 540},
                    "font_size": 20,
                    "color": "#232F3E",
                    "icon": "🛡️"
                }
            }
        },
        "wildberries_style": {
            "name": "📦 Wildberries Style",
            "description": "Стиль Wildberries с фиолетовыми акцентами",
            "category": "wildberries",
            "layout": {
                "width": 1200,
                "height": 800,
                "product_image_size": {"width": 550, "height": 550},
                "text_area_width": 550,
                "margin": 40
            },
            "colors": {
                "background": "#FFFFFF",
                "primary": "#7B1FA2",  # Wildberries purple
                "secondary": "#4A148C",
                "text_primary": "#212121",
                "text_secondary": "#757575",
                "accent": "#FF4081"  # Pink accent
            },
            "text_elements": {
                "product_name": {
                    "position": {"x": 620, "y": 40},
                    "font_size": 32,
                    "font_weight": "bold",
                    "color": "#212121",
                    "max_width": 500,
                    "max_lines": 3
                },
                "rating": {
                    "position": {"x": 620, "y": 140},
                    "font_size": 22,
                    "color": "#FFB300"
                },
                "price_main": {
                    "position": {"x": 620, "y": 190},
                    "font_size": 42,
                    "font_weight": "bold",
                    "color": "#7B1FA2"
                },
                "price_old": {
                    "position": {"x": 620, "y": 240},
                    "font_size": 22,
                    "color": "#757575",
                    "strikethrough": True
                },
                "discount_badge": {
                    "position": {"x": 800, "y": 190},
                    "font_size": 28,
                    "background_color": "#FF4081",
                    "text_color": "#FFFFFF",
                    "padding": 8,
                    "corner_radius": 4
                },
                "features": {
                    "position": {"x": 620, "y": 290},
                    "font_size": 18,
                    "color": "#424242",
                    "line_spacing": 8,
                    "max_lines": 6
                },
                "sku": {
                    "position": {"x": 620, "y": 480},
                    "font_size": 16,
                    "color": "#757575"
                },
                "availability": {
                    "position": {"x": 620, "y": 520},
                    "font_size": 18,
                    "color": "#388E3C",
                    "icon": "✅"
                }
            }
        },
        "ozon_style": {
            "name": "📊 Ozon Style",
            "description": "Стиль Ozon с синими акцентами",
            "category": "ozon",
            "layout": {
                "width": 1200,
                "height": 800,
                "product_image_size": {"width": 580, "height": 580},
                "text_area_width": 520,
                "margin": 50
            },
            "colors": {
                "background": "#FFFFFF",
                "primary": "#005BFF",  # Ozon blue
                "secondary": "#003B99",
                "text_primary": "#1A1A1A",
                "text_secondary": "#666666",
                "accent": "#FF6B35"  # Orange accent
            },
            "text_elements": {
                "product_name": {
                    "position": {"x": 640, "y": 50},
                    "font_size": 34,
                    "font_weight": "bold",
                    "color": "#1A1A1A",
                    "max_width": 480,
                    "max_lines": 2
                },
                "rating": {
                    "position": {"x": 640, "y": 130},
                    "font_size": 23,
                    "color": "#FFB300"
                },
                "price_main": {
                    "position": {"x": 640, "y": 190},
                    "font_size": 44,
                    "font_weight": "bold",
                    "color": "#005BFF"
                },
                "price_old": {
                    "position": {"x": 640, "y": 250},
                    "font_size": 23,
                    "color": "#666666",
                    "strikethrough": True
                },
                "discount_badge": {
                    "position": {"x": 820, "y": 190},
                    "font_size": 30,
                    "background_color": "#FF6B35",
                    "text_color": "#FFFFFF",
                    "padding": 9,
                    "corner_radius": 5
                },
                "description": {
                    "position": {"x": 640, "y": 310},
                    "font_size": 19,
                    "color": "#333333",
                    "max_width": 480,
                    "max_lines": 4
                },
                "brand": {
                    "position": {"x": 640, "y": 450},
                    "font_size": 18,
                    "color": "#005BFF",
                    "font_weight": "bold"
                },
                "category": {
                    "position": {"x": 640, "y": 490},
                    "font_size": 16,
                    "color": "#666666"
                }
            }
        },
        "yandex_style": {
            "name": "🎯 Яндекс.Маркет",
            "description": "Стиль Яндекс.Маркет с красными акцентами",
            "category": "yandex",
            "layout": {
                "width": 1200,
                "height": 800,
                "product_image_size": {"width": 560, "height": 560},
                "text_area_width": 540,
                "margin": 50
            },
            "colors": {
                "background": "#FFFFFF",
                "primary": "#FF0000",  # Yandex red
                "secondary": "#CC0000",
                "text_primary": "#000000",
                "text_secondary": "#555555",
                "accent": "#FC0"  # Yellow accent
            },
            "text_elements": {
                "product_name": {
                    "position": {"x": 630, "y": 40},
                    "font_size": 35,
                    "font_weight": "bold",
                    "color": "#000000",
                    "max_width": 500,
                    "max_lines": 2
                },
                "rating": {
                    "position": {"x": 630, "y": 120},
                    "font_size": 24,
                    "color": "#FFB300"
                },
                "price_main": {
                    "position": {"x": 630, "y": 180},
                    "font_size": 46,
                    "font_weight": "bold",
                    "color": "#FF0000"
                },
                "price_old": {
                    "position": {"x": 630, "y": 240},
                    "font_size": 24,
                    "color": "#555555",
                    "strikethrough": True
                },
                "discount_badge": {
                    "position": {"x": 830, "y": 180},
                    "font_size": 32,
                    "background_color": "#FF0000",
                    "text_color": "#FFFFFF",
                    "padding": 10,
                    "corner_radius": 5
                },
                "key_features": {
                    "position": {"x": 630, "y": 300},
                    "font_size": 20,
                    "color": "#333333",
                    "line_spacing": 12,
                    "max_lines": 4
                },
                "reviews_count": {
                    "position": {"x": 730, "y": 120},
                    "font_size": 18,
                    "color": "#555555"
                },
                "delivery": {
                    "position": {"x": 630, "y": 450},
                    "font_size": 19,
                    "color": "#008000",
                    "icon": "📦"
                }
            }
        },
        "minimal_modern": {
            "name": "🌀 Минимализм",
            "description": "Минималистичный современный шаблон",
            "category": "minimal",
            "layout": {
                "width": 1200,
                "height": 800,
                "product_image_size": {"width": 700, "height": 700},
                "text_area_width": 400,
                "margin": 50
            },
            "colors": {
                "background": "#F8F9FA",
                "primary": "#6C757D",
                "secondary": "#495057",
                "text_primary": "#212529",
                "text_secondary": "#6C757D",
                "accent": "#20C997"
            },
            "text_elements": {
                "product_name": {
                    "position": {"x": 770, "y": 60},
                    "font_size": 28,
                    "font_weight": "light",
                    "color": "#212529",
                    "max_width": 380,
                    "max_lines": 3
                },
                "price_main": {
                    "position": {"x": 770, "y": 200},
                    "font_size": 40,
                    "font_weight": "medium",
                    "color": "#212529"
                },
                "description": {
                    "position": {"x": 770, "y": 280},
                    "font_size": 18,
                    "color": "#6C757D",
                    "max_width": 380,
                    "max_lines": 5
                },
                "features": {
                    "position": {"x": 770, "y": 420},
                    "font_size": 16,
                    "color": "#495057",
                    "line_spacing": 6,
                    "max_lines": 4
                }
            }
        }
    }
    
    @staticmethod
    def get_template(template_id: str) -> Dict:
        """Получение шаблона по ID"""
        return MarketplaceTemplateManager.MARKETPLACE_TEMPLATES.get(
            template_id, 
            MarketplaceTemplateManager.MARKETPLACE_TEMPLATES["amazon_style"]
        )
    
    @staticmethod
    def get_templates_by_category(category: str = "all") -> List[Tuple[str, str]]:
        """Получение шаблонов по категории"""
        result = []
        for template_id, template_data in MarketplaceTemplateManager.MARKETPLACE_TEMPLATES.items():
            if category == "all" or template_data["category"] == category:
                result.append((template_id, template_data["name"]))
        return result
    
    @staticmethod
    def get_template_names() -> List[Tuple[str, str]]:
        """Получение всех шаблонов"""
        return [(tid, data["name"]) for tid, data in MarketplaceTemplateManager.MARKETPLACE_TEMPLATES.items()]

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
    def get_font(font_key: str, size: int, weight: str = "normal") -> ImageFont.FreeTypeFont:
        """Получение шрифта по ключу с указанным размером и весом"""
        try:
            if weight == "bold":
                # Попытка найти жирный шрифт
                bold_font_key = f"{font_key}_bold"
                if (hasattr(st.session_state, 'font_cache') and
                    st.session_state.font_cache and
                    bold_font_key in st.session_state.font_cache):
                    font_info = st.session_state.font_cache[bold_font_key]
                    if os.path.exists(font_info['path']):
                        return ImageFont.truetype(font_info['path'], int(size))
            
            if (hasattr(st.session_state, 'font_cache') and
                st.session_state.font_cache and
                font_key in st.session_state.font_cache):
                font_info = st.session_state.font_cache[font_key]
                if os.path.exists(font_info['path']):
                    return ImageFont.truetype(font_info['path'], int(size))
        except Exception as e:
            logger.error(f"Ошибка получения шрифта {font_key}: {e}")
        
        return FontManager.load_system_font('system_arial', size, weight)
    
    @staticmethod
    def get_available_fonts() -> List[Dict]:
        """Получение списка доступных шрифтов"""
        fonts = []
        
        system_fonts = [
            {"name": "Arial (системный)", "key": "system_arial", "type": "system"},
            {"name": "Arial Bold (системный)", "key": "system_arial_bold", "type": "system"},
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
    def load_system_font(font_name: str, size: int, weight: str = "normal") -> ImageFont.FreeTypeFont:
        """Загрузка системного шрифта"""
        try:
            if font_name == "system_arial":
                if weight == "bold":
                    try:
                        return ImageFont.truetype("arialbd.ttf", int(size))
                    except:
                        try:
                            font = ImageFont.truetype("arial.ttf", int(size))
                            # Имитация жирного шрифта через увеличение размера
                            return ImageFont.truetype("arial.ttf", int(size * 1.1))
                        except:
                            return ImageFont.load_default()
                else:
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
    """Класс для обработки изображений"""
    
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
    def create_canvas(width: int, height: int, background_color: str = "#FFFFFF") -> Image.Image:
        """Создание холста с заданным фоном"""
        try:
            if background_color.startswith('#'):
                r = int(background_color[1:3], 16)
                g = int(background_color[3:5], 16)
                b = int(background_color[5:7], 16)
                color = (r, g, b, 255)
            else:
                color = (255, 255, 255, 255)
            
            return Image.new('RGBA', (width, height), color)
        except:
            return Image.new('RGBA', (width, height), (255, 255, 255, 255))
    
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
    def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
        """Перенос текста по словам"""
        if not text:
            return []
        
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            
            try:
                if hasattr(font, 'getlength'):
                    width = font.getlength(test_line)
                else:
                    # Для старых версий PIL
                    from PIL import Image, ImageDraw
                    dummy_img = Image.new('RGB', (1, 1))
                    dummy_draw = ImageDraw.Draw(dummy_img)
                    width = dummy_draw.textlength(test_line, font=font)
                
                if width <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            except:
                # Если не удалось измерить текст, используем простой перенос
                if len(' '.join(current_line + [word])) * 10 <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    @staticmethod
    def draw_text_with_background(draw, text: str, position: Tuple[int, int], font: ImageFont.FreeTypeFont, 
                                 text_color: Tuple, bg_color: Optional[Tuple] = None, 
                                 padding: int = 5, corner_radius: int = 5) -> None:
        """Рисование текста с фоном"""
        try:
            if hasattr(draw, 'textbbox'):
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            else:
                text_width, text_height = draw.textsize(text, font=font)
            
            x, y = position
            
            if bg_color:
                # Рисуем закругленный прямоугольник
                rect_x1 = x - padding
                rect_y1 = y - padding
                rect_x2 = x + text_width + padding
                rect_y2 = y + text_height + padding
                
                # Рисуем прямоугольник с закругленными углами
                draw.rounded_rectangle(
                    [rect_x1, rect_y1, rect_x2, rect_y2],
                    radius=corner_radius,
                    fill=bg_color
                )
            
            draw.text((x, y), text, font=font, fill=text_color)
            
        except Exception as e:
            logger.error(f"Ошибка рисования текста: {e}")
            draw.text(position, text, font=font, fill=text_color)
    
    @staticmethod
    def draw_strikethrough_text(draw, text: str, position: Tuple[int, int], font: ImageFont.FreeTypeFont, 
                               text_color: Tuple) -> None:
        """Рисование текста с зачеркиванием"""
        try:
            if hasattr(draw, 'textbbox'):
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                y_offset = bbox[1]
            else:
                text_width, text_height = draw.textsize(text, font=font)
                y_offset = 0
            
            x, y = position
            
            # Рисуем текст
            draw.text((x, y), text, font=font, fill=text_color)
            
            # Рисуем линию зачеркивания
            line_y = y + text_height // 2 - y_offset
            draw.line([x, line_y, x + text_width, line_y], fill=text_color, width=2)
            
        except Exception as e:
            logger.error(f"Ошибка рисования зачеркнутого текста: {e}")
            draw.text(position, text, font=font, fill=text_color)
    
    @staticmethod
    def create_infographic(template_data: Dict, product_data: Dict, product_image: Image.Image) -> Image.Image:
        """Создание инфографики по шаблону"""
        try:
            layout = template_data["layout"]
            colors = template_data["colors"]
            text_elements = template_data["text_elements"]
            
            width = layout["width"]
            height = layout["height"]
            
            # Создаем холст
            canvas = ImageProcessor.create_canvas(width, height, colors["background"])
            draw = ImageDraw.Draw(canvas)
            
            # Настройки фона
            background_settings = safe_get_session_state('background_settings', {})
            
            # Добавляем рамку если нужно
            if background_settings.get('border_width', 0) > 0:
                canvas = ImageProcessor.add_border(
                    canvas, 
                    background_settings.get('border_color', '#E0E0E0'),
                    background_settings.get('border_width', 2)
                )
                draw = ImageDraw.Draw(canvas)
            
            # Добавляем скругленные углы если нужно
            if background_settings.get('corner_radius', 0) > 0:
                canvas = ImageProcessor.add_rounded_corners(
                    canvas, 
                    background_settings.get('corner_radius', 20)
                )
                draw = ImageDraw.Draw(canvas)
            
            # Размещаем изображение товара
            margin = layout.get("margin", 50)
            img_width = layout["product_image_size"]["width"]
            img_height = layout["product_image_size"]["height"]
            
            # Ресайзим изображение товара
            product_image_resized = product_image.resize((img_width, img_height), Image.Resampling.LANCZOS)
            
            # Добавляем изображение на холст
            canvas.paste(product_image_resized, (margin, margin))
            
            # Настройки шрифта
            font_settings = safe_get_session_state('font_settings', {})
            main_font_key = font_settings.get('main_font', 'system_arial')
            font_size_multiplier = font_settings.get('font_size_multiplier', 1.0)
            
            # Обрабатываем и добавляем текстовые элементы
            for element_id, element_config in text_elements.items():
                if element_id in product_data and product_data[element_id]:
                    text = product_data[element_id]
                    
                    # Умная обработка текста если включена
                    if safe_get_session_state('smart_text_processing', True):
                        text = TextProcessor.smart_process_text(element_id, text)
                    
                    if not text:
                        continue
                    
                    position = element_config["position"]
                    font_size = int(element_config.get("font_size", 24) * font_size_multiplier)
                    font_weight = element_config.get("font_weight", "normal")
                    color = element_config.get("color", "#000000")
                    
                    # Конвертируем цвет hex в RGB
                    if color.startswith('#'):
                        r = int(color[1:3], 16)
                        g = int(color[3:5], 16)
                        b = int(color[5:7], 16)
                        text_color = (r, g, b, 255)
                    else:
                        text_color = (0, 0, 0, 255)
                    
                    # Загружаем шрифт
                    try:
                        font = FontManager.get_font(main_font_key, font_size, font_weight)
                    except:
                        font = FontManager.load_system_font('system_arial', font_size, font_weight)
                    
                    # Обработка специальных элементов
                    if element_id == "features" and isinstance(text, list):
                        # Отрисовка списка характеристик
                        y_offset = position["y"]
                        max_lines = element_config.get("max_lines", 5)
                        line_spacing = element_config.get("line_spacing", 10)
                        
                        for i, feature in enumerate(text[:max_lines]):
                            feature_text = f"• {feature}"
                            
                            # Перенос текста если нужно
                            max_width = element_config.get("max_width", 400)
                            lines = ImageProcessor.wrap_text(feature_text, font, max_width)
                            
                            for line in lines:
                                draw.text((position["x"], y_offset), line, font=font, fill=text_color)
                                y_offset += font_size + line_spacing
                    
                    elif element_id == "discount_badge":
                        # Отрисовка бейджа скидки
                        bg_color = element_config.get("background_color", "#FF0000")
                        text_color_bg = element_config.get("text_color", "#FFFFFF")
                        padding = element_config.get("padding", 10)
                        corner_radius = element_config.get("corner_radius", 5)
                        
                        # Конвертируем цвета
                        if bg_color.startswith('#'):
                            r = int(bg_color[1:3], 16)
                            g = int(bg_color[3:5], 16)
                            b = int(bg_color[5:7], 16)
                            bg_color_rgb = (r, g, b, 255)
                        else:
                            bg_color_rgb = (255, 0, 0, 255)
                        
                        if text_color_bg.startswith('#'):
                            r = int(text_color_bg[1:3], 16)
                            g = int(text_color_bg[3:5], 16)
                            b = int(text_color_bg[5:7], 16)
                            text_color_final = (r, g, b, 255)
                        else:
                            text_color_final = (255, 255, 255, 255)
                        
                        ImageProcessor.draw_text_with_background(
                            draw, text, (position["x"], position["y"]), 
                            font, text_color_final, bg_color_rgb, padding, corner_radius
                        )
                    
                    elif element_config.get("strikethrough", False):
                        # Зачеркнутый текст (для старой цены)
                        ImageProcessor.draw_strikethrough_text(
                            draw, text, (position["x"], position["y"]), font, text_color
                        )
                    
                    elif element_config.get("icon"):
                        # Текст с иконкой
                        icon_text = f"{element_config['icon']} {text}"
                        draw.text((position["x"], position["y"]), icon_text, font=font, fill=text_color)
                    
                    else:
                        # Обычный текст с переносом
                        max_width = element_config.get("max_width", 500)
                        max_lines = element_config.get("max_lines", 2)
                        
                        lines = ImageProcessor.wrap_text(text, font, max_width)
                        
                        y_offset = position["y"]
                        for i, line in enumerate(lines[:max_lines]):
                            draw.text((position["x"], y_offset), line, font=font, fill=text_color)
                            y_offset += font_size + 5
            
            # Добавляем тень если нужно
            if background_settings.get('shadow_enabled', True):
                canvas = ImageProcessor.add_shadow_effect(canvas)
            
            return canvas
            
        except Exception as e:
            logger.error(f"Ошибка создания инфографики: {e}")
            # Создаем простой холст в случае ошибки
            return ImageProcessor.create_canvas(1200, 800)
    
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
        
        required_keywords = ['url', 'image', 'name', 'title', 'product', 'price', 'цена']
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
        """Интеллектуальный подбор колонок для маркетплейсов"""
        suggestions = {
            'product_name': None,
            'price': None,
            'old_price': None,
            'discount': None,
            'description': None,
            'features': None,
            'rating': None,
            'reviews': None,
            'image_url': None,
            'filename': None,
            'sku': None,
            'brand': None,
            'category': None,
            'shipping': None,
            'warranty': None,
            'availability': None
        }
        
        if df is None or df.empty:
            return suggestions
        
        column_stats = {}
        
        for col in df.columns:
            col_str = str(col).lower()
            col_data = df[col].dropna().astype(str)
            
            stats = {
                'name': col,
                'has_urls': False,
                'has_text': False,
                'has_numbers': False,
                'unique_count': col_data.nunique(),
                'max_length': col_data.str.len().max() if not col_data.empty else 0,
                'avg_length': col_data.str.len().mean() if not col_data.empty else 0
            }
            
            # Проверка на URL изображений
            url_patterns = ['.jpg', '.jpeg', '.png', '.webp', 'http://', 'https://', 'www.']
            url_count = sum(any(pattern in val.lower() for pattern in url_patterns) 
                          for val in col_data.head(20))
            
            if url_count > 5:
                stats['has_urls'] = True
            
            # Проверка на числовые данные (цены)
            try:
                numeric_data = pd.to_numeric(col_data.str.replace(r'[^\d.]', '', regex=True), errors='coerce')
                numeric_percentage = (numeric_data.notna().sum() / len(col_data)) * 100
                if numeric_percentage > 50:
                    stats['has_numbers'] = True
            except:
                pass
            
            # Проверка на текстовые данные
            text_keywords = ['название', 'name', 'title', 'товар', 'product']
            text_match = any(keyword in col_str for keyword in text_keywords)
            
            if text_match or stats['avg_length'] > 20:
                stats['has_text'] = True
            
            column_stats[col] = stats
        
        # Автоматическое сопоставление на основе содержимого колонок
        for col, stats in column_stats.items():
            col_lower = str(col).lower()
            
            # URL изображения
            if stats['has_urls']:
                suggestions['image_url'] = col
            
            # Название товара
            elif any(keyword in col_lower for keyword in ['название', 'name', 'title', 'товар', 'product']):
                suggestions['product_name'] = col
            
            # Цена
            elif any(keyword in col_lower for keyword in ['цена', 'price', 'стоимость', 'руб', '$', '€', '₽']):
                if 'старая' in col_lower or 'old' in col_lower:
                    suggestions['old_price'] = col
                else:
                    suggestions['price'] = col
            
            # Скидка
            elif any(keyword in col_lower for keyword in ['скидка', 'discount', 'акция', 'sale']):
                suggestions['discount'] = col
            
            # Описание
            elif any(keyword in col_lower for keyword in ['описание', 'description', 'детали']):
                suggestions['description'] = col
            
            # Характеристики
            elif any(keyword in col_lower for keyword in ['характеристики', 'features', 'особенности', 'параметры']):
                suggestions['features'] = col
            
            # Рейтинг
            elif any(keyword in col_lower for keyword in ['рейтинг', 'rating', 'оценка']):
                suggestions['rating'] = col
            
            # Отзывы
            elif any(keyword in col_lower for keyword in ['отзывы', 'reviews', 'комментарии']):
                suggestions['reviews'] = col
            
            # Бренд
            elif any(keyword in col_lower for keyword in ['бренд', 'brand', 'производитель']):
                suggestions['brand'] = col
            
            # Категория
            elif any(keyword in col_lower for keyword in ['категория', 'category', 'раздел']):
                suggestions['category'] = col
            
            # Доставка
            elif any(keyword in col_lower for keyword in ['доставка', 'shipping', 'delivery']):
                suggestions['shipping'] = col
            
            # Гарантия
            elif any(keyword in col_lower for keyword in ['гарантия', 'warranty', 'гарантий']):
                suggestions['warranty'] = col
            
            # Наличие
            elif any(keyword in col_lower for keyword in ['наличие', 'availability', 'в наличии']):
                suggestions['availability'] = col
            
            # Артикул/SKU (для имени файла)
            elif any(keyword in col_lower for keyword in ['артикул', 'sku', 'код', 'id']):
                suggestions['sku'] = col
                suggestions['filename'] = col
        
        # Если не нашли колонку для имени файла, ищем уникальную текстовую колонку
        if suggestions['filename'] is None:
            for col, stats in column_stats.items():
                if stats['unique_count'] == len(df) and stats['max_length'] < 50:
                    suggestions['filename'] = col
                    break
        
        # Заполняем оставшиеся пропуски
        for key in suggestions:
            if suggestions[key] is None:
                for col in df.columns:
                    if col not in suggestions.values():
                        suggestions[key] = col
                        break
        
        return suggestions

# ============================
# ОСНОВНОЙ ГЕНЕРАТОР ИНФОГРАФИКИ
# ============================
class InfographicGenerator:
    """Основной класс для генерации инфографики"""
    
    def __init__(self):
        self.image_processor = ImageProcessor()
    
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
            
            # Получаем URL изображения
            image_url = None
            if column_mapping.get('image_url'):
                url_col = column_mapping['image_url']
                if url_col in row_dict:
                    url_value = row_dict[url_col]
                    if url_value is not None and pd.notna(url_value):
                        url_str = str(url_value).strip()
                        if url_str and len(url_str) > 5:
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
                    'message': f'Нет URL изображения'
                }
            
            # Загружаем изображение
            processing_settings = safe_get_session_state('processing_settings', {})
            timeout = processing_settings.get('timeout', 30)
            retries = processing_settings.get('retry_count', 3)
            
            product_image = self.image_processor.load_image_from_url(
                image_url, 
                timeout=timeout,
                retries=retries
            )
            
            if product_image is None:
                return {
                    'row_index': row_index,
                    'status': 'error',
                    'message': f'Не удалось загрузить изображение',
                    'url': image_url[:100]
                }
            
            # Получаем шаблон
            template_id = safe_get_session_state('current_template', 'amazon_style')
            template = MarketplaceTemplateManager.get_template(template_id)
            
            # Подготавливаем данные продукта
            product_data = {}
            for field, column_name in column_mapping.items():
                if column_name and column_name in row_dict:
                    value = row_dict[column_name]
                    if pd.notna(value) and str(value).strip():
                        # Умная обработка текста если включена
                        if safe_get_session_state('smart_text_processing', True):
                            product_data[field] = TextProcessor.smart_process_text(field, str(value))
                        else:
                            product_data[field] = str(value).strip()
            
            # Особый случай для features (список)
            if 'features' in product_data and column_mapping.get('features'):
                features_text = product_data['features']
                product_data['features'] = TextProcessor.process_features(features_text)
            
            # Генерация имени файла
            filename = f"product_{row_index:04d}"
            
            # Пробуем получить имя из колонки filename
            if column_mapping.get('filename'):
                filename_col = column_mapping['filename']
                if filename_col in row_dict:
                    filename_source = row_dict.get(filename_col)
                    if filename_source is not None and pd.notna(filename_source):
                        filename = get_safe_filename(filename_source)
            
            # Если не нашли в filename, пробуем product_name
            if filename == f"product_{row_index:04d}" and column_mapping.get('product_name'):
                name_col = column_mapping['product_name']
                if name_col in row_dict:
                    name_source = row_dict.get(name_col)
                    if name_source is not None and pd.notna(name_source):
                        filename = get_safe_filename(name_source)
            
            # Создаем инфографику
            infographic = self.image_processor.create_infographic(
                template, product_data, product_image
            )
            
            # Изменяем размер если нужно
            export_settings = safe_get_session_state('export_settings', {})
            if export_settings.get('resize', True):
                target_size = export_settings.get('target_size', 1200)
                infographic = self.image_processor.resize_image(infographic, target_size)
            
            # Сохраняем изображение
            output_dir = safe_get_session_state('local_save_path', safe_get_session_state('output_dir', 'output_infographics'))
            
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
                infographic,
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
                return self.process_single_row(row, idx)
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
            
            uploaded_file = st.file_uploader(
                "Выберите файл",
                type=['xlsx', 'xls', 'xlsm', 'xlsb', 'ods', 'csv'],
                key="file_uploader",
                label_visibility="collapsed"
            )
            
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
                            
                            # Автоматически заполняем маппинг
                            for key in suggestions:
                                if suggestions[key] and key in st.session_state.column_mapping:
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
            
            if st.session_state.df is not None:
                with st.expander("👁️ Предпросмотр данных"):
                    preview_rows = st.slider("Строк", 5, 50, 10, key="preview_rows")
                    st.dataframe(st.session_state.df.head(preview_rows), width='stretch')
            
            st.subheader("💾 Локальное сохранение")
            
            save_path_input = st.text_input(
                "Путь для сохранения файлов",
                value=st.session_state.get('local_save_path', 
                                          os.path.join(os.path.expanduser("~"), "Desktop", "Инфографики")),
                key="save_path_input"
            )
            
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
            
            st.subheader("🎨 Шаблон")
            
            categories = MarketplaceTemplateManager.MARKETPLACE_TEMPLATES
            template_options = []
            template_ids = []
            
            for template_id, template_data in categories.items():
                template_options.append(template_data["name"])
                template_ids.append(template_id)
            
            current_template = st.session_state.get('current_template', 'amazon_style')
            current_index = template_ids.index(current_template) if current_template in template_ids else 0
            
            selected = st.selectbox(
                "Выберите стиль",
                template_options,
                index=current_index,
                key="template_select"
            )
            
            selected_index = template_options.index(selected)
            st.session_state.current_template = template_ids[selected_index]
            
            # Показываем описание шаблона
            template_data = MarketplaceTemplateManager.get_template(st.session_state.current_template)
            st.caption(f"📝 {template_data['description']}")
            
            st.subheader("🎨 Фон")
            
            st.session_state.background_settings['background_color'] = st.color_picker(
                "Цвет фона",
                value=st.session_state.background_settings.get('background_color', '#FFFFFF'),
                key="background_color"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.background_settings['border_width'] = st.slider(
                    "Толщина рамки",
                    0, 10, st.session_state.background_settings.get('border_width', 2),
                    key="border_width"
                )
            
            with col2:
                if st.session_state.background_settings['border_width'] > 0:
                    st.session_state.background_settings['border_color'] = st.color_picker(
                        "Цвет рамки",
                        value=st.session_state.background_settings.get('border_color', '#E0E0E0'),
                        key="border_color"
                    )
            
            st.session_state.background_settings['corner_radius'] = st.slider(
                "Скругление углов",
                0, 50, st.session_state.background_settings.get('corner_radius', 20),
                key="corner_radius"
            )
            
            st.session_state.background_settings['shadow_enabled'] = st.checkbox(
                "Добавить тень",
                value=st.session_state.background_settings.get('shadow_enabled', True),
                key="shadow"
            )
            
            st.subheader("🔤 Шрифты")
            
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
            
            # Загрузка пользовательских шрифтов
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
            
            st.session_state.smart_text_processing = st.checkbox(
                "Умная обработка текста",
                value=st.session_state.get('smart_text_processing', True),
                key="smart_text",
                help="Автоматически форматирует цены, скидки, рейтинги и т.д."
            )
            
            processed_count = safe_get_session_state('processed_count', 0)
            st.caption(f"Обработано: {processed_count}")
            st.caption("Версия: 10.0 (маркетплейсы)")
    
    @staticmethod
    def render_data_quality_tab():
        """Вкладка анализа качества данных"""
        if st.session_state.df is None:
            st.info("📥 Загрузите Excel файл в боковой панели для начала работы")
            return
        
        st.header("📊 Анализ качества данных")
        
        df = st.session_state.df
        
        # Статистика
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
        
        # Анализ колонок
        with st.expander("🔍 Детальный анализ колонок", expanded=True):
            column_info = []
            
            for col in df.columns:
                col_data = df[col].dropna()
                
                info = {
                    'Колонка': col,
                    'Тип': str(df[col].dtype),
                    'Не пустых': len(col_data),
                    'Уникальных': col_data.nunique(),
                    'Заполненность (%)': f"{(len(col_data) / len(df) * 100):.1f}",
                    'Пример': str(col_data.iloc[0])[:30] + "..." if len(col_data) > 0 else "Пусто"
                }
                column_info.append(info)
            
            column_df = pd.DataFrame(column_info)
            st.dataframe(column_df, use_container_width=True)
        
        # Выявление потенциальных проблем
        with st.expander("⚠️ Потенциальные проблемы", expanded=True):
            problems = []
            
            # Проверка на полностью пустые колонки
            for col in df.columns:
                if df[col].isna().all() or (df[col].astype(str).str.strip() == '').all():
                    problems.append(f"Колонка '{col}' полностью пустая")
            
            # Проверка на дубликаты в ключевых полях
            for col in df.columns:
                col_lower = str(col).lower()
                if any(keyword in col_lower for keyword in ['id', 'sku', 'артикул', 'код']):
                    if df[col].duplicated().any():
                        problems.append(f"Колонка '{col}' содержит дубликаты")
            
            # Проверка на URL колонки
            url_columns = []
            for col in df.columns:
                col_lower = str(col).lower()
                if any(keyword in col_lower for keyword in ['url', 'link', 'image', 'фото']):
                    url_columns.append(col)
            
            if not url_columns:
                problems.append("Не найдены колонки с URL изображений")
            
            if problems:
                for problem in problems:
                    st.warning(problem)
            else:
                st.success("✅ Критических проблем не обнаружено")
    
    @staticmethod
    def render_column_mapping_tab():
        """Вкладка настройки маппинга колонок"""
        if st.session_state.df is None:
            st.info("📥 Загрузите Excel файл в боковой панели для начала работы")
            return
        
        st.header("🔗 Настройка маппинга колонок")
        
        df = st.session_state.df
        available_columns = df.columns.tolist()
        
        st.info("📋 Сопоставьте колонки из вашего файла с полями для инфографики")
        
        # Автоподбор
        if st.button("🎯 Автоподбор колонок", type="primary"):
            suggestions = AdvancedExcelProcessor.get_intelligent_column_suggestions(df)
            for key in suggestions:
                if suggestions[key] and key in st.session_state.column_mapping:
                    st.session_state.column_mapping[key] = suggestions[key]
            st.success("✅ Колонки подобраны автоматически!")
            st.rerun()
        
        # Основные поля
        st.subheader("🎯 Основные поля")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Название товара
            current = st.session_state.column_mapping.get('product_name')
            index = available_columns.index(current) if current in available_columns else 0
            st.session_state.column_mapping['product_name'] = st.selectbox(
                "Название товара",
                available_columns,
                index=index,
                key="col_product_name",
                help="Название товара для отображения"
            )
            
            # Цена
            current = st.session_state.column_mapping.get('price')
            index = available_columns.index(current) if current in available_columns else min(1, len(available_columns)-1)
            st.session_state.column_mapping['price'] = st.selectbox(
                "Цена",
                available_columns,
                index=index,
                key="col_price",
                help="Текущая цена товара"
            )
            
            # Старая цена
            current = st.session_state.column_mapping.get('old_price')
            index = available_columns.index(current) if current in available_columns else min(2, len(available_columns)-1)
            st.session_state.column_mapping['old_price'] = st.selectbox(
                "Старая цена",
                available_columns,
                index=index,
                key="col_old_price",
                help="Цена до скидки (для отображения зачеркнутой)"
            )
            
            # Скидка
            current = st.session_state.column_mapping.get('discount')
            index = available_columns.index(current) if current in available_columns else min(3, len(available_columns)-1)
            st.session_state.column_mapping['discount'] = st.selectbox(
                "Скидка",
                available_columns,
                index=index,
                key="col_discount",
                help="Размер скидки в %"
            )
        
        with col2:
            # URL изображения
            current = st.session_state.column_mapping.get('image_url')
            index = available_columns.index(current) if current in available_columns else min(4, len(available_columns)-1)
            st.session_state.column_mapping['image_url'] = st.selectbox(
                "URL изображения",
                available_columns,
                index=index,
                key="col_image_url",
                help="Ссылка на изображение товара"
            )
            
            # Имя файла
            current = st.session_state.column_mapping.get('filename')
            index = available_columns.index(current) if current in available_columns else min(5, len(available_columns)-1)
            st.session_state.column_mapping['filename'] = st.selectbox(
                "Имя файла",
                available_columns,
                index=index,
                key="col_filename",
                help="Колонка для именования файлов (артикул, SKU или название)"
            )
            
            # Рейтинг
            current = st.session_state.column_mapping.get('rating')
            index = available_columns.index(current) if current in available_columns else min(6, len(available_columns)-1)
            st.session_state.column_mapping['rating'] = st.selectbox(
                "Рейтинг",
                available_columns,
                index=index,
                key="col_rating",
                help="Рейтинг товара (например: 4.5)"
            )
            
            # Описание
            current = st.session_state.column_mapping.get('description')
            index = available_columns.index(current) if current in available_columns else min(7, len(available_columns)-1)
            st.session_state.column_mapping['description'] = st.selectbox(
                "Описание",
                available_columns,
                index=index,
                key="col_description",
                help="Краткое описание товара"
            )
        
        # Дополнительные поля
        st.subheader("📝 Дополнительные поля")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Характеристики
            current = st.session_state.column_mapping.get('features')
            index = available_columns.index(current) if current in available_columns else min(8, len(available_columns)-1)
            st.session_state.column_mapping['features'] = st.selectbox(
                "Характеристики",
                available_columns,
                index=index,
                key="col_features",
                help="Характеристики товара (разделенные ; или |)"
            )
            
            # Бренд
            current = st.session_state.column_mapping.get('brand')
            index = available_columns.index(current) if current in available_columns else min(9, len(available_columns)-1)
            st.session_state.column_mapping['brand'] = st.selectbox(
                "Бренд",
                available_columns,
                index=index,
                key="col_brand"
            )
            
            # Категория
            current = st.session_state.column_mapping.get('category')
            index = available_columns.index(current) if current in available_columns else min(10, len(available_columns)-1)
            st.session_state.column_mapping['category'] = st.selectbox(
                "Категория",
                available_columns,
                index=index,
                key="col_category"
            )
        
        with col2:
            # Доставка
            current = st.session_state.column_mapping.get('shipping')
            index = available_columns.index(current) if current in available_columns else min(11, len(available_columns)-1)
            st.session_state.column_mapping['shipping'] = st.selectbox(
                "Доставка",
                available_columns,
                index=index,
                key="col_shipping"
            )
            
            # Гарантия
            current = st.session_state.column_mapping.get('warranty')
            index = available_columns.index(current) if current in available_columns else min(12, len(available_columns)-1)
            st.session_state.column_mapping['warranty'] = st.selectbox(
                "Гарантия",
                available_columns,
                index=index,
                key="col_warranty"
            )
            
            # Наличие
            current = st.session_state.column_mapping.get('availability')
            index = available_columns.index(current) if current in available_columns else min(13, len(available_columns)-1)
            st.session_state.column_mapping['availability'] = st.selectbox(
                "Наличие",
                available_columns,
                index=index,
                key="col_availability"
            )
        
        # Предпросмотр сопоставления
        with st.expander("👁️ Предпросмотр данных", expanded=True):
            if len(df) > 0:
                preview_data = {}
                for field, col in st.session_state.column_mapping.items():
                    if col and col in df.columns and len(df) > 0:
                        value = df.iloc[0][col]
                        if pd.notna(value) and str(value).strip():
                            if field == 'features':
                                processed = TextProcessor.process_features(str(value))
                                preview_data[field] = processed[:3]  # Показываем только 3 первые характеристики
                            else:
                                preview_data[field] = TextProcessor.smart_process_text(field, str(value))
                
                st.json(preview_data)
    
    @staticmethod
    def render_preview_tab(generator):
        """Вкладка предпросмотра"""
        if st.session_state.df is None:
            st.info("📥 Загрузите Excel файл в боковой панели для начала работы")
            return
        
        st.header("🎯 Предпросмотр инфографики")
        
        df = st.session_state.df
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.info(f"📊 Всего строк: {len(df)}")
        
        with col2:
            test_row = st.number_input(
                "Номер строки",
                0, len(df)-1, st.session_state.get('current_preview_row', 0),
                key="test_row"
            )
            st.session_state.current_preview_row = test_row
        
        with col3:
            st.write("")
            st.write("")
            test_button = st.button("🔄 Обновить предпросмотр", type="primary", width='stretch')
        
        if test_button or 'preview_generated' not in st.session_state:
            st.session_state.preview_generated = True
            
            with st.spinner("Создание предпросмотра..."):
                row = df.iloc[test_row]
                
                # Получаем данные
                column_mapping = st.session_state.column_mapping
                product_data = {}
                
                for field, column_name in column_mapping.items():
                    if column_name and column_name in row:
                        value = row[column_name]
                        if pd.notna(value) and str(value).strip():
                            if st.session_state.smart_text_processing:
                                product_data[field] = TextProcessor.smart_process_text(field, str(value))
                            else:
                                product_data[field] = str(value).strip()
                
                # Особый случай для features
                if 'features' in product_data and column_mapping.get('features'):
                    features_text = product_data['features']
                    product_data['features'] = TextProcessor.process_features(features_text)
                
                # Получаем URL изображения
                image_url = None
                if column_mapping.get('image_url'):
                    url_col = column_mapping['image_url']
                    if url_col in row:
                        url_value = row[url_col]
                        if url_value is not None and pd.notna(url_value):
                            url_str = str(url_value).strip()
                            if url_str:
                                if url_str.startswith('//'):
                                    image_url = 'https:' + url_str
                                elif url_str.startswith('www.'):
                                    image_url = 'https://' + url_str
                                else:
                                    image_url = url_str
                
                # Показываем данные
                with st.expander("📋 Данные строки", expanded=True):
                    st.json(product_data)
                    
                    if image_url:
                        st.write(f"**URL изображения:** {image_url[:100]}..." if len(image_url) > 100 else f"**URL изображения:** {image_url}")
                    
                    # Показываем имя файла
                    filename = f"product_{test_row:04d}"
                    if column_mapping.get('filename'):
                        filename_col = column_mapping['filename']
                        if filename_col in row:
                            filename_source = row.get(filename_col)
                            if filename_source is not None and pd.notna(filename_source):
                                filename = get_safe_filename(filename_source)
                    
                    st.write(f"**Имя файла:** `{filename}`")
                
                if image_url:
                    # Загружаем изображение
                    product_image = generator.image_processor.load_image_from_url(image_url, timeout=15)
                    
                    if product_image:
                        # Получаем шаблон
                        template_id = st.session_state.current_template
                        template = MarketplaceTemplateManager.get_template(template_id)
                        
                        # Создаем инфографику
                        infographic = generator.image_processor.create_infographic(
                            template, product_data, product_image
                        )
                        
                        # Показываем результат
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("📷 Оригинал")
                            st.image(product_image, width='stretch')
                            st.caption(f"{product_image.width}×{product_image.height}")
                        
                        with col2:
                            st.subheader("🎨 Инфографика")
                            st.image(infographic, width='stretch')
                            st.caption(f"Стиль: {template['name']}")
                        
                        # Сохраняем для скачивания
                        buffered = BytesIO()
                        format_ = st.session_state.export_settings.get('format', 'PNG')
                        
                        if format_ == 'JPEG':
                            infographic.convert('RGB').save(buffered, format='JPEG',
                                                          quality=st.session_state.export_settings.get('quality', 95))
                            mime = 'image/jpeg'
                        elif format_ == 'WEBP':
                            infographic.save(buffered, format='WEBP',
                                           quality=st.session_state.export_settings.get('quality', 95))
                            mime = 'image/webp'
                        else:
                            infographic.save(buffered, format='PNG')
                            mime = 'image/png'
                        
                        st.download_button(
                            label="💾 Скачать изображение",
                            data=buffered.getvalue(),
                            file_name=f"{filename}.{format_.lower()}",
                            mime=mime,
                            width='stretch'
                        )
                        
                        st.session_state.preview_image = infographic
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
                st.warning("⚠️ Не удалось проверить права доступа к папку")
        else:
            st.error("❌ **Не выбрана папка для сохранения!** Укажите путь в настройках.")
            return
        
        df = st.session_state.df
        total_rows = len(df)
        
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
        
        # Информация о именовании файлов
        if st.session_state.column_mapping.get('filename'):
            filename_col = st.session_state.column_mapping['filename']
            if filename_col in df.columns:
                sample_names = []
                for i in range(min(3, len(df))):
                    name = df.iloc[i].get(filename_col)
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
                results = generator.process_batch(df, start_idx, end_idx)
            
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
                        if errors:
                            for error in errors[:10]:  # Показываем только первые 10 ошибок
                                st.error(f"Строка {error.get('row_index')}: {error.get('message')}")
                
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
    def render_templates_tab():
        """Вкладка шаблонов"""
        st.header("🎨 Шаблоны")
        
        categories = MarketplaceTemplateManager.MARKETPLACE_TEMPLATES
        
        # Показываем все шаблоны в виде карточек
        for template_id, template_data in categories.items():
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.subheader(template_data["name"])
                    st.caption(template_data["description"])
                    
                    # Показываем цвета шаблона
                    colors = template_data["colors"]
                    color_html = """
                    <div style="display: flex; gap: 10px; margin: 10px 0;">
                    """
                    for color_name, color_value in colors.items():
                        color_html += f"""
                        <div style="display: flex; align-items: center; gap: 5px;">
                            <div style="width: 20px; height: 20px; background-color: {color_value}; border-radius: 3px; border: 1px solid #ccc;"></div>
                            <small>{color_name}</small>
                        </div>
                        """
                    color_html += "</div>"
                    st.markdown(color_html, unsafe_allow_html=True)
                
                with col2:
                    if st.button(f"Выбрать", key=f"select_{template_id}"):
                        st.session_state.current_template = template_id
                        st.success(f"✅ Выбран шаблон: {template_data['name']}")
                        st.rerun()
                
                st.divider()

# ============================
# ОСНОВНОЙ КОД ПРИЛОЖЕНИЯ
# ============================
def initialize_application():
    """Инициализация приложения"""
    try:
        ensure_session_state_initialized()
        
        os.makedirs("output_infographics", exist_ok=True)
        
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
    
    st.title("🚀 Генератор Инфографики PRO v10.0")
    st.markdown("---")
    
    st.caption("🆕 Версия 10.0: Оптимизированная работа с текстом как в современных программах для маркетплейсов")
    
    tab_names = [
        "📊 Анализ данных",
        "🔗 Настройка колонок",
        "🎯 Предпросмотр",
        "⚡ Обработка",
        "🎨 Шаблоны"
    ]
    
    tabs = st.tabs(tab_names)
    
    generator = InfographicGenerator()
    
    UIComponents.render_sidebar()
    
    with tabs[0]:
        UIComponents.render_data_quality_tab()
    
    with tabs[1]:
        UIComponents.render_column_mapping_tab()
    
    with tabs[2]:
        UIComponents.render_preview_tab(generator)
    
    with tabs[3]:
        UIComponents.render_processing_tab(generator)
    
    with tabs[4]:
        UIComponents.render_templates_tab()

def main():
    """Основная функция приложения"""
    try:
        if not hasattr(st.session_state, 'app_initialized') or not st.session_state.app_initialized:
            st.markdown("""
            <div style="text-align: center; padding: 100px;">
                <h1>🎯 Генератор Инфографики PRO v10.0</h1>
                <p>Профессиональный инструмент для создания инфографики для маркетплейсов</p>
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
