# Research Methodology

## Universe and benchmark

The research universe contains the 311 companies marked `Eligible=True` in `data/metadata/company_master.csv`. NIFTY 50 adjusted-close daily returns are the market benchmark. The study period is 1 January 2015 to 31 December 2025.

## Return construction and quality controls

1. Raw company and benchmark files must contain valid dates, positive OHLC/adjusted-close values, non-negative volume, no duplicate dates, and internally consistent OHLC ranges.
2. Company prices are inner-aligned to the NIFTY 50 calendar before returns are calculated.
3. Simple return is `Adjusted Close_t / Adjusted Close_(t-1) - 1`.
4. Log return is `ln(Adjusted Close_t / Adjusted Close_(t-1))`.
5. Excess return is company simple return minus NIFTY 50 simple return.
6. A return is admitted to analytics only when it follows the preceding benchmark session exactly once. Missing company observations are never imputed.
7. The pipeline verifies each computed return, log return, and excess return against its formula. The persisted analytical table contains only valid returns.

## COVID regimes

| Regime | Window | Treatment |
| --- | --- | --- |
| Pre-COVID | 2015-01-01 to 2020-02-28 | Baseline comparison period |
| COVID Shock | 2020-03-01 to 2020-03-31 | Isolated market shock month |
| Post-COVID | 2020-04-01 to 2025-12-31 | Recovery and subsequent period |

March 2020 is displayed separately and is excluded from the pre/post correlation and performance comparison.

## Metrics

Company and equal-weight industry portfolios report total return, CAGR, annualized volatility, downside deviation, Sharpe ratio, Sortino ratio, maximum drawdown, one-day historical 95% VaR/CVaR, beta to NIFTY 50, annualized alpha, tracking error, information ratio, active win rate, and market correlation. Annualization uses 252 trading days. Sharpe, Sortino, and alpha use a 0% annual risk-free rate unless changed in the Portfolio Lab.

Industry returns are equal-weight averages of constituent company returns. Correlation matrices use pairwise Pearson correlations of adjusted-close daily returns. The six quantitative clusters are reproducible K-means groups built from full-sample CAGR, volatility, Sharpe ratio, maximum drawdown, beta, and market correlation.

## Portfolio lab

The Portfolio Lab supplies long-only equal-weight, minimum-variance, and maximum-Sharpe historical portfolios. It uses synchronized daily observations for selected companies and enforces the user-selected maximum individual weight. It is research functionality, not an investment recommendation.
