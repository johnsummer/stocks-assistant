import pandas as pd

def extract_trading_history(file_name: str, stock_code: str, start_date: str, end_date: str) -> str:
    """
    CSVファイルから指定した銘柄コードおよび期間の取引日付、売りロット数、買いロット数を抽出し、
    取引日付:売りロット数-買いロット数という形式の文字列を生成します。

    Args:
        file_name (str): トレード履歴データを含むCSVファイルの名前。
        stock_code (str): 指定する銘柄コード。
        start_date (str): 期間の開始日（YYYYMMDD形式）。
        end_date (str): 期間の終了日（YYYYMMDD形式）。
        
    Returns:
        str: 取引日付:売りロット数-買いロット数形式の文字列。データがない場合は"該当するデータがありません"というメッセージ。
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
            return "該当するデータがありません"

        # 必要な列（取引日付、売りロット数、買いロット数）を抽出
        filtered_df = filtered_df[['取引日付', '売りロット数', '買いロット数']]

        # 取引日付、売りロット数、買いロット数を順番に抽出し、文字列を生成
        result_str = ','.join([f"{row['取引日付'].strftime('%Y-%m-%d')}:{row['売りロット数']}-{row['買いロット数']}" 
                               for index, row in filtered_df.iterrows()])

        return result_str
    except Exception as e:
        return str(e)
