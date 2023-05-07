import csv
from datetime import timedelta
from datetime import date
from typing import Tuple
import os
import collections
import copy
import traceback
import pandas as pd
import yfinance as yf

import CurrentTradingInfo as cti
import AmountChecker as amchkr
import StockInfo as si

class Trading:

    # TO DELETE
    # # 株価格のデータ
    # stock_data_df:pd.DataFrame = None

    # # 株銘柄の情報
    # stock_info = None
    # code:str
    # start_date:date
    # end_date:date
    stock_info:si.StockInfo

    # transactions_csv = None
    trading_history_csv = None

    # 最新取引の情報
    current_trading_info:cti.CurrentTradingInfoModel

    # 直近のトレード履歴(最新30件)を保存するリスト。誤入力の際にトレードの状態を戻すために使う
    __trading_info_history:collections.deque

    # トレード履歴の一時保存の最大件数(現在最新の状態＋30件前まで)
    __MAX_LENGTH_OF_HISTORY = 31

    # 総資産超過チェックを通らないときの処理モード
    action_mode:int

    ACTION_MODE_FORBIDDEN = 1
    ACTION_MODE_WARNING = 2

    amount_checker:amchkr.AmountChecker

    TRANSACTION_TIME_CLOSE = 0
    TRANSACTION_TIME_NEXT_OPEN = 1

    # トレードモード
    trading_mode:str
    
    TRADING_MODE_SINGLE:str = 'single'
    TRADING_MODE_CHANGEABLE:str = 'changeable'

    # トレード練習関連のフィールド

    # 練習を始めた日時
    training_start_datetime:str

    # 今回の練習対象となるトレードの開始日
    trading_start_date:str

    def __init__(self, stock_info:si.StockInfo, training_start_datetime:str, assets:float=0.0, identifier:str='', trading_start_date:str='20130101', trading_mode:str='single') -> None:
        """
        トレードを開始する
        Args:
            stock_info (StockInfo): トレード対象銘柄の情報
            assets (float): トレード開始時の資産額
            identifier (str): 同銘柄、同期間のトレードを行った際に、csvファイルに対して区別を付けたい時の識別子
        Returns:
            None
        """
        self.stock_info = stock_info
        self.trading_mode = trading_mode

        self.training_start_datetime = training_start_datetime
        self.trading_start_date = trading_start_date

        # 使わなさそうで、一旦以下の処理をコメントアウトする
        # 入力履歴を保存するcsvファイルを初期化する
        # self.transactions_csv =  'output/transaction_history_' + self.stock_info.code + '_' + self.stock_info.start_date.strftime('%Y%m%d') \
        #     + '_' + training_start_datetime + '_' + identifier + '.csv'
        # if not os.path.isfile(self.transactions_csv):
        #     with open(self.transactions_csv, 'w', newline='') as f:
        #         header = ['trading_date', 'short_lot', 'long_lot']
        #         writer = csv.writer(f)
        #         writer.writerow(header)

        code_in_file = ''
        if self.trading_mode == self.TRADING_MODE_CHANGEABLE:
            code_in_file = self.TRADING_MODE_CHANGEABLE
        else:
            code_in_file = self.stock_info.code

        # トレード履歴を保存するcsvファイルを初期化する
        self.trading_history_csv =  'output/trading_history_' + code_in_file + '_' + self.trading_start_date \
            + '_' + training_start_datetime + '_' + identifier + '.csv'
        if not os.path.isfile(self.trading_history_csv):
            with open(self.trading_history_csv, 'w', newline='') as f:
                header = ['銘柄コード', '取引日付', '株価', '買い株数', '保有株数', '平均取得単価', 'ロング損益', '空売り株数', '空売り中の株数', '平均売り単価', 'ショート損益', '総資産', 'メモ']
                writer = csv.writer(f)
                writer.writerow(header)

        self.current_trading_info = cti.CurrentTradingInfoModel()
        self.__trading_info_history = collections.deque()

        self.current_trading_info.assets = assets

        # 総資産超過チェッカーの初期化
        self.amount_checker = amchkr.AmountChecker()
        self.action_mode = self.ACTION_MODE_FORBIDDEN

    def one_transaction(self, trading_date:date, short_lot:int, long_lot:int, lot_volumn:int=100, transaction_time:int=0) -> Tuple[str, str]:
        """
        1回の取引を行う
        Args:
            trading_date (date): 取引の日付
            short_lot (int): 該当日に持っている空売りのロット数
            long_lot (int): 該当日に持っている買いのロット数
            lot_volumn (int): 1注文単位のロット数
            transaction_time (int): 注文タイミング（大引け:0、翌日寄付:1）
        Returns:
            Tuple[str, str]: 'success'/'failure', 付属のメッセージ
        """

        RETURN_FAIL = 'failure'
        RETURN_SUCCESS = 'success'

        try:
            stock_price = 0
            stock_data = None
            
            if transaction_time == self.TRANSACTION_TIME_CLOSE:
                # 大引けでの注文
                stock_data = self.stock_info.stock_data_df[self.stock_info.stock_data_df.index == trading_date.strftime('%Y-%m-%d')]
                if len(stock_data) == 0:
                    return RETURN_FAIL, "入力された日付のデータはない。その日は祝日か、取得期間外の日付かもしれない。"
                
                stock_price = float(stock_data['Close'])
            else:
                # 翌日寄付での注文
                trading_date = trading_date + timedelta(days=1)
                stock_data = self.stock_info.stock_data_df[self.stock_info.stock_data_df.index == trading_date.strftime('%Y-%m-%d')]

                # 翌日のデータがない場合、休日の可能性があるので、更にデータを取れるまで次の日のデータを取ってみる。
                # ただ、データの最後に来た可能性があるので、最大15日間で試す(15連休の可能性はない)
                i = 1
                while(len(stock_data) == 0 and i <= 15):
                    trading_date = trading_date + timedelta(days=1)
                    stock_data = self.stock_info.stock_data_df[self.stock_info.stock_data_df.index == trading_date.strftime('%Y-%m-%d')]
                    i = i + 1

                if len(stock_data) == 0:
                    return RETURN_FAIL, "入力された日付の翌営業日のデータはない。取得期間外の日付かもしれない。"
                
                stock_price = float(stock_data['Open'])
            # print(stock_price)

            # ショート注文の準備
            short_lot_volumn = short_lot * lot_volumn
            short_transaction_number = short_lot_volumn - self.current_trading_info.short_trading.number_now
            short_profit = 0

            # ロング注文の準備
            long_lot_volumn = long_lot * lot_volumn
            long_transaction_number = long_lot_volumn - self.current_trading_info.long_trading.number_now
            long_profit = 0

            # 総資産超過のチェック
            short_transaction_amount = short_transaction_number * stock_price
            long_transaction_amount = long_transaction_number * stock_price
            check_result = self.amount_checker.check_amount(self.current_trading_info, short_transaction_amount, long_transaction_amount)

            amount_check_message = ''

            # チェックが通らない場合の処理
            if check_result != amchkr.AmountChecker.CHECK_RESULT_OK:
                amount_check_message = self.__asset_over_action(check_result, short_transaction_amount, long_transaction_amount)
                if check_result == amchkr.AmountChecker.CHECK_RESULT_MARGIN_TRADING_LIMIT_OVER or self.action_mode == self.ACTION_MODE_FORBIDDEN:
                    # 信用取引の限度を超えそうになった場合は何もしない
                    # print(amount_check_message)
                    return RETURN_FAIL, amount_check_message

            # ショート注文の実行
            if short_transaction_number > 0: 
                self.current_trading_info.short_trading.short_sell(short_transaction_number, stock_price)
            else:
                short_profit = self.current_trading_info.short_trading.short_cover(0 - short_transaction_number, stock_price)

            # ロング注文の実行
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
            self.current_trading_info.lot_volumn = lot_volumn
            self.current_trading_info.stock_code = self.stock_info.code

            # 利益を総資産に加算
            self.current_trading_info.assets = self.current_trading_info.assets + short_profit + long_profit

            if short_transaction_number != 0 or long_transaction_number != 0:
                # この配下の処理は取引が発生している場合のみ行う

                # トレードの状態を履歴として保存する(現在最新の取引を含め、最大31件)
                if len(self.__trading_info_history) == self.__MAX_LENGTH_OF_HISTORY:
                    self.__trading_info_history.popleft()

                current_trading_info_tmp = copy.deepcopy(self.current_trading_info)
                self.__trading_info_history.append(current_trading_info_tmp)

                # # トレードの状態を履歴として保存する処理の動作確認
                # for current_trading_info_tmp in self.__trading_info_history:
                #     print(str(current_trading_info_tmp.trading_date) + ' : ' + str(current_trading_info_tmp.assets))

                # 取引記録のファイルを出力
                # self.__output_transaction_input_to_csv()
                self.__output_trading_info_to_csv()

            # 総資産超過の警告メッセージを渡して本取引後のトレード状態を表示する。超過していない場合は警告メッセージが空文字列になる
            # TO DELETE
            # self.__display_transaction_detail(amount_check_message)

            return RETURN_SUCCESS, amount_check_message
        except Exception as e:
            print(traceback.format_exc())

    def reset_trading_info(self, number:int):
        """
        指定した番号に該当したトレードの状態に戻す。番号についてはshow_trading_history_in_stack()で確認できる。
        Args:
            number (int): 戻したい取引の個数（例：2を指定した場合は2個前の取引の状態にトレードをリセットする）
        Returns:
            None
        """
        max = self.__MAX_LENGTH_OF_HISTORY if self.__MAX_LENGTH_OF_HISTORY < len(self.__trading_info_history) else len(self.__trading_info_history)
        max = max - 1   # 現在の最新状態を除いた後の最大の件数（戻す先の対象となる件数）

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

        # 使わなさそうで一旦コメントアウトする
        # df_transactions_csv = pd.read_csv(self.transactions_csv, encoding="shift-jis")
        # df_transactions_csv = df_transactions_csv[:-number]
        # df_transactions_csv.to_csv(self.transactions_csv, index=False, encoding="shift-jis")

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
            print(str(i) + ' : ' + current_trading_info_tmp.stock_code 
                + '  ' + current_trading_info_tmp.trading_date.strftime('%Y-%m-%d') 
                + '  ' + str(current_trading_info_tmp.short_lot) + '-' + str(current_trading_info_tmp.long_lot) 
                + '  (size: ' +  str(current_trading_info_tmp.lot_volumn) + ')'
                + '  ¥' + f'{current_trading_info_tmp.assets:,.1f}')
            i = i + 1

    def get_one_transaction_of_trading_history(self, number:int) -> cti.CurrentTradingInfoModel:
        """
        指定した番号に該当した取引の情報を取得する。番号についてはshow_trading_history_in_stack()で確認できる。
        Args:
            number (int): 取得したい取引の個数（例：2を指定した場合は2個前の取引の情報を取得する）
        Returns:
            None
        """
        trading_info = copy.deepcopy(self.__trading_info_history[-1-number])
        return trading_info

    def take_memo_by_date(self, memo_date:date, memo:str) -> int:
        """
        指定した日付のトレードに対していメモを記録する。
        Args:
            memo_date (date): 対象日付
            memo (str): メモ内容
        Returns:
            int: 書き込む対象となった行番号。-1->書き込みに失敗
        """
        df_trading_history_csv = pd.read_csv(self.trading_history_csv, encoding="shift-jis")
        
        # 該当行の番号を取得する
        row = df_trading_history_csv.query('取引日付 == "' + memo_date.strftime('%Y-%m-%d') + '"')

        if len(row) > 0:
            row_number = row.head(1).index.item()

            # メモを書き込む
            df_trading_history_csv.at[row_number, 'メモ'] = memo

            # csvに書き込む
            df_trading_history_csv.to_csv(self.trading_history_csv, index=False, encoding="shift-jis")

            return row_number
        else:
            return -1

    def take_memo_by_row_number(self, row_number:int, memo:str) -> str:
        """
        指定した日付のトレードに対していメモを記録する。
        Args:
            row_number (int): メモ記録対象の行番号。csv上の1行目の行番号は0になる。
            memo (str): メモ内容
        Returns:
            str: 書き込む対象となった行の取引日付(csvデータではインデックスとなる)。None->書き込みに失敗
        """
        df_trading_history_csv = pd.read_csv(self.trading_history_csv, encoding="shift-jis")

        df_row_count = len(df_trading_history_csv)

        if df_row_count > 0 and df_row_count > row_number:
            date_str = df_trading_history_csv.at[row_number, '取引日付']

            # メモを書き込む
            df_trading_history_csv.at[row_number, 'メモ'] = memo

            # csvに書き込む
            df_trading_history_csv.to_csv(self.trading_history_csv, index=False, encoding="shift-jis")

            return date_str
        else:
            return None

    # 使わなさそうで一旦コメントアウトする
    # 取引の入力情報をcsvファイルに書き出す
    # def __output_transaction_input_to_csv(self):

    #     transaction = [
    #         self.current_trading_info.trading_date.strftime('%Y-%m-%d'), 
    #         str(self.current_trading_info.short_lot), 
    #         str(self.current_trading_info.long_lot)
    #     ]

    #     with open(self.transactions_csv, 'a', newline='') as f:
    #         writer = csv.writer(f)
    #         writer.writerow(transaction)

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
            self.current_trading_info.stock_code,
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

    # TO DELETE
    # # 1取引を行った後のトレード詳細情報を表示する
    # def __display_transaction_detail(self, amount_check_message:str):

    #     # 平均単価が0の場合は0で出力する
    #     avg_short_price = 0
    #     if self.current_trading_info.short_trading.number_now != 0:
    #         avg_short_price = self.current_trading_info.short_trading.total_amount_now / self.current_trading_info.short_trading.number_now
    #     avg_long_price = 0
    #     if self.current_trading_info.long_trading.number_now != 0:
    #         avg_long_price = self.current_trading_info.long_trading.total_amount_now / self.current_trading_info.long_trading.number_now

    #     print('取引日付：' + self.current_trading_info.trading_date.strftime('%Y-%m-%d'))
    #     print('株価(終値)：' + f'{self.current_trading_info.stock_price:,.1f}')
    #     print('---------------------')
    #     print('売り注文株数：' + str(self.current_trading_info.short_transaction_number)
    #         + '\t\t売り総株数：' + str(self.current_trading_info.short_trading.number_now))
    #     print('平均売り単価：' + f'{avg_short_price:,.1f}'
    #         + '\t\t売り総額：' + f'{self.current_trading_info.short_trading.total_amount_now:,.1f}')
    #     print('損益(ショート)：' + f'{self.current_trading_info.short_profit:,.1f}')
    #     print('---------------------')
    #     print('買い注文株数：' + str(self.current_trading_info.long_transaction_number)
    #         + '\t\t保有株数：' + str(self.current_trading_info.long_trading.number_now))
    #     print('平均取得単価：' + f'{avg_long_price:,.1f}'
    #         + '\t\t保有総額：' + f'{self.current_trading_info.long_trading.total_amount_now:,.1f}')
    #     print('損益(ロング)：' + f'{self.current_trading_info.long_profit:,.1f}')
    #     print('---------------------')
    #     print('総資産：' + f'{self.current_trading_info.assets:,.1f}' + '\t' + amount_check_message)
    #     print('---------------------')

    # 総資産超過のチェックが通らない時のメッセージを生成する
    def __asset_over_action(self, check_result:int, short_transaction_amount, long_transaction_amount):

        if check_result == amchkr.AmountChecker.CHECK_RESULT_OK:
            return None

        message:str
        message_assets_info = '現在の総資産：' + f'{self.current_trading_info.assets:,.1f}' + os.linesep \
            + 'これまでの注文総額：　空売り：' + f'{self.current_trading_info.short_trading.total_amount_now:,.1f}' \
            + ', 買い：' + f'{self.current_trading_info.long_trading.total_amount_now:,.1f}' + os.linesep \
            + '注文しようとする金額：　空売り：' + f'{short_transaction_amount:,.1f}' \
            + ', 買い：' + f'{long_transaction_amount:,.1f}'

        if check_result == amchkr.AmountChecker.CHECK_RESULT_MARGIN_TRADING_LIMIT_OVER:
            message = '信用取引の限度(' + f'{self.current_trading_info.assets * 3.3:,.1f}' \
                + ')を超えますので、注文不可です。' + os.linesep + message_assets_info
        
        elif self.action_mode == self.ACTION_MODE_FORBIDDEN:
            if check_result == amchkr.AmountChecker.CHECK_RESULT_BOTH_AMOUNT_OVER:
                message = '空売り・買いの保有総額とも総資産を超えますので、注文不可です。'
            elif check_result == amchkr.AmountChecker.CHECK_RESULT_SHORT_AMOUNT_OVER:
                message = '空売りの保有総額が総資産を超えますので、売り注文は不可です。'
            elif check_result == amchkr.AmountChecker.CHECK_RESULT_LONG_AMOUNT_OVER:
                message = '買いの保有総額が総資産を超えますので、買い注文は不可です。'
            
            message = message + os.linesep + message_assets_info
        else:
            if check_result == amchkr.AmountChecker.CHECK_RESULT_BOTH_AMOUNT_OVER:
                message = '!!空売り・買いの保有総額とも総資産を超えます!!'
            elif check_result == amchkr.AmountChecker.CHECK_RESULT_SHORT_AMOUNT_OVER:
                message = '!!空売りの保有総額が総資産を超えます!!'
            elif check_result == amchkr.AmountChecker.CHECK_RESULT_LONG_AMOUNT_OVER:
                message = '!!買いの保有総額が総資産を超えます!!'

        return message