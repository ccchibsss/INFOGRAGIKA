import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import time
import os
import hashlib
from datetime import datetime
import zipfile
import json
import sys
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# ============================
# НАСТРОЙКА ПРИЛОЖЕНИЯ
# ============================
st.set_page_config(
    page_title="🎯 Генератор Инфографики v3.0 - Excel версия",
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
        'preview_image': None,
        'uploaded_file_name': None,
        'export_settings': {
            'format': 'PNG',
            'quality': 85,
            'resize': True,
            'target_size': 1200,
            'prefix': '',
            'suffix': ''
        },
        'processing_settings': {
            'batch_size': 100,
            'max_workers': 8,
            'timeout': 15,
            'retry_count': 2
        }
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ============================
# КЛАССЫ И УТИЛИТЫ
# ============================

class InfographicTemplates:
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
        return list(cls.TEMPLATES.keys())

    @classmethod
    def get_template_display_name(cls, template_id):
        return cls.TEMPLATES[template_id]["name"]


class ImageProcessor:
    @staticmethod
    def load_image_from_url(url, timeout=15, retries=2):
        for attempt in range(retries + 1):
            try:
                response = requests.get(url, timeout=timeout, headers={'User-Agent': 'Mozilla/5.0'})
                response.raise_for_status()
                img = Image.open(BytesIO(response.content))
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                cache_key = hashlib.md5(url.encode()).hexdigest()
                st.session_state.image_cache[cache_key] = img.copy()
                return img
            except Exception as e:
                if attempt == retries:
                    logger.error(f"Не удалось загрузить изображение {url}: {e}")
                    return None
                time.sleep(1)

    @staticmethod
    def resize_image(img, target_size=1200):
        if img.width > target_size or img.height > target_size:
            ratio = min(target_size / img.width, target_size / img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        return img

    @staticmethod
    def add_text_to_image(img, text_data, template_id="standard"):
        if img is None:
            return None
        template = InfographicTemplates.TEMPLATES[template_id]
        draw = ImageDraw.Draw(img)

        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        ]
        font_regular = None
        for path in font_paths:
            if os.path.exists(path):
                try:
                    font_regular = ImageFont.truetype(path, 24)
                    break
                except:
                    continue
        if font_regular is None:
            font_regular = ImageFont.load_default()

        for position_key, position_data in template["text_positions"].items():
            if position_key in text_data and text_data[position_key]:
                text = str(text_data[position_key])
                if not text.strip():
                    continue
                x = int(position_data["x"] * img.width)
                y = int(position_data["y"] * img.height)
                font_size = template["font_sizes"][position_key]
                font = None
                for path in font_paths:
                    if os.path.exists(path):
                        try:
                            font = ImageFont.truetype(path, font_size)
                            break
                        except:
                            continue
                if font is None:
                    font = ImageFont.load_default()
                if template["effects"]["shadow"]:
                    shadow_color = template["colors"]["shadow"]
                    draw.text((x+2, y+2), text, font=font, fill=shadow_color)
                text_color = template["colors"]["text"]
                draw.text((x, y), text, font=font, fill=text_color)
        return img

    @staticmethod
    def save_image(img, filepath, format='PNG', quality=85):
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            if format.upper() == 'JPEG':
                img = img.convert('RGB')
                img.save(filepath, 'JPEG', quality=quality, optimize=True)
            elif format.upper() == 'WEBP':
                img.save(filepath, 'WEBP', quality=quality)
            else:
                img.save(filepath, 'PNG', optimize=True)
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения {filepath}: {e}")
            return False


class ExcelProcessor:
    @staticmethod
    def read_excel_file(uploaded_file):
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
    def get_column_suggestions(df):
        suggestions = {
            'top_left': None,
            'top_right': None,
            'bottom_left': None,
            'bottom_right': None,
            'image_url': None,
            'filename': None
        }
        column_names = [str(col).lower() for col in df.columns]
        keyword_mapping = {
            'top_left': ['название', 'name', 'товар', 'product', 'title'],
            'top_right': ['цена', 'price', 'стоимость', 'руб'],
            'bottom_left': ['характеристики', 'spec', 'описание', 'description', 'детали'],
            'bottom_right': ['скидка', 'discount', 'акция', 'sale', 'распродажа'],
            'image_url': ['url', 'ссылка', 'image', 'картинка', 'фото', 'photo'],
            'filename': ['название', 'name', 'артикул', 'sku', 'код']
        }
        for position, keywords in keyword_mapping.items():
            for keyword in keywords:
                for col in column_names:
                    if keyword in col:
                        for original_col in df.columns:
                            if keyword in str(original_col).lower():
                                suggestions[position] = original_col
                                break
                        if suggestions[position]:
                            break
                if suggestions[position]:
                    break
        return suggestions

# ============================
# ОСНОВНЫЙ КЛАСС ГЕНЕРАТОРА
# ============================

class InfographicGenerator:
    def __init__(self):
        self.image_processor = ImageProcessor()
        self.excel_processor = ExcelProcessor()

    def process_single_row(self, row, column_mapping, template_id, export_settings, row_index=0):
        try:
            text_data = {
                'top_left': row.get(column_mapping.get('top_left'), ''),
                'top_right': row.get(column_mapping.get('top_right'), ''),
                'bottom_left': row.get(column_mapping.get('bottom_left'), ''),
                'bottom_right': row.get(column_mapping.get('bottom_right'), '')
            }
            image_url = row.get(column_mapping.get('image_url'), '')
            if not image_url or not isinstance(image_url, str):
                return {
                    'row_index': row_index,
                    'status': 'error',
                    'message': 'Некорректный URL изображения',
                    'filename': f"row_{row_index}"
                }
            img = self.image_processor.load_image_from_url(image_url, timeout=export_settings.get('timeout', 15))
            if img is None:
                return {
                    'row_index': row_index,
                    'status': 'error',
                    'message': 'Не удалось загрузить изображение',
                    'filename': f"row_{row_index}"
                }
            if export_settings.get('resize', True):
                img = self.image_processor.resize_image(img, export_settings.get('target_size', 1200))
            processed_img = self.image_processor.add_text_to_image(img.copy(), text_data, template_id)
            filename_source = row.get(column_mapping.get('filename'), '')
            filename = self.generate_filename(filename_source, row_index)
            filepath = os.path.join(st.session_state.output_dir, f"{filename}.{export_settings.get('format', 'PNG').lower()}")
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
                    'image_url': image_url
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
        filename = re.sub(r'[<>:"/\\|?*]', '', str(source))
        filename = filename.replace(' ', '_')
        if len(filename) > 100:
            filename = filename[:100]
        if not filename:
            filename = f"item_{index:06d}"
        return filename

    def process_batch(self, df, start_idx, end_idx, column_mapping, template_id, export_settings, processing_settings):
        results = []
        total_rows = end_idx - start_idx + 1
        os.makedirs(st.session_state.output_dir, exist_ok=True)
        max_workers = min(processing_settings.get('max_workers', 8), total_rows)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for idx in range(start_idx, end_idx + 1):
                row = df.iloc[idx]
                futures.append(executor.submit(self.process_single_row, row, column_mapping, template_id, export_settings, idx))
            completed = 0
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1
                    progress = completed / total_rows
                    st.session_state['progress_bar'].progress(progress)
                    success_count = sum(1 for r in results if r['status'] == 'success')
                    st.session_state['status_text'].text(
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
        if not batch_name:
            batch_name = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"infographics_{batch_name}.zip"
        zip_path = os.path.join(st.session_state.output_dir, zip_filename)
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for result in results:
                    if result['status'] == 'success' and 'filepath' in result:
                        if os.path.exists(result['filepath']):
                            zipf.write(result['filepath'], os.path.basename(result['filepath']))
            # Создаем CSV с результатами
            results_df = pd.DataFrame(results)
            csv_path = os.path.join(st.session_state.output_dir, f"results_{batch_name}.csv")
            results_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            # Добавляем CSV в архив
            with zipfile.ZipFile(zip_path, 'a', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(csv_path, os.path.basename(csv_path))
            return zip_path, csv_path
        except Exception as e:
            logger.error(f"Ошибка создания ZIP архива: {e}")
            return None, None

# ============================
# UI компоненты
# ============================

class UIComponents:
    @staticmethod
    def render_sidebar():
        with st.sidebar:
            st.title("⚙️ Настройки")
            uploaded_file = st.file_uploader("📁 Загрузка данных", type=['xlsx', 'xls'])
            if uploaded_file:
                if (st.session_state.uploaded_file_name != uploaded_file.name or st.session_state.df is None):
                    with st.spinner("🔄 Загрузка файла..."):
                        df = ExcelProcessor.read_excel_file(uploaded_file)
                        if df is not None:
                            st.session_state.df = df
                            st.session_state.uploaded_file_name = uploaded_file.name
                            suggestions = ExcelProcessor.get_column_suggestions(df)
                            st.session_state.column_mapping = suggestions
                            st.success(f"✅ Загружено {len(df)} строк")
                with st.expander("👁️ Предпросмотр данных", expanded=False):
                    preview_rows = st.slider("Строк для предпросмотра", 5, 50, 10)
                    st.dataframe(st.session_state.df.head(preview_rows))
            st.subheader("🎨 Шаблон инфографики")
            templates = InfographicTemplates.get_template_names()
            current_template = st.session_state.get('current_template', 'standard')
            selected_template = st.selectbox(
                "Выберите шаблон",
                options=templates,
                format_func=lambda x: f"{InfographicTemplates.TEMPLATES[x]['name']} - {InfographicTemplates.TEMPLATES[x]['description']}",
                index=templates.index(current_template) if current_template in templates else 0
            )
            st.session_state['current_template'] = selected_template
            template = InfographicTemplates.TEMPLATES[selected_template]
            st.caption(f"**Тип:** {template['name']}")
            st.caption(f"**Описание:** {template['description']}")
            st.subheader("💾 Настройки экспорта")
            export_format = st.selectbox(
                "Формат",
                ["PNG", "JPEG", "WebP"],
                index=["PNG", "JPEG", "WebP"].index(st.session_state['export_settings'].get('format', 'PNG'))
            )
            st.session_state['export_settings']['format'] = export_format
            quality = st.slider(
                "Качество",
                50, 100,
                value=st.session_state['export_settings'].get('quality', 85)
            )
            st.session_state['export_settings']['quality'] = quality
            resize = st.checkbox(
                "Изменять размер",
                value=st.session_state['export_settings'].get('resize', True)
            )
            st.session_state['export_settings']['resize'] = resize
            if resize:
                target_size = st.number_input(
                    "Целевой размер (px)",
                    min_value=500,
                    max_value=4000,
                    value=st.session_state['export_settings'].get('target_size', 1200)
                )
                st.session_state['export_settings']['target_size'] = target_size
            st.subheader("⚡ Настройки обработки")
            total_rows = len(st.session_state.df) if st.session_state.df is not None else 0
            batch_size = st.number_input(
                "Размер партии",
                min_value=1,
                max_value=10000,
                value=st.session_state['processing_settings'].get('batch_size', 100)
            )
            max_workers = st.number_input(
                "Максимум потоков",
                min_value=1,
                max_value=32,
                value=st.session_state['processing_settings'].get('max_workers', 8)
            )
            timeout = st.number_input(
                "Таймаут (сек)",
                min_value=5,
                max_value=60,
                value=st.session_state['processing_settings'].get('timeout', 15)
            )
            retry_count = st.number_input(
                "Повторные попытки",
                min_value=0,
                max_value=5,
                value=st.session_state['processing_settings'].get('retry_count', 2)
            )
            st.session_state['processing_settings'].update({
                'batch_size': batch_size,
                'max_workers': max_workers,
                'timeout': timeout,
                'retry_count': retry_count
            })
            st.markdown("---")
            st.caption(f"Обработано изображений: {st.session_state['processed_count']}")

    @staticmethod
    def render_column_mapping():
        if st.session_state.df is not None:
            st.subheader("📊 Настройка маппинга колонок")
            st.info("Выберите, какие колонки соответствуют элементам инфографики")
            available_columns = st.session_state.df.columns.tolist()

            def get_index_for_value(lst, val):
                try:
                    return lst.index(val)
                except:
                    return 0

            col1, col2 = st.columns(2)
            with col1:
                st.session_state['column_mapping']['top_left'] = st.selectbox(
                    "Верхний левый (Название)",
                    available_columns,
                    index=get_index_for_value(available_columns, st.session_state['column_mapping'].get('top_left'))
                )
                st.session_state['column_mapping']['top_right'] = st.selectbox(
                    "Верхний правый (Цена)",
                    available_columns,
                    index=get_index_for_value(available_columns, st.session_state['column_mapping'].get('top_right'))
                )
                st.session_state['column_mapping']['image_url'] = st.selectbox(
                    "URL изображения",
                    available_columns,
                    index=get_index_for_value(available_columns, st.session_state['column_mapping'].get('image_url'))
                )
            with col2:
                st.session_state['column_mapping']['bottom_left'] = st.selectbox(
                    "Нижний левый (Характеристики)",
                    available_columns,
                    index=get_index_for_value(available_columns, st.session_state['column_mapping'].get('bottom_left'))
                )
                st.session_state['column_mapping']['bottom_right'] = st.selectbox(
                    "Нижний правый (Скидка/Детали)",
                    available_columns,
                    index=get_index_for_value(available_columns, st.session_state['column_mapping'].get('bottom_right'))
                )
                st.session_state['column_mapping']['filename'] = st.selectbox(
                    "Имена файлов (источник)",
                    available_columns,
                    index=get_index_for_value(available_columns, st.session_state['column_mapping'].get('filename'))
                )

    @staticmethod
    def render_preview_tab(generator):
        if st.session_state.df is None:
            st.info("📥 Загрузите Excel файл для предпросмотра")
            return
        st.header("🎯 Предпросмотр и тестирование")
        col1, col2, col3 = st.columns([2,1,1])
        with col1:
            test_row_idx = st.number_input(
                "Номер строки для теста",
                min_value=0,
                max_value=len(st.session_state.df)-1,
                value=0
            )
        with col2:
            timeout = st.number_input(
                "Таймаут (сек)",
                min_value=5,
                max_value=60,
                value=st.session_state['export_settings'].get('timeout', 15)
            )
        with col3:
            st.write("")
        if st.button("🚀 Запустить тест") and st.session_state.df is not None:
            with st.spinner("Выполнение теста..."):
                row = st.session_state.df.iloc[test_row_idx]
                text_data = {
                    'top_left': str(row.get(st.session_state['column_mapping'].get('top_left', ''), '')),
                    'top_right': str(row.get(st.session_state['column_mapping'].get('top_right', ''), '')),
                    'bottom_left': str(row.get(st.session_state['column_mapping'].get('bottom_left', ''), '')),
                    'bottom_right': str(row.get(st.session_state['column_mapping'].get('bottom_right', ''), ''))
                }
                image_url = str(row.get(st.session_state['column_mapping'].get('image_url', ''), ''))
                if image_url and image_url.startswith(('http://','https://')):
                    img = generator.image_processor.load_image_from_url(image_url, timeout)
                    if img:
                        processed_img = generator.image_processor.add_text_to_image(img.copy(), text_data, st.session_state['current_template'])
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("📷 Оригинал")
                            st.image(img, use_column_width=True)
                            st.caption(f"Размер: {img.width}×{img.height}")
                        with col2:
                            st.subheader("🎨 С инфографикой")
                            st.image(processed_img, use_column_width=True)
                            st.caption(f"Шаблон: {st.session_state['current_template']}")
                        buf = BytesIO()
                        format_ext = st.session_state['export_settings']['format'].lower()
                        if st.session_state['export_settings']['format'] == 'JPEG':
                            processed_img.convert('RGB').save(buf, 'JPEG', quality=st.session_state['export_settings']['quality'])
                            mime_type='image/jpeg'
                        elif st.session_state['export_settings']['format'] == 'WEBP':
                            processed_img.save(buf, 'WEBP', quality=st.session_state['export_settings']['quality'])
                            mime_type='image/webp'
                        else:
                            processed_img.save(buf, 'PNG')
                            mime_type='image/png'
                        st.download_button(
                            "💾 Скачать тестовое изображение",
                            data=buf.getvalue(),
                            file_name="test_preview." + format_ext,
                            mime=mime_type
                        )
                    else:
                        st.error("❌ Не удалось загрузить изображение. Проверьте URL.")
                else:
                    st.warning("⚠️ Некорректный URL изображения")

    @staticmethod
    def render_processing_tab(generator):
        if st.session_state.df is None:
            st.info("📥 Загрузите Excel файл для начала")
            return
        st.header("⚡ Массовая обработка")
        total_rows = len(st.session_state.df)
        if total_rows == 0:
            st.info("Нет данных для обработки")
            return
        col1, col2, col3 = st.columns(3)
        with col1:
            start_idx = st.number_input(
                "Начать с",
                min_value=0,
                max_value=total_rows -1,
                value=0
            )
        with col2:
            max_end_idx = total_rows -1
            default_end = min(start_idx + st.session_state['processing_settings'].get('batch_size', 100) -1, total_rows -1)
            end_idx = st.number_input(
                "Закончить на",
                min_value=start_idx,
                max_value=max_end_idx,
                value=default_end
            )
        with col3:
            st.write("")
        if st.button("🔄 Обработать") and total_rows > 0:
            # инициализация прогресс-бара
            st.session_state['progress_bar'] = st.progress(0)
            st.session_state['status_text'] = st.empty()
            st.session_state['results_placeholder'] = st.empty()
            # Обработка
            with st.spinner("Обработка..."):
                results = generator.process_batch(
                    st.session_state['df'],
                    start_idx,
                    end_idx,
                    st.session_state['column_mapping'],
                    st.session_state['current_template'],
                    {
                        **st.session_state['export_settings'],
                        'timeout': st.session_state['processing_settings']['timeout']
                    },
                    st.session_state['processing_settings']
                )
            success_count = sum(1 for r in results if r['status']=='success')
            failed_count = len(results) - success_count
            st.session_state['processed_count'] += success_count
            st.session_state['batch_results'] = results
            # Статистика
            st.session_state['processing_stats'] = {
                'total': len(results),
                'success': success_count,
                'failed': failed_count,
                'start_time': None,
                'end_time': datetime.now()
            }
            with st.session_state['results_placeholder']:
                st.success(f"✅ Обработка завершена")
                st.metric("Успешно", success_count)
                st.metric("Ошибки", failed_count)
                duration = (st.session_state['processing_stats']['end_time'] - datetime.now()).total_seconds()
                if duration > 0:
                    speed = len(results)/duration
                    st.metric("Скорость", f"{speed:.2f} изображений/сек")
                # Архив
                zip_path, csv_path = generator.create_zip_archive(results)
                if zip_path and os.path.exists(zip_path):
                    with open(zip_path, 'rb') as f:
                        st.download_button("📦 Скачать ZIP архив", f.read(), os.path.basename(zip_path))
                    with open(csv_path, 'rb') as f:
                        st.download_button("📊 Скачать отчет (CSV)", f.read(), os.path.basename(csv_path))

    @staticmethod
    def render_statistics_tab():
        st.header("📊 Статистика")
        if st.session_state['processed_count'] == 0:
            st.info("Статистика появится после обработки данных")
            return
        success_total = st.session_state['processed_count']
        total_results = len(st.session_state.get('batch_results', []))
        if total_results == 0:
            return
        df_results = pd.DataFrame(st.session_state['batch_results'])
        if 'status' in df_results.columns:
            status_counts = df_results['status'].value_counts()
            st.bar_chart(status_counts)
        if st.session_state['processing_stats'].get('start_time') and st.session_state['processing_stats'].get('end_time'):
            duration = (st.session_state['processing_stats']['end_time'] - st.session_state['processing_stats']['']['start_time']).total_seconds()
            if duration > 0:
                speed = total_results / duration
                st.metric("Скорость обработки", f"{speed:.2f} изображений/сек")
        st.metric("Обработано изображений", st.session_state['processed_count'])

    @staticmethod
    def render_instructions_tab():
        st.header("📚 Инструкция")
        st.markdown("""
        ### Как подготовить файл:
        - Используйте формат .xlsx или .xls
        - В первой строке — заголовки
        - Обязательные колонки: Название, URL изображения, Цена, Характеристики, Скидка
        - Для получения прямых ссылок используйте "Копировать адрес изображения"
        - Можно использовать примеры шаблонов и маппинга
        """)

# ============================
# Основная функция
# ============================
def main():
    st.title("🎯 Генератор Инфографики v3.0")
    st.markdown("### Автоматическое создание инфографики из Excel файлов")
    st.markdown("---")
    # Инициализация компонентов
    UIComponents.render_sidebar()
    if st.session_state.df is not None:
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Настройка",
            "🎯 Предпросмотр",
            "⚡ Обработка",
            "📈 Статистика",
            "📚 Инструкция"
        ])
        with tab1:
            UIComponents.render_column_mapping()
        with tab2:
            UIComponents.render_preview_tab(generator=InfographicGenerator())
        with tab3:
            UIComponents.render_processing_tab(generator=InfographicGenerator())
        with tab4:
            UIComponents.render_statistics_tab()
        with tab5:
            UIComponents.render_instructions_tab()
    else:
        st.markdown("Загрузите файл в боковой панели слева для начала работы.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("Критическая ошибка")
        st.error(f"⚠️ Произошла критическая ошибка: {str(e)}")
