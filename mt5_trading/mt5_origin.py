
"""
To-do
1. calculate lot size
lot_size = (risk_ratio * capital) / (stop_loss * pip_value + commision_per_lot + spread)
!!!
!!!
This is wrong. Spread should not be in the (), should be spread/10*pip_value

formula
lot * stop_loss * pip_value + lot * commision_per_lot + lot * spread/10*pip_value = capital_in_risk
lot * (stop_loss * pip_value + commision_per_lot + spread/10*pip_value) = capital_in_risk
lot = capital_in_risk / (stop_loss * pip_value + commision_per_lot + spread/10*pip_value)

2. calculate spread in SL and TP

3. We can directly use the tick's lower price as our SL. No need to calc the SL and then convert and add to the current price.
4. Check that the previous two ticks formed the Dow's lower price. Only we meet this requirement, we open orders. So we might need to:
 1) compare 5-6 ticks, make sure the previous two's low are the lowest
 2) 

question:
waht's the Change in MT5, say 0.3%

"""

from http import server
from multiprocessing.resource_sharer import stop
import time
import MetaTrader5 as mt5
import credential_info

# import the 'pandas' module for displaying data obtained in the tabular form
import pandas as pd
pd.set_option('display.max_columns', 500) # number of columns to be displayed
pd.set_option('display.width', 1500)      # max table width to display

path = r"E:\Program Files\MetaTrader 5\terminal64.exe"

account_live = 10557130
password_live = credential_info.password
server_live = "ForexTimeFXTM-Live01"

# account_demo = 160255142
account_demo = 50919338
password_demo = credential_info.password_ICDemo
# server_demo = 'ForexTimeFXTM-Demo01'
server_demo = 'ICMarketsSC-Demo'

account = account_demo
server = server_demo
password = password_demo


def initialize(path):
    if not mt5.initialize(path):
        print("initialize() failed, error code =",mt5.last_error())
        quit()

    # if not mt5.initialize(login=account, server=server_live, password=password):
    #     print("initialize() failed, error code =",mt5.last_error())
    #     quit()

    # # display data on connection status, server name and trading account
    # print(mt5.terminal_info())
    # # display data on MetaTrader 5 version
    # print(mt5.version())


def login():
    authorized = mt5.login(account, password, server)

    if authorized:
        # display trading account data 'as is'
        print(mt5.account_info())
        # # display trading account data in the form of a list
        # print("Show account_info()._asdict():")
        # account_info_dict = mt5.account_info()._asdict()
        # for prop in account_info_dict:
        #     print("  {}={}".format(prop, account_info_dict[prop]))
    else:
        print("failed to connect at account #{}, error code: {}".format(account, mt5.last_error()))


# this seems optional
def prepare_request_structure(symbol = "USDJPY"):
    # prepare the buy request structure   
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(symbol, "not found, can not call order_check()")
        mt5.shutdown()
        quit()

    # if the symbol is unavailable in MarketWatch, add it
    if not symbol_info.visible:
        print(symbol, "is not visible, trying to switch on")
        if not mt5.symbol_select(symbol,True):
            print("symbol_select({}}) failed, exit",symbol)
            mt5.shutdown()
            quit()


# get the latest n ticks. n is 3 by default 
def get_last_n_ticks(symbol="USDJPY", timeframe=mt5.TIMEFRAME_M15, start_position=0, tick_count=3):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, start_position, tick_count)
    # print(rates) # print as is

    # # create DataFrame out of the obtained data
    # rates_frame = pd.DataFrame(rates)
    # # convert time in seconds into the datetime format
    # rates_frame['time']=pd.to_datetime(rates_frame['time'], unit='s')
    
    # # display data
    # print("\nDisplay dataframe with data")
    # print(rates_frame) 

    return rates 


def check_open_positions():
    # check the presence of open positions
    positions_total=mt5.positions_total()
    # if positions_total>0:
    #     print("Total positions=",positions_total)
    # else:
    #     print("Positions not found")
    return positions_total


def calculate_lot_size(sl, symbol, risk_ratio=0.05, commision_per_lot=0): #sl is in points, need to convert
    # pip_value = 1/10**(digits-1)*contract_size?
    # EURUSD 1/(10**(5-1)) * 100000 => 10 USD
    # USDJPY 1/(10**(3-1)) * 100000 => 1000 JPY
    # BTCUSD 1/(10**(2-1)) * 1 => 0.1 USD

    spread = mt5.symbol_info(symbol).spread

    #convert 
    stop_loss = sl/10
    print(f"sl pip: {stop_loss}")

    trade_contract_size = mt5.symbol_info(symbol).trade_contract_size
    digits = mt5.symbol_info(symbol).digits
    pip_value = 1/10**(digits-1)*trade_contract_size
    print(f"pip_value: {pip_value}")

    capital = mt5.account_info().balance
    capital_in_risk = risk_ratio * capital

    print(f"capital: {capital}, risk capital: {capital_in_risk}")

    # commission is of two operations, open and close. So it's 2 times of what mt5 specification shows (which is only for opening or closing, not opening and closing)
    # stop_loss is in pips, not points
    # lot_size = (risk_ratio * capital) / (stop_loss * pip_value + commision_per_lot + spread)
    # lot_size = capital_in_risk / (stop_loss * pip_value + commision_per_lot)
    lot_size = capital_in_risk / (stop_loss * pip_value + commision_per_lot + spread/10*pip_value)
    lot_size = round(lot_size, 2)

    if lot_size < 0.01:
        lot_size = 0.01
    
    # or maybe quit
    # if lot_size < 0.01:
    #     print("Insufficient funds. Cannot make 0.01 lots.")
    #     mt5.shutdown()
    #     quit()

    return lot_size


def open_request(sl_price, type="buy", sl="100", symbol="USDJPY", type_filling=mt5.ORDER_FILLING_FOK):
    
    # lot = 0.1
    lot = calculate_lot_size(sl, symbol)

    point = mt5.symbol_info(symbol).point    #EURUSD point: 1e-05   #BTCUSD point: 0.01 
    price = mt5.symbol_info_tick(symbol).ask
    deviation = 20


    if type == "buy":
        type = mt5.ORDER_TYPE_BUY
    elif type == "sell":
        type = mt5.ORDER_TYPE_SELL
        # if sell, sl shoult be price -  100* (-point)
        point = -point
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": type,
        "price": price,
        #"sl": price - sl * point, # "sl": price - 100 * point,  EURUSD 100 * 0.00001 => 0.001   1.02380-0.001 => 1.02280 => 10 pips
        # try to directly use the price of the previous tick low
        "sl": sl_price,
        "tp": price + sl * point,
        "deviation": deviation,
        "magic": 234000,
        "comment": "python script open",
        "type_time": mt5.ORDER_TIME_GTC,
        # "type_filling": mt5.ORDER_FILLING_RETURN,
        # "type_filling": mt5.ORDER_FILLING_FOK, # works for fxtm
        # "type_filling": mt5.ORDER_FILLING_IOC, # works for ic markect btc
        "type_filling": type_filling,

    }
    
    # send a trading request
    result = mt5.order_send(request)
    # check the execution result
    print("1. order_send(): by {} {} lots at {} with deviation={} points".format(symbol,lot,price,deviation));
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("2. order_send failed, retcode={}".format(result.retcode))
        print(mt5.ORDER_FILLING_RETURN)
        # request the result as a dictionary and display it element by element
        result_dict=result._asdict()
        for field in result_dict.keys():
            print("   {}={}".format(field,result_dict[field]))
            # if this is a trading request structure, display it element by element as well
            if field=="request":
                traderequest_dict=result_dict[field]._asdict()
                for tradereq_filed in traderequest_dict:
                    print("       traderequest: {}={}".format(tradereq_filed,traderequest_dict[tradereq_filed]))
        # print("shutdown() and quit")
        # mt5.shutdown()
        # quit()
        print("\nError\n")
    else:
        print("2. order_send done, ", result)
        print("   opened position with POSITION_TICKET={}".format(result.order))


"""
def close_request():
    # create a close request
    position_id=result.order
    price=mt5.symbol_info_tick(symbol).bid
    deviation=20
    request={
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_SELL,
        "position": position_id,
        "price": price,
        "deviation": deviation,
        "magic": 234000,
        "comment": "python script close",
        "type_time": mt5.ORDER_TIME_GTC,
        # "type_filling": mt5.ORDER_FILLING_RETURN,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }
    # send a trading request
    result=mt5.order_send(request)
    # check the execution result
    print("3. close position #{}: sell {} {} lots at {} with deviation={} points".format(position_id,symbol,lot,price,deviation));
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("4. order_send failed, retcode={}".format(result.retcode))
        print("   result",result)
    else:
        print("4. position #{} closed, {}".format(position_id,result))
        # request the result as a dictionary and display it element by element
        result_dict=result._asdict()
        for field in result_dict.keys():
            print("   {}={}".format(field,result_dict[field]))
            # if this is a trading request structure, display it element by element as well
            if field=="request":
                traderequest_dict=result_dict[field]._asdict()
                for tradereq_filed in traderequest_dict:
                    print("       traderequest: {}={}".format(tradereq_filed,traderequest_dict[tradereq_filed]))
"""

def historical_orders():
    from datetime import datetime
    # get the number of orders in history
    from_date=datetime(2022,7,21)
    to_date=datetime.now()
    history_orders=mt5.history_orders_total(from_date, to_date)
    if history_orders>0:
        print("Total history orders=",history_orders)
    else:
        print("Orders not found in history")

def historical_deals():
    from datetime import datetime

    # get the number of deals in history
    from_date=datetime(2022,7,21)
    to_date=datetime.now()
    deals=mt5.history_deals_total(from_date, to_date)
    if deals>0:
        print("Total deals=",deals)
    else:
        print("Deals not found in history")

# return current sma price on the current tick
# input sma length
def calculate_current_sma(symbol="BTCUSD", sma_length=24, start_position=0):
    rates = get_last_n_ticks(symbol=symbol, timeframe=mt5.TIMEFRAME_M5, start_position=start_position, tick_count=sma_length)
    total = 0
    for rate in rates:
        total += rate['close']
    sma = total / sma_length
    return sma

# sma_list length determines how many ticks we examine to see if we're above or below sma
def if_above_or_below_sma(sma_list, symbol="BTCUSD", sma_length=24, start_position=0):
    sma_list_length = len(sma_list)
    # only get several rates, e.g., 5, not 24
    rates = get_last_n_ticks(symbol=symbol, timeframe=mt5.TIMEFRAME_M5, start_position=start_position, tick_count=sma_list_length)

    sma_list.reverse()
    print(f"reversed sma list: {sma_list}")
    
    above_sma = 0
    below_sma = 0
    rate_close_list = []
    for rate in rates:
        rate_close_list.append(rate['close'])
        
    print(f"rate close list: {rate_close_list}")

    i = 0
    while i < sma_list_length:
        print(rate_close_list[i])
        if rate_close_list[i] > sma_list[i]:
             above_sma += 1
        i += 1

    if above_sma == sma_list_length:
        above_sma = "above_sma"
        return above_sma

    i = 0
    while i < sma_list_length:
        if rate_close_list[i] < sma_list[i]:
             below_sma += 1
        i += 1

    if below_sma == sma_list_length:
        below_sma = "below_sma"
        return below_sma

    return "mixed"

def check_retrace_when_long(symbol="BTCUSD", start_position=0, tick_count=5): 
    # 0 1 2 3 4 compare low of 2 and 3 with low of 0 and 1
    # 4 is the latest
    retracement = False
    rates = get_last_n_ticks(symbol=symbol, timeframe=mt5.TIMEFRAME_M5, start_position=start_position, tick_count=tick_count)
    tick_0_low = rates[0]['low']
    tick_1_low = rates[1]['low']
    tick_2_low = rates[2]['low']
    tick_3_low = rates[3]['low']
    # tick_4_low = rates[4]['low']
    lower_price_tick_0_and_1 = compare_two_and_get_lower(tick_0_low, tick_1_low)
    lower_price_tick_2_and_3 = compare_two_and_get_lower(tick_2_low, tick_3_low)
    # if the below is positive, then we have a retracement, the low price of the previous two got lower than the price of the previous previous two
    if lower_price_tick_2_and_3 < lower_price_tick_0_and_1:
        retracement = True        
    return retracement

def check_retrace_when_short(symbol="BTCUSD", start_position=0, tick_count=5): 
    retracement = False
    rates = get_last_n_ticks(symbol=symbol, timeframe=mt5.TIMEFRAME_M5, start_position=start_position, tick_count=tick_count)
    tick_0_high = rates[0]['high']
    tick_1_high = rates[1]['high']
    tick_2_high = rates[2]['high']
    tick_3_high = rates[3]['high']
    higher_price_tick_0_and_1 = compare_two_and_get_higher(tick_0_high, tick_1_high)
    higher_price_tick_2_and_3 = compare_two_and_get_higher(tick_2_high, tick_3_high)
    if higher_price_tick_2_and_3 > higher_price_tick_0_and_1:
        retracement = True
    return retracement

def compare_two_and_get_higher(tick_one_high, tick_two_high):
    if tick_one_high > tick_two_high:
        higher_price = tick_one_high
    else:
        higher_price = tick_two_high
    return higher_price

def compare_two_and_get_lower(tick_one_low, tick_two_low):
    if tick_one_low < tick_two_low:
        lower_price = tick_one_low
    else:
        lower_price = tick_two_low
    return lower_price


def double_tick_strategy():
    """
    USDJPY
    [(1658511000, 136.061, 136.191, 135.883, 136.007, 3592, 0, 0)
    (1658511900, 136.007, 136.134, 135.826, 136.08 , 3955, 0, 0)
    (1658512800, 136.082, 136.089, 135.976, 136.022, 1175, 0, 0)]

    Display dataframe with data
                    time     open     high      low    close  tick_volume  spread  real_volume
    0 2022-07-22 17:15:00  135.813  136.091  135.564  136.061         4312       0            0
    1 2022-07-22 17:30:00  136.061  136.191  135.883  136.007         3592       0            0
    2 2022-07-22 17:45:00  136.007  136.134  135.826  136.095         3903       0            0
    
    
    BTCUSD
    time        open        high    low         close    tick_volume spread real_volume
    [(1660398900, 24485.59, 24526.34, 24485.59, 24513.32, 367, 632, 0)
    (1660399200, 24512.36, 24517.21, 24490.33, 24496.34, 358, 632, 0)
    (1660399500, 24496.82, 24500.09, 24494.09, 24494.09,  10, 632, 0)]
    """

    symbol="BTCUSD"
    type_filling = mt5.ORDER_FILLING_IOC

    while True:
        
        open_positions = check_open_positions()
        if open_positions == 0:
            # rates <class 'numpy.ndarray'>
            rates = get_last_n_ticks(symbol=symbol, timeframe=mt5.TIMEFRAME_M5, tick_count=3)
            # print(rates)
            current_price = rates[2][4]
            
            # get the higher price of the previous one and two ticks
            tick_one_high = rates[0][2]
            tick_two_high = rates[1][2]
            higher_price = compare_two_and_get_higher(tick_one_high, tick_two_high)

            # get the lower price of the previous one and two ticks
            tick_one_low = rates[0][3]
            tick_two_low = rates[1][3]
            lower_price = compare_two_and_get_lower(tick_one_low, tick_two_low)

            #sma = calculate_current_sma(symbol="BTCUSD", sma_length=24)

            # last 5 sma prices start_pos =0, 1, 2, 3, 4
            sma_count = 5
            sma_list = []
            for start_position in range(0, sma_count): # sma from latest to earlier
                this_sma = calculate_current_sma(symbol="BTCUSD", sma_length=24, start_position=start_position)
                sma_list.append(this_sma)
            
            above_or_below_sma = if_above_or_below_sma(sma_list, symbol="BTCUSD", sma_length=24, start_position=0)
            print(f"above or under sma: {above_or_below_sma}")
            
            # if current_price > higher_price, and we are above the 24sma, and there's a retracement
            if current_price > higher_price and above_or_below_sma == "above_sma" and check_retrace_when_long: 
                print("buy")
                # sl = current_price * 1000 - rates[1][3] * 1000  # USDJPY
                sl = current_price * 100 - rates[1][3] * 100  # BTC
                open_request(sl_price=lower_price, type="buy", sl=sl, symbol=symbol, type_filling=type_filling)
                # continue # if we opened an order, we go back to the beginning of the loop, we don't sleep
            elif current_price < lower_price and above_or_below_sma == "below_sma" and check_retrace_when_short: # if current_price < lower_price and we are below the 25sma
                print("sell")
                # second_tick_high-current_price
                # sl = rates[1][2] * 1000 - current_price * 1000  # USDJPY
                sl = rates[1][2] * 100 - current_price * 100  # BTC
                open_request(sl_price=higher_price, type="sell", sl=sl, symbol=symbol, type_filling=type_filling)
                # continue
        # time.sleep(0.1)
        time.sleep(0.5)


    # rates = get_last_three_ticks()
    # current_price = rates[2][4]

    # if not check_open_positions():


    #     sl = current_price * 1000 - rates[1][3] * 1000
    #     print(f"{sl}**********************************")
    #     open_request("buy", sl)

    #     # sl = rates[1][2] * 1000 - current_price * 1000
    #     # open_request("sell", sl)

def check_symbol_info(symbol):
    # symbol = "EURJPY"
    # display EURJPY symbol properties
    symbol_info=mt5.symbol_info(symbol)
    if symbol_info:
        # # display the terminal data 'as is'    
        # print(symbol_info)
        # print("EURJPY: spread =",symbol_info.spread,"  digits =",symbol_info.digits)
        print(f"{symbol}: spread = {symbol_info.spread}, digits = {symbol_info.digits}")
        
        # display symbol properties as a list
        # print("Show symbol_info(\"EURJPY\")._asdict():")
        # symbol_info_dict = mt5.symbol_info("EURJPY")._asdict()
        # for prop in symbol_info_dict:
        #     print("  {}={}".format(prop, symbol_info_dict[prop]))

        return symbol_info


def main():
    initialize(path)
    login()

    # historical_orders()
    # historical_deals()

    double_tick_strategy()
    # symbol="XAUUSD"
    # point = mt5.symbol_info(symbol).point
    # print(point)

    # shut down connection to the MetaTrader 5 terminal
    #### mt5.shutdown() # code unreachable

if __name__ == "__main__":
    main()
