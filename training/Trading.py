import csv
from datetime import timedelta
from datetime import date
from datetime import datetime
from typing import Tuple
from pathlib import Path
import os
import traceback
import pandas as pd

import CurrentTradingInfo as cti
import AmountChecker as amchkr
import StockInfo as si
import ShortTrading as st
import LongTrading as lt

class Trading:
    
    # 株銘柄の情報
    stock_info:si.StockInfo

    # transactions_csv = None
    trading_history_csv:Path = None

    # 最新取引の情報
    current_trading_info:cti.CurrentTradingInfoModel

    # TO DELETE
    # 直近のトレード履歴(最新30件)を保存するリスト。誤入力の際にトレードの状態を戻すために使う
    # __trading_info_history:collections.deque

    # トレード履歴表示の最大件数
    __MAX_LENGTH_OF_HISTORY = 20

    # 総資産超過チェックを通らないときの処理モード
    action_mode:int

    ACTION_MODE_FORBIDDEN = 1
    ACTION_MODE_WARNING = 2

    amount_checker:amchkr.AmountChecker

    ORDER_TIME_CLOSE = 0
    ORDER_TIME_NEXT_OPEN = 1

    # トレードモード
    trading_mode:str
    
    TRADING_MODE_SINGLE:str = 'single'
    TRADING_MODE_CHANGEABLE:str = 'changeable'

    # トレード練習関連のフィールド

    # 練習を始めた日時
    training_start_datetime:str

    # 今回の練習対象となるトレードの開始日
    trading_start_date:str

    # 最小取引単位
    min_trading_unit:int = 100

    def __init__(self, stock_info:si.StockInfo, training_start_datetime:str, assets:float=0.0, identifier:str='', trading_start_date:str='20130101', trading_mode:str='single') -> None:
        """
        トレードを開始する
        Args:
            stock_info (StockInfo): トレード対象銘柄の情報
            training_start_datetime (str): 練習を始めた日時
            assets (float, optional): トレード開始時の資産額. Defaults to 0.0.
            identifier (str, optional): 同銘柄、同期間のトレードを行った際に、csvファイルに対して区別を付けたい時の識別子. Defaults to ''.
            trading_start_date (str, optional): 今回の練習期間の開始日. Defaults to '20130101'.
            trading_mode (str, optional): トレードモード. Defaults to 'single'.
        Returns:
            None
        """
        self.stock_info = stock_info
        self.trading_mode = trading_mode

        self.training_start_datetime = training_start_datetime
        self.trading_start_date = trading_start_date

        code_in_file = ''
        if self.trading_mode == self.TRADING_MODE_CHANGEABLE:
            code_in_file = self.TRADING_MODE_CHANGEABLE
        else:
            code_in_file = self.stock_info.code

        # トレード履歴を保存するcsvファイルを初期化する
        dir_path = Path('output')
        self.trading_history_csv =  dir_path.joinpath('trading_history_' + code_in_file + '_' + self.trading_start_date \
            + '_' + training_start_datetime + '_' + identifier + '.csv')
        if not self.trading_history_csv.is_file():
            with self.trading_history_csv.open(mode='w', encoding='shift-jis', newline='') as f:
                header = ['銘柄コード', '取引日付', '株価', 'ロットサイズ', '売りロット数', '売り平均単価', '売り損益', '買いロット数', '買い平均単価', '買い損益', '総資産', 'メモ']
                writer = csv.writer(f)
                writer.writerow(header)

        self.current_trading_info = cti.CurrentTradingInfoModel()
        # TO DELETE
        # self.__trading_info_history = collections.deque()

        self.current_trading_info.assets = assets

        # 総資産超過チェッカーの初期化
        self.amount_checker = amchkr.AmountChecker()
        self.action_mode = self.ACTION_MODE_FORBIDDEN

    def one_order(self, trading_date:date, short_lot:int, long_lot:int, lot_size:int=100, order_time:int=0, 
                  stock_price:float=-1) -> Tuple[str, str]:
        """
        1回の取引を行う
        Args:
            trading_date (date): 取引の日付
            short_lot (int): 取引後に持っている空売りのロット数
            long_lot (int): 取引後に持っている買いのロット数
            lot_size (int): ロットサイズ
            order_time (int): 注文タイミング（大引け:0、翌日寄付:1）
            stock_price (float): 注文株価
        Returns:
            Tuple[str, str]: 'success'/'failure', 付属のメッセージ
        """

        RETURN_FAIL = 'failure'
        RETURN_SUCCESS = 'success'

        try:
            stock_data = None
            
            if order_time == self.ORDER_TIME_CLOSE:
                # 大引けでの注文
                stock_data = self.stock_info.stock_data_df[self.stock_info.stock_data_df.index == trading_date.strftime('%Y-%m-%d')]
                if len(stock_data) == 0:
                    return RETURN_FAIL, "入力された日付のデータはない。その日は祝日か、取得期間外の日付かもしれない。"
                
                if stock_price < 0:
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
                
                if stock_price < 0:
                    stock_price = float(stock_data['Open'])
            # print(stock_price)

            # ショート注文の準備
            short_lot_volumn = short_lot * lot_size
            short_order_number = short_lot_volumn - self.current_trading_info.short_trading.number_now
            short_profit = 0

            # ロング注文の準備
            long_lot_volumn = long_lot * lot_size
            long_order_number = long_lot_volumn - self.current_trading_info.long_trading.number_now
            long_profit = 0

            # 総資産超過のチェック
            short_order_amount = short_order_number * stock_price
            long_order_amount = long_order_number * stock_price
            check_result = self.amount_checker.check_amount(self.current_trading_info, short_order_amount, long_order_amount)

            amount_check_message = ''

            # チェックが通らない場合の処理
            if check_result != amchkr.AmountChecker.CHECK_RESULT_OK:
                amount_check_message = self.__asset_over_action(check_result, short_order_amount, long_order_amount)
                if check_result == amchkr.AmountChecker.CHECK_RESULT_MARGIN_TRADING_LIMIT_OVER or self.action_mode == self.ACTION_MODE_FORBIDDEN:
                    # 信用取引の限度を超えそうになった場合は何もしない
                    # print(amount_check_message)
                    return RETURN_FAIL, amount_check_message

            # ショート注文の実行
            if short_order_number > 0: 
                self.current_trading_info.short_trading.short_sell(short_order_number, stock_price)
            else:
                short_profit = self.current_trading_info.short_trading.short_cover(0 - short_order_number, stock_price)

            # ロング注文の実行
            if long_order_number > 0:
                self.current_trading_info.long_trading.buy(long_order_number, stock_price)
            else:
                long_profit = self.current_trading_info.long_trading.sell(0 - long_order_number, stock_price)

            # 本取引の情報を最新取引情報として保存する
            self.current_trading_info.trading_date = trading_date
            self.current_trading_info.stock_price = stock_price
            self.current_trading_info.short_lot = short_lot
            # self.current_trading_info.short_order_number = short_order_number # TO DELETE
            self.current_trading_info.long_lot = long_lot
            # self.current_trading_info.long_order_number = long_order_number # TO DELETE
            self.current_trading_info.short_profit = short_profit
            self.current_trading_info.long_profit = long_profit
            self.current_trading_info.lot_size = lot_size
            self.current_trading_info.stock_code = self.stock_info.code

            # 利益を総資産に加算
            self.current_trading_info.assets = self.current_trading_info.assets + short_profit + long_profit

            if short_order_number != 0 or long_order_number != 0:
                # この配下の処理は取引が発生している場合のみ行う

                # TO DELETE
                # トレードの状態を履歴として保存する(現在最新の取引を含め、最大31件)
                # if len(self.__trading_info_history) == self.__MAX_LENGTH_OF_HISTORY:
                #     self.__trading_info_history.popleft()

                # current_trading_info_tmp = copy.deepcopy(self.current_trading_info)
                # self.__trading_info_history.append(current_trading_info_tmp)

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

    def reset_trading_info(self, number: int) -> None:
        """
        トレードの状態をリセットする
        Args:
            number (int): 指定した番号の取引の状態に戻す。負数を指定された場合は新しい取引からその絶対値の個数で取り消す処理になる。
        Returns:
            None
        """
        try:
            df = pd.read_csv(self.trading_history_csv, encoding="shift-jis")
            if number < 0:
                # 負数を指定された場合でもそれ以降同じ処理を行わせるために、DataFrameにある該当の項番に変換する
                number = len(df) + number - 1

            if df.empty or number >= len(df) or number < 0:
                print("指定された番号の取引履歴が存在しません。")
                return
    
            # 該当の取引情報を取得する
            row = df.iloc[number]
            self.current_trading_info = cti.CurrentTradingInfoModel()
            self.current_trading_info.trading_date = datetime.strptime(row['取引日付'], '%Y-%m-%d').date()
            self.current_trading_info.stock_price = float(row['株価'])
            self.current_trading_info.short_lot = int(row['売りロット数'])
            self.current_trading_info.short_profit = float(row['売り損益'])
            self.current_trading_info.short_trading = st.ShortTrading()
            self.current_trading_info.short_trading.number_now = int(row['売りロット数']) * int(row['ロットサイズ'])
            self.current_trading_info.short_trading.total_amount_now = float(row['売り平均単価']) * self.current_trading_info.short_trading.number_now
            self.current_trading_info.long_lot = int(row['買いロット数'])
            self.current_trading_info.long_profit = float(row['買い損益'])
            self.current_trading_info.long_trading = lt.LongTrading()    
            self.current_trading_info.long_trading.number_now = int(row['買いロット数']) * int(row['ロットサイズ'])
            self.current_trading_info.long_trading.total_amount_now = float(row['買い平均単価']) * self.current_trading_info.long_trading.number_now
            self.current_trading_info.lot_size = int(row['ロットサイズ'])
            self.current_trading_info.stock_code = row['銘柄コード']
            self.current_trading_info.assets = float(row['総資産'])
    
            # csvファイルから不要な行を削除する
            df = df[:number + 1]
            df.to_csv(self.trading_history_csv, index=False, encoding="shift-jis")
    
        except Exception as e:
            print(f"CSVファイルの読み込みに失敗しました: {e}")

    def show_trading_history(self):
        """
        戻す可能な取引の一覧を表示する。
        Args:
            None
        Returns:
            None
        """
        print("※：番号が一番大きい項目は現在最新の状態です。")
    
        try:
            df = pd.read_csv(self.trading_history_csv, encoding="shift-jis")
            if df.empty:
                print("取引履歴がありません。")
                return
    
            rows_to_display = min(len(df), self.__MAX_LENGTH_OF_HISTORY)
            for i, row in df.tail(rows_to_display).iterrows():
                print(f"{i} : {row['銘柄コード']}  {row['取引日付']}  {row['売りロット数']}-{row['買いロット数']} (size: {row['ロットサイズ']})  ¥{row['総資産']:,.1f}")
        except Exception as e:
            print(f"CSVファイルの読み込みに失敗しました: {e}")

    def get_one_order_of_trading_history(self, number: int) -> cti.CurrentTradingInfoModel:
        """
        指定した番号に該当した取引の情報を取得する。番号についてはshow_trading_history_in_stack()で確認できる。
        Args:
            number (int): 取得したい取引の個数（例：2を指定した場合は2個前の取引の情報を取得する）
        Returns:
            cti.CurrentTradingInfoModel: 取引の情報
        """
        try:
            df = pd.read_csv(self.trading_history_csv, encoding="shift-jis")
            if df.empty or number >= len(df):
                print("指定された番号の取引履歴が存在しません。")
                return None
    
            row = df.iloc[number]
            trading_info = cti.CurrentTradingInfoModel()
            trading_info.trading_date = datetime.strptime(row['取引日付'], '%Y-%m-%d').date()
            trading_info.stock_price = float(row['株価'])
            trading_info.short_lot = int(row['売りロット数'])
            trading_info.short_profit = float(row['売り損益'])
            trading_info.short_trading = st.ShortTrading()
            trading_info.short_trading.number_now = int(row['売りロット数']) * int(row['ロットサイズ'])
            trading_info.short_trading.total_amount_now = float(row['売り平均単価']) * trading_info.short_trading.number_now
            trading_info.long_lot = int(row['買いロット数'])
            trading_info.long_profit = float(row['買い損益'])
            trading_info.long_trading = lt.LongTrading()    
            trading_info.long_trading.number_now = int(row['買いロット数']) * int(row['ロットサイズ'])
            trading_info.long_trading.total_amount_now = float(row['買い平均単価']) * trading_info.long_trading.number_now
            trading_info.lot_size = int(row['ロットサイズ'])
            trading_info.stock_code = row['銘柄コード']
            trading_info.assets = float(row['総資産'])
            return trading_info
        except Exception as e:
            print(f"CSVファイルの読み込みに失敗しました: {e}")
            return None

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

    # ロットのサイズを計算する関数
    # TODO：クラスメソッドとして用意するのは少し違和感があるが、一旦このまま
    @classmethod
    def calculate_lot_size(self, assets, num_of_stocks=20, stock_price=None):
        """ロットのサイズを計算する関数

        Args:
            assets (int): トレードで導入する資金
            num_of_stocks (int, optional): 想定総玉数. Defaults to 20.
            stock_price (int): 株価

        Returns:
            int: ロットのサイズ（100の桁まで切り捨てる）
            -1: 引数に誤りがある場合
        """

        # 引数のチェック
        if stock_price is None:
            # 株価が入力されていない場合はエラーメッセージを表示し、-1を返す
            print("株価を入力してください。")
            return -1
        if assets <= 0:
            # 資金が0以下の場合はエラーメッセージを表示し、-1を返す
            print("資金は正の値で入力してください。")
            return -1
        if num_of_stocks <= 0:
            # 玉数が0以下の場合はエラーメッセージを表示し、-1を返す
            print("玉数は正の値で入力してください。")
            return -1
        
        # ロットのサイズの計算
        max_amount = assets * 3.3 # トレードで注文できる最大金額
        lot_size = max_amount / (num_of_stocks * stock_price * 1.1) # ロットのサイズの計算式
        lot_size = int(lot_size // 100 * 100) # ロットのサイズを100の桁まで切り捨てる

        if lot_size < 100:
            # ロットのサイズが100未満の場合は100にするとともに、警告メッセージを表示する
            lot_size = 100
            print("注意：株価が高すぎて既定の規則で計算したロットのサイズは100株未満になってしまいましたので、一旦100株にしました。")
        
        return lot_size

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
            str(self.current_trading_info.lot_size),
            str(self.current_trading_info.short_lot),
            str(avg_short_price),
            str(self.current_trading_info.short_profit),
            str(self.current_trading_info.long_lot),
            str(avg_long_price),
            str(self.current_trading_info.long_profit),
            str(self.current_trading_info.assets)
        ]

        with self.trading_history_csv.open('a', encoding='shift-jis', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(trading_info)

    # 総資産超過のチェックが通らない時のメッセージを生成する
    def __asset_over_action(self, check_result:int, short_order_amount, long_order_amount):

        if check_result == amchkr.AmountChecker.CHECK_RESULT_OK:
            return None

        message:str
        message_assets_info = '現在の総資産：' + f'{self.current_trading_info.assets:,.1f}' + os.linesep \
            + 'これまでの注文総額：　空売り：' + f'{self.current_trading_info.short_trading.total_amount_now:,.1f}' \
            + ', 買い：' + f'{self.current_trading_info.long_trading.total_amount_now:,.1f}' + os.linesep \
            + '注文しようとする金額：　空売り：' + f'{short_order_amount:,.1f}' \
            + ', 買い：' + f'{long_order_amount:,.1f}'

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