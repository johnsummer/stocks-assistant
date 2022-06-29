import csv
from datetime import datetime, timedelta
from datetime import date
import pandas as pd
import yfinance as yf

class Trading:

    transactions_list = []

    # 株価格のデータ
    stock_data = None

    # 株銘柄の情報
    stock_info = None

    def __init__(self, code:str, start_date:date, end_date:date) -> None:

        # yfinanceの仕様的に指定した終了日付の前日までデータを取得してくるので、1日を追加する
        end_date = end_date + timedelta(days=1)

        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        self.stock_data = yf.download(code+'.T', start=start_str, end=end_str, interval = "1d")

    def one_transaction(self, trading_date:date, short_lots:int, long_lots:int):
        transaction = [trading_date.strftime('%Y/%m/%d'), str(short_lots), str(long_lots)]
        self.transactions_list.append(transaction)