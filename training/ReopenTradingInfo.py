from pathlib import Path

class ReopenTradingInfo:

    last_code:str                   # 最後の取引に該当した銘柄コード
    start_date:str
    training_start_datetime:str
    last_trading_date:str

    file_list:dict
    assets_dict:dict

    def __init__(self, last_code:str, start_date:str, training_start_datetime:str, last_trading_date:str) -> None:
        """
        再開候補となるトレードの情報
        Args:
            last_code (str): 最後の取引に該当した銘柄コード
            start_date (str): 読み取った株データの開始日（≒練習トレードの開始日）
            training_start_datetime (str): 練習開始の日時
            last_trading_date (str): トレード練習の最後の取引日（≒練習トレードの中断日）
        Returns:
            None
        """
        self.last_code = last_code
        self.start_date = start_date
        self.training_start_datetime = training_start_datetime
        self.last_trading_date = last_trading_date
        self.file_list = {}
        self.assets_dict = {}

    def add_file(self, key:str, csv_file:Path):
        """
        本トレード再開情報に紐付けたいCSVファイルを追加する
        Args:
            csv_file (pathlib.Path): 本トレード再開情報と紐付けたいCSVファイル
        Returns:
            None
        """
        self.file_list[key] = csv_file

    def add_assets(self, key:str, assets:float):
        self.assets_dict[key] = assets
