from training import LongTrading

if __name__ == "__main__":
    lt = LongTrading.LongTrading()
    #result = lt.buy(total_amount_now=300000.0, number_now=2000, buying_number=1000, stock_price=1600.0)
    lt.buy(1000, 1600.0)
    print("amount: " + str(lt.total_amount_now))
    print("number: " + str(lt.number_now))

    lt.buy(500, 1620)
    print("amount: " + str(lt.total_amount_now))
    print("number: " + str(lt.number_now))
