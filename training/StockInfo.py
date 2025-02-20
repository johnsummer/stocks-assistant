from datetime import date
from datetime import timedelta

import pandas as pd
import yfinance as yf


class StockInfo:

    # 株価格のデータ
    stock_data_df:pd.DataFrame = None

    # 株銘柄の情報
    # stock_info = None   # 現時点は使わない
    code:str
    start_date:date
    end_date:date

    def __init__(self, code:str, start_date:date, end_date:date):
        """
        株価を含めた銘柄情報を読み込む
        Args:
            code (str): 銘柄コード
            start_date (date): 読み込む対象となる株価データの開始日
            end_date (date): 読み込む対象となる株価データの終了日
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
        self.stock_data_df = yf.download(code, start=start_str, end=end_str, interval = "1d", auto_adjust=False, multi_level_index=False)