import pytest
import pandas as pd
from src.reports import spending_by_category
from datetime import datetime

@pytest.fixture
def transactions_df():
    return pd.DataFrame([
        {"Дата операции": "10.05.2025 10:00:00", "Категория": "Супермаркеты", "Сумма платежа": -100.0},
        {"Дата операции": "10.01.2024 10:00:00", "Категория": "Супермаркеты", "Сумма платежа": -100.0},
        {"Дата операции": "15.02.2024 12:30:00", "Категория": "Супермаркеты", "Сумма платежа": -250.0},
        {"Дата операции": "20.03.2024 09:15:00", "Категория": "Рестораны", "Сумма платежа": -800.0},
        {"Дата операции": "05.04.2024 18:45:00", "Категория": "Супермаркеты", "Сумма платежа": -320.0},
        {"Дата операции": "01.12.2023 11:00:00", "Категория": "Супермаркеты", "Сумма платежа": -50.0},  # вне 3 месяцев
    ])


def test_spending_by_category_basic(transactions_df):

    result = spending_by_category(transactions_df, "Супермаркеты", '2024-04-11')

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 1
    assert result["Категория"].iloc[0] == "Супермаркеты"
    # сумма: -100 -250 -320 = -670
    assert abs(result["Сумма платежа"].iloc[0]) == 570.0


def test_spending_by_category_no_matches(transactions_df):
    """Проверка на отсутствие категории"""
    result = spending_by_category(transactions_df, category="Авиабилеты")

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0


def test_spending_by_category_invalid_date(transactions_df):
    """Проверка при невернном формате даты"""
    result = spending_by_category(transactions_df, "Супермаркеты", '20-04-11')

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0