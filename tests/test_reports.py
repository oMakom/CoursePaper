import pandas as pd

from src.reports import spending_by_category


def test_spending_by_category_basic(transactions_df):

    result = spending_by_category(transactions_df, "Супермаркеты", "2024-04-11")

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
    result = spending_by_category(transactions_df, "Супермаркеты", "20-04-11")

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0
