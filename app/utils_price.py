# app/utils_price.py
import re

# ================== REGEX ==================

# Цена:
#  - 73.000
#  - 104.000.0
#  - 72500
#  - 104000
# ❌ НЕ ловим: "17 256"
PRICE_RE = re.compile(
    r"""
    (?<!\d )           # слева не "цифра+пробел"
    (?<!\d)            # слева не цифра
    (
        \d{1,3}(?:\.\d{3})+(?:\.0)?   # 73.000 | 104.000.0
        |
        \d{5,6}                        # 72500 | 104000
    )
    (?!\d)             # справа не цифра
    """,
    re.VERBOSE
)

# строки, где цена НЕ является ценой товара
IGNORE_LINE_KEYWORDS = [
    "гаранти",
    "месяц",
    "шт",
    "в пути",
    "ожидаем",
    "дополнительную",
    "чехол",
    "кабель",
    "заряд",
    "magsafe",
    "airpods",
    "battery",
    "depо",
]

# ================== HELPERS ==================

def normalize_price(raw: str) -> int:
    return int(raw.replace(".", "").replace(" ", ""))

def format_price(n: int) -> str:
    return f"{n:,}".replace(",", ".")

def is_price_line(line: str) -> bool:
    l = line.lower()
    return not any(k in l for k in IGNORE_LINE_KEYWORDS)

# ================== NEW FUNCTIONS ==================

def remove_discount_paragraph(text: str) -> str:
    """
    Удаляет абзац с уценкой по правилам:
    1. Ищем строку с 'Уценка'
    2. Удаляем эту строку и все последующие строки до пустой строки (включительно)
    """
    lines = text.splitlines()
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Проверяем, содержит ли строка "Уценка"
        if "уценка" in line.lower():
            # Пропускаем строку с "Уценка"
            i += 1
            
            # Пропускаем все непустые строки после "Уценка"
            while i < len(lines) and lines[i].strip() != "":
                i += 1
            
            # Если есть пустая строка после уценки - тоже пропускаем
            if i < len(lines) and lines[i].strip() == "":
                i += 1
            
            continue
        
        # Добавляем строку, если она не в удаляемом абзаце
        new_lines.append(line)
        i += 1
    
    return "\n".join(new_lines)

def replace_phones_emoji(text: str) -> str:
    """
    Заменяет 📱📱📱 на @perviykremlevskiy 📱
    """
    return text.replace("📱📱📱", "@perviykremlevskiy 📱")

def is_active_at_start(line: str) -> bool:
    """
    Проверяет, находится ли слово 'актив'/'предактив'/'active' 
    в НАЧАЛЕ строки (после удаления пробелов).
    """
    line = line.strip().lower()
    
    # Проверяем, начинается ли строка с этих слов
    if line.startswith(('актив', 'предактив', 'active')):
        return True
    
    return False

def contains_active_keyword(line: str) -> bool:
    """
    Проверяет, содержит ли строка слова 'актив' или 'предактив' 
    в любом регистре, на русском или английском.
    """
    lower_line = line.lower()
    
    if ('актив' in lower_line or 'предактив' in lower_line or 'active' in lower_line):
        return True
    
    return False

def clean_text_advanced(text: str) -> str:
    """
    Основная функция очистки текста:
    1. Если 'актив' в НАЧАЛЕ строки → удаляет эту строку + строку над ней
    2. Если 'актив' НЕ в начале строки → удаляет только эту строку
    3. Строки со смайлами НЕ удаляются
    """
    lines = text.splitlines()
    cleaned_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Проверяем, содержит ли строка ключевые слова активности
        if contains_active_keyword(line):
            
            # Проверяем, находится ли 'актив' в НАЧАЛЕ строки
            if is_active_at_start(line):
                # 'Актив' в начале → удаляем эту строку + строку над ней
                if cleaned_lines and is_price_line(cleaned_lines[-1]):
                    cleaned_lines.pop()  # Удаляем строку над "Актив"
                # Саму строку с "Актив" в начале не добавляем
                i += 1
            else:
                # 'Актив' НЕ в начале → удаляем только эту строку
                i += 1
            
            continue
        
        # Оставляем нормальные строки (включая строки со смайлами)
        cleaned_lines.append(line)
        i += 1
    
    # Собираем обратно, удаляя лишние пустые строки
    result = "\n".join(cleaned_lines)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()

# ================== CORE FUNCTION ==================

def replace_prices_in_text(
    text: str,
    pro_delta: int,  # Параметр оставлен для совместимости, но не используется
    default_delta: int,  # Параметр оставлен для совместимости, но не используется
    min_zero: int = 0,
    min_ignore: int = 0
):
    """
    НОВАЯ ЛОГИКА (2025-12-27):
    - от ВСЕХ моделей дороже 10 000 рублей отнимаем 500 рублей
    - НЕТ разделения на PRO и обычные
    - анализ ТОЛЬКО построчно
    - "17 256" НЕ ТРОГАЕМ
    - Удаляет абзацы с уценкой
    - Заменяет 📱📱📱 на @perviykremlevskiy 📱
    - Удаляет строки с 'актив', 'предактив', 'active' по правилам:
        * Если в начале строки → удаляет строку + строку над ней
        * Если не в начале → удаляет только эту строку
    """
    
    # ШАГ 0: Расширенная очистка текста
    text = clean_text_advanced(text)
    
    # ШАГ 1: Заменяем эмодзи телефонов
    text = replace_phones_emoji(text)
    
    changed = False
    lines = text.splitlines()
    new_lines = []
    
    # Фиксированная дельта: -500 рублей для всех товаров дороже 10 000
    UNIFIED_DELTA = 500
    PRICE_THRESHOLD = 10000  # Минимальная цена для применения скидки

    for line in lines:
        original_line = line

        # пропускаем строки без товарных цен
        if not is_price_line(line):
            new_lines.append(line)
            continue

        # НОВАЯ ЛОГИКА: для ВСЕХ строк применяем одинаковую дельту
        def repl(m):
            nonlocal changed
            raw_price = m.group(1)

            price = normalize_price(raw_price)
            
            # Если цена меньше порога - не меняем
            if price <= PRICE_THRESHOLD:
                return raw_price
                
            new_price = price - UNIFIED_DELTA

            if new_price <= min_ignore:
                return raw_price
            if new_price < min_zero:
                new_price = min_zero

            changed = True
            return format_price(new_price)

        line = PRICE_RE.sub(repl, line)
        new_lines.append(line)

    result_text = "\n".join(new_lines)
    
    # ШАГ 2: Удаляем абзацы с уценкой
    result_text = remove_discount_paragraph(result_text)
    
    return result_text, changed
