import yfinance as yf

tickers = [
    "IOC.NS",
    "IOB.NS",
    "IRCTC.NS",
    "IRFC.NS"
]

for ticker in tickers:

    print("=" * 60)
    print(ticker)

    stock = yf.Ticker(ticker)

    try:

        info = stock.info

        print("Long Name :", info.get("longName"))
        print("Exchange  :", info.get("exchange"))
        print("Sector    :", info.get("sector"))

    except Exception as e:

        print("INFO ERROR :", e)

    try:

        hist = stock.history(period="max")

        print("Rows :", len(hist))

        if not hist.empty:
            print(hist.head())

    except Exception as e:

        print("HISTORY ERROR :", e)

    print()