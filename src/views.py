import datetime
import logging
import os
from typing import Any, Dict, Hashable, List

import pandas as pd
import requests

from src.utils import cards_filtered, read_user_settings, start_data_filtered

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


def cards_total_spent(transactions: List[Dict]) -> List[Dict]:
    """
    Принимает список словарей с транзакциями
    выводит По каждой карте:
                            последние 4 цифры карты ("last_digits");
                            общая сумма расходов ("total_spent");
                            кешбэк (1 рубль на каждые 100 рублей) ("cashback").
    списком словарей на выходе
    """
    if not transactions:
        logger.error("cards_total_spent отсутствуют транзакции для вывода. Заверщение функции. На выходе пустой список")
        return []
    logger.info("вызов cards_total_spent")
    df = pd.DataFrame(transactions)
    logger.info("cards_total_spent групировка данных")
    # общая сумма расходов - это приход + траты. то есть все расходы/приходы по карте
    grouped = df.groupby("Номер карты")["Сумма операции"].sum().reset_index()
    grouped["Сумма операции"] = grouped["Сумма операции"].abs()
    logger.info("cards_total_spent переименование колонок под стайт")
    grouped.rename(columns={"Номер карты": "last_digits"}, inplace=True)
    grouped.rename(columns={"Сумма операции": "total_spent"}, inplace=True)
    df_result = grouped.to_dict("records")
    logger.info("cards_total_spent оставлеем последние 4 цифры карты, округляем резутьтат тразакций, считаем cashback")
    for item in df_result:
        item["last_digits"] = cards_filtered(item["last_digits"])
        item["total_spent"] = round(item["total_spent"], 2)
        item["cashback"] = round(item["total_spent"] / 100, 2)
    logger.info("cards_total_spent завершение работы функции")
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
    # убираем транзакции, которые  не прошли
    df_not_failed = df[df["Статус"] != "FAILED"]
    # берем топ 5 малых сумм (Топ-5 транзакций по сумме платежа, т.е. расходы. Расходы со знаком "-")
    top_5 = df_not_failed.nsmallest(5, "Сумма операции")
    logger.info("top_5_transactions переименование колонок под сайт")
    top_5_renamed = top_5.rename(
        columns={
            "Дата операции": "date",
            "Сумма операции": "amount",
            "Категория": "category",
            "Описание": "description",
        }
    )
    # преобразуем расходы в положительные числа
    top_5_renamed["amount"] = top_5_renamed["amount"].abs()
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


def exchange_rates() -> List[Dict]:
    """
    функция забирает данные с 'https://www.cbr-xml-daily.ru/daily_json.js' по курсу валют и на выход подает
    список только тех курс валют, которые указаны в user_settings.json по ключу "user_currencies"в формате:
    [{'currency': 'USD', 'rate': 74.62}, {'currency': 'EUR', 'rate': 85.48}]
    Если валют не найдено или они отсутствуют в файле настроек, то выводит пустой список
    """
    # забираем из настроек список валют
    logger.info("вызов exchange_rates")
    currencies = read_user_settings("user_currencies")
    # забираем данные о валютах со стороннего ресурса
    if not currencies:
        logger.error(
            "exchange_rates в файле натроек нет данных о курсах валют. Выводим пустой список."
            " Завершение работы функции."
        )
        return []
    logger.info("exchange_rates чтение данных по валютам с 'https://www.cbr-xml-daily.ru/daily_json.js'")
    try:
        r = requests.get("https://www.cbr-xml-daily.ru/daily_json.js")
        currencies_dict = r.json()
        logger.info("exchange_rates успешное чтение данных по валютам")
    except requests.exceptions.RequestException as e:
        logger.error(
            f"exchange_rates ошибка чтения данных ERROR: {e}. Выводим пустой список. " f"Завершение работы функции"
        )
        return []

    result_currencies = []
    # для каждой валюты из списка в настройках
    for target_currency in currencies:
        result_currency = {}
        if currencies_dict.get("Valute").get(target_currency):
            logger.info(f"exchange_rates валюта {target_currency} найдена")
            result_currency["currency"] = target_currency
            result_currency["rate"] = round(currencies_dict.get("Valute").get(target_currency).get("Value"), 2)
            result_currencies.append(result_currency)
    if not result_currencies:
        logger.error("exchange_rates валют указаных в файле с настройками не найдено, выводим пустой список")
    logger.info("exchange_rates завершение работы функции")
    return result_currencies


def share_price():
    """
    функция забирает данные с MOEX ISS по курсу акций и на выход подает
    список только курс акций, которые указаны в user_settings.json по ключу "user_stocks" в формате:
    [{"stock": "AAPL", "price": 150.12}, {"stock": "AMZN", "price": 3173.18}]
    Если акций не найдено или они отсутствуют в файле настроек, то выводит пустой список
    ?iss.only=marketdata&marketdata.columns=LAST позволяет запросить только последнюю цену акции
    """
    logger.info("вызов share_price")
    tickers = read_user_settings("user_stocks")
    if not tickers:
        logger.error(
            "share_price в файле натроек нет данных о курсах валют. Выводим пустой список."
            " Завершение работы функции."
        )
        return []
    result_stocks = []
    for ticker in tickers:
        url = (
            f"https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/{ticker}.json"
            f"?iss.only=marketdata&marketdata.columns=LAST"
        )
        result_stock = {}
        try:
            logger.info(f"share_price читаем данные с iss.moex.com для акции с тикером '{ticker}' по url: {url}")
            r = requests.get(url)
            stock_dict = r.json()
            if stock_dict.get("marketdata").get("data") and stock_dict.get("marketdata").get("data")[0][0]:
                logger.info("share_price данные успешно найдены")
                result_stock["stock"] = ticker
                result_stock["price"] = round(stock_dict["marketdata"]["data"][0][0], 2)
                result_stocks.append(result_stock)
                logger.info(f"share_price успешная чтение/запись для акции с тикером '{ticker}'")
            else:
                logger.error(f"share_price данные по акции с тикером '{ticker} не найдены")
        except requests.exceptions.RequestException as e:
            logger.error(
                f"share_price ошибка чтения данных ERROR: {e}. Выводим пустой список. " f"Завершение работы функции"
            )
        except Exception as e:
            logger.error(
                f"share_price Непредвиденная ошибка ERROR: {e}. Выводим пустой список. " f"Завершение работы функции"
            )
            return []
    if not result_stocks:
        logger.error("share_price акций указаных в файле с настройками не найдено, выводим пустой список")
    logger.info("share_price завершение работы функции")
    return result_stocks
