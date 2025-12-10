# app/utils_price.py
# Парсер/замена цен: распознает разные форматы и корректно вычитает дельту.

import re
import unicodedata
from typing import Tuple
from . import config

# Регулярка для поиска цен с учётом разных разделителей и валютных обозначений
PRICE_REGEX = re.compile(
    r'(?P<full>\b(?P<number>\d{1,3}(?:[ \u00A0\.,]\d{3})*(?:[,\.\d]+)?)\s*(?P<currency>руб(?:\.|ля|лей)?|₽|rur|rub|\$|usd|грн|uah|₴|€|eur|£|gbp)\b)',
    flags=re.IGNORECASE
)

# Нормализация Unicode и пробелов
def normalize_text(s: str) -> str:
    s = s or ""
    s = unicodedata.normalize("NFC", s)
    # убираем повторяющиеся пробелы, но не удаляем переводы строк
    s = re.sub(r'[ \u00A0]+', ' ', s)
    return s

# Преобразование числа из формата с точками/запятыми/пробелами в float
def parse_number(num_str: str) -> float:
    s = num_str.strip()
    if '.' in s and ',' in s:
        # скорее всего точка — тысячные, запятая — дробные
        s = s.replace('.', '').replace(',', '.')
    else:
        # убираем пробелы и неразрывные
        s = s.replace('\u00A0', '').replace(' ', '')
        # если есть запятая и нет точки — воспринимаем запятую как дробную
        if ',' in s and '.' not in s:
            s = s.replace(',', '.')
        else:
            # иначе удалим запятые как тысячные разделители
            s = s.replace(',', '')
    try:
        return float(s)
    except:
        return 0.0

# Форматирование обратно: если целое — без дробной части
def format_number(val: float) -> str:
    if abs(val - round(val)) < 0.0001:
        return str(int(round(val)))
    return f"{val:.2f}"

# Функция замены цен в тексте
def replace_prices_in_text(text: str, has_pro: bool, pro_delta: float=None, default_delta: float=None, min_to_zero: bool=True) -> Tuple[str,int]:
    if text is None:
        return text, 0
    text = normalize_text(text)
    pro_delta = pro_delta if pro_delta is not None else config.PRICE_PRO_DELTA
    default_delta = default_delta if default_delta is not None else config.PRICE_DEFAULT_DELTA
    replacements = 0

    def repl(m):
        nonlocal replacements
        full = m.group("full")
        num = m.group("number")
        cur = m.group("currency")
        value = parse_number(num)
        delta = pro_delta if has_pro else default_delta
        new_val = value - delta
        if min_to_zero and new_val < 0:
            new_val = 0.0
        new_num = format_number(new_val)
        replacements += 1
        # Сохраняем пробел между числом и валютой если был
        sep = " " if re.search(r'\d\s+\D', full) else ""
        return f"{new_num}{sep}{cur}"

    new_text = PRICE_REGEX.sub(repl, text)
    return new_text, replacements

# Функция поиска наличия слова PRO в строках (учёт Pro/PRO/Pro Max)
def detect_pro_in_text(text: str) -> bool:
    if not text:
        return False
    return bool(re.search(r'\bPRO\b', text, flags=re.IGNORECASE))
