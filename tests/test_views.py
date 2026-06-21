import datetime
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.views import cards_filtered, read_datafile


@patch("builtins.open", side_effect=FileNotFoundError)
def test_read_exls_file_not_found(mock_open: MagicMock) -> None:
    """Тест обработки ошибки отсутствия файла."""
    result = read_datafile("nonexistent.exls")
    # вернула пустой список
    assert result == []
    # попытка открыть файл была
    assert mock_open.called


@patch("builtins.open", mock_open(read_data="некорректный exls {]"))
def test_exls_decode_error() -> None:
    """Тест обработки некорректного xlsx."""
    result = read_datafile("test_invalid.exls")
    assert result == []


@pytest.mark.parametrize("num_card, expected", [
    ("*1235", "1235"),
    ("*4851235", "1235"),
    ("235", ""),
    ("", ""),
])
def test_cards_filtered_correct(num_card: str, expected: str) -> None:
    """Тест правильности обработка различных номеров"""
    result = cards_filtered(num_card)
    assert result == expected


@pytest.mark.parametrize("num_card", [(1235)])
def test_cards_filtered__wrong_type(num_card: str) -> None:
    """Тест вызова ошибки TypeError"""
    with pytest.raises(TypeError):
        cards_filtered(num_card)
