from lib.ApiLib import *
from Position import *
import time
import beepy
from loguru import logger

TRY_COUNT = 5 

class BucketBot:
    def __init__(self, symbol):
        self.symbol = symbol

    def stop(self):
        pass

    def start(self, bucketJs):
        logger.info("{} | Start bucketBot", self.symbol)

        self.targetDI = bucketJs['targetDI']
        self.marginRatio = bucketJs['marginRatio']

        while True:
            try:
                order = self.BucketOrderLoop()   # 바스켓이 체결되면 리턴된다.
                beepy.beep(sound="ready")
                
                position = Position(
                    symbol = self.symbol,
                    order = order, 
                    bucketJs = bucketJs)
                    
                pnl = position.waitForPositionClosed()  # 포지션이 종료되면 리턴된다. (익절이든 본절/손절이든)
                logger.info("{} | 포지션 종료. PNL: {}%", self.symbol, pnl)

            except Exception as ex:
                logger.error("{} | BucketBot 종료. Exception: {}", self.symbol, repr(ex))
                break

    def orderBuyTargetDI(self, curPrice, ma20):
        
        targetPrice = ma20 * (1 - self.targetDI)
        quantity = Lib.getQuantity(curPrice, self.marginRatio)
        return Lib.api.create_limit_buy_order(self.symbol, quantity, targetPrice)

    def BucketOrderLoop(self):
        countOfFailure = 0
        order = None

        while True:
            now = dt.datetime.now()
            if now.second != 59 and now.second != 29:
                time.sleep(0.5)
                continue

            try:
                if order != None:
                    order = Lib.api.fetch_order(order['id'], self.symbol)

                    # 바스켓 매수 체결됨
                    if Lib.hasClosed(order):

                        break
                    else:   # 미체결 매수취소
                        Lib.api.cancel_order(order['id'], self.symbol)
                        order = None

                # (재) 매수 주문
                if order == None:
                    curPrice = Lib.getCurrentPrice(self.symbol)
                    ma20 = Lib.get20Ma(self.symbol, curPrice)
                    if curPrice < ma20: # 20 이평 아래 있을 때만 바스켓 매수 주문을 낸다.
                        order = self.orderBuyTargetDI(curPrice, ma20)

                if countOfFailure > 0:
                    logger.info("{} | 에러 복구 됨", self.symbol)
                    countOfFailure = 0
            
            except Exception as ex:
                countOfFailure += 1
                logger.warning("{} | {} Raised an exception. {}", self.symbol, countOfFailure, repr(ex))
                if countOfFailure >= TRY_COUNT:
                    raise ex  # 30초 뒤에 시도해 보고 연속 5번 exception 나면 매매를 종료한다.

            time.sleep(1)   # 1초에 두 번 취소->주문 되는걸 방지하기 위해 1초를 쉰다. 

        return order # 체결된 바스켓 주문을 리턴한다.