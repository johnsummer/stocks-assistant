# ショート（空売り）売買操作のクラス
class ShortTrading:

    # 空売りによる手持ちの総金額
    total_amount_now:float

    # 空売りの総株数
    number_now:int

    def __init__(self) -> None:
        self.total_amount_now = 0
        self.number_now = 0
        pass

    def short_sell(self, selling_number, stock_price):
        """
        株を空売りする
        Args:
            selling_number (int): 今回空売り株数
            stock_price (float): 空売り時の株価
        Returns:
            float: 今回の引き取りの後、空売りによる手持ちの総金額
            int:  今回の引き取りの後、空売りした総株数
        """
        # 空売り株数が0の場合、実際何も行われない
        if selling_number == 0:
            return (0.0, 0)

        self.total_amount_now = self.total_amount_now + selling_number * stock_price
        self.number_now = self.number_now + selling_number

        return (self.total_amount_now, self.number_now)

    def short_cover(self, short_covering_number, stock_price):
        """
        空売りした株を買い戻す
        Args:
            short_covering_number (int): 今回買い戻す株数
            stock_price (float): 買い戻す時の株価
        Returns:
            float: 今回買い戻した後、空売りによる手持ちの総金額
            int: 今回買い戻した後、空売りした総株数
            float: 損益
        """

        if short_covering_number > self.number_now:
            return (0.0, 0, 0.0)

        if short_covering_number == 0:
            return (0.0, 0, 0.0)

        profit = (self.total_amount_now / self.number_now - stock_price) * short_covering_number
        self.total_amount_now = self.total_amount_now - short_covering_number * self.total_amount_now / self.number_now
        self.number_now = self.number_now - short_covering_number

        return (self.total_amount_now, self.number_now, profit)