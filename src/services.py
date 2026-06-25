import json

from src.utils import read_datafile


def easy_search(text_search: str) -> str:
    transactions = read_datafile()
    result_transactions = []
    for transaction in transactions:
        if ((text_search.lower() in str(transaction["Категория"]).lower())
                or (text_search.lower() in str(transaction["Описание"]).lower())):
            result_transactions.append(transaction)
    json_transactions = json.dumps(result_transactions, ensure_ascii=False, indent=4)
    return json_transactions
