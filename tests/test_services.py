import json
from unittest.mock import patch

import pytest

from src.services import easy_search


@pytest.mark.parametrize("search_term", ["супер", "РЖД", "Попол"])
def test_easy_search_logic(mock_transactions, search_term):

    # Ожидаемые транзакции
    expected = [
        t
        for t in mock_transactions
        if (search_term.lower() in str(t["Категория"]).lower()) or (search_term.lower() in str(t["Описание"]).lower())
    ]
    with patch("src.services.read_datafile", return_value=mock_transactions):
        result_json = easy_search(search_term)
    result = json.loads(result_json)
    assert len(result) == len(expected)
    assert result == expected
