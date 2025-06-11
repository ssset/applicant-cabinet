# utils/ocr_utils.py
from PIL import Image
import pytesseract
import re

# Путь к исполняемому файлу Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Обновленный список предметов с дополнительными вариациями
predmety = [
    'русский язык', 'литература', 'алгебра', 'геометрия', 'математика',
    'информатика', 'история', 'обществознание', 'география', 'биология',
    'физика', 'химия', 'физкультура', 'музыка', 'изобразительное искусство',
    'технология', 'обж', 'о5ж', 'искусство', 'иностранный язык', 'английский язык',
    'живопись', 'опд', 'проектная деятельность'
]

def process_attestation_image(image_path):
    # Открываем изображение
    izobrazhenie = Image.open(image_path)

    # Преобразуем в градации серого
    izobrazhenie = izobrazhenie.convert('L')

    # Выполняем OCR с русским языком и настройками для таблицы
    tekst = pytesseract.image_to_string(izobrazhenie, lang='rus', config='--psm 4 --oem 3')

    # Выводим извлеченный текст для отладки
    print(f"Извлеченный текст из {image_path}:\n{tekst}\n")

    # Список всех найденных оценок
    otsenki = []

    # Резервный поиск оценок в строках с признаками
    lines = tekst.split('\n')
    keywords = ['удовл', 'хорош', 'отлич', 'баова', 'оронко', 'удова', 'хороше', 'бдовь', 'отлично']

    for line in lines:
        if any(predmet in line.lower() for predmet in predmety) or any(
                x in line.lower() for x in keywords):

            first_letter_pos = None
            for i, char in enumerate(line):
                if char.isalpha():
                    first_letter_pos = i
                    break

            if first_letter_pos is None:
                continue

            substr_after_letters = line[first_letter_pos:]

            matches = re.finditer(r'\b([3-5])\b', substr_after_letters.lower())
            for match in matches:
                number = match.group(1)
                if number:
                    otsenki.append(number)
                    print(f"Резерв: найдена оценка {number} в строке: '{line.strip()}'")

    # Выводим массив всех найденных оценок
    print(f"Найденные оценки в {image_path}: {otsenki}")

    # Расчет среднего балла
    if otsenki:
        average_grade = sum(int(grade) for grade in otsenki) / len(otsenki)
    else:
        average_grade = 0.0

    print(f"Средний балл в {image_path}: {average_grade:.2f}")
    return average_grade  # Возвращаем средний балл