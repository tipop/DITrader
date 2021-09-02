import ccxt
import datetime as dt
import time
import pandas as pd
import pprint
import datetime

class Lib:
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

    def get_1min_close(symbol, count):
        ohlc = Lib.api.fetch_ohlcv(
                symbol = symbol,
                timeframe = '1m',
                since = None,   # 1분봉은 최대 24시간 전만 가능하므로 since는 무의미
                limit = count)  # 1500개가 한계다

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
        df = Lib.get_1min_close(symbol, 20)
        close_1min_20_list = df['close'].to_list()
        close_1min_20_list[-1] = curPrice # 현재가로 교체하여 보정
        return Lib.get_moving_average(close_1min_20_list)

    def getLowestDIPastDay(symbol):  # 지난 몇 시간동안 최대 이격도를 구한다. (1분봉 20이평에서 하락 이격도)
        lowestDI = 0
        from20m = 0
        to20m = 20

        df = Lib.get_1min_close(symbol, 60 * 24)    # 1분봉은 최대 24시간만 가능함.

        while to20m < len(df.index):
            df20 = df.iloc[from20m:to20m]
            ma20 = sum(df20['close']) / len(df20['close'])
            low = df20.iloc[-1,2]   # 20번째 봉의 low 값
            di = (low - ma20) / ma20
            
            if lowestDI > di:
                lowestDI = di
            
            from20m += 1
            to20m += 1
        
        # print("lowest DI:", lowestDI * 100, "%")
        return lowestDI

        

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

#    print("\t[매도] 체결수량: ", order['filled'], "미체결수량: ", order['remaining'], "주문가: ", order['price'])