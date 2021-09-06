from lib.ApiLib import *
from Position import *
import time
from loguru import logger
from TelegramBot import *
import CatchBot

TRY_COUNT = 5

class BucketBot:
    def __init__(self, symbol, option):
        self.symbol = symbol
        self.option = option

    def stop(self):
        pass

    def start(self):
        logger.info("{:10} | Start BucketBot", self.symbol)

        while True:
            try:
                order = self.BucketOrderLoop()   # 바스켓이 체결되면 리턴된다.
                TelegramBot.sendMsg("{:10} | 바스켓 매수 체결됨: {:10.5f}".format(self.symbol, order['price']))
                
                position = Position(order, self.option)
                    
                pnl = position.waitForPositionClosed()  # 포지션이 종료되면 리턴된다. (익절이든 본절/손절이든)
                logger.info("{:10} | 바스켓 포지션 종료. PNL: {:10.5f}%", self.symbol, pnl)
                TelegramBot.sendMsg("{:10} | 바스켓 포지션 종료. PNL: {:10.5f}%".format(self.symbol, pnl))

            except Exception as ex:
                logger.error("{:10} | BucketBot 종료. Exception: {}", self.symbol, repr(ex))
                TelegramBot.sendMsg("{:10} | BucketBot 종료. Exception: {}".format(self.symbol, repr(ex)))
                break

    def orderBuyTargetDI(self, curPrice, ma20):
        targetPrice = ma20 * (1 - self.option.targetDI)
        quantity = Lib.getQuantity(curPrice, self.option.marginRatio)
        #logger.debug("{:10} | 매수 주문: {:10.5f}", self.symbol, targetPrice)
        return Lib.api.create_limit_buy_order(self.symbol, quantity, targetPrice)

    def BucketOrderLoop(self):
        countOfFailure = 0
        order = None

        while True:
            try:
                if CatchBot.isBuckbotSuspend == True:    # catch 포착되었으므로 여유 잔고를 비우기 위해 bucket 대기 매수 주문을 취소하고 일시중지한다.
                    if order != None:
                        logger.info("{:10} | Suspended. 미체결 취소: {:10.5f}", self.symbol, order['price'])
                        Lib.api.cancel_order(order['id'], self.symbol)
                        order = None

                    time.sleep(10)
                    continue

                now = dt.datetime.now()
                if now.second != 1:     #and now.second != 31:
                    time.sleep(0.2)     # time.sleep(0.5)
                    continue
            
                if order != None:
                    order = Lib.api.fetch_order(order['id'], self.symbol)

                    # 바스켓 매수 체결됨
                    if order != None:
                        if Lib.hasClosed(order):
                            logger.info("{:10} | 매수 체결됨: {:10.5f}", self.symbol, order['price'])
                            break
                        else:   # 미체결 매수취소
                            #logger.debug("{:10} | 미체결 취소: {:10.5f}", self.symbol, order['price'])
                            Lib.api.cancel_order(order['id'], self.symbol)
                            order = None

                # (재) 매수 주문
                if order == None:
                    curPrice = Lib.getCurrentPrice(self.symbol)
                    ma20 = Lib.get20Ma(self.symbol, curPrice)
                    if curPrice < ma20: # 20 이평 아래 있을 때만 바스켓 매수 주문을 낸다
                        order = self.orderBuyTargetDI(curPrice, ma20)

                if countOfFailure > 0:
                    logger.info("{:10} | 에러 복구 됨", self.symbol)
                    countOfFailure = 0
            
            except Exception as ex:
                countOfFailure += 1
                logger.warning("{:10} | {} Raised an exception. {}", self.symbol, countOfFailure, repr(ex))
                if countOfFailure >= TRY_COUNT:
                    raise ex  # 30초 뒤에 시도해 보고 연속 5번 exception 나면 매매를 종료한다.

            time.sleep(1)   # 1초에 두 번 취소->주문 되는걸 방지하기 위해 1초를 쉰다. 

        return order # 체결된 바스켓 주문을 리턴한다.