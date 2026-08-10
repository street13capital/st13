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
