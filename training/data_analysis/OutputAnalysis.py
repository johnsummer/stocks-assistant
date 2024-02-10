# pandasをインポートする
import pandas as pd
# mathをインポートする
import math

def aggregate_csv(csv_path:str, output_to_file:bool):
    """
        指定されたトレード履歴のCSVファイルに対して所定の規則で集計する。
        Args:
            csv_path (str): 集計対象のCSVファイル
            output_to_file (bool): 集計結果をCSVファイルに出力するか。Trueの場合は出力する。
        Returns:
            None
        """
    # csvファイルを読み込む
    df = pd.read_csv(csv_path, encoding="shift-jis")
    # 銘柄コードと取引日付と保有株数と空売り中の株数と総資産の列だけを抽出する
    df = df[["銘柄コード", "取引日付", "保有株数", "空売り中の株数", "総資産"]]
    # 銘柄コードが変わるかどうかを判定する列を追加する
    df["銘柄コード変更"] = df["銘柄コード"].shift(1) != df["銘柄コード"]
    # 銘柄コードが変わるときにグループ番号を増やす列を追加する
    df["グループ番号"] = df["銘柄コード変更"].cumsum()
    # グループ番号ごとに最初と最後の取引日付と保有株数と空売り中の株数と総資産を集約する
    df_agg = df.groupby("グループ番号").agg({"銘柄コード": "first", "取引日付": ["first", "last"], "保有株数": list, "空売り中の株数": list, "総資産": ["first", "last"]})
    # 列名を整理する
    df_agg.columns = ["銘柄コード", "開始日", "終了日", "保有株数リスト", "空売り中の株数リスト", "最初の総資産", "最後の総資産"]
    # インデックスをリセットする
    df_agg = df_agg.reset_index(drop=True)
    # ロットサイズを計算する関数を定義する
    def calc_lot_size(x):
        # 保有株数と空売り中の株数を結合する
        nums = x["保有株数リスト"] + x["空売り中の株数リスト"]
        # 0を除く
        nums = [n for n in nums if n != 0]
        # 最大公約数を求める
        gcd = math.gcd(*nums)
        # 最大公約数を返す
        return gcd
    # ロットサイズを計算して列に追加する
    df_agg["ロットサイズ"] = df_agg.apply(calc_lot_size, axis=1)
    # 行ごとに保有株数と空売り中の株数との合計を計算する
    df["合計株数"] = df["保有株数"] + df["空売り中の株数"]
    # グループ番号ごとに合計株数の最大値を集約する
    df_max = df.groupby("グループ番号").agg({"合計株数": "max"})
    # 列名を変更する
    df_max.columns = ["合計最大株数"]
    # インデックスをリセットする
    df_max = df_max.reset_index(drop=True)
    # df_aggとdf_maxを結合する
    df_agg = pd.concat([df_agg, df_max], axis=1)
    # 最大ロット数を計算する
    df_agg["最大ロット数"] = df_agg["合計最大株数"] // df_agg["ロットサイズ"]
    # 資産増額を計算する
    df_agg["資産増額"] = df_agg["最後の総資産"] - df_agg["最初の総資産"]
    # 資産増額を通貨のフォーマットで表示する
    df_agg["資産増額"] = df_agg["資産増額"].map(lambda x: f"¥{int(x):,}" if x >= 0 else f"-¥{abs(int(x)):,}")
    # 保有株数リストと空売り中の株数リストと合計最大株数と最初の総資産と最後の総資産の列を削除する
    df_agg = df_agg.drop(["保有株数リスト", "空売り中の株数リスト", "合計最大株数", "最初の総資産", "最後の総資産"], axis=1)
    # 結果を出力する
    print(df_agg)

    if output_to_file:
        df_agg["資産増額"] = df_agg["資産増額"].str.replace("¥", "")
        df_agg.to_csv(str(csv_path).replace('_history_', '_summary_'), index=False, encoding="shift-jis")

# 例として、sample.csvというファイルを使う
# aggregate_csv('output/trading_history_changeable_20000101_20240203112409_opcl.csv')