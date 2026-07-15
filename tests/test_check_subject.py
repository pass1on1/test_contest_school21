from document_agent import check_subject


def test_matches_agrochemistry():
    matches, confidence, reason = check_subject("Поставка минеральных удобрений (карбамид марки Б)")
    assert matches is True
    assert confidence > 0.5
    assert reason


def test_rejects_office_rent():
    matches, confidence, reason = check_subject("Аренда офисного помещения, г. Краснодар")
    assert matches is False
    assert confidence > 0.5
    assert reason


def test_rejects_no_match_default():
    matches, confidence, reason = check_subject("нечто совершенно постороннее")
    assert matches is False
    assert reason
