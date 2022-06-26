from training import LongTrading

if __name__ == "__main__":
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

    print("---------")

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