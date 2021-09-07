from lib.ApiLib import *
from Position import *
import time
from loguru import logger
from OrderInfo import *
from TelegramBot import *

WAIT_SECONDS_FOR_BUY = 30

isBuckbotSuspend = False

class CatchBot:
    def __init__(self, symbol, option):
        self.symbol = symbol
        self.option = option

    def stop(self):
        pass

    def start(self):
        logger.info("{:10} | Start CatchBot", self.symbol)

        while True:
            try:
                order = self.waitForCatch() # 타겟 이격도 이상 급락하면 매수해서 리턴된다.

                position = Position(order, self.option)
                    
                pnl = position.waitForPositionClosed()  # 포지션이 종료되면 리턴된다. (익절이든 본절/손절이든)
                logger.info("{:10} | 캐치 포지션 종료. PNL: {:10.5f}%", self.symbol, pnl)
                TelegramBot.sendMsg("{:10} | 캐치 포지션 종료. PNL: {:10.5f}%".format(self.symbol, pnl))
            
            except Exception as ex:
                logger.error("{:10} | CatchBot 종료. Exception: {}", self.symbol, repr(ex))
                TelegramBot.sendMsg("{:10} | CatchBot 종료. Exception: {}".format(self.symbol, repr(ex)))
                break

    def waitForBuyClosed(self, order, waitSeconds):
        if Lib.hasClosed(order):
            return order

        for sec in range(waitSeconds):
            o = Lib.api.fetch_order(order['id'], self.symbol)

            if Lib.hasClosed(o):
                break
            
            time.sleep(1)

        return o

    def getTargetDIPrice(self, curPrice):
        ma20 = Lib.get20Ma(self.symbol, curPrice)
        targetPrice = ma20 * (1 - self.option.targetDI)
        return targetPrice

    def orderBuyLimit(self, price):
        quantity = Lib.getQuantity(price, self.option.marginRatio)
        return Lib.api.create_limit_buy_order(self.symbol, quantity, price)
    
    def getFilledPrice(self, order):
        usdtSize = 0
        entryPrice = order['price']

        for i in range(3):
            try:
                positions = Lib.api.fetch_positions(self.symbol)
                break
            except:
                time.sleep(1)
                continue
        
        if len(positions) > 0 and positions[0]['entryPrice'] != None:
             entryPrice = positions[0]['entryPrice']
             usdtSize = positions[0]['entryPrice'] * positions[0]['contracts']
        
        logger.info("{:10} | 캐치 매수 체결됨: {:10.5f} / {}USDT", self.symbol, entryPrice, usdtSize)
        TelegramBot.sendMsg("{:10} | 캐치 매수 체결됨: {:10.5f} / {}USDT".format(self.symbol, entryPrice, usdtSize))
        return entryPrice

    def waitForCatch(self):
        global isBuckbotSuspend

        countOfFailure = 0
        order = None
        isBuckbotSuspend = False

        while True:
            if dt.datetime.now().second != 59:
                time.sleep(0.5)
                continue

            try:
                curPrice = Lib.getCurrentPrice(self.symbol)
                targetPrice = self.getTargetDIPrice(curPrice)
                
                if targetPrice >= curPrice:
                    logger.debug("{:10} | 캐치 만족: {:10.5f}", self.symbol, targetPrice)
                    isBuckbotSuspend = True # 매수할 때 잔고 여유가 있어야 하므로 bucketBot 대기 매수를 전부 취소하고 스레드를 일시 중지한다.
                    time.sleep(1)

                    order = self.orderBuyLimit(targetPrice)     # 1분봉 종료 시 이격도를 만족하면 지정가 매수한다.
                    logger.info("{:10} | 캐치 매수 주문: {:10.5f}", self.symbol, targetPrice)
                    order = self.waitForBuyClosed(order, WAIT_SECONDS_FOR_BUY)
                    
                    if Lib.hasClosed(order):
                        order['price'] = self.getFilledPrice(order) # 주문가를 체결가로 정정
                        break
                    else:
                        logger.info("{:10} | {}초 동안 미체결되어 매수 취소함", self.symbol, WAIT_SECONDS_FOR_BUY)
                        Lib.api.cancel_order(order['id'], self.symbol)  # 30초 동안 체결되지 않으면 주문 취소한다.
                        isBuckbotSuspend = False

                if countOfFailure > 0:
                    logger.info("{:10} | 에러 복구 됨", self.symbol)
                    countOfFailure = 0

            except Exception as ex:
                countOfFailure += 1
                logger.warning("{:10} | {} Raised an exception. {}", self.symbol, countOfFailure, repr(ex))
                if countOfFailure >= TRY_COUNT:
                    raise ex  # 1초 뒤에 다시 시도해 보고 연속 5번 exception 나면 매매를 종료한다.

            time.sleep(1) # 1초에 두 번 취소->주문 되는걸 방지하기 위해 1초를 쉰다.

        return order