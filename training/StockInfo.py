from datetime import date
from datetime import timedelta

import glob
import os
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
        yfinanceから株価を含めた銘柄情報を読み込む
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

    def __init__(self, code:str, data_type:str):
        """
        指定された証券コードおよびデータ種別に対応する最新のCSVファイルを、更新時刻ベースで読み込む
        Args:
            code (str): 銘柄コード
            data_type: データファイルの取得元（trv:TradingView, それ以外は未実装）
        Returns:
            None
        """

        # 動的にパスを構築
        base_dir = os.path.join('input', 'data', data_type)
        path_pattern = os.path.join(base_dir, f'{code}*.csv')

        # 該当ファイルを検索
        file_list = glob.glob(path_pattern)

        if not file_list:
            raise FileNotFoundError(f"No CSV files found for code: {code} in data_type: {data_type}")

        # ファイルの更新時刻で最新ファイルを選択
        latest_file = max(file_list, key=os.path.getmtime)

        df = None

        # TradingViewの前提でデータを処理する
        if data_type == 'trv':
            # 必要な列名（読み込み時の小文字）
            required_columns = ['time', 'open', 'high', 'low', 'close', 'volume']

            # CSVファイルを読み込み
            df = pd.read_csv(latest_file, usecols=lambda col: col.lower() in required_columns)

            # 'time'列をdatetime型に変換し、インデックスに設定
            df['time'] = pd.to_datetime(df['time'])
            df.set_index('time', inplace=True)

            # 列名の先頭文字を大文字に変換
            df.columns = [col.capitalize() for col in df.columns]

        self.code = code
        self.stock_data_df = df
