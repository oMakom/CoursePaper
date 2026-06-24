import pandas as pd
import datetime
import json
import logging
import os
from typing import Any, Dict, Hashable, List

# Определяем путь к проекту Src
root_path = os.path.dirname(os.path.abspath(__file__))
# Определяем путь к файлу logs/views.log
logs_path = os.path.abspath(os.path.join(root_path, "..", "logs/utils.log"))
logger = logging.getLogger("utils")
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


def read_user_settings(key: str) -> list:
    """
    Функция для считывания данных из файла настроки по ключу
    принимает на вход ключ в виде строки
    на выходе список данных по ключу или пустой список при ошибке или отсутствии данных
    "user_currencies" -> Список валют
    "user_stocks" -> Список акций
    """
    logger.info(f"вызов read_user_settings с ключем настроек : '{key}'")
    file_path = os.path.abspath((os.path.join(root_path, "..", "user_settings.json")))
    result_list = []
    try:
        with open(file_path, "r") as f:
            logger.info(f"read_user_settings чтение данных и файла настроек '{file_path}' по ключу '{key}'")
            data = json.load(f)
            if data.get(key):
                result_list = data[key]
                logger.info("read_user_settings учпешное чтение данных")
            else:
                logger.error(f"read_user_settings ключа настроек '{key}' не существует")
    except FileNotFoundError:
        logger.error(f"read_user_settings файл с настройками по пути : '{file_path}' не найден")
    except Exception as e:
        logger.error(f"read_user_settings непредвиденная ошибка : '{e}'")
    logger.info("read_user_settings завершение работы функции")
    return result_list


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