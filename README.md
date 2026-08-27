# Algorithmic Forward Trading

A Python-based algorithmic trading and quantitative research project
integrating MetaTrader 5 for forward-trading automation, risk
management, market-data processing, and statistical analysis.

## Overview

This project was developed as an ongoing personal project combining
Python software development with quantitative research.

The main trading system connects to MetaTrader 5 and supports
automated forward trading, position sizing, risk management,
market/news data processing, and trade execution.

The repository also contains probabilistic and statistical simulations
used to investigate possible trading outcomes and risk.

## Core Trading Engine
### Features

- Double-tick breakout detection
- SMA-based trend filtering across multiple timeframes
- Retracement and pause detection
- Dow high/low detection for stop-loss placement
- Risk-based lot-size calculation
- Spread and commission estimation
- Take-profit and stop-loss management
- Break-even stop-loss modification
- News-based trading protection
- Daily loss and consecutive-loss limits
- Optional hedge-position support
- ADX trend-strength filters

### How It Works

The engine:

1. Connects to a MetaTrader 5 terminal.
2. Logs into the selected trading account.
3. Retrieves OHLC data for the selected symbol and timeframe.
4. Checks breakout, SMA, retracement, pause, news, and risk conditions.
5. Calculates the position size from the account balance and stop-loss distance.
6. Opens and monitors trades through the MetaTrader 5 Python API.

### Requirements

- Python 3
- MetaTrader 5 desktop terminal
- A MetaTrader 5 trading account
- Python packages listed in `requirements.txt`

Install dependencies:

```bash
pip install MetaTrader5 numpy pandas tqdm requests
```

### Configuration
Create a local credential_info.py file containing your account credentials.
Configure the symbol, timeframe, risk percentage, stop-loss limits, take-profit
settings, and trading filters in main().

### Running
Start MetaTrader 5 first, login to your account, toggle algorithmic trading on, then run:
```bash
python trading_engine.py
```
The program will prompt for the account, terminal path, symbol, and strategy
settings.

### Risk Warning
This software can place live trades and may cause financial loss. Test it on
historical data and a demo account for statistics learning and avoid using it with real funds. It does not guarantee any profitability or uninterrupted operation.

### Status
The trading_engine.py program is experimental and under active development. Strategy rules, position sizing, broker compatibility, and market-data handling may require
further testing.

## Project Structure

### `mt5_trading/`

Contains the main MetaTrader 5 trading and automation components.

- `trading_engine.py` — core trading engine
- `get_news_data.py` — market/news data retrieval
- `calc_lot_and_execute.py` — position sizing and order-execution utility

### `simulations/`

Contains statistical and probabilistic simulations related to trading.

## Technologies

- Python
- MetaTrader 5
- NumPy
- pandas
- Matplotlib

## Trading System

The trading component is designed for forward trading through
MetaTrader 5 rather than historical backtesting through the MT5
platform.

## Notes

Copy mt5_trading/credential_info.example.py to
mt5_trading/credential_info.py and fill in your own credentials.

This project is intended primarily as a software engineering and
quantitative research project.

## Disclaimer

This project is provided for educational, research, and software-engineering
purposes only. It is not financial, investment, or trading advice.

The main trading engine and other MetaTrader 5 components are designed for
forward-trading automation and execution. The simulation programs generate
hypothetical trading outcomes based on specified assumptions and
probabilities. Simulated results are hypothetical and do not represent
actual investment performance.

Past simulated or live trading performance is not indicative of future
results. This software is not intended for use with real funds. Trading financial
instruments involves substantial risk, and the software may contain errors
or behave unexpectedly.

No guarantee is made regarding the accuracy, reliability, profitability, or
future performance of the strategies, trading system, or simulations
included in this repository.