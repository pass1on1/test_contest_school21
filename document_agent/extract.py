from __future__ import annotations

import re
from datetime import date

_SPACE_CHARS = "   "

_MONTH_STEMS = {
    "январ": 1, "феврал": 2, "март": 3, "апрел": 4, "май": 5, "мая": 5,
    "июн": 6, "июл": 7, "август": 8, "сентябр": 9, "октябр": 10,
    "ноябр": 11, "декабр": 12,
}

_AMOUNT_NEGATIVE_WORDS = ("ндс", "в том числе", "в т.ч.", "в т. ч.")
_AMOUNT_POSITIVE_WORDS = ("итого", "составляет", "стоимость", "к оплате", "сумму", "сумма")

_UNITS = {
    "ноль": 0, "один": 1, "одна": 1, "два": 2, "две": 2, "три": 3, "четыре": 4,
    "пять": 5, "шесть": 6, "семь": 7, "восемь": 8, "девять": 9,
    "десять": 10, "одиннадцать": 11, "двенадцать": 12, "тринадцать": 13,
    "четырнадцать": 14, "пятнадцать": 15, "шестнадцать": 16, "семнадцать": 17,
    "восемнадцать": 18, "девятнадцать": 19,
    "двадцать": 20, "тридцать": 30, "сорок": 40, "пятьдесят": 50,
    "шестьдесят": 60, "семьдесят": 70, "восемьдесят": 80, "девяносто": 90,
    "сто": 100, "двести": 200, "триста": 300, "четыреста": 400, "пятьсот": 500,
    "шестьсот": 600, "семьсот": 700, "восемьсот": 800, "девятьсот": 900,
}
_MULTIPLIERS = {
    "тысяча": 1_000, "тысячи": 1_000, "тысяч": 1_000,
    "миллион": 1_000_000, "миллиона": 1_000_000, "миллионов": 1_000_000,
}

_AMOUNT_RE = re.compile(
    r"(?P<num>\d(?:[\d\s.,]*\d)?)\s*(?:\([^)]*\)\s*)?"
    r"(?:руб(?:ль|ля|лей|\.)?|₽|RUB)(?!\w)",
    re.IGNORECASE,
)
_RUB_KOP_RE = re.compile(
    r"(?P<rub>\d(?:[\d\s.,]*\d)?)\s*руб\.?\s*(?P<kop>\d{1,2})\s*коп",
    re.IGNORECASE,
)
_INN_RE = re.compile(r"ИНН(?:/КПП)?[:\s]*(\d{10,12})", re.IGNORECASE)
_COMPANY_RE = re.compile(
    r"(?:ООО|АО|ЗАО|ПАО|ОАО)\s*«[^»]+»"
    r"|ИП\s+[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.\s*[А-ЯЁ]\.",
)
_SUBJECT_RE = re.compile(r"Предмет\s*:\s*(.+)", re.IGNORECASE)

_DATE_TOKEN_RE = re.compile(
    r"\b(?P<d1>\d{1,2})\.(?P<m1>\d{1,2})\.(?P<y1>\d{2,4})\b"
    r"|\b(?P<d2>\d{1,2})/(?P<m2>\d{1,2})/(?P<y2>\d{2,4})\b"
    r"|\b(?P<d3>\d{1,2})\s+(?P<mon3>[а-яё]+)\s+(?P<y3>\d{4})\s*г?\.?",
    re.IGNORECASE,
)


def extract(text: str) -> dict:
    return {
        "amount": _find_amount(text),
        "date": _find_date(text),
        "inn": _find_inn(text),
        "contractor": _find_contractor(text),
        "subject": _find_subject(text),
    }


def _normalize_number(raw: str) -> float:
    s = raw
    for ch in _SPACE_CHARS:
        s = s.replace(ch, "")
    s = s.strip()

    has_comma, has_dot = "," in s, "." in s
    if has_comma and has_dot:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif has_comma:
        head, _, tail = s.rpartition(",")
        if len(tail) == 2 and tail.isdigit():
            s = f"{head}.{tail}"
        else:
            s = s.replace(",", "")
    return float(s)


def _find_amount(text: str) -> float | None:
    candidates: list[tuple[int, float]] = []

    for m in _RUB_KOP_RE.finditer(text):
        try:
            value = _normalize_number(m.group("rub")) + int(m.group("kop")) / 100
        except ValueError:
            continue
        candidates.append((m.start(), value))

    for m in _AMOUNT_RE.finditer(text):
        try:
            value = _normalize_number(m.group("num"))
        except ValueError:
            continue
        candidates.append((m.start(), value))

    if not candidates:
        return _find_amount_in_words(text)

    best_value, best_score = None, None
    for pos, value in candidates:
        score = _score_amount_context(text[max(0, pos - 40): pos].lower())
        if best_score is None or score > best_score:
            best_score, best_value = score, value
    return best_value


def _score_amount_context(window: str) -> int:
    """Оценивает окно перед найденной суммой: итог с учётом НДС важнее, чем
    сумма самого НДС или "итого без НДС" (которая не является суммой к оплате)."""
    if re.search(r"итого\s+с\s+ндс", window):
        return 5
    if re.search(r"итого\s+без\s+ндс", window):
        return -5
    if any(w in window for w in ("в том числе ндс", "в т.ч. ндс", "в т. ч. ндс")):
        return -5
    if "ндс" in window:
        return -4
    if any(w in window for w in _AMOUNT_POSITIVE_WORDS):
        return 2
    return 0


def _find_amount_in_words(text: str) -> float | None:
    m = re.search(
        r"(?:составляет|сумму|стоимость)\s+([а-яёА-ЯЁ\s]+?)\s+рубл",
        text, re.IGNORECASE,
    )
    if not m:
        return None

    words = re.findall(r"[а-яё]+", m.group(1).lower())
    total, group, found = 0, 0, False
    for w in words:
        if w in _UNITS:
            group += _UNITS[w]
            found = True
        elif w in _MULTIPLIERS:
            total += (group or 1) * _MULTIPLIERS[w]
            group = 0
            found = True
    total += group
    return float(total) if found else None


def _find_inn(text: str) -> str | None:
    m = _INN_RE.search(text)
    return m.group(1) if m else None


def _find_contractor(text: str) -> str | None:
    m = _COMPANY_RE.search(text)
    return m.group(0) if m else None


def _find_subject(text: str) -> str | None:
    m = _SUBJECT_RE.search(text)
    if m:
        return m.group(1).strip().rstrip(".")
    return None


def _month_from_word(word: str) -> int | None:
    word = word.lower()
    for stem, num in _MONTH_STEMS.items():
        if word.startswith(stem):
            return num
    return None


def _safe_iso(year: int, month: int, day: int) -> str | None:
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None


def _parse_date_match(m: re.Match) -> str | None:
    if m.group("d1"):
        day, month, year = int(m.group("d1")), int(m.group("m1")), int(m.group("y1"))
        if year < 100:
            year += 2000
        return _safe_iso(year, month, day)

    if m.group("d2"):
        a, b, year = int(m.group("d2")), int(m.group("m2")), int(m.group("y2"))
        if year < 100:
            year += 2000
        # Слэш-формат неоднозначен (MM/DD/YY vs DD/MM/YY): если первое число
        # не может быть месяцем — это точно день, иначе считаем его месяцем
        # (следуя примеру из задания: 03/01/25 -> 2025-03-01).
        if a > 12:
            day, month = a, b
        else:
            month, day = a, b
        return _safe_iso(year, month, day)

    if m.group("d3"):
        month = _month_from_word(m.group("mon3"))
        if not month:
            return None
        return _safe_iso(int(m.group("y3")), month, int(m.group("d3")))

    return None


def _find_date(text: str) -> str | None:
    """Возвращает первую по тексту распознанную дату (обычно дата самого документа)."""
    for m in _DATE_TOKEN_RE.finditer(text):
        parsed = _parse_date_match(m)
        if parsed:
            return parsed
    return None
