import logging
import re
import os
from PIL import Image
import pytesseract

# Настройка логирования
logger = logging.getLogger(__name__)

# Указываем путь к Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Устанавливаем переменную окружения TESSDATA_PREFIX
os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'
logger.info(f"TESSDATA_PREFIX set to: {os.environ.get('TESSDATA_PREFIX')}")

# Проверяем доступность языков Tesseract
try:
    available_langs = pytesseract.get_languages()
    logger.info(f"Available Tesseract languages: {available_langs}")
    if 'rus' not in available_langs:
        logger.error("Russian language pack (rus) is not available in Tesseract")
except Exception as e:
    logger.error(f"Failed to get Tesseract languages: {str(e)}")


def extract_grades(image_path):
    """
    Извлекает оценки из изображения аттестата с помощью OCR.

    Args:
        image_path (str): Путь к изображению.

    Returns:
        list: Список оценок (целые числа).
    """
    logger.info(f"Extracting grades from image: {image_path}")

    try:
        # Открываем изображение
        image = Image.open(image_path)

        # Запускаем OCR с минимальными настройками (как в прототипе)
        text = pytesseract.image_to_string(image, lang='rus')
        logger.debug(f"Extracted raw text: {text}")

        if not text:
            logger.warning("No text extracted from image")
            return []

        # Регулярное выражение для извлечения оценок (как в прототипе)
        grade_pattern = r'(\d)\s*\((отлично|хорошо|удовлетворительно|неудовлетворительно)\)'
        grades = []

        # Обрабатываем текст построчно
        for line in text.split('\n'):
            match = re.search(grade_pattern, line)
            if match:
                grade = int(match.group(1))
                grades.append(grade)
                logger.info(f"Found grade: {grade} (description: {match.group(2)})")

        if not grades:
            logger.warning("No valid grades found in the extracted text")

        return grades

    except Exception as e:
        logger.error(f"Error during OCR processing: {str(e)}", exc_info=True)
        return []


def calculate_average_grade(grades):
    """
    Вычисляет средний балл из списка оценок.

    Args:
        grades (list): Список оценок.

    Returns:
        float: Средний балл, округлённый до 1 знака после запятой, или None, если список пуст.
    """
    if not grades:
        logger.warning("No grades provided for average calculation")
        return None

    average = round(sum(grades) / len(grades), 1)
    logger.info(f"Calculated average grade: {average}, based on grades: {grades}")
    return average


def process_attestation_image(image_path):
    """
    Полный процесс обработки изображения аттестата: OCR, вычисление среднего балла.

    Args:
        image_path (str): Путь к изображению аттестата.

    Returns:
        float: Средний балл или None в случае ошибки.
    """
    logger.info(f"Processing attestation image: {image_path}")

    try:
        # Проверяем, существует ли файл
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            raise Exception(f"Image file not found: {image_path}")

        # Извлекаем оценки напрямую, без предварительной обработки
        grades = extract_grades(image_path)

        # Вычисляем средний балл
        average_grade = calculate_average_grade(grades)
        return average_grade

    except Exception as e:
        logger.error(f"Error processing attestation image: {str(e)}", exc_info=True)
        return None