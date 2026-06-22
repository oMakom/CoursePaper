import datetime
import json
import logging
import os
from typing import Any, Dict, Hashable, List

import pandas as pd
import requests

# Определяем путь к проекту Src
root_path = os.path.dirname(os.path.abspath(__file__))
# Определяем путь к файлу logs/views.log
logs_path = os.path.abspath(os.path.join(root_path, "..", "logs/views.log"))
logger = logging.getLogger("views")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(logs_path, mode="w", encoding="utf-8")
file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)


def read_datafile(filename: str = "operations.xlsx") -> List[Dict[Hashable, Any]]:
    """
    Функция читает exls файл. Принимает на фход путь к файлу и выводит список словарей (при ошибках пустой список)
    Путь по умолчанию "operations.xlsx" (все файлы храняться в папке data)
    """
    file_path = os.path.abspath((os.path.join(root_path, "..", "data", filename)))
    logger.info(f"вызов read_datafile с путем до файла: {file_path}")
    try:
        df = pd.read_excel(file_path)
        transactions = df.to_dict(orient="records")
        logger.info("read_datafile завершение функции")
        return transactions
    except Exception as e:
        transactions = []
        logger.error(f"read_datafile завершение функции с ошибкой({e}). На выходе пустой список")
        return transactions


def greeting_by_time() -> str:
    """
    Фунция выводит приветствие в зависимости от текущего времени системы в формате строки
    Например: "Доброе утро" с 06:00 по 11:59
    """
    logger.info("вызов greeting_by_time")
    greetings_time = [
        {"Доброе утро": ["06:00", "11:59"]},
        {"Добрый день": ["12:00", "17:59"]},
        {"Добрый вечер": ["18:00", "22:59"]},
        {"Доброй ночи": ["23:00", "05:59"]},
    ]
    result_greeting = ""
    current_time = datetime.datetime.now().time()
    logger.info(f"greeting_by_time получение текущего времени: {current_time}")
    for greeting in greetings_time:
        for key, value in greeting.items():
            # по каждому диапазону сравниваем текущее время
            after_time = datetime.datetime.strptime(value[0], "%H:%M").time()
            before_time = datetime.datetime.strptime(value[1], "%H:%M").time()
            if (after_time <= current_time >= before_time) or (
                (current_time >= after_time) or (current_time <= before_time) and key == "Доброй ночи"
            ):
                result_greeting = key
                break
    logger.info(f"greeting_by_time завершение работы функции с параметром: {result_greeting}")
    return result_greeting


def cards_filtered(num_card: str) -> str:
    """
    Принимает на вход строку с номером карты, возваращает 4 последние цифры, либо пустую строку при ошибке
    """
    logger.info(f"вызов cards_filtered с параметром: {num_card}")
    if not isinstance(num_card, str):
        logger.error("cards_filtered Ошибка TypeError: 'Номер карты должен быть строкой'")
        raise TypeError("Номер карты должен быть строкой")
    if len(num_card) > 4:
        logger.info("cards_filtered обработка номера карты длинной больше 4х символов и завершение работы функции")
        return num_card[-4:]
    if len(num_card) == 4:
        logger.info("cards_filtered обработка номера карты длинной райной 4м символам и завершение работы функции")
        return num_card
    logger.info(
        "cards_filtered обработка номера карты длинной меньше 4х символов( на выводе пустая строка) "
        "и завершение работы функции"
    )
    return ""


def start_data_filtered(start_date: str, start_range: str = "M") -> datetime.datetime:
    """
    Принимает на вход строку с датой формата YYYY-MM-DD HH:MM:SS и второй необязательный параметр — диапазон данных.
    При ошибке принимает текущую дату и время
    По умолчанию диапазон равен одному месяцу (с начала месяца, на который выпадает дата, по саму дату).
    Возможные значения второго необязательного параметра:
    W — неделя, на которую приходится дата;
    M — месяц, на который приходится дата;
    Y — год, на который приходится дата;
    ALL — все данные до указанной даты.
    на выходе дата начала сбора данных, в зависимости от параметров, в формате datetime и конечная дата
    сбора данных в формате datetime
    """
    logger.info(f"вызов read_datafile с параметрами: start_date: '{start_date}', start_range: '{start_range}'")
    # если некорректный формат даты -> присваиваем сегодняшнюю дату
    try:
        date_filtered = datetime.datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        logger.info(f"read_datafile преобразование '{start_date}' в datetime по формату YYYY-MM-DD HH:MM:SS")
    except Exception as e:
        logger.error(
            f"read_datafile ошибка преобразования '{start_date}' в datetime по формату YYYY-MM-DD HH:MM:SS. "
            f"ERROR: {e}.   Сбор данных будет указан относительно текущей даты"
        )
        date_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_filtered = datetime.datetime.strptime(date_now, "%Y-%m-%d %H:%M:%S")
    # если указано будущее -> присваиваем сегодняшнюю дату
    if date_filtered > datetime.datetime.now():
        logger.error(f"read_datafile ошибка: Указано будущее({date_filtered}). Присваимваем текущую дату")
        date_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_filtered = datetime.datetime.strptime(date_now, "%Y-%m-%d %H:%M:%S")
    if start_range.lower() == "w":
        start_date_final = date_filtered - datetime.timedelta(days=date_filtered.weekday())
        logger.info("read_datafile фильтрация даты по текущей неделе")
    if start_range.lower() == "m":
        start_date_final = date_filtered.replace(day=1)
        logger.info("read_datafile фильтрация даты по текущему месяцу")
    if start_range.lower() == "y":
        start_date_final = date_filtered.replace(day=1, month=1)
        logger.info("read_datafile фильтрация даты по текущему году")
    if start_range.lower() == "all":
        logger.info("read_datafile фильтрация всех данных до указанной даты")
        start_date_final = datetime.datetime.strptime("1000-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
    logger.info("read_datafile завершение работы функции")
    end_date_final = date_filtered
    return start_date_final, end_date_final


def cards_total_spent(transactions: List[Dict]) -> List[Dict]:
    """
    Принимает список словарей с транзакциями
    выводит По каждой карте:
                            последние 4 цифры карты ("last_digits");
                            общая сумма расходов ("total_spent");
                            кешбэк (1 рубль на каждые 100 рублей) ("cashback").
    списком словарей на выходе
    """
    df = pd.DataFrame(transactions)
    grouped = df.groupby("Номер карты")["Сумма операции с округлением"].sum().reset_index()
    grouped.rename(columns={"Номер карты": "last_digits"}, inplace=True)
    grouped.rename(columns={"Сумма операции с округлением": "total_spent"}, inplace=True)
    df_result = grouped.to_dict("records")
    # меняем номер карты на 4 цифры
    for item in df_result:
        item["last_digits"] = cards_filtered(item["last_digits"])
        item["total_spent"] = round(item["total_spent"], 2)
        item["cashback"] = round(item["total_spent"] / 100, 2)
    return df_result


def top_5_transactions(transactions: List[Dict]) -> List[Dict]:
    """
    Принимает список словарей с транзакциями
    выводит топ 5 по транзакциям:
    "date": "21.12.2021",
    "amount": 1198.23,
    "category": "Переводы",
    "description": "Перевод Кредитная карта. ТП 10.2 RUR"
    выводит списком словарей на выходе
    """
    logger.info("вызов top_5_transactions")
    df = pd.DataFrame(transactions)
    logger.info("top_5_transactions получение данных о ТОП 5")
    top_5 = df.nlargest(5, "Сумма операции с округлением")
    logger.info("top_5_transactions переименование колонок под сайт")
    top_5_renamed = top_5.rename(
        columns={
            "Дата операции": "date",
            "Сумма операции с округлением": "amount",
            "Категория": "category",
            "Описание": "description",
        }
    )
    logger.info("top_5_transactions преобразование в словарь")
    df_top_5 = top_5_renamed[["date", "amount", "category", "description"]].to_dict("records")
    logger.info("top_5_transactions завершение функции")
    return df_top_5


def filter_transactions_by_date(transactions: List[Dict], start_date: str, start_range: str = "M") -> List[Dict]:
    """
    Фильтрует транзаций по дате и времени с использованием функции start_data_filtered()
    На входе список словарей, дата в формате YYYY-MM-DD HH:MM:SS, и необязательный параметр
    Возможные значения второго необязательного параметра:
    W — неделя, на которую приходится дата;
    M — месяц, на который приходится дата;
    Y — год, на который приходится дата;
    ALL — все данные до указанной даты.
    на выходе отсортированный список словарей по временному интервалу
    """
    start_date_transaction, end_date_transaction = start_data_filtered(start_date, start_range)
    result_transactions = []
    for transaction in transactions:
        if transaction.get("Дата операции"):
            if (
                start_date_transaction
                <= datetime.datetime.strptime(transaction["Дата операции"], "%d.%m.%Y %H:%M:%S")
                <= end_date_transaction
            ):
                result_transactions.append(transaction)
    return result_transactions
