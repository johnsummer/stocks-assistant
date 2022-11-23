import argparse
import datetime as dt
import Trading as tr
import StockInfo as si
import re
import traceback

# 1取引を行った後のトレード詳細情報を表示する
def display_transaction_detail(trading:tr.Trading, message:str):

    # 平均単価が0の場合は0で出力する
    avg_short_price = 0
    if trading.current_trading_info.short_trading.number_now != 0:
        avg_short_price = trading.current_trading_info.short_trading.total_amount_now / trading.current_trading_info.short_trading.number_now
    avg_long_price = 0
    if trading.current_trading_info.long_trading.number_now != 0:
        avg_long_price = trading.current_trading_info.long_trading.total_amount_now / trading.current_trading_info.long_trading.number_now

    if len(message) > 0:
        print(message)

    print('取引日付：' + trading.current_trading_info.trading_date.strftime('%Y-%m-%d')
        + '\t\t株価(終値)：' + f'{trading.current_trading_info.stock_price:,.1f}')
    print('---------------------')
    # print('売り注文株数：' + str(trading.current_trading_info.short_transaction_number)
    #     + '\t\t売り総株数：' + str(trading.current_trading_info.short_trading.number_now))
    print('平均売り単価：' + f'{avg_short_price:,.1f}'
        + '\t\t売り総額：' + f'{trading.current_trading_info.short_trading.total_amount_now:,.1f}'
        + '\t\t損益(ショート)：' + f'{trading.current_trading_info.short_profit:,.1f}')
    # print('---------------------')
    # print('買い注文株数：' + str(trading.current_trading_info.long_transaction_number)
    #     + '\t\t保有株数：' + str(trading.current_trading_info.long_trading.number_now))
    print('平均取得単価：' + f'{avg_long_price:,.1f}'
        + '\t\t保有総額：' + f'{trading.current_trading_info.long_trading.total_amount_now:,.1f}'
        + '\t\t損益(ロング)：' + f'{trading.current_trading_info.long_profit:,.1f}')
    print('---------------------')
    print('総資産：' + f'{trading.current_trading_info.assets:,.1f}')
    print('---------------------')

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
    assets = 10000000 if args.a == None else float(args.a)

    # 起動時入力された引数に関する動作確認
    print('code=' + args.code)
    print('start_date=' + str(start_date))
    print('end_date=' + str(end_date))
    print('lot=' + str(lot_volumn))
    print('assets=' + str(assets))

    print('データ読み込み中。。。')
    stock_info = si.StockInfo(args.code, start_date, end_date)
    print('データ読み込み完了。')

    # 取得できた株価データの範囲を確認するためにCLIでDataFrameを表示する
    stock_data = stock_info.stock_data_df
    print(stock_data)

    # 取引記録のファイル出力に関する動作確認用の変数
    # i = 0

    # トレーディングオブジェクトの初期化
    trading_close = tr.Trading(stock_info, assets, 'close')
    trading_next_open = tr.Trading(stock_info, assets, 'open')

    # 取引入力における日付の年の部分。Noneでなければ設定されているとする。その場合は年の入力を省くことができる。
    trading_date_year:str = None

    # トレード開始。取引するたびに一回入力する
    while True:
        input_str = input("★入力フォーマット「yyyymmdd 空売りロット数-買いロット数」：")

        # 取引以外の操作
        # 取引入力時の年を固定で設定するコマンド
        if input_str.startswith("y="):
            year_setting_input = input_str.split('=')
            if len(year_setting_input) == 2:
                trading_date_year = year_setting_input[1]
                
                # 年の設定をリセットする
                if trading_date_year == '':
                    trading_date_year = None
                    print("yearをリセットしました")
                    continue

                # 入力チェック
                if not re.compile('[0-9]{4}').search(trading_date_year):
                    print('年のフォーマットが不正')
                    trading_date_year = None

                print("year=" + trading_date_year)
            else:
                print('年設定が入力不正')

            continue

        # トレード履歴関連のコマンド
        if input_str.startswith("history "):
            command_list = input_str.split()
            if command_list[1] == "show":
                if len(command_list) == 2 or (len(command_list) == 3 and command_list[2] == "close"):
                    trading_close.show_trading_history_in_stack()
                elif len(command_list) == 3 and command_list[2] == "open":
                    trading_next_open.show_trading_history_in_stack()
                else:
                    print('コマンド不正')
                continue
            elif command_list[1] == "reset":
                if len(command_list) != 3:
                    print('コマンド不正')
                    continue
                
                number = int(command_list[2])
                trading_close.reset_trading_info(number)
                trading_next_open.reset_trading_info(number)
                continue
            else:
                print('コマンド不正')
                continue

        # 総資産超過時の処理モードを設定するコマンド
        if input_str.startswith("allow_over_assets="):
            command_list = input_str.split('=')
            if len(command_list) == 2:
                value = command_list[1]

                if value == 'true':
                    trading_close.action_mode = trading_close.ACTION_MODE_WARNING
                    trading_next_open.action_mode = trading_next_open.ACTION_MODE_WARNING
                elif value == 'false':
                    trading_close.action_mode = trading_close.ACTION_MODE_FORBIDDEN
                    trading_next_open.action_mode = trading_next_open.ACTION_MODE_FORBIDDEN
                else:
                    print('コマンド不正。値に true または false を指定してください。')

                print('allow_over_assets=' + value)
            else:
                print('コマンド不正')
                
            continue


        # アプリを終了させるコマンド
        if input_str == "exit":
            break

        # 上記のif文に該当しない場合、取引操作の解析に入る
        # 入力チェック
        trading_operation = input_str.split()
        if len(trading_operation) != 2:
            print('取引情報が入力不正')
            continue

        trading_date_str = trading_operation[0] if trading_date_year == None else trading_date_year + trading_operation[0]
        stock_lots_str = trading_operation[1]

        # 日付の入力チェック（桁数だけ）
        if not re.compile('[0-9]{8}').search(trading_date_str):
            print('日付のフォーマットが不正')
            continue

        # ロットの入力チェック
        stock_lots = stock_lots_str.split('-')
        if len(stock_lots) != 2:
            print('ロット数が入力不正')
            continue

        try:
            trading_date = dt.datetime.strptime(trading_date_str, '%Y%m%d')
            short_lot = int(stock_lots[0])
            long_lot = int(stock_lots[1])

            # 取引ごとの入力に関する動作確認
            # print('trading_date:' + str(trading_date.date()))
            # print('short_lot:' + str(short_lot))
            # print('long_lot:' + str(long_lot))

            print('■ 大引け注文：')
            trading_close_message = trading_close.one_transaction(trading_date, short_lot, long_lot, lot_volumn, 
                trading_close.TRANSACTION_TIME_CLOSE)

            if trading_close_message[0] == 'failure':
                print(trading_close_message[1])
            else:
                display_transaction_detail(trading_close, trading_close_message[1])
                
                print('■ 翌日注文：')
                trading_next_open_messege = trading_next_open.one_transaction(trading_date, short_lot, long_lot, lot_volumn, 
                    trading_next_open.TRANSACTION_TIME_NEXT_OPEN)

                if trading_next_open_messege[0] == 'failure':
                    print(trading_close_message[1])
                    trading_close.reset_trading_info(1)
                    print('Inof:翌日寄付注文に失敗のため、1取引分の大引け注文を巻き戻す')
                else:
                    display_transaction_detail(trading_next_open, trading_next_open_messege[1])

        except Exception as e:
            print('入力不正')
            print(traceback.format_exc())
        
        # 取引記録のファイル出力に関する動作確認
        # i = i + 1
        # if (i % 2 == 0):
        #     trading.output_transaction_list()