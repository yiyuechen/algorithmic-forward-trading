import numpy
import random
#import matplotlib.pyplot as plt
#from matplotlib.pyplot import MultipleLocator
import plotly.express as px
from tabulate import tabulate

from decimal import Decimal

import urllib3
from bs4 import BeautifulSoup

def convert_to_decimal(value_to_convert):
    # If a decimal number is defined using quotes ' ', it will be saved as a string rather than as a float.
    # convert to str, so it's the same as adding quotations with a number.
    # if the str is 0.58, then Decimal(value) is Decimal("0.58")
    value_str = str(value_to_convert) 
    
    # now value is a decimal type
    value_decimal = Decimal(value_str)

    return value_decimal

def generate_rand_trading_results(ideal_trade_count, win_rate, break_even_rate): # win_rate 0.58, break_even_rate 0.06
    """
    generates a rand list that contains win trades and loss trades with a designated win rate, say 55% (0.55)
    Parameters:
      ideal_trade_count - 假设胜率是从这么多次交易统计出来的
      win_rate - 固定胜率
    """
    
    rand = numpy.zeros(ideal_trade_count, dtype=int)

    # win_rate = str(win_rate) 
    # win_rate = Decimal(win_rate)

    win_rate = convert_to_decimal(win_rate)
    win_trade_count = int(ideal_trade_count * win_rate) # need to convert to int for list slicing
    # print(win_trade_count)
    # 把前百分之多少的改为win
    rand[:win_trade_count] = 1

    # 把最后百分之多少的改为breakeven
    break_even_rate = convert_to_decimal(break_even_rate)
    break_even_trade_count = int(ideal_trade_count*break_even_rate)
    rand[-break_even_trade_count:] = -1

    # 随机摇匀
    numpy.random.shuffle(rand)
    # 由于下面是随机在里面取，而且每次都是独立取，可以重复，其实不摇均匀也没关系
    # 好像不摇动均匀有关系，因为抽签通常都会摇匀

    # print(rand)
    # i = 0
    # for item in rand:
    #     if item == -1:
    #         i+=1
    # print(i/len(rand)) # it's 0.06
    
    return rand

# With this strategy, some of the winning trades we only hit a few pips and run, just in case the price reverses.
# We can expect a higher win rate by doing this strategy, say 70%, theoretically 80% is not impossible. 
def generate_rand_trading_results_with_hit_and_run_strategy(ideal_trade_count, win_rate, hit_and_run_rate):
    rand = numpy.zeros(ideal_trade_count, dtype=int)
    win_rate = convert_to_decimal(win_rate)
    win_trade_count = int(ideal_trade_count * win_rate) # need to convert to int for list slicing
    # print(win_trade_count)
    # 把前百分之多少的改为win
    rand[:win_trade_count] = 1

    # 把胜利的里面的百分之多少改为小赚就跑的
    hit_and_run_rate = convert_to_decimal(hit_and_run_rate)
    hit_and_run_win_trade_count = int(win_trade_count*hit_and_run_rate)
    rand[:hit_and_run_win_trade_count] = 2 # 因为rand的dtype=int是int其实让dtype=float

    # return rand

    # 随机摇匀
    numpy.random.shuffle(rand)
    # 由于下面是随机在里面取，而且每次都是独立取，可以重复，其实不摇均匀也没关系
    # 好像不摇动均匀有关系，因为抽签通常都会摇匀

    # print(rand)
    
    return rand

def generate_rand_trading_results_with_let_trades_run(ideal_trade_count, win_rate, break_even_rate, let_trade_run_rate):
    rand = numpy.zeros(ideal_trade_count, dtype=int)
    win_rate = convert_to_decimal(win_rate)
    win_trade_count = int(ideal_trade_count * win_rate) # need to convert to int for list slicing
    # print(win_trade_count)
    # 把前百分之多少的改为win
    rand[:win_trade_count] = 1

    # 把胜利的里面的百分之多少改为let trade run的
    let_trade_run_rate = convert_to_decimal(let_trade_run_rate)
    let_trade_run_win_trade_count = int(win_trade_count*let_trade_run_rate)
    rand[:let_trade_run_win_trade_count] = 2 # 因为rand的dtype=int是int其实让dtype=float

    # 把最后百分之多少的改为breakeven
    break_even_rate = convert_to_decimal(break_even_rate)
    break_even_trade_count = int(ideal_trade_count*break_even_rate)
    rand[-break_even_trade_count:] = -1

    # 随机摇匀
    numpy.random.shuffle(rand)

    return rand
    

def calculate_width_for_tabling_in_print_beautifully(trade_count, final_capital, theoretical_capital_in_risk, actual_capital_in_risk, actual_potential_profit, commission, spread_fee, total_fee):
    # calc the witdh for aligning number to the right
    
    trade_count_width = calculate_current_item_width(trade_count)
    final_capital_width = calculate_current_item_width(final_capital)
    theoretical_capital_in_risk_width = calculate_current_item_width(theoretical_capital_in_risk)
    actual_capital_in_risk_width = calculate_current_item_width(actual_capital_in_risk)
    actual_potential_profit_width = calculate_current_item_width(actual_potential_profit)
    commission_width = calculate_current_item_width(commission)
    spread_fee_width = calculate_current_item_width(spread_fee)
    total_fee_width = calculate_current_item_width(total_fee)
    
    return trade_count_width, final_capital_width, theoretical_capital_in_risk_width, actual_capital_in_risk_width, actual_potential_profit_width, commission_width, spread_fee_width, total_fee_width

def calculate_current_item_width(item):
    width_count = 0
    
    while True: 
        item = item/10
        width_count += 1
        
        if item < 1:
            break
     
    width = str(width_count)
    return width

# capital in risk is identical with theoretical_capital_in_risk
def print_beautifully(trade_count, current_initial, capital_in_risk, actual_capital_in_risk, actual_potential_profit, widths, lot_size, commission, spread_fee, total_fee, profit_change):
    
    # how to print it beautifully
    
    # print int
    # current_initial = int(current_initial)
    # initial = int(initial)
    # capital_in_risk = int(capital_in_risk)
    # actual_capital_in_risk = int(actual_capital_in_risk)
    # actual_potential_profit = int(actual_potential_profit)
    # commission = int(commission)
    # spread_fee = int(spread_fee)
    # total_fee = int(total_fee)
    

    trade_count_width = widths["trade_count_width"]
    # trade_count_width = 5
    final_capital_width = widths["final_capital_width"]
    # final_capital_width = 5
    theoretical_capital_in_risk_width = widths["theoretical_capital_in_risk_width"]
    # theoretical_capital_in_risk_width = 5
    actual_capital_in_risk_width = widths["actual_capital_in_risk_width"]
    # actual_capital_in_risk_width = 5
    actual_potential_profit_width = widths["actual_potential_profit_width"]
    # actual_potential_profit_width = 5
    commission_width = widths["commission_width"]
    spread_fee_width = widths["spread_fee_width"]
    total_fee_width = widths["total_fee_width"]
    
    
    # print(f"NO.{trade_count:>{width}}, pre: {current_initial:>{width}}, post: {initial:>{width}}, risk: {capital_in_risk:>{width}}, actual risk: {actual_capital_in_risk:>{width}}, actual profit: {actual_potential_profit:>{width}}, lot size: {lot_size:.2f}, commission: {commission:.2f}, spread fee: {spread_fee:.2f}, total fee: {total_fee:.2f}")
    
    # cut "post" to make it neater 只打印pre_current_trade的capital是多少
    # print(f"{trade_count:<{trade_count_width}}, capital: {current_initial:>{final_capital_width}.2f}, risk: {capital_in_risk:>{theoretical_capital_in_risk_width}.2f}, \
    # actual risk: {actual_capital_in_risk:>{actual_capital_in_risk_width}5.2f}, actual profit: {actual_potential_profit:>{actual_potential_profit_width}5.2f}, lot: {lot_size:>5.2f}, \
    # commission: {commission:>5.2f}, spread fee: {spread_fee:>5.2f}, total fee: {total_fee:>5.2f}, profit_change: {profit_change:>5.2f}")

    # print("{:<16} {:<16} {:<16} {:<16} {:<16} {:<16} {:<16} {:<16} ".format("Count", "Capital", "Actual Risk", "Actual Profit", "Lot", "Commission", "Spread", "Total Fee", "Profit Change"))

    # print(f"{trade_count:>{trade_count_width}} {current_initial:>{final_capital_width}.2f} {capital_in_risk:>{theoretical_capital_in_risk_width}.2f} \
    #  {actual_capital_in_risk:>{actual_capital_in_risk_width}.2f} {actual_potential_profit:>{actual_potential_profit_width}.2f} {lot_size:>4.2f} \
    #  {commission:>{commission_width}.2f} {spread_fee:>{spread_fee_width}.2f} {total_fee:>{total_fee_width}.2f} {profit_change:>4.2f}")

    print(f"{trade_count:<5} {current_initial:>5.2f} {capital_in_risk:>5.2f} \
    {actual_capital_in_risk:>5.2f} {actual_potential_profit:>5.2f} {lot_size:>5.2f} \
    {commission:>5.2f} {spread_fee:>5.2f} {total_fee:>5.2f} {profit_change:>5.2f}")



def print_total_info(win_trade_count, loss_trade_count, break_even_trade_count, let_trade_run_count, trade_count, initial, average_trades_per_day, is_limit_consecutive_wins, is_limit_consecutive_losses,
                     total_profits, total_losses):
    actual_win_rate = win_trade_count / trade_count
    actual_loss_rate = loss_trade_count / trade_count
    actual_break_even_rate = break_even_trade_count / trade_count
    actual_let_trade_run_rate = let_trade_run_count / trade_count
    profit_factor = abs(total_profits) / abs(total_losses)
    avg_win = abs(total_profits) / win_trade_count
    avg_loss = abs(total_losses) / loss_trade_count
    avg_risk_to_reward = avg_win / avg_loss
    expectancy = actual_win_rate * avg_win - actual_loss_rate * avg_loss

    # average_trades_per_day = int((8+15+9+7+5)/5)     # 从这几天统计 (4/18-4/22)
    
    days_to_complete = trade_count/average_trades_per_day
    # weeks_to_complete = days_to_complete/7
    weeks_to_complete = days_to_complete/5 # only five trading days a week
    months_to_complete = days_to_complete/20
    years_to_complete = months_to_complete/12

    print(f"win limit: {is_limit_consecutive_wins}")   
    print(f"loss limit: {is_limit_consecutive_losses}")

    print()
    print("total info:")
    print(f"final capital: {initial:.3f}")
    print(f"win trades: {win_trade_count}")
    print(f"loss trades: {loss_trade_count}")
    print(f"break even trades: {break_even_trade_count}")
    print(f"actual win rate: {actual_win_rate*100:.4f}%")
    print(f"actual loss rate: {actual_loss_rate*100:.4f}%")
    print(f"actual break even rate: {actual_break_even_rate*100:.4f}%")
    print(f"actual let trade run rate: {actual_let_trade_run_rate*100:.4f}%")
    # profit factor
    print(f"profit factor: {profit_factor}, total profits: {total_profits}, total losses: {total_losses}")
    print(f"expectancy: {expectancy}, avg_win: {avg_win}, avg_loss: {avg_loss}, avg_risk_to_reward: {avg_risk_to_reward}")
    print(f"time spent:\n \
    by day: {days_to_complete:.2f}\n \
    by week: {weeks_to_complete:.2f}\n \
    by month: {months_to_complete:.2f}\n \
    by year: {years_to_complete:.2f}\n \
    ")

    # total_info = {
    #     "actual_win_rate": actual_win_rate,
    #     # "average_trades_per_day": average_trades_per_day,
    #     "days_to_complete": days_to_complete,
    #     "weeks_to_complete": weeks_to_complete,
    #     "months_to_complete": months_to_complete,
    # }

    # return total_info

def limit_consecutive_wins(current_result, recent_six_trades_rand_values, limit_to=10):
    # 保留最近6次的rand的值，也就是win/loss的值，以便更加实际一些，假如10连胜了，那么下一次rand是1，则改为0
    # 这样似乎就破坏了随机抽取，但是在实际情况下，连胜应该会影响情绪，有可能会出问题
    # recent_six_trades_rand_values = [] # 不能放在这里
    
    # 每次获得值后，都查询一下之前的六个，如果六个全是1，那么把本次改为0
    if current_result == 1:    
        sum = 0
        for value in recent_six_trades_rand_values:
            sum += value
        if sum == limit_to:
            current_result = 0

    recent_six_trades_rand_values.append(current_result)
    
    if len(recent_six_trades_rand_values) > limit_to:
        recent_six_trades_rand_values.pop(0)
        
    #print(recent_six_trades_rand_values)   
    #print(len(recent_six_trades_rand_values))        
    return current_result

def limit_consecutive_losses(current_result, recent_trades_rand_values_for_limit_losses, limit_to=4):
    # 保留最近6次的rand的值，也就是win/loss的值，以便更加实际一些，假如六连胜了，那么下一次rand是1，则改为0
    # 这样似乎就破坏了随机抽取，但是在实际情况下，连胜应该会影响情绪，有可能会出问题
    # recent_six_trades_rand_values = [] # 不能放在这里
    
    # 每次获得值后，都查询一下之前的4个，如果4个全是0，那么把本次改为0
    if current_result == 0:    
        sum = 0
        for value in recent_trades_rand_values_for_limit_losses:
            sum += value
        if sum == 0:
            current_result = 1

    recent_trades_rand_values_for_limit_losses.append(current_result)
    
    if len(recent_trades_rand_values_for_limit_losses) > limit_to:
        recent_trades_rand_values_for_limit_losses.pop(0)
        
    #print(recent_six_trades_rand_values)   
    #print(len(recent_six_trades_rand_values))        
    return current_result


# def limit_consecutive_wins_and_losses(current_result, recent_six_trades_rand_values, recent_trades_rand_values_for_limit_losses, is_limit_consecutive_wins, is_limit_consecutive_losses, limit_consecutive_win_to=10, limit_consecutive_loss_to=4):
    # if is_limit_consecutive_wins:
        # if current_result == 1:    
            # sum = 0
            # for value in recent_six_trades_rand_values:
                # sum += value
            # if sum == limit_consecutive_win_to:
                # print(f"*****************************************************{limit_consecutive_win_to} consecutive wins**********************************************************")
                # current_result = 0

                # recent_six_trades_rand_values.append(current_result)
                # recent_trades_rand_values_for_limit_losses.append(current_result)
                
        # if current_result == 0:
            # recent_six_trades_rand_values.append(current_result)
            # recent_trades_rand_values_for_limit_losses.append(current_result)
                
    
    

    # if is_limit_consecutive_losses:
        # if current_result == 0:    
            # sum = 0
            # for value in recent_trades_rand_values_for_limit_losses:
                # sum += value

            # if len(recent_trades_rand_values_for_limit_losses) == limit_consecutive_loss_to:
                # if sum == 0:
                    # print(f"*****************************************************{limit_consecutive_loss_to} consecutive losses**********************************************************")
                    # current_result = 1

                # recent_six_trades_rand_values.append(current_result)
                # recent_trades_rand_values_for_limit_losses.append(current_result)
                
        # if current_result == 1:
            # recent_six_trades_rand_values.append(current_result)
            # recent_trades_rand_values_for_limit_losses.append(current_result)
    
    # if len(recent_six_trades_rand_values) > limit_consecutive_win_to:
       # # print("**************&^&^&^%&$^%$%#$^%&%$#$%^%&*(")
        # recent_six_trades_rand_values.pop(0)

    # if len(recent_trades_rand_values_for_limit_losses) > limit_consecutive_loss_to:
       # # print("*************FGHJKHGFGHJKHGFHJHGHJHJ*(")
        # recent_trades_rand_values_for_limit_losses.pop(0)

    # print("recent_six_trades_rand_values:")
    # print(recent_six_trades_rand_values)
    # print("recent_trades_rand_values_for_limit_losses:")
    # print(recent_trades_rand_values_for_limit_losses)

    # return current_result
    
def limit_consecutive_wins_and_losses(current_result, recent_six_trades_rand_values, recent_trades_rand_values_for_limit_losses, is_limit_consecutive_wins, is_limit_consecutive_losses, limit_consecutive_win_to, limit_consecutive_loss_to): #limit_consecutive_win_to, limit_consecutive_loss_to
    
    if is_limit_consecutive_wins == True and is_limit_consecutive_losses == True:
        # print("We are in #if is_limit_consecutive_wins == True and is_limit_consecutive_losses == True#")
        if current_result == 1: # 说明不是连输，无须处理连输
            #print("in #if current_result == 1:")
            sum = 0
            for value in recent_six_trades_rand_values:
                sum += value
            if sum == limit_consecutive_win_to: # 改成零之后添加
                #print(f"*****************************************************{limit_consecutive_win_to} consecutive wins**********************************************************")
                current_result = 0

                recent_six_trades_rand_values.append(current_result)
                recent_trades_rand_values_for_limit_losses.append(current_result)
                
            else: # 直接添加，一定要添加，不然由于一开始不可能等于limit_consecutive_win_to，所以里面会一直是空的
                recent_six_trades_rand_values.append(current_result)
                recent_trades_rand_values_for_limit_losses.append(current_result)
                
        elif current_result == 0:
            #print("in #elif current_result == 0:")
            sum = 0
            for value in recent_trades_rand_values_for_limit_losses:
                sum += value

            if sum == 0 and len(recent_trades_rand_values_for_limit_losses) == limit_consecutive_loss_to: # 有三个数了，还是0的话
                #print(f"*****************************************************{limit_consecutive_loss_to} consecutive losses**********************************************************")
                current_result = 1

                recent_six_trades_rand_values.append(current_result)
                recent_trades_rand_values_for_limit_losses.append(current_result)
                    
            else:
                recent_six_trades_rand_values.append(current_result)
                recent_trades_rand_values_for_limit_losses.append(current_result)
                    
 
    if is_limit_consecutive_wins == False and is_limit_consecutive_losses == True:
        #print("We are in if is_limit_consecutive_wins == False and is_limit_consecutive_losses == True:")
        if current_result == 1: #因为我们不处理连赢,所以直接统计到loss的那个列表
            recent_trades_rand_values_for_limit_losses.append(current_result) 
        elif current_result == 0:     
            sum = 0
            for value in recent_trades_rand_values_for_limit_losses:
                sum += value

            if sum == 0 and len(recent_trades_rand_values_for_limit_losses) == limit_consecutive_loss_to: # 有三个数了，还是0的话
                # print(f"*****************************************************{limit_consecutive_loss_to} consecutive losses**********************************************************")
                current_result = 1

                recent_trades_rand_values_for_limit_losses.append(current_result)
                
            else: # 如果不是三个数全是0，一定也要添加元素进去，否则list会一直是空。(比如[0], [0,0], [0,0,1])
                recent_trades_rand_values_for_limit_losses.append(current_result)
                
    
    if is_limit_consecutive_wins == True and is_limit_consecutive_losses == False:
        if current_result == 1: # 1的时候才需要处理
            #print("in #if current_result == 1:")
            sum = 0
            for value in recent_six_trades_rand_values:
                sum += value
            if sum == limit_consecutive_win_to: # 改成零之后添加
                # print(f"*****************************************************{limit_consecutive_win_to} consecutive wins**********************************************************")
                current_result = 0
                recent_six_trades_rand_values.append(current_result)
                
            else: # 如果不全是1，那么不改为0，直接添加1，一定要添加，不然由于一开始不可能等于limit_consecutive_win_to，所以里面会一直是空的
                recent_six_trades_rand_values.append(current_result)
                
                
        elif current_result == 0: #因为我们不处理连输,所以直接统计到连赢的那个列表
            recent_six_trades_rand_values.append(current_result)
    
    if is_limit_consecutive_wins == False and is_limit_consecutive_losses == False:
        # print(f"do not limit wins or losses, simply return current_result: {current_result}")
        return current_result
    
    # if is_limit_consecutive_losses:
        # if current_result == 0 and current_result_modified == False:    
            # sum = 0
            # for value in recent_trades_rand_values_for_limit_losses:
                # sum += value

            # if len(recent_trades_rand_values_for_limit_losses) == limit_consecutive_loss_to:
                # if sum == 0:
                    # print(f"*****************************************************{limit_consecutive_loss_to} consecutive losses**********************************************************")
                    # current_result = 1
                    # current_result_modified = True

                # recent_six_trades_rand_values.append(current_result)
                # recent_trades_rand_values_for_limit_losses.append(current_result)
                
        # if current_result == 1:
            # recent_six_trades_rand_values.append(current_result)
            # recent_trades_rand_values_for_limit_losses.append(current_result)
    
    #print(f"len of recent_six_trades_rand_values: {len(recent_six_trades_rand_values)}")
    #print(f"len of recent_trades_rand_values_for_limit_losses: {len(recent_trades_rand_values_for_limit_losses)}")
    
    if len(recent_six_trades_rand_values) > limit_consecutive_win_to:
        #print("**************pop 1st item from recent_six_trades_rand_values")
        recent_six_trades_rand_values.pop(0)
        #print(f"length of recent_six_trades_rand_values: {len(recent_six_trades_rand_values)}")

    if len(recent_trades_rand_values_for_limit_losses) > limit_consecutive_loss_to:
        #print("*************pop 1st item from len(recent_trades_rand_values_for_limit_losses)")
        recent_trades_rand_values_for_limit_losses.pop(0)
        #print(f"length of recent_trades_rand_values_for_limit_losses: {len(recent_trades_rand_values_for_limit_losses)}")

    # print("recent_six_trades_rand_values:")
    # print(recent_six_trades_rand_values)
    # print("recent_trades_rand_values_for_limit_losses:")
    # print(recent_trades_rand_values_for_limit_losses)

    return current_result    
 

def do_the_trades(initial, symbol, commision_per_lot, risk_per_trade_ratio, rand, target_capital, is_limit_consecutive_wins, is_limit_consecutive_losses, cut_loss_min_rate, cut_loss_max_rate, cut_profit_min_rate, cut_profit_max_rate, 
enable_actual_mode, stop_loss_min, stop_loss_max, spread_max, actual_capital_in_risk_rate, actual_potential_profit_rate, max_lot_limit, min_lot_limit, enable_hit_n_run, enable_let_trade_run, limit_consecutive_win_to, limit_consecutive_loss_to, bankruptcy_threshold):
    
    # print(f"win limit: {is_limit_consecutive_wins}")   
    # print(f"loss limit: {is_limit_consecutive_losses}")
        
    trade_count = 0
    win_trade_count = 0
    loss_trade_count = 0
    break_even_trade_count = 0
    let_trade_run_count = 0

    # calculate total profits and losses
    total_profits = 0
    total_losses = 0
    
    trades = []
    recent_six_trades_rand_values = []
    recent_trades_rand_values_for_limit_losses = []

    # constant should be outside of the loop
    # commision_per_lot = 4 

    # # this seems not to working now #
    # http = urllib3.PoolManager()
    # r = http.request('GET', 'https://www.mataf.net/en/forex/tools/pip-value')
    # soup = BeautifulSoup(r.data, features="html.parser")
    # pip_value = soup.find("th", text=symbol).find_next_sibling("td").text
    # # pip_value = Decimal(pip_value)
    # pip_value = float(pip_value)
    # print(f"{symbol} pip value {pip_value}")
    # #######################
    # instead, do this as a temporary workaround
    if symbol == "USDJPY":
        pip_value = 6.25 # 100000*0.01*1/160 (contract size * pip def * (JPY/USD)) 
    else:
        pip_value = 10

    # note:
    # pip_value is how much a pip is (usually in USD, could also be pound or eur) with one lot (or 100,000 volume)

    # pip_value = 10
    
    while initial < target_capital:

        current_initial = initial
        capital_in_risk = initial * risk_per_trade_ratio

        # # it's too early to calculate it here. we need to calculate risk and profit with the actual lot size
        # if enable_actual_mode == False:
        #     actual_capital_in_risk = capital_in_risk
        #     actual_potential_profit = capital_in_risk
        # else:
        #     actual_capital_in_risk = capital_in_risk * actual_capital_in_risk_rate # 如果情况不妙就手动止损，8/12=0.66
        #     actual_potential_profit = capital_in_risk * actual_potential_profit_rate # 假设手动止盈，在tp为12$的时候，在10手动tp, 10/12=0.83
        #     # 9.2/12.8 = 0.71
        
                

        # capital_in_risk = capital*risk_per_trade_ratio
        # lot_size = capital_in_risk/(stop_loss*10)
        
        # every trade, the stop_loss and spread are different
        stop_loss = random.randint(stop_loss_min, stop_loss_max)
        spread = random.randint(0, spread_max) # 10
        
        # lot_size = (risk_per_trade_ratio * initial) / (stop_loss * pip_value + commision_per_lot + spread)
        # lot_size = capital_in_risk / (stop_loss * pip_value + commision_per_lot + spread) # this only applies to EURUSD when pip value is 10, so 10/10 doesn't make a change
        
        # theo lot size is float
        theo_lot_size = capital_in_risk / ((stop_loss + 1) * pip_value + commision_per_lot + spread / 10 * pip_value) 
        # stop + 1 because we enter when 1 pip passing 2 ticks
        # and the tp is actually sl -1
        
        # get the consevative lot size
        lot_size = float(str(theo_lot_size).split(".")[0] + "." + str(theo_lot_size).split(".")[1][:2])
        # debugging
        # print(f"theo_lot_size: {theo_lot_size}")
        # print(f"actual_lot_size: {lot_size}")
        
        
        # if lot size is greater than max lot limit, then make it equal to max lot limit
        if lot_size > max_lot_limit:
            lot_size = max_lot_limit
        elif lot_size < min_lot_limit:
            # # 1. stop the program
            # print(f"calculated lot_size {lot_size} is less than min_lot_limit {min_lot_limit}")
            # break
            
            # 2. set lot_size to min_lot_limit
            print(f"calculated lot_size {lot_size} is less than min_lot_limit {min_lot_limit}. \nsetting it to {min_lot_limit}.")
            lot_size = min_lot_limit
        

        # if theo lot size is 0.1, then it is equal to the actual lot size.
        # but as we always get a result like theo_lot_size: 0.1157582240227035
        # and the actual lot size will be 0.11, so they will NEVER be equal
        # so there is no need to do the below if condition to compare the two
        # if theo_lot_size != lot_size:
        
        # recalculate capital in risk and potential profit
        # capital_in_risk = lot_size * ((stop_loss + 1) * pip_value + commision_per_lot + spread / 10 * pip_value) # stop + 1 because we enter when 1 pip passing 2 ticks
        
        # actual potential risk WITHOUT commission fee and spread fee
        capital_in_risk  = lot_size * (stop_loss + 1) * pip_value

        if enable_actual_mode == False:
            actual_capital_in_risk = capital_in_risk
            # this is the profit without fee
            actual_potential_profit = lot_size * stop_loss * pip_value
        else:

            # make it dynamic, say the actual risk is 50% to 80% of the planned risk
            random_rate = numpy.random.randint(cut_loss_min_rate, cut_loss_max_rate)
            random_rate = random_rate/100
            actual_capital_in_risk = capital_in_risk * random_rate
            actual_potential_profit = lot_size * stop_loss * pip_value * actual_potential_profit_rate # 假设手动止盈，在tp为12$的时候，在10手动tp, 10/12=0.83

            # actual_capital_in_risk = capital_in_risk * actual_capital_in_risk_rate # 如果情况不妙就手动止损，8/12=0.66
            # actual_potential_profit = lot_size * stop_loss * pip_value * actual_potential_profit_rate # 假设手动止盈，在tp为12$的时候，在10手动tp, 10/12=0.83
            

        # # recalculate capital in risk and 
        # # #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # if lot_size > max_lot_limit:
        #     lot_size = max_lot_limit
            
        #     # we need to !!!ACTUALLY RECALCULATE!!! the capital_in_risk
        #     capital_in_risk = lot_size * (stop_loss * pip_value + commision_per_lot + spread)
        #     if enable_actual_mode == False:
        #         actual_capital_in_risk = capital_in_risk
        #         actual_potential_profit = lot_size * ((stop_loss - 1) * pip_value)
        #     else:
        #         actual_capital_in_risk = capital_in_risk * actual_capital_in_risk_rate # 如果情况不妙就手动止损，8/12=0.66
        #         actual_potential_profit = lot_size * ((stop_loss - 1) * pip_value) * actual_potential_profit_rate # 假设手动止盈，在tp为12$的时候，在10手动tp, 10/12=0.83
        #         # 9.2/12.8 = 0.71
        # #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        #commission
        commission = lot_size * commision_per_lot

        # spread fee
        # spread_fee = spread / 10 * pip_value * lot_size #　spread / 10 * pip_value * lot_size #　因为eurusd的pip_value正好是10，所以相当于*10/10
        # it seems there isn't such spread fee ???
        spread_fee = 0
        
        #total fee
        total_fee = commission + spread_fee
        
        #######
        
        # 本次的胜负，从结果组里面随机抽取一个。
        current_result = random.choice(rand)
        
        
        # # 如果需要限制连赢，那么call func limit_consecutive_wins()
        # if is_limit_consecutive_wins == True and current_result == 1:
        #     current_result = limit_consecutive_wins(current_result, recent_six_trades_rand_values) 
        
        # if is_limit_consecutive_losses == True and current_result == 0:
        
        #if is_limit_consecutive_wins or is_limit_consecutive_losses:

        # !!!!!! this is a bug. if we enable hit and run mode, then current_result can be 2, but limit_consecutive_wins_and_losses() only presume current_result to be only 1 or 0
        current_result = limit_consecutive_wins_and_losses(current_result, recent_six_trades_rand_values, recent_trades_rand_values_for_limit_losses, is_limit_consecutive_wins, is_limit_consecutive_losses, limit_consecutive_win_to, limit_consecutive_loss_to)
        # !!!!!!!!!!!!!!!

        if enable_hit_n_run:
            if current_result == 1:
                profit_change = actual_potential_profit - total_fee
                # initial = initial + actual_potential_profit - total_fee
                initial = initial + profit_change
                win_trade_count += 1
                trade_count += 1
                total_profits += profit_change
            elif current_result == 0:

                # 每一次输的时候都是见机行事cut loss而不是等着被止损
                # 
                # cut_loss_min_rate = 30 # 注意这里是不带百分比的数字，下面要除以100
                # cut_loss_max_rate = 80 # 止损设置在理论止损的60%
                random_rate = numpy.random.randint(cut_loss_min_rate, cut_loss_max_rate)
                random_rate = random_rate/100
                actual_capital_in_risk = actual_capital_in_risk * random_rate

                profit_change = - actual_capital_in_risk - total_fee
                # initial = initial - actual_capital_in_risk - total_fee
                initial = initial + profit_change
                loss_trade_count += 1
                trade_count += 1
                total_losses += profit_change
            elif current_result == 2:
                # 小赚
                # random_rate：实际赚得的是70%的理论盈利的百分之多少
                # cut_profit_min_rate = 20 # 注意这里是不带百分比的数字，下面要除以100
                # cut_profit_max_rate = 66
                random_rate = numpy.random.randint(cut_profit_min_rate, cut_profit_max_rate)
                random_rate = random_rate/100
                actual_potential_profit = actual_potential_profit * random_rate

                profit_change = actual_potential_profit - total_fee
                # initial = initial + actual_potential_profit - total_fee
                initial = initial + profit_change
                win_trade_count += 1
                trade_count += 1
                total_profits += profit_change
        elif enable_let_trade_run:
            if current_result == 1:
                profit_change = actual_potential_profit - total_fee
                # initial = initial + actual_potential_profit - total_fee
                initial = initial + profit_change
                win_trade_count += 1
                trade_count += 1
                total_profits += profit_change
            elif current_result == 0:

                profit_change = - actual_capital_in_risk - total_fee
                # initial = initial - actual_capital_in_risk - total_fee
                initial = initial + profit_change
                loss_trade_count += 1
                trade_count += 1
                total_losses += profit_change

            elif current_result == 2:
                # let trade run
                # random_rate：实际赚得的是70%的理论盈利的百分之多少
                # cut_profit_min_rate = 20 # 注意这里是不带百分比的数字，下面要除以100
                # cut_profit_max_rate = 66
                random_rate = numpy.random.randint(cut_profit_min_rate, cut_profit_max_rate)
                random_rate = random_rate/100
                actual_potential_profit = actual_potential_profit * random_rate

                profit_change = actual_potential_profit - total_fee
                # initial = initial + actual_potential_profit - total_fee
                initial = initial + profit_change
                win_trade_count += 1
                let_trade_run_count += 1
                trade_count += 1
                total_profits += profit_change

            elif current_result == -1:
                # break even
                profit_change = - total_fee
                initial = initial + profit_change
                break_even_trade_count += 1
                trade_count += 1
                total_losses += profit_change
        
        # serious 1 vs 1 risk reward ratio, no hit and run trick
        else:
            if current_result == 1:
                profit_change = actual_potential_profit - total_fee
                # initial = initial + actual_potential_profit - total_fee
                initial = initial + profit_change
                win_trade_count += 1
                trade_count += 1
                total_profits += profit_change
            elif current_result == 0:

                # # 每一次输的时候都是见机行事cut loss而不是等着被止损
                # # 
                # # cut_loss_min_rate = 30 # 注意这里是不带百分比的数字，下面要除以100
                # # cut_loss_max_rate = 80 # 止损设置在理论止损的60%
                # random_rate = numpy.random.randint(cut_loss_min_rate, cut_loss_max_rate)
                # random_rate = random_rate/100
                # actual_capital_in_risk = actual_capital_in_risk * random_rate

                profit_change = - actual_capital_in_risk - total_fee
                # initial = initial - actual_capital_in_risk - total_fee
                initial = initial + profit_change
                loss_trade_count += 1
                trade_count += 1
                total_losses += profit_change

            elif current_result == -1:
                # break even
                profit_change = - total_fee
                initial = initial + profit_change
                break_even_trade_count += 1
                trade_count += 1
                total_losses += profit_change

        
        this_trade = {
            "trade_count": trade_count,
            "previous_capital": current_initial,
            "new_capital": initial,
            "theoretical_capital_in_risk": capital_in_risk,
            "actual_capital_in_risk": actual_capital_in_risk,
            "actual_potential_profit": actual_potential_profit,
            "lot_size": lot_size,
            "commission": commission,
            "spread_fee": spread_fee,
            "total_fee": total_fee,
            # add actual profit change
            "profit_change": profit_change,
        }
        
        trades.append(this_trade)
        
        if initial < bankruptcy_threshold:
            break
        
        # print("inside function do the trade")
        # print(trade_count) #这里是正确数目，局部和全局变量问题
        
        # should NOT be in the while loop, bacuse trades_info will be assgined again and again during each loop.
        # However, what we expect is we calcuate trades_info when the loop ends.

        # trades_info = {
        #     "trades": trades,
        #     "trade_count" : trade_count,
        #     "win_trade_count": win_trade_count,
        #     "loss_trade_count": loss_trade_count,
        #     "initial": initial
        # }
        # print(trades_info)

    trades_info = {
        "trades": trades,
        "trade_count" : trade_count,
        "win_trade_count": win_trade_count,
        "loss_trade_count": loss_trade_count,
        "break_even_trade_count": break_even_trade_count,
        "let_trade_run_count": let_trade_run_count,
        "initial": initial,
        "total_profits": total_profits,
        "total_losses": total_losses,
    }
    # print(trades_info)
        
    return trades_info


def tabulate_print_trades_data_in_table(trades):
    trade_data_list_for_tabulate = []
    table_title_list = ["Count", "Capital", "Theo Risk", "Final Risk", "Final Profit", "Lot", "Commission", "Spread", "Total Fee", "Profit Change"]
    trade_data_list_for_tabulate.append(table_title_list)

    for trade in trades:
        trade_count = trade["trade_count"]
        current_initial = trade["previous_capital"]
        # initial = trade["new_capital"]
        capital_in_risk = trade["theoretical_capital_in_risk"]
        actual_capital_in_risk = trade["actual_capital_in_risk"]
        actual_potential_profit = trade["actual_potential_profit"]
        lot_size = trade["lot_size"]
        commission = trade["commission"]
        spread_fee = trade["spread_fee"]
        total_fee = trade["total_fee"]
        profit_change = trade['profit_change']
        
        # print_beautifully(trade_count, current_initial, capital_in_risk, actual_capital_in_risk, actual_potential_profit, widths, lot_size, commission, spread_fee, total_fee, profit_change)

        current_trade_data_list = [trade_count, current_initial, capital_in_risk, actual_capital_in_risk, actual_potential_profit, lot_size, commission, spread_fee, total_fee, profit_change]
        trade_data_list_for_tabulate.append(current_trade_data_list)

    print(tabulate(trade_data_list_for_tabulate, headers='firstrow', tablefmt='github', numalign="right", floatfmt=".3f"))


def draw_plotly_chart(trades):
    plot_list = []
    for trade in trades:
        trade_count = trade["trade_count"]
        current_initial = trade["previous_capital"]
        initial = trade["new_capital"]
        # capital_in_risk = trade["theoretical_capital_in_risk"]
        # actual_capital_in_risk = trade["actual_capital_in_risk"]
        # actual_potential_profit = trade["actual_potential_profit"]
        # lot_size = trade["lot_size"]
        # commission = trade["commission"]
        # spread_fee = trade["spread_fee"]
        # total_fee = trade["total_fee"]
        # profit_change = trade['profit_change']
    
        plot_list.append(current_initial)

    plot_list.append(initial)
    x = range(0, trade_count+1)

    # print(x)
    # print(plot_list)

    fig = px.line( x = x ,
                y = plot_list,
                title = 'Trade-Capital')


    # below commmented is for printing win rate on the plotly page

    # actual_win_rate = total_info["actual_win_rate"]
    # # print(type(actual_win_rate)) # <class 'float'>
    # actual_win_rate = str(actual_win_rate).split(".")[0] + "." + str(actual_win_rate).split(".")[1][:4]
    # # print(type(actual_win_rate)) # <class 'str'>
    # actual_win_rate = actual_win_rate + " (" + actual_win_rate.split(".")[1][:2] + "." + actual_win_rate.split(".")[1][-2:] + "%)"

    # "days_to_complete": days_to_complete,
    # "weeks_to_complete": months_to_complete,
    # "months_to_complete": months_to_complete,

    # try fix not showing issue
    # fig_text = '<head><script src="https://cdn.plot.ly/plotly-latest.min.js"></script></head>'
    # fig_text = ""

    # fig_text += "actual_win_rate:" + actual_win_rate + "<br>"
    # fig_text += "days_to_complete: " + str(total_info["days_to_complete"]) + "<br>"
    # fig_text += "weeks_to_complete: " + str(total_info["weeks_to_complete"]) + "<br>"
    # fig_text += "months_to_complete: " + str(total_info["months_to_complete"]) + "<br>"


    # Step 1 - adjust margins to make room for the text
    # fig.update_layout(
    #     margin=dict(l=0, r=0, t=0, b=0),
    #     # paper_bgcolor="LightSteelBlue",
    # )

    # # Step 2 - add line
    # fig.add_shape(type='line',
    #                 # x0=LabelDateB,
    #                 y0=0,
    #                 # x1=LabelDateB,
    #                 y1=5,
    #                 line=dict(color='black', dash='dot'),
    #                 xref='x',
    #                 yref='paper'
    # )

    # add annotation
    # there's an issue.
    # it's not showing on firefox intactly
    # and the plotly page gets blank ocassionally
    # seems it has something to do with vscode. It's not happening with notepad++
    # can use devtool F12 in the broswer to see the error
    # something is not loaded properly
    # fig.add_annotation(dict(font=dict(color='black',size=12),
                                            # x=0.2,
                                            # y=1.2,
                                            # showarrow=False,
                                            # text=fig_text,
                                            # textangle=0,
                                            # xanchor='auto',
                                            # xref="paper",
                                            # yref="paper"))              

    fig.show()

# 149376$   # 4257 for legion
def main(initial=4_500, target_capital=8_500, risk_per_trade_ratio=0.01, win_rate=0.60, break_even_rate=0.08, hit_and_run_rate=0.9, let_trade_run_rate=0.04, symbol="XAUUSD", is_limit_consecutive_wins=0, 
is_limit_consecutive_losses=0, cut_loss_min_rate=40, cut_loss_max_rate=80, cut_profit_min_rate=200, cut_profit_max_rate=500, enable_actual_mode=True, stop_loss_min=45, 
stop_loss_max=150, spread_max=50, actual_capital_in_risk_rate=0.70, actual_potential_profit_rate=1, max_lot_limit=100, min_lot_limit=0.01, average_trades_per_day=3, enable_hit_n_run=0, enable_let_trade_run=1,
ideal_trade_count_for_generating_rand=100000, limit_consecutive_win_to=8, limit_consecutive_loss_to=6, bankruptcy_threshold=20, commision_per_lot=7): 
    """
    actual_mode -> sl is 60% of theo sl, tp is 75% of theo tp.  hit_n_run -> cut loss quick, take profit quick
    average_trades_per_day, if timeframe is m5, then around (16+21+15+21+20+20)/6 = 18.83 trades per day
    commision_per_lot is the total fee for opening and closing trade with one lot. so actually the commission is 2 for one single buy or sell action.

    now use cut_loss_min_rate, cut_loss_max_rate instead of actual_capital_in_risk_rate to make the actual risk dynamic from x% to y%
    now use cut_profit_max_rate, cut_profit_max_rate isntead of actual_potential_profit_rate to try to simulate "let the trade run"
    """
    
    # initial = 650

    # target_capital = 1500

    # risk_per_trade_ratio = 0.05

    if enable_hit_n_run:
        # generate rand with 0, 1, and 2 (2 is hit and run)
        rand = generate_rand_trading_results_with_hit_and_run_strategy(ideal_trade_count=ideal_trade_count_for_generating_rand, win_rate=win_rate, hit_and_run_rate=hit_and_run_rate)
    elif enable_let_trade_run:
        rand = generate_rand_trading_results_with_let_trades_run(ideal_trade_count=ideal_trade_count_for_generating_rand, win_rate=win_rate, break_even_rate=break_even_rate, let_trade_run_rate=let_trade_run_rate)
    else:
        # only generate rand with 0 and 1
        rand = generate_rand_trading_results(ideal_trade_count=ideal_trade_count_for_generating_rand, win_rate=win_rate, break_even_rate=break_even_rate)



    trades_info = do_the_trades(initial, symbol, commision_per_lot, risk_per_trade_ratio, rand, target_capital, is_limit_consecutive_wins, is_limit_consecutive_losses, cut_loss_min_rate, cut_loss_max_rate, cut_profit_min_rate, cut_profit_max_rate, enable_actual_mode, 
    stop_loss_min, stop_loss_max, spread_max, actual_capital_in_risk_rate, actual_potential_profit_rate, max_lot_limit, min_lot_limit, enable_hit_n_run, enable_let_trade_run, limit_consecutive_win_to, limit_consecutive_loss_to, bankruptcy_threshold)

    trades = trades_info["trades"]
    trade_count = trades_info["trade_count"]
    win_trade_count = trades_info["win_trade_count"]
    loss_trade_count = trades_info["loss_trade_count"]
    break_even_trade_count = trades_info["break_even_trade_count"]
    let_trade_run_count = trades_info["let_trade_run_count"]
    initial = trades_info["initial"]

    # add total profits and losses
    total_profits = trades_info["total_profits"]
    total_losses = trades_info["total_losses"]


    # this seems to calc the width for table printing
    # last_trade = trades[-1]

    # theoretical_capital_in_risk = last_trade["theoretical_capital_in_risk"]
    # actual_capital_in_risk = last_trade["actual_capital_in_risk"]
    # actual_potential_profit = last_trade["actual_potential_profit"]
    # commission = last_trade["commission"]
    # spread_fee = last_trade["spread_fee"]
    # total_fee = last_trade["total_fee"]

    # trade_count_width, final_capital_width, theoretical_capital_in_risk_width, actual_capital_in_risk_width, actual_potential_profit_width, commission_width, spread_fee_width, total_fee_width  = calculate_width_for_tabling_in_print_beautifully(trade_count, initial, 
    # theoretical_capital_in_risk, actual_capital_in_risk, actual_potential_profit, commission, spread_fee, total_fee)

    # widths = {
    #     "trade_count_width": trade_count_width,
    #     "final_capital_width": final_capital_width,
    #     "theoretical_capital_in_risk_width": theoretical_capital_in_risk_width,
    #     "actual_capital_in_risk_width": actual_capital_in_risk_width,
    #     "actual_potential_profit_width": actual_potential_profit_width,
    #     "commission_width": commission_width,
    #     "spread_fee_width": spread_fee_width,
    #     "total_fee_width": total_fee_width,
    # }

    # plot_list = []

    # # print("{:>16} {:>16} {:>16} {:>16} {:>16} {:>16} {:>16} {:>16} {:>16} {:>16}".format("Count", "Capital", "risk", "Actual Risk", "Actual Profit", "Lot", "Commission", "Spread", "Total Fee", "Profit Change"))

    # trade_data_list_for_tabulate = []
    # table_title_list = ["Count", "Capital", "Theo Risk", "Final Risk", "Final Profit", "Lot", "Commission", "Spread", "Total Fee", "Profit Change"]
    # trade_data_list_for_tabulate.append(table_title_list)

    # for trade in trades:
    #     trade_count = trade["trade_count"]
    #     current_initial = trade["previous_capital"]
    #     initial = trade["new_capital"]
    #     capital_in_risk = trade["theoretical_capital_in_risk"]
    #     actual_capital_in_risk = trade["actual_capital_in_risk"]
    #     actual_potential_profit = trade["actual_potential_profit"]
    #     lot_size = trade["lot_size"]
    #     commission = trade["commission"]
    #     spread_fee = trade["spread_fee"]
    #     total_fee = trade["total_fee"]
    #     profit_change = trade['profit_change']
        
    #     # print_beautifully(trade_count, current_initial, capital_in_risk, actual_capital_in_risk, actual_potential_profit, widths, lot_size, commission, spread_fee, total_fee, profit_change)

    #     current_trade_data_list = [trade_count, current_initial, capital_in_risk, actual_capital_in_risk, actual_potential_profit, lot_size, commission, spread_fee, total_fee, profit_change]
    #     trade_data_list_for_tabulate.append(current_trade_data_list)

    #     plot_list.append(current_initial)

    # print(tabulate(trade_data_list_for_tabulate, headers='firstrow', tablefmt='github', numalign="right", floatfmt=".3f"))
    tabulate_print_trades_data_in_table(trades)

    # total_info = print_total_info(win_trade_count, loss_trade_count, trade_count, initial)
    print_total_info(win_trade_count, loss_trade_count, break_even_trade_count, let_trade_run_count, trade_count, initial, average_trades_per_day, is_limit_consecutive_wins, is_limit_consecutive_losses,
                     total_profits, total_losses)

    
    draw_plotly_chart(trades)

    # print()
    # print(f"width of the final capital: {widths}")



    # plot_list.append(initial)
    # x = range(0, trade_count+1)

    # # print(x)
    # # print(plot_list)

    # fig = px.line( x = x ,
    #             y = plot_list,
    #             title = 'Trade-Capital')


    # # below commmented is for printing win rate on the plotly page

    # # actual_win_rate = total_info["actual_win_rate"]
    # # # print(type(actual_win_rate)) # <class 'float'>
    # # actual_win_rate = str(actual_win_rate).split(".")[0] + "." + str(actual_win_rate).split(".")[1][:4]
    # # # print(type(actual_win_rate)) # <class 'str'>
    # # actual_win_rate = actual_win_rate + " (" + actual_win_rate.split(".")[1][:2] + "." + actual_win_rate.split(".")[1][-2:] + "%)"

    # # "days_to_complete": days_to_complete,
    # # "weeks_to_complete": months_to_complete,
    # # "months_to_complete": months_to_complete,

    # # try fix not showing issue
    # # fig_text = '<head><script src="https://cdn.plot.ly/plotly-latest.min.js"></script></head>'
    # # fig_text = ""

    # # fig_text += "actual_win_rate:" + actual_win_rate + "<br>"
    # # fig_text += "days_to_complete: " + str(total_info["days_to_complete"]) + "<br>"
    # # fig_text += "weeks_to_complete: " + str(total_info["weeks_to_complete"]) + "<br>"
    # # fig_text += "months_to_complete: " + str(total_info["months_to_complete"]) + "<br>"


    # # Step 1 - adjust margins to make room for the text
    # # fig.update_layout(
    # #     margin=dict(l=0, r=0, t=0, b=0),
    # #     # paper_bgcolor="LightSteelBlue",
    # # )

    # # # Step 2 - add line
    # # fig.add_shape(type='line',
    # #                 # x0=LabelDateB,
    # #                 y0=0,
    # #                 # x1=LabelDateB,
    # #                 y1=5,
    # #                 line=dict(color='black', dash='dot'),
    # #                 xref='x',
    # #                 yref='paper'
    # # )

    # # add annotation
    # # there's an issue.
    # # it's not showing on firefox intactly
    # # and the plotly page gets blank ocassionally
    # # seems it has something to do with vscode. It's not happening with notepad++
    # # can use devtool F12 in the broswer to see the error
    # # something is not loaded properly
    # # fig.add_annotation(dict(font=dict(color='black',size=12),
    #                                         # x=0.2,
    #                                         # y=1.2,
    #                                         # showarrow=False,
    #                                         # text=fig_text,
    #                                         # textangle=0,
    #                                         # xanchor='auto',
    #                                         # xref="paper",
    #                                         # yref="paper"))              

    # fig.show()


if __name__ == "__main__":
    main()

# end of file test