import pandas as pd


PRICE_COLUMNS = [
    "Open",
    "High",
    "Low",
    "Close",
    "Adj Close",
]


def missing_values(df):

    return int(df.isna().sum().sum())


def duplicate_dates(df):

    return int(df["Date"].duplicated().sum())


def negative_prices(df):

    return int((df[PRICE_COLUMNS] < 0).sum().sum())


def negative_volume(df):

    return int((df["Volume"] < 0).sum())


def date_sorted(df):

    return bool(df["Date"].is_monotonic_increasing)


def ohlc_errors(df):

    errors = (
        (df["Low"] > df["Open"])
        | (df["Low"] > df["Close"])
        | (df["Low"] > df["High"])
        | (df["High"] < df["Open"])
        | (df["High"] < df["Close"])
    )

    return int(errors.sum())


def volume_statistics(df):

    return {
        "Minimum": int(df["Volume"].min()),
        "Median": int(df["Volume"].median()),
        "Maximum": int(df["Volume"].max()),
        "Average": int(df["Volume"].mean())
    }