import datetime
from typing import Optional

import pandas as pd
from dateutil.relativedelta import relativedelta

from src.utils import str_to_datetime


def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    """
    Функция возвращает траты по заданной категории за последние три месяца (от переданной даты)
    Если дата не передана, то берется текущая дата.
    """
    # приводим стролюец 'Дата операции' к datetime
    transactions["Дата операции"] = pd.to_datetime(transactions["Дата операции"], format="%d.%m.%Y %H:%M:%S")
    if date is not None:
        # Пробуем преобразовать время, иначе указываем текущее
        if str_to_datetime(date):
            date_end = str_to_datetime(date)
        else:
            date_end = datetime.datetime.now()
    else:
        date_end = datetime.datetime.now()
    # Узнаем дату за 3 месяца до
    date_start = date_end - relativedelta(months=3)
    # все операции за указанный период
    result_data_transactions = transactions.query("@date_start <= `Дата операции` <= @date_end")
    # выбираем транзакции по категории
    result_transactions = result_data_transactions.loc[result_data_transactions["Категория"] == category]
    # общая сумма расходов - это приход + траты. то есть все расходы/приходы
    grouped = result_transactions.groupby("Категория")["Сумма платежа"].sum().reset_index()
    grouped["Сумма платежа"] = grouped["Сумма платежа"].abs()
    return grouped
