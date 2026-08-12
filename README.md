# st13 v0.9.6 🐉
To install latest version of st13 Python package for trend analysis

```python
pip3 install st13 --upgrade
```

To analyse a financial asset run it with the following, where SYMBOL is the asset symbol on [Yahoo Finance](https://finance.yahoo.com). If SYMBOL is not given, MSFT will be used for demo, since Microsoft owns GitHub where this code lives.

```python
python3 -m st13 SYMBOL
```

The package works by identifying clusters of weekly closing prices that are statistically significant. The rationale is if price has moved above a key level, the bias is bullish and if price has moved below a key level, the bias is bearish. Because the market is moving away from a key price level. Naturally, there can be whipsaws around key levels.

More on how this project came about and commentary on MSFT sample chart at this [LinkedIn post](https://www.linkedin.com/posts/kensoh_ive-just-published-the-beta-version-of-st13-share-7491391742349369344-guBe/). Further examples at this [LinkedIn newsletter](https://www.linkedin.com/pulse/technical-analysis-62-st13-python-packages-take-btcusd-ken-soh-sysyc) where I applied st13 package to out-of-sample financial assets not used during its development, namely BTCUSD, KC1!, USDJPY, BYND, KOSPI. Its views look reasonable to me.
 
![png](https://raw.githubusercontent.com/street13capital/st13/refs/heads/main/sample.png)

# API Mode 🤖
You can invoke st13 from your Python code and use the outputs accordingly

```python
>>> from st13 import get_trend

>>> get_trend() # if not provided, the default symbol is MSFT
('BULLISH', np.float64(506.05999755859375), np.float64(491.8847961425781), [np.float64(491.8847961425781), np.float64(408.3346252441406), np.float64(368.8730163574219), np.float64(319.2364196777344), np.float64(286.98883056640625), np.float64(241.458740234375), np.float64(218.7037811279297), np.float64(198.009033203125)])

>>> trend_bias, latest_price, key_line, lines_list = get_trend('AAPL')
>>> trend_bias
'BEARISH'
>>> latest_price
np.float64(308.260009765625)
>>> key_line
np.float64(308.6438293457031)
>>> lines_list
[np.float64(308.6438293457031), np.float64(264.1086730957031), np.float64(217.7839813232422), np.float64(187.8817138671875), np.float64(168.6041717529297), np.float64(145.42784118652344), np.float64(121.35916900634766), np.float64(105.50035095214844)]
```

See this [LinkedIn post](https://www.linkedin.com/posts/kensoh_super-excited-to-share-an-update-on-st13-activity-7493235230267305984-xRK1) for examples of how you could build trading strategies to backtest on top of st13 package.
