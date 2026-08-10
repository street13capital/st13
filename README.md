# st13 v0.9.5 🐉
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

>>> get_trend() # if not provided, default symbol is MSFT
('BULLISH', np.float64(491.8847961425781), [np.float64(491.8847961425781), np.float64(408.3346252441406), np.float64(368.87298583984375), np.float64(319.2364196777344), np.float64(286.9888916015625), np.float64(241.4587860107422), np.float64(218.7037811279297), np.float64(198.00904846191406)])

>>> trend_bias, key_line, lines_list = get_trend('AAPL')
>>> trend_bias
'BEARISH'
>>> key_line
np.float64(308.9100036621094)
>>> lines_list
[np.float64(308.9100036621094), np.float64(264.3364562988281), np.float64(217.9718017578125), np.float64(188.0437774658203), np.float64(168.74957275390625), np.float64(145.55325317382812), np.float64(121.46382141113281), np.float64(105.59131622314453)]
```
