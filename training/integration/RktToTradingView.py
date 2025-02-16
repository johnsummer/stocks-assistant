import os
import re
import pandas as pd
from collections import defaultdict
from pandas.tseries.offsets import BDay

def _get_target_files(base_folder, start_date, end_date):
    """
    指定された期間に該当するファイルを `input` フォルダから取得する。
    ファイル名は `trading_history_rkt_yyyymm_yyyymm.csv` の形式。
    """
    input_folder = os.path.join(base_folder, "input")
    files = os.listdir(input_folder)
    target_files = []
    
    # 文字列の日付を `Timestamp` に変換
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    for file in files:
        # ファイル名のフォーマットを正規表現でチェック
        match = re.match(r"trading_history_rkt_(\d{6})_(\d{6})\.csv", file)
        if match:
            file_start = pd.to_datetime(match.group(1), format="%Y%m")
            file_end = pd.to_datetime(match.group(2), format="%Y%m")
            # 指定した期間にかかるファイルを選択
            if file_start <= end_date and file_end >= start_date:
                target_files.append(os.path.join(input_folder, file))
    
    return sorted(target_files)

def process_trade_history(target_code, start_date, end_date):
    """
    指定された銘柄コード・期間に対して、対象のファイルから建玉履歴を集計。
    
    Args:
        target_code (int): フィルタリング対象の銘柄コード。
        start_date (str): データを取得する開始日 (YYYYMMDD 形式)。
        end_date (str): データを取得する終了日 (YYYYMMDD 形式)。
    
    Returns:
        str: 日付ごとの建玉履歴を表す文字列。
    """
    if target_code is None:
        raise ValueError("target_codeは必須です。")
    
    # 実行スクリプトの場所からベースフォルダを推定
    base_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    # 日付フォーマットを変換
    start_date = pd.to_datetime(start_date, format="%Y%m%d").strftime("%Y-%m-%d")
    end_date = pd.to_datetime(end_date, format="%Y%m%d").strftime("%Y-%m-%d")
    
    # 対象のファイルリストを取得
    file_paths = _get_target_files(base_folder, start_date, end_date)
    
    if not file_paths:
        return "指定された期間のデータが見つかりませんでした。"
    
    position = defaultdict(lambda: {"売建": 0, "買建": 0})
    
    for file_path in file_paths:
        # CSVファイルをUTF-8エンコーディングで読み込む
        df = pd.read_csv(file_path, encoding="utf-8")
        df["発注/受注日時"] = pd.to_datetime(df["発注/受注日時"])
        
        # 0:00～9:00 の注文は前営業日、土日の注文も前営業日に変更
        df["日付"] = df["発注/受注日時"].apply(
            lambda x: (x - BDay(1)).strftime("%Y-%m-%d") if x.hour < 9 or x.weekday() >= 5 else x.strftime("%Y-%m-%d")
        )
        
        # 指定された銘柄コードでフィルタリング
        df = df[df["コード"] == target_code]
        
        # 指定された期間でフィルタリング
        df = df[(df["日付"] >= start_date) & (df["日付"] <= end_date)]
        
        # 日ごとの建玉集計
        for _, row in df.iterrows():
            date = row["日付"]
            qty = int(row["約定数量(株/口)"])
            if row["売買"] == "売建":
                position[date]["売建"] += qty
            elif row["売買"] == "買建":
                position[date]["買建"] += qty
            elif row["売買"] == "買埋":
                position[date]["売建"] -= qty
            elif row["売買"] == "売埋":
                position[date]["買建"] -= qty
    
    # 日付順に並べて建玉履歴を作成
    sorted_dates = sorted(position.keys())
    sell_total, buy_total = 0, 0
    result = []
    for date in sorted_dates:
        sell_total += position[date]["売建"]
        buy_total += position[date]["買建"]
        result.append(f"{date}:{sell_total}-{buy_total}")
    
    return ",".join(result)

# 動作確認用のコード
if __name__ == "__main__":
    # ユーザー入力を受け取る
    target_code = int(input("銘柄コードを入力してください: "))
    start_date = input("開始日 (YYYYMMDD) を入力してください: ")
    end_date = input("終了日 (YYYYMMDD) を入力してください: ")
    
    # データ処理を実行し、結果を出力
    output = process_trade_history(target_code, start_date, end_date)
    print(output)
