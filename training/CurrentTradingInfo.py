from datetime import date

import ShortTrading as st
import LongTrading as lt

# トレードにおける最新取引の情報モデル　TODO：最新ではなく、１取引の情報を保存するモデルにリネームする
class CurrentTradingInfoModel:

    trading_date:date               # 最新取引の日付
    stock_price:float               # 最新取引の株価(デフォルトは終値)

    short_lot:int                   # 売りロット数
    short_order_number:int          # 最新取引における売りの株数。マイナスの場合は買い戻しの株数
    short_profit:float              # 最新取引におけるショートトレードの損益
    short_trading:st.ShortTrading   # 売りのポジション情報（売り保有の総額、株数）

    long_lot:int                    # 買いロット数
    long_order_number:int           # 最新取引における買いの株数。マイナスの場合は手仕舞う株数
    long_profit:float               # 最新取引におけるロングトレードの損益
    long_trading:lt.LongTrading     # 買いのポジション情報（買い保有の総額、株数）

    lot_size:int                  # ロットサイズ

    stock_code:str                  # 銘柄コード

    assets:float                    # 総資産

    def __init__(self, lot_size:int=100) -> None:
        self.short_lot = 0
        self.short_trading = st.ShortTrading()
        self.short_profit = 0
        self.long_lot = 0
        self.long_trading = lt.LongTrading()
        self.long_profit = 0
        self.lot_size = lot_size
        self.assets = 0