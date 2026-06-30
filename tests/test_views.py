from datetime import datetime
from typing import Dict, List
from unittest.mock import patch

import pytest

from src.views import cards_total_spent, exchange_rates_for_settings, filter_transactions_by_date, top_5_transactions


@pytest.fixture
def test_transactions() -> List[Dict]:
    return [
        {"Номер карты": "4276123456789012", "Сумма платежа": -150.50},  # Трата
        {"Номер карты": "4276123456789012", "Сумма платежа": 200.00},  # Приход
        {"Номер карты": "5469987654321098", "Сумма платежа": -300.00},
        {"Номер карты": "5469987654321098", "Сумма платежа": -50.00},
    ]


@patch("src.utils.cards_filtered")
def test_cards_total_spent_basic(mock_cards_filtered, test_transactions):
    # Настраиваем мок для cards_filtered: пусть возвращает последние 4 цифры как есть
    mock_cards_filtered.side_effect = lambda x: str(x)[-4:]

    result = cards_total_spent(test_transactions)

    # Проверка длины результата
    assert len(result) == 2

    # Поиск записей по картам для удобной проверки
    card_1 = next(item for item in result if item["last_digits"] == "9012")
    card_2 = next(item for item in result if item["last_digits"] == "1098")

    assert card_1["total_spent"] == 49.5
    assert card_1["cashback"] == 0.49

    assert card_2["total_spent"] == 350.0
    assert card_2["cashback"] == 3.5


@patch("src.utils.transaction_tu_rub")
def test_top_5_with_provided_data(mock_tu_rub, mock_transactions):
    # Мокаем transaction_tu_rub: возвращаем те же данные, чтобы тестировать только логику топ‑5
    mock_tu_rub.return_value = mock_transactions

    result = top_5_transactions(mock_transactions)  # аргумент не важен: mock подменит результат

    # 1. Должно быть ровно 5 транзакций
    assert len(result) == 5

    # 2. Проверяем, что FAILED-транзакция (первая в списке) исключена
    failed_date = "10.05.2025 10:00:00"
    assert not any(r["date"] == failed_date for r in result)

    expected_amounts = [1050.0, 800.0, 350.0, 100, 70.0]
    amounts = [r["amount"] for r in result]
    assert amounts == expected_amounts

    # 4. Проверяем структуру и переименование колонок
    first = result[0]
    assert set(first.keys()) == {"date", "amount", "category", "description"}

    # 5. Проверяем соответствие данных (на примере первой записи)
    assert first["amount"] == 1050.0
    assert first["category"] == "Супермаркеты"
    assert "Mouse Tail" in first["description"]


@patch("src.views.exchange_rates")
@patch("src.views.read_user_settings")
def test_exchange_rates_basic(mock_read, mock_exch):
    # Настраиваем моки
    mock_read.return_value = ["USD", "EUR", "JPY"]
    mock_exch.return_value = {
        "USD": 74.621,
        "EUR": 85.484,
        "JPY": 0.512,
        "CNY": 10.333,
    }

    result = exchange_rates_for_settings()

    assert len(result) == 3
    assert result == [
        {"currency": "USD", "rate": 74.62},
        {"currency": "EUR", "rate": 85.48},
        {"currency": "JPY", "rate": 0.51},
    ]


@pytest.fixture
def sample_transactions():
    return [
        {"Дата операции": "01.05.2024 10:00:00", "Сумма": -100},
        {"Дата операции": "15.05.2024 12:30:00", "Сумма": -200},
        {"Дата операции": "31.05.2024 09:15:00", "Сумма": -300},
        {"Дата операции": "01.06.2024 18:45:00", "Сумма": -400},  # вне мая
        {"Сумма": -500},  # нет даты — должна быть пропущена
    ]


# --- Тест 1: Базовый сценарий (M — месяц) ---
@patch("src.views.start_data_filtered")
def test_filter_by_month(mock_start_data, sample_transactions):
    # Мокаем start_data_filtered: пусть вернёт 1–31 мая 2024
    start_range = datetime(2024, 5, 1, 0, 0, 0)
    end_range = datetime(2024, 5, 31, 23, 59, 59)
    mock_start_data.return_value = (start_range, end_range)

    result = filter_transactions_by_date(sample_transactions, "2024-05-15", "M")

    # Проверяем, что start_data_filtered был вызван с нужными аргументами
    mock_start_data.assert_called_once_with("2024-05-15", "M")
    # Ожидаем только транзакции за май 2024 (без 1 июня и без записи без даты)
    assert len(result) == 3
    dates = [t["Дата операции"] for t in result]
    assert "01.05.2024 10:00:00" in dates
    assert "15.05.2024 12:30:00" in dates
    assert "31.05.2024 09:15:00" in dates
    assert "01.06.2024 18:45:00" not in dates


# --- Тест 2: Неделя (W) ---
@patch("src.views.start_data_filtered")
def test_filter_by_week(mock_start_data, sample_transactions):
    # Допустим, start_data_filtered для W возвращает нужный диапазон
    start_range = datetime(2024, 5, 13, 0, 0, 0)
    end_range = datetime(2024, 5, 19, 23, 59, 59)
    mock_start_data.return_value = (start_range, end_range)

    result = filter_transactions_by_date(sample_transactions, "2024-05-15", "W")

    mock_start_data.assert_called_once_with("2024-05-15", "W")
    # В диапазон 13–19 мая попадает только 15.05
    assert len(result) == 1
    assert result[0]["Дата операции"] == "15.05.2024 12:30:00"


# --- Тест 3: Год (Y) ---
@patch("src.views.start_data_filtered")
def test_filter_by_year(mock_start_data, sample_transactions):
    start_range = datetime(2024, 1, 1, 0, 0, 0)
    end_range = datetime(2024, 12, 31, 23, 59, 59)
    mock_start_data.return_value = (start_range, end_range)

    result = filter_transactions_by_date(sample_transactions, "2024-05-15", "Y")

    mock_start_data.assert_called_once_with("2024-05-15", "Y")
    # Все транзакции за 2024 год (кроме той, где нет даты)
    assert len(result) == 4


# --- Тест 4: ALL — все данные до указанной даты ---
@patch("src.views.start_data_filtered")
def test_filter_all_until_date(mock_start_data, sample_transactions):
    # ALL означает «от начала времён до указанной даты»
    start_range = datetime.min
    end_range = datetime(2024, 5, 15, 23, 59, 59)  # до 15 мая включительно
    mock_start_data.return_value = (start_range, end_range)

    result = filter_transactions_by_date(sample_transactions, "2024-05-15", "ALL")

    mock_start_data.assert_called_once_with("2024-05-15", "ALL")
    # Должны попасть 01.05 и 15.05; 31.05 уже после 15.05 — не попадает
    assert len(result) == 2
    dates = [t["Дата операции"] for t in result]
    assert "01.05.2024 10:00:00" in dates
    assert "15.05.2024 12:30:00" in dates
    assert "31.05.2024 09:15:00" not in dates


# --- Тест 5: Транзакция без поля "Дата операции" ---
@patch("src.views.start_data_filtered")
def test_skip_transactions_without_date(mock_start_data):
    transactions = [
        {"Дата операции": "01.05.2024 10:00:00"},
        {},  # нет даты
        {"Дата операции": ""},  # пустая строка
        {"Дата операции": None},
    ]
    start_range = datetime(2024, 5, 1, 0, 0, 0)
    end_range = datetime(2024, 5, 31, 23, 59, 59)
    mock_start_data.return_value = (start_range, end_range)

    result = filter_transactions_by_date(transactions, "2024-05-15", "M")
    # Только одна валидная запись
    assert len(result) == 1
    assert result[0]["Дата операции"] == "01.05.2024 10:00:00"


# --- Тест 6: Некорректный формат даты (ошибка strptime) ---
@patch("src.views.start_data_filtered")
def test_invalid_date_format_in_transaction(mock_start_data):
    transactions = [
        {"Дата операции": "01/05/2024 10:00:00"},  # неверный формат
        {"Дата операции": "01.05.2024 10:00:00"},
    ]
    start_range = datetime(2024, 5, 1, 0, 0, 0)
    end_range = datetime(2024, 5, 31, 23, 59, 59)
    mock_start_data.return_value = (start_range, end_range)
    with pytest.raises(ValueError):
        filter_transactions_by_date(transactions, "2024-05-15", "M")
