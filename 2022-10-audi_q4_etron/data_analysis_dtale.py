#!/usr/bin/env python

import pandas as pd
import dtale

if __name__ == '__main__':
    df = pd.read_parquet('2022-Oct-10-dataframe.parquet')
    d = dtale.show(df, subprocess=False)
    d.open_browser()