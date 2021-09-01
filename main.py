# main.py
# 2021.08.28 ~ 
# Shin, SangYun

import threading
from DITrader import *
import json
from loguru import logger

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

logger.add('logs/log.log', level='INFO')
logger.info("TargetDI: " + str(bucketJs['targetDI']*100) + "%")
logger.info("profit: " + str(bucketJs['profitPercent']*100) + "%")
logger.info("marginRatio: " + str(bucketJs['marginRatio']*100) + "%")
logger.info("stoplossTrigger: " + str(bucketJs['stoplossTriggerPercent']*100) + "%")
logger.info("Target Symbols: " + str(len(coinList)))
logger.info(coinList)

for coin in coinList:
    t = threading.Thread(target = startDITrading, args=(coin, bucketJs))
    t.start()


# new thread
# bucketBot = BucketBot(binance, symbol)
# bucketBot.startBucketTrading()