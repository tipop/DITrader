# main.py
# 2021.08.28 ~ 
# Shin, SangYun
# 
# 절차지향에서 객체지향으로
#
import threading
from lib.ApiLib import *
from DITrader import *

def startDITrading(symbol, isBucketMode):
    print("Started monitoring: ", symbol)
    coin = DITrader(symbol=symbol, isBucketMode=isBucketMode)
    # coin.startTrading(targetDI=0.009, marginRatio=0.04)
    coin.startTrading(targetDI=0.033, marginRatio=0.5)
    

#################### main ####################
coinList = [
    "ADA/USDT",  
    "AXS/USDT", 
    "BCH/USDT",
    "BNB/USDT",
    "CHZ/USDT",
    "DOGE/USDT",
    "DOT/USDT",
    "EOS/USDT",
    "ETC/USDT",
    "FIL/USDT",
    "LINK/USDT",
    "LTC/USDT",
    "LUNA/USDT",
    "MANA/USDT",
    "MATIC/USDT",
    "ONE/USDT",
    "RSR/USDT",
    "SOL/USDT",
    "XRP/USDT",    
    ]   # 19개 (제외 코인: BTC, ETH)

print("Main started")

for coin in coinList:
    t = threading.Thread(target = startDITrading, args=(coin, True))    
    t.start()


# new thread
# bucketBot = BucketBot(binance, symbol)
# bucketBot.startBucketTrading()