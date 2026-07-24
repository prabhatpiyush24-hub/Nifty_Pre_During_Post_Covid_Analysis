import numpy as np
import pandas as pd


def calculate_simple_return(df, price_column="Adj Close"):
    """
    Calculate simple daily returns.
    """

    df = df.copy()

    df["Return"] = df[price_column].pct_change()

    return df


def calculate_log_return(df, price_column="Adj Close"):
    """
    Calculate log returns.
    """

    df = df.copy()

    df["Log Return"] = np.log(
        df[price_column] / df[price_column].shift(1)
    )

    return df


def calculate_cumulative_return(df):
    """
    Calculate cumulative returns from simple returns.
    """

    df = df.copy()

    df["Cumulative Return"] = (
        1 + df["Return"]
    ).cumprod() - 1

    return df


def calculate_drawdown(df, price_column="Adj Close"):
    """
    Calculate drawdown.
    """

    df = df.copy()

    running_max = df[price_column].cummax()

    df["Drawdown"] = (
        df[price_column] - running_max
    ) / running_max

    return df


def calculate_rolling_volatility(
    df,
    window=21
):
    """
    Annualized rolling volatility.
    """

    df = df.copy()

    df["Rolling Volatility"] = (
        df["Return"]
        .rolling(window)
        .std()
        * np.sqrt(252)
    )

    return df