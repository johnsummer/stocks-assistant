from training import LongTrading
from training import ShortTrading
from training.integration import OrdersToTradingView

def long_trading_test():

    print("long_trading_test")

    lt = LongTrading.LongTrading()
    lt.buy(1000, 1600)
    print("amount: " + str(lt.total_amount_now))
    print("number: " + str(lt.number_now))

    lt.buy(500, 2000)
    print("amount: " + str(lt.total_amount_now))
    print("number: " + str(lt.number_now))

    result = lt.sell(500, 2000)
    print("amount: " + str(lt.total_amount_now))
    print("number: " + str(lt.number_now))
    print("profit: " + str(result[2]))
    print("avg_price: " + str(lt.total_amount_now / lt.number_now))

    result = lt.sell(1000, 1600)
    print("amount: " + str(lt.total_amount_now))
    print("number: " + str(lt.number_now))
    print("profit: " + str(result[2]))
    # print("avg_price: " + str(lt.total_amount_now / lt.number_now))

    print("*************")

    lt = LongTrading.LongTrading()
    lt.buy(1000, 1600)
    print("amount: " + str(lt.total_amount_now))
    print("number: " + str(lt.number_now))

    lt.buy(1000, 2000)
    print("amount: " + str(lt.total_amount_now))
    print("number: " + str(lt.number_now))

    result = lt.sell(500, 2500)
    print("amount: " + str(lt.total_amount_now))
    print("number: " + str(lt.number_now))
    print("profit: " + str(result[2]))
    print("avg_price: " + str(lt.total_amount_now / lt.number_now))

    lt.buy(1000, 2000)
    print("amount: " + str(lt.total_amount_now))
    print("number: " + str(lt.number_now))

    result = lt.sell(2500, 2000)
    print("amount: " + str(lt.total_amount_now))
    print("number: " + str(lt.number_now))
    print("profit: " + str(result[2]))

    print("*************")

    lt = LongTrading.LongTrading()
    lt.buy(1000, 1600)
    print("amount: " + str(lt.total_amount_now))
    print("number: " + str(lt.number_now))

    result = lt.sell(2000, 2500)
    print("amount: " + str(lt.total_amount_now))
    print("number: " + str(lt.number_now))
    print("profit: " + str(result[2]))

def short_trading_test():

    print("short_trading_test")

    st = ShortTrading.ShortTrading()
    st.short_sell(1000, 2000)
    print("amount: " + str(st.total_amount_now))
    print("number: " + str(st.number_now))

    st.short_sell(500, 1500)
    print("amount: " + str(st.total_amount_now))
    print("number: " + str(st.number_now))

    result = st.short_cover(500, 1500)
    print("amount: " + str(st.total_amount_now))
    print("number: " + str(st.number_now))
    print("profit: " + str(result[2]))

    result = st.short_cover(1000, 2000)
    print("amount: " + str(st.total_amount_now))
    print("number: " + str(st.number_now))
    print("profit: " + str(result[2]))

    print("*************")

    st = ShortTrading.ShortTrading()
    st.short_sell(1000, 2000)
    print("amount: " + str(st.total_amount_now))
    print("number: " + str(st.number_now))

    st.short_sell(1000, 1000)
    print("amount: " + str(st.total_amount_now))
    print("number: " + str(st.number_now))

    result = st.short_cover(1000, 1500)
    print("amount: " + str(st.total_amount_now))
    print("number: " + str(st.number_now))
    print("profit: " + str(result[2]))

    st.short_sell(1000, 1500)
    print("amount: " + str(st.total_amount_now))
    print("number: " + str(st.number_now))

    result = st.short_cover(2000, 1000)
    print("amount: " + str(st.total_amount_now))
    print("number: " + str(st.number_now))
    print("profit: " + str(result[2]))

    print("*************")

    st = ShortTrading.ShortTrading()
    st.short_sell(1000, 2000)
    print("amount: " + str(st.total_amount_now))
    print("number: " + str(st.number_now))

    result = st.short_cover(2000, 1500)
    print("amount: " + str(st.total_amount_now))
    print("number: " + str(st.number_now))
    print("profit: " + str(result[2]))

def test_order_to_trv():
    file_name = 'output\\trading_history_changeable_20130101_20241102231112_close.csv'
    銘柄コード = '2267.T'  # 例：'1234'
    開始日 = '20240101'
    終了日 = '20241231'
    建玉操作の文字列 = OrdersToTradingView.extract_trading_history(file_name, 銘柄コード, 開始日, 終了日)
    print(f'建玉操作の文字列: "{建玉操作の文字列}"')

if __name__ == "__main__":
    # long_trading_test()
    # short_trading_test()
    test_order_to_trv()
