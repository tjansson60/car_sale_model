# What does the market think my car is worth?

Original work can be found in the `skoda_fabia`. The `peugeot_5008` is a incomplete example for a friend with a limited
number of cars.

## Requirements

Beside all the usual stuff as scikit-learn, pandas, seaborn etc. there are some extra dependencies. Selenium is needed
to scrape the danish car sales website, where I intended to sell my car.

```
$ pip install selenium
```

Download the firefox headleass driver from:
- https://github.com/mozilla/geckodriver/releases/download/v0.23.0/geckodriver-v0.23.0-linux64.tar.gz

```
$ tar -xvzf  geckodriver-v0.23.0-linux64.tar.gz
$ chmod +x geckodriver
$ mv geckodriver ~/bin/
```
