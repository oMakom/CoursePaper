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
    logger.info(f"вызов read_excel_file с путем до файла: {file_path}")
    try:
        df = pd.read_excel(file_path)
        transactions = df.to_dict(orient="records")
        logger.info("read_excel_file завершение функции")
        return transactions
    except Exception as e:
        transactions = []
        logger.error(f"read_excel_file завершение функции с ошибкой({e}). На выходе пустой список")
        return transactions


def greeting_by_time() -> str:
    """
    Фунция выводит приветствие в зависимости от текущего времени системы в формате строки
    Например: "Доброе утро" с 06:00 по 11:59
    """
    greetings_time = [
        {"Доброе утро": ["06:00", "11:59"]},
        {"Добрый день": ["12:00", "17:59"]},
        {"Добрый вечер": ["18:00", "22:59"]},
        {"Доброй ночи": ["23:00", "05:59"]},
    ]
    result_greeting = ""
    current_time = datetime.datetime.now().time()
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
    return result_greeting
