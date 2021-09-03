from lib.ApiLib import *
from Position import *
import time
import beepy
from loguru import logger
from OrderInfo import *

WAIT_SECONDS_FOR_BUY = 30

class CatchBot:
    def __init__(self, symbol, option):
        self.symbol = symbol
        self.option = option

    def start(self):
        logger.info("{} | Start catching", self.symbol)

        while True:
            try:
                order = self.waitForCatch() # 타겟 이격도 이상 급락하면 매수해서 리턴된다.
                beepy.beep(sound="ready")

                position = Position(order, self.option)
                    
                pnl = position.waitForPositionClosed()  # 포지션이 종료되면 리턴된다. (익절이든 본절/손절이든)
                logger.info("{} | 포지션 종료. PNL: {}%", self.symbol, pnl)
            
            except Exception as ex:
                logger.error("{} | CatchBot 종료. Exception: {}", self.symbol, repr(ex))
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

    def waitForCatch(self):
        countOfFailure = 0
        order = None

        while True:
            #if dt.datetime.now().second != 59:
            #    time.sleep(0.5)
            #    continue

            try:
                # 1분봉 종료 시 이격도를 만족하면 지정가 매수한다.
                curPrice = Lib.getCurrentPrice(self.symbol)
                targetPrice = self.getTargetDIPrice(curPrice)

                # 0.3%를 더한 이유는 밑꼬리가 0.5초 만에 순식간에 달리고 올라가는 경우가 많기 때문에 타겟 가격 0.3% 근처에 오면 미리 매수 주문을 넣어 두고 체결 안되면 취소하는게 낫다.
                if (targetPrice * 1.003) >= curPrice:
                    order = self.orderBuyLimit(targetPrice)
                    logger.info("{} | 캐치 매수 주문: {}", self.symbol, targetPrice)
                    beepy.beep(sound="coin")
                    order = self.waitForBuyClosed(order, WAIT_SECONDS_FOR_BUY)
                    
                    if Lib.hasClosed(order):
                        logger.info("{} | 매수 체결: {}", self.symbol, order['price'])
                        break   # 매수 체결되었으므로 캐치 종료
                    else:
                        logger.info("{} | {}초 동안 미체결되어 매수 취소함", self.symbol, WAIT_SECONDS_FOR_BUY)
                        Lib.api.cancel_order(order['id'], self.symbol)  # 30초 동안 체결되지 않으면 주문 취소한다.

                if countOfFailure > 0:
                    logger.info("{} | 에러 복구 됨", self.symbol)
                    countOfFailure = 0

            except Exception as ex:
                countOfFailure += 1
                logger.warning("{} | {} Raised an exception. {}", self.symbol, countOfFailure, repr(ex))
                if countOfFailure >= TRY_COUNT:
                    raise ex  # 1초 뒤에 다시 시도해 보고 연속 5번 exception 나면 매매를 종료한다.

            time.sleep(1) # 1초에 두 번 취소->주문 되는걸 방지하기 위해 1초를 쉰다.

        return order