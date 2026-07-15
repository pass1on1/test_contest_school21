from document_agent import classify


def test_invoice_classification():
    doc_type, confidence = classify("Счёт на оплату №12 от 01.03.2025 ...")
    assert doc_type == "invoice"
    assert confidence > 0.5


def test_unknown_on_no_keywords():
    doc_type, confidence = classify("бессвязный текст без опознавательных слов")
    assert doc_type == "unknown"
    assert confidence == 0.0


def test_contract_classification():
    doc_type, _ = classify(
        "ДОГОВОР ПОСТАВКИ № 1\nПредмет договора: поставка товара. "
        "Именуемое в дальнейшем Покупатель."
    )
    assert doc_type == "contract"


def test_act_classification():
    doc_type, _ = classify("АКТ ВЫПОЛНЕННЫХ РАБОТ № 1\nРаботы выполнены в полном объёме.")
    assert doc_type == "act"
