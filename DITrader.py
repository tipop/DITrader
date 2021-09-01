from numpy import percentile
from lib.ApiLib import *
import os.path
import time
import beepy

class DITrader:
    def __init__(self, symbol, isBucketMode):
        self.symbol = symbol
        self.isBucketMode = isBucketMode

        pathHere = os.path.dirname(__file__)
        filePath = os.path.join(pathHere, 'api.txt')

        self.lib = Lib(filePath)
        self.api = self.lib.getBinanceApi()

    def startTrading(self, targetDI, marginRatio):
        # 1. DI trading
        #

        # 2. Bucket trading
        bucketBot = BucketBot(self.symbol, self.lib)
        bucketBot.start(targetDI, marginRatio)
        

class BucketBot:
    def __init__(self, symbol, lib):
        self.symbol = symbol
        self.lib = lib

    def stop(self):
        pass

    def start(self, targetDI, marginRatio):
        self.targetDI = targetDI
        self.marginRatio = marginRatio

        while True:
            order = self.BucketOrderLoop()   # 바스켓이 체결되면 리턴된다.
            beepy.beep(sound="ready")
            
            position = Position(
                lib = self.lib,
                symbol = self.symbol,
                order = order, 
                profitPercent = 1.01,        # x% 익절
                triggerPercentForStoploss = 1.004)    # x% 상승하면 본절로스를 건다.
                
            pnl = position.waitForPositionClosed()  # 포지션이 종료되면 리턴된다. (익절이든 본절/손절이든)

    def orderBuyTargetDI(self):
        curPrice = self.lib.getCurrentPrice(self.symbol)
        ma20 = self.lib.get20Ma(self.symbol, curPrice)
        targetPrice = ma20 * (1 - self.targetDI)
        quantity = self.lib.getQuantity(curPrice, self.marginRatio)
        return self.api.create_limit_buy_order(self.symbol, quantity, targetPrice)

    def BucketOrderLoop(self):
        TRY_COUNT = 5
        countOfFailure = 0
        order = None
        api = self.lib.api

        while True:
            now = dt.datetime.now()
            if now.second != 59 and now.second != 29:
                time.sleep(0.5)
                continue

            # 매분 59초가 되면 바스켓 주문을 업데이트 한다. (취소 후 재주문)
            nowStr = now.strftime("%Y-%m-%d %H:%M:%S")
            
            try:
                if order != None:
                    order = api.fetch_order(order['id'], self.symbol)

                    # 바스켓 매수 체결됨
                    if self.lib.hasClosed(order):
                        print(nowStr, self.symbol, "[바스켓] 체결되었다: ", order['price'])
                        break
                    else:   # 미체결 매수취소
                        api.cancel_order(order['id'], self.symbol)
                        order = None

                # (재) 매수 주문
                if order == None:
                    order = self.orderBuyTargetDI()

                countOfFailure = 0
            
            except Exception as ex:
                print("Exception failure count: ", countOfFailure, ex)
                countOfFailure += 1
                if countOfFailure >= TRY_COUNT:
                    raise ex  # 30초 뒤에 시도해 보고 연속 5번 exception 나면 매매를 종료한다.

            time.sleep(1)   # 1초에 두 번 취소->주문 되는걸 방지하기 위해 1초를 쉰다. 

        return order # 체결된 바스켓 주문을 리턴한다.


class Position:
    def __init__(self, lib, symbol, order, profitPercent, triggerPercentForStoploss):    
        self.lib = lib
        self.symbol = symbol
        self.positionOrder = order
        self.profitPrice = order['price'] * profitPercent
        self.triggerPriceForStoploss = order['price'] * triggerPercentForStoploss
        
        self.stopOrder = None
        self.profitOrder = None
    
    def orderProfit(self):
        self.profitOrder = self.lib.api.create_limit_sell_order(
            self.symbol, 
            self.positionOrder['filled'], 
            self.profitPrice)
    
    def orderStoploss(self, stoplossPercent):
        stoplossPrice = self.positionOrder['price'] * stoplossPercent
        
        #params = {'stopPrice': stopP, 'reduceOnly': True}
        # 스탑 가격이 평단가보다 높을 때는 수익권일 때만 주문이 들어간다.
        params = {'stopPrice': stoplossPrice}

        self.stopOrder = self.lib.api.createOrder(
            self.symbol,
            'stop_market',
            'sell',
            self.positionOrder['filled'],
            None,
            params)

    def isStopTriggerPriceOver(self):
        return self.lib.getCurrentPrice(self.symbol) > self.triggerPriceForStoploss

    def hasProfitOrderClosed(self):
        self.profitOrder = self.lib.api.fetch_order(self.profitOrder['id'], self.symbol)
        return self.profitOrder['status'] == 'closed'

    def hasStopOrderClosed(self):
        self.stopOrder = self.lib.api.fetch_order(self.stopOrder['id'], self.symbol)
        return self.stopOrder['status'] == 'closed'
    
    def getPNL(self, nowStr):
        pnl = 0
        
        if self.profitOrder != None and self.profitOrder['status'] == 'closed':
            pnl = (self.profitOrder['price'] - self.positionOrder['price']) / self.positionOrder['price']
            print(nowStr, self.symbol, "[바스켓] ## 익절완료. pnl: ", pnl)
            beepy.beep(sound='success')
        
        elif self.stopOrder != None and self.stopOrder['status'] == 'closed':
            pnl = (self.stopOrder['price'] - self.positionOrder['price']) / self.positionOrder['price']
            print(nowStr, self.symbol, "[바스켓] ## 본절완료. pnl: ", pnl)
            beepy.beep(sound='ping')

        # 손익 % 뿐만아니라 손익 금액 및 잔고 변화도 출력해야한다.
        return pnl

    def waitForPositionClosed(self):
        TRY_COUNT = 5
        countOfFailure = 0

        # 익절 주문 걸고 시작
        self.orderProfit()
        print("[바스켓]", self.symbol, "익절 주문: ", self.profitOrder['price'])
        

        while True:
            now = dt.datetime.now()
            nowStr = now.strftime("%Y-%m-%d %H:%M:%S")

            try:
                # 본절 로스 조건부 주문 (1회)
                if self.stopOrder == None and self.isStopTriggerPriceOver():
                    self.orderStoploss(1.001)
                    print(nowStr, self.symbol, "[바스켓] 본절로스 주문: ", self.stopOrder['price'])

                # 익절 체결됐나
                if self.hasProfitOrderClosed():
                    if self.stopOrder != None:
                        self.lib.api.cancel_order(self.stopOrder['id'], self.symbol)
                    break

                # 스탑로스 체결됐나
                if self.stopOrder != None and self.hasStopOrderClosed():
                    if self.profitOrder != None:
                        self.lib.api.cancel_order(self.profitOrder['id'], self.symbol)
                    break

                countOfFailure = 0

            except Exception as ex:
                print("Exception failure count: ", countOfFailure, ex)
                countOfFailure += 1
                if countOfFailure >= TRY_COUNT:
                    raise ex  # 30초 뒤에 시도해 보고 연속 5번 exception 나면 매매를 종료한다.

            time.sleep(5)

        return self.getPNL(nowStr)
        
        # 포지션을 들고 있는 상태에서
        #   - 2초마다 본절스탑 트리거 이상 상승했는지는 체크해서 +0.1%에 스탑로스 주문을 넣어야 한다.
        #   - 익절주문/스탑주문이 체결되었는지 체크하는건 10초마다 해도 된다.