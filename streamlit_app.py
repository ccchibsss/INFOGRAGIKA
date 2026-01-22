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
        'image_cache': {},  # Инициализация словаря для кэша изображений
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
        """Получить список доступных шаблонов"""
        return list(cls.TEMPLATES.keys())
    
    @classmethod
    def get_template_display_name(cls, template_id):
        """Получить отображаемое имя шаблона"""
        return cls.TEMPLATES[template_id]["name"]

# ============================
# УТИЛИТЫ ДЛЯ РАБОТЫ С ИЗОБРАЖЕНИЯМИ
# ============================
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
                # Кэшируем изображение
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
        """Изменение размера изображения с сохранением пропорций"""
        if img.width > target_size or img.height > target_size:
            ratio = min(target_size / img.width, target_size / img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        return img
    
    @staticmethod
    def add_text_to_image(img, text_data, template_id="standard"):
        """Добавление текста на изображение по шаблону"""
        if img is None:
            return None
            
        template = InfographicTemplates.TEMPLATES[template_id]
        draw = ImageDraw.Draw(img)
        
        # Пытаемся загрузить шрифт
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        ]
        regular_font = None
        for path in font_paths:
            if os.path.exists(path):
                try:
                    regular_font = ImageFont.truetype(path, 24)
                    break
                except:
                    continue
        if regular_font is None:
            regular_font = ImageFont.load_default()
        
        # Обработка каждого текстового элемента
        for position_key, position_data in template["text_positions"].items():
            if position_key in text_data and text_data[position_key]:
                text = str(text_data[position_key])
                if not text.strip():
                    continue
                # Координаты
                x = int(position_data["x"] * img.width)
                y = int(position_data["y"] * img.height)
                font_size = template["font_sizes"][position_key]
                # Загружаем шрифт
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
                # Тень
                if template["effects"]["shadow"]:
                    shadow_color = template["colors"]["shadow"]
                    draw.text((x+2, y+2), text, font=font, fill=shadow_color)
                # Основной текст
                text_color = template["colors"]["text"]
                draw.text((x, y), text, font=font, fill=text_color)
        return img
    
    @staticmethod
    def save_image(img, filepath, format='PNG', quality=85):
        """Сохранение изображения в файл"""
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
            # Очистка данных
            df = df.replace({np.nan: None, '': None})
            # Логирование структуры данных
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
# ОСНОВНОЙ ПРОЦЕССОР
# ============================
class InfographicGenerator:
    """Основной класс для генерации инфографики"""
    def __init__(self):
        self.image_processor = ImageProcessor()
        self.excel_processor = ExcelProcessor()
    def process_single_row(self, row, column_mapping, template_id, 
                          export_settings, row_index=0):
        """Обработка одной строки данных"""
        try:
            # Извлекаем данные по маппингу
            text_data = {
                'top_left': row.get(column_mapping.get('top_left'), ''),
                'top_right': row.get(column_mapping.get('top_right'), ''),
                'bottom_left': row.get(column_mapping.get('bottom_left'), ''),
                'bottom_right': row.get(column_mapping.get('bottom_right'), '')
            }
            image_url = row.get(column_mapping.get('image_url'), '')
            # Генерация имени файла
            filename_source = row.get(column_mapping.get('filename'), '')
            if filename_source:
                filename = self.generate_filename(filename_source, row_index)
            else:
                filename = f"infographic_{row_index:06d}"
            # Загрузка изображения
            if not image_url or not isinstance(image_url, str):
                return {
                    'row_index': row_index,
                    'status': 'error',
                    'message': 'Некорректный URL изображения',
                    'filename': filename
                }
            img = self.image_processor.load_image_from_url(
                image_url, 
                timeout=export_settings.get('timeout', 15)
            )
            if img is None:
                return {
                    'row_index': row_index,
                    'status': 'error',
                    'message': 'Не удалось загрузить изображение',
                    'filename': filename
                }
            # Изменение размера
            if export_settings.get('resize', True):
                img = self.image_processor.resize_image(
                    img, 
                    export_settings.get('target_size', 1200)
                )
            # Добавление текста
            processed_img = self.image_processor.add_text_to_image(
                img, 
                text_data, 
                template_id
            )
            # Сохранение
            output_dir = st.session_state.output_dir
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
        """Генерация имени файла из исходной строки"""
        filename = re.sub(r'[<>:"/\\|?*]', '', str(source))
        filename = filename.replace(' ', '_')
        if len(filename) > 100:
            filename = filename[:100]
        if not filename:
            filename = f"item_{index:06d}"
        return filename
    def process_batch(self, df, start_idx, end_idx, column_mapping, 
                     template_id, export_settings, processing_settings):
        """Пакетная обработка данных"""
        results = []
        total_rows = end_idx - start_idx + 1
        os.makedirs(st.session_state.output_dir, exist_ok=True)
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
                    idx
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
        zip_path = os.path.join(st.session_state.output_dir, zip_filename)
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for result in results:
                    if result['status'] == 'success' and 'filepath' in result:
                        if os.path.exists(result['filepath']):
                            arcname = os.path.basename(result['filepath'])
                            zipf.write(result['filepath'], arcname)
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
# ИНТЕРФЕЙС ПОЛЬЗОВАТЕЛЯ
# ============================
class UIComponents:
    """Класс для компонентов пользовательского интерфейса"""
    @staticmethod
    def render_sidebar():
        """Отрисовка боковой панели"""
        with st.sidebar:
            st.title("⚙️ Настройки")
            # Загрузка файла
            st.subheader("📁 Загрузка данных")
            uploaded_file = st.file_uploader(
                "Выберите Excel файл",
                type=['xlsx', 'xls'],
                help="Файл должен содержать данные о товарах"
            )
            if uploaded_file:
                if (st.session_state.uploaded_file_name != uploaded_file.name or 
                    st.session_state.df is None):
                    with st.spinner("Загрузка файла..."):
                        df = ExcelProcessor.read_excel_file(uploaded_file)
                        if df is not None:
                            st.session_state.df = df
                            st.session_state.uploaded_file_name = uploaded_file.name
                            # Автоматическое предложение колонок
                            suggestions = ExcelProcessor.get_column_suggestions(df)
                            st.session_state.column_mapping = suggestions
                            st.success(f"✅ Загружено {len(df)} строк")
                # Предпросмотр данных
                with st.expander("👁️ Предпросмотр данных", expanded=False):
                    if st.session_state.df is not None:
                        preview_rows = st.slider("Строк для предпросмотра", 5, 50, 10)
                        st.dataframe(st.session_state.df.head(preview_rows))
            # Выбор шаблона
            st.subheader("🎨 Шаблон инфографики")
            template_options = InfographicTemplates.get_template_names()
            current_template = st.session_state.get('current_template', 'standard')
            selected_template = st.selectbox(
                "Выберите шаблон",
                options=template_options,
                format_func=lambda x: f"{InfographicTemplates.TEMPLATES[x]['name']} - "
                                    f"{InfographicTemplates.TEMPLATES[x]['description']}",
                index=template_options.index(current_template) if current_template in template_options else 0
            )
            st.session_state['current_template'] = selected_template
            # Превью шаблона
            template = InfographicTemplates.TEMPLATES[selected_template]
            st.caption(f"**Тип:** {template['name']}")
            st.caption(f"**Описание:** {template['description']}")
            # Настройки экспорта
            st.subheader("💾 Настройки экспорта")
            col1, col2 = st.columns(2)
            with col1:
                export_format = st.selectbox(
                    "Формат",
                    ["PNG", "JPEG", "WebP"],
                    index=["PNG", "JPEG", "WebP"].index(st.session_state['export_settings'].get('format', 'PNG'))
                )
                st.session_state['export_settings']['format'] = export_format
            with col2:
                quality = st.slider(
                    "Качество",
                    50, 100, 
                    st.session_state['export_settings'].get('quality', 85)
                )
                st.session_state['export_settings']['quality'] = quality
            st.session_state['export_settings']['resize'] = st.checkbox(
                "Изменять размер", 
                value=st.session_state['export_settings'].get('resize', True)
            )
            if st.session_state['export_settings']['resize']:
                target_size = st.number_input(
                    "Целевой размер (px)",
                    500, 4000,
                    value=st.session_state['export_settings'].get('target_size', 1200)
                )
                st.session_state['export_settings']['target_size'] = target_size
            # Настройки обработки
            st.subheader("⚡ Настройки обработки")
            col1, col2 = st.columns(2)
            with col1:
                batch_size = st.number_input(
                    "Размер партии",
                    1, 10000,
                    value=st.session_state['processing_settings'].get('batch_size', 100)
                )
                st.session_state['processing_settings']['batch_size'] = batch_size
            with col2:
                max_workers = st.number_input(
                    "Максимум потоков",
                    1, 32,
                    value=st.session_state['processing_settings'].get('max_workers', 8)
                )
                st.session_state['processing_settings']['max_workers'] = max_workers
            st.session_state['processing_settings']['timeout'] = st.number_input(
                "Таймаут (сек)",
                5, 60,
                value=st.session_state['processing_settings'].get('timeout', 15)
            )
            st.session_state['processing_settings']['retry_count'] = st.number_input(
                "Повторные попытки",
                0, 5,
                value=st.session_state['processing_settings'].get('retry_count', 2)
            )
            # Информация о системе
            st.divider()
            st.caption(f"Обработано: {st.session_state['processed_count']} изображений")
            st.caption("Версия: 3.0 (Excel)")

    @staticmethod
    def render_column_mapping():
        """Отрисовка настройки маппинга колонок"""
        if st.session_state.df is not None:
            st.subheader("📊 Настройка маппинга колонок")
            st.info("Выберите, какие колонки из файла соответствуют элементам инфографики")
            available_columns = st.session_state.df.columns.tolist()

            def get_index_for_value(list_, value):
                try:
                    return list_.index(value)
                except:
                    return 0

            # Создаем колонки для выбора
            col1, col2 = st.columns(2)
            with col1:
                st.session_state['column_mapping']['top_left'] = st.selectbox(
                    "Верхний левый угол (Название)",
                    available_columns,
                    index=get_index_for_value(available_columns, st.session_state['column_mapping'].get('top_left'))
                )
                st.session_state['column_mapping']['top_right'] = st.selectbox(
                    "Верхний правый угол (Цена)",
                    available_columns,
                    index=get_index_for_value(available_columns, st.session_state['column_mapping'].get('top_right'))
                )
                st.session_state['column_mapping']['image_url'] = st.selectbox(
                    "URL изображений",
                    available_columns,
                    index=get_index_for_value(available_columns, st.session_state['column_mapping'].get('image_url'))
                )
            with col2:
                st.session_state['column_mapping']['bottom_left'] = st.selectbox(
                    "Нижний левый угол (Характеристики)",
                    available_columns,
                    index=get_index_for_value(available_columns, st.session_state['column_mapping'].get('bottom_left'))
                )
                st.session_state['column_mapping']['bottom_right'] = st.selectbox(
                    "Нижний правый угол (Скидка/Детали)",
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
        """Отрисовка вкладки предпросмотра"""
        if st.session_state.df is None:
            st.info("📥 Загрузите Excel файл в боковой панели для начала работы")
            return
        st.header("🎯 Предпросмотр и тестирование")
        # Выбор строки для теста
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            test_row_idx = st.number_input(
                "Номер строки для тестирования",
                min_value=0,
                max_value=len(st.session_state.df)-1,
                value=0
            )
        with col2:
            timeout = st.number_input(
                "Таймаут (сек)",
                5, 60,
                value=st.session_state['export_settings'].get('timeout', 15)
            )
        with col3:
            st.write("")  # Пустое место для выравнивания
            st.write("")
            test_button = st.button("🚀 Запустить тест")
        if test_button and test_row_idx < len(st.session_state.df):
            with st.spinner("Выполнение теста..."):
                row = st.session_state.df.iloc[test_row_idx]
                # Формируем текстовые данные
                text_data = {
                    'top_left': str(row.get(st.session_state['column_mapping'].get('top_left', ''), '')),
                    'top_right': str(row.get(st.session_state['column_mapping'].get('top_right', ''), '')),
                    'bottom_left': str(row.get(st.session_state['column_mapping'].get('bottom_left', ''), '')),
                    'bottom_right': str(row.get(st.session_state['column_mapping'].get('bottom_right', ''), ''))
                }
                image_url = str(row.get(st.session_state['column_mapping'].get('image_url', ''), ''))
                # Показываем исходные данные
                with st.expander("📋 Исходные данные строки"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.json(text_data)
                    with col2:
                        st.code(f"URL: {image_url}")
                if image_url and image_url.startswith(('http://', 'https://')):
                    # Загружаем изображение
                    img = generator.image_processor.load_image_from_url(image_url, timeout)
                    if img:
                        # Обрабатываем изображение
                        processed_img = generator.image_processor.add_text_to_image(
                            img.copy(),
                            text_data,
                            st.session_state['current_template']
                        )
                        # Показываем результат
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("📷 Оригинал")
                            st.image(img, use_column_width=True)
                            st.caption(f"Размер: {img.width}×{img.height}")
                        with col2:
                            st.subheader("🎨 С инфографикой")
                            st.image(processed_img, use_column_width=True)
                            st.caption(f"Шаблон: {st.session_state['current_template']}")
                        # Кнопка скачивания тестового файла
                        buffered = BytesIO()
                        format_ext = st.session_state['export_settings']['format'].lower()
                        if st.session_state['export_settings']['format'] == 'JPEG':
                            processed_img.convert('RGB').save(
                                buffered, 
                                format='JPEG',
                                quality=st.session_state['export_settings']['quality']
                            )
                            mime_type = 'image/jpeg'
                        elif st.session_state['export_settings']['format'] == 'WEBP':
                            processed_img.save(
                                buffered,
                                format='WEBP',
                                quality=st.session_state['export_settings']['quality']
                            )
                            mime_type = 'image/webp'
                        else:
                            processed_img.save(buffered, format='PNG')
                            mime_type = 'image/png'
                        st.download_button(
                            label="💾 Скачать тестовое изображение",
                            data=buffered.getvalue(),
                            file_name=f"test_preview.{format_ext}",
                            mime=mime_type
                        )
                        # Сохраняем для возможного повторного использования
                        st.session_state['preview_image'] = processed_img
                    else:
                        st.error("❌ Не удалось загрузить изображение. Проверьте URL.")
                else:
                    st.warning("⚠️ Некорректный URL изображения")

    @staticmethod
    def render_processing_tab(generator):
        """Отрисовка вкладки обработки"""
        if st.session_state.df is None:
            st.info("📥 Загрузите Excel файл в боковой панели для начала работы")
            return
        st.header("⚡ Массовая обработка")
        total_rows = len(st.session_state.df)
        st.info(f"📊 Готово к обработке: {total_rows} строк")
        # Настройки обработки
        col1, col2, col3 = st.columns(3)
        with col1:
            start_idx = st.number_input(
                "Начать с строки",
                0, total_rows-1, 0
            )
        with col2:
            end_idx = st.number_input(
                "Закончить на строке",
                start_idx, total_rows-1,
                min=start_idx + st.session_state['processing_settings'].get('batch_size', 100) - 1, 
                value=min(start_idx + st.session_state['processing_settings'].get('batch_size', 100) - 1, total_rows-1)
            )
        with col3:
            st.write("")
            st.write("")
            process_button = st.button("🔄 Начать обработку")
        # Информация о партии
        batch_size = end_idx - start_idx + 1
        if batch_size > 0:
            st.success(f"✅ Будет обработано: {batch_size} строк")
        # Обработка
        if process_button and batch_size > 0:
            # Сброс статистики
            st.session_state['processing_stats'] = {
                'total': batch_size,
                'success': 0,
                'failed': 0,
                'start_time': datetime.now(),
                'end_time': None
            }
            # Создаем элементы интерфейса для прогресса
            st.session_state['progress_bar'] = st.progress(0)
            st.session_state['status_text'] = st.empty()
            st.session_state['results_placeholder'] = st.empty()
            # Запускаем обработку
            with st.spinner("Запуск обработки..."):
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
            # Обновляем статистику
            success_count = sum(1 for r in results if r['status'] == 'success')
            failed_count = len(results) - success_count
            st.session_state['processing_stats'].update({
                'success': success_count,
                'failed': failed_count,
                'end_time': datetime.now()
            })
            st.session_state['processed_count'] += success_count
            st.session_state['batch_results'] = results
            # Показываем результаты
            with st.session_state['results_placeholder'].container():
                st.success(f"✅ Обработка завершена!")
                # Сводка
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Успешно", success_count)
                with col2:
                    st.metric("С ошибками", failed_count)
                with col3:
                    if st.session_state['processing_stats']['start_time'] and st.session_state['processing_stats']['end_time']:
                        duration = (
                            st.session_state['processing_stats']['end_time'] - 
                            st.session_state['processing_stats']['start_time']
                        ).total_seconds()
                        st.metric("Время", f"{duration:.1f} сек")
                # Детали ошибок
                if failed_count > 0:
                    with st.expander("📋 Детали ошибок"):
                        error_results = [r for r in results if r['status'] == 'error']
                        error_df = pd.DataFrame(error_results)
                        st.dataframe(error_df[['row_index', 'message']])
                # Создание архива
                if success_count > 0:
                    with st.spinner("Создание архива..."):
                        zip_path, csv_path = generator.create_zip_archive(results)
                        if zip_path and os.path.exists(zip_path):
                            # Кнопки скачивания
                            col1, col2 = st.columns(2)
                            with col1:
                                with open(zip_path, 'rb') as f:
                                    st.download_button(
                                        label="📦 Скачать ZIP архив",
                                        data=f.read(),
                                        file_name=os.path.basename(zip_path),
                                        mime="application/zip"
                                    )
                            with col2:
                                with open(csv_path, 'rb') as f:
                                    st.download_button(
                                        label="📊 Скачать отчет (CSV)",
                                        data=f.read(),
                                        file_name=os.path.basename(csv_path),
                                        mime="text/csv"
                                    )
                            # Информация о файлах
                            zip_size = os.path.getsize(zip_path) / (1024 * 1024)
                            st.info(f"Размер архива: {zip_size:.2f} MB")

    @staticmethod
    def render_statistics_tab():
        """Отрисовка вкладки статистики"""
        st.header("📊 Статистика и аналитика")
        if st.session_state['processed_count'] == 0:
            st.info("📈 Статистика появится после обработки данных")
            return
        # Основные метрики
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Всего обработано", st.session_state['processed_count'])
        with col2:
            if st.session_state['batch_results']:
                success_rate = (
                    sum(1 for r in st.session_state['batch_results'] if r['status'] == 'success') /
                    len(st.session_state['batch_results']) * 100
                )
                st.metric("Успешность", f"{success_rate:.1f}%")
        with col3:
            st.metric("Текущий шаблон", 
                     InfographicTemplates.TEMPLATES[st.session_state['current_template']]['name'])
        with col4:
            st.metric("Формат экспорта", st.session_state['export_settings']['format'])
        # Графики и детальная статистика
        if st.session_state['batch_results']:
            st.subheader("📈 Детальная статистика последней обработки")
            results_df = pd.DataFrame(st.session_state['batch_results'])
            if 'status' in results_df.columns:
                status_counts = results_df['status'].value_counts()
                col1, col2 = st.columns(2)
                with col1:
                    st.bar_chart(status_counts)
                with col2:
                    st.dataframe(status_counts)
            if (st.session_state['processing_stats']['start_time'] and 
                st.session_state['processing_stats']['end_time']):
                duration = (
                    st.session_state['processing_stats']['end_time'] - 
                    st.session_state['processing_stats']['start_time']
                ).total_seconds()
                if duration > 0 and len(results_df) > 0:
                    speed = len(results_df) / duration
                    st.metric("Скорость обработки", f"{speed:.2f} изобр/сек")

    @staticmethod
    def render_instructions_tab():
        """Отрисовка вкладки инструкций"""
        st.header("📚 Инструкция по использованию")
        with st.expander("📊 Подготовка Excel файла", expanded=True):
            st.markdown("""
            ### Требования к Excel файлу:
            1. **Формат файла**: .xlsx или .xls
            2. **Первая строка**: должна содержать заголовки колонок
            3. **Обязательные данные**:
               - Названия товаров
               - URL изображений (прямые ссылки)
               - Цены и характеристики
            ### Рекомендуемая структура:
            ```
            | Название      | URL картинки                  | Цена     | Характеристики      | Скидка |
            |---------------|-------------------------------|----------|---------------------|--------|
            | Смартфон Xiaomi | https://example.com/phone.jpg | 24 999 ₽ | 128GB, 8GB RAM     | -17%   |
            | Наушники Sony  | https://example.com/hp.jpg    | 8 499 ₽  | Bluetooth 5.0      | -23%   |
            ```
            ### Как получить прямые ссылки на изображения:
            - **Маркетплейсы**: Правая кнопка → "Копировать адрес изображения"
            - **Google Drive**: Измените ссылку на: `https://drive.google.com/uc?id=ID_ФАЙЛА`
            - **Свои изображения**: Загрузите на хостинг изображений
            """)
        with st.expander("⚙️ Настройка маппинга колонок"):
            st.markdown("""
            ### Что такое маппинг колонок?
            Это соответствие между колонками в вашем Excel файле и элементами инфографики.
            ### Стандартный маппинг:
            - **Верхний левый угол** → Название товара
            - **Верхний правый угол** → Цена
            - **Нижний левый угол** → Характеристики
            - **Нижний правый угол** → Скидка или доп. информация
            - **URL изображений** → Колонка с прямыми ссылками
            - **Имена файлов** → Колонка для генерации имен файлов
            ### Советы:
            1. Используйте кнопку "Автоподбор" для автоматического определения колонок
            2. Тестируйте маппинг в режиме предпросмотра
            3. Меняйте колонки для разных типов товаров
            """)
        with st.expander("🎨 Выбор шаблона"):
            st.markdown("""
            ### Доступные шаблоны:
            1. **📋 Стандартный** 
               - Для большинства товаров
               - Универсальный дизайн
               - Хорошая читаемость
            2. **⭐ Премиум**
               - Для люксовых товаров
               - Сдержанный дизайн
               - Акцент на бренде
            3. **🔥 Акционный**
               - Для распродаж
               - Яркие цвета
               - Крупный текст
            4. **📱 Вертикальный**
               - Для Instagram Stories
               - Вертикальная компоновка
               - Мобильная оптимизация
            ### Как выбрать:
            1. Протестируйте все шаблоны на разных товарах
            2. Учитывайте целевую аудиторию
            3. Следите за читаемостью текста
            """)
        with st.expander("⚡ Оптимизация скорости обработки"):
            st.markdown("""
            ### Рекомендации по настройкам:
            | Объем | Потоки | Размер партии | Таймаут |
            |-------|--------|---------------|---------|
            | До 100 | 4-8    | 50            | 15 сек  |
            | 100-1000 | 8-16  | 100-200       | 15 сек  |
            | 1000+ | 16-32   | 200-500       | 10 сек  |
            ### Что делать при ошибках:
            1. **Медленная загрузка** → Увеличьте таймаут
            2. **Ошибки памяти** → Уменьшите размер партии
            3. **Блокировка запросов** → Уменьшите количество потоков
            4. **Плохое качество** → Увеличьте качество экспорта
            ### Оптимальные настройки экспорта:
            - **Для сайтов**: JPEG, качество 85%, размер 1200px
            - **Для соцсетей**: PNG или WebP, качество 90%
            - **Для печати**: PNG, качество 100%, размер 3000px
            """)
        with st.expander("❌ Решение проблем"):
            st.markdown("""
            ### Частые проблемы и решения:
            1. **Не загружается Excel файл**
               - Проверьте формат (.xlsx или .xls)
               - Убедитесь, что файл не поврежден
               - Попробуйте сохранить файл заново
            2. **Не загружаются изображения**
               - Проверьте URL в браузере
               - Убедитесь, что ссылки прямые
               - Для Google Drive используйте правильный формат ссылки
            3. **Текст не виден на изображении**
               - Выберите другой шаблон
               - Уменьшите длину текста
               - Проверьте контрастность в предпросмотре
            4. **Медленная обработка**
               - Уменьшите количество потоков
               - Уменьшите размер партии
               - Проверьте скорость интернета
            5. **Ошибки памяти**
               - Закройте другие приложения
               - Уменьшите размер партии
               - Уменьшите целевую размер изображений
            """)

# ============================
# ОСНОВНОЙ КОД ПРИЛОЖЕНИЯ
# ============================
def main():
    """Основная функция приложения"""
    st.title("🎯 Генератор Инфографики v3.0")
    st.markdown("### Автоматическое создание инфографики из Excel файлов")
    st.markdown("---")
    
    # Инициализация классов
    generator = InfographicGenerator()
    ui = UIComponents()
    
    # Боковая панель
    ui.render_sidebar()
    
    # Основное содержимое
    if st.session_state.df is not None:
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
            # Дополнительные настройки имен файлов
            st.subheader("🏷️ Настройка имен файлов")
            col1, col2 = st.columns(2)
            with col1:
                add_prefix = st.checkbox("Добавить префикс", value=st.session_state['export_settings'].get('prefix', ''))
                if add_prefix:
                    prefix = st.text_input("Префикс", value=st.session_state['export_settings'].get('prefix', 'product_'))
                    st.session_state['export_settings']['prefix'] = prefix
            with col2:
                add_suffix = st.checkbox("Добавить суффикс", value=st.session_state['export_settings'].get('suffix', ''))
                if add_suffix:
                    suffix = st.text_input("Суффикс", value=st.session_state['export_settings'].get('suffix', '_promo'))
                    st.session_state['export_settings']['suffix'] = suffix
            # Автоподбор колонок
            if st.button("🔍 Автоподбор колонок"):
                suggestions = ExcelProcessor.get_column_suggestions(st.session_state.df)
                st.session_state['column_mapping'] = suggestions
                st.success("✅ Колонки автоматически подобраны!")
                st.experimental_rerun()
        
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
        st.markdown("""
        ## 🚀 Добро пожаловать в Генератор Инфографики!
        **Превратите ваши Excel данные в профессиональную инфографику за несколько кликов.**
        ### 📋 Как начать:
        1. **Подготовьте Excel файл** с данными о товарах
        2. **Загрузите файл** в боковой панели слева
        3. **Настройте соответствие** колонок элементам инфографики
        4. **Выберите шаблон** дизайна
        5. **Протестируйте** на одном товаре
        6. **Запустите массовую обработку**
        ### ⚡ Основные возможности:
        - ✅ **Поддержка Excel** (.xlsx, .xls)
        - ✅ **4 готовых шаблона** дизайна
        - ✅ **Автоподбор** колонок
        - ✅ **Пакетная обработка** с многопоточностью
        - ✅ **Экспорт** в PNG, JPEG, WebP
        - ✅ **Автоматическое создание ZIP** архива
        - ✅ **Подробная статистика** обработки
        ### 🎯 Идеально для:
        - 🛍️ **Интернет-магазины** - карточки товаров
        - 📱 **Соцсети** - посты для Instagram, Facebook
        - 📊 **Маркетплейсы** - Yandex Market, Ozon, Wildberries
        - 🏢 **B2B компании** - каталоги продукции
        - 🏷️ **Распродажи** - акционные баннеры
        """)
        st.markdown("---")
        st.markdown(
            "📁 Подготовьте ваш Excel файл и начните создавать профессиональную инфографику уже сегодня!"
        )
        # Пример структуры файла
        with st.expander("📋 Пример структуры Excel файла"):
            example_data = {
                "Название товара": ["Смартфон Xiaomi Redmi Note 12", "Наушники Sony WH-1000XM5"],
                "URL изображения": [
                    "https://example.com/xiaomi.jpg",
                    "https://example.com/sony.jpg"
                ],
                "Цена": ["24 999 ₽", "34 999 ₽"],
                "Старая цена": ["29 999 ₽", "39 999 ₽"],
                "Характеристики": ["128GB, 8GB RAM, AMOLED", "Шумоподавление, 30ч работы"],
                "Скидка": ["-17%", "-13%"],
                "Доставка": ["Бесплатно", "1-2 дня"]
            }
            example_df = pd.DataFrame(example_data)
            st.dataframe(example_df, use_container_width=True)
            # Кнопка для скачивания шаблона
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                example_df.to_excel(writer, index=False, sheet_name='Товары')
            st.download_button(
                label="📥 Скачать шаблон Excel файла",
                data=buffer.getvalue(),
                file_name="шаблон_товары.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # Футер
    st.markdown("---")
    st.markdown(
        """
    <div style='text-align: center; color: #666; font-size: 0.9em;'>
        <p>Генератор Инфографики v3.0 | Поддержка Excel файлов | 
        Обработано изображений: <b>{processed_count}</b></p>
        <p>Для вопросов и предложений: support@example.com</p>
    </div>
    """.format(processed_count=st.session_state['processed_count']), unsafe_allow_html=True
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
