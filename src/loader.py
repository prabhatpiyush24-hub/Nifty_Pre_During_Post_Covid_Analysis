import pandas as pd

from pathlib import Path


def load_price_file(file_path: Path):

    df = pd.read_csv(file_path)

    df["Date"] = pd.to_datetime(
        df["Date"],
        format="mixed",
        dayfirst=True
    )

    df = df.sort_values("Date")

    df.reset_index(drop=True, inplace=True)

    return df