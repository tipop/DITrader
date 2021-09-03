# main.py
# 2021.08.28 ~ 
# Shin, SangYun

import json
import os.path
import threading
from BucketBot import *
from CatchBot import *
from OrderInfo import *

from loguru import logger

def readJsonSetting(jsonFile):
    with open(jsonFile, "r") as file:
        return json.load(file)

def initApi(apiFile):
    pathHere = os.path.dirname(__file__)
    filePath = os.path.join(pathHere, apiFile)
    Lib.init(filePath)

def startBucketBot(symbol, bucketJs):
    BucketBot(symbol).start(bucketJs)

def startCatchBot(orderInfo, notUsed):
    CatchBot(orderInfo).start()

def initLogging(bucketJs, coinList):
    logger.add('logs/log.log', level='INFO')
    logger.info("TargetDI: {}%", bucketJs['targetDI']*100)
    logger.info("profit: {}%", bucketJs['profitPercent']*100)
    logger.info("marginRatio: {}%", bucketJs['marginRatio']*100)
    logger.info("stoplossTrigger: {}%", bucketJs['stoplossTriggerPercent']*10)
    logger.info("Target Symbols: {}", len(coinList))
    #logger.info(coinList)


#################### main ####################
js = readJsonSetting("trade_setting.json")
bucketJs = js['bucket']
catchJs = js['catch']
coinList = js["symbols"]
initLogging(bucketJs, coinList)
initApi('api.txt')


for coin in coinList:
    #bucketThread = threading.Thread(target = startBucketBot, args=(coin, bucketJs))
    #bucketThread.start()

    orderInfo = OrderInfo(
    symbol = coin,
    targetDI = catchJs[0]['targetDI'],
    marginRatio = catchJs[0]['marginRatio'],
    profitPercent = catchJs[0]['profitPercent'],
    stoplossTriggerPercent = catchJs[0]['stoplossTriggerPercent'],
    stoplossPercent = 0.001)

    catchThread = threading.Thread(target = startCatchBot, args = (orderInfo, None))
    catchThread.start()