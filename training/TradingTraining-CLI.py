import argparse
import datetime as dt

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='トレード練習ツール(CLIプロトタイプ版)')

    parser.add_argument('code', help='銘柄コード(XXXX)')
    parser.add_argument('-s', help='トレード開始日付(yyyymmdd)。デフォルトは2018/01/01')
    parser.add_argument('-e', help='トレード終了日付(yyyymmdd)。デフォルトは実行日付')
    parser.add_argument('-l', help='1ロットの株数。デフォルトは100株')
    parser.add_argument('-a', help='トレード用の想定金額(初期資産)。デフォルトは1000万(円)')

    args = parser.parse_args()

    # 各引数のデフォルト値を定義する
    start_date_str = '20180101' if args.s == None else args.s
    start_date = dt.datetime.strptime(start_date_str, '%Y%m%d').date()
    end_date = dt.datetime.now().date() if args.e == None else dt.datetime.strptime(args.e, '%Y%m%d').date()
    lot = 100 if args.l == None else int(args.l)
    assets = 10000000 if args.a == None else int(args.a)

    print('code=' + args.code)
    print('start_date=' + str(start_date))
    print('end_date=' + str(end_date))
    print('lot=' + str(lot))
    print('assets=' + str(assets))
