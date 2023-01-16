import time
import traceback
import MetaTrader5 as mt5
import numpy as np
import credential_info

# import the 'pandas' module for displaying data obtained in the tabular form
import pandas as pd
pd.set_option('display.max_columns', 500) # number of columns to be displayed
pd.set_option('display.width', 1500)      # max table width to display


from mt5_origin import initialize, login, get_last_n_ticks, find_dows_low, find_dows_high, calculate_lot_size, compare_two_and_get_lower, compare_two_and_get_higher


path = r"C:\Program Files\MetaTrader 5\terminal64.exe"

# fxtm live
account_live = 10557130
password_live = credential_info.password
server_live = "ForexTimeFXTM-Live01"

account_demo = 160265336            ##160260280 #most used            #160255142 #reverse
password_demo = credential_info.password2
server_demo = 'ForexTimeFXTM-Demo01'

# account = account_demo
# password = password_demo
# server_to_connect = server_demo


account = account_live
password = password_live
server_to_connect = server_live


symbol = "USDJPY"
# timeframe = mt5.TIMEFRAME_M15
timeframe = mt5.TIMEFRAME_H1
risk_ratio = 0.05
risk_reward_ratio = 1

manual_sl_ratio = 0.65
manual_tp_ratio = 1


initialize(path)
login(account, password, server_to_connect)



def pending_order(sl_price, entry_price, lot= 0.01, type="buy", sl=100, symbol="USDJPY", type_filling=mt5.ORDER_FILLING_FOK, risk_reward_ratio=2):
    # lot = 0.1
    # lot = calculate_lot_size(sl=sl, symbol=symbol, risk_ratio=risk_ratio, commision_per_lot=commision_per_lot) # sl, symbol, risk_ratio=0.05, commision_per_lot=4

    point = mt5.symbol_info(symbol).point    #EURUSD point: 1e-05   #BTCUSD point: 0.01 
    #####################
    # attention: the point here is not stop_loss_in_pips * 10. Instead, it's a decimal, telling us how many digits there are.
    #####################
    # price = mt5.symbol_info_tick(symbol).ask
    price = entry_price

    deviation = 20


    if type == "buy":
        type = mt5.ORDER_TYPE_BUY_STOP
    elif type == "sell":
        type = mt5.ORDER_TYPE_SELL_STOP
        # if sell, sl shoult be price -  100* (-point)
        point = -point
    
    # in points
    tp = (sl - 15) / risk_reward_ratio  # sl - 1 pip above dow's high (or below low ) and - 0.5 pip when price goes pass previous two ticks
    # tp = sl / risk_reward_ratio
    
    # safe TP that could be reached
    tp = tp * manual_tp_ratio

    request = {
        "action": mt5.TRADE_ACTION_PENDING,
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

def market_execution(sl_price, lot= 0.01, type="buy", sl=100, symbol="USDJPY", type_filling=mt5.ORDER_FILLING_FOK, risk_reward_ratio=2):
    # lot = 0.1
    # lot = calculate_lot_size(sl=sl, symbol=symbol, risk_ratio=risk_ratio, commision_per_lot=commision_per_lot) # sl, symbol, risk_ratio=0.05, commision_per_lot=4

    point = mt5.symbol_info(symbol).point    #EURUSD point: 1e-05   #BTCUSD point: 0.01 
    #####################
    # attention: the point here is not stop_loss_in_pips * 10. Instead, it's a decimal, telling us how many digits there are.
    #####################
    price = mt5.symbol_info_tick(symbol).ask
    # price = entry_price
    

    deviation = 20


    if type == "buy":
        type = mt5.ORDER_TYPE_BUY
    elif type == "sell":
        type = mt5.ORDER_TYPE_SELL
        # if sell, sl shoult be price -  100* (-point)
        point = -point
    
    # in points
    tp = (sl - 15) / risk_reward_ratio  # sl - 1 pip above dow's high (or below low ) #### and - 0.5 pip when price goes pass previous two ticks
    # tp = sl / risk_reward_ratio
    
    # safe TP that could be reached
    tp = tp * manual_tp_ratio

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


while True:
    print()
    print(f"symbol: {symbol}")
    print(f"timeframe: {timeframe}")
    digits = mt5.symbol_info(symbol).digits # BTC digits -> 2         mt5.symbol_info(symbol).xxx, not mt5.symbol_info_tick(symbol).xxx
    multiply_digits = 10 ** digits

    point = mt5.symbol_info(symbol).point

    direction = input("Buy or Sell? [B/S] (enter 'C' to switch symbol)")

    rates = get_last_n_ticks(symbol, timeframe, 0, 3)

    if direction.capitalize() == "B":
        ideal_entry_price = compare_two_and_get_higher(rates[0]['high'], rates[1]['high'])
        dows_low = find_dows_low(symbol=symbol, timeframe=timeframe, tick_count=12)

        # make it safer, 
        # entry price is 5 points away
        # sl price is dows_low_price - 1 pip (10 points)
        ideal_entry_price = ideal_entry_price + 5 * point
        dows_low = dows_low - 10 * point

        if dows_low:
            current_price = rates[2]['close']
            if current_price >= ideal_entry_price:
                sl = current_price * multiply_digits - dows_low * multiply_digits # this is only for calcing lot
                lot = calculate_lot_size(sl, symbol, risk_ratio=risk_ratio, commision_per_lot=4)
                ideal_sl = ideal_entry_price * multiply_digits - dows_low * multiply_digits # to calc the safe tp precisely, we need the ideal sl (points/pips) 
                input("Market execution buy. Press any key to continue")
                market_execution(sl_price=dows_low, lot=lot, type="buy", sl=ideal_sl, symbol=symbol, type_filling=mt5.ORDER_FILLING_FOK, risk_reward_ratio=risk_reward_ratio)
            else:
                sl = ideal_entry_price * multiply_digits - dows_low * multiply_digits
                lot = calculate_lot_size(sl, symbol, risk_ratio=risk_ratio, commision_per_lot=4)
                input("Buy stop. Press any key to continue")
                pending_order(sl_price=dows_low, entry_price=ideal_entry_price, lot=lot, type="buy", sl=sl, symbol=symbol, type_filling=mt5.ORDER_FILLING_FOK, risk_reward_ratio=risk_reward_ratio)
        else:
            print(f"didn't find dows_low in previous ticks, won't open order")
            

    elif direction.capitalize() == "S":
        ideal_entry_price = compare_two_and_get_lower(rates[0]['low'], rates[1]['low'])
        dows_high = find_dows_high(symbol=symbol, timeframe=timeframe, tick_count=12)

        # make it safer, 
        # entry price is 5 points away
        # sl price is dows_low_price - 1 pip (10 points)
        ideal_entry_price = ideal_entry_price - 5 * point
        dows_high = dows_high + 10 * point

        if dows_high:
            current_price = rates[2]['close']
            if current_price <= ideal_entry_price:
                sl = dows_high * multiply_digits - current_price * multiply_digits
                lot = calculate_lot_size(sl, symbol, risk_ratio=risk_ratio, commision_per_lot=4)
                ideal_sl= dows_high * multiply_digits - ideal_entry_price * multiply_digits
                input("Market execution sell. Press any key to continue")
                market_execution(sl_price=dows_high, lot=lot, type="sell", sl=ideal_sl, symbol=symbol, type_filling=mt5.ORDER_FILLING_FOK, risk_reward_ratio=risk_reward_ratio)
            else:
                sl = dows_high * multiply_digits - ideal_entry_price * multiply_digits
                lot = calculate_lot_size(sl, symbol, risk_ratio=risk_ratio, commision_per_lot=4)
                input("Sell stop. Press any key to continue")                
                pending_order(sl_price=dows_high, entry_price=ideal_entry_price, lot=lot, type="sell", sl=sl, symbol=symbol, type_filling=mt5.ORDER_FILLING_FOK, risk_reward_ratio=risk_reward_ratio)
        else:
            print(f"didn't find dows_high in previous ticks, won't open order")


    elif direction.upper() in ["EUR", "EURUSD"]:
        symbol = "EURUSD"
    elif direction.upper() in ['YEN', 'JPY', 'USDJPY']:
        symbol = "USDJPY"
    elif direction in ['h1', '1']:
        timeframe = mt5.TIMEFRAME_H1
    elif direction in ['m30', '30']:
        timeframe = mt5.TIMEFRAME_M30
    elif direction in ['m15', '15']:
        timeframe = mt5.TIMEFRAME_M15
    elif direction in ['m5', '5']:
        timeframe = mt5.TIMEFRAME_M5
    elif direction.capitalize() == "C":
        change_symbol = input("Enter a pair to switch to: (e.g. EURUSD)")
        if change_symbol != "":
            symbol = change_symbol.upper() 

    # elif direction.capitalize() == "C":
    #     change_symbol = input("Change symbol to: (Enter to skip)")
    #     if change_symbol != "":
    #         symbol = change_symbol.upper()

    elif direction.capitalize() == "T":
        change_timeframe = input("Change timeframe to: (Enter to skip)")
        if change_timeframe == "h4":
            timeframe = mt5.TIMEFRAME_H4
        elif change_timeframe == "h1":
            timeframe = mt5.TIMEFRAME_H1
        elif change_timeframe == "m30":
            timeframe = mt5.TIMEFRAME_M30
        elif change_timeframe == "m15":
            timeframe = mt5.TIMEFRAME_M15
        elif change_timeframe == "m5":
            timeframe = mt5.TIMEFRAME_M5
        elif change_timeframe == "m1":
            timeframe = mt5.TIMEFRAME_M1
        else:
            print("invaid timeframe")
        
        
