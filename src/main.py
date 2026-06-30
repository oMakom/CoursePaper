import json

from src.utils import read_datafile
from src.views import (cards_total_spent, exchange_rates_for_settings, filter_transactions_by_date, greeting_by_time,
                       share_price, top_5_transactions)


def main_views_function(date_time: str, start_range: str = "M") -> str:
    """
    функция собирает JSON-ответ на основе данных анализа
    date_time: дата и время в формате YYYY-MM-DD HH:MM:SS
    start_range: необязательный параметр — диапазон данных
    """
    file_data = read_datafile()
    result_answer = {}
    result_answer["greeting"] = greeting_by_time()
    result_answer["cards"] = cards_total_spent(filter_transactions_by_date(file_data, date_time, start_range))
    result_answer["top_transactions"] = top_5_transactions(file_data)
    result_answer["currency_rates"] = exchange_rates_for_settings()
    result_answer["stock_prices"] = share_price()

    return json.dumps(result_answer, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    date = "2018-12-03 00:00:00"
    date_range = "y"
    print(main_views_function(date, date_range))
