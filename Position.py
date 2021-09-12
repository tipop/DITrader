
from lib.ApiLib import *
import time
from loguru import logger
from TelegramBot import *

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
        params = {'reduceOnly': True}

        self.profitOrder = Lib.api.create_limit_sell_order(
            self.symbol, 
            self.positionOrder['filled'],
            self.profitPrice,
            params)

        return self.profitOrder
    
    def orderStoploss(self, stoplossPercent):
        stoplossPrice = self.positionOrder['price'] * stoplossPercent
        
        #params = {'stopPrice': stopP, 'reduceOnly': True}
        # 스탑 가격이 평단가보다 높을 때는 수익권일 때만 주문이 들어간다.
        params = {'stopPrice': stoplossPrice, 'reduceOnly': True}

        self.stopOrder = Lib.api.createOrder(
            self.symbol,
            'stop_market',
            'sell',
            self.positionOrder['filled'],
            None,
            params)

        return self.stopOrder

    def isStopTriggerPriceOver(self):
        return Lib.getCurrentPrice(self.symbol) > self.triggerPriceForStoploss

    def isPositionOpen(self):
        positions = Lib.api.fetch_positions(self.symbol)
        
        # 실제 리턴되는 position 객체에는 'status' 변수가 없다...
        # 포지션이 종료되도 list에 항목이 남아있다.
        # 포지션이 종료되면 side = None 로 변하기 때문에 이를 판단 기준으로 삼는다.
        if positions != None and len(positions) > 0 and positions[0] != None and positions[0]['side'] != None: 
            #logger.debug("{:10} 포지션 존재", self.symbol)
            return True

        #logger.debug("{:10} 포지션 없음", self.symbol)
        return False

    def hasProfitOrderClosed(self):
        self.profitOrder = Lib.api.fetch_order(self.profitOrder['id'], self.symbol)
        return self.profitOrder['status'] == 'closed'

    def hasStopOrderClosed(self):
        self.stopOrder = Lib.api.fetch_order(self.stopOrder['id'], self.symbol)
        return self.stopOrder['status'] == 'closed'

    def getPNL(self):
        pnl = 0
        ## TODO: 아래 코드는 동작하지 않는다. 각 order를 API로 물어보지 않고 값을 체크하고 있기 때문이다.
        # position 객체로 변경할 때 한꺼번에 수정한다.
        if self.profitOrder != None and self.profitOrder['status'] == 'closed':
            pnl = (self.profitOrder['price'] - self.positionOrder['price']) / self.positionOrder['price']
            logger.info("{:10} | 익절 완료. PNL: {:10.5f}", self.symbol, pnl)
        
        elif self.stopOrder != None and self.stopOrder['status'] == 'closed':
            pnl = (self.stopOrder['price'] - self.positionOrder['price']) / self.positionOrder['price']
            logger.info("{:10} | 본절 완료. PNL: {:10.5f}", self.symbol, pnl)

        # 손익 % 뿐만아니라 손익 금액 및 잔고 변화도 출력해야한다.
        return pnl

    def waitForPositionClosed(self):
        SLEEP_SEC = 0.2
        countOfFailure = 0
        positionOpenTime = dt.datetime.now()
        after3min = positionOpenTime + dt.timedelta(minutes=3)
        
        # 익절 주문 걸고 시작
        self.orderProfit()
        logger.info("{:10} | 익절 주문: {:10.5f}", self.symbol, self.profitOrder['price'])

        while True:
            try:
                positions = Lib.api.fetch_positions(self.symbol)
                if not (positions != None and len(positions) > 0 and positions[0] != None and positions[0]['side'] != None):
                    if self.hasProfitOrderClosed(): # 익절이 체결되면 스탑로스 주문이 자동으로 취소되지 않기에 수동으로 취소해야한다. (스탑로스가 체결되면 익절 주문은 자동 취소 됨)
                        Lib.api.cancel_order(self.stopOrder['id'], self.symbol)
                        logger.debug("{:10} | 스탑로스 취소: {:10.5f}", self.symbol, self.stopOrder['price'])
                    break

                # 본절 로스 조건부 주문 (1회)
                if self.stopOrder == None and self.isStopTriggerPriceOver():
                    self.orderStoploss(1.001)
                    #logger.info("{:10} | 본절로스 주문: {:10.5f}", self.symbol, self.stopOrder['price'])  => TypeError('unsupported format string passed to NoneType.__format__')
                    logger.info("{:10} | 본절로스 주문", self.symbol)
            
                # 손절
                if dt.datetime.now() >= after3min and positions != None and len(positions) > 0 and positions[0]['unrealizedPnl'] < 0:
                    curPrice = Lib.getCurrentPrice(self.symbol)
                    pnlPercent = ((curPrice - positions[0]['entryPrice']) / positions[0]['entryPrice']) * 100
                    if pnlPercent <= -3:    # 3분 후에도 -3% 손실 중이면 손절
                        params = {'reduceOnly': True}
                        Lib.api.create_market_sell_order(self.symbol, positions[0]['contractSize'], params)
                        logger.info("{:10} | 손절 완료. {} %\t {} USDT", self.symbol, pnlPercent, positions[0]['unrealizedPnl'])
                        TelegramBot.sendMsg("{:10} | 손절 완료. {} %\t {} USDT".format(self.symbol, pnlPercent, positions[0]['unrealizedPnl']))
                        raise Exception("손절되어 캐치 감시 종료")
                        #break

                if countOfFailure > 0:
                    logger.info("{:10} | 에러 복구 됨", self.symbol)
                    countOfFailure = 0

            except Exception as ex:
                countOfFailure += 1
                logger.warning("{:10} | {} Raised an exception: {}", self.symbol, countOfFailure, repr(ex))
                TelegramBot.sendMsg("{:10} | {} Raised an exception: {}".format(self.symbol, countOfFailure, repr(ex)))
                if countOfFailure >= TRY_COUNT:
                    raise ex  # 30초 뒤에 시도해 보고 연속 5번 exception 나면 매매를 종료한다.

            time.sleep(SLEEP_SEC)

        return self.getPNL()