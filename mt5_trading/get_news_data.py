import investpy
import pandas as pd
from datetime import datetime, timedelta, timezone

def normalize_time(t):
    if t == "All Day":
        return "00:00:00"             # treat all-day as midnight
    parts = t.split(":")
    if len(parts) == 2:
        return t + ":00"              # append seconds if you only have HH:MM
    return t                          # already has HH:MM:SS

def get_news_df():
    # # 1. Define the window: now → next 24 hours
    now_utc = datetime.now(timezone.utc)
    from_date = now_utc.strftime("%d/%m/%Y")
    to_date   = (now_utc + timedelta(days=7)).strftime("%d/%m/%Y")
    print(f"now_utc: {now_utc}")
    print(f"from_date: {from_date}")
    print(f"to_date: {to_date}")

    # 2. Fetch calendar for your country (e.g. 'united kingdom') and only HIGH impact
    df = investpy.economic_calendar(importances=["high"],
                                    from_date=from_date,
                                    to_date=to_date,
                                    # time_zone="GMT +8:00",
                                    # time_zone="GMT +1:00",
                                    # time_zone="GMT",
                                    )

    # print(df)

    if df.empty:
        print("The dataframe is empty")
        exit()

    # 3) drop any rows where importance isn't “high”
    #    (this will get rid of all those None/holiday entries)
    df = df[df["importance"].str.lower() == "high"]

    print("drop events whose importance isn't high")
    # print(df)

    # # 3. Parse the datetime of each event


    # 1. Create a cleaned-up time column
    df["time_clean"] = df["time"].apply(normalize_time)

    # 2. Parse into a datetime
    df["event_date_plus_time"] = pd.to_datetime(
        df["date"] + " " + df["time_clean"],
        format="%d/%m/%Y %H:%M:%S",
        dayfirst=True,
        # utc=True,
    )

    # print(df)
    return df


def trades_blocker_to_avoid_news(minutes, df):
    now = datetime.now()
    # 4. Filter upcoming high-impact events in the next X minutes
    window_before = timedelta(minutes=minutes)
    window_after  = timedelta(minutes=minutes)
    start_block   = now - window_before
    end_block     = now + window_after

    print(start_block)
    print(end_block)

    blockers = df[(df["event_date_plus_time"] >= start_block) & (df["event_date_plus_time"] <= end_block)]

    if not blockers.empty: # if blockers is not empty # if there is news nearby
        print("🚫 High-impact news — avoid trading!")
        print(blockers[["event_date_plus_time","event","currency","actual","forecast","previous"]])
        return True
    else:
        print("✅ No major news right now.")
        return False

    

def main():
    df = get_news_df()
    print(df)

if __name__ == "__main__":
    main()