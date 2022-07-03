import argparse
import datetime as dt
import Trading as tr

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
    lot_volumn = 100 if args.l == None else int(args.l)
    assets = 10000000 if args.a == None else int(args.a)

    # 起動時入力された引数に関する動作確認
    print('code=' + args.code)
    print('start_date=' + str(start_date))
    print('end_date=' + str(end_date))
    print('lot=' + str(lot_volumn))
    print('assets=' + str(assets))

    print('データ読み込み中。。。')
    trading = tr.Trading(args.code, start_date, end_date, assets)
    print('データ読み込み完了。')

    # 株価データ取得に関する動作確認
    # stock_data = trading.stock_data_df
    # print(stock_data)

    # 取引記録のファイル出力に関する動作確認用の変数
    # i = 0

    # 取引入力における日付の年の部分。Noneでなければ設定されているとする。その場合は年の入力を省くことができる。
    trading_date_year:str = None

    # トレード開始。取引するたびに一回入力する
    while True:
        input_str = input("★入力フォーマット「yyyymmdd 空売りロット数-買いロット数」：")

        # 取引以外の操作
        # 取引入力時の年を固定で設定する
        if input_str.startswith("y="):
            input = input_str.split('=')
            if len(input != 2):
                print('入力不正')
                continue

            trading_date_year = input[1]
            # TODO: 入力チェック
            continue

        # アプリを終了させる
        if input_str == "exit":
            break

        trading_operation = input_str.split()
        if len(trading_operation) != 2:
            print('入力不正')
            continue

        # TODO: 設定された年を使う
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

            # 取引ごとの入力に関する動作確認
            # print('trading_date:' + str(trading_date.date()))
            # print('short_lot:' + str(short_lot))
            # print('long_lot:' + str(long_lot))

            trading.one_transaction(trading_date, short_lot, long_lot, lot_volumn)

        except:
            print('入力不正')
        
        # 取引記録のファイル出力に関する動作確認
        # i = i + 1
        # if (i % 2 == 0):
        #     trading.output_transaction_list()