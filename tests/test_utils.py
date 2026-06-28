import datetime
import json
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.utils import (cards_filtered, read_datafile, read_user_settings, start_data_filtered, str_to_datetime,
                       transaction_tu_rub)


@patch("builtins.open", side_effect=FileNotFoundError)
def test_read_exls_file_not_found(mock_open: MagicMock) -> None:
    """Тест обработки ошибки отсутствия файла."""
    result = read_datafile("nonexistent.exls")
    # вернула пустой список
    assert result == []
    # попытка открыть файл была
    assert mock_open.called


@patch("builtins.open", mock_open(read_data="некорректный exls {]"))
def test_read_datafile_exls_decode_error() -> None:
    """Тест обработки некорректного xlsx."""
    result = read_datafile("test_invalid.exls")
    assert result == []


@pytest.mark.parametrize(
    "num_card, expected",
    [
        ("*1235", "1235"),
        ("*4851235", "1235"),
        ("235", ""),
        ("", ""),
    ],
)
def test_cards_filtered_correct(num_card: str, expected: str) -> None:
    """Тест правильности обработка различных номеров"""
    result = cards_filtered(num_card)
    assert result == expected


@pytest.mark.parametrize("num_card", [1235])
def test_cards_filtered__wrong_type(num_card: str) -> None:
    """Тест вызова ошибки TypeError"""
    with pytest.raises(TypeError):
        cards_filtered(num_card)


@pytest.mark.parametrize(
    "start_date, start_range,  expected",
    [
        (
            "2026-04-01 00:00:00",
            "w",
            (datetime.datetime(2026, 3, 30, 0, 0, 0), datetime.datetime(2026, 4, 1, 0, 0, 0)),
        ),
        (
            "2026-04-01 00:00:00",
            "ALL",
            (datetime.datetime(1000, 1, 1, 0, 0, 0), datetime.datetime(2026, 4, 1, 0, 0, 0)),
        ),
        (
            "2026-04-20 00:00:00",
            "M",
            (datetime.datetime(2026, 4, 1, 0, 0, 0), datetime.datetime(2026, 4, 20, 0, 0, 0)),
        ),
        ("2026-04-01 00:00:00", "y", (datetime.datetime(2026, 1, 1, 0, 0, 0), datetime.datetime(2026, 4, 1, 0, 0, 0))),
    ],
)
def test_start_data_filtered(start_date: str, start_range: str, expected: str) -> None:
    """Тест правильности обработка различных номеров"""
    result = start_data_filtered(start_date, start_range)
    assert result == expected


@pytest.mark.parametrize(
    "input_str,expected_year,expected_month,expected_day",
    [
        # Формат 1: "%d.%m.%Y %H:%M:%S"
        ("27.06.2024 14:30:05", 2024, 6, 27),
        ("01.01.2000 00:00:00", 2000, 1, 1),
        # Формат 2: "%Y-%m-%d %H:%M:%S"
        ("2024-06-27 14:30:05", 2024, 6, 27),
        # Формат 3: "%d.%m.%Y"
        ("27.06.2024", 2024, 6, 27),
        # Формат 4: "%Y-%m-%d"
        ("2024-06-27", 2024, 6, 27),
        # Формат 5: "%d/%m/%Y %H:%M"
        ("27/06/2024 14:30", 2024, 6, 27),
        # Граничные даты (високосный год и т.п.)
        ("29.02.2024", 2024, 2, 29),
        ("31.12.2023", 2023, 12, 31),
    ],
)
def test_str_to_datetime_success(input_str, expected_year, expected_month, expected_day):
    """Проверка корректных данных"""
    result = str_to_datetime(input_str)
    assert result is not None
    assert isinstance(result, datetime.datetime)
    assert result.year == expected_year
    assert result.month == expected_month
    assert result.day == expected_day


def test_str_to_datetime_incorrect():
    """Проверка некорректных данных"""
    result = str_to_datetime("11-2-23")
    assert result is None


@pytest.mark.parametrize(
    "key,expected_result",
    [
        ("user_currencies", ["RUB", "USD", "EUR"]),
        ("user_stocks", ["GAZP", "SBER", "YNDX"]),
        ("unknown_key", []),  # ключ не существует -> пустой список
    ],
)
def test_read_user_settings(key, expected_result):
    mock_data = {key: expected_result}
    m = mock_open(read_data=json.dumps(mock_data))
    # Мокаем open внутри модуля, где определена read_user_settings
    with patch("src.utils.open", m, create=True):
        result = read_user_settings(key)
    assert result == expected_result
    m.assert_called_once()  # проверяем, что файл реально открыли


@pytest.mark.parametrize(
    "rates",
    [
        ({"USD": 90.0, "EUR": 100.0}),
    ],
)
def test_transaction_tu_rub_conversion(mock_transactions, rates):
    with patch("src.utils.exchange_rates", return_value=rates) as mock_rates:
        result = transaction_tu_rub(mock_transactions)
    # Проверка, что exchange_rates вызвали ровно 1 раз
    mock_rates.assert_called_once()
    # Проверяем, что RUB не изменился
    assert result[0]["Валюта платежа"] == "RUB"
    assert result[0]["Сумма платежа"] == -100.0
    # Проверяем конвертацию EUR
    assert result[2]["Валюта платежа"] == "RUB"
    assert abs(result[2]["Сумма платежа"]) == 25000  # допуск на float
    # Проверяем конвертацию EUR
    assert result[4]["Валюта платежа"] == "RUB"
    assert abs(result[4]["Сумма платежа"]) == 28800


def test_transaction_tu_rub_conversion_no_rates(mock_transactions):
    rates = []
    with patch("src.utils.exchange_rates", return_value=rates) as mock_rates:
        result = transaction_tu_rub(mock_transactions)
    mock_rates.assert_called_once()
    assert result == mock_transactions
