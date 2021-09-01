# main.py
# 2021.08.28 ~ 
# Shin, SangYun

import threading
from lib.ApiLib import *
from DITrader import *
import pprint
import json

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

#TODO: 옵션을 JSON으로 분리한다.
#   - 공통 target DI 1, 2 3  (3 / 3.3 / 4.5)
#   - 공통 진입 배율(마진)
#   - symbol 목록
#   - symbol 별 target DI (명시할 때만 공통 target DI를 무시한다)
#   - 익절 %
#   - 본절 트리거 %