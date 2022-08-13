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
        ロングで株を買う
        Args:
            buying_number (int): 今回買う株数
            stock_price (float): 買う時の株価
        Returns:
            None
        """

        # 買う株数が0の場合、実際何も行われない
        if buying_number == 0:
            return

        self.total_amount_now = self.total_amount_now + buying_number * stock_price
        self.number_now = self.number_now + buying_number

        return

    def sell(self, selling_number, stock_price):
        """
        ロングで株を売る
        Args:
            selling_number (int): 今回売る株数
            stock_price (float): 売る時の株価
        Returns:
            float: 損益
        """

        if selling_number > self.number_now:
            return 0.0

        if selling_number == 0:
            return 0.0

        profit = (stock_price - self.total_amount_now / self.number_now) * selling_number
        self.total_amount_now = self.total_amount_now - selling_number * self.total_amount_now / self.number_now
        self.number_now = self.number_now - selling_number

        return profit