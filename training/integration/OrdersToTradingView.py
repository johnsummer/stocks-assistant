import pandas as pd

def extract_trading_history(file_name:str, stock_code:str, start_date:str, end_date:str):
    """
    CSVファイルから指定した銘柄コードおよび期間の取引日付と建玉操作の情報を抽出します。

    Args:
        file_name (str): トレード履歴データを含むCSVファイルの名前。
        stock_code (str): 指定する銘柄コード。
        start_date (str): 期間の開始日（YYYYMMDD形式）。
        end_date (str): 期間の終了日（YYYYMMDD形式）。
        
    Returns:
        tuple: 2つの文字列を含むタプル：
            - dates_str (str): 取引日付をカンマで区切った文字列。データがない場合は"データがありません"というメッセージ。
            - lot_nummers_str (str): 売りロット数と買いロット数をハイフンで区切り、さらにカンマで区切った文字列。データがない場合は"データがありません"というメッセージ。
    """
    try:
        # CSVファイルを読み込む（Shift-JISエンコーディングを使用）
        df = pd.read_csv(file_name, encoding='shift-jis')

        # 取引日付をdatetime型に変換
        df['取引日付'] = pd.to_datetime(df['取引日付'])

        # 引数の日付をyyyy-mm-dd形式に変換
        start_date = pd.to_datetime(start_date, format='%Y%m%d')
        end_date = pd.to_datetime(end_date, format='%Y%m%d')

        # 指定した銘柄コードおよび期間のデータをフィルタリング
        filtered_df = df[(df['銘柄コード'] == stock_code) & 
                         (df['取引日付'] >= start_date) & 
                         (df['取引日付'] <= end_date)]

        # データが存在しない場合の処理
        if filtered_df.empty:
            return "該当するデータがありません", "該当するデータがありません"

        # 必要な列（取引日付、売りロット数、買いロット数）を抽出
        dates = filtered_df['取引日付'].dt.strftime('%Y-%m-%d').tolist()
        sell_lots = filtered_df['売りロット数'].tolist()
        buy_lots = filtered_df['買いロット数'].tolist()

        # 日付の文字列を生成
        dates_str = ','.join(dates)

        # ロット数の文字列を生成
        lot_nummers_str = ','.join([f"{sell}-{buy}" for sell, buy in zip(sell_lots, buy_lots)])

        return dates_str, lot_nummers_str
    except Exception as e:
        return str(e), str(e)
