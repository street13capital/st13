# st13 📉📈
Python package for trend analysis using technical analysis of price behaviour around trend lines.

This is still in Pre-Alpha, the framework for downloading data, plotting log chart with trendlines is done.

Next up is improving the trendlines detection and plotting, before coding in price behaviour analysis.

To install the latest version of st13 Python package

```python
pip3 install st13 --upgrade
```

To see a sample plot of an asset with trendlines, run it with the following, where SYMBOL is the asset symbol on Yahoo Finance. If not provided, AAPL will be used for demonstration.

```python
python3 -m st13 SYMBOL
```

![png](https://raw.githubusercontent.com/street13capital/st13/refs/heads/main/sample.png)
