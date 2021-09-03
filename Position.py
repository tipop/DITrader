
from lib.ApiLib import *
import time
import beepy
from loguru import logger

TRY_COUNT = 5 

class Position:
    def __init__(self, order, option):
        self.symbol = order['symbol']
        self.positionOrder = order
        self.profitPrice = order['price'] * (1 + option.profitPercent)
        self.triggerPriceForStoploss = order['price'] * (1 + option.stoplossTriggerPercent)
        
        self.stopOrder = None
        self.profitOrder = None
    
    def orderProfit(self):
        self.profitOrder = Lib.api.create_limit_sell_order(
            self.symbol, 
            self.positionOrder['filled'],
            self.profitPrice)
    
    def orderStoploss(self, stoplossPercent):
        stoplossPrice = self.positionOrder['price'] * stoplossPercent
        
        #params = {'stopPrice': stopP, 'reduceOnly': True}
        # 스탑 가격이 평단가보다 높을 때는 수익권일 때만 주문이 들어간다.
        params = {'stopPrice': stoplossPrice}

        self.stopOrder = Lib.api.createOrder(
            self.symbol,
            'stop_market',
            'sell',
            self.positionOrder['filled'],
            None,
            params)

    def isStopTriggerPriceOver(self):
        return Lib.getCurrentPrice(self.symbol) > self.triggerPriceForStoploss

    def hasProfitOrderClosed(self):
        self.profitOrder = Lib.api.fetch_order(self.profitOrder['id'], self.symbol)
        return self.profitOrder['status'] == 'closed'

    def hasStopOrderClosed(self):
        self.stopOrder = Lib.api.fetch_order(self.stopOrder['id'], self.symbol)
        return self.stopOrder['status'] == 'closed'
    
    def getPNL(self):
        pnl = 0
        
        if self.profitOrder != None and self.profitOrder['status'] == 'closed':
            pnl = (self.profitOrder['price'] - self.positionOrder['price']) / self.positionOrder['price']
            logger.info("{} | 익절 완료. PNL: {}", self.symbol, pnl)
            beepy.beep(sound='success')
        
        elif self.stopOrder != None and self.stopOrder['status'] == 'closed':
            pnl = (self.stopOrder['price'] - self.positionOrder['price']) / self.positionOrder['price']
            logger.info("{} | 본절 완료. PNL: {}", self.symbol, pnl)
            beepy.beep(sound='ping')

        # 손익 % 뿐만아니라 손익 금액 및 잔고 변화도 출력해야한다.
        return pnl

    def waitForPositionClosed(self):
        countOfFailure = 0

        # 익절 주문 걸고 시작
        self.orderProfit()
        logger.info("{} | 익절 주문: {}", self.symbol, self.profitOrder['price'])
        

        while True:
            try:
                # 본절 로스 조건부 주문 (1회)
                if self.stopOrder == None and self.isStopTriggerPriceOver():
                    self.stopOrder = self.orderStoploss(1.001)
                    logger.info("{} | 본절로스 주문: {}", self.symbol, self.stopOrder['price'])

                # 익절 체결됐나
                if self.hasProfitOrderClosed():
                    if self.stopOrder != None:
                        Lib.api.cancel_order(self.stopOrder['id'], self.symbol)
                    break

                # 스탑로스 체결됐나
                if self.stopOrder != None and self.hasStopOrderClosed():
                    if self.profitOrder != None:
                        Lib.api.cancel_order(self.profitOrder['id'], self.symbol)
                    break

                if countOfFailure > 0:
                    logger.info("{} | 에러 복구 됨", self.symbol)
                    countOfFailure = 0

            except Exception as ex:
                countOfFailure += 1
                logger.warning("{} | {} Raised an exception. {}", self.symbol, countOfFailure, repr(ex))
                if countOfFailure >= TRY_COUNT:
                    raise ex  # 30초 뒤에 시도해 보고 연속 5번 exception 나면 매매를 종료한다.

            #time.sleep(5)
            time.sleep(2)

        return self.getPNL()
        
        # 포지션을 들고 있는 상태에서
        #   - 2초마다 본절스탑 트리거 이상 상승했는지는 체크해서 +0.1%에 스탑로스 주문을 넣어야 한다.
        #   - 익절주문/스탑주문이 체결되었는지 체크하는건 10초마다 해도 된다.