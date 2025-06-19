from setuptools import setup

setup(
    name='st13',
    version='0.5.0',
    py_modules=['st13'],
    install_requires=['yfinance>=0.2.63',
                      'matplotlib>=3.10.3',
                      'matplotlib-inline>=0.1.7',
                      'mplfinance>=0.12.10b0'],
    author='Ken Soh',
    license='MIT License',
    url='https://github.com/street13capital/st13',
    description='Python package for trend analysis',
    long_description='Python package for trend analysis using technical analysis of price behaviour around trend lines',
    long_description_content_type='text/markdown',
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
    ]
)
