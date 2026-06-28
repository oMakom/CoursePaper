import datetime
import json
import logging
import os
from functools import wraps
from typing import Optional

import pandas as pd
from dateutil.relativedelta import relativedelta

from src.utils import str_to_datetime

# Определяем путь к проекту Src
root_path = os.path.dirname(os.path.abspath(__file__))
# Определяем путь к файлу logs/views.log
logs_path = os.path.abspath(os.path.join(root_path, "..", "logs/reports.log"))
logger = logging.getLogger("reports")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(logs_path, mode="w", encoding="utf-8")
file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)


def save_report(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        """
        записывает данные отчета в файл с названием по умолчанию
        """
        # Определяем путь к проекту Src
        logger.info(f"вызов декоратора save_report для {func.__name__}")
        root_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.abspath(os.path.join(root_path, "..", "spending_category_report.json"))

        result = func(*args, **kwargs)
        try:
            data = json.loads(result.to_json(orient="records", force_ascii=False))
        except Exception as e:
            logger.error(f"декоратор save_report для {func.__name__} ошибка чтения данных ERROR{e}.")
            data = []
        if not data:
            logger.error(f"декоратор save_report для {func.__name__} нет данных по категории.")
            data = json.loads('{"Категория": "нет данных по категории в выбранном диапазоне"}')
        logger.info(f"декоратор save_report для {func.__name__} запись в файл {file_path} результата")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info(f"декоратор save_report для {func.__name__} завершение работы")
        return result

    return wrapper


@save_report
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    """
    Функция возвращает траты по заданной категории за последние три месяца (от переданной даты)
    Если дата не передана, то берется текущая дата.
    """
    logger.info("вызов spending_by_category")
    # приводим стролюец 'Дата операции' к datetime
    transactions["Дата операции"] = pd.to_datetime(transactions["Дата операции"], format="%d.%m.%Y %H:%M:%S")
    if date is not None:
        # Пробуем преобразовать время, иначе указываем текущее
        logger.info(f"spending_by_category перобразуем дату '{date}' в datetime")
        if str_to_datetime(date):
            date_end = str_to_datetime(date)
        else:
            date_end = datetime.datetime.now()
            logger.error(f"spending_by_category ошибка преобразования, используем текуюю дату '{date_end}'")
    else:
        date_end = datetime.datetime.now()
        logger.info(f"spending_by_category дата не указана, используем текуюю дату '{date_end}'")
    # Узнаем дату за 3 месяца до
    date_start = date_end - relativedelta(months=3)
    # все операции за указанный период
    logger.info(f"spending_by_category выбираем транзакции за период '{date_start} - {date_end}'")
    result_data_transactions = transactions.query("@date_start <= `Дата операции` <= @date_end")
    # выбираем транзакции по категории
    logger.info(f"spending_by_category оставляем транзакции по категории {category}")
    result_transactions = result_data_transactions.loc[result_data_transactions["Категория"] == category]
    # общая сумма расходов - это приход + траты. то есть все расходы/приходы
    logger.info("spending_by_category суммируем траты")
    grouped = result_transactions.groupby("Категория")["Сумма платежа"].sum().reset_index()
    grouped["Сумма платежа"] = grouped["Сумма платежа"].abs()
    logger.info("spending_by_category завершение работы")
    return grouped
