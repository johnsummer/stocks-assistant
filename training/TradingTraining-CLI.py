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

    # トレード開始。取引するたびに一回入力する
    while True:
        input_str = input("入力フォーマット「yyyymmdd 空売りロット数-買いロット数」：")
        if input_str == "exit":
            break

        trading_operation = input_str.split()
        if len(trading_operation) != 2:
            print('入力不正')
            continue

        trading_date_str = trading_operation[0]
        stock_lots_str = trading_operation[1]

        stock_lots = stock_lots_str.split('-')
        if len(stock_lots) != 2:
            print('入力不正')
            continue

        try:
            trading_date = dt.datetime.strptime(trading_date_str, '%Y%m%d')
            short_lot = int(stock_lots[0])
            long_lot = int(stock_lots[1])

            print('trading_date:' + str(trading_date))
            print('short_lot:' + str(short_lot))
            print('long_lot:' + str(long_lot))
        except:
            print('入力不正')
        