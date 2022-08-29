capital = 200
current_time = 0
# by month
# time_given = 1.5 * 12 # unit: months. 3 years, or 36 months
# by day
time_given = 30 # 1 * 365 # 1 year

daily_return = 0.1 # 10%
monthly_return = 0.6 # 60%
risk_per_trade = 0.05 # 5%

#1000 + 1000 * 0.1 

# def calc_compound(capital):
#     if capital < 10000:
#         print(f"capital: {capital}")
#         return calc_compound(capital * (1 + month_return))

def calc_compound_by_time(capital, current_time):
    if current_time > time_given:
        return capital
    else:
        print(f"day {current_time}  capital: {round(capital, 3)}")
        return calc_compound_by_time(capital * (1 + daily_return), current_time + 1)


def calc_compound_by_goal(capital, goal):
    if capital >= goal:
        print(f"goal achieved: {capital}")
        return capital
    else:
        print(f"capital: {capital}")
        return calc_compound_by_goal(capital * (1 + risk_per_trade), goal)

calc_compound_by_time(capital, current_time)

# how to achieve 60% if we risk 5% per trade
# calc_compound_by_goal(1600, 2560)