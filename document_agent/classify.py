"""Классификация типа документа по ключевым словам с порогом уверенности."""
from __future__ import annotations

# Насколько разрыв между лучшим и вторым по счёту типом должен быть большим,
# чтобы не возвращать "unknown". Подобрано на dataset/: у распознаваемых
# документов разрыв обычно >= 4 (заголовок даёт вес*2), у scan_ocr_001.txt
# (испорченный OCR) все скоры нулевые и разрыва нет. Порог 2 отсекает случаи
# слабого одиночного совпадения без заголовка (шум), не отсекая уверенные
# распознавания. Больше порог -> больше документов уходит в "unknown" (выше
# точность, ниже полнота). Меньше порог -> риск уверенно классифицировать
# документы с случайным одиночным совпадением слова.
CONFIDENCE_GAP_THRESHOLD = 2

HEADER_WINDOW = 120
HEADER_WEIGHT_MULTIPLIER = 2

_KEYWORDS: dict[str, list[tuple[str, int]]] = {
    "contract": [
        # "поставщик"/"покупатель"/"стороны" намеренно не участвуют в скоринге:
        # это общие слова, которые часто встречаются и в счетах/актах
        # (например, как ссылка "Основание: Договор поставки ... от ...").
        ("договор поставки", 3),
        ("предмет договора", 2),
        ("сумма договора", 2),
        ("именуемое в дальнейшем", 2),
    ],
    "spec": [
        ("спецификация", 3),
        ("номенклатура", 1),
        ("итого без ндс", 2),
        ("к договору поставки", 2),
    ],
    "invoice": [
        ("счёт на оплату", 3),
        ("счет на оплату", 3),
        ("счёт №", 2),
        ("счет №", 2),
        ("к оплате", 1),
        ("исполнитель", 1),
        ("заказчик", 1),
    ],
    "act": [
        ("акт выполненных работ", 3),
        ("универсальный передаточный документ", 3),
        ("упд", 3),
        ("товар передан", 2),
        ("работы выполнены", 2),
        ("принял", 1),
    ],
}


def classify(text: str) -> tuple[str, float]:
    """Определяет тип документа (contract/spec/invoice/act/unknown) и уверенность 0..1."""
    lowered = text.lower()
    header = lowered[:HEADER_WINDOW]

    scores: dict[str, int] = {cat: 0 for cat in _KEYWORDS}
    for cat, keywords in _KEYWORDS.items():
        for kw, weight in keywords:
            if kw in header:
                scores[cat] += weight * HEADER_WEIGHT_MULTIPLIER
            elif kw in lowered:
                scores[cat] += weight

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top_cat, top_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0

    if top_score == 0:
        return "unknown", 0.0

    total = sum(scores.values())
    confidence = round(top_score / total, 2) if total else 0.0

    if top_score - second_score < CONFIDENCE_GAP_THRESHOLD:
        return "unknown", confidence

    return top_cat, confidence
