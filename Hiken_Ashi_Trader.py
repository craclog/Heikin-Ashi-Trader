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
from postman import Postman
from pprint import pprint, pformat


def get_arguments() :
    parser = argparse.ArgumentParser()
    parser.add_argument('--ticker', dest='ticker', default='AAPL',
                        help='Target ticker to trace.')
    parser.add_argument('-v', '--verbose', dest='verbose', action='count',
                        help='Make the operation more talkative')
    args = parser.parse_args()
    args.ticker = args.ticker.upper()

    if args.verbose :
        logging.basicConfig(level=logging.DEBUG, format='%(message)s')
    else :
        logging.basicConfig(level=logging.INFO, format='%(message)s')

    logging.debug(f"Ticker = {args.ticker}")
    return args

# Read config.yml for IEX API token
def read_config(config_file) :
    with open(config_file) as f :
        config = yaml.load(f)
    return config

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
            last_ha_open    = chart_json[i-1]['haOpen']
            last_ha_close   = chart_json[i-1]['haClose']

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

def is_time_to_buy(day) :
    block_len = day.haClose - day.haOpen
    upper_tail_len = day.haHigh - day.haClose
    # When power of buying trend is strong, it's time to buy.
    if day.haLow == day.haOpen and block_len / 2 <= upper_tail_len:
        return True
    else :
        return False

def is_time_to_sell(day) :
    # When selling trend is getting start, it's time to sell.
    if day.haHigh == day.haClose :
        return True
    else :
        return False

if __name__ == "__main__" :

    # TODO : argparse for saving data from IEX & saved data path

    args = get_arguments()
    ticker = args.ticker

    cfg = read_config("config.yml")

    # Get chart data using IEX REST API
    try :
        url = f'https://sandbox.iexapis.com/stable/stock/{ticker}/chart/1m?token={cfg["PUBLISHABLE_TOKEN"]}'
        req_chart = requests.get(url)
        data_json = req_chart.json()
    except :
        logging.error(f"Request Failed. {url}")
        exit(1)

    data_json = add_hiken_ashi_data(data_json)
    df = pd.DataFrame(data_json)
    df.set_index("date", inplace=True)
    logging.debug(df)

    # Create Hiken-Ashi chart
    fig = go.Figure(data=[go.Candlestick(
                        x=df.index,
                        open=df['haOpen'],
                        high=df['haHigh'],
                        low=df['haLow'],
                        close=df['haClose'])])

    postman = Postman(sender_email=cfg["SENDER_EMAIL"],
                        sender_pwd=cfg["SENDER_PWD"],
                        receiver_email=cfg["RECEIVER_EMAIL"])
    fig.show()

    if is_time_to_buy(df.iloc[-1]) :
        postman.send(f"BUY {ticker}", "")

    elif is_time_to_sell(df.iloc[-1]) :
        postman.send(f"SELL {ticker}", "")