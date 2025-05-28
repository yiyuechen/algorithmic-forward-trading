
"""
To-do
1. calculate lot size
lot_size = (risk_ratio * capital) / (stop_loss * pip_value + commission_per_lot + spread)    [X]
!!!
!!!
This is wrong. Spread should not be in the (), should be spread/10*pip_value

formula
lot * stop_loss * pip_value + lot * commission_per_lot + lot * spread/10*pip_value = capital_in_risk
lot * (stop_loss * pip_value + commission_per_lot + spread/10*pip_value) = capital_in_risk
lot = capital_in_risk / (stop_loss * pip_value + commission_per_lot + spread/10*pip_value)   [OK]

2. calculate spread in SL and TP

3. We can directly use the tick's lower price as our SL. No need to calc the SL and then convert and add to the current price.      [OK]
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


# the branch reversed works really well in consolidations. So we may do this:
1) check sma, if say, 5 to 10 ticks, if the abs (tick0_sma - tick9_sma) < gap_limit, then we consider it's consolidating.
then we use this stragegy
( Or maybe we could do the slope, but this this it's the same. because slope = price_change/time_change)
2) if not consolidating, we use the normal way, to follow the trend. 
3) Or, we could simply don't do trades during consolidation. just check 1)

add time range 7am-11pm

################
add modify stop loss when price nears within 3 pips from TP

avoid shrinking steps

add risk reward ratio, if doing 1 min, try risk:reward 2:1 or 3:1

try when 2pips in profit, close the order
################


try:
when 3 pips from tp, counting down 10 seconds to close the order [Done]



to do:
when tp and then the current position still meets requirements for openting an order, we need to check if there's already an chance prior to this one, 
if so, it means we've missed the best chance to get in.

The idea would be to see the one prior to the current one, or the one prior to prior, or even further, so see if we have one tick that meets the best chance to get in

we can achieve this in another way:
everytime we count down 10s and close an order, after we close it, we count down for the time of two ticks, so we wait for two ticks before looking for another trade
it's like we are taking a break from the market

"""


from getpass import getpass
import time
import traceback
import MetaTrader5 as mt5
import numpy as np
import credential_info
from datetime import datetime, timedelta, timezone

# import the 'pandas' module for displaying data obtained in the tabular form
import pandas as pd

import os

import get_news_data

pd.set_option('display.max_columns', 500) # number of columns to be displayed
pd.set_option('display.width', 1500)      # max table width to display


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


def login(account, password, server_to_connect):
    authorized = mt5.login(account, password, server_to_connect)

    if authorized:
        # # display trading account data 'as is'
        # print(mt5.account_info())
        # display trading account data in the form of a list
        print("Show account_info()._asdict():")
        account_info_dict = mt5.account_info()._asdict()
        for prop in account_info_dict:
            print("  {}={}".format(prop, account_info_dict[prop]))
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


# def check_current_symbol_open_positions(symbol="USDJPY"):
#     current_symbol_positions = mt5.positions_get(symbol=symbol)
#     # print(f"current_symbol_positions: {current_symbol_positions}")
#     # print(type(current_symbol_positions))
#     # output
#     # current_symbol_positions: ()
#     # <class 'tuple'>
#     if current_symbol_positions:
#         print(current_symbol_positions)
#         # print(current_symbol_positions[0].time)
#         position_total_of_current_symbol = len(current_symbol_positions)
#     else:
#         position_total_of_current_symbol = 0

#     return position_total_of_current_symbol

def check_current_symbol_open_positions(symbol="USDJPY"):
    current_symbol_open_positions = mt5.positions_get(symbol=symbol)
    # print(f"current_symbol_open_positions: {current_symbol_open_positions}")
    # print(type(current_symbol_open_positions))
    # output
    # current_symbol_open_positions: ()
    # <class 'tuple'>
    
    return current_symbol_open_positions


# def calculate_lot_size(sl, symbol, risk_ratio=0.05, commission_per_lot=4): #sl is in points, need to convert     # currently @param commission_per_lot is not included in the passed parameters
#     # pip_value = 1/10**(digits-1)*contract_size?
#     # EURUSD 1/(10**(5-1)) * 100000 => 10 USD
#     # USDJPY 1/(10**(3-1)) * 100000 => 1000 JPY
#     # BTCUSD 1/(10**(2-1)) * 1 => 0.1 USD

#     spread = mt5.symbol_info(symbol).spread

#     #convert 
#     stop_loss = sl/10
#     print(f"sl pip: {stop_loss}")

#     trade_contract_size = mt5.symbol_info(symbol).trade_contract_size
#     digits = mt5.symbol_info(symbol).digits
#     pip_value = 1/10**(digits-1)*trade_contract_size
#     # pip_value = 1/10**(digits-1)*trade_contract_size * 
    
#     # hard code not the best way
#     # tmp method
#     if symbol == "USDJPY":
#         pip_value = pip_value / mt5.symbol_info(symbol).ask
    
#     print(f"pip_value: {pip_value}")

#     capital = mt5.account_info().balance
#     capital_in_risk = risk_ratio * capital

#     print(f"capital: {capital}")
#     print(f"capital in risk: {capital_in_risk}") 
#     print(f"65% risk capital: {capital_in_risk * 0.65}")

#     # commission is of two operations, open and close. So it's 2 times of what mt5 specification shows (which is only for opening or closing, not opening and closing)
#     # stop_loss is in pips, not points
#     # lot_size = (risk_ratio * capital) / (stop_loss * pip_value + commission_per_lot + spread)
#     # lot_size = capital_in_risk / (stop_loss * pip_value + commission_per_lot)
#     lot_size = capital_in_risk / (stop_loss * pip_value + commission_per_lot + spread/10*pip_value)


#     print(f"lot size = {lot_size} before rounding")
#     lot_size = round(lot_size, 2)
#     print(f"lot size = {lot_size}, commision = {lot_size*commission_per_lot}, commission_per_lot = {commission_per_lot}")

#     if lot_size < 0.01:
#         print(f"lot size = {lot_size}. Change to 0.01")
#         lot_size = 0.01
    
#     # or maybe quit
#     # if lot_size < 0.01:
#     #     print("Insufficient funds. Cannot make 0.01 lots.")
#     #     mt5.shutdown()
#     #     quit()

#     return lot_size

# def calculate_lot_size(sl, symbol, risk_ratio=0.05, commission_per_lot=4): #sl is in points, need to convert     # currently @param commission_per_lot is not included in the passed parameters
#     # pip_value = 1/10**(digits-1)*contract_size?
#     # EURUSD 1/(10**(5-1)) * 100000 => 10 USD
#     # USDJPY 1/(10**(3-1)) * 100000 => 1000 JPY
#     # BTCUSD 1/(10**(2-1)) * 1 => 0.1 USD

#     spread = mt5.symbol_info(symbol).spread

#     #convert 
#     stop_loss = sl/10
#     print(f"sl pip: {stop_loss}")

#     trade_contract_size = mt5.symbol_info(symbol).trade_contract_size
#     digits = mt5.symbol_info(symbol).digits

#     # pip_value = 1/10**(digits-1)*trade_contract_size
#     # # pip_value = 1/10**(digits-1)*trade_contract_size * 
    
#     # # hard code not the best way
#     # # tmp method
#     # if symbol == "USDJPY":
#     #     pip_value = pip_value / mt5.symbol_info(symbol).ask

#     """
#     With a similar contract, the Pip don't have the same value on every currency pairs. the formula is:

#     S: Size of the contract
#     dPIP: pip definition (0.0001, 0.001...)
#     XXX: the first currency
#     YYY: the second currency

#     the value of the Pip for the pair XXX/YYY = S * dPIP * YYY/USD
#     """
#     dPIP = 1/10**(digits-1)
#     YYY = symbol[-3:]
#     if YYY == "USD":
#         YYY_USD = "USDUSD"
#         print(f"YYY_USD: {YYY_USD}")
#         value_YYY_USD = 1
#         print(f"value_YYY_USD: {value_YYY_USD}")
#     else:
#         YYY_USD = YYY + "USD"
#         USD_YYY = "USD" + YYY
#         print(f"YYY_USD: {YYY_USD}")
#         print(f"USD_YYY: {USD_YYY}")
#         value_YYY_USD = 1/mt5.symbol_info(USD_YYY).bid
#         print(f"value_YYY_USD: {value_YYY_USD}")

    
#     pip_value = trade_contract_size * dPIP * value_YYY_USD
    
#     print(f"pip_value: {pip_value}")
#     print(f"spread: {spread}")

#     capital = mt5.account_info().balance
#     capital_in_risk = risk_ratio * capital

#     print(f"capital: {capital}")
#     print(f"capital in risk: {capital_in_risk}") 
#     # print(f"65% risk capital: {capital_in_risk * 0.65}")

#     # commission is of two operations, open and close. So it's 2 times of what mt5 specification shows (which is only for opening or closing, not opening and closing)
#     # stop_loss is in pips, not points
#     # lot_size = (risk_ratio * capital) / (stop_loss * pip_value + commission_per_lot + spread)
#     # lot_size = capital_in_risk / (stop_loss * pip_value + commission_per_lot)
#     lot_size = capital_in_risk / (stop_loss * pip_value + commission_per_lot + spread/10*pip_value)


#     print(f"lot size = {lot_size} before rounding")
#     # lot_size = round(lot_size, 2)


#     # check if lot size is valid
#     if lot_size < 0.01:
#         # # 1. stop the program
#         # print(f"lot_size_truncated is {lot_size}, less than 0.01, cannot open trade.")
#         # print(f"Insufficient funds. Cannot open {lot_size} lot.")
#         # mt5.shutdown()
#         # quit()

#         # 2. set lot_size to min_lot_limit
#         print(f"lot_size_truncated {lot_size} is less than min_lot_limit 0.01. \nsetting it to 0.01.")
#         lot_size = 0.01
        
#     elif lot_size > 100:
#         print(f"lot_size_truncated is {lot_size}. \nsetting it to maximum.")
#         lot_size = 100

#     # moved it from before to after the above block (lot size 0.01 to 100)
#     # after we limit lot size to 0.01 to 100, then we are safe to use the str split method.
#     # conservative lot size
#     if "." in str(lot_size): # !!!!! FATAL ERROR !!!! if lot_size is displayed in scientific notation, e.g. 1.7977235979606702e-05    this will be converted to 1.79 lot; it should be converted to 0.01
#         lot_size = float(str(lot_size).split(".")[0] + "." + str(lot_size).split(".")[1][:2])
#         print("lot size changed to conservative")

#     print(f"lot size = {lot_size}, commision = {lot_size*commission_per_lot}, commission_per_lot = {commission_per_lot}")
    
#     # or maybe quit
#     # if lot_size < 0.01:
#     #     print("Insufficient funds. Cannot make 0.01 lots.")
#     #     mt5.shutdown()
#     #     quit()

#     return lot_size

def calculate_lot_size(sl, symbol, risk_ratio, commission_per_lot): #sl is in points, need to convert     # currently @param commission_per_lot is not included in the passed parameters
    # pip_value = 1/10**(digits-1)*contract_size?
    # EURUSD 1/(10**(5-1)) * 100000 => 10 USD
    # USDJPY 1/(10**(3-1)) * 100000 => 1000 JPY
    # BTCUSD 1/(10**(2-1)) * 1 => 0.1 USD

    spread = mt5.symbol_info(symbol).spread
    # print(f"{mt5.symbol_info(symbol)}") # this does not contain commission info

    #convert 
    stop_loss = sl/10
    print(f"sl pip: {stop_loss}")

    trade_contract_size = mt5.symbol_info(symbol).trade_contract_size
    digits = mt5.symbol_info(symbol).digits

    # pip_value = 1/10**(digits-1)*trade_contract_size
    # # pip_value = 1/10**(digits-1)*trade_contract_size * 
    
    # # hard code not the best way
    # # tmp method
    # if symbol == "USDJPY":
    #     pip_value = pip_value / mt5.symbol_info(symbol).ask

    """
    With a similar contract, the Pip don't have the same value on every currency pairs. the formula is:

    S: Size of the contract
    dPIP: pip definition (0.0001, 0.001...)
    XXX: the first currency
    YYY: the second currency

    the value of the Pip for the pair XXX/YYY = S * dPIP * YYY/USD
    """
    dPIP = 1/10**(digits-1)


    # if len(symbol) == 6 and "USD" in symbol: # if it's USDXXX or XXXUSD, e.g. USDJPY and EURUSD 
    if "USD" in symbol:
        YYY = symbol[3:6]
        # for example, xauusd.p
        if YYY == "USD": # XXXUSD
            YYY_USD = "USDUSD"
            print(f"YYY_USD: {YYY_USD}")
            value_YYY_USD = 1
            print(f"value_YYY_USD: {value_YYY_USD}")
        else: # USDXXX # e.g. usdjpy.p
            YYY_USD = YYY + "USD"
            USD_YYY = "USD" + YYY
            print(f"YYY_USD: {YYY_USD}")
            print(f"USD_YYY: {USD_YYY}")
            value_YYY_USD = 1 / mt5.symbol_info(symbol).bid # I wrote usd_yyy as in mt5.symbol_info(USD_YYY).bid previously, which caused issues. because I assume it'd be USDJPY, but it could be ""USDJPY.p". So it's safer to just use "symbol"
            print(f"value_YYY_USD: {value_YYY_USD}")

        pip_value = trade_contract_size * dPIP * value_YYY_USD

    elif symbol == "BITCOIN": # just !!!STAY AWAY!!! from it. the commission is HUGE!
        value_YYY_USD = 1
        pip_value = trade_contract_size * dPIP * value_YYY_USD
        commission_per_lot = mt5.symbol_info(symbol).bid * 0.0015 # as describled in specification on mt5, it's ## 0.15% in USD per lot (min 0.01) ##
        commission_per_lot = 2 * commission_per_lot # as the commission_per_lot here is the final total commission. but actually commission per lot is calculated each time when you buy or sell, so when you close a trade, it is calculated twice.

    # # error ! because not every broker has symbols like xauusd, for dominion, they have xauusd.p, which is not a length of 6.
    # # if len(symbol) == 6 and "USD" in symbol: # if it's USDXXX or XXXUSD, e.g. USDJPY and EURUSD 
    # if len(symbol) == 6:

    #     YYY = symbol[-3:]
    #     if YYY == "USD": # XXXUSD
    #         YYY_USD = "USDUSD"
    #         print(f"YYY_USD: {YYY_USD}")
    #         value_YYY_USD = 1
    #         print(f"value_YYY_USD: {value_YYY_USD}")
    #     else: # USDXXX
    #         YYY_USD = YYY + "USD"
    #         USD_YYY = "USD" + YYY
    #         print(f"YYY_USD: {YYY_USD}")
    #         print(f"USD_YYY: {USD_YYY}")
    #         value_YYY_USD = 1/mt5.symbol_info(USD_YYY).bid
    #         print(f"value_YYY_USD: {value_YYY_USD}")

    #     pip_value = trade_contract_size * dPIP * value_YYY_USD

    # elif symbol == "BITCOIN": # just !!!STAY AWAY!!! from it. the commission is HUGE!
    #     value_YYY_USD = 1
    #     pip_value = trade_contract_size * dPIP * value_YYY_USD
    #     commission_per_lot = mt5.symbol_info(symbol).bid * 0.0015 # as describled in specification on mt5, it's ## 0.15% in USD per lot (min 0.01) ##
    #     commission_per_lot = 2 * commission_per_lot # as the commission_per_lot here is the final total commission. but actually commission per lot is calculated each time when you buy or sell, so when you close a trade, it is calculated twice. 
    
    
    
    print(f"pip_value: {pip_value}")
    print(f"spread: {spread}")

    capital = mt5.account_info().balance
    # # testing to avoid error
    # if capital == 0:
    #     capital = 1000
    #     print("!!!!!!!!!!!!!!!!!!!!")
    #     print(f"capital is 0. setting it to {capital} just for testing")
    capital_in_risk = risk_ratio * capital

     # do not print capital, just do the right trades, not focusing on the balance
    print(f"capital: {capital}")
    print(f"capital in risk: {capital_in_risk}") 
    # print(f"65% risk capital: {capital_in_risk * 0.65}")

    # commission is of two operations, open and close. So it's 2 times of what mt5 specification shows (which is only for opening or closing, not opening and closing)
    # stop_loss is in pips, not points
    # lot_size = (risk_ratio * capital) / (stop_loss * pip_value + commission_per_lot + spread)
    # lot_size = capital_in_risk / (stop_loss * pip_value + commission_per_lot)
    lot_size = capital_in_risk / (stop_loss * pip_value + commission_per_lot + spread/10*pip_value)


    # # need to move it after checking lot_size validity, bc if lot size < 0.01, lot_size is 0.00, and radicalize it will be 0.00, and later calculation will yield errors, like float division by zero
    # oh, actually the divison by zero error is due to the capital is zero
    # radical_lot_size = round(lot_size, 2)
    # print(f"lot size = {lot_size} before rounding")
    # # lot_size = round(lot_size, 2)



    # check if lot size is valid
    if lot_size < 0.01:
        # # 1. stop the program
        # print(f"lot_size_truncated is {lot_size}, less than 0.01, cannot open trade.")
        # print(f"Insufficient funds. Cannot open {lot_size} lot.")
        # mt5.shutdown()
        # quit()

        # 2. set lot_size to min_lot_limit
        print(f"lot_size_truncated {lot_size} is less than min_lot_limit 0.01. \nsetting it to 0.01.")
        lot_size = 0.01
        
    elif lot_size > 100:
        print(f"lot_size_truncated is {lot_size}. \nsetting it to maximum.")
        lot_size = 100

    # moved after checking lot_size validity, bc if lot size < 0.01, lot_size is 0.00, and radicalize it will be 0.00, and later calculation will yield errors, like float division by zero
    radical_lot_size = round(lot_size, 2)
    print(f"lot size = {lot_size} before rounding")

    
    # !!!!! FATAL ERROR !!!! if lot_size is displayed in scientific notation, e.g. 1.7977235979606702e-05    this will be converted to 1.79 lot; it should be converted to 0.01
    # moved it from before to after the above block (lot size 0.01 to 100)
    # after we limit lot size to 0.01 to 100, then we are safe to use the str split method.
    # conservative lot size
    if "." in str(lot_size):
        lot_size = float(str(lot_size).split(".")[0] + "." + str(lot_size).split(".")[1][:2])
        print("lot size changed to conservative")

    print(f"lot size = {lot_size}, commision = {lot_size*commission_per_lot}, commission_per_lot = {commission_per_lot}")
    
    print()
    print(f"radical lot size: {radical_lot_size}")
    actual_capital_in_risk_without_fee = radical_lot_size * (stop_loss * pip_value)
    print(f"actual_capital_in_risk_without_fee: {actual_capital_in_risk_without_fee}, risk percent: {actual_capital_in_risk_without_fee/capital}") 
    # print(f"actual_capital_in_risk_without_fee: {actual_capital_in_risk_without_fee}, risk percent: {actual_capital_in_risk_without_fee/capital*100:.4f}%")
    actual_capital_in_risk_with_fee = radical_lot_size * (stop_loss * pip_value + commission_per_lot + spread/10*pip_value)
    print(f"actual_capital_in_risk_with_fee: {actual_capital_in_risk_with_fee}, risk percent: {actual_capital_in_risk_with_fee/capital} ({actual_capital_in_risk_with_fee/capital*100:.2f}%)")
    print(f"total fee: {radical_lot_size * (commission_per_lot + spread/10*pip_value)}, where: \n commission: {radical_lot_size * commission_per_lot}\n spread fee: {radical_lot_size * spread/10*pip_value}") 
    
    print()
    print(f"conservative lot size: {lot_size}")
    actual_capital_in_risk_without_fee = lot_size * (stop_loss * pip_value)
    print(f"actual_capital_in_risk_without_fee: {actual_capital_in_risk_without_fee}, risk percent: {actual_capital_in_risk_without_fee/capital}") 
    actual_capital_in_risk_with_fee = lot_size * (stop_loss * pip_value + commission_per_lot + spread/10*pip_value)
    print(f"actual_capital_in_risk_with_fee: {actual_capital_in_risk_with_fee}, risk percent: {actual_capital_in_risk_with_fee/capital} ({actual_capital_in_risk_with_fee/capital*100:.2f}%)")
    print(f"total fee: {lot_size * (commission_per_lot + spread/10*pip_value)}, where: \n commission: {lot_size * commission_per_lot}\n spread fee: {lot_size * spread/10*pip_value}") 
    
    return lot_size


def open_request(sl_price, type="buy", sl=100, symbol="USDJPY", type_filling=mt5.ORDER_FILLING_IOC, commission_per_lot=0, risk_ratio=0.05, risk_reward_ratio=2, tp_percent=0.75, added_points_to_sl=0, added_points_to_tp=0, fixed_tp=True, fixed_tp_in_points=0):
    
    # lot = 0.1
    lot = calculate_lot_size(sl=sl, symbol=symbol, risk_ratio=risk_ratio, commission_per_lot=commission_per_lot) # sl, symbol, risk_ratio=0.05, commission_per_lot=4

    point = mt5.symbol_info(symbol).point    #EURUSD point: 1e-05   #BTCUSD point: 0.01 
    #####################
    # attention: the point here is not stop_loss_in_pips * 10. Instead, it's a decimal, telling us how many digits there are.
    #####################
    # price = mt5.symbol_info_tick(symbol).ask
    deviation = 20


    if type == "buy":
        type = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).ask
    elif type == "sell":
        type = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid
        # if sell, sl shoult be price -  100* (-point)
        point = -point
    
    if fixed_tp:
        tp = fixed_tp_in_points
    else:
        # in points
        tp = sl / risk_reward_ratio
        # make tp 75% of theo tp
        tp = int(tp * tp_percent)

    # tp is already ideal sl + added_points_to_sl, 
    # but let's add an additional added_points_to_sl to tp
    # so that tp is ideal sl + added_points_to_sl + added_points_to_sl
    # meaning 2 * added_points_to_sl
    # i.e. tp = tight sl (without one pip below the low) + 1 pip and then + another 1 (to cover the spread and commission fees)
    # comment this so that tp = sl, not sl + 1 pip

    # I'd say don't add another 1 pip to the sl (which is strict sl + 1pip), because it does not work well on m30, m15. price is 1 pip shy from tp and then reverses to hit the sl
    # tp = tp + added_points_to_sl 
    tp += added_points_to_tp # so we add (maybe) 1 pip to the tp, then the tp is 1 pip larger than sl, making the RR positive, no matter if the sl is the strict sl or sl + 1pip

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": type,
        "price": price,
        #"sl": price - sl * point, # "sl": price - 100 * point,  EURUSD 100 * 0.00001 => 0.001   1.02380-0.001 => 1.02280 => 10 pips
        # try to directly use the price of the previous tick low
        "sl": sl_price,
        # "tp": price + sl * point,
        "tp": price + tp * point,
        "deviation": deviation,
        "magic": 108080,
        "comment": "open_request",
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



def close_request(symbol, ticket, lot, type_filling, close_type):
    # create a close request
    # position_id=result.order

    if close_type == 0:
        type = mt5.ORDER_TYPE_BUY
        price=mt5.symbol_info_tick(symbol).ask
    elif close_type == 1:
        type = mt5.ORDER_TYPE_SELL
        price=mt5.symbol_info_tick(symbol).bid

    
    deviation=20
    request={
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": type,
        "position": ticket,
        "price": price,
        "deviation": deviation,
        "magic": 234000,
        "comment": "python script close",
        "type_time": mt5.ORDER_TIME_GTC,
        # "type_filling": mt5.ORDER_FILLING_RETURN,
        "type_filling": type_filling,
    }
    # send a trading request
    result = mt5.order_send(request)
    # check the execution result
    print("3. close position #{}: sell {} {} lots at {} with deviation={} points".format(ticket, symbol, lot, price, deviation));
    while result.retcode != mt5.TRADE_RETCODE_DONE:
        print("4. order_send failed, retcode={}".format(result.retcode))
        # print("   result", result)
        # request the result as a dictionary and display it element by element
        result_dict = result._asdict()
        for field in result_dict.keys():
            print("   {}={}".format(field,result_dict[field]))
            # if this is a trading request structure, display it element by element as well
            if field == "request":
                traderequest_dict=result_dict[field]._asdict()
                for tradereq_filed in traderequest_dict:
                    print("       traderequest: {}={}".format(tradereq_filed,traderequest_dict[tradereq_filed]))
        # print("shutdown() and quit")
        # mt5.shutdown()
        # quit()

        # print("\nError\n")
        if result_dict["comment"] == "AutoTrading disabled by client":
            print("AutoTrading disabled by client")
            mt5.shutdown()
            quit()

        # send AGAIN until it successfully closes the trade
        result = mt5.order_send(request)


    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print("4. position #{} closed, {}".format(ticket, result))
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
IF no tp is set:

points_from_tp = 20.000000000010232 points
points_from_tp = 20.000000000010232 points
points_from_tp = 20.000000000010232 points
points_from_tp = 20.000000000010232 points
points_from_tp = 20.000000000010232 points
points_from_tp = 20.000000000010232 points
points_from_tp = 19.000000000005457 points
1. order_send(): modifying the sl to break even
2. order_send done,  OrderSendResult(retcode=10009, deal=0, order=0, volume=0.0, price=0.0, bid=0.0, ask=0.0, comment='Request executed', request_id=151, retcode_external=0, request=TradeRequest(action=6, magic=234000, order=0, symbol='USDJPY', volume=0.0, price=0.0, stoplimit=0.0, sl=138.574, tp=0.0, deviation=20, type=0, type_filling=0, type_time=0, expiration=0, comment='python script open', position=2274618675, position_by=0))
   modified stop loss with POSITION_TICKET=0
points_from_tp = 138571.0 points
points_from_tp = 138572.0 points
points_from_tp = 138572.0 points
points_from_tp = 138572.0 points
points_from_tp = 138572.0 points
points_from_tp = 138572.0 points
"""

def modify_sl_request(symbol, ticket, sl_price, tp_price, type_filling): # MUST set TP, OR TP will be empty, NO TP after modifying SL
    # # lot = 0.1
    # lot = calculate_lot_size(sl=sl, symbol=symbol, risk_ratio=risk_ratio, commission_per_lot=commission_per_lot) # sl, symbol, risk_ratio=0.05, commission_per_lot=4

    # point = mt5.symbol_info(symbol).point    #EURUSD point: 1e-05   #BTCUSD point: 0.01 
    #####################
    # attention: the point here is not stop_loss_in_pips * 10. Instead, it's a decimal, telling us how many digits there are.
    #####################
    # price = mt5.symbol_info_tick(symbol).ask
    deviation = 20

    # if type == "buy":
    #     type = mt5.ORDER_TYPE_BUY
    # elif type == "sell":
    #     type = mt5.ORDER_TYPE_SELL
    #     # if sell, sl shoult be price -  100* (-point)
    #     point = -point
    
    # # in points
    # tp = sl / risk_reward_ratio

    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "symbol": symbol,
        # "volume": lot,
        # "type": type,
        "position": ticket,
        # "price": price,
        #"sl": price - sl * point, # "sl": price - 100 * point,  EURUSD 100 * 0.00001 => 0.001   1.02380-0.001 => 1.02280 => 10 pips
        # try to directly use the price of the previous tick low
        "sl": sl_price,
        "tp": tp_price,
        # "tp": price + sl * point,
        # "tp": price + tp * point,
        "deviation": deviation,
        "magic": 108081,
        "comment": "modify_sl_request",
        "type_time": mt5.ORDER_TIME_GTC,
        # "type_filling": mt5.ORDER_FILLING_RETURN,
        # "type_filling": mt5.ORDER_FILLING_FOK, # works for fxtm
        # "type_filling": mt5.ORDER_FILLING_IOC, # works for ic markect btc
        "type_filling": type_filling,

    }
    
    # send a trading request
    result = mt5.order_send(request)
    # check the execution result
    print("1. order_send(): modifying the sl to break even")
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
        print("   modified stop loss with POSITION_TICKET={}".format(result.order))


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
    #print(f"sma list: {sma_list}")

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
        
    #print(f"rate close list: {rate_close_list}")

    sma_position_list = []

    i = 0
    while i < sma_list_length:
        if rate_close_list[i] < sma_list[i]:
            sma_position_list.append("below")
        elif rate_close_list[i] == sma_list[i]:
            sma_position_list.append("equal") # this is very hard to be met, because 1) the price we see has a latency 2) the program pauses 0.5s for each check (and each check takes time)
        elif rate_close_list[i] > sma_list[i]:
            sma_position_list.append("above")
        i += 1

    #print(f"The position of each tick's close price: ")
    #print(sma_position_list)

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
    # else:
    #     position = "mixed"
    # in the below two conditions. we want to simulate when the price touch the sma and then bounce back to its previous trend. 
    # sometimes, one or two ticks may close on the other side of the sma, but if the current one is still on the trend's side, we consider it still tends to continue the trend
    # so the sma_position_list.count("above [or below]") could not be equal to sma_list_length, 
    # we need to be in the elif condition of the previously absolute above and absolute below conditions, and the across_sma_conditions
    # because they are different conditions
    
    # as long as there's a retracement, and the current price is above the sma, and there's 5-2=3 close prices above sma (two random ricks, one must be the current)
    # even if it's crossing from below to above 
    elif sma_position_list[sma_list_length-1] == "above" and sma_position_list.count("above") == sma_list_length - 2: 
        position = "mixed_above"
    elif sma_position_list[sma_list_length-1] == "below" and sma_position_list.count("below") == sma_list_length - 2:
        position = "mixed_below"
    else:
        position = "mixed"

    return position



# revised version of checking sma, 1/27/2023
def check_price_sma_position(sma_list, timeframe=mt5.TIMEFRAME_M5, symbol="BTCUSD", start_position=0, multiply_digits=1000):
    sma_list_length = len(sma_list)
    # only get several rates, e.g., 5, not 24
    rates = get_last_n_ticks(symbol=symbol, timeframe=timeframe, start_position=start_position, tick_count=sma_list_length)

    # position = 0
    
    # rate_close_list = []
    # for rate in rates:
    #     rate_close_list.append(rate['close'])
        
    # #print(f"rate close list: {rate_close_list}")

    rate_data_list = []
    for count, rate in enumerate(rates):
        low = rate['low']
        high = rate['high']
        open = rate['open']
        close = rate['close']
        current_rate_data_dic = {
            "open": open,
            "high": high,
            "low": low,
            "close": close,
            "sma": sma_list[count]
        }

        rate_data_list.append(current_rate_data_dic)
    
    # # debug
    # for dic in rate_data_list:
    #     for key, item in dic.items():
    #         print(f"{key}: {item}")
    #     print()


    current_bid_price = rate_data_list[sma_list_length-1]['close']
    current_ask_price = mt5.symbol_info_tick(symbol).ask
    current_sma = rate_data_list[sma_list_length-1]['sma']
    # if current_bid_price > current_sma and # this is not needed, and may even cause issues. we don't care what the current price is at as long as the crossing tick closes >= its sma.
    # [added on 2/8/2023] the above line is WRONG! We need to compare the current price and the sma. If across_sma_from_below_to_above, we need the current price to be at least above sma.
    # or else, if it goes down below sma, and then further breaks the two candles' lows, it still detects as "across_sma_from_below_to_above", but at that moment, "across_sma_from_below_to_above"
    # is broken, and instead it's a below sma sell.
    if rate_data_list[sma_list_length-2]['close'] >= rate_data_list[sma_list_length-2]['sma'] and \
        rate_data_list[sma_list_length-2]['close'] > compare_two_and_get_higher(rate_data_list[sma_list_length-3]['high'], rate_data_list[sma_list_length-4]['high']) and \
        rate_data_list[sma_list_length-3]['high'] < rate_data_list[sma_list_length-3]['sma'] and \
        rate_data_list[sma_list_length-4]['high'] < rate_data_list[sma_list_length-4]['sma']:
        #4 is current, #3 is crossing from below to above, and close >= its sma. #3 passes #2 and #1's high, but at that moment, #3's price (namely the higher of #1 and #2 is not >= #3's sma
        # but, we see #3's close is >= #3's sma. so this is valid for a buy based on special rule crossing sma from below to above) 
        position = "across_sma_from_below_to_above"
    elif rate_data_list[sma_list_length-2]['close'] <= rate_data_list[sma_list_length-2]['sma'] and \
        rate_data_list[sma_list_length-2]['close'] < compare_two_and_get_lower(rate_data_list[sma_list_length-3]['low'], rate_data_list[sma_list_length-4]['low']) and \
        rate_data_list[sma_list_length-3]['low'] > rate_data_list[sma_list_length-3]['sma'] and \
        rate_data_list[sma_list_length-4]['low'] > rate_data_list[sma_list_length-4]['sma']:
        position = "across_sma_from_above_to_below"
    elif current_bid_price >= current_sma:
        position = "above"
    elif current_ask_price <= current_sma:
        position = "below"
    else:
        position = "mixed" # when spread is large. bid < sma, ask > sma.

    # calc points between price and sma
    if position in ["above", "across_sma_from_below_to_above"]:
        distance_in_points = (current_bid_price - current_sma) * multiply_digits
    elif position in ["below", "across_sma_from_above_to_below"]:
        # negative value
        distance_in_points = (current_ask_price - current_sma) * multiply_digits
    elif position == "mixed":
        distance_in_points = 0

    return position, distance_in_points

def check_retrace_when_long(symbol="BTCUSD", timeframe=mt5.TIMEFRAME_M5, start_position=0, tick_count=5): 
    retracement = False
    rates = get_last_n_ticks(symbol=symbol, timeframe=timeframe, start_position=start_position, tick_count=tick_count)

    for i in range(2, tick_count):
        # rates[i] #current_tick
        if rates[i]['low'] < rates[i-1]['low'] and rates[i]['low'] < rates[i-2]['low']:
            # rates[i] forms retracement
            retracement = True
            # print(f"rates[{i}] forms retracement. rates[{i}]['low'] is {rates[i]['low']} func check_retrace_when_long()")
    
    # print(f"retracement: {retracement}", end="\r")
    return retracement

def check_pause_when_long(symbol="BTCUSD", timeframe="TIMEFRAME_M5", start_position=0, tick_count=5):
    pause = False
    rates = get_last_n_ticks(symbol=symbol, timeframe=timeframe, start_position=start_position, tick_count=tick_count)

    for i in range(2, tick_count):
        if rates[i]['high'] < rates[i-2]['high'] and rates[i-1]['high'] < rates[i-2]['high']:
            pause = True
            # print(f"rates[{i}] and rates[{i-1}] forms pause, both of their high are lower than that of rates[{i-2}]. func check_pause_when_long")
            # print(f"rates[{i}]['high']: {rates[i]['high']}, rates[{i-1}]['high]: {rates[i-1]['high']}, rates[{i-2}]['high]: {rates[i-2]['high']}")

    # print(f"pause: {pause}", end="\r")
    return pause

def check_retrace_when_short(symbol="BTCUSD", timeframe=mt5.TIMEFRAME_M5, start_position=0, tick_count=5):
    retracement = False
    rates = get_last_n_ticks(symbol=symbol, timeframe=timeframe, start_position=start_position, tick_count=tick_count)

    for i in range(2, tick_count):
        if rates[i]['high'] > rates[i-1]['high'] and rates[i]['high'] > rates[i-2]['high']:
            retracement = True
            # print(f"rates[{i}] forms retracement. rates[{i}]['high'] is {rates[i]['high']} func check_retrace_when_short()")

    # print(f"retracement: {retracement}", end="\r")
    return retracement

def check_pause_when_short(symbol="BTCUSD", timeframe="TIMEFRAME_M5", start_position=0, tick_count=5):
    pause = False
    rates = get_last_n_ticks(symbol=symbol, timeframe=timeframe, start_position=start_position, tick_count=tick_count)

    for i in range(2, tick_count):
        if rates[i]['low'] > rates[i-2]['low'] and rates[i-1]['low'] > rates[i-2]['low']:
            pause = True
            # print(f"rates[{i}] and rates[{i-1}] forms pause, both of their lows are higher than that of rates[{i-2}]. func check_pause_when_short")
            # print(f"rates[{i}]['low']: {rates[i]['low']}, rates[{i-1}]['low']: {rates[i-1]['low']}, rates[{i-2}['low']: {rates[i-2]['low']}")

    # print(f"pause: {pause}", end="\r")
    return pause

# if retracement true
# !!! tick_count=7 instead of 5 !!!
# maybe need to set tick_count to higher, such as 7, so that we know the recent ideal entry
def find_which_tick_breaks_after_retracement_when_long(symbol="BTCUSD", timeframe=mt5.TIMEFRAME_M5, start_position=0, tick_count=7):
    # retracement = False
    rates = get_last_n_ticks(symbol=symbol, timeframe=timeframe, start_position=start_position, tick_count=tick_count)

    # a list of rates that forms retracement. so that we know the first and last rates that form retracement
    index_of_retracement_rates = []

    for i in range(2, tick_count):
        # rates[i] #current_tick
        if rates[i]['low'] < rates[i-1]['low'] and rates[i]['low'] < rates[i-2]['low']:
            # rates[i] forms retracement
            # retracement = True
            # print(f"rates[{i}] forms retracement. rates[{i}]['low'] is {rates[i]['low']} func find_which_tick_breaks_after_retracement_when_long")
            index_of_retracement_rates.append(i)
    
    if index_of_retracement_rates:
        # if len(index_of_retracement_rates) == 1:
        #     # rates[i] is the one that forms retracement
        #     i = index_of_retracement_rates[0]

        # else: # there are newer ticks form retracement
        #     # assign i with the last element, which is the newest tick that forms retracement
        #     i = index_of_retracement_rates[-1]
        #     # rates[i] is the one that forms retracement

        # no need to check length. just get the last element. if len is 1, it's the only one
        i = index_of_retracement_rates[-1]   

        while i < tick_count:
            # check if the retracement rate "rates[i]"" breaks previous two high
            if rates[i]['high'] > rates[i-1]['high'] and rates[i]['high'] > rates[i-2]['high']:
                index_of_tick_that_breaks = i
                ideal_entry_price = compare_two_and_get_higher(rates[i-1]['high'], rates[i-2]['high'])
                break
            i += 1

        return index_of_tick_that_breaks, ideal_entry_price
    else:
        # no retracement
        return None, None
        
def find_which_tick_breaks_after_retracement_when_short(symbol="BTCUSD", timeframe=mt5.TIMEFRAME_M5, start_position=0, tick_count=7):
    rates = get_last_n_ticks(symbol=symbol, timeframe=timeframe, start_position=start_position, tick_count=tick_count)

    # a list of rates that forms retracement. so that we know the first and last rates that form retracement
    index_of_retracement_rates = []

    for i in range(2, tick_count):
        if rates[i]['high'] > rates[i-1]['high'] and rates[i]['high'] > rates[i-2]['high']:
            # print(f"rates[{i}] forms retracement. rates[{i}]['high'] is {rates[i]['high']} func find_which_tick_breaks_after_retracement_when_short")      
            index_of_retracement_rates.append(i)

    if index_of_retracement_rates:
        i = index_of_retracement_rates[-1]

        while i < tick_count:
            if rates[i]['low'] < rates[i-1]['low'] and rates[i]['low'] < rates[i-2]['low']:
                index_of_tick_that_breaks = i
                ideal_entry_price = compare_two_and_get_lower(rates[i-1]['low'], rates[i-2]['low'])
                break
            i += 1

        return index_of_tick_that_breaks, ideal_entry_price

    else:
        return None, None

def find_which_tick_breaks_after_pause_when_long(symbol="USDJPY", timeframe=mt5.TIMEFRAME_M5, start_position=0, tick_count=7):
    rates = get_last_n_ticks(symbol=symbol, timeframe=timeframe, start_position=start_position, tick_count=tick_count)
    index_of_pause_rates = []

    for i in range(2, tick_count):
        if rates[i]['high'] < rates[i-2]['high'] and rates[i-1]['high'] < rates[i-2]['high']:
            index_of_pause_rates.append(i)
        
    if index_of_pause_rates:
        i = index_of_pause_rates[-1] + 1
        # i = index + 1 is because the tick cannot PAUSE and break at the same time. (however, it can RETRACE and break at the same time)
        while i < tick_count:
            if rates[i]['high'] > rates[i-2]['high'] and rates[i]['high'] > rates[i-1]['high']:
                index_of_tick_that_breaks = i
                ideal_entry_price = max(rates[i-2]['high'], rates[i-1]['high'])
                break
            i += 1
        return index_of_tick_that_breaks, ideal_entry_price
    
    else:
        return None, None

def find_which_tick_breaks_after_pause_when_short(symbol="USDJPY", timeframe=mt5.TIMEFRAME_M5, start_position=0, tick_count=7):  
    rates = get_last_n_ticks(symbol=symbol, timeframe=timeframe, start_position=start_position, tick_count=tick_count)
    index_of_pause_rates = []

    for i in range(2, tick_count):
        if rates[i]['low'] > rates[i-2]['low'] and rates[i-1]['low'] > rates[i-2]['low']:
            index_of_pause_rates.append(i)

    if index_of_pause_rates:
        i = index_of_pause_rates[-1] + 1
        # i = index + 1 is because the tick cannot PAUSE and break at the same time. (however, it can RETRACE and break at the same time)
        while i < tick_count:
            if rates[i]['low'] < rates[i-1]['low'] and rates[i]['low'] < rates[i-2]['low']:
                index_of_tick_that_breaks = i
                ideal_entry_price = min(rates[i-1]['low'], rates[i-2]['low'])
                break
            i += 1

        return index_of_tick_that_breaks, ideal_entry_price
    
    else:
        return None, None

def check_retrace_when_long_old(symbol="BTCUSD", timeframe=mt5.TIMEFRAME_M5, start_position=0, tick_count=5): 
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

    # if the current price broke previous two ticks' low and then went back up, breaking previous two ticks' high
    if tick_4_low < lower_price_tick_2_and_3:
        retracement = True

    # ERROR!!! need to pass *TWO* ticks
    # but there's a third situation
    # the 1 2'low < 0's low, but 3 fails to pass 1,2, but 4 passes
    # if lower_price_tick_1_and_2 < tick_0_low:
    #     retracement = True
    #     print("lower_price_tick_1_and_2 < tick_0_low")

    print(f"retracement: {retracement}")
    return retracement

def find_which_tick_completed_retracement(symbol, timeframe, start_position=0, tick_count=5):
    rates = get_last_n_ticks(symbol=symbol, timeframe=timeframe, start_position=start_position, tick_count=tick_count)
    tick_0_low = rates[0]['low']
    tick_1_low = rates[1]['low']
    tick_2_low = rates[2]['low']
    tick_3_low = rates[3]['low']
    tick_4_low = rates[4]['low'] # current tick
    
    if tick_4_low < compare_two_and_get_lower(tick_2_low, tick_3_low):
        # current_tick breaks its previous 2 ticks' low
        # the current price is the valid price for opening order
        pass
    elif tick_3_low < compare_two_and_get_lower(tick_2_low, tick_1_low):
        # the tick before the current tick breaks its previous 2 ticks' low 
        # the current price is the valid price for opening order
        pass
    
    pass
    

def check_retrace_when_short_old(symbol="BTCUSD", timeframe=mt5.TIMEFRAME_M5, start_position=0, tick_count=5): 
    retracement = False
    rates = get_last_n_ticks(symbol=symbol, timeframe=timeframe, start_position=start_position, tick_count=tick_count)
    tick_0_high = rates[0]['high']
    tick_1_high = rates[1]['high']
    tick_2_high = rates[2]['high']
    tick_3_high = rates[3]['high']
    tick_4_high = rates[4]['high']
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

    # if the current price broke previous two ticks' high and then went back down, breaking previous two ticks' low
    if tick_4_high > higher_price_tick_2_and_3:
        retracement = True

    # # ERROR!!! need to pass *TWO* ticks
    # # but there's a third situation
    # # the 1 2'high > 0's high, but 3 fails to pass 1,2, but 4 passes
    # if higher_price_tick_1_and_2 > tick_0_high:
    #     retracement = True
    #     print("higher_price_tick_1_and_2 > tick_0_high")

    print(f"retracement: {retracement}")
    return retracement




def check_pause_when_long_old(symbol="BTCUSD", timeframe="TIMEFRAME_M5", start_position=0, tick_count=5):
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

def check_pause_when_short_old(symbol="BTCUSD", timeframe=mt5.TIMEFRAME_M5, start_position=0, tick_count=5):
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
    # if retrace_when_long or pause_when_long:
    #     return True
    # else:
    #     return False
    if retrace_when_long and pause_when_long:
        return 'retrace_n_pause_when_long'
    elif retrace_when_long and pause_when_long == False:
        return 'ratrace_when_long'
    elif retrace_when_long == False and pause_when_long:
        return 'pause_when_long'
    else:
        return False
    

def check_retrace_or_pause_when_short(symbol="BTCUSD", timeframe=mt5.TIMEFRAME_M5, start_position=0, tick_count=5):
    retrace_when_short = check_retrace_when_short(symbol=symbol, timeframe=timeframe, start_position=start_position, tick_count=tick_count)
    pause_when_short = check_pause_when_short(symbol=symbol, timeframe=timeframe, start_position=start_position, tick_count=tick_count)
    # if retrace_when_short or pause_when_short:
    #     return True
    # else:
    #     return False
    if retrace_when_short and pause_when_short:
        return 'retrace_n_pause_when_short'
    elif retrace_when_short and pause_when_short == False:
        return 'ratrace_when_short'
    elif retrace_when_short == False and pause_when_short:
        return 'pause_when_short'
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

def check_consolidation_when_long(symbol="BTCUSD", timeframe=mt5.TIMEFRAME_M5, tick_count=30):
    rates = get_last_n_ticks(symbol=symbol, timeframe=timeframe, tick_count=tick_count)
    rates = np.flipud(rates)    

    
# not as we expected
# we are looking for newer to older, see the painting for elaboration
# ONLY when the current tick goes up passing two ticks, this is checked
def check_steps_when_long(symbol="BTCUSD", timeframe=mt5.TIMEFRAME_M5, tick_count=30):
    # we need high_0, low_0, high_1, low_1
    # from now to past
    # for long trades
    # first, the current tick's price passes previous two ticks's higher, store the lower low of the previous two ticks. This is low_1
    # * get the previous tick, check its high and low.
    #    a. check if its low is lower than its previous two, if so, then store the higher high of the previous two ticks as high_1, 
    #    b. check if its high is higher than its two ticks, if so, then store the lower low of the previous two ticks as low_0
    # if a not true, check b, if b not true, go on, check the previous one. until a not true, b is true.
    rates = get_last_n_ticks(symbol=symbol, timeframe=timeframe, tick_count=tick_count)

    rates = np.flipud(rates)
    # print(rates)

    # after reverse(), rates[0] is the newset/latest one. rates[1] is the one before that, rates[2] is before before that
    # as we only check_ladders when we found a price passing the previous two ticks, so the rates[0]['close'] is > previous two ticks' high (or < when selling)
    # so first, let's store the low_1
    # low_1 = compare_two_and_get_lower(rates[1]['low'], rates[2]['low'])
    # # find the nearest tick that goes pass its previous two ticks's high
    # for index, rate in enumerate(rates):
    #     # as rate[0] is the current one and it meets the requirements, but we don't count it.
    #     if index == 0:
    #         continue

    #     # as the price's high, low, close, open have formed, we will check the high, not the close
    #     # rate is the same as rates[index], as we enumerate
    #     # must do index < len(rates) - 2. otherwise, list out of range
    #     if index < len(rates) - 2 and rate['high'] > compare_two_and_get_higher(rates[index+1]['high'], rates[index+2]['high']):
    #         # ok, this seems to be a valid high, let's check if the tick after it breaks its low
    #         # actually I'm not sure if this check is needed, because if the price evetually gets to low_1, then there must be valid pass of previous two ticks' low.
    #         # and what's more, the current high is the earliest one, the highest, so even if there are more than one breaks afterwards, the is the one that is the highest, and the one we count for high_1
    #         high_1 = rate['high']
    #         high_1_index = index
    #         # must break. otherwise, it will look for earlier ones, and eventually finds the earliest one. but we just need the latest(nearest) one
    #         break


    try:
        for index in range(len(rates)):
            if index < len(rates) - 2 and rates[index]['low'] < compare_two_and_get_lower(rates[index+1]['low'], rates[index+2]['low']):
                low_1 = rates[index]['low']
                low_1_index = index
                break
        print(f"low_1: {low_1}, index: {low_1_index}")
            
        for index in range(low_1_index, len(rates)):
            if index < len(rates) - 2 and rates[index]['high'] > compare_two_and_get_higher(rates[index+1]['high'], rates[index+2]['high']):
                high_1 = rates[index]['high']
                high_1_index = index
                break # I forgot to break at first, that's why it finds the earliest one that passes the previous two's high. I was confused why it went so far away
        print(f"high_1: {high_1}, index: {high_1_index}")

        # start from high_1_index, check earlier ticks
        for index in range(high_1_index, len(rates)):
            if index < len(rates) - 2 and rates[index]['low'] < compare_two_and_get_lower(rates[index+1]['low'], rates[index+2]['low']):
                low_0 = rates[index]['low']
                low_0_index = index
                break
        print(f"low_0: {low_0}, index: {low_0_index}")

        for index in range(low_0_index, len(rates)):
            if index < len(rates) - 2 and rates[index]['high'] > compare_two_and_get_higher(rates[index+1]['high'], rates[index+2]['high']):
                high_0 = rates[index]['high']
                high_0_index = index
                break
        print(f"high_0: {high_0}, index: {high_0_index}")
        
        # print(f"high_0: {high_0}")
        # print(f"low_0: {low_0}")
        # print(f"high_1: {high_1}")
        # print(f"low_1: {low_1}")

        
        if high_0 > high_1 > low_0 > low_1:
            print("valid descending steps")
            # return high_0
            return high_1
        # elif high_0 >= high_1 and low_0 <= low_1:
        #     print("the price range is shrinking or not breaking, consolidating")
        #     return "shrinking"
        # else:
        #     return high_0

        # if high_0 > high_1 and low_0 < low_1:
        #     print("the price range is shrinking")
        else:
            print("doesn't meet high_0 > high_1 > low_0 > low_1") 
            return False

    except Exception as exception:
        print(traceback.format_exc())
        print(f"error info: {exception}")
        print(f"maybe did not find all the four points in previous {len(rates)} ticks\n \
            guess there isn't descending steps\n \
            please check\n")
        return False



# not as we expected
def check_steps_when_short(symbol="BTCUSD", timeframe=mt5.TIMEFRAME_M5, tick_count=30):
    rates = get_last_n_ticks(symbol=symbol, timeframe=timeframe, tick_count=tick_count)
    rates = np.flipud(rates)

    try:
        for index in range(len(rates)):
            if index < len(rates) - 2 and rates[index]['high'] > compare_two_and_get_higher(rates[index+1]['high'], rates[index+2]['high']):
                high_1 = rates[index]['high']
                high_1_index = index
                break
        print(f"high_1: {high_1}, index: {high_1_index}")
            
        for index in range(high_1_index, len(rates)):
            if index < len(rates) - 2 and rates[index]['low'] < compare_two_and_get_lower(rates[index+1]['low'], rates[index+2]['low']):
                low_1 = rates[index]['low']
                low_1_index = index
                break 
        print(f"low_1: {low_1}, index: {low_1_index}")

        # start from high_1_index, check earlier ticks
        for index in range(low_1_index, len(rates)):
            if index < len(rates) - 2 and rates[index]['high'] > compare_two_and_get_higher(rates[index+1]['high'], rates[index+2]['high']):
                high_0 = rates[index]['high']
                high_0_index = index
                break
        print(f"high_0: {high_0}, index: {high_0_index}")

        for index in range(high_0_index, len(rates)):
            if index < len(rates) - 2 and rates[index]['low'] < compare_two_and_get_lower(rates[index+1]['low'], rates[index+2]['low']):
                low_0 = rates[index]['low']
                low_0_index = index
                break
        print(f"low_0: {low_0}, index: {low_0_index}")
        
        
        if high_1 > high_0 > low_1 > low_0:
            print("valid ascending steps")
            # return low_0
            return low_1
            # need to pass the nearest low/high to break the ascending/desending steps

        else: # does not form steps
            print("doesn't meet high_1 > high_0 > low_1 > low_0")
            return False

    except Exception as exception:
        print(traceback.format_exc())
        print(f"error info: {exception}")
        print(f"maybe did not find all the four points in previous {len(rates)} ticks\n \
            guess there isn't descending steps\n \
            please check\n")
        return False

# not used
def find_dows_low_n_its_nearby_ticks(symbol="BTCUSD", timeframe=mt5.TIMEFRAME_M5, tick_count=12):
    rates = get_last_n_ticks(symbol=symbol, timeframe=timeframe, tick_count=tick_count)
    rates = np.flipud(rates) # so now it's from recent to past

    # so the current tick is the dow's low, this doesn't sound right for our "amending order" strategy
    # if we need to amend order, it means the current tick isn't passing pre ticks. so this condition probably won't happen
    if rates[0]['low'] < rates[1]['low'] and rates[0]['low'] < rates[2]['low']: # so this ensures it's a real retracement, no need to check retracement
        dows_low = rates[0]['low']

        dows_low_tick = {
            'low': rates[0]['low'],
            'high': rates[0]['high'],
        }

        tick_b4_it = {
            'low': rates[1]['low'],
            'high': rates[1]['high'],
        }

        tick_b4_b4_it = {
            'low': rates[2]['low'],
            'high': rates[2]['high'],
        }

        tick_location = 0

        ticks = {
            'dows_low_tick': dows_low_tick,
            'tick_b4_it': tick_b4_it,
            'tick_b4_b4_it': tick_b4_b4_it,
        }

        # return dows_low
        return tick_location, ticks
    
    else:
        for i in range(1, len(rates) - 2): # until the one before the last two, so that we have 2 ticks on its left
            # below line ensures this is dows low, actually this comparision seems not needed
            if rates[i]['low'] <= compare_two_and_get_lower(rates[i+1]['low'], rates[i-1]['low']) \
                and rates[i]['low'] < rates[i+1]['low'] and rates[i]['low'] < rates[i+2]['low']: # this line ensures there's a retracement
                dows_low = rates[i]['low']
                
                
                dows_low_tick = {
                    'low': rates[i]['low'],
                    'high': rates[i]['high'],
                }

                tick_b4_it = {
                    'low': rates[i+1]['low'],
                    'high': rates[i+1]['high'],
                }

                tick_b4_b4_it = {
                    'low': rates[i+2]['low'],
                    'high': rates[i+2]['high'],
                }

                tick_after_it = {
                    'low': rates[i-1]['low'],
                    'high': rates[i-1]['high'],
                }

                tick_after_after_it = {
                    'low': rates[i-2]['low'],
                    'high': rates[i-2]['high'],
                }

                tick_location = i

                ticks = {
                    'dows_low_tick': dows_low_tick,
                    'tick_b4_it': tick_b4_it,
                    'tick_b4_b4_it': tick_b4_b4_it,
                    "tick_after_it": tick_after_it,
                    "tick_after_after_it": tick_after_after_it,
                }

                # return dows_low
                return tick_location, ticks
            
    return None, None

# not used
def find_dows_high_n_its_nearby_ticks(symbol="BTCUSD", timeframe=mt5.TIMEFRAME_M5, tick_count=12):
    pass

# not used
def find_recent_ideal_entry_price(symbol="USDJPY", timeframe=mt5.TIMEFRAME_M30, tick_count=12):
    """find the most recent ideal entry price at the current moment"""
    
    # first find if there's mos recent pause, if so, then this is the entry price
    # a pause is when two ticks' lower low is higher than that of their previous tick
    # but next tick right after the pause may not break. but pause again, so need to check further

    # find most recent dow's low (high) first
    # need to get info including high, low of dows tick and ticks around it
    tick_location, ticks = find_dows_low_n_its_nearby_ticks(symbol=symbol, timeframe=timeframe, tick_count=tick_count)
    if tick_location and ticks:
        print(f"tick_location: {tick_location}")
        if tick_location != 0:
            # check if dows tick's high goes higher than previous 2 tick's high
            pass

    # check if the dow's low (high) forms a retracement (check if its low is lower than previous two ticks for buy; high higher than previous two ticks for sell)
    
    # if not, then check if there's a pause
    
    # if downtread, the ideal entry price should be:
    # check if the low in the dow's high tick is passing below previous two ticks,
    #  if so, it means the price forms dow's high and then goes back down to go below previous 2 ticks
    #  and the entry price should be the lower of the previous two ticks' lows.

    # if not, assume tick before dows high tick as 1, dows high tick as 2, tick after dows high as 3, then:
    # if 3's low is lower than the lower one of 1 and 2's low, then the lower one of 1 and 2's low is the ideal entry price for sell


    # if uptread, the ideal entry price should be:
    # check if the high in the dow's low's tick is passing the previous two ticks, 
    #   if so, it means the price forms dow's low at the current tick and then goes back up to break previous two ticks
    #   and the entry price should be the higher of the previous two ticks' highs.

    # if not, then check if the high of the tick after dow's low is higher than dow's low tick's high and the high of the tick before dows low tick
    #  if so, then entry price should be the higher one of dows low tick's high and the high of the tick before dows low tick
    pass


def confirm_symbol_n_timeframe(symbol, timeframe):
    while True:
        print(f"symbol: {symbol}")
        print(f"timeframe: {timeframe}")
        confirm_info = input("confirm symbol and timeframe [Y/n]")
        if confirm_info == "":
            break
        elif confirm_info.upper() == "N":
            input_symbol = input("change symbol to: ").upper()
            if input_symbol == "":
                pass
            else:
                symbol = input_symbol

            input_timeframe = input("change timeframe to: ")
            if input_timeframe == "":
                pass
            elif input_timeframe in ['daily']:
                timeframe = mt5.TIMEFRAME_D1
            elif input_timeframe in ['h4', '240']:
                timeframe = mt5.TIMEFRAME_H4
            elif input_timeframe in ['h1', '60']:
                timeframe = mt5.TIMEFRAME_H1
            elif input_timeframe in ['m30', '30']:
                timeframe = mt5.TIMEFRAME_M30
            elif input_timeframe in ['m15', '15']:
                timeframe = mt5.TIMEFRAME_M15
            elif input_timeframe in ['m5', '5']:
                timeframe = mt5.TIMEFRAME_M5
            elif input_timeframe in ['m1', '1']:
                timeframe = mt5.TIMEFRAME_M1

    return symbol, timeframe

def double_tick_strategy(symbol, type_filling, timeframe, sl_limit, sl_min, body_points_limit, points_gap_between_ideal_n_current_limit,
                         offset_limit, points_from_tp_limit, commission_per_lot, risk_ratio, risk_reward_ratio, tp_percent, 
                         check_timeframe_consistency, count_down_after_modifying_sl, check_above_or_below_sma, check_if_trading_time, check_sma_resistance,
                         pattern_list, pattern_index, added_points_to_sl, added_points_to_tp, fixed_tp, fixed_tp_in_points, hedge, 
                         adx_threshold, is_check_adx_threshold_enabled, is_check_adx_ascending_enabled,
                         broker_time_offset_hours_from_utc, news_df, trade_state):
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

    


    # flag for dragging the sl for only once, otherwise it will divide by two and divide again 
    # and eventually break even (when we want to just set the sl to half of the origin sl)
    # not wokring. what if order 1 is open, and modified, then the flag is set to 1, but then another order 2 is open, but flag is 1, so sl will be be modified
    # sl_modified = 0

    symbol, timeframe = confirm_symbol_n_timeframe(symbol, timeframe)
    # while True:
    #     print(f"symbol: {symbol}")
    #     print(f"timeframe: {timeframe}")
    #     confirm_info = input("confirm symbol and timeframe [Y/n]")
    #     if confirm_info == "":
    #         break
    #     elif confirm_info.upper() == "N":
    #         input_symbol = input("change symbol to: ").upper()
    #         if input_symbol == "":
    #             pass
    #         else:
    #             symbol = input_symbol

    #         input_timeframe = input("change timeframe to: ")
    #         if input_timeframe == "":
    #             pass
    #         elif input_timeframe in ['daily']:
    #             timeframe = mt5.TIMEFRAME_D1
    #         elif input_timeframe in ['h4', '240']:
    #             timeframe = mt5.TIMEFRAME_H4
    #         elif input_timeframe in ['h1', '60']:
    #             timeframe = mt5.TIMEFRAME_H1
    #         elif input_timeframe in ['m30', '30']:
    #             timeframe = mt5.TIMEFRAME_M30
    #         elif input_timeframe in ['m15', '15']:
    #             timeframe = mt5.TIMEFRAME_M15
    #         elif input_timeframe in ['m5', '5']:
    #             timeframe = mt5.TIMEFRAME_M5
    #         elif input_timeframe in ['m1', '1']:
    #             timeframe = mt5.TIMEFRAME_M1
    print(f"chosen_symbol: {symbol}")
    print(f"chosen_timeframe: {timeframe}")
    
    # need to be after confirmation of symbol and timeframe
    # so that the digits and muliply_digits are recalculated with the final settings
    digits = mt5.symbol_info(symbol).digits
    multiply_digits = 10 ** digits

    symbol_point = mt5.symbol_info(symbol).point

    while True:
        time.sleep(0.1) # this is under the whole while loop. so we check if it's trading time & current open position status every 0.1 second # this is moved to the start of the while loop to fix crazy spinning bars when DT happens BUT continues
        # is_trading_time = True
        if check_if_trading_time: 
            is_trading_time = check_if_its_trading_time()
        else:
            is_trading_time = True

        # the below if statement is not needed. see comment in below """ """ which lists 4 possibilities
        # if is_trading_time == False:
        #     continue

        """
        1. open_positions == 0 and is_trading_time == True:
        no open orders. trading time. look for orders
        2. open_positions == 0 and is_trading_time == False
        no open orders. not trading time. peace. do nothing
        3. open_positions != 0 and and is_trading_time == True
        there's an open order. trading time. monitor the tp of the open order
        3. open_positions != 0 and and is_trading_time == False
        there's an open order. not trading time. monitor the tp of the open order
        """

        # open_positions = check_open_positions() # check open positions of any symbol
        current_symbol_open_positions = check_current_symbol_open_positions(symbol=symbol)
        # if open_positions == 0 and is_trading_time == True:
        
        # if len(current_symbol_open_positions) < 2 and is_trading_time == True and current_price != open_positions[0]['price_open']:
        if len(current_symbol_open_positions) == 0:
            look_for_trades = True
            look_for_sell_or_buy = "all"
        elif hedge == True and len(current_symbol_open_positions) == 1 and abs(current_symbol_open_positions[0].time - mt5.symbol_info(symbol).time) > 60:
                # and abs(current_symbol_open_positions[0].price_open - get_last_n_ticks(symbol=symbol, timeframe=timeframe, tick_count=1)[0][4]) * multiply_digits > points_gap_between_ideal_n_current_limit):
                # there are issues on the gap check. 1. on demo we accidentally opened a second sell on H4 after 10 minutes at almost the same price, 1.09024, 1.09043. 2. if price reverses, it can theoretically break at the same price, but in an opposite direction and at a later time. 
                # Therefore, we abandon this condition. and add another filter: look_for_sell_or_buy
                # manually calc (don't bother, as we can use the serve time mt5.symbol)info.time): current time local time minus 6 hours (int(time.time())-6 * 60 * 60)). if the order is at the same price, and the the same time, it means maybe we retraced back, we don't want to open it again. even if the time has passed 60 seconds
            look_for_trades = True
            if current_symbol_open_positions[0].type == 0:
                # the first position is buy, then we look for sell to hedge
                look_for_sell_or_buy = "sell"
            elif current_symbol_open_positions[0].type == 1:
                # the first position is sell, then we look for buy to hedge
                look_for_sell_or_buy = "buy"

        else:
            # # debug
            # print(f"current_symbol_open_positions[0].time: {current_symbol_open_positions[0].time}")
            # print(f"mt5.symbol_info(symbol).time: {mt5.symbol_info(symbol).time}")
            # print(f"time gap: {abs(current_symbol_open_positions[0].time - mt5.symbol_info(symbol).time)}")
            # print(f"price gap: {abs(current_symbol_open_positions[0].price_open - get_last_n_ticks(symbol=symbol, timeframe=timeframe, tick_count=1)[0][4]) * multiply_digits}")
            # debug
            look_for_trades = False
            look_for_sell_or_buy = False

        if is_trading_time == True and look_for_trades == True:
            # rates <class 'numpy.ndarray'>
            rates = get_last_n_ticks(symbol=symbol, timeframe=timeframe, tick_count=3)
            # print(f"rates: {rates}")
            current_price = rates[2][4] 
            # this should be the bid price. need to verify

            # bid_price = mt5.symbol_info(symbol).bid
            ask_price = mt5.symbol_info_tick(symbol).ask
            
            # print(f"current_price: {current_price}")
            # print(f"bid_price: {bid_price}")
            # print(f"ask_price: {ask_price}")
            """
            tested output:
            current_price: 129.586
            bid_price: 129.586
            ask_price: 129.599

            current_price: 0.65285
            bid_price: 0.65285
            ask_price: 0.653
            """

            # get the higher price of the previous one and two ticks
            tick_one_high = rates[0][2]
            tick_two_high = rates[1][2]
            higher_price = compare_two_and_get_higher(tick_one_high, tick_two_high)

            # get the lower price of the previous one and two ticks
            tick_one_low = rates[0][3]
            tick_two_low = rates[1][3]
            lower_price = compare_two_and_get_lower(tick_one_low, tick_two_low)

            tick_two_close = rates[1]['close']
            tick_two_open = rates[1]['open']

            #sma = calculate_current_sma(symbol="BTCUSD", sma_length=24)
            
            # sma_list = calculate_sma_of_latest_n_ticks(symbol=symbol, timeframe=timeframe, sma_length=24, sma_count=5)
            
            # # # v1 
            # # above_or_below_sma = if_above_or_below_sma(sma_list, timeframe=timeframe, symbol=symbol, start_position=0)
            # # print(f"above or below sma: {above_or_below_sma}")

            # # # v2
            # # above_or_below_sma = check_each_tick_close_price_above_or_below_sma(sma_list, timeframe=timeframe, symbol=symbol, start_position=0)
            # # # print(f"above or below sma: {above_or_below_sma}")

            # # v3
            # above_or_below_sma, dip_current_timeframe = check_price_sma_position(sma_list, timeframe=timeframe, symbol=symbol, start_position=0, multiply_digits=multiply_digits)

            # print(f"    {above_or_below_sma}", end="\r", flush=True)
            # print()
            # print(above_or_below_sma)
            # print()

            sma_list_m5 = calculate_sma_of_latest_n_ticks(symbol=symbol, timeframe=mt5.TIMEFRAME_M5, sma_length=24, sma_count=5)
            above_or_below_sma_m5, dip_m5 = check_price_sma_position(sma_list_m5, timeframe=mt5.TIMEFRAME_M5, symbol=symbol, start_position=0, multiply_digits=multiply_digits) # dip is short for distance in points

            sma_list_m15 = calculate_sma_of_latest_n_ticks(symbol=symbol, timeframe=mt5.TIMEFRAME_M15, sma_length=24, sma_count=5)
            above_or_below_sma_m15, dip_m15 = check_price_sma_position(sma_list_m15, timeframe=mt5.TIMEFRAME_M15, symbol=symbol, start_position=0, multiply_digits=multiply_digits)

            sma_list_m30 = calculate_sma_of_latest_n_ticks(symbol=symbol, timeframe=mt5.TIMEFRAME_M30, sma_length=24, sma_count=5)
            above_or_below_sma_m30, dip_m30 = check_price_sma_position(sma_list_m30, timeframe=mt5.TIMEFRAME_M30, symbol=symbol, start_position=0, multiply_digits=multiply_digits)

            sma_list_h1 = calculate_sma_of_latest_n_ticks(symbol=symbol, timeframe=mt5.TIMEFRAME_H1, sma_length=24, sma_count=5)
            above_or_below_sma_h1, dip_h1 = check_price_sma_position(sma_list_h1, timeframe=mt5.TIMEFRAME_H1, symbol=symbol, start_position=0, multiply_digits=multiply_digits)

            sma_list_h4 = calculate_sma_of_latest_n_ticks(symbol=symbol, timeframe=mt5.TIMEFRAME_H4, sma_length=24, sma_count=5)
            above_or_below_sma_h4, dip_h4 = check_price_sma_position(sma_list_h4, timeframe=mt5.TIMEFRAME_H4, symbol=symbol, start_position=0, multiply_digits=multiply_digits)


            # compare current timeframe and assign the current above_or_below_sma, so that it does not need to be recalculated
            # check timeframe
            if timeframe == mt5.TIMEFRAME_M1:
                # usually we don't use this, so calculate only when it's selected
                sma_list_m1 = calculate_sma_of_latest_n_ticks(symbol=symbol, timeframe=mt5.TIMEFRAME_M1, sma_length=24, sma_count=5)
                above_or_below_sma_m1, dip_m1 = check_price_sma_position(sma_list_m1, timeframe=mt5.TIMEFRAME_M1, symbol=symbol, start_position=0, multiply_digits=multiply_digits) # dip is short for distance in points
                above_or_below_sma = above_or_below_sma_m1
            elif timeframe == mt5.TIMEFRAME_M5:
                above_or_below_sma = above_or_below_sma_m5
            elif timeframe == mt5.TIMEFRAME_M15:
                above_or_below_sma = above_or_below_sma_m15
                # print("above_or_below_sma = above_or_below_sma_m15")
            elif timeframe == mt5.TIMEFRAME_M30:
                above_or_below_sma = above_or_below_sma_m30
                # print("above_or_below_sma = above_or_below_sma_m30")
            elif timeframe == mt5.TIMEFRAME_H1:
                above_or_below_sma = above_or_below_sma_h1
            elif timeframe == mt5.TIMEFRAME_H4:
                above_or_below_sma = above_or_below_sma_h4

            # print()
            # print(timeframe)
            # print(f"{above_or_below_sma}")
            # print()

            ###############print a spinning circle ##############
            current_pattern = pattern_list[pattern_index]
            pattern_index += 1
            if pattern_index == len(pattern_list):
                pattern_index = 0

            # print(f"  {current_pattern}", end="\r", flush=True)
            # print(f"  {current_pattern}", end="  ", flush=True)
            ###############print a spinning circle ##############

            # print(f"{above_or_below_sma}", end="\r", flush=True)

            # print sma and spinning bar in a single line, this helps resolve the flickering spnning bar.
            print(f"  {current_pattern}  M5: {above_or_below_sma_m5} {dip_m5:.0f}, M15: {above_or_below_sma_m15} {dip_m15:.0f}, M30: {above_or_below_sma_m30} {dip_m30:.0f}, H1: {above_or_below_sma_h1} {dip_h1:.0f}, H4: {above_or_below_sma_h4} {dip_h4:.0f}  {current_pattern}  *{symbol}|{timeframe}*", end="\r")#, flush=True)
            
            # if current_price > higher_price, and we are above the 24sma, and there's a retracement
            if current_price > higher_price:
                # print("buy")
                # sl = current_price * 1000 - rates[1][3] * 1000  # USDJPY
                # BTC digits -> 2   USDJPY digits -> 3
                # digits = mt5.symbol_info(symbol).digits # BTC digits -> 2         mt5.symbol_info(symbol).xxx, not mt5.symbol_info_tick(symbol).xxx
                # multiply_digits = 10 ** digits
                # sl is in points, /10 if needed to convert to pips
                #### sl previous two ticks' low ###
                #### sl = current_price * multiply_digits - lower_price * multiply_digits  # BTC ####
                ###################################
                # sl = current_price * 100 - lower_price * 100  # BTC
                
                # check if we should look for a sell order or a buy order
                # print(f"look_for_sell_or_buy: {look_for_sell_or_buy}")
                if look_for_sell_or_buy in {"all", "buy"}:
                    pass
                else:
                    continue
                
                if check_above_or_below_sma:
                    if above_or_below_sma in {"above"}:
                        pass
                    else:
                        # need to be above but not above, doesn't meet requirements. abort
                        continue
                else:
                    pass


                if check_timeframe_consistency:
                    # check if timeframes {timeframe}, H1, and H4 are in the same trend.

                    if timeframe == mt5.TIMEFRAME_M5:
                        #if above_or_below_sma_m15 == "above" and above_or_below_sma_m30 == "above" and above_or_below_sma_h1 == "above":# and above_or_below_sma_h4 == "above": 
                        # we have to consider when we are CROSSING the sma, sitting at the next running candle right after the key crossing candle which has closed. At that moment the above_or_below_sma_xxx is not above or below, but across_sma_from_below_to_above, but it's actually still above or below
                        if above_or_below_sma_m15 in {"above", "across_sma_from_below_to_above"} and above_or_below_sma_m30 in {"above", "across_sma_from_below_to_above"} and above_or_below_sma_h1 in {"above", "across_sma_from_below_to_above"}:
                            print("trading on m5. m5 m15 m30 h1 all identical. ok")
                            pass
                        else:
                            print(f"timeframes are not identical.")
                            print(f"M5: {above_or_below_sma_m5}, M15: {above_or_below_sma_m15}, M30: {above_or_below_sma_m30}, H1: {above_or_below_sma_h1}, H4: {above_or_below_sma_h4}")
                            continue
                    elif timeframe == mt5.TIMEFRAME_M15:
                        if above_or_below_sma_m30 in {"above", "across_sma_from_below_to_above"} and above_or_below_sma_h1 in {"above", "across_sma_from_below_to_above"}:# and above_or_below_sma_h4 == "above":
                            print("trading on m15. m15 m30 h1 all identical. ok")
                            pass
                        else:
                            print(f"timeframes are not identical.")
                            print(f"M5: {above_or_below_sma_m5}, M15: {above_or_below_sma_m15}, M30: {above_or_below_sma_m30}, H1: {above_or_below_sma_h1}, H4: {above_or_below_sma_h4}")
                            continue
                    elif timeframe == mt5.TIMEFRAME_M30:
                        if above_or_below_sma_h1 in {"above", "across_sma_from_below_to_above"}:# and above_or_below_sma_h4 == "above":
                            print("trading on m30. m30 h1 all identical. ok")
                            pass
                        else:
                            print(f"timeframes are not identical.")
                            print(f"M5: {above_or_below_sma_m5}, M15: {above_or_below_sma_m15}, M30: {above_or_below_sma_m30}, H1: {above_or_below_sma_h1}, H4: {above_or_below_sma_h4}")
                            # print(f"{timeframe}: {above_or_below_sma}, H1: {above_or_below_sma_h1}, H4: {above_or_below_sma_h4}")
                            continue
                

                ####### find SL ########
                # dows_low = find_dows_low(symbol=symbol, timeframe=timeframe, tick_count=12)
                dows_low = find_dows_low(symbol=symbol, timeframe=timeframe, tick_count=4)
                if dows_low:
                    sl = current_price * multiply_digits - dows_low * multiply_digits
                else:
                    # print(f"didn't find dows_low in previous 4 ticks, will get last 3 ticks and use the first tick's low as dow's low")
                    dows_low = tick_one_low
                    sl = current_price * multiply_digits - dows_low * multiply_digits
                # else:
                #     print(f"didn't find dows_low in previous ticks, won't open order")
                #     continue
                ####### ######## ########

                # make sl one pip larger. because we want the sl price to be one pip below or above dows high and low
                sl = sl + added_points_to_sl
                dows_low = (dows_low * multiply_digits - added_points_to_sl) / multiply_digits # 141.350 * 1000 - 10 is 141350 - 10, which is 141340. then 141340 / 1000 is 141.340

                # hard-coded for USD/JPY
                # if sl >= sl_limit and symbol == "USDJPY": # if sl > 300 points, or 30 pips
                    # print(f"sl is {sl} points. too large. aborted.")
                    # continue
                # if symbol in {"USDJPY", "EURUSD"}:
                #     if sl > sl_limit:  # if sl > 300 points, or 30 pips
                #         print(f"sl is {sl} points. too large, > sl_limit {sl_limit}, aborted.")
                #         continue
                #     elif sl < sl_min:
                #         print(f"sl is {sl} points. too small, < sl_min {sl_min}, aborted.")
                #         continue
                if sl > sl_limit:  # if sl > 300 points, or 30 pips
                    # print(f"sl is {sl} points. too large, > sl_limit {sl_limit}, aborted.")
                    continue
                elif sl < sl_min:
                    # print(f"sl is {sl} points. too small, < sl_min {sl_min}, aborted.")
                    continue

                # if the price passes two ticks, but far from ideal opening position. (This typically happens when the price moves very fast and hits TP, and the entry and the exit is on the same tick)
                actual_offset = multiply_digits * abs(current_price - higher_price)
                if actual_offset > offset_limit:
                    # print(f"actual_offset is {actual_offset}, exceeded offset_limit: {offset_limit} points. not opening tickets")
                    continue
                
                retrace_or_pause_when_long = check_retrace_or_pause_when_long(symbol=symbol, timeframe=timeframe, start_position=0, tick_count=5)

                if retrace_or_pause_when_long is False:
                    continue

                elif retrace_or_pause_when_long in {'retrace_n_pause_when_long', 'ratrace_when_long'}:
                    # find the ideal entry price, which is the recent first breaking price, and compare it with the current price. if it's not the same, it indicates that we are not in the earliest ideal entry
                    index_of_tick_that_breaks, ideal_entry_price = find_which_tick_breaks_after_retracement_when_long(symbol=symbol, timeframe=timeframe, start_position=0, tick_count=7)
                    if index_of_tick_that_breaks: # this seems redundant as it should always be true
                        # print(f"index of tick that breaks after_retracement_when_long: {index_of_tick_that_breaks}")
                        # print(f"ideal entry price: {ideal_entry_price}")
                        # print(f"current bid price: {current_price}")
                        points_gap_between_ideal_n_current = abs((current_price - ideal_entry_price) * multiply_digits)
                        # print(f"points gap between ideal entry price and current bid price: {points_gap_between_ideal_n_current}")
                        if points_gap_between_ideal_n_current > points_gap_between_ideal_n_current_limit:
                            # print(f"points_gap_between_ideal_n_current {points_gap_between_ideal_n_current} is greater than points_gap_between_ideal_n_current_limit {points_gap_between_ideal_n_current_limit}")
                            continue
                elif retrace_or_pause_when_long == 'pause_when_long':
                    index_of_tick_that_breaks, ideal_entry_price = find_which_tick_breaks_after_pause_when_long(symbol=symbol, timeframe=timeframe, start_position=0, tick_count=7)
                    if index_of_tick_that_breaks: # this seems redundant as it should always be true
                        # print(f"index of tick that breaks after_pause_when_long: {index_of_tick_that_breaks}")
                        # print(f"ideal entry price: {ideal_entry_price}")
                        # print(f"current bid price: {current_price}")
                        points_gap_between_ideal_n_current = abs((current_price - ideal_entry_price) * multiply_digits)
                        # print(f"points gap between ideal entry price and current bid price: {points_gap_between_ideal_n_current}")
                        if points_gap_between_ideal_n_current > points_gap_between_ideal_n_current_limit:
                            # print(f"points_gap_between_ideal_n_current {points_gap_between_ideal_n_current} is greater than points_gap_between_ideal_n_current_limit {points_gap_between_ideal_n_current_limit}")
                            continue


                # check if SMAs in different timeframes are standing in the way towards our tp
                if check_sma_resistance:

                    if fixed_tp:
                        tp = fixed_tp_in_points
                    else:
                        # sl is sl points. need to add it to entry price to get tp price
                        tp = sl / risk_reward_ratio # tp in points
                        tp = int(tp * tp_percent)
                        tp_price = ask_price + tp * symbol_point

                    if timeframe == mt5.TIMEFRAME_M30:
                        if current_price < sma_list_h4[-1] < tp_price:
                            print(f"h4 sma {sma_list_h4[-1]} is in the way between entry price {current_price} and tp_price {tp_price}. abort")
                            continue
                        elif current_price < sma_list_h1[-1] < tp_price:
                            print(f"h1 sma {sma_list_h1[-1]} is in the way between entry price {current_price} and tp_price {tp_price}. abort")
                            continue
                        elif current_price < sma_list_m15[-1] < tp_price:
                            print(f"m15 sma {sma_list_m15[-1]} is in the way between entry price {current_price} and tp_price {tp_price}. abort")
                            continue
                        else:
                            print("h4, h1, m15 smas are not in the way between entry price and tp_price")
                            print(f"entry price {current_price}, tp_price {tp_price}")
                            print(f"h4 sma {sma_list_h4[-1]}")
                            print(f"h1 sma {sma_list_h1[-1]}")
                            print(f"m15 sma {sma_list_m15[-1]}")
                    elif timeframe == mt5.TIMEFRAME_H1:
                        if current_price < sma_list_h4[-1] < tp_price:
                            print(f"h4 sma {sma_list_h4[-1]} is in the way between entry price {current_price} and tp_price {tp_price}. abort")
                            continue
                        elif current_price < sma_list_m30[-1] < tp_price:
                            print(f"m30 sma {sma_list_m30[-1]} is in the way between entry price {current_price} and tp_price {tp_price}. abort")
                            continue
                        elif current_price < sma_list_m15[-1] < tp_price:
                            print(f"m15 sma {sma_list_m15[-1]} is in the way between entry price {current_price} and tp_price {tp_price}. abort")
                            continue
                        else:
                            print("h4, m30, m15 smas are not in the way between entry price and tp_price")
                            print(f"entry price {current_price}, tp_price {tp_price}")
                            print(f"h4 sma {sma_list_h4[-1]}")
                            print(f"m30 sma {sma_list_m30[-1]}")
                            print(f"m15 sma {sma_list_m15[-1]}")

                # # the calculation seems not right. 
                # # calculation complex high cpu. put it after calculating actual_offset
                # high_1 = check_steps_when_long(symbol=symbol, timeframe=timeframe, tick_count=30)
                # if high_1:
                #     if current_price > high_1:
                #         print(f"price goes above high_1 {high_1}, descending steps fail. OK to place order.")
                #     else:
                #         print(f"price doesn't go above high_1 {high_1}, descending steps are growing. not OK to place order.")
                #         continue # skip the open request func and all below code. go to the next loop
                # else:
                #     print("no descending steps. OK to place order.")


                
                if is_check_adx_threshold_enabled:
                    # this checks if adx is above 25
                    check_adx_result = check_if_adx_meets_requirements(symbol=symbol, timeframe=timeframe, adx_threshold=adx_threshold)
                    if check_adx_result == False:
                        continue
                if is_check_adx_ascending_enabled:
                    # this checks if adx is ascending
                    check_adx_ascending_res = check_adx_ascending(symbol=symbol, timeframe=timeframe, n=2) # previously working setting was that n was set to 3
                    if check_adx_ascending_res == False:
                        continue

                

                # check if there is news ahead or if we are after news
                news_exist = get_news_data.trades_blocker_to_avoid_news(60, news_df)
                if news_exist:
                    continue
                

                open_request(sl_price=dows_low, type="buy", sl=sl, symbol=symbol, type_filling=type_filling, commission_per_lot=commission_per_lot, risk_ratio=risk_ratio, risk_reward_ratio=risk_reward_ratio, 
                             tp_percent=tp_percent, added_points_to_sl=added_points_to_sl, added_points_to_tp=added_points_to_tp, fixed_tp=fixed_tp, fixed_tp_in_points=fixed_tp_in_points)
                # continue # if we opened an order, we go back to the beginning of the loop, we don't sleep
            elif ask_price < lower_price: # if current_price < lower_price and we are below the 25sma
                # print("sell")

                # # check if timeframes {timeframe}, H1, and H4 are in the same trend.
                # if above_or_below_sma_h1 == "below":# and above_or_below_sma_h4 == "below":
                #     pass
                # else:
                #     print(f"timeframes are not identical.")
                #     print(f"{timeframe}: {above_or_below_sma}, H1: {above_or_below_sma_h1}, H4: {above_or_below_sma_h4}")
                #     continue

                # check if we should look for a sell order or a buy order
                # print(f"look_for_sell_or_buy: {look_for_sell_or_buy}")
                if look_for_sell_or_buy in {"all", "sell"}:
                    pass
                else:
                    continue

                if check_above_or_below_sma:
                    if above_or_below_sma in {"below"}:
                        pass
                    else:
                        # need to be above but not above, doesn't meet requirements. abort
                        continue
                else:
                    pass


                if check_timeframe_consistency:
                    # check timeframe, and make sure higher timeframes' trends are identical with that of the current timeframe
                    if timeframe == mt5.TIMEFRAME_M5:
                        if above_or_below_sma_m15 in {"below", "across_sma_from_above_to_below"} and above_or_below_sma_m30 in {"below", "across_sma_from_above_to_below"} and above_or_below_sma_h1 in {"below", "across_sma_from_above_to_below"}:# and above_or_below_sma_h4 == "above":
                            print("trading on m5. m5 m15 m30 h1 all identical. ok")
                            pass
                        else:
                            print(f"timeframes are not identical.")
                            print(f"M5: {above_or_below_sma_m5}, M15: {above_or_below_sma_m15}, M30: {above_or_below_sma_m30}, H1: {above_or_below_sma_h1}, H4: {above_or_below_sma_h4}")
                            continue
                    elif timeframe == mt5.TIMEFRAME_M15:
                        if above_or_below_sma_m30 in {"below", "across_sma_from_above_to_below"} and above_or_below_sma_h1 in {"below", "across_sma_from_above_to_below"}:# and above_or_below_sma_h4 == "above":
                            print("trading on m15. m15 m30 h1 all identical. ok")
                            pass
                        else:
                            print(f"timeframes are not identical.")
                            print(f"M5: {above_or_below_sma_m5}, M15: {above_or_below_sma_m15}, M30: {above_or_below_sma_m30}, H1: {above_or_below_sma_h1}, H4: {above_or_below_sma_h4}")
                            continue
                    elif timeframe == mt5.TIMEFRAME_M30:
                        if above_or_below_sma_h1 in {"below", "across_sma_from_above_to_below"}:# and above_or_below_sma_h4 == "above":
                            print("trading on m30. m30 h1 all identical. ok")
                            pass
                        else:
                            print(f"timeframes are not identical.")
                            print(f"M5: {above_or_below_sma_m5}, M15: {above_or_below_sma_m15}, M30: {above_or_below_sma_m30}, H1: {above_or_below_sma_h1}, H4: {above_or_below_sma_h4}")
                            # print(f"{timeframe}: {above_or_below_sma}, H1: {above_or_below_sma_h1}, H4: {above_or_below_sma_h4}")
                            continue



                ##### find SL #####
                # second_tick_high-current_price
                # sl = rates[1][2] * 1000 - current_price * 1000  # USDJPY
                # digits = mt5.symbol_info(symbol).digits
                # multiply_digits = 10 ** digits
                #sl = higher_price * multiply_digits - current_price * multiply_digits  # BTC
                # dows_high = find_dows_high(symbol=symbol, timeframe=timeframe, tick_count=12)
                dows_high = find_dows_high(symbol=symbol, timeframe=timeframe, tick_count=4)
                if dows_high:
                    sl = dows_high * multiply_digits - ask_price * multiply_digits
                else:
                    # print(f"didn't find dows_high in previous 4 ticks, will get last 3 ticks and use the first tick's high as dow's high")
                    dows_high = tick_one_high
                    sl = dows_high * multiply_digits - ask_price * multiply_digits
                    
                # sl = higher_price * 100 - current_price * 100  # BTC
                ##### ##### #####

                # make sl one pip larger. because we want the sl price to be one pip below or above dows high and low
                sl = sl + added_points_to_sl
                dows_high = (dows_high * multiply_digits + added_points_to_sl) / multiply_digits # 141.350 * 1000 - 10 is 141350 - 10, which is 141340. then 141340 / 1000 is 141.340
                

                # check if sl too large too small
                if sl > sl_limit:  # if sl > 300 points, or 30 pips
                    # print(f"sl is {sl} points. too large, > sl_limit {sl_limit}, aborted.")
                    continue
                elif sl < sl_min:
                    # print(f"sl is {sl} points. too small, < sl_min {sl_min}, aborted.")
                    continue

                actual_offset = multiply_digits * abs(ask_price - lower_price)
                if actual_offset > offset_limit:
                    # print(f"actual_offset is {actual_offset}, exceeded offset_limit: {offset_limit} points. not opening tickets")
                    continue
                
                retrace_or_pause_when_short = check_retrace_or_pause_when_short(symbol=symbol, timeframe=timeframe, start_position=0, tick_count=5)
                if retrace_or_pause_when_short is False:
                    continue
                elif retrace_or_pause_when_short in {'retrace_n_pause_when_short', 'ratrace_when_short'}:
                    index_of_tick_that_breaks, ideal_entry_price = find_which_tick_breaks_after_retracement_when_short(symbol=symbol, timeframe=timeframe, start_position=0, tick_count=7)
                    if index_of_tick_that_breaks:
                        # print(f"tick_breaks_after_retracement_when_short: {index_of_tick_that_breaks}")
                        # print(f"ideal entry price: {ideal_entry_price}")
                        # print(f"current ask price: {ask_price}")
                        points_gap_between_ideal_n_current = abs((ask_price - ideal_entry_price) * multiply_digits)
                        # print(f"points gap between ideal entry price and current ask price: {points_gap_between_ideal_n_current}")
                        if points_gap_between_ideal_n_current > points_gap_between_ideal_n_current_limit:
                            # print(f"points_gap_between_ideal_n_current {points_gap_between_ideal_n_current} is greater than points_gap_between_ideal_n_current_limit {points_gap_between_ideal_n_current_limit}")
                            continue
                elif retrace_or_pause_when_short == 'pause_when_short':
                    index_of_tick_that_breaks, ideal_entry_price = find_which_tick_breaks_after_pause_when_short(symbol=symbol, timeframe=timeframe, start_position=0, tick_count=7)
                    if index_of_tick_that_breaks:
                        # print(f"tick_breaks_after_pause_when_short: {index_of_tick_that_breaks}")
                        # print(f"ideal entry price: {ideal_entry_price}")
                        # print(f"current ask price: {ask_price}")
                        points_gap_between_ideal_n_current = abs((ask_price - ideal_entry_price) * multiply_digits)
                        # print(f"points gap between ideal entry price and current ask price: {points_gap_between_ideal_n_current}")
                        if points_gap_between_ideal_n_current > points_gap_between_ideal_n_current_limit:
                            # print(f"points_gap_between_ideal_n_current {points_gap_between_ideal_n_current} is greater than points_gap_between_ideal_n_current_limit {points_gap_between_ideal_n_current_limit}")
                            continue



                # check if SMAs in different timeframes are standing in the way towards our tp
                if check_sma_resistance:
                    
                    if fixed_tp:
                        tp = fixed_tp_in_points
                    else:
                        # sl is sl points. need to add it to entry price to get tp price
                        tp = sl / risk_reward_ratio # tp in points
                        tp = int(tp * tp_percent)
                        tp_price = ask_price - tp * symbol_point

                    if timeframe == mt5.TIMEFRAME_M30:
                        if ask_price > sma_list_h4[-1] > tp_price:
                            print(f"h4 sma {sma_list_h4[-1]} is in the way between entry price {ask_price} and tp_price {tp_price}. abort")
                            continue
                        elif ask_price > sma_list_h1[-1] > tp_price:
                            print(f"h1 sma {sma_list_h1[-1]} is in the way between entry price {ask_price} and tp_price {tp_price}. abort")
                            continue
                        elif ask_price > sma_list_m15[-1] > tp_price:
                            print(f"m15 sma {sma_list_m15[-1]} is in the way between entry price {ask_price} and tp_price {tp_price}. abort")
                            continue
                        else:
                            print("h4, h1, m15 smas are not in the way between entry price and tp_price")
                            print(f"entry price {ask_price}, tp_price {tp_price}")
                            print(f"h4 sma {sma_list_h4[-1]}")
                            print(f"h1 sma {sma_list_h1[-1]}")
                            print(f"m15 sma {sma_list_m15[-1]}")
                    elif timeframe == mt5.TIMEFRAME_H1:
                        if ask_price > sma_list_h4[-1] > tp_price:
                            print(f"h4 sma {sma_list_h4[-1]} is in the way between entry price {ask_price} and tp_price {tp_price}. abort")
                            continue
                        elif ask_price > sma_list_m30[-1] > tp_price:
                            print(f"m30 sma {sma_list_m30[-1]} is in the way between entry price {ask_price} and tp_price {tp_price}. abort")
                            continue
                        elif ask_price > sma_list_m15[-1] > tp_price:
                            print(f"m15 sma {sma_list_m15[-1]} is in the way between entry price {ask_price} and tp_price {tp_price}. abort")
                            continue
                        else:
                            print("h4, m30, m15 smas are not in the way between entry price and tp_price")
                            print(f"entry price {ask_price}, tp_price {tp_price}")
                            print(f"h4 sma {sma_list_h4[-1]}")
                            print(f"m30 sma {sma_list_m30[-1]}")
                            print(f"m15 sma {sma_list_m15[-1]}")



                # low_1 = check_steps_when_short(symbol=symbol, timeframe=timeframe, tick_count=30)
                # if low_1:
                #     if current_price < low_1:
                #         print(f"price goes below low_1 {low_1}, ascending steps fail. OK to place order.")
                #     else:
                #         print(f"price doesn't go below low_1 {low_1}, ascending steps are growing. not OK to place order.")
                #         continue # skip the open request func and all below code. go to the next loop
                # else:
                #     print("no ascending steps. OK to place order.")


                if is_check_adx_threshold_enabled:
                    # this checks if adx is above 25
                    check_adx_result = check_if_adx_meets_requirements(symbol=symbol, timeframe=timeframe, adx_threshold=adx_threshold)
                    if check_adx_result == False:
                        continue
                if is_check_adx_ascending_enabled:
                    # this checks if adx is ascending
                    check_adx_ascending_res = check_adx_ascending(symbol=symbol, timeframe=timeframe, n=2) # previously working setting was that n was set to 3
                    if check_adx_ascending_res == False:
                        continue


                # check if there is news ahead or if we are after news
                news_exist = get_news_data.trades_blocker_to_avoid_news(60, news_df)
                if news_exist:
                    continue


                open_request(sl_price=dows_high, type="sell", sl=sl, symbol=symbol, type_filling=type_filling, commission_per_lot=commission_per_lot, risk_ratio=risk_ratio, risk_reward_ratio=risk_reward_ratio, 
                             tp_percent=tp_percent, added_points_to_sl=added_points_to_sl, added_points_to_tp=added_points_to_tp, fixed_tp=fixed_tp, fixed_tp_in_points=fixed_tp_in_points)
                # continue

            # do we need to check retrace or pause when doing across sma trades?
            # maybe not. because usually it's the price goes down from above to below and then go above, so there should be a natural retrace/reverse
            # actually it's best to include, maybe. bacause if the reverse point is too far away (in this case maybe no retrace nearby the sma), 
            # the price would touch the sma and then bounce back, continue its previous trend

            ############### This seems to be not working well on at least M5. So disable it temporarily ###################

            # across_sma_from_below_to_above, 
            #elif current_price > tick_two_close and above_or_below_sma == "across_sma_from_below_to_above" and tick_two_close > tick_two_open: # and check_retrace_or_pause_when_long(symbol=symbol, timeframe=timeframe, start_position=0, tick_count=5):
            elif current_price > tick_two_close and above_or_below_sma == "across_sma_from_below_to_above" and tick_two_close > tick_two_open:
                # tick_two_close > tick_two_open to ensure this key candle crossing sma is closed a bullish candle.
                # sometimes there might be a jump (window) or maybe the sma is steep, and the candle will close as a bearish candle with a very small body and a long upper wick
                # if this happens, we do not think this is a valid crossing. i guess this usually happens in lower timeframes. i observed this on m5
                # in such case this is the so called 
                
                # check if we should look for a sell order or a buy order
                # print(f"look_for_sell_or_buy: {look_for_sell_or_buy}")
                if look_for_sell_or_buy in {"all", "buy"}:
                    pass
                else:
                    continue                
                
                # print("buy, across_sma_from_below_to_above")
                if check_above_or_below_sma:
                    pass
                else:
                    # does check above or below sma, so there's no such thing as across_sma_from_below_to_above
                    continue

                # # check if timeframes {timeframe}, H1, and H4 are in the same trend.
                # if above_or_below_sma_h1 == "above":# and above_or_below_sma_h4 == "above":
                #     pass
                # else:
                #     print(f"timeframes are not identical.")
                #     print(f"{timeframe}: {above_or_below_sma}, H1: {above_or_below_sma_h1}, H4: {above_or_below_sma_h4}")
                #     continue

                if check_timeframe_consistency:
                    # check timeframe, and make sure higher timeframes' trends are identical with that of the current timeframe
                    if timeframe == mt5.TIMEFRAME_M5:
                        if above_or_below_sma_m15 in {"above", "across_sma_from_below_to_above"} and above_or_below_sma_m30 in {"above", "across_sma_from_below_to_above"} and above_or_below_sma_h1 in {"above", "across_sma_from_below_to_above"}:# and above_or_below_sma_h4 == "above":
                            print("trading on m5. m5 m15 m30 h1 all identical. ok")
                            pass
                        else:
                            print(f"timeframes are not identical.")
                            print(f"M5: {above_or_below_sma_m5}, M15: {above_or_below_sma_m15}, M30: {above_or_below_sma_m30}, H1: {above_or_below_sma_h1}, H4: {above_or_below_sma_h4}")
                            continue
                    elif timeframe == mt5.TIMEFRAME_M15:
                        if above_or_below_sma_m30 in {"above", "across_sma_from_below_to_above"} and above_or_below_sma_h1 in {"above", "across_sma_from_below_to_above"}:# and above_or_below_sma_h4 == "above":
                            print("trading on m15. m15 m30 h1 all identical. ok")
                            pass
                        else:
                            print(f"timeframes are not identical.")
                            print(f"M5: {above_or_below_sma_m5}, M15: {above_or_below_sma_m15}, M30: {above_or_below_sma_m30}, H1: {above_or_below_sma_h1}, H4: {above_or_below_sma_h4}")
                            continue
                    elif timeframe == mt5.TIMEFRAME_M30:
                        if above_or_below_sma_h1 in {"above", "across_sma_from_below_to_above"}:# and above_or_below_sma_h4 == "above":
                            print("trading on m30. m30 h1 all identical. ok")
                            pass
                        else:
                            print(f"timeframes are not identical.")
                            print(f"M5: {above_or_below_sma_m5}, M15: {above_or_below_sma_m15}, M30: {above_or_below_sma_m30}, H1: {above_or_below_sma_h1}, H4: {above_or_below_sma_h4}")
                            # print(f"{timeframe}: {above_or_below_sma}, H1: {above_or_below_sma_h1}, H4: {above_or_below_sma_h4}")
                            continue

                ##### find SL ######
                # sl = current_price * 1000 - rates[1][3] * 1000  # USDJPY
                # BTC digits -> 2   USDJPY digits -> 3
                # digits = mt5.symbol_info(symbol).digits # BTC digits -> 2         mt5.symbol_info(symbol).xxx, not mt5.symbol_info_tick(symbol).xxx
                # multiply_digits = 10 ** digits
                # sl is in points, /10 if needed to convert to pips
                #sl = current_price * multiply_digits - lower_price * multiply_digits  # BTC

                # dows_low = find_dows_low(symbol=symbol, timeframe=timeframe, tick_count=12)
                # if dows_low:
                #     sl = current_price * multiply_digits - dows_low * multiply_digits
                # else:
                #     print(f"didn't find dows_low in previous ticks, won't open order")
                #     continue

                dows_low = find_dows_low(symbol=symbol, timeframe=timeframe, tick_count=5) # as crossing sma we are opening order on a new candle. so it's 5 ticks
                if dows_low:
                    sl = current_price * multiply_digits - dows_low * multiply_digits
                else:
                    # print(f"didn't find dows_low in previous 5 ticks, will get last 3 ticks and use the first tick's low as dow's low")
                    dows_low = tick_one_low
                    sl = current_price * multiply_digits - dows_low * multiply_digits
                # sl = current_price * 100 - lower_price * 100  # BTC
                ##################

                # make sl one pip larger. because we want the sl price to be one pip below or above dows high and low
                sl = sl + added_points_to_sl
                dows_low = (dows_low * multiply_digits - added_points_to_sl) / multiply_digits # 141.350 * 1000 - 10 is 141350 - 10, which is 141340. then 141340 / 1000 is 141.340

                # check if it's a large tick that is crossing sma
                body_points = abs(tick_two_open * multiply_digits - tick_two_close * multiply_digits)
                if body_points >= body_points_limit:# and symbol == "USDJPY":
                    # print(f"the body of the tick crossing sma is {body_points}, exceeding {body_points_limit}, too large. aborted.")
                    continue

                # check if sl too large too small
                if sl > sl_limit:  # if sl > 300 points, or 30 pips
                    # print(f"sl is {sl} points. too large, > sl_limit {sl_limit}, aborted.")
                    continue
                elif sl < sl_min:
                    # print(f"sl is {sl} points. too small, < sl_min {sl_min}, aborted.")
                    continue

                actual_offset = multiply_digits * abs(current_price - tick_two_close)
                if actual_offset > offset_limit:
                    # print(f"actual_offset is {actual_offset}, exceeded offset_limit: {offset_limit} points. not opening tickets")
                    continue
                


                retrace_or_pause_when_long = check_retrace_or_pause_when_long(symbol=symbol, timeframe=timeframe, start_position=0, tick_count=5)

                if retrace_or_pause_when_long is False:
                    continue
                
                ########### I imagine we do not need to check the current price with the ideal entry (the breaking price) for crossing sma scenarios. because there should normally be a visible gap, making it "not ideal"##############
                ########### if we compare this, we will rarely open a trade (unless in rare conditions where the next canlde after the breaking candle is still around the ideal price) ##########
                # elif retrace_or_pause_when_long in {'retrace_n_pause_when_long', 'ratrace_when_long'}:
                #     # find the ideal entry price, which is the recent first breaking price, and compare it with the current price. if it's not the same, it indicates that we are not in the earliest ideal entry
                #     index_of_tick_that_breaks, ideal_entry_price = find_which_tick_breaks_after_retracement_when_long(symbol=symbol, timeframe=timeframe, start_position=0, tick_count=7)
                #     if index_of_tick_that_breaks: # this seems redundant as it should always be true
                #         # print(f"index of tick that breaks after_retracement_when_long: {index_of_tick_that_breaks}")
                #         # print(f"ideal entry price: {ideal_entry_price}")
                #         # print(f"current bid price: {current_price}")
                #         points_gap_between_ideal_n_current = abs((current_price - ideal_entry_price) * multiply_digits)
                #         # print(f"points gap between ideal entry price and current bid price: {points_gap_between_ideal_n_current}")
                #         if points_gap_between_ideal_n_current > points_gap_between_ideal_n_current_limit:
                #             # print(f"points_gap_between_ideal_n_current {points_gap_between_ideal_n_current} is greater than points_gap_between_ideal_n_current_limit {points_gap_between_ideal_n_current_limit}")
                #             continue
                # elif retrace_or_pause_when_long == 'pause_when_long':
                #     index_of_tick_that_breaks, ideal_entry_price = find_which_tick_breaks_after_pause_when_long(symbol=symbol, timeframe=timeframe, start_position=0, tick_count=7)
                #     if index_of_tick_that_breaks: # this seems redundant as it should always be true
                #         # print(f"index of tick that breaks after_pause_when_long: {index_of_tick_that_breaks}")
                #         # print(f"ideal entry price: {ideal_entry_price}")
                #         # print(f"current bid price: {current_price}")
                #         points_gap_between_ideal_n_current = abs((current_price - ideal_entry_price) * multiply_digits)
                #         # print(f"points gap between ideal entry price and current bid price: {points_gap_between_ideal_n_current}")
                #         if points_gap_between_ideal_n_current > points_gap_between_ideal_n_current_limit:
                #             # print(f"points_gap_between_ideal_n_current {points_gap_between_ideal_n_current} is greater than points_gap_between_ideal_n_current_limit {points_gap_between_ideal_n_current_limit}")
                #             continue



                # check if SMAs in different timeframes are standing in the way towards our tp
                if check_sma_resistance:
                    
                    if fixed_tp:
                        tp = fixed_tp_in_points
                    else:
                        # sl is sl points. need to add it to entry price to get tp price
                        tp = sl / risk_reward_ratio # tp in points
                        tp = int(tp * tp_percent)
                        tp_price = ask_price + tp * symbol_point

                    if timeframe == mt5.TIMEFRAME_M30:
                        if current_price < sma_list_h4[-1] < tp_price:
                            print(f"h4 sma {sma_list_h4[-1]} is in the way between entry price {current_price} and tp_price {tp_price}. abort")
                            continue
                        elif current_price < sma_list_h1[-1] < tp_price:
                            print(f"h1 sma {sma_list_h1[-1]} is in the way between entry price {current_price} and tp_price {tp_price}. abort")
                            continue
                        elif current_price < sma_list_m15[-1] < tp_price:
                            print(f"m15 sma {sma_list_m15[-1]} is in the way between entry price {current_price} and tp_price {tp_price}. abort")
                            continue
                        else:
                            print("h4, h1, m15 smas are not in the way between entry price and tp_price")
                            print(f"entry price {current_price}, tp_price {tp_price}")
                            print(f"h4 sma {sma_list_h4[-1]}")
                            print(f"h1 sma {sma_list_h1[-1]}")
                            print(f"m15 sma {sma_list_m15[-1]}")
                    elif timeframe == mt5.TIMEFRAME_H1:
                        if current_price < sma_list_h4[-1] < tp_price:
                            print(f"h4 sma {sma_list_h4[-1]} is in the way between entry price {current_price} and tp_price {tp_price}. abort")
                            continue
                        elif current_price < sma_list_m30[-1] < tp_price:
                            print(f"m30 sma {sma_list_m30[-1]} is in the way between entry price {current_price} and tp_price {tp_price}. abort")
                            continue
                        elif current_price < sma_list_m15[-1] < tp_price:
                            print(f"m15 sma {sma_list_m15[-1]} is in the way between entry price {current_price} and tp_price {tp_price}. abort")
                            continue
                        else:
                            print("h4, m30, m15 smas are not in the way between entry price and tp_price")
                            print(f"entry price {current_price}, tp_price {tp_price}")
                            print(f"h4 sma {sma_list_h4[-1]}")
                            print(f"m30 sma {sma_list_m30[-1]}")
                            print(f"m15 sma {sma_list_m15[-1]}")

                # # calculation complex high cpu. put it after calculating actual_offset
                # high_1 = check_steps_when_long(symbol=symbol, timeframe=timeframe, tick_count=30)
                # if high_1:
                #     if current_price > high_1:
                #         print(f"price goes above high_1 {high_1}, descending steps fail. OK to place order.")
                #     else:
                #         print(f"price doesn't go above high_1 {high_1}, descending steps are growing. not OK to place order.")
                #         continue # skip the open request func and all below code. go to the next loop
                # else:
                #     print("no descending steps. OK to place order.")


                if is_check_adx_threshold_enabled:
                    # this checks if adx is above 25
                    check_adx_result = check_if_adx_meets_requirements(symbol=symbol, timeframe=timeframe, adx_threshold=adx_threshold)
                    if check_adx_result == False:
                        continue
                if is_check_adx_ascending_enabled:
                    # this checks if adx is ascending
                    check_adx_ascending_res = check_adx_ascending(symbol=symbol, timeframe=timeframe, n=2) # previously working setting was that n was set to 3
                    if check_adx_ascending_res == False:
                        continue
                
                
                # check if there is news ahead or if we are after news
                news_exist = get_news_data.trades_blocker_to_avoid_news(60, news_df)
                if news_exist:
                    continue


                open_request(sl_price=dows_low, type="buy", sl=sl, symbol=symbol, type_filling=type_filling, commission_per_lot=commission_per_lot, risk_ratio=risk_ratio, risk_reward_ratio=risk_reward_ratio, 
                             tp_percent=tp_percent, added_points_to_sl=added_points_to_sl, added_points_to_tp=added_points_to_tp, fixed_tp=fixed_tp, fixed_tp_in_points=fixed_tp_in_points)
                # continue # if we opened an order, we go back to the beginning of the loop, we don't sleep
            # across_sma_from_above_to_below
            elif ask_price < tick_two_close and above_or_below_sma == "across_sma_from_above_to_below" and tick_two_close < tick_two_open:
                # tick_two_close < tick_two_open to ensure this key candle crossing sma is closed a bearish candle.
                
                # check if we should look for a sell order or a buy order
                # print(f"look_for_sell_or_buy: {look_for_sell_or_buy}")
                if look_for_sell_or_buy in {"all", "sell"}:
                    pass
                else:
                    continue                
                
                # print("sell, across_sma_from_above_to_below")
                if check_above_or_below_sma:
                    pass
                else:
                    # does check above or below sma, so there's no such thing as across_sma_from_below_to_above
                    continue

                # # check if timeframes {timeframe}, H1, and H4 are in the same trend.
                # if above_or_below_sma_h1 == "below":# and above_or_below_sma_h4 == "below":
                #     pass
                # else:
                #     print(f"timeframes are not identical.")
                #     print(f"{timeframe}: {above_or_below_sma}, H1: {above_or_below_sma_h1}, H4: {above_or_below_sma_h4}")
                #     continue

                if check_timeframe_consistency:
                    # check timeframe, and make sure higher timeframes' trends are identical with that of the current timeframe
                    if timeframe == mt5.TIMEFRAME_M5:
                        if above_or_below_sma_m15 in {"below", "across_sma_from_above_to_below"} and above_or_below_sma_m30 in {"below", "across_sma_from_above_to_below"} and above_or_below_sma_h1 in {"below", "across_sma_from_above_to_below"}:# and above_or_below_sma_h4 == "above":
                            print("trading on m5. m5 m15 m30 h1 all identical. ok")
                            pass
                        else:
                            print(f"timeframes are not identical.")
                            print(f"M5: {above_or_below_sma_m5}, M15: {above_or_below_sma_m15}, M30: {above_or_below_sma_m30}, H1: {above_or_below_sma_h1}, H4: {above_or_below_sma_h4}")
                            continue
                    elif timeframe == mt5.TIMEFRAME_M15:
                        if above_or_below_sma_m30 in {"below", "across_sma_from_above_to_below"} and above_or_below_sma_h1 in {"below", "across_sma_from_above_to_below"}:# and above_or_below_sma_h4 == "above":
                            print("trading on m15. m15 m30 h1 all identical. ok")
                            pass
                        else:
                            print(f"timeframes are not identical.")
                            print(f"M5: {above_or_below_sma_m5}, M15: {above_or_below_sma_m15}, M30: {above_or_below_sma_m30}, H1: {above_or_below_sma_h1}, H4: {above_or_below_sma_h4}")
                            continue
                    elif timeframe == mt5.TIMEFRAME_M30:
                        if above_or_below_sma_h1 in {"below", "across_sma_from_above_to_below"}:# and above_or_below_sma_h4 == "above":
                            print("trading on m30. m30 h1 all identical. ok")
                            pass
                        else:
                            print(f"timeframes are not identical.")
                            print(f"M5: {above_or_below_sma_m5}, M15: {above_or_below_sma_m15}, M30: {above_or_below_sma_m30}, H1: {above_or_below_sma_h1}, H4: {above_or_below_sma_h4}")
                            # print(f"{timeframe}: {above_or_below_sma}, H1: {above_or_below_sma_h1}, H4: {above_or_below_sma_h4}")
                            continue



                ##### find SL #####
                # second_tick_high-current_price
                # sl = rates[1][2] * 1000 - current_price * 1000  # USDJPY
                # digits = mt5.symbol_info(symbol).digits
                # multiply_digits = 10 ** digits
                #sl = higher_price * multiply_digits - current_price * multiply_digits  # BTC
                
                # dows_high = find_dows_high(symbol=symbol, timeframe=timeframe, tick_count=12)
                # if dows_high:
                #     sl = dows_high * multiply_digits - ask_price * multiply_digits
                # else:
                #     print(f"didn't find dows_high in previous ticks, won't open order")
                #     continue
                dows_high = find_dows_high(symbol=symbol, timeframe=timeframe, tick_count=5)
                if dows_high:
                    sl = dows_high * multiply_digits - ask_price * multiply_digits
                else:
                    # print(f"didn't find dows_high in previous 5 ticks, will get last 3 ticks and use the first tick's high as dow's high")
                    dows_high = tick_one_high
                    sl = dows_high * multiply_digits - ask_price * multiply_digits
                ##### ###### ######
                
                # make sl one pip larger. because we want the sl price to be one pip below or above dows high and low
                sl = sl + added_points_to_sl
                dows_high = (dows_high * multiply_digits + added_points_to_sl) / multiply_digits # 141.350 * 1000 - 10 is 141350 - 10, which is 141340. then 141340 / 1000 is 141.340

                # check if it's a large tick that is crossing sma
                body_points = abs(tick_two_open * multiply_digits - tick_two_close * multiply_digits)
                if body_points >= body_points_limit:# and symbol == "USDJPY":
                    # print(f"the body of the tick crossing sma is {body_points}, exceeding {body_points_limit}, too large. aborted.")
                    continue

                # check if sl too large too small
                if sl > sl_limit:  # if sl > 300 points, or 30 pips
                    # print(f"sl is {sl} points. too large, > sl_limit {sl_limit}, aborted.")
                    continue
                elif sl < sl_min:
                    # print(f"sl is {sl} points. too small, < sl_min {sl_min}, aborted.")
                    continue

                actual_offset = multiply_digits * abs(ask_price - tick_two_close)
                if actual_offset > offset_limit:
                    # print(f"actual_offset is {actual_offset}, exceeded offset_limit: {offset_limit} points. not opening tickets")
                    continue
                


                ########### I imagine we do not need to check the current price with the ideal entry (the breaking price) for crossing sma scenarios. because there should normally be a visible gap, making it "not ideal"##############
                ########### if we compare this, we will rarely open a trade (unless in rare conditions where the next canlde after the breaking candle is still around the ideal price) ##########
                retrace_or_pause_when_short = check_retrace_or_pause_when_short(symbol=symbol, timeframe=timeframe, start_position=0, tick_count=5)
                if retrace_or_pause_when_short is False:
                    continue
                # elif retrace_or_pause_when_short in {'retrace_n_pause_when_short', 'ratrace_when_short'}:
                #     index_of_tick_that_breaks, ideal_entry_price = find_which_tick_breaks_after_retracement_when_short(symbol=symbol, timeframe=timeframe, start_position=0, tick_count=7)
                #     if index_of_tick_that_breaks:
                #         # print(f"tick_breaks_after_retracement_when_short: {index_of_tick_that_breaks}")
                #         # print(f"ideal entry price: {ideal_entry_price}")
                #         # print(f"current ask price: {ask_price}")
                #         points_gap_between_ideal_n_current = abs((ask_price - ideal_entry_price) * multiply_digits)
                #         # print(f"points gap between ideal entry price and current ask price: {points_gap_between_ideal_n_current}")
                #         if points_gap_between_ideal_n_current > points_gap_between_ideal_n_current_limit:
                #             # print(f"points_gap_between_ideal_n_current {points_gap_between_ideal_n_current} is greater than points_gap_between_ideal_n_current_limit {points_gap_between_ideal_n_current_limit}")
                #             continue
                # elif retrace_or_pause_when_short == 'pause_when_short':
                #     index_of_tick_that_breaks, ideal_entry_price = find_which_tick_breaks_after_pause_when_short(symbol=symbol, timeframe=timeframe, start_position=0, tick_count=7)
                #     if index_of_tick_that_breaks:
                #         # print(f"tick_breaks_after_pause_when_short: {index_of_tick_that_breaks}")
                #         # print(f"ideal entry price: {ideal_entry_price}")
                #         # print(f"current ask price: {ask_price}")
                #         points_gap_between_ideal_n_current = abs((ask_price - ideal_entry_price) * multiply_digits)
                #         # print(f"points gap between ideal entry price and current ask price: {points_gap_between_ideal_n_current}")
                #         if points_gap_between_ideal_n_current > points_gap_between_ideal_n_current_limit:
                #             # print(f"points_gap_between_ideal_n_current {points_gap_between_ideal_n_current} is greater than points_gap_between_ideal_n_current_limit {points_gap_between_ideal_n_current_limit}")
                #             continue


                # check if SMAs in different timeframes are standing in the way towards our tp
                if check_sma_resistance:
                    
                    if fixed_tp:
                        tp = fixed_tp_in_points
                    else:
                        # sl is sl points. need to add it to entry price to get tp price
                        tp = sl / risk_reward_ratio # tp in points
                        tp = int(tp * tp_percent)
                        tp_price = ask_price - tp * symbol_point

                    if timeframe == mt5.TIMEFRAME_M30:
                        if ask_price > sma_list_h4[-1] > tp_price:
                            print(f"h4 sma {sma_list_h4[-1]} is in the way between entry price {ask_price} and tp_price {tp_price}. abort")
                            continue
                        elif ask_price > sma_list_h1[-1] > tp_price:
                            print(f"h1 sma {sma_list_h1[-1]} is in the way between entry price {ask_price} and tp_price {tp_price}. abort")
                            continue
                        elif ask_price > sma_list_m15[-1] > tp_price:
                            print(f"m15 sma {sma_list_m15[-1]} is in the way between entry price {ask_price} and tp_price {tp_price}. abort")
                            continue
                        else:
                            print("h4, h1, m15 smas are not in the way between entry price and tp_price")
                            print(f"entry price {ask_price}, tp_price {tp_price}")
                            print(f"h4 sma {sma_list_h4[-1]}")
                            print(f"h1 sma {sma_list_h1[-1]}")
                            print(f"m15 sma {sma_list_m15[-1]}")
                    elif timeframe == mt5.TIMEFRAME_H1:
                        if ask_price > sma_list_h4[-1] > tp_price:
                            print(f"h4 sma {sma_list_h4[-1]} is in the way between entry price {ask_price} and tp_price {tp_price}. abort")
                            continue
                        elif ask_price > sma_list_m30[-1] > tp_price:
                            print(f"m30 sma {sma_list_m30[-1]} is in the way between entry price {ask_price} and tp_price {tp_price}. abort")
                            continue
                        elif ask_price > sma_list_m15[-1] > tp_price:
                            print(f"m15 sma {sma_list_m15[-1]} is in the way between entry price {ask_price} and tp_price {tp_price}. abort")
                            continue
                        else:
                            print("h4, m30, m15 smas are not in the way between entry price and tp_price")
                            print(f"entry price {ask_price}, tp_price {tp_price}")
                            print(f"h4 sma {sma_list_h4[-1]}")
                            print(f"m30 sma {sma_list_m30[-1]}")
                            print(f"m15 sma {sma_list_m15[-1]}")

                # low_1 = check_steps_when_short(symbol=symbol, timeframe=timeframe, tick_count=30)
                # if low_1:
                #     if current_price < low_1:
                #         print(f"price goes below low_1 {low_1}, ascending steps fail. OK to place order.")
                #     else:
                #         print(f"price doesn't go below low_1 {low_1}, ascending steps are growing. not OK to place order.")
                #         continue # skip the open request func and all below code. go to the next loop
                # else:
                #     print("no ascending steps. OK to place order.")

                
                if is_check_adx_threshold_enabled:
                    # this checks if adx is above 25
                    check_adx_result = check_if_adx_meets_requirements(symbol=symbol, timeframe=timeframe, adx_threshold=adx_threshold)
                    if check_adx_result == False:
                        continue
                if is_check_adx_ascending_enabled:
                    # this checks if adx is ascending
                    check_adx_ascending_res = check_adx_ascending(symbol=symbol, timeframe=timeframe, n=2) # previously working setting was that n was set to 3
                    if check_adx_ascending_res == False:
                        continue


                # check if there is news ahead or if we are after news
                news_exist = get_news_data.trades_blocker_to_avoid_news(60, news_df)
                if news_exist:
                    continue


                # sl = higher_price * 100 - current_price * 100  # BTC
                open_request(sl_price=dows_high, type="sell", sl=sl, symbol=symbol, type_filling=type_filling, commission_per_lot=commission_per_lot, risk_ratio=risk_ratio, risk_reward_ratio=risk_reward_ratio, 
                             tp_percent=tp_percent, added_points_to_sl=added_points_to_sl, added_points_to_tp=added_points_to_tp, fixed_tp=fixed_tp, fixed_tp_in_points=fixed_tp_in_points)
                # continue

            ############### This seems to be not working well on at least M5. So disable it temporarily ###################

            # time.sleep(0.1)
        # elif open_positions != 0:
        elif len(current_symbol_open_positions) != 0:
            try:
                # positions = get_positions_by_symbol(symbol=symbol)
                positions = mt5.positions_get() # get all open positions
                # as we only open one position at a time, so there should be only one item in this list/set?
                
                # position = positions[0] # this is the origin working line
                

                # print(position)
                # print()
                # print(type(position))
                # current_symbol = position.symbol
            except Exception as exception:
                print(traceback.format_exc())
                print(f"error info: {exception}")
                continue




            for position in positions:
                # need to calc new !!!multiply_digits!!!
                # because if we choose usdjpy but there's an eurusd order opended on another script 
                # then the multiply_digits is still usdjpy, unless we change it here
                # !!! make sure to distinguish position digits and digits of the current monitoring currency pair
                position_symbol_digits = mt5.symbol_info(position.symbol).digits
                position_symbol_multiply_digits = 10 ** position_symbol_digits


                ###### some variables that we need later on #####
                points_from_tp = abs(position.price_current - position.tp) * position_symbol_multiply_digits
                points_from_entry = abs(position.price_current - position.price_open) * position_symbol_multiply_digits

                points_full_tp = abs(position.price_open - position.tp) * position_symbol_multiply_digits
                points_full_sl = abs(position.price_open - position.sl) * position_symbol_multiply_digits
                ###### some variables that we need later on #####


                ###################### realize max positive excursion (MPE) #################### # I checked but this is not an industry used name
                # definition: the highest floating points this trade has ever had
                # this is the initialization of the trade with mpe information
                if position.ticket not in trade_state:
                    trade_state[position.ticket] = {
                        'mpe': 0, # in points
                        'be_moved'  : False,
                        'checked_first_candle_close': False,
                        'checked_60': False,
                        'checked_90': False
                    }
                # with the initialization, we can say that we have this "position.ticket" in the trade_state dict

                # now let's update the mpe information
                current_ticket_state = trade_state[position.ticket]
                # points_from_tp = abs(position.price_current - position.tp) * position_symbol_multiply_digits
                # points_full_tp = abs(position.price_open - position.tp) * position_symbol_multiply_digits

                if points_from_tp <= points_full_tp:
                    # in profits or at least BE
                    points_earned_so_far = abs(position.price_open - position.price_current) * position_symbol_multiply_digits
                    # compare it with the current mpe
                    if points_earned_so_far > current_ticket_state['mpe']:
                        current_ticket_state['mpe'] = points_earned_so_far # python mutable objects (lists, dicts) any name bound to them refers to the same underlying object

                else:
                    # in drawdown
                    # no need to update the MPE
                    pass
            
                ###################### realize max positive excursion (MPE) ####################



                # how far away are we from tp
                # digits = mt5.symbol_info(symbol).digits
                # multiply_digits = 10 ** digits
                # points_from_tp = abs(position.price_current - position.tp) * position_symbol_multiply_digits
                # print(f"points_from_tp = {round(points_from_tp, 2)} points   ", end="\r", flush=True)
                # print(f"points_from_tp = {points_from_tp:.2f} points  *{position.symbol}* ", end="\r", flush=True) # working one
                print(f"{points_from_tp:.0f} *{position.symbol}* |", end=" ", flush=True)
                # output:
                # points_from_tp = 138669.0 points
                # points_from_tp = 138667.0 points
                # somehow, this will open a new position with sl and open price the same, BUT WITH NO TP!!!
                # so points_from_tp is very large, if shorting, then it's the distance to ZERO!!!
                # No, it does NOT open a new order, it just modifies the order, because we didn't pass tp, so there's no TP, WHICH makes sense!!!

                # if we do this, it doesn't work on a 1 min scalping chart, because price moves fast, and tp is just 3-4 pips already. 
                # so if we drag the sl to entry price. we are immediately stopped out, frequently, open order, drag sl, kicked out. again and again. constantly lossing commisions!!!
                # but it might work on 1 hour chart.
                # anyway, let's try something else at the moment, set the sl to half of the original sl.
                # half_original_sl_price = (position.price_open + position.sl) / 2
                # need a sl_modified =0 flag outside
                # the above needs a flag, otherwise it's going to divide till zero


                ################# working for dragging sl based on risk ratio #####################
                # # as the risk reward ratio is 2 to 1, so if we want to set sl to half, just set it to tp, NO NO NO. rememnber, it's price. not points
                # point = mt5.symbol_info(symbol).point
                # tp_in_points = abs(position.price_open - position.tp) * multiply_digits
                # if position.type == 0: # buy
                #     sl_price = position.price_open - tp_in_points * point # 0.001
                # elif position.type == 1: # sell
                #     sl_price = position.price_open + tp_in_points * point

                # sl_price = round(sl_price, digits)
                ##################################################################################
            

                """
                print(f"position.sl: {position.sl}")
                print(f"sl_price: {sl_price}")
                if position.sl != sl_price:
                    print("position.sl != sl_price is TRUE")

                output:
                position.sl: 139.446
                sl_price: 139.44600000000003
                position.sl != sl_price is TRUE

                position.sl is the actual position_sl_price, it's a threee decimal price
                but sl_price as we calculate, it contains many decimals. so they are theoretically not identical. but approximately the same.
                sl_price

                The workaround: round the calculated sl_price to a three decimal price?
                """

                
                # # work for risk reward 2:1
                # if points_from_tp <= points_from_tp_limit and position.sl != sl_price:
                #     modify_sl_request(symbol=symbol, ticket=position.ticket, sl_price=sl_price, tp_price=position.tp, type_filling=type_filling)
                    
                # print(f"\n\n\npoints_from_tp = {points_from_tp:.2f} points \n\n\n  ")


                # try to check how long the position is open
                # print(position)
                # 144745 *USDJPY.p* | TradePosition(ticket=355201, time=1746410198, time_msc=1746410198550, time_update=1746410198, time_update_msc=1746410198550, type=0, magic=0, identifier=355201, reason=0, volume=0.01, price_open=144.746, sl=0.0, tp=0.0, price_current=144.745, swap=0.0, profit=-0.01, symbol='USDJPY.p', comment='', external_id='')
                
                # The problem with datetime.utcnow() and datetime.utcfromtimestamp() occurs because these return naïve datetimes (i.e. with no timezone attached), and in Python 3, these are interpreted as system-local times. Explicitly specifying a time zone solves the problem.
                
                trade_open_time_sec = position.time
                
                # Convert trade open time to datetime
                open_time_broker_local = datetime.fromtimestamp(trade_open_time_sec) # this converts using my local timezone, utc+1, so there is something wrong
                open_time_broker_local_real_utc = datetime.fromtimestamp(trade_open_time_sec, tz=timezone.utc)

                open_time_utc = convert_mt5_time_to_utc(trade_open_time_sec, broker_time_offset_hours_from_utc)
                
                # Get current UTC time, timezone-aware
                now_utc = datetime.now(timezone.utc)     
                # Calculate time difference
                time_diff = now_utc - open_time_utc

                # print(f"trade_open_time_sec: {trade_open_time_sec}")
                # print(f"open_time_broker_local: {open_time_broker_local}")
                # print(f"open_time_broker_local_real_utc: {open_time_broker_local_real_utc}")
                # print(f"open_time_utc: {open_time_utc}")
                # print(f"now_utc: {now_utc}")
                # print(f"time_diff: {time_diff}")
                # print(f"timedelta(minutes=90): {timedelta(minutes=90)}")
                # exit()

                """
                    trade_open_time_sec: 1746454779
                    open_time_broker_local: 2025-05-05 15:19:39
                    open_time_broker_local_real_utc: 2025-05-05 14:19:39+00:00
                    open_time_utc: 2025-05-05 12:19:39+00:00
                    now_utc: 2025-05-05 12:42:13.502437+00:00
                    time_diff: 0:22:34.502437
                    timedelta(minutes=90): 1:30:00
                """

                # 1. SPIKE in 30 mins (previously the rule is 5 minutes)
                # check spike in drawndown >= 75% of full stop loss within 5 minutes CONTINUOUSLY
                if time_diff <= timedelta(minutes=30): # instead of 5, let's do 30
                    if points_from_tp <= points_full_tp:
                        # the points between the current price and the take profit price is <= than the points of the full take profit
                        # this means we are in profits or BE
                        pass
                    else:
                        # we are in drawdown
                        drawdown_proportion = points_from_entry / points_full_sl # e.g 150 / 200 points = 0.75
                        if drawdown_proportion >= 0.75:
                            order_type = position.type
                            if order_type == 0:
                                close_type = 1
                            elif order_type == 1:
                                close_type = 0
                            print("Risk Management 1")
                            close_request(symbol=symbol, ticket=position.ticket, lot=position.volume, type_filling=type_filling, close_type=close_type)                            

                # 2. FIRST CANDLE CLOSE healthcheck
                # check right when the first bar is closed, how can I do this? this is tricky
                # I can write down the open time, and calculate how many minutes are left before the entry candle closes, calling it minutes_left_for_entry_close, and then minutes_left_for_entry_close += 30
                
                if 0 <= open_time_utc.minute < 30:
                    entry_bar_start_time = open_time_utc.replace(minute=0, second=0, microsecond=0)
                else:
                    # minute has to be 30 to 59 in this condition
                    entry_bar_start_time = open_time_utc.replace(minute=30, second=0, microsecond=0)
                
                first_full_bar_start = entry_bar_start_time + timedelta(minutes=30)
                first_full_bar_close = first_full_bar_start + timedelta(minutes=30)

                # if the current time is later than the first bar close time and the first_candle_close is not checked
                if now_utc >= first_full_bar_close and not current_ticket_state['checked_first_candle_close']: 
                    current_ticket_state['checked_first_candle_close'] = True
                    if points_from_tp <= points_full_tp:
                        # in profits or BE
                        # do nothing
                        pass
                    else:
                        drawdown_proportion = points_from_entry / points_full_sl
                        if drawdown_proportion >= 0.3:
                            order_type = position.type
                            if order_type == 0:
                                close_type = 1
                            elif order_type == 1:
                                close_type = 0
                            print("Risk Management 2")
                            close_request(symbol=symbol, ticket=position.ticket, lot=position.volume, type_filling=type_filling, close_type=close_type)    

                # 3. 60 Min no-momentum check (runs ONCE at 60 minutes)
                if time_diff >= timedelta(minutes=60) and not current_ticket_state['checked_60']:
                    current_ticket_state['checked_60'] = True
                    
                    mpe_proportion = current_ticket_state['mpe'] / points_full_tp

                    if points_from_tp <= points_full_tp:
                        current_risk_exceeds_limit = False
                    else:
                        drawdown_proportion = points_from_entry / points_full_sl
                        if drawdown_proportion >= 0.2:
                            current_risk_exceeds_limit = True
                        else:
                            current_risk_exceeds_limit = False


                    # if BOTH are met, that is, mpe_proportion smaller than 30% AND current floating loss is greater than 20% of the stop loss
                    # initially we wanted both to be true, later I think "or" might be better
                    # if mpe_proportion < 0.3 and current_risk_exceeds_limit:
                    if mpe_proportion < 0.3 or current_risk_exceeds_limit:
                        order_type = position.type
                        if order_type == 0:
                            close_type = 1
                        elif order_type == 1:
                            close_type = 0
                        print("Risk Management 3")
                        close_request(symbol=symbol, ticket=position.ticket, lot=position.volume, type_filling=type_filling, close_type=close_type)
                    

                # Check *AT* 90 minutes, if price has ever reached 30% profits, If so, then leave it. If not, close the trade.
                # ... #

                # 4. 90 minutes check
                # Check if within 90 minutes
                # Check constantly if after 90 minutes, we are above 20% profits, if at any time price retraces below 20% proits, close IMMEDIATELY. So this is CONTINUOUS checking
                # if time_diff <= timedelta(minutes=90):
                #     print("✅ Trade was opened within the last 90 minutes.")
                # else:
                #     print("❌ Trade is older than 90 minutes.")
                if time_diff > timedelta(minutes=90):
                    # check if the profits is at least 0.3 R
                    # points_from_tp = abs(position.price_current - position.tp) * position_symbol_multiply_digits
                    # points_full_tp = abs(position.price_open - position.tp) * position_symbol_multiply_digits
                    if points_from_tp <= points_full_tp:
                        # at least in profits
                        points_earned_so_far = abs(position.price_open - position.price_current) * position_symbol_multiply_digits
                        earned_proportion = points_earned_so_far / points_full_tp
                        earned_proportion_threshold = 0.2 # set this to 0.3 (30% of total tp) or any proportion # I feel 30% might be too strict, which might close winners
                        if earned_proportion >= earned_proportion_threshold: 
                            # print(f"still in profits: {points_earned_so_far} points")
                            close_trade = False
                        else:
                            print(f"doesn't meet earned_proportion_threshold: {earned_proportion_threshold} of total tp. closing...") # if the "if condition is if earned_proportion >= 0" then this can never be run
                            close_trade = True
                    else:
                        # how come points_from_tp is greater than the full tp? that means we are in drawdown
                        points_earned_so_far = -abs(position.price_open - position.price_current) * position_symbol_multiply_digits
                        print(f"in drawdown. closing now...")
                        close_trade = True

                    if close_trade:
                        order_type = position.type
                        if order_type == 0:
                            close_type = 1
                        elif order_type == 1:
                            close_type = 0

                        print("Risk Management 4")
                        close_request(symbol=symbol, ticket=position.ticket, lot=position.volume, type_filling=type_filling, close_type=close_type)


                # check if there is news in just 1 minute. This happens when we open a trade and it's be more than 60 minutes, and the trade is still open. Now the news is ahead. We should close it 1 minute before news
                news_exist = get_news_data.trades_blocker_to_avoid_news(1, news_df)
                if news_exist:
                    order_type = position.type
                    if order_type == 0:
                        close_type = 1
                    elif order_type == 1:
                        close_type = 0
                    print("Closing trades due to news within 1 minute...")
                    close_request(symbol=symbol, ticket=position.ticket, lot=position.volume, type_filling=type_filling, close_type=close_type)


                # points_from_tp_limit is static. here it's tried dynamic based on the 0.1 risk to get tp
                dynamic_points_from_tp_limit = points_full_tp * 0.1

                # set sl to price_open, this should work for higher timeframes
                if points_from_tp <= dynamic_points_from_tp_limit: # points_from_tp_limit
                    if position.sl != position.price_open:
                        modify_sl_request(symbol=position.symbol, ticket=position.ticket, sl_price=position.price_open, tp_price=position.tp, type_filling=type_filling)


                    # #### this section counts down from 10 and then close the order ####
                    # # this means we are 3 pips away from TP
                    # # so let's count down
                    # count_down = 10
                    # for _ in range(0, count_down+1): # count down + 1 until zero
                    #     print(f"{count_down} s before closing the order...")
                    #     count_down -= 1
                    #     time.sleep(1)

                    # order_type = position.type
                    # if order_type == 0:
                    #     close_type = 1
                    # elif order_type == 1:
                    #     close_type = 0

                    # close_request(symbol=symbol, ticket=position.ticket, lot=position.volume, type_filling=type_filling, close_type=close_type)
                    # #### this section counts down from 10 and then close the order ####


                    # #### this section counts down for 2 ticks' time before looking for new trading chances ####
                    # CAUTION! #
                    # this section also fix an issue where an order is opened on the next candle after the previous tp candle, 
                    # because the price on the next candle is passing the previous 2 candles, and the offset limit is met, 
                    # and there is retracement or pause, so base on our code logic, it will open an order, which is an issue
                    # the offset limit only prevents opening an order immediately when tp is met on the candle where tp is taken
                    # but it cannot prevent opening another order on the next candle passing its previous 2 candles
                    ############
                    # after closing, count down for 2 ticks' time, say 5min chart, then it's 10minutes

                        # position.symbol == symbol means that if we're monitoring usdjpy, and it's a usdjpy position, then we count down
                        # but if we're monitoring eurusd, and it's a usdjpy position, then we do not count down
                        if count_down_after_modifying_sl and position.symbol == symbol: 
                            if timeframe == mt5.TIMEFRAME_M1:
                                pause_time = 2 * 1 * 60
                            elif timeframe == mt5.TIMEFRAME_M5:
                                pause_time = 2 * 5 * 60
                            elif timeframe == mt5.TIMEFRAME_M15:
                                pause_time = 2 * 15 * 60
                            elif timeframe == mt5.TIMEFRAME_M30:
                                pause_time = 2 * 30 * 60
                            elif timeframe == mt5.TIMEFRAME_H1:
                                pause_time = 2 * 60 * 60

                            # this is used to reset pause_time
                            # default_pause_time = pause_time

                            for _ in range(0, pause_time+1): # count down + 1 until zero
                                # print(f"{pause_time} s before looking for another trade...")
                                print(f"{pause_time} s before looking for another trade...", end="\r", flush=True)
                                pause_time -= 1
                                time.sleep(1)
                                # # in the meantime, if price moves to {points_from_tp_limit} points from tp
                                # if points_from_tp <= points_from_tp_limit:
                                #     pause_time = default_pause_time
                                # # then we need to recount down
                            # #### this section counts down for 2 ticks' time before looking for new trading chances ####
            
            # at the end of position check in this loop
            # move the curser back to the beginning of the line
            print(f"", end="\r", flush="True")   



            # open_positions > 0
            # sys.stdout.write(".")
            # sys.stdout.flush()

            # print(f"\t\t\t\t{timer}", end="\r", flush=True) # timer
            

        # time.sleep(0.1) # this is under the whole while loop. so we check if it's trading time & current open position status every 0.1 second # this is moved to the start of the while loop to fix crazy spinning bars when DT happens BUT continues
        # os.system('cls') # this will clean all the output, not what we expect
        # timer += 0.1 # timer




    # rates = get_last_three_ticks()
    # current_price = rates[2][4]

    # if not check_open_positions():


    #     sl = current_price * 1000 - rates[1][3] * 1000
    #     print(f"{sl}**********************************")
    #     open_request("buy", sl)

    #     # sl = rates[1][2] * 1000 - current_price * 1000
    #     # open_request("sell", sl)



# this function is functioning WRONG and is not used
def get_mt5_server_offset_hours():
    positions = mt5.positions_get()
    if not positions:
        raise RuntimeError("No open positions found — can't determine server time offset.")

    # Take the time of the first position
    trade_time = positions[0].time  # this is in server time (Unix timestamp)
    trade_time_dt = datetime.fromtimestamp(trade_time)

    # Get current UTC time
    utc_now = datetime.now(timezone.utc).replace(tzinfo=None)

    # this is WRONG!!!! because we are comparing the trade opening time (in the broker's timezone) with the CURRENT utc time, which is not neccessarily the trade open utc time.
    # we should compare the trade open time (broker time) with the trade open time (utc time)

    # Compute the offset between server time and UTC
    offset = trade_time_dt - utc_now
    offset_hours = round(offset.total_seconds() / 3600)

    print(f"trade_time_dt: {trade_time_dt}")
    print(f"utc_now: {utc_now}")
    print(f"offset seconds: {offset}")
    print(f"offset hours: {offset_hours}")
    
    return offset_hours



def convert_mt5_time_to_utc(trade_open_time_sec, broker_time_offset_hours_from_utc):
    # offset_hours = get_mt5_server_offset_hours()
    offset_hours = broker_time_offset_hours_from_utc
    open_time_utc = datetime.fromtimestamp(trade_open_time_sec, tz=timezone.utc) - timedelta(hours=offset_hours)
    return open_time_utc.replace(tzinfo=timezone.utc)



def find_dows_low(symbol="BTCUSD", timeframe=mt5.TIMEFRAME_M5, tick_count=30):
    rates = get_last_n_ticks(symbol=symbol, timeframe=timeframe, tick_count=tick_count)
    rates = np.flipud(rates)
    if rates[0]['low'] < rates[1]['low']:
        dows_low = rates[0]['low']
        return dows_low
    else:
        for i in range(1, len(rates)-1): # until the one before the last one, so that we have one tick on its left and one on its right
            if rates[i]['low'] <= compare_two_and_get_lower(rates[i+1]['low'], rates[i-1]['low']):
                dows_low = rates[i]['low']
                return dows_low

    return None

def find_dows_high(symbol="BTCUSD", timeframe=mt5.TIMEFRAME_M5, tick_count=30):
    rates = get_last_n_ticks(symbol=symbol, timeframe=timeframe, tick_count=tick_count)
    rates = np.flipud(rates)
    if rates[0]['high'] > rates[1]['high']:
        dows_high = rates[0]['high']
        return dows_high
    else:
        for i in range(1, len(rates)-1):
            if rates[i]['high'] >= compare_two_and_get_higher(rates[i+1]['high'], rates[i-1]['high']):
                dows_high = rates[i]['high']
                return dows_high
    return None



def calc_dm_plus_dm_minus(symbol="USDJPY", timeframe=mt5.TIMEFRAME_M15, start_position=0, tick_count=150, period=14): 
    # the result data_list only has 149 items, because the first tick has no previous tick for calculating 
    # so set tick_count to 151 if we want 150 ticks' data
    
    # 15 ticks. from 0 to 14
    
    # the first tick is not calculated for dm+ dm-, and tr, 
    # because we need a previous tick for calculating these, and the first tick doesn't have a previous tick

    # so the actual data_list we get is from the second one to the latest one, 
    # and we see the second one AS THE FIRST ONE

    rates = get_last_n_ticks(symbol=symbol, timeframe=timeframe, start_position=start_position, tick_count=tick_count)
    # we have 150 ticks index: [0-149]

    data_list = [] # store adx related data for each tick
    for i in range(0, tick_count-1): # until the one before the current tick        tick_count-1 is 149, so we will have index 148, so i+1 is 149, the current tick
        current_dict = {}
        
        # but actually we are using i+1 so we have the latest/current tick's info
        #+DM = current high - previous high.
        #-DM = previous low - current low.
        current_dict['dm_plus'] = rates[i+1]['high'] - rates[i]['high']
        current_dict['dm_minus'] = rates[i]['low'] - rates[i+1]['low']
        
        # Use +DM when current high - previous high > previous low - current low. Use -DM when previous low - current low > current high - previous high.
        if current_dict['dm_plus'] > current_dict['dm_minus']:
            if current_dict['dm_plus'] < 0:
                current_dict['dm_plus'] = 0
            current_dict['dm_minus'] = 0

        elif current_dict['dm_plus'] < current_dict['dm_minus']:
            if current_dict['dm_minus'] < 0:
                current_dict['dm_minus'] = 0
            current_dict['dm_plus'] = 0

        # TR is the greater of the current high - current low, abs(current high - previous close), or abs(current low - previous close)
        current_dict['tr'] = compare_two_and_get_higher(compare_two_and_get_higher(rates[i+1]['high'] - rates[i+1]['low'], abs(rates[i+1]['high'] - rates[i]['close'])), abs(rates[i+1]['low'] - rates[i]['close']))

        data_list.append(current_dict)

    # smoothed_dm_plus = 

    return data_list

"""
First TR14 = Sum of first 14 periods of TR1 
Second TR14 = First TR14 - (First TR14/14) + Current TR1 
Subsequent Values = Prior TR14 - (Prior TR14/14) + Current TR1
"""
def calc_tr14_dm_plus14_dm_minus14(data_list):
    # only need to calc the first tr14
    # so from 13, we have 14 TRs, and can calc the first tr14

    for i in range(0, 13):
        # set the first 13 (0-12) tr as 'N/A'
        data_list[i]['tr14'] = 'N/A'
        data_list[i]['dm_plus14'] = 'N/A'
        data_list[i]['dm_minus14'] = 'N/A'

    tr14 = 0
    dm_plus14 = 0
    dm_minus14 = 0

# at first I didn't add tr13 to the sum!!!!!! now it's OK with another loop from 0 to 14
    for i in range(0, 14): # from 0 to 13
        # calc the sum
        tr14 += data_list[i]['tr']
        dm_plus14 += data_list[i]['dm_plus']
        dm_minus14 += data_list[i]['dm_minus']



    data_list[13]['tr14'] = tr14
    data_list[13]['dm_plus14'] = dm_plus14
    data_list[13]['dm_minus14'] = dm_minus14

    for i in range(14, len(data_list)):
        previous_tr14 = data_list[i-1]['tr14']
        subsequent_tr14 = previous_tr14 - (previous_tr14/14) + data_list[i]['tr']
        data_list[i]['tr14'] = subsequent_tr14

        previous_dm_plus14 = data_list[i-1]['dm_plus14']
        subsequent_dm_plus14 = previous_dm_plus14 - (previous_dm_plus14/14) + data_list[i]['dm_plus']
        data_list[i]['dm_plus14'] = subsequent_dm_plus14

        previous_dm_minus14 = data_list[i-1]['dm_minus14']
        subsequent_dm_minus14 = previous_dm_minus14 - (previous_dm_minus14/14) + data_list[i]['dm_minus']
        data_list[i]['dm_minus14'] = subsequent_dm_minus14


    return data_list

def calc_di_plus_di_minus(data_list):
    for i in range(0, len(data_list)): 
        if data_list[i]['tr14'] == "N/A":
            data_list[i]['di_plus'] = "N/A"
            data_list[i]['di_minus'] = "N/A"
        else:
            # calc DI+
            di_plus = data_list[i]['dm_plus14'] / data_list[i]['tr14'] * 100
            di_minus = data_list[i]['dm_minus14'] / data_list[i]['tr14'] * 100
            data_list[i]['di_plus'] = di_plus
            data_list[i]['di_minus'] = di_minus
        
    return data_list

def calc_dx(data_list):
    for i in range(0, len(data_list)): 
        if data_list[i]['tr14'] == "N/A":
            data_list[i]['dx'] = "N/A"
        else:
            # calc dx
            dx = abs(data_list[i]['di_plus'] - data_list[i]['di_minus']) / abs(data_list[i]['di_plus'] + data_list[i]['di_minus']) * 100
            data_list[i]['dx'] = dx
        
    return data_list


# First ADX = sum 14 periods of DX / 14.
# After that, ADX = ((prior ADX * 13) + current DX) / 14.
def calc_adx(data_list):
    first_adx = 0
    for i in range(13, 13+14): # from 13 to 26 [13,26] or [13, 27) 27 not included
        first_adx += data_list[i]['dx']
    first_adx /= 14
    data_list[13+14-1]['adx'] = first_adx

    for i in range(0, 13+14-1):
        data_list[i]['adx'] = "N/A"

    for i in range(13+14, len(data_list)):
        previous_adx = data_list[i-1]['adx']
        subsequent_adx = (previous_adx * 13 + data_list[i]['dx']) / 14
        data_list[i]['adx'] = subsequent_adx

    return data_list


def get_current_adx(symbol="USDJPY", timeframe=mt5.TIMEFRAME_M15, start_position=0, tick_count=150):
    data_list = calc_dm_plus_dm_minus(symbol=symbol, timeframe=timeframe, start_position=start_position, tick_count=tick_count)
    data_list = calc_tr14_dm_plus14_dm_minus14(data_list)
    data_list = calc_di_plus_di_minus(data_list)
    data_list = calc_dx(data_list)
    data_list = calc_adx(data_list)
    current_adx = data_list[-1]['adx']
    # current_adx = round(current_adx, 2)
    return current_adx

def get_last_n_adx(symbol="USDJPY", timeframe=mt5.TIMEFRAME_M15, start_position=0, tick_count=150, n=3):
    data_list = calc_dm_plus_dm_minus(symbol=symbol, timeframe=timeframe, start_position=start_position, tick_count=tick_count)
    data_list = calc_tr14_dm_plus14_dm_minus14(data_list)
    data_list = calc_di_plus_di_minus(data_list)
    data_list = calc_dx(data_list)
    data_list = calc_adx(data_list)
    last_n_data_list = data_list[-n:]
    last_n_adx_list = [item['adx'] for item in last_n_data_list]
    return last_n_adx_list

def check_adx_ascending(symbol="USDJPY", timeframe=mt5.TIMEFRAME_M15, n=3):
    is_valid = False
    last_n_adx_list = get_last_n_adx(symbol=symbol, timeframe=timeframe, start_position=0, tick_count=150, n=n)

    # hard code # because we only compare 2 ADXs or at most maybe 3 ADXs
    if n == 2:
        if last_n_adx_list[0] < last_n_adx_list [1]:
            print(f"ascending adx. OK to place order")
            is_valid = True
        else:
            print(f"Latest {n} ascending adxes are not ascending. Aborted")

        print(f"{last_n_adx_list[0]}, {last_n_adx_list[1]}")
        return is_valid    
    
    elif n == 3:
        if last_n_adx_list[0] < last_n_adx_list[1] < last_n_adx_list[2]:
            print(f"ascending adx. OK to place order")
            is_valid = True
        else:
            print(f"Latest {n} ascending adxes are not ascending. Aborted")

        print(f"{last_n_adx_list[0]}, {last_n_adx_list[1]}, {last_n_adx_list[2]}")
        return is_valid

    else:
        print(f"n is hard-coded to support only 2 or 3 adx comparison. the input n is {n}, which is unexpected")
        return is_valid # which is false


def check_if_adx_meets_requirements(symbol="USDJPY", timeframe=mt5.TIMEFRAME_M15, adx_threshold=25):
    current_adx = get_current_adx(symbol=symbol, timeframe=timeframe, start_position=0, tick_count=150)
    if current_adx >= adx_threshold:
        print(f"current_adx: {current_adx}")
        print(f"adx >= {adx_threshold}. OK to place order.")
        return True
    else:
        print(f"current_adx: {current_adx}")
        print(f"adx < {adx_threshold}. aborted.")
        return False

# positions is a set. if no positions, it's an empty set
def get_positions_by_symbol(symbol="USDJPY"):
    positions=mt5.positions_get(symbol=symbol)
    if len(positions) == 0:
        print(f"No positions on {symbol}, positions = {positions}, error code={mt5.last_error()}")
    elif len(positions) > 0:
        # print(f"Total positions on {symbol} = {len(positions)}")
        # # display all open positions
        # for position in positions:
        #     print(position)
        #     print(type(position))
        pass
    
    return positions


def get_positions_by_group(group="*USD*"):
    # get the list of positions on symbols whose names contain "*USD*"
    usd_positions=mt5.positions_get(group=group)
    if usd_positions==None:
        print("No positions with group=\"*USD*\", error code={}".format(mt5.last_error()))
    elif len(usd_positions)>0:
        print("positions_get(group=\"*USD*\")={}".format(len(usd_positions)))
        # display these positions as a table using pandas.DataFrame
        df=pd.DataFrame(list(usd_positions),columns=usd_positions[0]._asdict().keys())
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.drop(['time_update', 'time_msc', 'time_update_msc', 'external_id'], axis=1, inplace=True)
        print(df)    


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

def algo_trading_prompt():
    confirmation = input("Is Algo Trading enabled? [Y/n]")
    if confirmation == "":
        pass # OK
    elif confirmation.capitalize() != "Y":
        quit()

def select_mt5_path(main_path, practice_path):
    path = main_path
    print(f"current path: {path}")
    print(f"1. main_mt5 path: {main_path}")
    print(f"2. practice_path: {practice_path}")
    confirmation = input("Enter to continue or select a path: ")
   
    if confirmation == "":
        pass
    elif confirmation == "1":
        path = main_path
    elif confirmation == "2":
        path = practice_path

    print(f"confirmed, using {path}")
    
    return path

def select_account(
        account_demo, password_demo, server_demo, 
        account_live, password_live, server_live,
        saved_last_manually_input_account_id, saved_last_manually_input_account_password, saved_last_manually_input_account_server,
        account, password, server_to_connect):
    print(f"current account: {account}")
    print(f"1. live account {account_live}")
    print(f"2. demo account {account_demo}")
    print(f"3. manually input account ID")
    print(f"4. last manually input account ID {saved_last_manually_input_account_id}")
    confirmation = input("Enter to continue, or choose an account: ")

    if confirmation == "":
        pass
    elif confirmation == '1':
        account = account_live
        password = password_live
        server_to_connect = server_live
    elif confirmation == '2':
        account = account_demo
        password = password_demo
        server_to_connect = server_demo
    elif confirmation == '3':
        account = int(input("account: "))
        password = getpass()
        print(f"1. {server_demo}")
        print(f"2. {server_live}")
        selected_server = input("select a server or directly input the server string: ")
        if selected_server == '1':
            server_to_connect = server_demo
        elif selected_server == '2':
            server_to_connect = server_live
        else:
            server_to_connect = selected_server

        save_account_n_password = input("Save account and password? [Y/N]")
        if save_account_n_password in ["Y", "y", "Yes", "yes", ""]:
            # hard-coded path
            # path = r"D:\yue\Documents\python_projects\forex\mt5_trading\credential_info.py"
            # dynamic path
            # Get the absolute path of the current script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Create a path to the file in the same directory
            path = os.path.join(script_dir, "credential_info.py")
            with open(path, "r+") as f:
                f_lines = f.readlines()
                # print(f_lines)
                edited_f_lines = []
                for line in f_lines:
                    if "saved_last_manually_input_account_id" in line:
                        line = "saved_last_manually_input_account_id = " + str(account) + "\n"
                    if "saved_last_manually_input_account_password" in line:
                        line = "saved_last_manually_input_account_password = '" + str(password) + "'\n"
                    if "saved_last_manually_input_account_server" in line:
                        line = "saved_last_manually_input_account_server = '" + server_to_connect + "'\n"
                    edited_f_lines.append(line)
                

                # print(edited_f_lines)
                # After using readlines the pointe is at the end of the file, so if I don't file.seek then I will append the content to the original content
                # Reposition the file pointer to the beginning of the file
                f.seek(0)
                f.writelines(edited_f_lines)
        else:
            pass
        

        

    elif confirmation == '4':
        account = saved_last_manually_input_account_id
        password = saved_last_manually_input_account_password
        server_to_connect = saved_last_manually_input_account_server

    return account, password, server_to_connect

def check_if_its_trading_time():
    current_time = datetime.now()
    current_time_str = current_time.strftime("%H: %M: %S")
    splitted_current_time_str = current_time_str.split(":")
    current_hour = int(splitted_current_time_str[0])

    # temprarily hard coded to convert dublin time to beijing time
    # current_hour += 8 # only for winter time # we cannot just +8, what if 23:00??
    # 9.00 - 23.00 beijing time
    # 1.00 - 15.00 dublin

    current_minute = int(splitted_current_time_str[1])
    current_second = int(splitted_current_time_str[2])
    # print(f"current_hour: {current_hour}")
    # print(f"current_minute: {current_minute}")
    # print(f"current_second: {current_second}")
    # input()

    # >>> datetime.now().strftime("%H: %M: %S")         
    # output
    # '00: 04: 42'  4 minutes after midnight

    # if current_hour == 23: # there's no 24 i guess
    #     print(f"It's {current_hour}: {current_minute}: {current_second}. We need to follow our plan. Call it a day." )
    #     mt5.shutdown()
    #     quit()
    # hour_to_start_trading = 9
    # hour_to_end_trading = 23

    # normal time
    # hour_to_start_trading = 1 # 1 (utc+0) = 9 (utc+8)
    # hour_to_end_trading = 15 # 15(utc+0) = 23 (utc+8)
    # summer time
    hour_to_start_trading = 2 # 2am (utc+1) equal to 2+7=9am (utc+8)
    hour_to_end_trading = 16 # utc+1 => 16+7 = 23 (utc+8)

    # hour_to_start_trading = 7
    # hour_to_end_trading = 1
    # if hour_to_end_trading == 23:
    #     hour_to_end_trading = -1
    # if current_hour == 23:
    #     current_hour = -1
    # if current_hour < 7 or current_hour == 23: # trading from 7am to 23pm
    # if current_hour < 8 or current_hour == 23: # trading from 8am to 23pm
    # if hour_to_end_trading <= current_hour < hour_to_start_trading: # trading from 7am all the way to 1am dawn next day, one hour after London Close # only when current hour is 1,2,3,4,5,6 the condition is true
    if hour_to_start_trading <= current_hour < hour_to_end_trading:
        return True
    else:
    # if current_hour < 9 or current_hour == 23: # trading from 9am to 23pm
        # if current_hour == 23: # if 23, the remaining hours will be minus. 23 is equivelant to -1
        #     current_hour = -1
        # time_remaining_in_minutes = 8*60 - current_hour * 60 - current_minute
        # total_remaining_seconds = 8 * 60 * 60 - current_hour * 60 * 60 - current_minute * 60 - current_second # starts at 8am
        # total_remaining_seconds = 7 * 60 * 60 - current_hour * 60 * 60 - current_minute * 60 - current_second # starts at 7am
        # total_remaining_seconds = 9 * 60 * 60 - current_hour * 60 * 60 - current_minute * 60 - current_second # starts at 9am

        # I don't think this is necessary. it seems redundant
        # if current_hour == 0:
        #     current_hour = 24
        #     hour_to_start_trading += 24 # this is absolutely wrong here# seems i wanted to put it in the if currenthour == 0 if condition. but even that is incorrect, or redundant

        # i guess it should be:
        if current_hour >= hour_to_end_trading:
            hour_to_start_trading += 24


        total_remaining_seconds = hour_to_start_trading * 60 * 60 - current_hour * 60 * 60 - current_minute * 60 - current_second # starts at 7am
        # 5:43 8:00
        # 8*60-5*60-43
        # 7:00 8:00
        # 5:43:16 8:00:00
        # 8 * 60 * 60 - 5 * 60 * 60 - 43 * 60 - 16
        remaining_hours = total_remaining_seconds // 60 // 60
        remaining_minutes = (total_remaining_seconds - remaining_hours * 60 * 60) // 60
        remaining_seconds = total_remaining_seconds - remaining_hours * 60 * 60 - remaining_minutes * 60

        remaining_hours = check_n_add_zero_b4_1_digit_natural_nums(remaining_hours)
        remaining_minutes = check_n_add_zero_b4_1_digit_natural_nums(remaining_minutes)
        remaining_seconds = check_n_add_zero_b4_1_digit_natural_nums(remaining_seconds)

        print(f"                                                            It's {current_time_str}. \
            Time remaining: {remaining_hours}: {remaining_minutes}: {remaining_seconds}          ", end="\r", flush=True)
        
        # At the beginning of the trading time, it will print "00: 00: 01", which is not pretty. Because when it's trading time, we don't have the chance to go into this condition to print.
        # Trying to resolve this.
        if remaining_hours == "00" and remaining_minutes == "00" and remaining_seconds == "01":
            time.sleep(1) # wait for 1 sec to simulate
            remaining_seconds = "00"
            # get current time again, now it should be sharp trading start time
            current_time = datetime.now()
            current_time_str = current_time.strftime("%H: %M: %S")
            print(f"                                                            It's {current_time_str}. \
                Time remaining: {remaining_hours}: {remaining_minutes}: {remaining_seconds}          ", end="\n", flush=True) # with end="\n", we go to the next line, so that when we exit the checking trading func, we can print info in the next line
            print("Happy trading!")

        # time.sleep(0.5)
        return False
    # else:
    #     return True
           
def check_n_add_zero_b4_1_digit_natural_nums(num):
    if 0 <= num <= 9:
        num = '0' + str(num)
        return num # str
    else: # IMPORTANT!!! if it's not 1 digit num, we need to return it as is
        # return num # int
        return str(num) # now it's also str

def get_broker_time_n_utc_time_offset(symbol):
    symbol_info = check_symbol_info(symbol)    
    broker_time = datetime.fromtimestamp(symbol_info.time, tz=timezone.utc)
    utc_time = datetime.now(timezone.utc)
    time_offset = broker_time - utc_time
    hours_offset = time_offset.total_seconds() / 3600
    hours_offset_int = round(hours_offset)

    print(f"broker_time: {broker_time}")
    print(f"utc_time: {utc_time}")
    print(f"time_offset: {time_offset}")
    print(f"hours_offset: {hours_offset}")
    print(f"hours_offset_int: {hours_offset_int}")

    return hours_offset_int


def main():
    # # main mt5 path
    main_path = r"C:\Program Files\MetaTrader 5\terminal64.exe"
    # # practicing mt5 path
    practice_path = r"E:\Program Files\MetaTrader 5\terminal64.exe"

    # fxtm live
    account_live = credential_info.live_account_id # must be int, not string
    password_live = credential_info.password
    server_live = credential_info.server_live

    # # IC demo
    # account_demo = 50919338
    # password_demo = credential_info.password_ICDemo
    # server_demo = 'ICMarketsSC-Demo'

    # fxtm demo
    account_demo = credential_info.demo_account_id # 160299611 #160265336       ##160260280 # invalid #most used            #160255142 #reverse
    password_demo = credential_info.password2
    server_demo = credential_info.server_demo

    # last manually input info
    saved_last_manually_input_account_id = credential_info.saved_last_manually_input_account_id
    saved_last_manually_input_account_password = credential_info.saved_last_manually_input_account_password
    saved_last_manually_input_account_server = credential_info.saved_last_manually_input_account_server

    # choose demo account
    account = account_demo
    password = password_demo
    server_to_connect = server_demo

    # # choose live account
    # account = account_live
    # password = password_live
    # server_to_connect = server_live

    algo_trading_prompt()
    path = select_mt5_path(main_path, practice_path)
    initialize(path)

    account, password, server_to_connect = select_account(
        account_demo, password_demo, server_demo, 
        account_live, password_live, server_live,
        saved_last_manually_input_account_id, saved_last_manually_input_account_password, saved_last_manually_input_account_server,
        account, password, server_to_connect)
    
    login(account, password, server_to_connect)

    # historical_orders()
    # historical_deals()

    ################# variables for dt_strategy function ################
    # broker_time_offset_hours_from_utc = 3 # 3 means that mt5 is utc+3
    # symbol="BTCUSD"
    # symbol = "XAUUSD"
    symbol = input("Enter the symbol to trade: (default USDJPY.p)")
    if symbol == "":
        symbol = "USDJPY.p"
    # symbol = "EURUSD.p"
    # symbol="AUDUSD"
    type_filling = mt5.ORDER_FILLING_IOC # dominion markets
    # type_filling = mt5.ORDER_FILLING_IOC # IC
    # type_filling = mt5.ORDER_FILLING_FOK # FXTM
    # timeframe = mt5.TIMEFRAME_M1
    # timeframe = mt5.TIMEFRAME_M5
    # timeframe = mt5.TIMEFRAME_M15
    timeframe = mt5.TIMEFRAME_M30
    # timeframe = mt5.TIMEFRAME_H1

    broker_time_offset_hours_from_utc = get_broker_time_n_utc_time_offset(symbol)
    print(f"broker_time_offset_hours_from_utc: {broker_time_offset_hours_from_utc}")
    print()

    # sl_limit = 600 #520 #320 #200 # points for USDJPY # 300
    # sl_limit = 270
    # body_points_limit = 160

    sl_limit = 300 #360 # for usdjpy previous setting was 650
    # sl_limit = 800 #350 # setting to 500 for XAUUSD testing
    sl_min = 100
    # body points limit is used for crossing sma setups, where the crossing candle's body should be be too big.
    body_points_limit = 300 # setting it to 400 points for XAUUSD testing 
    # for usdjpy I set it to 200
    
    points_gap_between_ideal_n_current_limit = 30 # setting it to 15points is TOO TIGHT. might not open order on gold as the spread is already 15-20 points

    # distance between ideal opening price & current price  
    offset_limit = 20 # 10 # points for USDJPY
    # the offset limit only prevents opening an order immediately when tp is met on the candle where tp is taken
    # but it cannot prevent opening another order on the next candle passing its previous 2 candles
    # the workaround is we use a timer to count down after price is {points_from_tp_limit} points away from tp
    # so if during counting down tp is hit, then it needs to recount.

    # if we are two pips shy of TP, we will take actions like moving sl to breakeven
    points_from_tp_limit = 30 #20 # points
    # points_from_tp_limit = 0 # disable

    added_points_to_sl = 0 # don't add any pips. set to 10 to add 1 pip # add 1 pips to sl, so that the sl is 1 pip below the dow's low, but I find it usually not beneficial, because if it is a winner then usually price won't go that back

    added_points_to_tp = 10 # add 1 pip to tp, so that the tp can cover the fees including commission and spreads, making the risk reward ratio to be 1 to 1

    # specify the commision for each lot here and make sure to pass it in the following open_request() functions
    # currently it is not included in the parameters
    commission_per_lot = 7 #4

    risk_ratio = 0.05 # 0.01 # 2% 5%

    risk_reward_ratio = 1 #1:3 risk:reward 2:1
    # risk_reward_ratio = 0.33 #1:3 risk:reward 2:1

    # to make the actual tp to 75% of theo tp
    tp_percent = 1 # 0.75

    fixed_tp = False
    fixed_tp_in_points = 50

    # set hedge to true to look for a second postion which is an opposite position if DT break happens during the first positon's drawdown
    # if we are in a buy, and price goes into drawdown, and DT break occurs, then a sell is opened (if other requirements including consistency, sma, etc) while the first position is left running.
    hedge = False

    # check if adx is greater or equal than this value, usually set to 20 or 25
    adx_threshold = 20
    is_check_adx_threshold_enabled= False
    is_check_adx_ascending_enabled = False

    # # used to print how many seconds it runs, 
    # # also if the program freezes, the print output will not change, which draws us attention
    # timer = 0

    count_down_after_modifying_sl = False
    check_if_trading_time = True # there's a func called check_if_its_trading_time # do not use that same name or it will cause issues
    
    # enabled
    check_timeframe_consistency = False
    # enable: buy above sma, sell below sma. disable: buy/sell as long as price goes beyond ticks and other requirements are met.
    check_above_or_below_sma = True
    # check if SMAs in different timeframes are standing in the way towards our tp
    check_sma_resistance = False

    # # disabled
    # check_timeframe_consistency = False
    # # enable: buy above sma, sell below sma. disable: buy/sell as long as price goes beyond ticks and other requirements are met.
    # check_above_or_below_sma = True
    # # check if SMAs in different timeframes are standing in the way towards our tp
    # check_sma_resistance = False


    pattern_list = ["\\", "|", "/", "-"]
    pattern_index = 0

    ################# end of variables for dt_strategy function ################

    # confirm risk per trade
    print(f"risk_ratio is {risk_ratio}, or {risk_ratio * 100}%")
    risk_ratio_confirm = input("Press enter to confirm or input a new risk_ratio: ") # 0.00001
    if risk_ratio_confirm == '':
        pass
    else:
        risk_ratio = float(risk_ratio_confirm)
    print(f"confirmed risk_ratio is {risk_ratio}, or {risk_ratio * 100}%")

    # confirm sl_limit, sl_min, body_points_limit
    print(f"sl_limit: {sl_limit}")
    print(f"sl_min: {sl_min}")
    print(f"body_points_limit: {body_points_limit}")


    # get news dataframe
    news_df = get_news_data.get_news_df()
    # print all news_df
    print("All news this week:")
    print(news_df)
    print("Important news related to USDJPY:")
    # print only high impact and USD JPY related
    print(news_df[
        (news_df["importance"].isin(["High"])) &
        (news_df["country"].isin(["USD", "JPY"]))
    ])
    

    # A place to store per-trade state ---
    trade_state = {}   # key = ticket, value = dict(entry_price, stop_dist, mpe, start_time)


    double_tick_strategy(symbol, type_filling, timeframe, sl_limit, sl_min, body_points_limit, points_gap_between_ideal_n_current_limit,
                         offset_limit, points_from_tp_limit, commission_per_lot, risk_ratio, risk_reward_ratio, tp_percent, 
                         check_timeframe_consistency, count_down_after_modifying_sl, check_above_or_below_sma, check_if_trading_time, check_sma_resistance,
                         pattern_list, pattern_index, added_points_to_sl, added_points_to_tp, fixed_tp, fixed_tp_in_points, hedge, 
                         adx_threshold, is_check_adx_threshold_enabled, is_check_adx_ascending_enabled,
                         broker_time_offset_hours_from_utc, news_df, trade_state)
    # symbol="XAUUSD"
    # point = mt5.symbol_info(symbol).point
    # print(point)

    # shut down connection to the MetaTrader 5 terminal
    #### mt5.shutdown() # code unreachable

if __name__ == "__main__":
    main()
