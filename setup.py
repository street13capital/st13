from setuptools import setup

with open('README.md') as f:
    long_description = f.read()

setup(
    name='st13',
    version='0.5.5',
    py_modules=['st13'],
    install_requires=['pandas',
                      'yfinance',
                      'matplotlib',
                      'matplotlib-inline',
                      'mplfinance'],
    author='Ken Soh',
    license='MIT License',
    url='https://github.com/street13capital/st13',
    description='Python package for trend analysis using technical analysis of price behaviour around trend lines',
    long_description=long_description,
    long_description_content_type='text/markdown; charset=UTF-8',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Financial and Insurance Industry',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Topic :: Office/Business :: Financial :: Investment',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    keywords=['finance', 'candlestick', 'ohlc', 'investing', 'technical analysis']
)
