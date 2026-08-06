# st13 📉📈
To install latest version of st13 Python package for trend analysis

```python
pip3 install st13 --upgrade
```

To analyse a financial asset run it with the following, where SYMBOL is the asset symbol on [Yahoo Finance](https://finance.yahoo.com). If SYMBOL is not provided, MSFT will be used for demonstration, since Microsoft owns GitHub. The package works by identifying weekly closing prices that are statistically significant. If price has moved above a key level, the bias is bullish and if price has moved below a key level, the bias is bearish. Of course, there can be whipsaws around key levels. This package is just an experimental free open-source tool, not meant for making trading decisions base on its outputs.

```python
python3 -m st13 SYMBOL
```

![png](https://raw.githubusercontent.com/street13capital/st13/refs/heads/main/sample.png)
