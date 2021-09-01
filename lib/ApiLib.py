import ccxt
import datetime as dt
import time
import pandas as pd
import pprint

#api = ccxt.binance()

#    print("\t[매도] 체결수량: ", order['filled'], "미체결수량: ", order['remaining'], "주문가: ", order['price'])

class Lib:
    api = None

    def init(apiKeyFilePath):
        # binance 객체 생성
        with open(apiKeyFilePath, "r") as f:
            lines = f.readlines()
            api_key = lines[0].strip()
            secret = lines[1].strip()

        Lib.api = ccxt.binance(config={
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True,        # 시장가로 주문이 제출되는 것을 방지하기 위한 'Post-only' 설정값
            'options': { 
                'defaultType': 'future',    # 선물 마켓으로 객체 생성
                # 'api-expires': 60         # 제출한 주문 유효기간 (초). 60초 (자동 취소 안되네?)
            }
        })

    # 현재가 가져오기
    def getCurrentPrice(symbol):
        return Lib.api.fetch_ticker(symbol)['last']

    def getFreeBalance():
        return Lib.api.fetch_balance()['USDT']['free']

    def getQuantity(price, marginRatio):
        return (Lib.getFreeBalance() * marginRatio) / price

    def hasServerPosition():
        balance = Lib.api.fetch_balance()
    
        if balance['used']['USDT'] > 0:
            return True

        return False
    
    # 부분이라도 체결되었는가
    def hasClosed(order):
        return (order['status'] == 'closed') or ((order['status'] == 'open') and (order['filled'] > 0))

    def isOrderOpenStatus(order, symbol):
        return (order != None) and ('open' == Lib.api.fetch_order(order['id'], symbol)['status'])

    # 비트코인 선물 현재가 1초 마다 출력
    def print_current_price_sec(symbol):
        while True:
            btc = Lib.api.fetch_ticker(symbol) 
            now = dt.datetime.now()
            print(now, "\t", btc['last']) # 현재가 ex) 48800.00
            time.sleep(1)   # 1초

    def get_1min_close_20(symbol):
        ohlc = Lib.api.fetch_ohlcv(
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
    def get_moving_average(close_prices):
        return sum(close_prices) / len(close_prices)

    def get20Ma(symbol, curPrice):
        df = Lib.get_1min_close_20(symbol)
        close_1min_20_list = df['close'].to_list()
        close_1min_20_list[-1] = curPrice # 현재가로 교체하여 보정
        return Lib.get_moving_average(close_1min_20_list)


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