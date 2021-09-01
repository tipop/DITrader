import ccxt
import datetime as dt
import time
import pandas as pd
import pprint

#    print("\t[매도] 체결수량: ", order['filled'], "미체결수량: ", order['remaining'], "주문가: ", order['price'])

class Lib:
    def __init__(self, apiKeyFilePath):
        # binance 객체 생성
        with open(apiKeyFilePath, "r") as f:
            lines = f.readlines()
            api_key = lines[0].strip()
            secret = lines[1].strip()

        self.api = ccxt.binance(config={
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True,        # 시장가로 주문이 제출되는 것을 방지하기 위한 'Post-only' 설정값
            'options': { 
                'defaultType': 'future',    # 선물 마켓으로 객체 생성
                # 'api-expires': 60         # 제출한 주문 유효기간 (초). 60초 (자동 취소 안되네?)
            }
        })

    def getBinanceApi(self):
        return self.api

    # 현재가 가져오기
    def getCurrentPrice(self, symbol):
        return self.api.fetch_ticker(symbol)['last']

    def getFreeBalance(self):
        return self.api.fetch_balance()['USDT']['free']

    def getQuantity(self, price, marginRatio):
        return (self.getFreeBalance() * marginRatio) / price

    def hasServerPosition(self):
        balance = self.api.fetch_balance()
    
        if balance['used']['USDT'] > 0:
            return True

        return False
    
    # 부분이라도 체결되었는가
    def hasClosed(self, order):
        return (order['status'] == 'closed') or ((order['status'] == 'open') and (order['filled'] > 0))

    def isOrderOpenStatus(self, order):
        return (order != None) and ('open' == self.api.fetch_order(order['id'], self.symbol)['status'])

    # 비트코인 선물 현재가 1초 마다 출력
    def print_current_price_sec(self, symbol):
        while True:
            btc = self.api.fetch_ticker(symbol) 
            now = dt.datetime.now()
            print(now, "\t", btc['last']) # 현재가 ex) 48800.00
            time.sleep(1)   # 1초

    def get_1min_close_20(self, symbol):
        ohlc = self.api.fetch_ohlcv(
                symbol = symbol,
                timeframe = '1m',
                since = None,
                limit = 20)

        # pprint.pprint(ohlc)
            
        df = pd.DataFrame(
            data=ohlc,
            columns=['datetime', 'open', 'high', 'low', 'close', 'volume']
        )

        df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
        df.set_index('datetime', inplace=True)
        #pprint.pprint(df)
        #last = df.iloc[-1]
        #print(last['close'])
        return df

    # 1분봉 20 이평 가격
    def get_moving_average(self, close_prices):
        return sum(close_prices) / len(close_prices)

    def get20Ma(self, symbol, curPrice):
        df = self.get_1min_close_20(symbol)
        close_1min_20_list = df['close'].to_list()
        close_1min_20_list[-1] = curPrice # 현재가로 교체하여 보정
        return self.get_moving_average(close_1min_20_list)


    ####### 트레이링 스탑 동작 함###############
        #rate = '0.5'
        #price = None
        #params = {
        #    'stopPrice': order['price']-1,
        #    'callbackRate': rate
        #}

        #order = self.api.create_order(
        #    self.symbol, 
        #    'TRAILING_STOP_MARKET', 
        #    'sell',
        #    1, 
        #    price, 
        #    params)
        #################################