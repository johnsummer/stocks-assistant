# ロング売買操作のクラス
class LongTrading:

    # 現在持っている株の総額
    total_amount_now:float

    # 現在持っている株数
    number_now:int

    def __init__(self) -> None:
        self.total_amount_now = 0
        self.number_now = 0
        pass

    def buy(self, buying_number, stock_price):
        """
        ロングで株を購入する
        Args:
            buying_number (int): これから購入する株数
            stock_price (float): 購入株価
        Returns:
            float: 購入後の持っている株の総額
            int: 購入後の持っている株数
        """

        # 現在持っている株数と購入株数とも0の場合、実際何も行われない
        if buying_number == 0:
            return (0.0, 0)

        self.total_amount_now = self.total_amount_now + buying_number * stock_price
        self.number_now = self.number_now + buying_number

        return (self.total_amount_now, self.number_now)

    # ロングのイグジットをする
    def sell():
        return None