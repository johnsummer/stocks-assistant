import argparse
import datetime as dt
import sys
import re
import traceback

from pandas import DataFrame

from colorama import init
from termcolor import colored

import Trading as tr
import StockInfo as si
import CSVLoader as cl
import ReopenTradingInfo as rti

# 1取引を行った後のトレード詳細情報を表示する
def display_transaction_detail(trading:tr.Trading, message:str):

    # 平均単価が0の場合は0で出力する
    avg_short_price = 0
    if trading.current_trading_info.short_trading.number_now != 0:
        avg_short_price = trading.current_trading_info.short_trading.total_amount_now / trading.current_trading_info.short_trading.number_now
    avg_long_price = 0
    if trading.current_trading_info.long_trading.number_now != 0:
        avg_long_price = trading.current_trading_info.long_trading.total_amount_now / trading.current_trading_info.long_trading.number_now

    # Windowsターミナル対応のため
    init()

    if len(message) > 0:
        print(message)

    # 損益の色を定義する
    COLOR_COMMON = 'on_black'
    COLOR_PROFIT = 'on_light_red'
    COLOR_LOSS = 'on_light_green'

    # ショートの損益色
    short_profit_color = COLOR_COMMON
    if trading.current_trading_info.short_profit > 0:
        short_profit_color = COLOR_PROFIT
    elif trading.current_trading_info.short_profit < 0:
        short_profit_color = COLOR_LOSS
    
    # ロングの損益色
    long_profit_color = COLOR_COMMON
    if trading.current_trading_info.long_profit > 0:
        long_profit_color = COLOR_PROFIT
    elif trading.current_trading_info.long_profit < 0:
        long_profit_color = COLOR_LOSS

    # 平均売り単価の色
    short_price_color = COLOR_COMMON
    if avg_short_price > trading.current_trading_info.stock_price:
        short_price_color = COLOR_PROFIT
    elif avg_short_price > 0 and avg_short_price < trading.current_trading_info.stock_price:
        short_price_color = COLOR_LOSS

    # 平均取得単価の色
    long_price_color = COLOR_COMMON
    if avg_long_price > 0 and avg_long_price < trading.current_trading_info.stock_price:
        long_price_color = COLOR_PROFIT
    elif avg_long_price > trading.current_trading_info.stock_price:
        long_price_color = COLOR_LOSS

    print('取引日付：' + trading.current_trading_info.trading_date.strftime('%Y-%m-%d')
        + '\t\t株価：' + f'{trading.current_trading_info.stock_price:,.1f}'
        + '\t\t' + colored('総資産：' + f'{trading.current_trading_info.assets:,.1f}', 'red', attrs=["bold"]))
    print('---------------------')
    # print('売り注文株数：' + str(trading.current_trading_info.short_transaction_number)
    #     + '\t\t売り総株数：' + str(trading.current_trading_info.short_trading.number_now))
    print(colored('平均売り単価：' + f'{avg_short_price:,.1f}', on_color=short_price_color)
        + '\t\t売り総額：' + f'{trading.current_trading_info.short_trading.total_amount_now:,.1f}'
        + '\t\t損益(ショート)：' + colored(f'{trading.current_trading_info.short_profit:,.1f}', on_color=short_profit_color))
    # print('---------------------')
    # print('買い注文株数：' + str(trading.current_trading_info.long_transaction_number)
    #     + '\t\t保有株数：' + str(trading.current_trading_info.long_trading.number_now))
    print(colored('平均取得単価：' + f'{avg_long_price:,.1f}', on_color=long_price_color)
        + '\t\t保有総額：' + f'{trading.current_trading_info.long_trading.total_amount_now:,.1f}'
        + '\t\t損益(ロング)：' + colored(f'{trading.current_trading_info.long_profit:,.1f}', on_color=long_profit_color))
    print('------------------------------------------------------------------------------------')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='トレード練習ツール(CLI版)')

    parser.add_argument('code', help='銘柄コード(日本銘柄の場合：XXXX.T)')
    parser.add_argument('-s', help='トレード開始日付(yyyymmdd)。デフォルトは2013/01/01')
    parser.add_argument('-e', help='トレード終了日付(yyyymmdd)。デフォルトは実行日付')
    parser.add_argument('-l', help='1ロットの株数。デフォルトは100株')
    parser.add_argument('-a', help='トレード用の想定金額(初期資産)。デフォルトは1000万(円)')
    parser.add_argument('-ro', '--reopen', help='トレード再開モードで起動する', action='store_true')

    args = parser.parse_args()

    # 各引数のデフォルト値を定義する
    start_date_str = '20130101' if args.s == None else args.s
    end_date = dt.datetime.now().date() if args.e == None else dt.datetime.strptime(args.e, '%Y%m%d').date()
    lot_volumn = 100 if args.l == None else int(args.l)

    assets_close = 10000000
    assets_open = assets_close
    assets_opcl = assets_close    # 翌日寄付で注文・大引で手仕舞いの方式の資産

    mode = ''
    code = args.code

    if args.code == 'ca' or args.code == 'changeable':
        mode = 'changeable'
        code = 'changeable'
    else:
        mode = 'single'

    if args.a != None:
        assets_close = float(args.a)
        assets_open = assets_close
        assets_opcl = assets_close

    # トレード練習の開始日時（文字列）
    training_start_datetime_str = None

    if args.reopen:
        # トレード再開の場合、各引数の値を上書きする
        csv_loader = cl.CSVLoader(code)
        reopen_choices = list(csv_loader.reopen_trading_items.values())

        if len(reopen_choices) == 0:
            print('再開可能なトレードがありません。銘柄コードを確認のうえ本ツールを再度起動してください。')
            sys.exit()

        print('再開可能なトレード候補：')
        print('番号\tトレード開始日\tトレード中断日\t練習開始日時\t中断時の総資産(大引け - 寄付 - 組合せ)\t\t最後の銘柄コード')

        i = 0
        for choice in reopen_choices:
            print(str(i) + '\t' + choice.start_date + '\t' + choice.last_trading_date + '\t' 
                + choice.training_start_datetime + '\t￥' + f'{choice.assets_dict["close"]:,.1f}' 
                + ' - ￥' + f'{choice.assets_dict["open"]:,.1f}' + ' - ￥' + f'{choice.assets_dict["opcl"]:,.1f}'
                + '\t\t' + choice.last_code)
            i = i + 1

        input_str_choice = input('上記の番号から再開したいトレードを選択してください：')
        if input_str_choice == "exit":
            sys.exit()

        while int(input_str_choice) >= i or int(input_str_choice) < 0:
            print('範囲外の番号を選択されています。もう一度入力しなおしてください。')
            input_str_choice = input('上記の番号から再開したいトレードを選択してください：')
            if input_str_choice == "exit":
                sys.exit()

        reopen_trading_info:rti.ReopenTradingInfo = reopen_choices[int(input_str_choice)]

        start_date_str = reopen_trading_info.start_date
        training_start_datetime_str = reopen_trading_info.training_start_datetime
        assets_close = reopen_trading_info.assets_dict['close']
        assets_open = reopen_trading_info.assets_dict['open']
        assets_opcl =reopen_trading_info.assets_dict['opcl']   # TODO:Noneによりエラーが発生する可能性がある

    # 文字列の引数を処理に必要な型に変換
    start_date = dt.datetime.strptime(start_date_str, '%Y%m%d').date()
    if training_start_datetime_str == None:
        training_start_datetime_str = dt.datetime.now().strftime('%Y%m%d%H%M%S')


    # モード共通の変数を用意する
    stock_info:si.StockInfo = None
    stock_data:DataFrame = None
    trading_close:tr.Trading = None
    trading_next_open:tr.Trading = None
    trading_opcl:tr.Trading = None

    if mode == 'changeable':
        print('「銘柄可変」モードでトレードを始めます。')
        code = None
    else:
        print('データ読み込み中。。。')
        stock_info = si.StockInfo(code, start_date, end_date)
        print('データ読み込み完了。')

        # 取得できた株価データの範囲を確認するためにCLIでDataFrameを表示する
        stock_data = stock_info.stock_data_df
        print(stock_data)

        # トレードパラメータの表示、兼入力引数に関する動作確認
        print('code=' + code)
        print('start_date=' + str(start_date))
        print('end_date=' + str(end_date))
        print('lot=' + str(lot_volumn))
        print('assets=￥' + f'{assets_close:,.1f}' + ' - ￥' + f'{assets_open:,.1f}' + ' - ￥' + f'{assets_opcl:,.1f}')
        print()

    # トレーディングオブジェクトの初期化
    trading_close = tr.Trading(stock_info, training_start_datetime_str, assets_close, 'close', start_date_str, mode)
    trading_next_open = tr.Trading(stock_info, training_start_datetime_str, assets_open, 'open', start_date_str, mode)
    trading_opcl = tr.Trading(stock_info, training_start_datetime_str, assets_opcl, 'opcl', start_date_str, mode)

    # 取引入力における日付の年の部分。Noneでなければ設定されているとする。その場合は年の入力を省くことができる。
    trading_date_year:str = None

    # トレード開始。取引するたびに一回入力する
    while True:
        input_str = input("★ コマンド：")
        print()

        # 取引以外の操作
        # トレード時のパラメータを設定する操作
        # 取引入力時の年を固定で設定するコマンド
        if input_str.startswith("y="):
            year_setting_input = input_str.split('=')
            if len(year_setting_input) == 2:
                
                # 年の設定をリセットする
                if year_setting_input[1] == '':
                    trading_date_year = None
                    print("yearをリセットしました")
                    continue

                # 入力チェック
                if not re.compile('[0-9]{4}').search(year_setting_input[1]):
                    print('年のフォーマットが不正')
                    continue

                trading_date_year = year_setting_input[1]
                print(trading_date_year + '年のトレードを開始します。')
            else:
                print('年設定が入力不正')

            continue

        # ロットサイズを変更するコマンド
        elif input_str.startswith("l="):
            
            # ポジションが0-0でないとロットサイズ変更させない
            if trading_close.current_trading_info.long_lot != 0 or \
                trading_close.current_trading_info.short_lot != 0 or \
                trading_next_open.current_trading_info.long_lot != 0 or \
                trading_next_open.current_trading_info.short_lot != 0 or \
                trading_opcl.current_trading_info.long_lot != 0 or \
                trading_opcl.current_trading_info.short_lot != 0:
                print('ポジションを0-0にしてロットサイズを変更してください')
                continue

            lot_setting_input = input_str.split('=')
            if len(lot_setting_input) == 2:
                try:
                    lot_volumn = int(lot_setting_input[1])
                    print('ロットサイズ：' + str(lot_volumn))
                except Exception as e:
                    print('ロットサイズの指定値が不正。整数で入力してください。')
                    print(traceback.format_exc())
            else:
                print('コマンド不正')

            continue

        # トレード対象の銘柄を設定するコマンド
        elif input_str.startswith('i='):
            if mode == 'changeable':
                # ポジションが0-0でないと銘柄を変更させない
                if trading_close.current_trading_info.long_lot != 0 or \
                    trading_close.current_trading_info.short_lot != 0 or \
                    trading_next_open.current_trading_info.long_lot != 0 or \
                    trading_next_open.current_trading_info.short_lot != 0 or \
                    trading_opcl.current_trading_info.long_lot != 0 or \
                    trading_opcl.current_trading_info.short_lot != 0:
                    print('ポジションを0-0にして銘柄を変更してください')
                    continue


                command_list = input_str.split('=')
                if len(command_list) == 2:
                    if command_list[1] == '':
                        print('銘柄コードが空になっています。')
                        continue

                    code = command_list[1]
                    print('データ読み込み中。。。')
                    stock_info = si.StockInfo(code, start_date, end_date)
                    print('データ読み込み完了。')

                    # 取得できた株価データの範囲を確認するためにCLIでDataFrameを表示する
                    stock_data = stock_info.stock_data_df
                    print(stock_data)

                    # トレードパラメータの表示、兼入力引数に関する動作確認
                    print('code=' + code)
                    print('lot=' + str(lot_volumn))
                    print('assets=￥' + f'{trading_close.current_trading_info.assets:,.1f}' 
                          + ' - ￥' + f'{trading_next_open.current_trading_info.assets:,.1f}'
                          + ' - ￥' + f'{trading_opcl.current_trading_info.assets:,.1f}')
                    print()

                    # トレーディングオブジェクトの初期化
                    trading_close.stock_info = stock_info
                    trading_next_open.stock_info = stock_info
                    trading_opcl.stock_info = stock_info
                else:
                    print('コマンド不正')
            else:
                print('単独モードでは銘柄変更ができません。')
            
            continue

        # 総資産超過時の処理モードを設定するコマンド
        elif input_str.startswith("allow_over_assets="):
            command_list = input_str.split('=')
            if len(command_list) == 2:
                value = command_list[1]

                if value == 'true':
                    trading_close.action_mode = trading_close.ACTION_MODE_WARNING
                    trading_next_open.action_mode = trading_next_open.ACTION_MODE_WARNING
                    trading_opcl.action_mode = trading_opcl.ACTION_MODE_WARNING
                elif value == 'false':
                    trading_close.action_mode = trading_close.ACTION_MODE_FORBIDDEN
                    trading_next_open.action_mode = trading_next_open.ACTION_MODE_FORBIDDEN
                    trading_opcl.action_mode = trading_opcl.ACTION_MODE_FORBIDDEN
                else:
                    print('コマンド不正。値に true または false を指定してください。')

                print('allow_over_assets=' + value)
            else:
                print('コマンド不正')
                
            continue

        # 指令系の操作
        # トレード履歴関連のコマンド
        elif input_str.startswith("history "):
            command_list = input_str.split()
            if command_list[1] == "show":
                if len(command_list) == 2 or (len(command_list) == 3 and command_list[2] == "close"):
                    trading_close.show_trading_history_in_stack()
                elif len(command_list) == 3 and command_list[2] == "open":
                    trading_next_open.show_trading_history_in_stack()
                elif len(command_list) == 3 and command_list[2] == "opcl":
                    trading_opcl.show_trading_history_in_stack()
                else:
                    print('コマンド不正')
                
                print()
                continue
            elif command_list[1] == "reset":
                if len(command_list) != 3:
                    print('コマンド不正')
                    continue
                
                number = int(command_list[2])

                trading_info = trading_close.get_one_transaction_of_trading_history(number)
                if trading_info.stock_code != code:
                    print('異なる銘柄コードの取引履歴に戻すことができません。')
                    continue

                trading_close.reset_trading_info(number)
                trading_next_open.reset_trading_info(number)
                trading_opcl.reset_trading_info(number)

                # 当該取引の時のロットサイズを現在のロットサイズにセットする
                lot_volumn = trading_close.current_trading_info.lot_volumn

                continue
            else:
                print('コマンド不正')
                continue
        
        # メモ記録のコメント
        elif input_str.startswith("memo "):
            command_list = input_str.split()
            if len(command_list) != 3:
                print('取引情報が入力不正')
                continue

            memo_date_str = command_list[1] if len(command_list[1]) == 8 or trading_date_year == None else trading_date_year + command_list[1]
            
            # 日付の入力チェック（桁数だけ）
            if not re.compile('[0-9]{8}').search(memo_date_str):
                print('日付のフォーマットが不正')
                continue

            memo_date = dt.datetime.strptime(memo_date_str, '%Y%m%d').date()

            result_of_taking_memo_open = None
            result_of_taking_memo_opcl = None
            # 大引けの日付を基準でメモを書き込む。寄付、また組合せのファイルに対しては指定した日付の次の営業日に書き込む
            row_number = trading_close.take_memo_by_date(memo_date, command_list[2])
            if row_number != -1:
                result_of_taking_memo_open = trading_next_open.take_memo_by_row_number(row_number, command_list[2])
                result_of_taking_memo_opcl = trading_opcl.take_memo_by_row_number(row_number, command_list[2])
            else:
                print("大引け取引のcsvファイルへのメモ記録に失敗しました。指定した日付はトレード履歴がない可能性があります。")
                continue

            if result_of_taking_memo_open is None:
                print("寄付取引のcsvファイルへのメモ記録に失敗しました。")
            
            if result_of_taking_memo_opcl is None:
                print("組合せのcsvファイルへのメモ記録に失敗しました。")

            continue

        # アプリを終了させるコマンド
        elif input_str == "exit":
            sys.exit()

        # 上記の条件分岐に該当しない場合、取引操作として処理する

        # 銘柄コードが指定されているかをチェックする
        if code is None or code == '' or stock_info is None:
            print('トレード対象の銘柄を指定されていません。')
            continue

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
                print('Info:大引注文に失敗のため、他の注文を実行しませんでした。')
            else:
                display_transaction_detail(trading_close, trading_close_message[1])
                
                print('■ 翌日寄付注文：')
                trading_next_open_messege = trading_next_open.one_transaction(trading_date, short_lot, long_lot, lot_volumn, 
                    trading_next_open.TRANSACTION_TIME_NEXT_OPEN)

                if trading_next_open_messege[0] == 'failure':
                    print(trading_next_open_messege[1])
                    trading_close.reset_trading_info(1)
                    print('Info:翌日寄付注文に失敗のため、大引注文を1取引分巻き戻し、組合せ注文を実行しませんでした。')
                else:
                    display_transaction_detail(trading_next_open, trading_next_open_messege[1])

                    print('■ 組合せ注文：')

                    # 注文タイミングの設定
                    transaction_time = trading_opcl.TRANSACTION_TIME_NEXT_OPEN
                    current_short_number = trading_opcl.current_trading_info.short_trading.number_now
                    current_long_number = trading_opcl.current_trading_info.long_trading.number_now

                    if short_lot == 0 and long_lot == 0:    # 玉持ちで全部手仕舞った場合
                        transaction_time = trading_opcl.TRANSACTION_TIME_CLOSE
                    elif ( short_lot == long_lot ):  # スクエアにした場合
                        transaction_time = trading_opcl.TRANSACTION_TIME_CLOSE
                    elif ( current_short_number != 0 and current_long_number != 0) \
                        and (short_lot == 0 or long_lot == 0 ):     # 売買の片方を全部手仕舞い、もう片方は維持する場合
                        short_number = short_lot * lot_volumn
                        long_number = long_lot * lot_volumn
                        if short_number == current_short_number or long_number == current_long_number:
                            transaction_time = trading_opcl.TRANSACTION_TIME_CLOSE

                    # 上記以外の場合は初期値にする

                    trading_opcl_messege = trading_opcl.one_transaction(trading_date, short_lot, long_lot, lot_volumn, 
                        transaction_time)

                    if trading_opcl_messege[0] == 'failure':
                        print(trading_opcl_messege[1])
                        trading_close.reset_trading_info(1)
                        trading_next_open.reset_trading_info(1)
                        print('Info:組合せ文に失敗のため、他の注文を1取引分巻き戻しました。')
                    else:
                        display_transaction_detail(trading_opcl, trading_opcl_messege[1])

        except Exception as e:
            print('入力不正')
            print(traceback.format_exc())

        print()   
        # 取引記録のファイル出力に関する動作確認
        # i = i + 1
        # if (i % 2 == 0):
        #     trading.output_transaction_list()