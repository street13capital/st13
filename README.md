# st13 📉📈
Python package for trend analysis using technical analysis of price behaviour around trend lines.

***IMPORTANT - This project has been deprecated***

It is still in Pre-Alpha, the framework for downloading data, plotting log chart with trendlines is done. Originally, the next steps would be improving trendlines detection and plotting, before coding in price behaviour analysis.

However, I realise that identifying the best trendline has more nuances than what I could code in mathematically using formulas. I would think that having this package would give misleading analysis and cause more harm than benefit. Thus I've shelved this project.

To install the latest version of st13 Python package

```python
pip3 install st13 --upgrade
```

To see a sample plot of an asset with trendlines, run it with the following, where SYMBOL is the asset symbol on Yahoo Finance. If not provided, AAPL will be used for demonstration.

```python
python3 -m st13 SYMBOL
```

![png](https://raw.githubusercontent.com/street13capital/st13/refs/heads/main/sample.png)
