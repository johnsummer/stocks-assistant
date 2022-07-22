import csv
from datetime import datetime, timedelta
from datetime import date
import os
import collections
import copy
import pandas as pd
import yfinance as yf

import LongTrading as lt
import ShortTrading as st
import CurrentTradingInfo as cti

class Trading:

    # transactions_list = []
    # trading_history_list = []

    # 株価格のデータ
    stock_data_df:pd.DataFrame = None

    # 株銘柄の情報
    stock_info = None
    code:str
    start_date:date
    end_date:date

    transactions_csv = None
    trading_history_csv = None

    # # ロングトレードの情報
    # long_trading:lt.LongTrading = None

    # # ショートトレードの情報
    # short_trading:st.ShortTrading = None

    # 最新取引の情報
    current_trading_info:cti.CurrentTradingInfoModel

    # 直近のトレード履歴(最新10件)を保存するリスト。誤入力の際にトレードの状態を戻すために使う
    __trading_info_history:collections.deque

    # トレード履歴の一時保存の最大件数(現在最新の状態＋10件前まで)
    __MAX_LENGTH_OF_HISTORY = 11

    def __init__(self, code:str, start_date:date, end_date:date, assets:float=0.0) -> None:
        """
        トレードを開始する
        Args:
            code (str): トレード対象銘柄のコード
            start_date (date): トレードの開始日付
            end_date (date): トレードの終了日付
        Returns:
            None
        """

        self.code = code
        self.start_date = start_date
        self.end_date = end_date

        # yfinanceの仕様的に指定した終了日付の前日までデータを取得してくるので、1日を追加する
        end_date = end_date + timedelta(days=1)

        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        self.stock_data_df = yf.download(code + '.T', start=start_str, end=end_str, interval = "1d")

        # 入力履歴を保存するcsvファイルを初期化する
        self.transactions_csv =  'output/transaction_history_' + self.code + '_' + self.start_date.strftime('%Y%m%d') + '_' + self.end_date.strftime('%Y%m%d') + '.csv'
        if not os.path.isfile(self.transactions_csv):
            with open(self.transactions_csv, 'w', newline='') as f:
                header = ['trading_date', 'short_lot', 'long_lot']
                writer = csv.writer(f)
                writer.writerow(header)

        # トレード履歴を保存するcsvファイルを初期化する
        self.trading_history_csv =  'output/trading_history_' + self.code + '_' + self.start_date.strftime('%Y%m%d') + '_' + self.end_date.strftime('%Y%m%d') + '.csv'
        if not os.path.isfile(self.trading_history_csv):
            with open(self.trading_history_csv, 'w', newline='') as f:
                header = ['取引日付', '株価', '買い株数', '保有株数', '平均取得単価', 'ロング損益', '空売り株数', '空売り中の株数', '平均売り単価', 'ショート損益', '総資産']
                writer = csv.writer(f)
                writer.writerow(header)

        self.current_trading_info = cti.CurrentTradingInfoModel()
        self.__trading_info_history = collections.deque()

        self.current_trading_info.assets = assets
        # self.long_trading = lt.LongTrading()
        # self.short_trading = st.ShortTrading()

    def one_transaction(self, trading_date:date, short_lot:int, long_lot:int, lot_volumn:int=100):
        """
        1回の取引を行う
        Args:
            trading_date (date): 取引の日付
            short_lot (int): 該当日に持っている空売りのロット数
            long_lot (int): 該当日に持っている買いのロット数
        Returns:
            None
        """
        try:
            stock_data = self.stock_data_df[self.stock_data_df.index == trading_date.strftime('%Y-%m-%d')]
            if len(stock_data) == 0:
                print("入力された日付のデータはない。その日は祝日か、取得期間外の日付かもしれない。")
                return
            
            stock_price = float(stock_data['Close'])
            # print(stock_price)

            # ショート売買
            short_lot_volumn = short_lot * lot_volumn
            short_transaction_number = short_lot_volumn - self.current_trading_info.short_trading.number_now
            short_profit = 0
            if short_transaction_number > 0: 
                self.current_trading_info.short_trading.short_sell(short_transaction_number, stock_price)
            else:
                short_profit = self.current_trading_info.short_trading.short_cover(0 - short_transaction_number, stock_price)

            # ロング売買
            long_lot_volumn = long_lot * lot_volumn
            long_transaction_number = long_lot_volumn - self.current_trading_info.long_trading.number_now
            long_profit = 0
            if long_transaction_number > 0:
                self.current_trading_info.long_trading.buy(long_transaction_number, stock_price)
            else:
                long_profit = self.current_trading_info.long_trading.sell(0 - long_transaction_number, stock_price)

            # 本取引の情報を最新取引情報として保存する
            self.current_trading_info.trading_date = trading_date
            self.current_trading_info.stock_price = stock_price
            self.current_trading_info.short_lot = short_lot
            self.current_trading_info.short_transaction_number = short_transaction_number
            self.current_trading_info.long_lot = long_lot
            self.current_trading_info.long_transaction_number = long_transaction_number
            self.current_trading_info.short_profit = short_profit
            self.current_trading_info.long_profit = long_profit

            # 利益を総資産に加算
            self.current_trading_info.assets = self.current_trading_info.assets + short_profit + long_profit

            # トレードの状態を履歴として保存する(最大10件)
            if len(self.__trading_info_history) == self.__MAX_LENGTH_OF_HISTORY:
                self.__trading_info_history.popleft()

            current_trading_info_tmp = copy.deepcopy(self.current_trading_info)
            self.__trading_info_history.append(current_trading_info_tmp)

            # # トレードの状態を履歴として保存する処理の動作確認
            # for current_trading_info_tmp in self.__trading_info_history:
            #     print(str(current_trading_info_tmp.trading_date) + ' : ' + str(current_trading_info_tmp.assets))

            # 取引記録のファイルを出力
            self.__output_transaction_input_to_csv()
            self.__output_trading_info_to_csv()

            self.__display_transaction_detail()

        except Exception as e:
            print(e)

    def reset_trading_info(self, number:int):
        """
        指定した番号に該当したトレードの状態に戻す。番号についてはshow_trading_history_in_stack()で確認できる。
        Args:
            number (int): 戻したい取引の個数（例：2を指定した場合は2個前の取引の状態にトレードをリセットする）
        Returns:
            None
        """
        max = self.__MAX_LENGTH_OF_HISTORY if self.__MAX_LENGTH_OF_HISTORY < len(self.__trading_info_history) else len(self.__trading_info_history)
        max = max - 1   # 現在の最新状態を除いた後の最大の件数

        if number > max:
            print('指定した番号は上限を超えています。現時点は最大' + str(max) + '個前の取引まで戻すことが可能です。')
            return
        
        if number <= 0:
            print('1～' + str(max) + 'の整数を指定してください。')
            return

        for i in range(number):
            self.__trading_info_history.pop()

        # トレードの状態をリセットする
        self.current_trading_info = copy.deepcopy(self.__trading_info_history[-1])

        # csvファイルからも不要な行を削除する
        df_trading_history_csv = pd.read_csv(self.trading_history_csv, encoding="shift-jis")
        df_trading_history_csv = df_trading_history_csv[:-number]
        df_trading_history_csv.to_csv(self.trading_history_csv, index=False, encoding="shift-jis")

        df_transactions_csv = pd.read_csv(self.transactions_csv, encoding="shift-jis")
        df_transactions_csv = df_transactions_csv[:-number]
        df_transactions_csv.to_csv(self.transactions_csv, index=False, encoding="shift-jis")

    def show_trading_history_in_stack(self):
        """
        戻す可能な取引の一覧を表示する。
        Args:
            None
        Returns:
            None
        """
        print("※：0番は現在最新の状態です。")

        i = 0
        for current_trading_info_tmp in reversed(self.__trading_info_history):
            print(str(i) + ' : ' + current_trading_info_tmp.trading_date.strftime('%Y-%m-%d') 
                + ', ショートロット: ' + str(current_trading_info_tmp.short_lot) 
                + ', ロングロット：' + str(current_trading_info_tmp.long_lot) 
                + ', 総資産：' + f'{current_trading_info_tmp.assets:,.1f}')
            i = i + 1

    # 取引の入力情報をcsvファイルに書き出す
    def __output_transaction_input_to_csv(self):

        transaction = [
            self.current_trading_info.trading_date.strftime('%Y-%m-%d'), 
            str(self.current_trading_info.short_lot), 
            str(self.current_trading_info.long_lot)
        ]

        with open(self.transactions_csv, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(transaction)

    # トレード履歴をcsvファイルに書き出す
    def __output_trading_info_to_csv(self):

        # 平均単価が0の場合は0で出力する
        avg_short_price = 0
        if self.current_trading_info.short_trading.number_now != 0:
            avg_short_price = self.current_trading_info.short_trading.total_amount_now / self.current_trading_info.short_trading.number_now
        avg_long_price = 0
        if self.current_trading_info.long_trading.number_now != 0:
            avg_long_price = self.current_trading_info.long_trading.total_amount_now / self.current_trading_info.long_trading.number_now

        trading_info = [
            self.current_trading_info.trading_date.strftime('%Y-%m-%d'),
            str(self.current_trading_info.stock_price),
            str(self.current_trading_info.long_transaction_number),
            str(self.current_trading_info.long_trading.number_now),
            str(avg_long_price),
            str(self.current_trading_info.long_profit),
            str(self.current_trading_info.short_transaction_number),
            str(self.current_trading_info.short_trading.number_now),
            str(avg_short_price),
            str(self.current_trading_info.short_profit),
            str(self.current_trading_info.assets)
        ]

        with open(self.trading_history_csv, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(trading_info)

    # 1取引を行った後のトレード詳細情報を表示する
    def __display_transaction_detail(self):

        # 平均単価が0の場合は0で出力する
        avg_short_price = 0
        if self.current_trading_info.short_trading.number_now != 0:
            avg_short_price = self.current_trading_info.short_trading.total_amount_now / self.current_trading_info.short_trading.number_now
        avg_long_price = 0
        if self.current_trading_info.long_trading.number_now != 0:
            avg_long_price = self.current_trading_info.long_trading.total_amount_now / self.current_trading_info.long_trading.number_now

        print('取引日付：' + self.current_trading_info.trading_date.strftime('%Y-%m-%d'))
        print('株価(終値)：' + f'{self.current_trading_info.stock_price:,.1f}')
        print('---------------------')
        print('平均売り単価：' + f'{avg_short_price:,.1f}')
        print('空売り株数：' + str(self.current_trading_info.short_transaction_number))
        print('空売り中の総株数：' + str(self.current_trading_info.short_trading.number_now))
        print('損益(ショート)：' + f'{self.current_trading_info.short_profit:,.1f}')
        print('---------------------')
        print('平均取得単価：' + f'{avg_long_price:,.1f}')
        print('買い株数：' + str(self.current_trading_info.long_transaction_number))
        print('保有株数：' + str(self.current_trading_info.long_trading.number_now))
        print('損益(ロング)：' + f'{self.current_trading_info.long_profit:,.1f}')
        print('---------------------')
        print('総資産：' + f'{self.current_trading_info.assets:,.1f}')
        print('---------------------')
