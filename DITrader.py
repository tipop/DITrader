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
        ############### TEST ###########
        #order = self.lib.api.create_market_buy_order(self.symbol, 50)
        
        #stopP = order['price'] - (order['price'] * 0.01)
        #stopP = order['price'] + (order['price'] * 0.001)
        #params = {'stopPrice': stopP, 'reduceOnly': True}

        # 스탑 가격이 평단가보다 높을 때는 수익권일 때만 주문이 들어간다.
        #stopOrder = self.api.createOrder(
        #    self.symbol,
        #    'stop_market',
        #    'sell',
        #    order['filled'],
        #    None,
        #    params)

        #return

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

        # return
        #################################

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
            #pprint.pprint(order)
            beepy.beep(sound="ready")
            
            position = Position(
                lib = self.lib,
                symbol = self.symbol,
                order = order, 
                profitPercent = 1.01,        # x% 익절
                triggerPercentForStoploss = 1.004)    # x% 상승하면 본절로스를 건다.
                
            pnl = position.waitForClosed()  # 포지션이 종료되면 리턴된다. (익절이든 본절/손절이든)


    def BucketOrderLoop(self):
        order = None
        api = self.lib.api

        while True:
            now = dt.datetime.now()
            if now.second != 59 and now.second != 29:
                time.sleep(0.5)
                continue

            # 매분 59초가 되면 바스켓 주문을 업데이트 한다. (취소 후 재주문)
            nowStr = now.strftime("%Y-%m-%d %H:%M:%S")
            
            # 주문한게 체결되었나 안되었나? 
            if order != None:
                order = api.fetch_order(order['id'], self.symbol)

                # 바스켓 체결됨
                if self.lib.hasClosed(order):
                    print(nowStr, self.symbol, "[바스켓] 체결되었다: ", order['price'])
                    break # 함수 종료
                else:
                    # print(nowStr, self.symbol, "[바스켓] 미체결 취소: ", order['price'])
                    api.cancel_order(order['id'], self.symbol)
                    order = None

            # (재) 매수 주문
            if order == None:
                curPrice = self.lib.getCurrentPrice(self.symbol)
                ma20 = self.lib.get20Ma(self.symbol, curPrice)
                targetPrice = ma20 * (1 - self.targetDI)
                quantity = self.lib.getQuantity(curPrice, self.marginRatio)
                order = api.create_limit_buy_order(self.symbol, quantity, targetPrice)
                # print(nowStr, self.symbol, "[바스켓] 매수 주문: ", order['price'])

            time.sleep(1)   # 1초에 두번 취소->주문 되는걸 방지하기 위해 1초를 쉰다. 

        return order # 체결된 바스켓 주문을 리턴한다.


class Position:
    def __init__(self, lib, symbol, order, profitPercent, triggerPercentForStoploss):    
        self.lib = lib
        self.symbol = symbol
        self.positionOrder = order
        self.profitPrice = order['price'] * profitPercent
        self.triggerPriceForStoploss = order['price'] * triggerPercentForStoploss
    
    def waitForClosed(self):
        profitOrder = None
        stopOrder = None
        pnl = 0

        # 익절 주문 걸어두고
        profitOrder = self.lib.api.create_limit_sell_order(
            self.symbol, 
            self.positionOrder['filled'], 
            self.profitPrice)
        
        print("[바스켓]", self.symbol, "익절 주문: ", self.profitPrice)

        while True:
            
            now = dt.datetime.now()
            nowStr = now.strftime("%Y-%m-%d %H:%M:%S")

            if stopOrder == None:
                curPrice = self.lib.getCurrentPrice(self.symbol)
                if curPrice > self.triggerPriceForStoploss:
                    stoplossPrice = self.positionOrder['price'] * 1.001
                    
                    #params = {'stopPrice': stopP, 'reduceOnly': True}
                    # 스탑 가격이 평단가보다 높을 때는 수익권일 때만 주문이 들어간다.
                    params = {'stopPrice': stoplossPrice}

                    stopOrder = self.lib.api.createOrder(
                        self.symbol,
                        'stop_market',
                        'sell',
                        self.positionOrder['filled'],
                        None,
                        params)

                    print(nowStr, self.symbol, "[바스켓] 본절로스 주문: ", stoplossPrice)
            
            # 익절 체결되었으면 스탑로스를 취소한다.
            

            if profitOrder != None:
                profitOrder = self.lib.api.fetch_order(profitOrder['id'], self.symbol)
                if profitOrder['status'] == 'closed':
                    if stopOrder != None:
                        self.lib.api.cancel_order(stopOrder['id'], self.symbol)

                    pnl = 1     # TODO: pnl을 계산해서 리턴해야 한다.
                    print(nowStr, self.symbol, "[바스켓] 익절 체결 완료. pnl: ", pnl)
                    beepy.beep(sound='success')
                    break

            # 스탑로스 체결되었으면 익절 주문 취소한다.
            if stopOrder != None:
                stopOrder = self.lib.api.fetch_order(stopOrder['id'], self.symbol)
                if stopOrder['status'] == 'closed':
                    if profitOrder != None:
                        self.lib.api.cancel_order(profitOrder['id'], self.symbol)

                pnl = 1     # TODO: pnl을 계산해서 리턴해야 한다.
                print(nowStr, self.symbol, "[바스켓] 본절 체결 완료. pnl: ", pnl)
                beepy.beep(sound='ping')
                break

            time.sleep(5)
        
        return pnl
        
        # 포지션을 들고 있는 상태에서 
        #   - 2초마다 본절스탑 트리거 이상 상승했는지는 체크해서 +0.1%에 스탑로스 주문을 넣어야 한다.
        #   - 익절주문/스탑주문이 체결되었는지 체크하는건 10초마다 해도 된다.