import CurrentTradingInfo as cti

# 空売り・買い注文の総額が総資産を超過しているかをチェックするクラス
class AmountChecker:

    # チェック結果
    CHECK_RESULT_OK = 0
    CHECK_RESULT_SHORT_AMOUNT_OVER = 1
    CHECK_RESULT_LONG_AMOUNT_OVER = 2
    CHECK_RESULT_BOTH_AMOUNT_OVER = 3
    CHECK_RESULT_MARGIN_TRADING_LIMIT_OVER = 4

    def __init__(self) -> None:
        """
        空売り・買い注文の総額が総資産を超過しているかのチェッカーを初期化する
        Args:
            None
        Returns:
            None
        """
        pass

    def check_amount(self, current_trading_info:cti.CurrentTradingInfoModel, short_transaction_amount:float = 0, long_transaction_amount:float = 0):
        """
        仮に現在の注文が成立した場合、空売り・買い注文の総額が総資産を超過しているかをチェックする
        Args:
            current_trading_info(CurrentTradingInfo.CurrentTradingInfoModel) : 現時点のトレード状態(総資産、空売り総額、買い総額など)を保存しているオブジェクト
            short_transaction_amount(float) : 空売り注文しようとする金額
            long_transaction_amount(float) : 買い注文しようとする金額
        Returns:
            int:
                AmountChecker.CHECK_RESULT_OK(0) : 超過していない
                AmountChecker.CHECK_RESULT_SHORT_AMOUNT_OVER(1) : 売り注文総額が超過している
                AmountChecker.CHECK_RESULT_LONG_AMOUNT_OVER(2) : 買い注文総額が超過している
                AmountChecker.CHECK_RESULT_BOTH_AMOUNT_OVER(3) : 売り・買い注文とも超過している
                AmountChecker.CHECK_RESULT_MARGIN_TRADING_LIMIT_OVER(4) : 信用取引の限度(総資産の3.3倍)を超過している
        """

        # 仮に現在の注文が成立した場合の空売り・買い注文総額を計算する
        short_amount = current_trading_info.short_trading.total_amount_now + short_transaction_amount
        long_amount = current_trading_info.long_trading.total_amount_now + long_transaction_amount
        assets = current_trading_info.assets

        # 注文総額と総資産を比較する
        if short_amount + long_amount >= assets * 3.3:
            return self.CHECK_RESULT_MARGIN_TRADING_LIMIT_OVER

        if short_amount > assets:
            if long_amount > assets:
                return self.CHECK_RESULT_BOTH_AMOUNT_OVER
            else:
                return self.CHECK_RESULT_SHORT_AMOUNT_OVER

        if long_amount > assets:
            return self.CHECK_RESULT_LONG_AMOUNT_OVER

        return self.CHECK_RESULT_OK
        
