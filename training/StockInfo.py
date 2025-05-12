from datetime import date
from datetime import timedelta

import glob
import os
import re
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

    def __init__(self, code:str, start_date:date, end_date:date, data_type:str):
        """
        株価を含めた銘柄情報を読み込む
        読み込んだデータは、stock_data_df フィールドに格納される。ただし、銘柄コードに対応するデータが存在しない場合は None となる。
        Args:
            code (str): 銘柄コード
            start_date (date): 読み込む対象となる株価データの開始日
            end_date (date): 読み込む対象となる株価データの終了日
            data_type (str): データの取得元（loc:ローカルファイル, yf:yfinance）
        Returns:
            None
        """
        # 正規化した（Yahoo Finance形式にした）コードを株の銘柄コード情報として使う
        self.code = self.__normalize_tse_code(code)

        # data_typeが 'loc' の場合、start_date と end_date は使われない
        self.start_date = start_date
        self.end_date = end_date

        # データの取得元に応じて処理を分岐
        if data_type == 'loc':
            # ローカルファイルから読み込む
            try:
                self.stock_data_df = self.__load_trv_csv(code)
            except FileNotFoundError:
                # TradingViewのCSVファイルが存在しない場合、チャートギャラリーのテキストファイルを読み込む
                print(f"TradingViewのCSVファイルが見つかりません。チャートギャラリーのテキストファイルを読み込みます: {code}")
                try:
                    self.stock_data_df = self.__load_chg_txt(code)
                except FileNotFoundError:
                    print(f"チャートギャラリーのテキストファイルも見つかりません。データは取得できません: {code}")
                    self.stock_data_df = None
        elif data_type == 'yf':
            # yfinanceから取得する
            
            # yfinanceの仕様的に指定した終了日付の前日までデータを取得してくるので、1日を追加する
            end_date = end_date + timedelta(days=1)

            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            self.stock_data_df = yf.download(code, start=start_str, end=end_str, interval = "1d", auto_adjust=False, multi_level_index=False)
        else:
            print(f"不正なデータ種別: {data_type}")
            self.stock_data_df = None

    def __normalize_tse_code(self, code: str) -> str:
        """
        東証上場銘柄に対して証券コードを正規化する。
        - TSE_XXXX → XXXX.T
        - XXXX → XXXX.T
        - XXXX.T → XXXX.T
        - ただし、XXXX は4桁の数字に限る。それ以外は日本株ではないので、変換しないまま返す

        Args:
            code (str): 入力された証券コード

        Returns:
            str: 正規化されたコード（'XXXX.T'）
        """
        match = re.fullmatch(r'(TSE_)?(\d{4})(\.T)?', code)
        if match:
            return f"{match.group(2)}.T"
        return code

    def __load_trv_csv(self, code: str) -> pd.DataFrame:
        """
        指定された銘柄コードに対応するTradingViewのCSVファイルを読み込み、DataFrame を返す。

        Args:
            code (str): 証券コード（"TSE_XXXX", "XXXX.T", "XXXX" 形式のいずれか）

        Returns:
            pd.DataFrame: 整形済みの DataFrame（time をインデックス）
        """
        # 証券コードの統一（4桁 + ".T" に変換）
        if code.startswith("TSE_"):
            code_num = code[4:]
        elif code.endswith(".T"):
            code_num = code[:-2]
        else:
            code_num = code

        if not code_num.isdigit() or len(code_num) != 4:
            raise ValueError(f"不正な銘柄コード形式: {code}")

        # 動的にパスを構築
        base_dir = os.path.join('input', 'data', 'trv')
        path_pattern = os.path.join(base_dir, f'TSE_{code_num}*.csv')

        # 該当ファイルを検索
        file_list = glob.glob(path_pattern)

        if not file_list:
            raise FileNotFoundError(f"指定銘柄コードに該当したTradingViewデータは存在しません: {code}。")

        # ファイルの更新時刻で最新ファイルを選択
        latest_file = max(file_list, key=os.path.getmtime)

        df = None

        # 必要な列名（読み込み時の小文字）
        required_columns = ['time', 'open', 'high', 'low', 'close', 'volume']

        # CSVファイルを読み込み
        df = pd.read_csv(latest_file, usecols=lambda col: col.lower() in required_columns)

        # 'time'列をdatetime型に変換し、インデックスに設定
        df['time'] = pd.to_datetime(df['time'])
        df.set_index('time', inplace=True)

        # 列名の先頭文字を大文字に変換
        df.columns = [col.capitalize() for col in df.columns]

        return df

    def __load_chg_txt(self, code: str) -> pd.DataFrame:
        """
        指定された銘柄コードに対応するチャートギャラリーのテキストファイルを読み込み、DataFrame を返す。

        Args:
            code (str): 証券コード（"TSE_XXXX", "XXXX.T", "XXXX" 形式のいずれか）

        Returns:
            pd.DataFrame: 整形済みの DataFrame（time をインデックス）
        """
        # 証券コードの統一（4桁 + ".T" に変換）
        if code.startswith("TSE_"):
            code_num = code[4:]
        elif code.endswith(".T"):
            code_num = code[:-2]
        else:
            code_num = code

        if not code_num.isdigit() or len(code_num) != 4:
            raise ValueError(f"不正な銘柄コード形式: {code}")

        filename = f"TSE_{code_num}.txt"
        filepath = os.path.join("input", "data", "chg", filename)

        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"指定銘柄コードに該当したチャートギャラリーデータは存在しません: {code}。")

        # ファイル読み込みと整形
        data = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                cols = line.strip().split('\t')
                if len(cols) < 6:
                    continue  # Volumeを含まない行はスキップ
                row = cols[:5] + [cols[-1]]
                data.append(row)

        df = pd.DataFrame(data, columns=['time', 'open', 'high', 'low', 'close', 'Volume'])

        # 日付変換とインデックス設定
        df['time'] = pd.to_datetime(df['time'], format='%y/%m/%d')
        df.set_index('time', inplace=True)

        # 列名を大文字始まりに
        df.columns = [col.capitalize() for col in df.columns]

        return df
