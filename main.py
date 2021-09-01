# main.py
# 2021.08.28 ~ 
# Shin, SangYun

import threading
from DITrader import *
import pprint
import json
#from loguru import logger

def startDITrading(symbol, bucketJs):
    coin = DITrader(symbol, True)
    coin.startTrading(bucketJs)

def readJsonSetting():
    with open("trade_setting.json", "r") as jsonFile:
        return json.load(jsonFile)

#################### main ####################
js = readJsonSetting()
bucketJs = js['bucket']
coinList = js["symbols"]

print("\nTargetDI:\t", bucketJs['targetDI']*100, "%")
print("profit:\t\t", bucketJs['profitPercent']*100, "%")
print("marginRatio:\t", bucketJs['marginRatio']*100, "%")
print("stoplossTrigger:", bucketJs['stoplossTriggerPercent']*100, "%")
print("\nTarget Symbols:\t", len(coinList))
pprint.pprint(coinList)


for coin in coinList:
        t = threading.Thread(target = startDITrading, args=(coin, bucketJs))
        t.start()


# new thread
# bucketBot = BucketBot(binance, symbol)
# bucketBot.startBucketTrading()