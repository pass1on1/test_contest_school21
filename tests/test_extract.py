from document_agent import extract


def test_amount_basic():
    assert extract("Сумма: 1 250 000,00 руб.")["amount"] == 1_250_000.0


def test_amount_dot_decimal():
    assert extract("Итого: 1250000.00 ₽")["amount"] == 1_250_000.0


def test_amount_us_style():
    assert extract("на сумму 1,250,000.00 RUB")["amount"] == 1_250_000.0


def test_inn():
    assert extract("ИНН 7701234567")["inn"] == "7701234567"


def test_inn_kpp_combo():
    assert extract("ИНН/КПП: 7701234567 / 770101001")["inn"] == "7701234567"


def test_amount_missing():
    assert extract("без цифр")["amount"] is None


def test_date_dot_format():
    assert extract("01.03.2025")["date"] == "2025-03-01"


def test_date_text_format():
    assert extract("1 марта 2025 г.")["date"] == "2025-03-01"


def test_date_slash_format():
    assert extract("03/01/25")["date"] == "2025-03-01"


def test_all_fields_none_on_empty_text():
    fields = extract("")
    assert fields == {
        "amount": None,
        "date": None,
        "inn": None,
        "contractor": None,
        "subject": None,
    }
