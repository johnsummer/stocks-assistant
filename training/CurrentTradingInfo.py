from datetime import date

import ShortTrading as st
import LongTrading as lt

# トレードにおける最新取引の情報モデル
class CurrentTradingInfoModel:

    trading_date:date               # 最新取引の日付
    stock_price:float               # 最新取引の株価(デフォルトは終値)

    short_lot:int
    short_transaction_number:int    # 最新取引における空売りの株数。マイナスの場合は買い戻しの株数
    short_profit:float              # 最新取引におけるショートトレードの損益
    short_trading:st.ShortTrading   # ショートトレードのポジション情報（空売り中の総額、株数）

    long_lot:int
    long_transaction_number:int     # 最新取引における買いの株数。マイナスの場合は売りの株数
    long_profit:float               # 最新取引におけるロングトレードの損益
    long_trading:lt.LongTrading     # ロングトレードのポジション情報（保有株の総額、株数）

    assets:float                    # 総資産

    def __init__(self) -> None:
        self.short_trading = st.ShortTrading()
        self.short_profit = 0
        self.long_trading = lt.LongTrading()
        self.long_profit = 0
        self.assets = 0