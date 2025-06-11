import pytesseract
from PIL import Image
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


# Функция для подсчета оценок
def podschet_ocenok(put_k_izobrazheniyu):
    # Открываем изображение
    izobrazhenie = Image.open(put_k_izobrazheniyu)

    # Преобразуем в градации серого
    izobrazhenie = izobrazhenie.convert('L')

    # Выполняем OCR с русским языком и настройками для таблицы
    tekst = pytesseract.image_to_string(izobrazhenie, lang='rus', config='--psm 4 --oem 3')

    # Выводим извлеченный текст для отладки
    print(f"Извлеченный текст из {put_k_izobrazheniyu}:\n{tekst}\n")

    # Список всех найденных оценок (только из резервного поиска)
    otsenki = []

    # Резервный поиск оценок в строках с признаками
    lines = tekst.split('\n')
    # Расширенный список ключевых слов с вариантами опечаток
    keywords = ['удовл', 'хорош', 'отлич', 'баова', 'оронко', 'удова', 'хороше', 'бдовь', 'отлично']

    for line in lines:
        # Проверяем, содержит ли строка предмет или ключевое слово
        if any(predmet in line.lower() for predmet in predmety) or any(
                x in line.lower() for x in keywords):

            # Игнорируем цифры, идущие ДО первой буквы в строке
            # Находим позицию первой буквы в строке
            first_letter_pos = None
            for i, char in enumerate(line):
                if char.isalpha():
                    first_letter_pos = i
                    break

            # Если в строке нет букв - пропускаем
            if first_letter_pos is None:
                continue

            # Ищем оценки только после первой буквы
            substr_after_letters = line[first_letter_pos:]

            # Упрощенное регулярное выражение для поиска оценок
            matches = re.finditer(r'\b([3-5])\b', substr_after_letters.lower())
            for match in matches:
                number = match.group(1)
                if number:
                    otsenki.append(number)
                    print(f"Резерв: найдена оценка {number} в строке: '{line.strip()}'")

    # Выводим массив всех найденных оценок
    print(f"Найденные оценки в {put_k_izobrazheniyu}: {otsenki}")

    return len(otsenki)  # Возвращаем общее количество


# Пример использования
puti_k_izobrazheniyam = [
    r'C:\Users\DNS\PycharmProjects\applicant-cabinet\backend\media\attestations\122886_41814.png'
]

for put in puti_k_izobrazheniyam:
    total_ocenok = podschet_ocenok(put)
    print(f"Общее количество оценок в {put}: {total_ocenok}")