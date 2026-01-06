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

# признаки PRO-моделей (ТОЛЬКО для строк с айфонами)
PRO_LINE_RE = re.compile(
    r"\b(pro max|pro)\b",
    re.IGNORECASE
)

# ================== HELPERS ==================

def normalize_price(raw: str) -> int:
    return int(raw.replace(".", "").replace(" ", ""))

def format_price(n: int) -> str:
    return f"{n:,}".replace(",", ".")

def is_price_line(line: str) -> bool:
    l = line.lower()
    return not any(k in l for k in IGNORE_LINE_KEYWORDS)

def is_pro_line(line: str) -> bool:
    return bool(PRO_LINE_RE.search(line))

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
            
            # Если есть пустая строкой после уценки - тоже пропускаем
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

def contains_active_keyword(line: str) -> bool:
    """
    Проверяет, содержит ли строка слова 'актив' или 'предактив' 
    в любом регистре, на русском или английском, с любыми символами вокруг.
    """
    # Приводим к нижнему регистру для универсальной проверки
    lower_line = line.lower()
    
    # Русские варианты
    if ('актив' in lower_line or 'предактив' in lower_line):
        return True
    
    # Английские варианты (ACTIVE, Active и т.д.)
    if 'active' in lower_line:
        return True
    
    return False

def is_emoji_only_line(line: str) -> bool:
    """
    Проверяет, состоит ли строка ТОЛЬКО из эмодзи, пунктуации и пробелов.
    Если в строке есть хотя бы одна буква или цифра - это не 'эмодзи-строка'.
    """
    if not line.strip():  # Пустая строка или только пробелы
        return False
    
    # Удаляем все эмодзи, пунктуацию и пробелы
    # \p{So} - категория Unicode "Symbol, Other" (эмодзи)
    # \p{P} - пунктуация
    # \s - пробельные символы
    cleaned = re.sub(r'[\p{So}\p{P}\s]', '', line, flags=re.UNICODE)
    
    # Если после очистки ничего не осталось - значит строка состоит только из эмодзи/пунктуации
    return len(cleaned) == 0

def clean_text_advanced(text: str) -> str:
    """
    Основная функция очистки текста:
    1. Удаляет строки с 'актив'/'предактив'/'active'
    2. Удаляет строки, состоящие только из эмодзи/спецсимволов
    3. Удаляет пустые строки в начале/конце
    """
    lines = text.splitlines()
    cleaned_lines = []
    
    for line in lines:
        # Пропускаем строки с ключевыми словами активности
        if contains_active_keyword(line):
            continue
        
        # Пропускаем строки, состоящие только из эмодзи/спецсимволов
        if is_emoji_only_line(line):
            continue
        
        # Оставляем нормальные строки
        cleaned_lines.append(line)
    
    # Собираем обратно, удаляя лишние пустые строки
    result = "\n".join(cleaned_lines)
    # Убираем множественные пустые строки, оставляя максимум одну подряд
    result = re.sub(r'\n{3,}', '\n\n', result)
    # Убираем пустые строки в начале и конце
    return result.strip()

# ================== CORE FUNCTION ==================

def replace_prices_in_text(
    text: str,
    pro_delta: int,
    default_delta: int,
    min_zero: int = 0,
    min_ignore: int = 0
):
    """
    ЛОГИКА (ВАЖНО):
    - анализ ТОЛЬКО построчно
    - Pro / Pro Max → pro_delta
    - обычные / Air → default_delta
    - "17 256" НЕ ТРОГАЕМ
    - Удаляет абзацы с уценкой
    - Заменяет 📱📱📱 на @perviykremlevskiy 📱
    - Удаляет строки с 'актив', 'предактив', 'active'
    - Удаляет строки только из эмодзи/спецсимволов
    """
    
    # ШАГ 0: Расширенная очистка текста
    text = clean_text_advanced(text)
    
    # ШАГ 1: Заменяем эмодзи телефонов
    text = replace_phones_emoji(text)
    
    changed = False
    lines = text.splitlines()
    new_lines = []

    for line in lines:
        original_line = line

        # пропускаем строки без товарных цен
        if not is_price_line(line):
            new_lines.append(line)
            continue

        pro_line = is_pro_line(line)

        def repl(m):
            nonlocal changed
            raw_price = m.group(1)

            price = normalize_price(raw_price)

            delta = pro_delta if pro_line else default_delta
            new_price = price - delta

            if new_price <= min_ignore:
                return raw_price
            if new_price < min_zero:
                new_price = min_zero

            changed = True
            return format_price(new_price)

        line = PRICE_RE.sub(repl, line)
        new_lines.append(line)

    result_text = "\n".join(new_lines)
    
    # ШАГ 2: Удаляет абзацы с уценкой
    result_text = remove_discount_paragraph(result_text)
    
    return result_text, changed
