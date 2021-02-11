"""
Hiken-Ashi Trader

Hiken-Ashi Trader gets stock data using IEX API, so you need to get
API token from https://iexcloud.io/, and you should put them in
config.yml
"""

import requests
import json, yaml
import datetime
import logging
import argparse
import plotly.graph_objects as go
import pandas as pd
from pprint import pprint, pformat


logging.basicConfig(level=logging.DEBUG)

def get_arguments() :
    parser = argparse.ArgumentParser()
    parser.add_argument('--ticker', dest='ticker', default='AAPL',
                        help='Target ticker to trace.')
    args = parser.parse_args()
    args.ticker = args.ticker.upper()
    logging.debug(f"Ticker = {args.ticker}")
    return args


# Read config.yml for IEX API token
def read_config(config_file) :
    with open(config_file) as f :
        config = yaml.load(f)
    secret_token        = config['SECRET_TOKEN']
    publishable_token   = config['PUBLISHABLE_TOKEN']
    return secret_token, publishable_token

# Add Hiken-Ashi data column
def add_hiken_ashi_data(chart_json) :
    for i in range(len(chart_json)) :

        # First Hiken-Ashi data is same as normal candle data.
        if i == 0 :
            chart_json[i]['haOpen']  = chart_json[i]['fOpen']
            chart_json[i]['haClose'] = chart_json[i]['fClose']
            chart_json[i]['haHigh']  = chart_json[i]['fHigh']
            chart_json[i]['haLow']   = chart_json[i]['fLow']

        else :
            last_ha_open = chart_json[i-1]['haOpen']
            last_ha_close = chart_json[i-1]['haClose']

            cur_open    = chart_json[i]['fOpen']
            cur_close   = chart_json[i]['fClose']
            cur_high    = chart_json[i]['fHigh']
            cur_low     = chart_json[i]['fLow']

            chart_json[i]['haOpen']  = (last_ha_open + last_ha_close) / 2.0
            chart_json[i]['haClose'] = (cur_open + cur_close + cur_high + cur_low ) / 4.0
            chart_json[i]['haHigh']  = max(cur_high, last_ha_open, last_ha_close)
            chart_json[i]['haLow']   = min(cur_low, last_ha_open, last_ha_close)

    logging.debug(pformat(chart_json))
    return chart_json


if __name__ == "__main__" :

    # TODO : argparse for saving data from IEX & saved data path
    # TODO : argparse for verbose logging

    args = get_arguments()
    ticker = args.ticker

    secret_token, publishable_token = read_config("config.yml")

    # Get chart data using IEX REST API
    try :
        url = f'https://sandbox.iexapis.com/stable/stock/{ticker}/chart/1m?token={publishable_token}'
        req_chart = requests.get(url)
        data_json = req_chart.json()
    except :
        logging.error(f"Request Failed. {url}")
        exit(1)

    data_json = add_hiken_ashi_data(data_json)
    df = pd.DataFrame(data_json)
    logging.debug(df)

    # Create Hiken-Ashi chart
    fig = go.Figure(data=[go.Candlestick(
                        x=df['date'],
                        open=df['haOpen'],
                        high=df['haHigh'],
                        low=df['haLow'],
                        close=df['haClose'])])
    fig.show()

    # TODO : Mail to user when the time to sell/buy comes.