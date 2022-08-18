
"""
To-do
1. calculate lot size
lot_size = (risk_ratio * capital) / (stop_loss * pip_value + commision_per_lot + spread)    [X]
!!!
!!!
This is wrong. Spread should not be in the (), should be spread/10*pip_value

formula
lot * stop_loss * pip_value + lot * commision_per_lot + lot * spread/10*pip_value = capital_in_risk
lot * (stop_loss * pip_value + commision_per_lot + spread/10*pip_value) = capital_in_risk
lot = capital_in_risk / (stop_loss * pip_value + commision_per_lot + spread/10*pip_value)   [OK]

2. calculate spread in SL and TP

3. We can directly use the tick's lower price as our SL. No need to calc the SL and then convert and add to the current price.
4. Check that the previous two ticks formed the Dow's lower price. Only we meet this requirement, we open orders. So we might need to:
 1) compare 5-6 ticks, make sure the previous two's low are the lowest
 2) 


5. change the SL to the dow's lowest price, not the price of the previous tick
6. avoid consolidation (special rule 5)
 to do this, we need to  store at least four prices, should be a high, low, inner high, inner low 
 let's call them 0 1 2 3
 and we need to check 
 0 > 2
 1 < 3

7. move SL to break even or slight loss when the price is near TP, for USPJPY it should be 30-40 spreads.

8. log errors in log files
9. usdjpy lot size incorrect
10. detect if autotrading enabled and auto enable it. Possbile?


11. if successfully tp but still meet the requirements,
another ticket will be opened. This is usually not what we want.
(usually happens when the tick moves fast, when makes tp and open price on the same tick. So the requirements are still met.
So we need to add another limitation for opening orders.
Could try limit the distance between the current price and the ideal entry point. If the gap is larger than 20 points, 30 points,
then we don't open orders.

12. an additional new rule for opening an order. if cross sma (check open above, close below or equal), check if current price is higher than the previous two ticks and mean if pause or retrace.

13. the SL should be below the lowest of the previous two ticks and the current tick. Sometimes the current tick could have a lower price. This needs to be modified

14. need to check retrace func, not quite accurate

15. before implementing 11, 12 ,13, 14, create branches or new files. 
1) set buy and sell reverse. This could be profitable, especially in a consolidation, I guess. (note 8/17/2022 this didn't work after a three day test. Mon-Wed)
2) stay put buy and sell. Cancel the sma


16. avoid consolidation. if sl and tp is too small, consider it's not a good chance? I don't know if this is a good way.
e.g. sl < 50 points, then we don't trade

17. if sma doesn't change much, say, the price of five SMAs is not far from 20 points. 
This indicats we don't have a trend. So if we use sma and only buy when above, sell when below. it won't work


18. if lot size too large, leverage not enough, shows "comment=No Money" error
need to calc the maximum lot size to avoid that.

question:
waht's the Change in MT5, say 0.3%

19. if almost pause, which is to say, the price is just a bit pass the previous higher price by 1-5 points (point, not pip) We may consider it 
a valid condition.

20. retracement needs to check another situation. 
0 1 2 3 4
previously, we check 
1) 2 3's lower < 1 2's lower
2) 3 4's lower < 2 3's lower

but we have another situation:
3) 1 2's low < 0, 3 does't pass two previous ticks, but 4 passes

Actually, there's a better way to do the above. We get 6 ticks, just in case.
0 1 2 3 4 5
then we literate, pick from the third one, which is 2, call it current
if current's low < 0 and < 1:
    retracement = True

So if previous recent ticks have a retracement, then it's a retracement.

if it's tick 2 that retraced, it's a bit far a way, we need to verify if the current price has gone too high and far away from that tick 



sma above or below bug
when cross from above to below, it's still above.
It's more often above, because above if statement is checked first and returned first
Only when there's only 1 tick's close price > sma does the condition fail and the 'checking below sma' code have the chance to run

we have fixed this bug buy revising and creating a new func

Currently, the cross sma works fine. if we sell when cross up to down, and got SL'ed, which means the price goes above sma again, then we immediately buy when SL'ed. 

# to do:
a. need to check high low high low shrinking, in order to avoid consolidaiton

b. utilize sma-price position checker. 
if mixed & current price > sma, should long.
if mixed & current price < sma, should short
best to also check the consecutive ascending/descending ladders

"""


import time
import MetaTrader5 as mt5
import credential_info

# import the 'pandas' module for displaying data obtained in the tabular form
import pandas as pd
pd.set_option('display.max_columns', 500) # number of columns to be displayed
pd.set_option('display.width', 1500)      # max table width to display

path = r"E:\Program Files\MetaTrader 5\terminal64.exe"

# fxtm live
account_live = 10557130
password_live = credential_info.password
server_live = "ForexTimeFXTM-Live01"

# IC demo
# account_demo = 50919338
# password_demo = credential_info.password_ICDemo
# server_demo = 'ICMarketsSC-Demo'

# fxtm demo
account_demo = 160260280
password_demo = credential_info.password2
server_demo = 'ForexTimeFXTM-Demo01'

account = account_demo
password = password_demo
server_to_connect = server_demo



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
    authorized = mt5.login(account, password, server_to_connect)

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


def calculate_lot_size(sl, symbol, risk_ratio=0.05, commision_per_lot=4): #sl is in points, need to convert     # currently @param commision_per_lot is not included in the passed parameters
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
    # pip_value = 1/10**(digits-1)*trade_contract_size * 
    
    # hard code not the best way
    # tmp method
    if symbol == "USDJPY":
        pip_value = pip_value / mt5.symbol_info(symbol).ask
    
    print(f"pip_value: {pip_value}")

    capital = mt5.account_info().balance
    capital_in_risk = risk_ratio * capital

    print(f"capital: {capital}, risk capital: {capital_in_risk}")

    # commission is of two operations, open and close. So it's 2 times of what mt5 specification shows (which is only for opening or closing, not opening and closing)
    # stop_loss is in pips, not points
    # lot_size = (risk_ratio * capital) / (stop_loss * pip_value + commision_per_lot + spread)
    # lot_size = capital_in_risk / (stop_loss * pip_value + commision_per_lot)
    lot_size = capital_in_risk / (stop_loss * pip_value + commision_per_lot + spread/10*pip_value)


    print(f"lot size = {lot_size} before rounding")
    lot_size = round(lot_size, 2)
    print(f"lot size = {lot_size}, commision = {lot_size*commision_per_lot}, commision_per_lot = {commision_per_lot}")

    if lot_size < 0.01:
        print(f"lot size = {lot_size}. Change to 0.01")
        lot_size = 0.01
    
    # or maybe quit
    # if lot_size < 0.01:
    #     print("Insufficient funds. Cannot make 0.01 lots.")
    #     mt5.shutdown()
    #     quit()

    return lot_size


def open_request(sl_price, type="buy", sl="100", symbol="USDJPY", type_filling=mt5.ORDER_FILLING_FOK, commision_per_lot=4):
    
    # lot = 0.1
    lot = calculate_lot_size(sl=sl, symbol=symbol, commision_per_lot=commision_per_lot) # sl, symbol, risk_ratio=0.05, commision_per_lot=4

    point = mt5.symbol_info(symbol).point    #EURUSD point: 1e-05   #BTCUSD point: 0.01 
    #####################
    # attention: the point here is not stop_loss_in_pips * 10. Instead, it's a decimal, telling us how many digits there are.
    #####################
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
        if result_dict["comment"] == "AutoTrading disabled by client":
            print("AutoTrading disabled by client")
            mt5.shutdown()
            quit()
        
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
def calculate_current_sma(symbol="BTCUSD", timeframe=mt5.TIMEFRAME_M5, sma_length=24, start_position=0):
    rates = get_last_n_ticks(symbol=symbol, timeframe=timeframe, start_position=start_position, tick_count=sma_length)
    total = 0
    for rate in rates:
        total += rate['close']
    sma = total / sma_length
    return sma


"""
# calculate the 24sma value of the latest 5 ticks
# sma from latest to earlier

# last 5 sma prices start_pos =0, 1, 2, 3, 4
sma_count = 5

return an sma_list that contains 5 (or n) sma prices 
"""
def calculate_sma_of_latest_n_ticks(symbol="USDJPY", timeframe= mt5.TIMEFRAME_M5, sma_length=24, sma_count=5):
    sma_list = []
    for start_position in range(0, sma_count): # 0 means latest tick, 1 means the tick previous to the latest tick
        this_sma = calculate_current_sma(symbol=symbol, timeframe= timeframe, sma_length=sma_length, start_position=start_position)
        sma_list.append(this_sma)

    # the order is: latest sma at the front of the list, earlier sma at the later of the list

    sma_list.reverse()
    # sma list now is from earlier to later, which is the natural order
    print(f"sma list: {sma_list}")

    return sma_list
    

# sma_list length determines how many ticks we examine to see if we're above or below sma
def if_above_or_below_sma(sma_list, timeframe=mt5.TIMEFRAME_M5, symbol="BTCUSD", start_position=0):
    sma_list_length = len(sma_list)
    # only get several rates, e.g., 5, not 24
    rates = get_last_n_ticks(symbol=symbol, timeframe=timeframe, start_position=start_position, tick_count=sma_list_length)
    
    above_sma = 0
    below_sma = 0
    rate_close_list = []
    for rate in rates:
        rate_close_list.append(rate['close'])
        
    print(f"rate close list: {rate_close_list}")

    i = 0
    while i < sma_list_length:
        # print(rate_close_list[i])
        if rate_close_list[i] > sma_list[i]:
             above_sma += 1
        i += 1

    # if above_sma == sma_list_length:
    if above_sma >= sma_list_length - 3: # 5-3 -> 2 # this should be good. If the close price goes above it or just on it, when the next tick emerges, immediately we will open an order. # This is the special rule 3
        above_sma = "above"
        return above_sma

    i = 0
    while i < sma_list_length:
        if rate_close_list[i] < sma_list[i]:
             below_sma += 1
        i += 1

    # if below_sma == sma_list_length:
    if below_sma >= sma_list_length - 3:
        below_sma = "below"
        return below_sma

    # if above_sma == "above_sma" and below_sma == "below_sma":
    #     # this means we have two close prices > the corresponding sma
    #     # and two close prices < the corresponding sma
    #     # so we are kinda in the middle
    #     # the last tick's close price is the current tick's price. It's still changing, not the real close price
    #     mixed = "mixed"
    #     return mixed

    return "mixed"

"""
This is the revised version of func if_above_or_below_sma()
return a string with a value of one of the below four:
above, below, across_sma_from_below_to_above, across_sma_from_above_to_below

also we have a list that contains five (or designated length) tick's position relative to the sma
this is not returned
"""
def check_each_tick_close_price_above_or_below_sma(sma_list, timeframe=mt5.TIMEFRAME_M5, symbol="BTCUSD", start_position=0):
    sma_list_length = len(sma_list)
    # only get several rates, e.g., 5, not 24
    rates = get_last_n_ticks(symbol=symbol, timeframe=timeframe, start_position=start_position, tick_count=sma_list_length)

    # position = 0
    
    rate_close_list = []
    for rate in rates:
        rate_close_list.append(rate['close'])
        
    print(f"rate close list: {rate_close_list}")

    sma_position_list = []

    i = 0
    while i < sma_list_length:
        if rate_close_list[i] < sma_list[i]:
            sma_position_list.append("below")
        elif rate_close_list[i] == sma_list[i]:
            sma_position_list.append("equal")
        elif rate_close_list[i] > sma_list[i]:
            sma_position_list.append("above")
        i += 1

    print(f"The position of each tick's close price: ")
    print(sma_position_list)

    # if 5 sma, then sma_list_length is 5. We have 0, 1, 2, 3, 4, these four items. 4 is the current tick. 3 is the one previous the current one
    # sma_list_length - 1 is the current tick, sma_list_length - 2 is the one previous the current one
    # the close price of this tick is formed. the current tick is not yet formed but still changing. 
    # we cannot take the current tick's changing price as what we use to check if we are above or below

    # if sma_position_list.count("above") >= sma_list_length-2:
    #     position = "above"
    # elif sma_position_list.count("below") >= sma_list_length-2:
    #     position = "below"
    # elif sma_position_list[sma_list_length-2] in {"above", "equal"} and sma_position_list[sma_list_length-3] == "below" and sma_position_list[sma_list_length-4] == "below":
    #     position = "down2up_across_sma"
    # elif sma_position_list[sma_list_length-2] in {"below", "equal"} and sma_position_list[sma_list_length-3] == "above" and sma_position_list[sma_list_length-4] == "above":
    #     position = "up2down_across_sma"
    
    # ok. let's only do good and clear trades
    # if it's ambiguous and the ticks are up and down across the sma when we cannot tell if it's above or below, we wait 

    if sma_position_list.count("above") == sma_list_length: # absolute above
        position = "above"
    elif sma_position_list.count("below") == sma_list_length: # absolute below
        position = "below"
    elif sma_position_list[sma_list_length-1] == "above" and sma_position_list[sma_list_length-2] in {"above", "equal"} \
        and sma_position_list[sma_list_length-3] == "below" and sma_position_list[sma_list_length-4] == "below" and sma_position_list[sma_list_length-5] == "below":
        position = "across_sma_from_below_to_above"
    elif sma_position_list[sma_list_length-1] == "below" and sma_position_list[sma_list_length-2] in {"below", "equal"} \
        and sma_position_list[sma_list_length-3] == "above" and sma_position_list[sma_list_length-4] == "above" and sma_position_list[sma_list_length-5] == "above":
        position = "across_sma_from_above_to_below"
    else:
        position = "mixed"

    return position
    

def check_retrace_when_long(symbol="BTCUSD", timeframe=mt5.TIMEFRAME_M5, start_position=0, tick_count=5): 
    # 0 1 2 3 4 compare low of 2 and 3 with low of 0 and 1
    # 4 is the latest
    retracement = False
    rates = get_last_n_ticks(symbol=symbol, timeframe=timeframe, start_position=start_position, tick_count=tick_count)
    tick_0_low = rates[0]['low']
    tick_1_low = rates[1]['low']
    tick_2_low = rates[2]['low']
    tick_3_low = rates[3]['low']
    tick_4_low = rates[4]['low'] # current tick
    lower_price_tick_0_and_1 = compare_two_and_get_lower(tick_0_low, tick_1_low)
    lower_price_tick_2_and_3 = compare_two_and_get_lower(tick_2_low, tick_3_low)
    print(f"lower_price_tick_0_and_1: {lower_price_tick_0_and_1}")
    print(f"lower_price_tick_2_and_3: {lower_price_tick_2_and_3}")
    # if the below is positive, then we have a retracement, the low price of the previous two got lower than the price of the previous previous two
    # below is compare 'the two ticks before the current tick' and 'the two ticks before the aforementioned two ticks'
    if lower_price_tick_2_and_3 < lower_price_tick_0_and_1:
        retracement = True
    
    # but there's another situation
    # the lower of the current tick and the tick before the current < the lower of the previous two ticks before them
    lower_price_tick_3_and_4 = compare_two_and_get_lower(tick_3_low, tick_4_low)
    lower_price_tick_1_and_2 = compare_two_and_get_lower(tick_1_low, tick_2_low)
    print(f"lower_price_tick_1_and_2: {lower_price_tick_1_and_2}")
    print(f"lower_price_tick_3_and_current: {lower_price_tick_3_and_4}")
    if lower_price_tick_3_and_4 < lower_price_tick_1_and_2:
        retracement = True


    # ERROR!!! need to pass *TWO* ticks
    # but there's a third situation
    # the 1 2'low < 0's low, but 3 fails to pass 1,2, but 4 passes
    # if lower_price_tick_1_and_2 < tick_0_low:
    #     retracement = True
    #     print("lower_price_tick_1_and_2 < tick_0_low")

    print(f"retracement: {retracement}")
    return retracement

def check_retrace_when_short(symbol="BTCUSD", timeframe=mt5.TIMEFRAME_M5, start_position=0, tick_count=5): 
    retracement = False
    rates = get_last_n_ticks(symbol=symbol, timeframe=timeframe, start_position=start_position, tick_count=tick_count)
    tick_0_high = rates[0]['high']
    tick_1_high = rates[1]['high']
    tick_2_high = rates[2]['high']
    tick_3_high = rates[3]['high']
    tick_4_high = rates[3]['high']
    higher_price_tick_0_and_1 = compare_two_and_get_higher(tick_0_high, tick_1_high)
    higher_price_tick_2_and_3 = compare_two_and_get_higher(tick_2_high, tick_3_high)
    print(f"higher_price_tick_0_and_1: {higher_price_tick_0_and_1}")
    print(f"higher_price_tick_2_and_3: {higher_price_tick_2_and_3}")

    if higher_price_tick_2_and_3 > higher_price_tick_0_and_1:
        retracement = True

    higher_price_tick_3_and_4 = compare_two_and_get_higher(tick_3_high, tick_4_high)
    higher_price_tick_1_and_2 = compare_two_and_get_higher(tick_1_high, tick_2_high)
    if higher_price_tick_3_and_4 > higher_price_tick_1_and_2:
        retracement = True

    # # ERROR!!! need to pass *TWO* ticks
    # # but there's a third situation
    # # the 1 2'high > 0's high, but 3 fails to pass 1,2, but 4 passes
    # if higher_price_tick_1_and_2 > tick_0_high:
    #     retracement = True
    #     print("higher_price_tick_1_and_2 > tick_0_high")

    print(f"retracement: {retracement}")
    return retracement

def check_pause_when_long(symbol="BTCUSD", timeframe="TIMEFRAME_M5", start_position=0, tick_count=5):
    pause = False
    rates = get_last_n_ticks(symbol=symbol, timeframe=timeframe, start_position=start_position, tick_count=tick_count)
    tick_0_high = rates[0]['high']
    tick_1_high = rates[1]['high']
    tick_2_high = rates[2]['high']
    tick_3_high = rates[3]['high']
    higher_of_tick_0_and_1_high = compare_two_and_get_higher(tick_0_high, tick_1_high)
    higher_of_tick_2_and_3_high = compare_two_and_get_higher(tick_2_high, tick_3_high)
    # if higher_of_tick_2_and_3_high <= higher_of_tick_0_and_1_high:
    if higher_of_tick_2_and_3_high <= tick_1_high: # tick 1 high + 5 points give it some space
        pause = True

    # another situation, need to realize
    # if 0 highest, 1 < 2 < 0, 3 < 2, 4 > 3&2:
    # namely, if 1,2's higher < 0's high
    higher_of_tick_1_and_2_high = compare_two_and_get_higher(tick_1_high, tick_2_high)
    if higher_of_tick_1_and_2_high <= tick_0_high:
        pause = True

    print(f"higher_of_tick_0_and_1_high: {higher_of_tick_0_and_1_high}")
    print(f"higher_of_tick_2_and_3_high: {higher_of_tick_2_and_3_high}")
    print(f"pause: {pause}")
    return pause

def check_pause_when_short(symbol="BTCUSD", timeframe=mt5.TIMEFRAME_M5, start_position=0, tick_count=5):
    pause = False
    rates = get_last_n_ticks(symbol=symbol, timeframe=timeframe, start_position=start_position, tick_count=tick_count)
    tick_0_low = rates[0]['low']
    tick_1_low = rates[1]['low']
    tick_2_low = rates[2]['low']
    tick_3_low = rates[3]['low']
    lower_of_tick_0_and_1_low = compare_two_and_get_lower(tick_0_low, tick_1_low)
    # higher_of_tick_2_and_3_low = compare_two_and_get_higher(tick_2_low, tick_3_low) # wrong, must be the lower that is above lower_of_tick_0_and_1_low
    lower_of_tick_2_and_3_low = compare_two_and_get_lower(tick_2_low, tick_3_low) 
    # if lower_of_tick_2_and_3_low >= lower_of_tick_0_and_1_low:
    if lower_of_tick_2_and_3_low >= tick_1_low: # seems tick_1_low will do the job
        pause = True
    
    # another situation, need to realize
    # if 0 lowest, 1 > 2 > 0, 3 > 2, 4 < 3&2:
    # namely, if 1,2's low < 0's low
    lower_of_tick_1_and_2_low = compare_two_and_get_lower(tick_1_low, tick_2_low)
    if lower_of_tick_1_and_2_low >= tick_0_low:
        pause =True

    print(f"lower_of_tick_0_and_1_low: {lower_of_tick_0_and_1_low}")
    print(f"lower_of_tick_2_and_3_low: {lower_of_tick_2_and_3_low}")
    print(f"pause: {pause}")
    return pause

def check_retrace_or_pause_when_long(symbol="BTCUSD", timeframe=mt5.TIMEFRAME_M5, start_position=0, tick_count=5):
    retrace_when_long = check_retrace_when_long(symbol=symbol, timeframe=timeframe, start_position=start_position, tick_count=tick_count)
    pause_when_long = check_pause_when_long(symbol=symbol, timeframe=timeframe, start_position=start_position, tick_count=tick_count)
    if retrace_when_long or pause_when_long:
        return True
    else:
        return False

def check_retrace_or_pause_when_short(symbol="BTCUSD", timeframe=mt5.TIMEFRAME_M5, start_position=0, tick_count=5):
    retrace_when_short = check_retrace_when_short(symbol=symbol, timeframe=timeframe, start_position=start_position, tick_count=tick_count)
    pause_when_short = check_pause_when_short(symbol=symbol, timeframe=timeframe, start_position=start_position, tick_count=tick_count)
    if retrace_when_short or pause_when_short:
        return True
    else:
        return False

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

    # symbol="BTCUSD"
    symbol="USDJPY"
    # type_filling = mt5.ORDER_FILLING_IOC # IC
    type_filling = mt5.ORDER_FILLING_FOK # FXTM
    timeframe = mt5.TIMEFRAME_M5
    sl_limit = 300 # points for USDJPY

    # specify the commision for each lot here and make sure to pass it in the following open_request() functions
    # currently it is not included in the parameters
    commision_per_lot = 4

    # used to print how many seconds it runs, 
    # also if the program freezes, the print output will not change, which draws us attention
    timer = 0

    while True:

        open_positions = check_open_positions()
        if open_positions == 0:
            # rates <class 'numpy.ndarray'>
            rates = get_last_n_ticks(symbol=symbol, timeframe=timeframe, tick_count=3)
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

            tick_two_close = rates[1]['close']

            #sma = calculate_current_sma(symbol="BTCUSD", sma_length=24)
            
            sma_list = calculate_sma_of_latest_n_ticks(symbol=symbol, timeframe=timeframe, sma_length=24, sma_count=5)
            
            # # v1 
            # above_or_below_sma = if_above_or_below_sma(sma_list, timeframe=timeframe, symbol=symbol, start_position=0)
            # print(f"above or below sma: {above_or_below_sma}")

            # v2
            above_or_below_sma = check_each_tick_close_price_above_or_below_sma(sma_list, timeframe=timeframe, symbol=symbol, start_position=0)
            print(f"above or below sma: {above_or_below_sma}")
            
            # if current_price > higher_price, and we are above the 24sma, and there's a retracement
            if current_price > higher_price and above_or_below_sma == "above" and check_retrace_or_pause_when_long(symbol=symbol, timeframe=timeframe, start_position=0, tick_count=5):
                print("buy")
                # sl = current_price * 1000 - rates[1][3] * 1000  # USDJPY
                # BTC digits -> 2   USDJPY digits -> 3
                digits = mt5.symbol_info(symbol).digits # BTC digits -> 2         mt5.symbol_info(symbol).xxx, not mt5.symbol_info_tick(symbol).xxx
                multiply_digits = 10 ** digits
                # sl is in points, /10 if needed to convert to pips
                sl = current_price * multiply_digits - lower_price * multiply_digits  # BTC
                # sl = current_price * 100 - lower_price * 100  # BTC
                
                open_request(sl_price=lower_price, type="buy", sl=sl, symbol=symbol, type_filling=type_filling, commision_per_lot=commision_per_lot)
                # continue # if we opened an order, we go back to the beginning of the loop, we don't sleep
            elif current_price < lower_price and above_or_below_sma == "below" and check_retrace_or_pause_when_short(symbol=symbol, timeframe=timeframe, start_position=0, tick_count=5): # if current_price < lower_price and we are below the 25sma
                print("sell")
                # second_tick_high-current_price
                # sl = rates[1][2] * 1000 - current_price * 1000  # USDJPY
                digits = mt5.symbol_info(symbol).digits
                multiply_digits = 10 ** digits
                sl = higher_price * multiply_digits - current_price * multiply_digits  # BTC
                # sl = higher_price * 100 - current_price * 100  # BTC
                open_request(sl_price=higher_price, type="sell", sl=sl, symbol=symbol, type_filling=type_filling, commision_per_lot=commision_per_lot)
                # continue

            # do we need to check retrace or pause when doing across sma trades?
            # maybe not. because usually it's the price goes down from above to below and then go above, so there should be a natural retrace/reverse
            # actually it's best to include, maybe. bacause if the reverse point is too far away (in this case maybe no retrace nearby the sma), 
            # the price would touch the sma and then bounce back, continue its previous trend

            # across_sma_from_below_to_above, 
            elif current_price > tick_two_close and above_or_below_sma == "across_sma_from_below_to_above": # and check_retrace_or_pause_when_long(symbol=symbol, timeframe=timeframe, start_position=0, tick_count=5):
                print("buy")
                # sl = current_price * 1000 - rates[1][3] * 1000  # USDJPY
                # BTC digits -> 2   USDJPY digits -> 3
                digits = mt5.symbol_info(symbol).digits # BTC digits -> 2         mt5.symbol_info(symbol).xxx, not mt5.symbol_info_tick(symbol).xxx
                multiply_digits = 10 ** digits
                # sl is in points, /10 if needed to convert to pips
                sl = current_price * multiply_digits - lower_price * multiply_digits  # BTC
                # sl = current_price * 100 - lower_price * 100  # BTC

                # hard-coded for USD/JPY
                if sl >= sl_limit: # if sl > 300 points, or 30 pips
                    print(f"sl is {sl} points. too large. aborted.")
                    continue
                
                open_request(sl_price=lower_price, type="buy", sl=sl, symbol=symbol, type_filling=type_filling, commision_per_lot=commision_per_lot)
                # continue # if we opened an order, we go back to the beginning of the loop, we don't sleep
            # across_sma_from_above_to_below
            elif current_price < tick_two_close and above_or_below_sma == "across_sma_from_above_to_below": # and check_retrace_or_pause_when_short(symbol=symbol, timeframe=timeframe, start_position=0, tick_count=5):
                print("sell")
                # second_tick_high-current_price
                # sl = rates[1][2] * 1000 - current_price * 1000  # USDJPY
                digits = mt5.symbol_info(symbol).digits
                multiply_digits = 10 ** digits
                sl = higher_price * multiply_digits - current_price * multiply_digits  # BTC
                # hard-coded for USD/JPY
                if sl >= sl_limit: # if sl > 300 points, or 30 pips
                    print(f"sl is {sl} points. too large. aborted.")
                    continue

                # sl = higher_price * 100 - current_price * 100  # BTC
                open_request(sl_price=higher_price, type="sell", sl=sl, symbol=symbol, type_filling=type_filling, commision_per_lot=commision_per_lot)
                # continue

        # time.sleep(0.1)
        else:
            # open_positions > 0
            # sys.stdout.write(".")
            # sys.stdout.flush()
            print(f"\t{timer} s", end="\r", flush=True)
            

        time.sleep(0.5)
        # os.system('cls') # this will clean all the output, not what we expect
        timer += 0.5




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
