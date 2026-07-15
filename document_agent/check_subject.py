"""Проверка соответствия предмета оплаты условиям льготной сельхоз-программы.

Реализация без внешних API: список разрешённых сельхоз-категорий против
списка типичных "не сельхоз" категорий, сопоставление по ключевым словам.
Это одновременно основной подход и offline-fallback, требуемый заданием —
дополнительно подключать LLM в условиях жёсткого дедлайна не стали (см. RESULTS.md).
"""
from __future__ import annotations

_POSITIVE_CATEGORIES: dict[str, list[str]] = {
    "агрохимия": [
        "удобрен", "агрохим", "гербицид", "фунгицид", "пестицид", "кас-32",
        "средства защиты растений", "почвенный анализ", "обследование угодий",
    ],
    "семена": ["семен", "семян", "посевн", "сорт"],
    "техника": ["комбайн", "трактор", "сельхозтехник", "зерноуборочн", "мтз"],
    "топливо": ["топлив", "дизел", "гсм"],
    "запчасти": ["запчаст", "запасных частей", "запасные части"],
    "полевые работы": [
        "полевых работ", "обработка почвы", "внесение удобрений",
        "агрохимических работ",
    ],
    "страхование урожая": ["страхование урожая", "страхование посевов"],
}

_NEGATIVE_CATEGORIES: dict[str, list[str]] = {
    "аренда офиса": ["аренда офис", "офисного помещения"],
    "юридические услуги": ["юридическ", "консультационные услуги"],
    "офисные товары": ["офисной мебел", "канцеляр"],
    "маркетинг/IT": ["сайт", "seo", "продвижен"],
    "клининг": ["клининг", "уборка администра"],
    "обучение персонала": ["обучение", "механизаторов работе"],
    "аренда техники": ["аренда сельскохозяйственной техники", "аренда техники"],
    "консультации": ["консультант", "консультации"],
    "транспортные услуги": ["транспортные услуги", "доставке", "перевозк"],
}

_BASE_CONFIDENCE = 0.55
_CONFIDENCE_STEP = 0.15
_MAX_CONFIDENCE = 0.95


def check_subject(subject: str) -> tuple[bool, float, str]:
    """Возвращает (соответствует, уверенность, объяснение) для предмета оплаты."""
    lowered = subject.lower()

    pos_hits = [
        (cat, kw)
        for cat, keywords in _POSITIVE_CATEGORIES.items()
        for kw in keywords
        if kw in lowered
    ]
    neg_hits = [
        (cat, kw)
        for cat, keywords in _NEGATIVE_CATEGORIES.items()
        for kw in keywords
        if kw in lowered
    ]

    pos_score, neg_score = len(pos_hits), len(neg_hits)

    if pos_score and not neg_score:
        category = pos_hits[0][0]
        confidence = min(_MAX_CONFIDENCE, _BASE_CONFIDENCE + _CONFIDENCE_STEP * pos_score)
        return True, round(confidence, 2), f"предмет относится к категории '{category}'"

    if neg_score and not pos_score:
        category = neg_hits[0][0]
        confidence = min(_MAX_CONFIDENCE, _BASE_CONFIDENCE + _CONFIDENCE_STEP * neg_score)
        return False, round(confidence, 2), f"'{category}' не относится к сельхоз-деятельности"

    if pos_score and neg_score:
        matches = pos_score > neg_score
        confidence = round(0.5 + 0.05 * abs(pos_score - neg_score), 2)
        pos_cat, neg_cat = pos_hits[0][0], neg_hits[0][0]
        verdict = "скорее соответствует" if matches else "скорее не соответствует"
        reason = (
            f"пограничный случай: есть признаки '{pos_cat}', но также '{neg_cat}' "
            f"— {verdict} программе"
        )
        return matches, confidence, reason

    return False, 0.5, "не найдено ключевых признаков сельхоз-программы"
