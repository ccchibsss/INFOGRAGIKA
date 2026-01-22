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

# ============================
# НАСТРОЙКА ПРИЛОЖЕНИЯ
# ============================
st.set_page_config(
   page_title="🎯 Генератор Инфографики v4.0 - Расширенная версия",
   page_icon="🎨",
   layout="wide",
   initial_sidebar_state="expanded"
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
       'current_template': 'standard',
       'column_mapping': {},
       'output_dir': 'output_infographics',
       'batch_results': [],
       'image_cache': {},
       'font_cache': {},  # Кэш для загруженных шрифтов
       'uploaded_fonts': [],  # Список загруженных шрифтов
       'preview_image': None,
       'uploaded_file_name': None,
       'export_settings': {
           'format': 'PNG',
           'quality': 85,
           'resize': True,
           'target_size': 1200
       },
       'processing_settings': {
           'batch_size': 100,
           'max_workers': 8,
           'timeout': 15,
           'retry_count': 2
       },
       'text_offset_settings': {
           'top_left': {'x_offset': 0, 'y_offset': 0},
           'top_right': {'x_offset': 0, 'y_offset': 0},
           'bottom_left': {'x_offset': 0, 'y_offset': 0},
           'bottom_right': {'x_offset': 0, 'y_offset': 0}
       },
       'image_overlay_settings': {  # Настройки для наложения изображений
           'enabled': False,
           'position': 'center',
           'scale': 100,
           'opacity': 100,
           'x_offset': 0,
           'y_offset': 0,
           'max_width': 50,
           'max_height': 50
       },
       'symmetrical_offsets': False,
       'font_settings': {  # Настройки шрифтов
           'main_font': 'system_arial',
           'bold_font': 'system_arial',
           'font_size_multiplier': 1.0,
           'auto_font_selection': True
       }
   }
   for key, value in defaults.items():
       if key not in st.session_state:
           st.session_state[key] = value

# Инициализация в начале запуска приложения
init_session_state()

# ============================
# КОНСТАНТЫ И ШАБЛОНЫ
# ============================
class InfographicTemplates:
   """Класс для управления шаблонами инфографики"""
   TEMPLATES = {
       "standard": {
           "name": "📋 Стандартный",
           "description": "Универсальный шаблон для большинства товаров",
           "text_positions": {
               "top_left": {"x": 0.05, "y": 0.05, "align": "left", "max_width": 0.4},
               "top_right": {"x": 0.95, "y": 0.05, "align": "right", "max_width": 0.4},
               "bottom_left": {"x": 0.05, "y": 0.85, "align": "left", "max_width": 0.4},
               "bottom_right": {"x": 0.95, "y": 0.85, "align": "right", "max_width": 0.4}
           },
           "image_positions": {  # Позиции для наложения изображений
               "center": {"x": 0.5, "y": 0.5, "anchor": "center"},
               "top_center": {"x": 0.5, "y": 0.1, "anchor": "center"},
               "bottom_center": {"x": 0.5, "y": 0.9, "anchor": "center"}
           },
           "font_sizes": {
               "top_left": 36,
               "top_right": 32,
               "bottom_left": 24,
               "bottom_right": 24
           },
           "colors": {
               "text": (255, 255, 255, 255),
               "shadow": (0, 0, 0, 180),
               "highlight": (255, 215, 0, 255)
           },
           "effects": {
               "shadow": True,
               "background": False,
               "border": False
           }
       },
       "premium": {
           "name": "⭐ Премиум",
           "description": "Сдержанный дизайн для премиальных товаров",
           "text_positions": {
               "top_left": {"x": 0.1, "y": 0.08, "align": "left", "max_width": 0.8},
               "top_right": {"x": 0.9, "y": 0.08, "align": "right", "max_width": 0.3},
               "bottom_left": {"x": 0.1, "y": 0.88, "align": "left", "max_width": 0.8},
               "bottom_right": {"x": 0.9, "y": 0.88, "align": "right", "max_width": 0.3}
           },
           "image_positions": {
               "center": {"x": 0.5, "y": 0.5, "anchor": "center"},
               "top_right": {"x": 0.85, "y": 0.15, "anchor": "center"},
               "bottom_left": {"x": 0.15, "y": 0.85, "anchor": "center"}
           },
           "font_sizes": {
               "top_left": 32,
               "top_right": 28,
               "bottom_left": 20,
               "bottom_right": 20
           },
           "colors": {
               "text": (255, 255, 255, 230),
               "shadow": (0, 0, 0, 150),
               "highlight": (220, 220, 220, 255)
           },
           "effects": {
               "shadow": True,
               "background": True,
               "border": True
           }
       },
       "promo": {
           "name": "🔥 Акционный",
           "description": "Яркий шаблон для распродаж и акций",
           "text_positions": {
               "top_left": {"x": 0.05, "y": 0.05, "align": "left", "max_width": 0.45},
               "top_right": {"x": 0.95, "y": 0.05, "align": "right", "max_width": 0.45},
               "bottom_left": {"x": 0.05, "y": 0.9, "align": "left", "max_width": 0.45},
               "bottom_right": {"x": 0.95, "y": 0.9, "align": "right", "max_width": 0.45}
           },
           "image_positions": {
               "center": {"x": 0.5, "y": 0.5, "anchor": "center"},
               "top_left": {"x": 0.15, "y": 0.15, "anchor": "center"},
               "bottom_right": {"x": 0.85, "y": 0.85, "anchor": "center"}
           },
           "font_sizes": {
               "top_left": 40,
               "top_right": 42,
               "bottom_left": 26,
               "bottom_right": 26
           },
           "colors": {
               "text": (255, 255, 0, 255),
               "shadow": (255, 0, 0, 180),
               "highlight": (255, 255, 255, 255)
           },
           "effects": {
               "shadow": True,
               "background": True,
               "border": False
           }
       },
       "vertical": {
           "name": "📱 Вертикальный",
           "description": "Оптимизирован для Instagram Stories",
           "text_positions": {
               "top_left": {"x": 0.1, "y": 0.05, "align": "center", "max_width": 0.8},
               "top_right": {"x": 0.5, "y": 0.15, "align": "center", "max_width": 0.8},
               "bottom_left": {"x": 0.1, "y": 0.8, "align": "left", "max_width": 0.8},
               "bottom_right": {"x": 0.9, "y": 0.9, "align": "right", "max_width": 0.8}
           },
           "image_positions": {
               "center": {"x": 0.5, "y": 0.5, "anchor": "center"},
               "top": {"x": 0.5, "y": 0.3, "anchor": "center"},
               "bottom": {"x": 0.5, "y": 0.7, "anchor": "center"}
           },
           "font_sizes": {
               "top_left": 32,
               "top_right": 28,
               "bottom_left": 22,
               "bottom_right": 20
           },
           "colors": {
               "text": (255, 255, 255, 255),
               "shadow": (0, 0, 0, 200),
               "highlight": (135, 206, 250, 255)
           },
           "effects": {
               "shadow": True,
               "background": False,
               "border": False
           }
       }
   }
   
   @classmethod
   def get_template_names(cls):
       """Получить список доступных шаблонов"""
       return list(cls.TEMPLATES.keys())
   
   @classmethod
   def get_template_display_name(cls, template_id):
       """Получить отображаемое имя шаблона"""
       return cls.TEMPLATES[template_id]["name"]

# ============================
# УТИЛИТЫ ДЛЯ РАБОТЫ С ИЗОБРАЖЕНИЯМИ И ШРИФТАМИ
# ============================
class FontManager:
   """Класс для управления шрифтами"""
   
   @staticmethod
   def load_font_from_file(uploaded_file):
       """Загрузка шрифта из файла"""
       try:
           # Создаем временный файл для шрифта
           with tempfile.NamedTemporaryFile(delete=False, suffix='.ttf') as tmp_file:
               tmp_file.write(uploaded_file.getvalue())
               tmp_path = tmp_file.name
           
           # Пробуем загрузить шрифт
           try:
               font = ImageFont.truetype(tmp_path, 24)
               font_name = uploaded_file.name
               
               # Сохраняем шрифт в кэш
               font_key = hashlib.md5(uploaded_file.getvalue()).hexdigest()
               
               if 'font_cache' not in st.session_state:
                   st.session_state['font_cache'] = {}
               
               if 'uploaded_fonts' not in st.session_state:
                   st.session_state['uploaded_fonts'] = []
               
               # Сохраняем информацию о шрифте
               font_info = {
                   'name': font_name,
                   'path': tmp_path,
                   'key': font_key,
                   'size': 24
               }
               
               st.session_state.font_cache[font_key] = font_info
               
               # Добавляем в список загруженных шрифтов
               if font_name not in [f['name'] for f in st.session_state.uploaded_fonts]:
                   st.session_state.uploaded_fonts.append(font_info)
               
               return font_key, font_name
           except Exception as e:
               logger.error(f"Ошибка загрузки шрифта {uploaded_file.name}: {e}")
               # Пробуем загрузить как OTF
               try:
                   font = ImageFont.truetype(tmp_path, 24)
                   return font_key, uploaded_file.name
               except:
                   return None, None
       except Exception as e:
           logger.error(f"Ошибка обработки файла шрифта: {e}")
           return None, None
   
   @staticmethod
   def get_font(font_key, size):
       """Получение шрифта по ключу с указанным размером"""
       try:
           if font_key in st.session_state.get('font_cache', {}):
               font_info = st.session_state.font_cache[font_key]
               return ImageFont.truetype(font_info['path'], size)
       except Exception as e:
           logger.error(f"Ошибка получения шрифта: {e}")
       
       # Возвращаем стандартный шрифт в случае ошибки
       try:
           return ImageFont.load_default(size=size)
       except:
           return ImageFont.load_default()
   
   @staticmethod
   def get_available_fonts():
       """Получение списка доступных шрифтов"""
       fonts = []
       
       # Системные шрифты
       system_fonts = [
           {"name": "Arial (системный)", "key": "system_arial", "type": "system"},
           {"name": "Helvetica (системный)", "key": "system_helvetica", "type": "system"},
           {"name": "Times New Roman (системный)", "key": "system_times", "type": "system"}
       ]
       
       # Загруженные пользователем шрифты
       if 'uploaded_fonts' in st.session_state:
           for font_info in st.session_state.uploaded_fonts:
               fonts.append({
                   "name": f"📁 {font_info['name']}",
                   "key": font_info['key'],
                   "type": "uploaded"
               })
       
       return system_fonts + fonts
   
   @staticmethod
   def load_system_font(font_name, size):
       """Загрузка системного шрифта"""
       try:
           font_paths = {
               "system_arial": [
                   "C:/Windows/Fonts/arial.ttf",
                   "/System/Library/Fonts/Helvetica.ttc",
                   "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
               ],
               "system_helvetica": [
                   "/System/Library/Fonts/Helvetica.ttc",
                   "C:/Windows/Fonts/arial.ttf"
               ],
               "system_times": [
                   "C:/Windows/Fonts/times.ttf",
                   "/System/Library/Fonts/Times New Roman.ttf"
               ]
           }
           
           if font_name in font_paths:
               for path in font_paths[font_name]:
                   if os.path.exists(path):
                       return ImageFont.truetype(path, size)
       except Exception as e:
           logger.error(f"Ошибка загрузки системного шрифта {font_name}: {e}")
       
       # Возвращаем стандартный шрифт
       try:
           return ImageFont.load_default(size=size)
       except:
           return ImageFont.load_default()

class ImageProcessor:
   """Класс для обработки изображений"""
   
   @staticmethod
   def load_image_from_url(url, timeout=15, retries=2):
       """Загрузка изображения по URL с повторными попытками"""
       for attempt in range(retries + 1):
           try:
               response = requests.get(
                   url,
                   timeout=timeout,
                   headers={'User-Agent': 'Mozilla/5.0'}
               )
               response.raise_for_status()
               img = Image.open(BytesIO(response.content))
               if img.mode != 'RGBA':
                   img = img.convert('RGBA')
               if 'image_cache' not in st.session_state:
                   st.session_state['image_cache'] = {}
               cache = st.session_state['image_cache']
               cache_key = hashlib.md5(url.encode()).hexdigest()
               cache[cache_key] = img.copy()
               return img
           except Exception as e:
               if attempt == retries:
                   logger.error(f"Не удалось загрузить изображение {url}: {e}")
                   return None
               time.sleep(1)
       return None
   
   @staticmethod
   def load_overlay_image(image_source):
       """Загрузка изображения для наложения"""
       try:
           if isinstance(image_source, str):
               # Если это URL
               if image_source.startswith(('http://', 'https://')):
                   return ImageProcessor.load_image_from_url(image_source)
               # Если это base64
               elif image_source.startswith('data:image'):
                   return ImageProcessor.load_image_from_base64(image_source)
               else:
                   # Пробуем как путь к файлу
                   if os.path.exists(image_source):
                       img = Image.open(image_source)
                       if img.mode != 'RGBA':
                           img = img.convert('RGBA')
                       return img
           # Если это уже объект Image
           elif isinstance(image_source, Image.Image):
               return image_source.copy()
           
           return None
       except Exception as e:
           logger.error(f"Ошибка загрузки изображения для наложения: {e}")
           return None
   
   @staticmethod
   def load_image_from_base64(base64_string):
       """Загрузка изображения из base64 строки"""
       try:
           # Удаляем префикс data:image
           if ',' in base64_string:
               base64_data = base64_string.split(',')[1]
           else:
               base64_data = base64_string
           
           image_data = base64.b64decode(base64_data)
           img = Image.open(BytesIO(image_data))
           if img.mode != 'RGBA':
               img = img.convert('RGBA')
           return img
       except Exception as e:
           logger.error(f"Ошибка загрузки изображения из base64: {e}")
           return None
   
   @staticmethod
   def resize_image(img, target_size=1200):
       """Изменение размера изображения с сохранением пропорций"""
       if img is None:
           return None
           
       if img.width > target_size or img.height > target_size:
           ratio = min(target_size / img.width, target_size / img.height)
           new_size = (int(img.width * ratio), int(img.height * ratio))
           # Используем LANCZOS для высококачественного ресайза
           img = img.resize(new_size, Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
       return img
   
   @staticmethod
   def add_text_to_image(img, text_data, template_id="standard", text_offsets=None, font_settings=None):
       """Добавление текста на изображение по шаблону с учетом смещений и шрифтов"""
       if img is None:
           return None
           
       template = InfographicTemplates.TEMPLATES.get(template_id, InfographicTemplates.TEMPLATES["standard"])
       draw = ImageDraw.Draw(img)
       
       # Получение настроек шрифта
       if font_settings is None:
           font_settings = st.session_state.get('font_settings', {})
       
       # Загрузка шрифтов
       main_font_key = font_settings.get('main_font', 'system_arial')
       bold_font_key = font_settings.get('bold_font', main_font_key)
       font_size_multiplier = font_settings.get('font_size_multiplier', 1.0)
       
       # Если offsets не переданы, используем значения по умолчанию
       if text_offsets is None:
           text_offsets = st.session_state.get('text_offset_settings', {
               'top_left': {'x_offset': 0, 'y_offset': 0},
               'top_right': {'x_offset': 0, 'y_offset': 0},
               'bottom_left': {'x_offset': 0, 'y_offset': 0},
               'bottom_right': {'x_offset': 0, 'y_offset': 0}
           })
       
       # Обработка каждого текстового элемента с учетом смещений
       for position_key, position_data in template.get("text_positions", {}).items():
           if position_key in text_data and text_data[position_key]:
               text = str(text_data[position_key])
               if not text.strip():
                   continue
               
               # Получаем базовые координаты из шаблона
               base_x = position_data["x"] * img.width
               base_y = position_data["y"] * img.height
               
               # Применяем смещения
               if position_key in text_offsets:
                   offset_x = text_offsets[position_key].get('x_offset', 0)
                   offset_y = text_offsets[position_key].get('y_offset', 0)
                   
                   if abs(offset_x) <= 100:  # Проценты
                       base_x += offset_x * img.width / 100
                   else:  # Пиксели
                       base_x += offset_x
                       
                   if abs(offset_y) <= 100:  # Проценты
                       base_y += offset_y * img.height / 100
                   else:  # Пиксели
                       base_y += offset_y
               
               x = int(base_x)
               y = int(base_y)
               
               # Выбираем шрифт и размер
               font_size = int(template["font_sizes"].get(position_key, 24) * font_size_multiplier)
               
               # Выбираем шрифт в зависимости от позиции
               if position_key in ['top_left', 'top_right'] and bold_font_key != main_font_key:
                   # Для заголовков используем жирный шрифт если он отличается
                   try:
                       if bold_font_key.startswith('system_'):
                           font = FontManager.load_system_font(bold_font_key, font_size)
                       else:
                           font = FontManager.get_font(bold_font_key, font_size)
                   except:
                       font = FontManager.load_system_font('system_arial', font_size)
               else:
                   # Для остального текста используем основной шрифт
                   try:
                       if main_font_key.startswith('system_'):
                           font = FontManager.load_system_font(main_font_key, font_size)
                       else:
                           font = FontManager.get_font(main_font_key, font_size)
                   except:
                       font = FontManager.load_system_font('system_arial', font_size)
               
               # Добавляем тень
               if template["effects"].get("shadow", True):
                   shadow_color = template["colors"].get("shadow", (0, 0, 0, 180))
                   draw.text((x+2, y+2), text, font=font, fill=shadow_color)
               
               # Добавляем основной текст
               text_color = template["colors"].get("text", (255, 255, 255, 255))
               draw.text((x, y), text, font=font, fill=text_color,
                        align=position_data.get("align", "left"))
       
       return img
   
   @staticmethod
   def add_image_overlay(background_img, overlay_img, overlay_settings, template_id="standard"):
       """Добавление изображения поверх основного"""
       if background_img is None or overlay_img is None:
           return background_img
       
       try:
           # Создаем копию изображения
           result_img = background_img.copy()
           
           # Получаем настройки позиции из шаблона
           template = InfographicTemplates.TEMPLATES.get(template_id, InfographicTemplates.TEMPLATES["standard"])
           
           if overlay_settings.get('position') in template.get('image_positions', {}):
               position_data = template['image_positions'][overlay_settings['position']]
           else:
               # Позиция по умолчанию
               position_data = {"x": 0.5, "y": 0.5, "anchor": "center"}
           
           # Рассчитываем размеры накладываемого изображения
           max_width_px = int(background_img.width * overlay_settings.get('max_width', 50) / 100)
           max_height_px = int(background_img.height * overlay_settings.get('max_height', 50) / 100)
           
           # Изменяем размер накладываемого изображения
           scale = overlay_settings.get('scale', 100) / 100
           overlay_ratio = min(max_width_px / overlay_img.width, max_height_px / overlay_img.height)
           new_width = int(overlay_img.width * overlay_ratio * scale)
           new_height = int(overlay_img.height * overlay_ratio * scale)
           
           if new_width > 0 and new_height > 0:
               overlay_resized = overlay_img.resize((new_width, new_height), 
                                                   Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
               
               # Применяем прозрачность
               opacity = overlay_settings.get('opacity', 100)
               if opacity < 100:
                   overlay_resized = ImageProcessor.apply_opacity(overlay_resized, opacity)
               
               # Рассчитываем позицию
               base_x = position_data["x"] * background_img.width
               base_y = position_data["y"] * background_img.height
               
               # Применяем смещения
               base_x += overlay_settings.get('x_offset', 0) * background_img.width / 100
               base_y += overlay_settings.get('y_offset', 0) * background_img.height / 100
               
               # Применяем якорь (anchor)
               anchor = position_data.get("anchor", "center")
               if anchor == "center":
                   x = int(base_x - new_width / 2)
                   y = int(base_y - new_height / 2)
               elif anchor == "top_left":
                   x = int(base_x)
                   y = int(base_y)
               elif anchor == "top_right":
                   x = int(base_x - new_width)
                   y = int(base_y)
               elif anchor == "bottom_left":
                   x = int(base_x)
                   y = int(base_y - new_height)
               elif anchor == "bottom_right":
                   x = int(base_x - new_width)
                   y = int(base_y - new_height)
               else:
                   x = int(base_x - new_width / 2)
                   y = int(base_y - new_height / 2)
               
               # Накладываем изображение
               if overlay_resized.mode != 'RGBA':
                   overlay_resized = overlay_resized.convert('RGBA')
               
               result_img.paste(overlay_resized, (x, y), overlay_resized)
           
           return result_img
       except Exception as e:
           logger.error(f"Ошибка при наложении изображения: {e}")
           return background_img
   
   @staticmethod
   def apply_opacity(img, opacity):
       """Применение прозрачности к изображению"""
       if img.mode != 'RGBA':
           img = img.convert('RGBA')
       
       # Создаем маску с прозрачностью
       alpha = img.split()[3]
       alpha = alpha.point(lambda p: p * opacity / 100)
       
       img.putalpha(alpha)
       return img
   
   @staticmethod
   def save_image(img, filepath, format='PNG', quality=85):
       """Сохранение изображения в файл"""
       try:
           os.makedirs(os.path.dirname(filepath), exist_ok=True)
           format_upper = format.upper()
           if format_upper == 'JPEG':
               img = img.convert('RGB')
               img.save(filepath, 'JPEG', quality=quality, optimize=True)
           elif format_upper == 'WEBP':
               img.save(filepath, 'WEBP', quality=quality)
           else:  # PNG по умолчанию
               img.save(filepath, 'PNG', optimize=True)
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
   def read_excel_file(uploaded_file):
       """Чтение Excel файла с автоматическим определением формата"""
       try:
           file_extension = uploaded_file.name.split('.')[-1].lower()
           if file_extension == 'xlsx':
               df = pd.read_excel(uploaded_file, engine='openpyxl')
           elif file_extension == 'xls':
               df = pd.read_excel(uploaded_file, engine='xlrd')
           else:
               st.error(f"❌ Неподдерживаемый формат файла: {file_extension}")
               return None
           df = df.replace({np.nan: None, '': None})
           logger.info(f"Загружен файл: {uploaded_file.name}")
           logger.info(f"Колонки: {df.columns.tolist()}")
           logger.info(f"Строк: {len(df)}")
           return df
       except Exception as e:
           st.error(f"❌ Ошибка чтения файла: {str(e)}")
           logger.error(f"Ошибка чтения Excel: {e}")
           return None

   @staticmethod
   def validate_dataframe(df, required_columns=None):
       """Валидация структуры DataFrame"""
       if df is None or df.empty:
           return False, "DataFrame пустой или не загружен"
       if required_columns:
           missing_columns = [col for col in required_columns if col not in df.columns]
           if missing_columns:
               return False, f"Отсутствуют колонки: {missing_columns}"
       return True, "DataFrame валиден"

   @staticmethod
   def get_column_suggestions(df):
       """Автоматическое предложение колонок для маппинга"""
       suggestions = {
           'top_left': None,
           'top_right': None,
           'bottom_left': None,
           'bottom_right': None,
           'image_url': None,
           'overlay_image_url': None,  # Новая колонка для изображений наложения
           'filename': None
       }
       if df is None:
           return suggestions
           
       column_names = [str(col).lower() for col in df.columns]
       keyword_mapping = {
           'top_left': ['название', 'name', 'товар', 'product', 'title'],
           'top_right': ['цена', 'price', 'стоимость', 'руб'],
           'bottom_left': ['характеристики', 'spec', 'описание', 'description', 'детали'],
           'bottom_right': ['скидка', 'discount', 'акция', 'sale', 'распродажа'],
           'image_url': ['url', 'ссылка', 'image', 'картинка', 'фото', 'photo', 'основное'],
           'overlay_image_url': ['лого', 'logo', 'бренд', 'brand', 'дополнительно', 'additional', 'наложение', 'overlay', 'стикер', 'sticker'],
           'filename': ['название', 'name', 'артикул', 'sku', 'код']
       }
       for position, keywords in keyword_mapping.items():
           for keyword in keywords:
               if any(keyword in col for col in column_names):
                   for original_col in df.columns:
                       if keyword in str(original_col).lower():
                           suggestions[position] = original_col
                           break
                   if suggestions[position]:
                       break
       return suggestions

# ============================
# ОСНОВНОЙ ПРОЦЕССОР
# ============================
class InfographicGenerator:
   """Основной класс для генерации инфографики"""
   def __init__(self):
       self.image_processor = ImageProcessor()
       self.excel_processor = ExcelProcessor()

   def process_single_row(self, row, column_mapping, template_id, export_settings, row_index=0, text_offsets=None, overlay_settings=None, font_settings=None):
       """Обработка одной строки данных с учетом смещений текста и наложения изображений"""
       try:
           text_data = {
               'top_left': row.get(column_mapping.get('top_left'), ''),
               'top_right': row.get(column_mapping.get('top_right'), ''),
               'bottom_left': row.get(column_mapping.get('bottom_left'), ''),
               'bottom_right': row.get(column_mapping.get('bottom_right'), '')
           }
           
           # Основное изображение
           image_url = row.get(column_mapping.get('image_url'), '')
           
           # Изображение для наложения
           overlay_image_url = None
           if 'overlay_image_url' in column_mapping:
               overlay_image_url = row.get(column_mapping.get('overlay_image_url'), '')
           
           filename_source = row.get(column_mapping.get('filename'), '')
           if filename_source:
               filename = self.generate_filename(filename_source, row_index)
           else:
               filename = f"infographic_{row_index:06d}"
           
           if not image_url or not isinstance(image_url, str):
               return {
                   'row_index': row_index,
                   'status': 'error',
                   'message': 'Некорректный URL основного изображения',
                   'filename': filename
               }
           
           # Загружаем основное изображение
           img = self.image_processor.load_image_from_url(
               image_url,
               timeout=export_settings.get('timeout', 15)
           )
           
           if img is None:
               return {
                   'row_index': row_index,
                   'status': 'error',
                   'message': 'Не удалось загрузить основное изображение',
                   'filename': filename
               }
           
           if export_settings.get('resize', True):
               img = self.image_processor.resize_image(
                   img,
                   export_settings.get('target_size', 1200)
               )
           
           # Добавляем текст
           processed_img = self.image_processor.add_text_to_image(
               img,
               text_data,
               template_id,
               text_offsets=text_offsets,
               font_settings=font_settings
           )
           
           # Накладываем дополнительное изображение если есть
           if overlay_settings and overlay_settings.get('enabled', False) and overlay_image_url:
               overlay_img = self.image_processor.load_overlay_image(overlay_image_url)
               if overlay_img:
                   processed_img = self.image_processor.add_image_overlay(
                       processed_img,
                       overlay_img,
                       overlay_settings,
                       template_id
                   )
           
           output_dir = st.session_state.get('output_dir', 'output_infographics')
           format_ext = export_settings.get('format', 'PNG').lower()
           filepath = os.path.join(output_dir, f"{filename}.{format_ext}")
           
           success = self.image_processor.save_image(
               processed_img,
               filepath,
               format=export_settings.get('format', 'PNG'),
               quality=export_settings.get('quality', 85)
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
               'message': str(e),
               'filename': f"row_{row_index}"
           }

   def generate_filename(self, source, index):
       """Генерация имени файла из исходной строки"""
       filename = re.sub(r'[<>:"/\\|?*]', '', str(source))
       filename = filename.replace(' ', '_')
       if len(filename) > 100:
           filename = filename[:100]
       if not filename:
           filename = f"item_{index:06d}"
       return filename

   def process_batch(self, df, start_idx, end_idx, column_mapping, template_id, export_settings, processing_settings, text_offsets=None, overlay_settings=None, font_settings=None):
       """Пакетная обработка данных с учетом всех настроек"""
       results = []
       total_rows = end_idx - start_idx + 1
       output_dir = st.session_state.get('output_dir', 'output_infographics')
       os.makedirs(output_dir, exist_ok=True)
       max_workers = min(processing_settings.get('max_workers', 8), total_rows)
       
       with ThreadPoolExecutor(max_workers=max_workers) as executor:
           futures = []
           for idx in range(start_idx, end_idx + 1):
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
               futures.append(future)
           
           completed = 0
           for future in as_completed(futures):
               try:
                   result = future.result()
                   results.append(result)
                   completed += 1
                   progress = completed / total_rows
                   if 'progress_bar' in st.session_state:
                       st.session_state.progress_bar.progress(progress)
                   if 'status_text' in st.session_state:
                       success_count = sum(1 for r in results if r['status'] == 'success')
                       st.session_state.status_text.text(
                           f"Обработано: {completed}/{total_rows} | Успешно: {success_count} | Ошибок: {completed - success_count}"
                       )
               except Exception as e:
                   logger.error(f"Ошибка в потоке обработки: {e}")
                   results.append({
                       'row_index': completed,
                       'status': 'error',
                       'message': str(e)
                   })
       return results

   def create_zip_archive(self, results, batch_name=None):
       """Создание ZIP архива с результатами"""
       if not batch_name:
           batch_name = datetime.now().strftime("%Y%m%d_%H%M%S")
       zip_filename = f"infographics_{batch_name}.zip"
       output_dir = st.session_state.get('output_dir', 'output_infographics')
       zip_path = os.path.join(output_dir, zip_filename)
       
       try:
           with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
               for result in results:
                   if result['status'] == 'success' and 'filepath' in result:
                       if os.path.exists(result['filepath']):
                           arcname = os.path.basename(result['filepath'])
                           zipf.write(result['filepath'], arcname)
           
           results_df = pd.DataFrame(results)
           csv_path = os.path.join(output_dir, f"results_{batch_name}.csv")
           results_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
           
           with zipfile.ZipFile(zip_path, 'a', zipfile.ZIP_DEFLATED) as zipf:
               zipf.write(csv_path, os.path.basename(csv_path))
           
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
               key="sidebar_file_uploader"
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
                           st.success(f"✅ Загружено {len(df)} строк")
           
           with st.expander("👁️ Предпросмотр данных", expanded=False):
               if st.session_state.get('df') is not None:
                   preview_rows = st.slider(
                       "Строк для предпросмотра", 
                       5, 50, 10,
                       key="sidebar_preview_rows_slider"
                   )
                   st.dataframe(st.session_state.df.head(preview_rows))
           
           st.subheader("🎨 Шаблон инфографики")
           template_options = InfographicTemplates.get_template_names()
           current_template = st.session_state.get('current_template', 'standard')
           selected_template = st.selectbox(
               "Выберите шаблон",
               options=template_options,
               format_func=lambda x: f"{InfographicTemplates.TEMPLATES[x]['name']} - "
                                   f"{InfographicTemplates.TEMPLATES[x]['description']}",
               index=template_options.index(current_template) if current_template in template_options else 0,
               key="sidebar_template_selectbox"
           )
           st.session_state.current_template = selected_template
           
           template = InfographicTemplates.TEMPLATES[selected_template]
           st.caption(f"**Тип:** {template['name']}")
           st.caption(f"**Описание:** {template['description']}")
           
           st.subheader("💾 Настройки экспорта")
           col1, col2 = st.columns(2)
           with col1:
               export_format = st.selectbox(
                   "Формат",
                   ["PNG", "JPEG", "WebP"],
                   index=["PNG", "JPEG", "WebP"].index(
                       st.session_state.export_settings.get('format', 'PNG')
                   ),
                   key="sidebar_export_format_selectbox"
               )
               st.session_state.export_settings['format'] = export_format
           with col2:
               quality = st.slider(
                   "Качество",
                   50, 100,
                   st.session_state.export_settings.get('quality', 85),
                   key="sidebar_quality_slider"
               )
               st.session_state.export_settings['quality'] = quality
           
           resize_checkbox = st.checkbox(
               "Изменять размер",
               st.session_state.export_settings.get('resize', True),
               key="sidebar_resize_checkbox"
           )
           st.session_state.export_settings['resize'] = resize_checkbox
           
           if st.session_state.export_settings['resize']:
               target_size = st.number_input(
                   "Целевой размер (px)",
                   500, 4000,
                   st.session_state.export_settings.get('target_size', 1200),
                   key="sidebar_target_size_number"
               )
               st.session_state.export_settings['target_size'] = target_size
           
           st.subheader("⚡ Настройки обработки")
           col1, col2 = st.columns(2)
           with col1:
               batch_size = st.number_input(
                   "Размер партии",
                   1, 10000,
                   st.session_state.processing_settings.get('batch_size', 100),
                   key="sidebar_batch_size_number"
               )
               st.session_state.processing_settings['batch_size'] = batch_size
           with col2:
               max_workers = st.number_input(
                   "Максимум потоков",
                   1, 32,
                   st.session_state.processing_settings.get('max_workers', 8),
                   key="sidebar_max_workers_number"
               )
               st.session_state.processing_settings['max_workers'] = max_workers
           
           timeout_input = st.number_input(
               "Таймаут (сек)",
               5, 60,
               st.session_state.processing_settings.get('timeout', 15),
               key="sidebar_timeout_number"
           )
           st.session_state.processing_settings['timeout'] = timeout_input
           
           retry_count = st.number_input(
               "Повторные попытки",
               0, 5,
               st.session_state.processing_settings.get('retry_count', 2),
               key="sidebar_retry_count_number"
           )
           st.session_state.processing_settings['retry_count'] = retry_count
           
           st.divider()
           st.caption(f"Обработано: {st.session_state.get('processed_count', 0)} изображений")
           st.caption(f"Версия: 4.0 (Расширенная)")

   @staticmethod
   def render_column_mapping():
       """Отрисовка настройки маппинга колонок"""
       if st.session_state.get('df') is not None:
           st.subheader("📊 Настройка маппинга колонок")
           st.info("Выберите, какие колонки из файла соответствуют элементам инфографики")
           
           available_columns = st.session_state.df.columns.tolist()
           col1, col2 = st.columns(2)
           
           with col1:
               st.session_state.column_mapping['top_left'] = st.selectbox(
                   "Верхний левый угол (Название)",
                   available_columns,
                   index=available_columns.index(
                       st.session_state.column_mapping.get('top_left', available_columns[0])
                   ) if st.session_state.column_mapping.get('top_left') in available_columns else 0,
                   key="mapping_top_left_selectbox"
               )
               st.session_state.column_mapping['top_right'] = st.selectbox(
                   "Верхний правый угол (Цена)",
                   available_columns,
                   index=available_columns.index(
                       st.session_state.column_mapping.get('top_right', available_columns[1])
                   ) if st.session_state.column_mapping.get('top_right') in available_columns and len(available_columns) > 1 else min(1, len(available_columns)-1),
                   key="mapping_top_right_selectbox"
               )
               st.session_state.column_mapping['image_url'] = st.selectbox(
                   "URL основного изображения",
                   available_columns,
                   index=available_columns.index(
                       st.session_state.column_mapping.get('image_url', available_columns[2])
                   ) if st.session_state.column_mapping.get('image_url') in available_columns and len(available_columns) > 2 else min(2, len(available_columns)-1),
                   key="mapping_image_url_selectbox"
               )
           
           with col2:
               st.session_state.column_mapping['bottom_left'] = st.selectbox(
                   "Нижний левый угол (Характеристики)",
                   available_columns,
                   index=available_columns.index(
                       st.session_state.column_mapping.get('bottom_left', available_columns[3])
                   ) if st.session_state.column_mapping.get('bottom_left') in available_columns and len(available_columns) > 3 else min(3, len(available_columns)-1),
                   key="mapping_bottom_left_selectbox"
               )
               st.session_state.column_mapping['bottom_right'] = st.selectbox(
                   "Нижний правый угол (Скидка/Детали)",
                   available_columns,
                   index=available_columns.index(
                       st.session_state.column_mapping.get('bottom_right', available_columns[4])
                   ) if st.session_state.column_mapping.get('bottom_right') in available_columns and len(available_columns) > 4 else min(4, len(available_columns)-1),
                   key="mapping_bottom_right_selectbox"
               )
               st.session_state.column_mapping['filename'] = st.selectbox(
                   "Имена файлов (источник)",
                   available_columns,
                   index=available_columns.index(
                       st.session_state.column_mapping.get('filename', available_columns[0])
                   ) if st.session_state.column_mapping.get('filename') in available_columns else 0,
                   key="mapping_filename_selectbox"
               )
           
           # Дополнительная колонка для изображения наложения
           st.subheader("🖼️ Изображение для наложения")
           st.info("Выберите колонку с URL дополнительных изображений (логотипы, стикеры и т.д.)")
           
           col1, col2 = st.columns([3, 1])
           with col1:
               overlay_image_column = st.selectbox(
                   "Колонка с изображениями для наложения",
                   ["Не использовать"] + available_columns,
                   index=0 if st.session_state.column_mapping.get('overlay_image_url') not in available_columns else 
                         available_columns.index(st.session_state.column_mapping.get('overlay_image_url')) + 1,
                   key="mapping_overlay_image_selectbox"
               )
               
               if overlay_image_column != "Не использовать":
                   st.session_state.column_mapping['overlay_image_url'] = overlay_image_column
               else:
                   if 'overlay_image_url' in st.session_state.column_mapping:
                       del st.session_state.column_mapping['overlay_image_url']
           
           with col2:
               st.session_state.image_overlay_settings['enabled'] = st.checkbox(
                   "Включить наложение",
                   value=st.session_state.image_overlay_settings.get('enabled', False),
                   key="mapping_enable_overlay_checkbox"
               )
   
   @staticmethod
   def render_font_settings():
       """Отрисовка настроек шрифтов"""
       st.subheader("🔤 Настройки шрифтов")
       
       col1, col2 = st.columns(2)
       
       with col1:
           st.markdown("**Загрузка шрифтов**")
           
           # Загрузка шрифтов через файл
           uploaded_fonts = st.file_uploader(
               "Загрузите файлы шрифтов (.ttf, .otf)",
               type=['ttf', 'otf', 'TTF', 'OTF'],
               accept_multiple_files=True,
               help="Загрузите свои шрифты для использования в инфографике",
               key="font_settings_font_uploader"
           )
           
           if uploaded_fonts:
               for font_file in uploaded_fonts:
                   font_key, font_name = FontManager.load_font_from_file(font_file)
                   if font_key:
                       st.success(f"✅ Шрифт '{font_name}' загружен")
                   else:
                       st.error(f"❌ Ошибка загрузки шрифта '{font_file.name}'")
           
           # Список загруженных шрифтов
           if 'uploaded_fonts' in st.session_state and st.session_state.uploaded_fonts:
               st.markdown("**Загруженные шрифты:**")
               for font_info in st.session_state.uploaded_fonts:
                   st.caption(f"📁 {font_info['name']}")
       
       with col2:
           st.markdown("**Выбор шрифтов**")
           
           # Получаем список доступных шрифтов
           available_fonts = FontManager.get_available_fonts()
           
           if available_fonts:
               font_options = [f["name"] for f in available_fonts]
               font_keys = [f["key"] for f in available_fonts]
               
               # Основной шрифт
               current_main_font = st.session_state.font_settings.get('main_font', 'system_arial')
               current_main_index = font_keys.index(current_main_font) if current_main_font in font_keys else 0
               
               main_font_name = st.selectbox(
                   "Основной шрифт",
                   font_options,
                   index=current_main_index,
                   key="font_settings_main_font_selectbox"
               )
               
               if main_font_name:
                   selected_index = font_options.index(main_font_name)
                   st.session_state.font_settings['main_font'] = font_keys[selected_index]
               
               # Жирный шрифт (опционально)
               current_bold_font = st.session_state.font_settings.get('bold_font', 'system_arial')
               current_bold_index = font_keys.index(current_bold_font) if current_bold_font in font_keys else 0
               
               bold_font_name = st.selectbox(
                   "Жирный шрифт (для заголовков)",
                   ["Тот же что основной"] + font_options,
                   index=0 if current_bold_font == current_main_font else current_bold_index + 1,
                   key="font_settings_bold_font_selectbox"
               )
               
               if bold_font_name == "Тот же что основной":
                   st.session_state.font_settings['bold_font'] = st.session_state.font_settings['main_font']
               elif bold_font_name:
                   selected_index = font_options.index(bold_font_name)
                   st.session_state.font_settings['bold_font'] = font_keys[selected_index]
               
               # Множитель размера шрифта
               font_size_multiplier = st.slider(
                   "Множитель размера шрифта",
                   0.5, 2.0,
                   st.session_state.font_settings.get('font_size_multiplier', 1.0),
                   0.1,
                   key="font_settings_font_size_multiplier_slider"
               )
               st.session_state.font_settings['font_size_multiplier'] = font_size_multiplier
               
               st.caption(f"Текущий шрифт: {main_font_name}")
   
   @staticmethod
   def render_text_offset_settings():
       """Отрисовка настроек смещения текста"""
       if st.session_state.get('df') is not None:
           st.subheader("🎯 Настройки смещения текста")
           st.info("Регулируйте положение текста на изображении")
           
           # Кнопка для включения симметричных смещений
           col1, col2 = st.columns(2)
           with col1:
               symmetrical = st.checkbox(
                   "🔄 Симметричные смещения для всех углов",
                   value=st.session_state.get('symmetrical_offsets', False),
                   help="При включении все углы будут иметь одинаковые смещения",
                   key="text_offset_symmetrical_offsets_checkbox"
               )
               st.session_state.symmetrical_offsets = symmetrical
           
           with col2:
               if symmetrical:
                   st.info("⚠️ Режим симметричных смещений активен")
           
           # Создаем 4 колонки для настроек смещения
           cols = st.columns(4)
           
           # Верхний левый угол
           with cols[0]:
               st.markdown("**↖️ Верхний левый**")
               
               if not symmetrical:
                   x_offset = st.number_input(
                       "Смещение X (%)",
                       -100, 100,
                       st.session_state.text_offset_settings['top_left'].get('x_offset', 0),
                       key="text_offset_top_left_x"
                   )
                   y_offset = st.number_input(
                       "Смещение Y (%)",
                       -100, 100,
                       st.session_state.text_offset_settings['top_left'].get('y_offset', 0),
                       key="text_offset_top_left_y"
                   )
                   st.session_state.text_offset_settings['top_left'] = {
                       'x_offset': x_offset,
                       'y_offset': y_offset
                   }
               else:
                   st.info("Настройки применяются ко всем углам")
           
           # Верхний правый угол
           with cols[1]:
               st.markdown("**↗️ Верхний правый**")
               if not symmetrical:
                   x_offset = st.number_input(
                       "Смещение X (%)",
                       -100, 100,
                       st.session_state.text_offset_settings['top_right'].get('x_offset', 0),
                       key="text_offset_top_right_x"
                   )
                   y_offset = st.number_input(
                       "Смещение Y (%)",
                       -100, 100,
                       st.session_state.text_offset_settings['top_right'].get('y_offset', 0),
                       key="text_offset_top_right_y"
                   )
                   st.session_state.text_offset_settings['top_right'] = {
                       'x_offset': x_offset,
                       'y_offset': y_offset
                   }
               else:
                   st.caption(f"X: {st.session_state.text_offset_settings['top_left'].get('x_offset', 0)}%")
                   st.caption(f"Y: {st.session_state.text_offset_settings['top_left'].get('y_offset', 0)}%")
           
           # Нижний левый угол
           with cols[2]:
               st.markdown("**↙️ Нижний левый**")
               if not symmetrical:
                   x_offset = st.number_input(
                       "Смещение X (%)",
                       -100, 100,
                       st.session_state.text_offset_settings['bottom_left'].get('x_offset', 0),
                       key="text_offset_bottom_left_x"
                   )
                   y_offset = st.number_input(
                       "Смещение Y (%)",
                       -100, 100,
                       st.session_state.text_offset_settings['bottom_left'].get('y_offset', 0),
                       key="text_offset_bottom_left_y"
                   )
                   st.session_state.text_offset_settings['bottom_left'] = {
                       'x_offset': x_offset,
                       'y_offset': y_offset
                   }
               else:
                   st.caption(f"X: {st.session_state.text_offset_settings['top_left'].get('x_offset', 0)}%")
                   st.caption(f"Y: {st.session_state.text_offset_settings['top_left'].get('y_offset', 0)}%")
           
           # Нижний правый угол
           with cols[3]:
               st.markdown("**↘️ Нижний правый**")
               if not symmetrical:
                   x_offset = st.number_input(
                       "Смещение X (%)",
                       -100, 100,
                       st.session_state.text_offset_settings['bottom_right'].get('x_offset', 0),
                       key="text_offset_bottom_right_x"
                   )
                   y_offset = st.number_input(
                       "Смещение Y (%)",
                       -100, 100,
                       st.session_state.text_offset_settings['bottom_right'].get('y_offset', 0),
                       key="text_offset_bottom_right_y"
                   )
                   st.session_state.text_offset_settings['bottom_right'] = {
                       'x_offset': x_offset,
                       'y_offset': y_offset
                   }
               else:
                   st.caption(f"X: {st.session_state.text_offset_settings['top_left'].get('x_offset', 0)}%")
                   st.caption(f"Y: {st.session_state.text_offset_settings['top_left'].get('y_offset', 0)}%")
           
           # Если включен режим симметрии, показываем общие контролы
           if symmetrical:
               st.markdown("---")
               st.subheader("🔄 Общие настройки для всех углов")
               
               col1, col2 = st.columns(2)
               with col1:
                   common_x_offset = st.number_input(
                       "Общее смещение по X (%)",
                       -100, 100,
                       st.session_state.text_offset_settings['top_left'].get('x_offset', 0),
                       key="text_offset_common_x_offset_symmetrical"
                   )
               with col2:
                   common_y_offset = st.number_input(
                       "Общее смещение по Y (%)",
                       -100, 100,
                       st.session_state.text_offset_settings['top_left'].get('y_offset', 0),
                       key="text_offset_common_y_offset_symmetrical"
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
               if st.button("🔄 Сбросить смещения", type="secondary", key="text_offset_reset_offsets_button"):
                   st.session_state.text_offset_settings = {
                       'top_left': {'x_offset': 0, 'y_offset': 0},
                       'top_right': {'x_offset': 0, 'y_offset': 0},
                       'bottom_left': {'x_offset': 0, 'y_offset': 0},
                       'bottom_right': {'x_offset': 0, 'y_offset': 0}
                   }
                   st.rerun()
           
           with col2:
               if not symmetrical:
                   if st.button("📐 Сделать симметричными", type="secondary", key="text_offset_make_symmetrical_button"):
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
       """Отрисовка настроек наложения изображений"""
       if st.session_state.get('df') is not None and st.session_state.image_overlay_settings.get('enabled', False):
           st.subheader("🖼️ Настройки наложения изображений")
           st.info("Настройте параметры для дополнительных изображений (логотипы, стикеры и т.д.)")
           
           template = InfographicTemplates.TEMPLATES[st.session_state.current_template]
           
           # Выбор позиции
           col1, col2 = st.columns(2)
           with col1:
               position_options = list(template.get('image_positions', {'center': {"x": 0.5, "y": 0.5, "anchor": "center"}}).keys())
               current_position = st.session_state.image_overlay_settings.get('position', 'center')
               position = st.selectbox(
                   "Позиция на изображении",
                   position_options,
                   index=position_options.index(current_position) if current_position in position_options else 0,
                   key="overlay_position_selectbox"
               )
               st.session_state.image_overlay_settings['position'] = position
           
           with col2:
               opacity = st.slider(
                   "Прозрачность (%)",
                   0, 100,
                   st.session_state.image_overlay_settings.get('opacity', 100),
                   key="overlay_opacity_slider"
               )
               st.session_state.image_overlay_settings['opacity'] = opacity
           
           # Настройки размера
           col1, col2 = st.columns(2)
           with col1:
               scale = st.slider(
                   "Масштаб (%)",
                   10, 200,
                   st.session_state.image_overlay_settings.get('scale', 100),
                   key="overlay_scale_slider"
               )
               st.session_state.image_overlay_settings['scale'] = scale
           
           with col2:
               max_width = st.slider(
                   "Макс. ширина (% от основного)",
                   5, 100,
                   st.session_state.image_overlay_settings.get('max_width', 50),
                   key="overlay_max_width_slider"
               )
               st.session_state.image_overlay_settings['max_width'] = max_width
           
           # Смещения
           col1, col2 = st.columns(2)
           with col1:
               x_offset = st.number_input(
                   "Смещение по X (%)",
                   -100, 100,
                   st.session_state.image_overlay_settings.get('x_offset', 0),
                   key="overlay_x_offset_input"
               )
               st.session_state.image_overlay_settings['x_offset'] = x_offset
           
           with col2:
               y_offset = st.number_input(
                   "Смещение по Y (%)",
                   -100, 100,
                   st.session_state.image_overlay_settings.get('y_offset', 0),
                   key="overlay_y_offset_input"
               )
               st.session_state.image_overlay_settings['y_offset'] = y_offset
           
           st.caption("💡 Используйте смещения для точной настройки положения изображения")
           
           # Предпросмотр позиции
           if st.checkbox("Показать предпросмотр позиции", value=False, key="overlay_show_preview_checkbox"):
               st.info(f"**Позиция:** {position}")
               st.info(f"**Масштаб:** {scale}%, **Прозрачность:** {opacity}%")
               st.info(f"**Смещение:** X={x_offset}%, Y={y_offset}%")

   @staticmethod
   def render_preview_tab(generator):
       """Отрисовка вкладки предпросмотра"""
       if st.session_state.get('df') is None:
           st.info("📥 Загрузите Excel файл в боковой панели для начала работы")
           return
       
       st.header("🎯 Предпросмотр и тестирование")
       
       # Настройки шрифтов
       UIComponents.render_font_settings()
       
       # Настройки смещения текста
       UIComponents.render_text_offset_settings()
       
       # Настройки наложения изображений
       UIComponents.render_image_overlay_settings()
       
       # Выбор строки для теста
       col1, col2, col3 = st.columns([2, 1, 1])
       with col1:
           test_row_idx = st.number_input(
               "Номер строки для тестирования",
               min_value=0,
               max_value=len(st.session_state.df)-1,
               value=0,
               key="preview_test_row_idx_number"
           )
       with col2:
           timeout = st.number_input(
               "Таймаут (сек)",
               5, 60,
               st.session_state.export_settings.get('timeout', 15),
               key="preview_timeout_number"
           )
       with col3:
           st.write("")
           st.write("")
           test_button = st.button("🚀 Запустить тест", type="primary", key="preview_test_button")
       
       if test_button and test_row_idx < len(st.session_state.df):
           with st.spinner("Выполнение теста..."):
               row = st.session_state.df.iloc[test_row_idx]
               
               text_data = {
                   'top_left': str(row.get(st.session_state.column_mapping.get('top_left', ''), '')),
                   'top_right': str(row.get(st.session_state.column_mapping.get('top_right', ''), '')),
                   'bottom_left': str(row.get(st.session_state.column_mapping.get('bottom_left', ''), '')),
                   'bottom_right': str(row.get(st.session_state.column_mapping.get('bottom_right', ''), ''))
               }
               
               image_url = str(row.get(st.session_state.column_mapping.get('image_url', ''), ''))
               
               overlay_image_url = None
               if 'overlay_image_url' in st.session_state.column_mapping:
                   overlay_image_url = str(row.get(st.session_state.column_mapping.get('overlay_image_url', ''), ''))
               
               with st.expander("📋 Исходные данные строки"):
                   col1, col2 = st.columns(2)
                   with col1:
                       st.json(text_data, key="preview_text_data_json")
                   with col2:
                       st.code(f"Основное изображение: {image_url}", key="preview_main_url_code")
                       if overlay_image_url:
                           st.code(f"Изображение наложения: {overlay_image_url}", key="preview_overlay_url_code")
               
               if image_url and image_url.startswith(('http://', 'https://')):
                   img = generator.image_processor.load_image_from_url(image_url, timeout)
                   
                   if img:
                       # Показываем текущие настройки
                       if st.session_state.get('symmetrical_offsets', False):
                           st.success(f"**🔄 Симметричные смещения:** X: {st.session_state.text_offset_settings['top_left'].get('x_offset', 0)}%, Y: {st.session_state.text_offset_settings['top_left'].get('y_offset', 0)}%")
                       else:
                           st.info(f"**Применяемые смещения текста:** {st.session_state.text_offset_settings}")
                       
                       if st.session_state.image_overlay_settings.get('enabled', False):
                           st.info(f"**Наложение изображений:** Включено, позиция: {st.session_state.image_overlay_settings.get('position', 'center')}")
                       
                       # Обрабатываем изображение
                       processed_img = generator.image_processor.add_text_to_image(
                           img.copy(),
                           text_data,
                           st.session_state.current_template,
                           text_offsets=st.session_state.text_offset_settings,
                           font_settings=st.session_state.font_settings
                       )
                       
                       # Накладываем дополнительное изображение если есть
                       if (st.session_state.image_overlay_settings.get('enabled', False) and 
                           overlay_image_url and overlay_image_url.startswith(('http://', 'https://', 'data:'))):
                           
                           overlay_img = generator.image_processor.load_overlay_image(overlay_image_url)
                           if overlay_img:
                               processed_img = generator.image_processor.add_image_overlay(
                                   processed_img,
                                   overlay_img,
                                   st.session_state.image_overlay_settings,
                                   st.session_state.current_template
                               )
                               st.success("✅ Изображение наложения добавлено")
                           else:
                               st.warning("⚠️ Не удалось загрузить изображение для наложения")
                       
                       col1, col2 = st.columns(2)
                       with col1:
                           st.subheader("📷 Оригинал")
                           st.image(img, use_column_width=True)
                           st.caption(f"Размер: {img.width}×{img.height}")
                       with col2:
                           st.subheader("🎨 С инфографикой")
                           st.image(processed_img, use_column_width=True)
                           st.caption(f"Шаблон: {st.session_state.current_template}")
                           
                           # Показываем сетку для визуализации позиций
                           show_grid = st.checkbox("Показать сетку позиций", value=False, key="preview_show_grid_checkbox")
                           if show_grid:
                               grid_img = img.copy()
                               draw = ImageDraw.Draw(grid_img)
                               template = InfographicTemplates.TEMPLATES[st.session_state.current_template]
                               
                               for position_key, position_data in template.get("text_positions", {}).items():
                                   base_x = position_data["x"] * img.width
                                   base_y = position_data["y"] * img.height
                                   
                                   if position_key in st.session_state.text_offset_settings:
                                       offset_x = st.session_state.text_offset_settings[position_key].get('x_offset', 0)
                                       offset_y = st.session_state.text_offset_settings[position_key].get('y_offset', 0)
                                       
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
                                   
                                   draw.ellipse([x-5, y-5, x+5, y+5], fill='red')
                                   draw.text((x+10, y-10), position_key, fill='red')
                               
                               # Показываем позиции для наложения изображений
                               for pos_name, pos_data in template.get('image_positions', {}).items():
                                   x = int(pos_data["x"] * img.width)
                                   y = int(pos_data["y"] * img.height)
                                   draw.rectangle([x-10, y-10, x+10, y+10], outline='blue', width=2)
                                   draw.text((x+15, y-15), pos_name, fill='blue')
                               
                               st.image(grid_img, use_column_width=True, caption="Сетка позиций (красный - текст, синий - изображения)")
                       
                       # Кнопка скачивания тестового файла
                       buffered = BytesIO()
                       format_ext = st.session_state.export_settings.get('format', 'PNG').lower()
                       
                       if st.session_state.export_settings['format'] == 'JPEG':
                           processed_img.convert('RGB').save(
                               buffered,
                               format='JPEG',
                               quality=st.session_state.export_settings.get('quality', 85)
                           )
                           mime_type = 'image/jpeg'
                       elif st.session_state.export_settings['format'] == 'WEBP':
                           processed_img.save(
                               buffered,
                               format='WEBP',
                               quality=st.session_state.export_settings.get('quality', 85)
                           )
                           mime_type = 'image/webp'
                       else:
                           processed_img.save(buffered, format='PNG')
                           mime_type = 'image/png'
                       
                       st.download_button(
                           label="💾 Скачать тестовое изображение",
                           data=buffered.getvalue(),
                           file_name=f"test_preview.{format_ext}",
                           mime=mime_type,
                           key="preview_test_download_button"
                       )
                       
                       st.session_state.preview_image = processed_img
                   else:
                       st.error("❌ Не удалось загрузить изображение. Проверьте URL.")
               else:
                   st.warning("⚠️ Некорректный URL основного изображения")

   @staticmethod
   def render_processing_tab(generator):
       """Отрисовка вкладки обработки"""
       if st.session_state.get('df') is None:
           st.info("📥 Загрузите Excel файл в боковой панели для начала работы")
           return
       
       st.header("⚡ Массовая обработка")
       
       # Показываем текущие настройки
       if st.session_state.get('symmetrical_offsets', False):
           st.success(f"**🔄 Будут применены симметричные смещения:** X: {st.session_state.text_offset_settings['top_left'].get('x_offset', 0)}%, Y: {st.session_state.text_offset_settings['top_left'].get('y_offset', 0)}%")
       else:
           st.info(f"**Будут применены смещения текста:** {st.session_state.text_offset_settings}")
       
       if st.session_state.image_overlay_settings.get('enabled', False):
           st.info(f"**🖼️ Наложение изображений:** Включено, позиция: {st.session_state.image_overlay_settings.get('position', 'center')}")
       
       if st.session_state.font_settings.get('main_font'):
           available_fonts = FontManager.get_available_fonts()
           font_name = next((f["name"] for f in available_fonts if f["key"] == st.session_state.font_settings['main_font']), "Системный шрифт")
           st.info(f"**🔤 Шрифт:** {font_name}, множитель: {st.session_state.font_settings.get('font_size_multiplier', 1.0)}")
       
       total_rows = len(st.session_state.df)
       st.info(f"📊 Готово к обработке: {total_rows} строк")
       
       col1, col2, col3 = st.columns(3)
       with col1:
           start_idx = st.number_input(
               "Начать с строки",
               0, total_rows-1, 0,
               key="processing_start_idx_number"
           )
       with col2:
           end_idx = st.number_input(
               "Закончить на строке",
               start_idx, total_rows-1,
               min(start_idx + st.session_state.processing_settings.get('batch_size', 100) - 1, total_rows-1),
               key="processing_end_idx_number"
           )
       with col3:
           st.write("")
           st.write("")
           process_button = st.button(
               "🔄 Начать обработку", 
               type="primary", 
               use_container_width=True,
               key="processing_process_button"
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
           
           progress_bar = st.progress(0, key="processing_progress_bar")
           status_text = st.empty()
           results_placeholder = st.empty()
           
           st.session_state.progress_bar = progress_bar
           st.session_state.status_text = status_text
           
           with st.spinner("Запуск обработки..."):
               results = generator.process_batch(
                   st.session_state.df,
                   start_idx,
                   end_idx,
                   st.session_state.column_mapping,
                   st.session_state.current_template,
                   {
                       **st.session_state.export_settings,
                       'timeout': st.session_state.processing_settings.get('timeout', 15)
                   },
                   st.session_state.processing_settings,
                   text_offsets=st.session_state.text_offset_settings,
                   overlay_settings=st.session_state.image_overlay_settings if st.session_state.image_overlay_settings.get('enabled', False) else None,
                   font_settings=st.session_state.font_settings
               )
           
           success_count = sum(1 for r in results if r['status'] == 'success')
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
                   st.metric("Успешно", success_count, key="processing_success_metric")
               with col2:
                   st.metric("С ошибками", failed_count, key="processing_failed_metric")
               with col3:
                   if st.session_state.processing_stats['start_time'] and st.session_state.processing_stats['end_time']:
                       duration = (
                           st.session_state.processing_stats['end_time'] -
                           st.session_state.processing_stats['start_time']
                       ).total_seconds()
                       st.metric("Время", f"{duration:.1f} сек", key="processing_time_metric")
               
               if failed_count > 0:
                   with st.expander("📋 Детали ошибок"):
                       error_results = [r for r in results if r['status'] == 'error']
                       error_df = pd.DataFrame(error_results)
                       st.dataframe(error_df[['row_index', 'message']])
               
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
                                       key="processing_zip_download_button"
                                   )
                           with col2:
                               with open(csv_path, 'rb') as f:
                                   st.download_button(
                                       label="📊 Скачать отчет (CSV)",
                                       data=f.read(),
                                       file_name=os.path.basename(csv_path),
                                       mime="text/csv",
                                       use_container_width=True,
                                       key="processing_csv_download_button"
                                   )
                           
                           zip_size = os.path.getsize(zip_path) / (1024 * 1024)
                           st.info(f"Размер архива: {zip_size:.2f} MB")

   @staticmethod
   def render_statistics_tab():
       """Отрисовка вкладки статистики"""
       st.header("📊 Статистика и аналитика")
       
       if st.session_state.get('processed_count', 0) == 0:
           st.info("📈 Статистика появится после обработки данных")
           return
       
       col1, col2, col3, col4 = st.columns(4)
       with col1:
           st.metric("Всего обработано", st.session_state.get('processed_count', 0), key="stats_total_processed_metric")
       with col2:
           if st.session_state.get('batch_results'):
               success_rate = (
                   sum(1 for r in st.session_state.batch_results if r['status'] == 'success') /
                   len(st.session_state.batch_results) * 100
               )
               st.metric("Успешность", f"{success_rate:.1f}%", key="stats_success_rate_metric")
       with col3:
           st.metric("Текущий шаблон",
                    InfographicTemplates.TEMPLATES[st.session_state.current_template]['name'],
                    key="stats_template_metric")
       with col4:
           st.metric("Формат экспорта", st.session_state.export_settings.get('format', 'PNG'), key="stats_format_metric")
       
       # Показываем текущие настройки
       show_settings = st.checkbox("Показать текущие настройки", value=False, key="stats_show_settings_checkbox")
       if show_settings:
           st.subheader("⚙️ Текущие настройки")
           
           if st.session_state.get('symmetrical_offsets', False):
               st.success("🔄 Режим симметричных смещений активен")
               st.write(f"**Общие смещения:** X: {st.session_state.text_offset_settings['top_left'].get('x_offset', 0)}%, Y: {st.session_state.text_offset_settings['top_left'].get('y_offset', 0)}%")
           else:
               offset_df = pd.DataFrame(st.session_state.text_offset_settings).T
               st.write("**Смещения текста:**")
               st.dataframe(offset_df)
           
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
                   st.bar_chart(status_counts, key="stats_status_chart")
               with col2:
                   st.dataframe(status_counts, key="stats_status_dataframe")
           
           if (st.session_state.processing_stats.get('start_time') and
               st.session_state.processing_stats.get('end_time')):
               duration = (
                   st.session_state.processing_stats['end_time'] -
                   st.session_state.processing_stats['start_time']
               ).total_seconds()
               
               if duration > 0 and len(results_df) > 0:
                   speed = len(results_df) / duration
                   st.metric("Скорость обработки", f"{speed:.2f} изобр/сек", key="stats_speed_metric")

   @staticmethod
   def render_instructions_tab():
       """Отрисовка вкладки инструкций"""
       st.header("📚 Инструкция по использованию")
       
       with st.expander("🔤 Загрузка и настройка шрифтов", expanded=True):
           st.markdown(
               """
               ### Как работать с шрифтами:
               
               #### 📁 Загрузка собственных шрифтов:
               1. **Поддерживаемые форматы**: .ttf, .otf
               2. **Нажмите "Загрузите файлы шрифтов"** в настройках шрифтов
               3. **Выберите файлы** с вашего компьютера
               4. **Загруженные шрифты** появятся в списке доступных
               
               #### 🎯 Выбор шрифтов:
               - **Основной шрифт**: Используется для всего текста
               - **Жирный шрифт**: Используется для заголовков (можно использовать тот же что основной)
               - **Множитель размера**: Увеличивает/уменьшает размер всех шрифтов
               
               #### 💡 Советы:
               - Используйте **читаемые шрифты** для лучшего восприятия
               - **Толстые шрифты** лучше видны на сложном фоне
               - **Тестируйте** разные шрифты в режиме предпросмотра
               """
           )
       
       with st.expander("🖼️ Наложение изображений", expanded=True):
           st.markdown(
               """
               ### Как работать с наложением изображений:
               
               #### 📊 Подготовка Excel файла:
               - **Добавьте колонку** с URL дополнительных изображений
               - **Названия колонок**: лого, logo, бренд, brand, наложение, overlay
               - **Формат URL**: Прямые ссылки на изображения или base64
               
               #### ⚙️ Настройки наложения:
               1. **Включите наложение** в настройках маппинга
               2. **Выберите колонку** с изображениями
               3. **Настройте параметры**:
                  - **Позиция**: Выберите из доступных позиций шаблона
                  - **Масштаб**: Размер изображения относительно основного
                  - **Прозрачность**: Видимость накладываемого изображения
                  - **Смещения**: Точная настройка положения
               
               #### 📝 Примеры использования:
               - **Логотипы брендов** на товарах
               - **Стикеры акций** (-50%, NEW, Хит)
               - **Водяные знаки** для защиты
               - **Дополнительные элементы** дизайна
               
               #### 💡 Советы:
               - Используйте **PNG с прозрачностью** для лучшего результата
               - **Тестируйте позиции** в режиме предпросмотра
               - **Настройте прозрачность** если изображение мешает тексту
               """
           )
       
       with st.expander("📊 Подготовка Excel файла", expanded=False):
           st.markdown(
               """
               ### Требования к Excel файлу:
               1. **Формат файла**: .xlsx или .xls
               2. **Первая строка**: должна содержать заголовки колонок
               3. **Обязательные данные**:
                  - Названия товаров
                  - URL основного изображения
                  - Цены и характеристики
                  - (Опционально) URL дополнительных изображений
               ### Рекомендуемая структура:
               ```
               | Название      | Основное изображение         | Цена     | Логотип            | Характеристики      |
               |---------------|-------------------------------|----------|---------------------|---------------------|
               | Смартфон Xiaomi | https://example.com/phone.jpg | 24 999 ₽ | https://example.com/logo.png | 128GB, 8GB RAM     |
               | Наушники Sony  | https://example.com/hp.jpg    | 8 499 ₽  | https://example.com/brand.png | Bluetooth 5.0      |
               ```
               ### Как получить прямые ссылки на изображения:
               - **Маркетплейсы**: Правая кнопка → "Копировать адрес изображения"
               - **Google Drive**: Измените ссылку на: `https://drive.google.com/uc?id=ID_ФАЙЛА`
               - **Свои изображения**: Загрузите на хостинг изображений
               """
           )

# ============================
# ОСНОВНОЙ КОД ПРИЛОЖЕНИЯ
# ============================
def main():
   """Основная функция приложения"""
   if 'image_cache' not in st.session_state:
       st.session_state['image_cache'] = {}
   if 'font_cache' not in st.session_state:
       st.session_state['font_cache'] = {}
   if 'uploaded_fonts' not in st.session_state:
       st.session_state['uploaded_fonts'] = []

   st.title("🎯 Генератор Инфографики v4.0")
   st.markdown("### Расширенная версия с загрузкой шрифтов и наложением изображений")
   st.markdown("---")
   
   # Инициализация классов
   generator = InfographicGenerator()
   ui = UIComponents()
   
   # Боковая панель
   ui.render_sidebar()
   
   # Основное содержимое
   if st.session_state.get('df') is not None:
       # Вкладки
       tab1, tab2, tab3, tab4, tab5 = st.tabs([
           "📊 Настройка",
           "🎯 Предпросмотр",
           "⚡ Обработка",
           "📈 Статистика",
           "📚 Инструкция"
       ])
       
       with tab1:
           ui.render_column_mapping()
           
           st.subheader("🏷️ Настройка имен файлов")
           col1, col2 = st.columns(2)
           with col1:
               add_prefix = st.checkbox("Добавить префикс", value=False, key="settings_add_prefix_checkbox")
               if add_prefix:
                   prefix = st.text_input("Префикс", value="product_", key="settings_prefix_text")
                   st.session_state.export_settings['prefix'] = prefix
           with col2:
               add_suffix = st.checkbox("Добавить суффикс", value=False, key="settings_add_suffix_checkbox")
               if add_suffix:
                   suffix = st.text_input("Суффикс", value="_promo", key="settings_suffix_text")
                   st.session_state.export_settings['suffix'] = suffix
           
           # Настройки шрифтов
           ui.render_font_settings()
           
           # Настройки смещения текста
           ui.render_text_offset_settings()
           
           # Настройки наложения изображений
           ui.render_image_overlay_settings()
           
           if st.button("🔍 Автоподбор колонок", type="secondary", key="settings_auto_map_button"):
               suggestions = ExcelProcessor.get_column_suggestions(st.session_state.df)
               st.session_state.column_mapping = suggestions
               st.success("✅ Колонки автоматически подобраны!")
               st.rerun()
       
       with tab2:
           ui.render_preview_tab(generator)
       
       with tab3:
           ui.render_processing_tab(generator)
       
       with tab4:
           ui.render_statistics_tab()
       
       with tab5:
           ui.render_instructions_tab()
   else:
       # Экран приветствия
       st.markdown(
           """
           ## 🚀 Добро пожаловать в Генератор Инфографики v4.0!
           **Расширенная версия с новыми возможностями:**
           - **Загрузка собственных шрифтов**
           - **Наложение дополнительных изображений**
           - **Точная настройка всех элементов**
           
           ### 📋 Как начать:
           1. **Подготовьте Excel файл** с данными о товарах
           2. **Загрузите файл** в боковой панели слева
           3. **Загрузите шрифты** (опционально)
           4. **Настройте соответствие** колонок элементам инфографики
           5. **Выберите шаблон** дизайна
           6. **Настройте все параметры**
           7. **Протестируйте** на одном товаре
           8. **Запустите массовую обработку**
           """
       )
       
       # Блок с новыми возможностями
       with st.container():
           st.markdown("### 🎯 Новые возможности версии 4.0:")
           col1, col2 = st.columns(2)
           with col1:
               st.markdown("""
               - **Загрузка собственных шрифтов**
               - **Наложение дополнительных изображений**
               - **Поддержка форматов TTF и OTF**
               - **Выбор позиции для изображений**
               """)
           with col2:
               st.markdown("""
               - **Настройка прозрачности и масштаба**
               - **Управление жирностью шрифтов**
               - **Множитель размера шрифта**
               - **Поддержка base64 изображений**
               """)
       
       st.markdown(
           """
           ---        
           **📁 Подготовьте ваш Excel файл и начните создавать профессиональную инфографику уже сегодня!**
           """
       )
       
       # Пример структуры файла с новыми колонками
       with st.expander("📋 Пример структуры Excel файла"):
           example_data = {
               "Название товара": ["Смартфон Xiaomi Redmi Note 12", "Наушники Sony WH-1000XM5"],
               "Основное изображение": [
                   "https://example.com/xiaomi.jpg",
                   "https://example.com/sony.jpg"
               ],
               "Логотип бренда": [
                   "https://example.com/xiaomi_logo.png",
                   "https://example.com/sony_logo.png"
               ],
               "Цена": ["24 999 ₽", "34 999 ₽"],
               "Старая цена": ["29 999 ₽", "39 999 ₽"],
               "Характеристики": ["128GB, 8GB RAM, AMOLED", "Шумоподавление, 30ч работы"],
               "Скидка": ["-17%", "-13%"],
               "Доставка": ["Бесплатно", "1-2 дня"]
           }
           example_df = pd.DataFrame(example_data)
           st.dataframe(example_df, use_container_width=True)
           
           buffer = BytesIO()
           with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
               example_df.to_excel(writer, index=False, sheet_name='Товары')
           
           st.download_button(
               label="📥 Скачать шаблон Excel файла",
               data=buffer.getvalue(),
               file_name="шаблон_товары_v4.xlsx",
               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
               key="main_template_download_button"
           )
       
       # Футер
       st.markdown("---")
       st.markdown(
           """
           <div style='text-align: center; color: #666; font-size: 0.9em;'>
               <p>Генератор Инфографики v4.0 | Расширенная версия |
               Обработано изображений: <b>{processed_count}</b></p>
               <p>Для вопросов и предложений: support@example.com</p>
           </div>
           """.format(processed_count=st.session_state.get('processed_count', 0)), unsafe_allow_html=True
       )

# ============================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ============================
if __name__ == "__main__":
   try:
       main()
   except Exception as e:
       logger.error(f"Критическая ошибка в приложении: {e}", exc_info=True)
       st.error(f"⚠️ Произошла критическая ошибка: {str(e)}")
       st.info("Попробуйте обновить страницу или перезапустить приложение.")
