from lib.ApiLib import *
from Position import *
import time
from loguru import logger
from OrderInfo import *
from TelegramBot import *

WAIT_SECONDS_FOR_BUY = 30

class CatchBot:
    def __init__(self, symbols, option):
        self.symbols = symbols
        self.option = option

    def stop(self):
        pass

    def start(self):
        while True:
            try:
                order = self.waitForCatch() # 타겟 이격도 이상 급락하면 매수해서 리턴된다.

                position = Position(order, self.option)
                    
                pnl = position.waitForPositionClosed()  # 포지션이 종료되면 리턴된다. (익절이든 본절/손절이든)
                logger.info("{:10} | 캐치 포지션 종료. PNL: {:10.5f}%", order['symbol'], pnl)
                TelegramBot.sendMsg("{:10} | 캐치 포지션 종료. PNL: {:10.5f}%".format(order['symbol'], pnl))
            
            except Exception as ex:
                logger.error("{:10} | CatchBot 종료. Exception: {}", order['symbol'], repr(ex))
                TelegramBot.sendMsg("{:10} | CatchBot 종료. Exception: {}".format(order['symbol'], repr(ex)))
                break

    def waitForBuyClosed(self, order, waitSeconds):
        if Lib.hasClosed(order):
            return order

        for sec in range(waitSeconds):
            o = Lib.api.fetch_order(order['id'], order['symbol'])

            if Lib.hasClosed(o):
                break
            
            time.sleep(1)

        return o

    def orderBuyLimit(self, symbol, price):
        quantity = Lib.getQuantity(price, self.option.marginRatio)
        return Lib.api.create_limit_buy_order(symbol, quantity, price)
    
    def getFilledPrice(self, order):
        usdtSize = 0
        entryPrice = order['price']

        for i in range(3):
            try:
                positions = Lib.api.fetch_positions(order['symbol'])
                break
            except:
                time.sleep(1)
                continue
        
        if len(positions) > 0 and positions[0]['entryPrice'] != None:
             entryPrice = positions[0]['entryPrice']
             usdtSize = positions[0]['entryPrice'] * positions[0]['contracts']
        
        logger.info("{:10} | 캐치 매수 체결됨: {:10.5f} / {}USDT", order['symbol'], entryPrice, usdtSize)
        TelegramBot.sendMsg("{:10} | 캐치 매수 체결됨: {:10.5f} / {}USDT".format(order['symbol'], entryPrice, usdtSize))
        return entryPrice

    def getLowestDI(self):
        lowest = dict()
        lowest['DI'] = 100
        lowest['symbol'] = None
        lowest['targetPrice'] = 0 

        for symbol in self.symbols:
            curPrice =  Lib.api.fetch_ticker(symbol)['last']
            ma20 = Lib.get20Ma(symbol, curPrice)
            di = ((curPrice - ma20) / curPrice)

            #if di <= self.option.targetDI:
            #    TelegramBot.sendMsg("{} 이격도 만족 {:10.1}".format(symbol, di))

            if di < lowest['DI']:
                lowest['DI'] = di
                lowest['symbol'] = symbol
                lowest['targetPrice'] = ma20 * (1 - self.option.targetDI)
            
            #time.sleep(0.01)

        return lowest

    def waitForCatch(self):
        countOfFailure = 0
        order = None

        while True:
            try:
                if dt.datetime.now().second != 59:
                    time.sleep(0.5)
                    continue
                
                lowest = self.getLowestDI()

                if lowest['DI'] <= self.option.targetDI:
                    order = self.orderBuyLimit(lowest['symbol'], lowest['targetPrice'])
                    logger.info("{:10} | 캐치 매수 주문: {:10.5f}, DI: {:10.1f}", lowest['symbol'], lowest['targetPrice'], lowest['DI'] * 100)
                    order = self.waitForBuyClosed(order, WAIT_SECONDS_FOR_BUY)
                    
                    if Lib.hasClosed(order):
                        order['price'] = self.getFilledPrice(order) # 주문가를 체결가로 정정
                        break
                    else:
                        logger.info("{:10} | {}초 동안 미체결되어 매수 취소함", lowest['symbol'], WAIT_SECONDS_FOR_BUY)
                        Lib.api.cancel_order(order['id'], lowest['symbol'])  # 30초 동안 체결되지 않으면 주문 취소한다.

                if countOfFailure > 0:
                    logger.info("{:10} | 에러 복구 됨", lowest['symbol'])
                    countOfFailure = 0

            except Exception as ex:
                countOfFailure += 1
                logger.warning("{:10} | {} Raised an exception. {}", lowest['symbol'], countOfFailure, repr(ex))
                TelegramBot.sendMsg("{:10} | {} Raised an exception. {}".format(lowest['symbol'], countOfFailure, repr(ex)))
                if countOfFailure >= TRY_COUNT:
                    raise ex  # 1초 뒤에 다시 시도해 보고 연속 5번 exception 나면 매매를 종료한다.

            time.sleep(1) # 1초에 두 번 취소->주문 되는걸 방지하기 위해 1초를 쉰다.

        return order