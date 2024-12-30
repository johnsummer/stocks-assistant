import pandas as pd
import math
from pathlib import Path

def aggregate_csv(csv_path: Path, output_to_file: bool, line_number: int = -1) -> str:
    """
    指定されたトレード履歴のCSVファイルに対して所定の規則で集計する。
    Args:
        csv_path (Path): 集計対象のCSVファイル
        output_to_file (bool): 集計結果をCSVファイルに出力するか。Trueの場合は出力する。
        line_number (int): 戻り値の文字列に含まれるサマリーの件数。ファイル出力には影響しない。マイナスの整数を指定した場合(デフォルトでもある)は全件表示になる。
    Returns:
        画面表示用の文字列（エラーメッセージの場合がある）
    """
    
    if csv_path is None:
        return '対象ファイルが設定されていません。'

    # csvファイルを読み込む
    df = pd.read_csv(csv_path, encoding="shift-jis")

    # 銘柄コードと取引日付と買いロット数と売りロット数と総資産の列だけを抽出する
    df = df[["銘柄コード", "取引日付", "ロットサイズ", "売りロット数", "買いロット数", "総資産"]]
    
    # 取引日付をdatetime型に変換する
    df["取引日付"] = pd.to_datetime(df["取引日付"])

    # 銘柄コードとロットサイズが変わるか、取引日付が前に戻るかどうかを判定する列を追加する
    df["グループ変更"] = (df["銘柄コード"].shift(1) != df["銘柄コード"]) | \
                        (df["ロットサイズ"].shift(1) != df["ロットサイズ"]) | \
                        (df["取引日付"].shift(1) > df["取引日付"])

    # グループ変更があったときにグループ番号を増やす列を追加する
    df["グループ番号"] = df["グループ変更"].cumsum()
    
    # グループ番号ごとに最初と最後の取引日付と買いロット数と売りロット数と総資産を集約する
    df_agg = df.groupby("グループ番号").agg({
        "銘柄コード": "first", 
        "取引日付": ["first", "last"], 
        "ロットサイズ": "first",
        "買いロット数": list, 
        "売りロット数": list, 
        "総資産": ["first", "last"]
    })

    # 列名を整理する
    df_agg.columns = ["銘柄コード", "開始日", "終了日", "ロットサイズ", "買いロット数リスト", "売りロット数リスト", "最初の総資産", "最後の総資産"]
    df_agg = df_agg.reset_index(drop=True)

    # 行ごとに買いロット数と売りロット数との合計を計算する
    df["合計ロット数"] = df["買いロット数"] + df["売りロット数"]

    # グループ番号ごとに合計ロット数の最大値を集約する
    df_max = df.groupby("グループ番号").agg({"合計ロット数": "max"})
    df_max.columns = ["合計最大ロット数"]
    df_max = df_max.reset_index(drop=True)
    df_agg = pd.concat([df_agg, df_max], axis=1)

    # 資産増額を計算する
    df_agg["資産増額"] = df_agg["最後の総資産"] - df_agg["最初の総資産"]
    df_agg["資産増額"] = df_agg["資産増額"].map(lambda x: f"¥{int(x):,}" if x >= 0 else f"-¥{abs(int(x)):,}")
    df_agg = df_agg.drop(["買いロット数リスト", "売りロット数リスト", "最初の総資産", "最後の総資産"], axis=1)

    # CSVファイルに出力
    if output_to_file:
        df_agg["資産増額"] = df_agg["資産増額"].str.replace("¥", "")
        df_agg.to_csv(str(csv_path).replace('_history_', '_summary_'), index=False, encoding="shift-jis")

    dataframe_for_show = df_agg

    # 全件表示するかを判断する
    if line_number >= 0:
        dataframe_for_show = dataframe_for_show.tail(line_number)

    return dataframe_for_show.to_string()
