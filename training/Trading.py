import csv
from datetime import datetime, timedelta
from datetime import date
import os
import pandas as pd
import yfinance as yf

import LongTrading as lt
import ShortTrading as st

class Trading:

    transactions_list = []

    # 株価格のデータ
    stock_data_df:pd.DataFrame = None

    # 株銘柄の情報
    stock_info = None
    code:str
    start_date:date
    end_date:date

    transactions_csv = None

    # ロングトレードの情報
    long_trading:lt.LongTrading = None

    # ショートトレードの情報
    short_trading:st.ShortTrading = None

    # 総資産
    assets = 0.0

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
        self.assets = assets

        # yfinanceの仕様的に指定した終了日付の前日までデータを取得してくるので、1日を追加する
        end_date = end_date + timedelta(days=1)

        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        self.stock_data_df = yf.download(code + '.T', start=start_str, end=end_str, interval = "1d")

        # 取引履歴を保存するcsvファイルを初期化する
        self.transactions_csv =  'output/transaction_history_' + self.code + '_' + self.start_date.strftime('%Y%m%d') + '_' + self.end_date.strftime('%Y%m%d') + '.csv'
        if not os.path.isfile(self.transactions_csv):
            with open(self.transactions_csv, 'w', newline='') as f:
                header = ['trading_date', 'short_lot', 'long_lot']
                writer = csv.writer(f)
                writer.writerow(header)

        self.long_trading = lt.LongTrading()
        self.short_trading = st.ShortTrading()

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
            
            stock_price = float(stock_data['Adj Close'])
            # print(stock_price)

            transaction = [trading_date.strftime('%Y-%m-%d'), str(short_lot), str(long_lot)]
            self.transactions_list.append(transaction)

            # ショート売買
            short_lot_volumn = short_lot * lot_volumn
            short_transaction_number = short_lot_volumn - self.short_trading.number_now
            short_profit = 0
            if short_transaction_number > 0: 
                self.short_trading.short_sell(short_transaction_number, stock_price)
            else:
                short_profit = self.short_trading.short_cover(0 - short_transaction_number, stock_price)

            # ロング売買
            long_lot_volumn = long_lot * lot_volumn
            long_transaction_number = long_lot_volumn - self.long_trading.number_now
            long_profit = 0
            if long_transaction_number > 0:
                self.long_trading.buy(long_transaction_number, stock_price)
            else:
                long_profit = self.long_trading.sell(0 - long_transaction_number, stock_price)

            # 利益を総資産に加算
            self.assets = self.assets + short_profit + long_profit

            # 取引記録のファイルを出力
            if short_lot == 0 and long_lot == 0:
                self.output_transaction_list()

            self.__display_transaction_detail(trading_date, stock_price, short_transaction_number, long_transaction_number, short_profit, long_profit)

        except Exception as e:
            print(e)


    def output_transaction_list(self):
        """
        メモリに溜まっている取引のデータをcsvファイルに書き出す。書き出したらメモリをクリアする。
        Args:
            None
        Returns:
            None
        """

        if len(self.transactions_list) == 0:
            return

        with open(self.transactions_csv, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(self.transactions_list)
        # f.close()

        self.transactions_list = []
        return

    # 1取引を行った後のトレード詳細情報を表示する
    def __display_transaction_detail(self, trading_date, stock_price, short_transaction_number, long_transaction_number, short_profit, long_profit):

        # 平均単価が0の場合は0で出力する
        avg_short_price = 0 if self.short_trading.number_now == 0 else self.short_trading.total_amount_now / self.short_trading.number_now
        avg_long_price = 0 if self.long_trading.number_now == 0 else self.long_trading.total_amount_now / self.long_trading.number_now

        print('取引日付：' + trading_date.strftime('%Y-%m-%d'))
        print('株価(終値)：' + f'{stock_price:,.1f}')
        print('---------------------')
        print('平均売り単価：' + f'{avg_short_price:,.1f}')
        print('空売り株数：' + str(short_transaction_number))
        print('空売り中の総株数：' + str(self.short_trading.number_now))
        print('損益(ショート)：' + f'{short_profit:,.2f}')
        print('---------------------')
        print('平均取得単価：' + f'{avg_long_price:,.1f}')
        print('買い株数：' + str(long_transaction_number))
        print('保有株数：' + str(self.long_trading.number_now))
        print('損益(ロング)：' + f'{long_profit:,.2f}')
        print('---------------------')
        print('総資産：' + f'{self.assets:,.2f}')