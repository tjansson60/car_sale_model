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
- https://github.com/mozilla/geckodriver/releases
- https://github.com/mozilla/geckodriver/releases/download/v0.31.0/geckodriver-v0.31.0-linux64.tar.gz

```
$ tar -xvzf  geckodriver-v0.23.0-linux64.tar.gz
$ chmod +x geckodriver
$ mv geckodriver ~/bin/
```

## Issues
If you get the error `Your Firefox profile cannot be loaded. It may be missing or inaccessible.` you need to uninstall
firefox installed through snap (default on modern Ubuntu) and install through apt:

```
sudo snap remove firefox
sudo add-apt-repository ppa:mozillateam/ppa
```
To ensure that PPA/deb/apt version of Firefox is preferred edit `/etc/apt/preferences.d/mozilla-firefox` to contain
```
Package: *
Pin: release o=LP-PPA-mozillateam
Pin-Priority: 1001
```

To ensure future Firefox upgrades to be installed automatically edit `/etc/apt/apt.conf.d/51unattended-upgrades-firefox`
to contain:
```
Unattended-Upgrade::Allowed-Origins:: "LP-PPA-mozillateam:${distro_codename}";
```

Finally install firefox:
```
sudo apt install firefox
```


