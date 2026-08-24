import random

from numpy import choose


# def calc_compound(capital):
#     if capital < 10000:
#         print(f"capital: {capital}")
#         return calc_compound(capital * (1 + month_return))

def calc_compound_by_time(capital, current_time, time_given, daily_return, result_list):
    if current_time > time_given:
        return result_list
    else:
        print(f"day {current_time}  capital: {round(capital, 3)}")

        current_data = {
            "day": current_time,
            "capital": capital, 
        }
        result_list.append(current_data)

        # uncomment to choose everytime
        # daily_return = choose_every_time(daily_return=daily_return)

        return calc_compound_by_time(capital * (1 + daily_return), current_time + 1, time_given, daily_return, result_list)

def choose_every_time(daily_return):
    win_or_lose = None
    while win_or_lose not in ["1", "2", ""]:
        # prompt to choose win or lose each time
        win_or_lose = input("win or lose? choose [1]/2 ")
        if win_or_lose == "" or win_or_lose == "1":
            daily_return = abs(daily_return)
        elif win_or_lose == "2":
            daily_return = -abs(daily_return)
        else:
            print("invaid input. choose 1 or 2")
    return daily_return

def calc_compound_by_goal(capital, goal):
    if capital >= goal:
        print(f"goal achieved: {capital}")
        return capital
    else:
        print(f"capital: {capital}")
        # if randint less than 0, it's a losing trade
        profit_per_trade = random.randint(0, 3) / 100 # each trade, the reward could be 1%-5%, generate a random one
        return calc_compound_by_goal(capital * (1 + profit_per_trade), goal)



def main():
    capital = 130
    current_time = 0
    # by month
    # time_given = 1.5 * 12 # unit: months. 3 years, or 36 months
    # by day
    time_given = 20*6 # 4 * 20 # this can be seen as trade count. unit day or trade # 1 * 365 # 1 year

    daily_return = 0.05 # 10% 
    monthly_return = 0.6 # 60%
    profit_per_trade = 0.01 # 5%
    
    result_list = []

    #1000 + 1000 * 0.1 
    result_list = calc_compound_by_time(capital, current_time, time_given, daily_return, result_list)
    for current in result_list:
        print(f"goal {current['day']:<5}  capital: {round(current['capital'], 3):<5}")


    enable_plotly = 0
    
    if enable_plotly:

        import plotly.express as px
        x, y = [current['day'] for current in result_list], [current['capital'] for current in result_list]

        fig = px.line(
            x = x,
            y = y,
            title = 'Trade-Capital'
                
        )

        fig.show()


    # goal = 229

    # print("****************************************")

    # for i in range(0, len(result_list) - 1):
    #     print(f"day {result_list[i+1]['day']} action plan:")
    #     calc_compound_by_goal(capital=result_list[i]['capital'], goal=result_list[i+1]['capital'])
    #     print("")

    # how to achieve 60% if we risk 5% per trade
    # calc_compound_by_goal(1600, 2560, risk_per_trade)


if __name__ == "__main__":
    main()


"""
if 5%, it means only profitable 5% risk trade will do the job. if 10%, then two 5% trades will do the job, two 5% is actually more than one 10%. see below:

>>> 50000*(1+0.01)**10      ten 1%
55231.10627056022
>>> 50000*(1+0.05)**2       two 5%
55125.0
>>> 50000*(1+0.1)           one 10%
55000.00000000001
>>>
"""