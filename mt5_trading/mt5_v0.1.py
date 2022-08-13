from http import server
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


def initialize():
    if not mt5.initialize():
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


def get_last_three_ticks(symbol="USDJPY", timeframe=mt5.TIMEFRAME_M15):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 3)
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


def open_request(type="buy", sl="100", symbol="USDJPY", type_filling=mt5.ORDER_FILLING_FOK):
    
    lot = 0.1
    point = mt5.symbol_info(symbol).point
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
        "sl": price - sl * point, # "sl": price - 100 * point,
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
        print("shutdown() and quit")
        mt5.shutdown()
        quit()
    
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
    """

    symbol="BTCUSD"
    type_filling = mt5.ORDER_FILLING_IOC

    while True:
        
        open_positions = check_open_positions()
        if open_positions == 0:
            rates = get_last_three_ticks(symbol=symbol, timeframe=mt5.TIMEFRAME_M5)
            # print(rates)
            current_price = rates[2][4]

            if current_price > rates[0][2] and current_price > rates[1][2]:   
                print("buy")
                # sl = current_price * 1000 - rates[1][3] * 1000  # USDJPY
                sl = current_price * 100 - rates[1][3] * 100  # BTC
                open_request(type="buy", sl=sl, symbol=symbol, type_filling=type_filling)
                continue
            if current_price < rates[0][3] and current_price < rates[1][3]:
                print("sell")
                # second_tick_high-current_price
                # sl = rates[1][2] * 1000 - current_price * 1000  # USDJPY
                sl = rates[1][2] * 100 - current_price * 100  # BTC
                open_request(type="sell", sl=sl, symbol=symbol, type_filling=type_filling)
                continue
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
