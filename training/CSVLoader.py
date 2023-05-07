import csv
from pathlib import Path
import pandas as pd

import ReopenTradingInfo as rti

class CSVLoader:

    reopen_trading_items:dict

    def __init__(self, code:str) -> None:
        """
        指定した銘柄コードに該当したCSVファイルをロードし、トレード再開の対象を選択させるための情報に変換する
        Args:
            code (str): 銘柄コード
        Returns:
            None
        """
        self.reopen_trading_items = {}

        dir_path = Path('output')
        csv_file_list = list(dir_path.glob('trading_history_' + code + '_*.csv'))

        if len(csv_file_list) == 0:
            return

        for file in csv_file_list:

            # print(file.name)

            # ファイル名は　trading_history_[銘柄コード]_[株データの開始日]_[トレード練習実施開始日時分秒]_[close/open].csv　の前提で解析を始める
            file_name_objects = file.stem.split('_')
            df_csv = pd.read_csv(file, encoding="shift-jis")
            if len(df_csv) == 0:
                continue

            last_row = df_csv.tail(1)   # TODO タイトル行しかないときのチェック
            last_code = last_row['銘柄コード'].item()
            last_trading_date = last_row['取引日付'].item().replace('-', '')
            assets = float(last_row['総資産'])

            if file_name_objects[2] + file_name_objects[3] + file_name_objects[4] not in self.reopen_trading_items:
                reopen_trading_info = rti.ReopenTradingInfo(last_code, file_name_objects[3], file_name_objects[4], last_trading_date)
                reopen_trading_info.add_file(file)
                reopen_trading_info.add_assets(file_name_objects[5], assets)
                self.reopen_trading_items[file_name_objects[2] + file_name_objects[3] + file_name_objects[4]] = reopen_trading_info
            else:
                self.reopen_trading_items[file_name_objects[2] + file_name_objects[3] + file_name_objects[4]].add_file(file)
                self.reopen_trading_items[file_name_objects[2] + file_name_objects[3] + file_name_objects[4]].add_assets(file_name_objects[5], assets)


        
