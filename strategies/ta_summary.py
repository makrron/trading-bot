from tradingview_ta import TA_Handler, Interval, Exchange
from lnm_client import lnm_client
from time import time, sleep
import logging
import json
import csv
import pandas as pd
import os

class TAS():

  # Connection to LNMarkets API
  def __init__(self, options):
        self.options = options
        self.lnm = lnm_client(self.options)

  # Get trading signal from trading view https://www.tradingview.com/symbols/XBTUSD/technicals/
  def get_ta(symbol, screener, exchange, interval):
    interval_list = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d', '1W', '1M']
    ta_interval_list = [Interval.INTERVAL_1_MINUTE,
                        Interval.INTERVAL_5_MINUTES,
                        Interval.INTERVAL_15_MINUTES,
                        Interval.INTERVAL_30_MINUTES,
                        Interval.INTERVAL_1_HOUR,
                        Interval.INTERVAL_2_HOURS,
                        Interval.INTERVAL_4_HOURS,
                        Interval.INTERVAL_1_DAY,
                        Interval.INTERVAL_1_WEEK,
                        Interval.INTERVAL_1_MONTH]
    
    ta_interval = ta_interval_list[interval_list.index(interval)]

    return TA_Handler(
    symbol=symbol,
    screener=screener,
    exchange=exchange,
    interval=ta_interval,
    ).get_analysis().summary

  # Output can be a graph showing the evolution of your Balance during the strategy
  def ta_summary(self, quantity, leverage, takeprofit, stoploss, interval, timeout): 
    symbol='XBTUSD.P'
    screener='CRYPTO'
    exchange='BITMEX'
    
    interval_list = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d', '1W', '1M']
    t_interval_list = [60, 300, 900, 1800, 3600, 7200, 14400, 86400, 604800, 2592000]
    t_interval = t_interval_list[interval_list.index(interval)]

    timeout = time() + 60*timeout

    pid_list = []

    analysis = TAS.get_ta(symbol, screener, exchange, interval)
    print(analysis)
    if (analysis['RECOMMENDATION'] == 'STRONG_BUY'):
      side = 'long'
      offer = json.loads(self.lnm.get_bid_offer())['offer']
      tp = round(offer * (1 + takeprofit))
      sl = round(offer * (1 - stoploss))
      pid = json.loads(self.lnm.market_long(quantity = quantity, leverage = leverage, takeprofit = tp, stoploss = sl))['position']['pid']
      pid_list.append(pid)
    elif (analysis['RECOMMENDATION'] == 'STRONG_SELL'):
      side = 'short'
      bid = json.loads(self.lnm.get_bid_offer())['bid']
      tp = round(bid * (1 - takeprofit))
      sl = round(bid * (1 + stoploss))
      pid = json.loads(self.lnm.market_short(quantity = quantity, leverage = leverage, takeprofit = tp, stoploss = sl))['position']['pid']
      pid_list.append(pid)
    else:
      side = 'neutral'
      pid = ''
      
    sleep(t_interval)

    while True:
      analysis = TAS.get_ta(symbol, screener, exchange, interval)
      print(analysis)

      num_pos_running = len(json.loads(self.lnm.get_positions(type_pos='running')))
      pid_running = [json.loads(self.lnm.get_positions(type_pos='running'))[i]['pid'] for i in range(num_pos_running)]

      if (pid in pid_running):
        if side == 'long':
          if ('BUY' in analysis['RECOMMENDATION']):
            logging.info('Keep long open')
          elif (analysis['RECOMMENDATION'] == 'STRONG_SELL'):
            self.lnm.close_position(pid)
            side = 'short'
            bid = json.loads(self.lnm.get_bid_offer())['bid']
            tp = round(bid * (1 - takeprofit))
            sl = round(bid * (1 + stoploss))
            pid = json.loads(self.lnm.market_short(quantity = quantity, leverage = leverage, takeprofit = tp, stoploss = sl))['position']['pid']
            pid_list.append(pid)        
          else:
            self.lnm.close_position(pid)
            side = 'neutral'
        elif side == 'short':
          if ('SELL' in analysis['RECOMMENDATION']):
            logging.info('Keep short open')
          elif (analysis['RECOMMENDATION'] == 'STRONG_BUY'):
            self.lnm.close_position(pid)
            side = 'long'
            offer = json.loads(self.lnm.get_bid_offer())['offer']
            tp = round(offer * (1 + takeprofit))
            sl = round(offer * (1 - stoploss))
            pid = json.loads(self.lnm.market_long(quantity = quantity, leverage = leverage, takeprofit = tp, stoploss = sl))['position']['pid']
            pid_list.append(pid)    
          else:
            self.lnm.close_position(pid)
            side = 'neutral'     
        elif side == 'neutral':
          if (analysis['RECOMMENDATION'] == 'STRONG_BUY'):
            side = 'long'
            offer = json.loads(self.lnm.get_bid_offer())['offer']
            tp = round(offer * (1 + takeprofit))
            sl = round(offer * (1 - stoploss))
            pid = json.loads(self.lnm.market_long(quantity = quantity, leverage = leverage, takeprofit = tp, stoploss = sl))['position']['pid']
            pid_list.append(pid)
          elif (analysis['RECOMMENDATION'] == 'STRONG_SELL'):
            side = 'short'
            bid = json.loads(self.lnm.get_bid_offer())['bid']
            tp = round(bid * (1 - takeprofit))
            sl = round(bid * (1 + stoploss))
            pid = json.loads(self.lnm.market_short(quantity = quantity, leverage = leverage,  takeprofit = tp, stoploss = sl))['position']['pid']
            pid_list.append(pid)
          else:
            side = 'neutral'
            logging.info('Stay neutral')
          
      else:
        if (analysis['RECOMMENDATION'] == 'STRONG_BUY'):
          side = 'long'
          offer = json.loads(self.lnm.get_bid_offer())['offer']
          tp = round(offer * (1 + takeprofit))
          sl = round(offer * (1 - stoploss))
          pid = json.loads(self.lnm.market_long(quantity = quantity, leverage = leverage, takeprofit = tp, stoploss = sl))['position']['pid']
          pid_list.append(pid)
        elif (analysis['RECOMMENDATION'] == 'STRONG_SELL'):
          side = 'short'
          bid = json.loads(self.lnm.get_bid_offer())['bid']
          tp = round(bid * (1 - takeprofit))
          sl = round(bid * (1 + stoploss))
          pid = json.loads(self.lnm.market_short(quantity = quantity, leverage = leverage, takeprofit = tp, stoploss = sl))['position']['pid']
          pid_list.append(pid)
        else:
          side = 'neutral'
          pid = ''     
        
      if time() > timeout:
        break
      
      sleep(t_interval)

    self.lnm.close_position(pid)
    pid_list.append(pid)

    closed_positions = json.loads(self.lnm.get_positions(type_pos='closed'))
    df_closed_positions = pd.DataFrame.from_dict(closed_positions)

    df_closed_pos = df_closed_positions[df_closed_positions['pid'].isin(pid_list)].copy()

    pl = df_closed_pos['pl'].sum()

    logging.info('Total PL (sats) = ' + str(pl))

    path = os.path.join(os.path.dirname(__file__), "df_closed_pos.csv")
    df_closed_pos.to_csv(path)
    logging.info('df_closed_pos.csv saved in strategies folder')
