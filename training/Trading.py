import csv
from datetime import datetime, timedelta
from datetime import date
import os
import pandas as pd
import yfinance as yf

class Trading:

    transactions_list = []

    # 株価格のデータ
    stock_data = None

    # 株銘柄の情報
    stock_info = None
    code:str
    start_date:date
    end_date:date

    transactions_csv = None

    def __init__(self, code:str, start_date:date, end_date:date) -> None:
        """
        トレードを開始する
        Args:
            code (str): トレード対象銘柄のコード
            start_date (date): トレードの開始日付
            end_date (date): トレードの終了日付
        Returns:
            None
        """

        self.code = code
        self.start_date = start_date
        self.end_date = end_date

        # yfinanceの仕様的に指定した終了日付の前日までデータを取得してくるので、1日を追加する
        end_date = end_date + timedelta(days=1)

        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        self.stock_data = yf.download(code+'.T', start=start_str, end=end_str, interval = "1d")

        # 取引履歴を保存するcsvファイルを初期化する
        self.transactions_csv =  'output/transaction_history_' + self.code + '_' + self.start_date.strftime('%Y%m%d') + '_' + self.end_date.strftime('%Y%m%d') + '.csv'
        if not os.path.isfile(self.transactions_csv):
            with open(self.transactions_csv, 'w', newline='') as f:
                header = ['trading_date', 'short_lot', 'long_lot']
                writer = csv.writer(f)
                writer.writerow(header)

    def one_transaction(self, trading_date:date, short_lot:int, long_lot:int):
        """
        1回の取引を行う
        Args:
            trading_date (date): 取引の日付
            short_lot (int): 該当日に持っている空売りのロット数
            long_lot (int): 該当日に持っている買いのロット数
        Returns:
            None
        """
        transaction = [trading_date.strftime('%Y/%m/%d'), str(short_lot), str(long_lot)]
        self.transactions_list.append(transaction)

    def output_transaction_list(self):
        """
        メモリに溜まっている取引のデータをcsvファイルに書き出す
        Args:
            None
        Returns:
            None
        """

        if len(self.transactions_list) == 0:
            return

        with open(self.transactions_csv, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(self.transactions_list)
        # f.close()

        self.transactions_list = []
        return