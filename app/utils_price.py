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

# ================== CORE ==================

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
    """

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

    return "\n".join(new_lines), changed
