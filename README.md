# st13 📉📈
To install latest version of st13 Python package for trend analysis

```python
pip3 install st13 --upgrade
```

To analyse a financial asset run it with the following, where SYMBOL is the asset symbol on [Yahoo Finance](https://finance.yahoo.com). If SYMBOL is not given, MSFT will be used for demonstration, since Microsoft owns GitHub where this code lives.

```python
python3 -m st13 SYMBOL
```

The package works by identifying clusters of weekly closing prices that are statistically significant. The rationale is if price has moved above a key level, the bias is bullish and if price has moved below a key level, the bias is bearish. Because the market is moving away from a key price level. Naturally, there can be whipsaws around key levels.
 
![png](https://raw.githubusercontent.com/street13capital/st13/refs/heads/main/sample.png)
