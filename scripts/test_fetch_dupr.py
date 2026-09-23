from fetch_dupr import is_french


def test_is_french():
    assert is_french({"shortAddress": "Paris, IDF, FR"})
    assert is_french({"shortAddress": "Saint-Denis, RE"})
    assert not is_french({"shortAddress": "Bromley, England, GB"})
    assert not is_french({"shortAddress": None})
