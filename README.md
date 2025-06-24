# st13 📉📈
Python package for trend analysis using technical analysis of price behaviour around trend lines.

This is still in Pre-Alpha, the framework for downloading data, plotting log chart, with horizontal trendlines is done.

Next up is coding in the turning points detection on sloping trendlines and plot the lines on the asset log chart.

To install the latest version of st13 Python package

```python
pip3 install st13 --upgrade
```

To see a sample plot of an asset with horizontal trendlines, run it with the following, where SYMBOL is the asset symbol on Yahoo Finance. If not provided, AAPL will be used for demonstration.

```python
python3 -m st13 SYMBOL
```

![png](https://raw.githubusercontent.com/street13capital/st13/refs/heads/main/sample.png)
