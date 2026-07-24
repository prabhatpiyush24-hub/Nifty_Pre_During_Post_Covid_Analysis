import pandas as pd

regimes = pd.DataFrame({

    "Regime":[

        "Pre-COVID",

        "COVID Crash",

        "Recovery",

        "Post-COVID"

    ],

    "Start":[

        "2015-01-01",

        "2020-02-20",

        "2020-04-01",

        "2022-01-01"

    ],

    "End":[

        "2020-02-19",

        "2020-03-31",

        "2021-12-31",

        "2025-12-31"

    ]

})

regimes.to_csv(

"data/metadata/market_regimes.csv",

index=False

)

print(regimes)