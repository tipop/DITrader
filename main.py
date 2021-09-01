# main.py
# 2021.08.28 ~ 
# Shin, SangYun

import threading
from lib.ApiLib import *
from DITrader import *
import pprint

def startDITrading(symbol, isBucketMode):
    coin = DITrader(symbol=symbol, isBucketMode=isBucketMode)
    # coin.startTrading(targetDI=0.009, marginRatio=0.04)
    coin.startTrading(targetDI=0.03, marginRatio=0.5)
    
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

print("Target symbols: ", len(coinList))
pprint.pprint(coinList)

for coin in coinList:
    t = threading.Thread(target = startDITrading, args=(coin, True))    
    t.start()


# new thread
# bucketBot = BucketBot(binance, symbol)
# bucketBot.startBucketTrading()