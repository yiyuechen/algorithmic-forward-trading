import requests
import pandas as pd
from datetime import datetime, timedelta, timezone

def get_news_df():
    # 1) Fetch the calendar JSON
    url = 'https://nfs.faireconomy.media/ff_calendar_thisweek.json'
    resp = requests.get(url)
    resp.raise_for_status()                # blow up if we get a bad status
    events = resp.json()                  # list of dicts

    # 2) Turn into a DataFrame
    df = pd.json_normalize(events)

    # 3) Rename for clarity
    df = df.rename(columns={
        'date':       'raw_date',
        'title':      'event',
        'impact':     'importance'
    })

    # 4) Parse the ISO8601 timestamp into a timezone‐aware datetime
    #    pandas automatically reads the "-04:00" offset.
    df['datetime'] = pd.to_datetime(df['raw_date'])

    # 5) (Optional) Convert to UTC or your local zone, e.g. Dublin:
    df['dt_utc']        = df['datetime'].dt.tz_convert('UTC')
    df['dt_dublin']     = df['datetime'].dt.tz_convert('Europe/Dublin')

    # 6) Pick just the columns you need
    df = df[[
        'datetime',    # original, tz-aware
        'dt_utc',      # in UTC
        'dt_dublin',   # in Europe/Dublin
        'event',
        'country',
        'importance',
        'forecast',
        'previous'
    ]]

    # print(df)
    return df

def trades_blocker_to_avoid_news(minutes, df):
    # do not do the current time. might introduce bugs when moving around regions # now = datetime.now()
    now = datetime.now(timezone.utc) # get utc time now
    # now = get_debug_datetime()
    # Filter upcoming high-impact events in the next X minutes
    window_before = timedelta(minutes=minutes)
    window_after  = timedelta(minutes=minutes)
    start_block   = now - window_before
    end_block     = now + window_after

    # print(start_block)
    # print(end_block)

    blockers = df[
        (df["dt_utc"]   >= start_block) &
        (df["dt_utc"]   <= end_block)  &
        (df["importance"].isin(["High"])) & # (df["importance"].isin(["High", "Medium"]))
        (df["country"].isin(["USD", "JPY"]))
    ]

    if not blockers.empty: # if blockers is not empty # if there is news nearby
        # print(f"start_block_UTC_time: {start_block}")
        # print(f"curent_UTC_time: {now}")
        # print(f"end_block_UTC_time: {end_block}")
        # print(f"High-impact news — avoid trading!")
        # print(blockers[["dt_utc", "dt_dublin", "event", "country", "importance", "forecast", "previous"]])
        # so we have the now utc time, and we check 60minutes (or 1min) before and after this utc now time, so we have a start_block and end_block.
        # we want to see during this time window, if we have any news. if so, blockers has something, NOT empty.
        # so at this NOW moment, if we know, ok, we have news at this window, but should we wait until 60min after the time the news happens, or we wait unitl the end_block?
        return True
    else:
        # do not print, no info is good info
        # print("No major news right now.") 
        return False


def get_debug_datetime():
    # say you want 2025-05-15 at 13:30:45 UTC
    # debug_dt = datetime(
    #     year=2025,
    #     month=5,
    #     day=15,
    #     hour=13,
    #     minute=30,
    #     second=45,
    #     tzinfo=timezone.utc
    # )
    debug_dt = datetime(
        year=2025,
        month=5,
        day=8,
        hour=15,
        minute=0,
        second=45,
        tzinfo=timezone.utc
    )
    print("debugging datetime...")
    return debug_dt


def main():
    df = get_news_df()

    # print complete
    print(df)

    # print only high impact and USD JPY related
    print(df[
        (df["importance"].isin(["High"])) &
        (df["country"].isin(["USD", "JPY"]))
    ])

    blocker_result = trades_blocker_to_avoid_news(60, df)
    print(f"blocker_result: {blocker_result}")

if __name__ == "__main__":
    main()
