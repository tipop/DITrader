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

def startCatchBot(symbol, option):
    CatchBot(symbol, option).start()

def parseCatchOption(jsCatch):
    option = OrderInfo(
        targetDI = jsCatch['targetDI'],
        marginRatio = jsCatch['marginRatio'],
        profitPercent = jsCatch['profitPercent'],
        stoplossTriggerPercent = jsCatch['stoplossTriggerPercent'],
        stoplossPercent = 0.001)

    logger.info("TargetDI: {}%", option.targetDI * 100)
    logger.info("Profit: {}%", option.profitPercent * 100)
    logger.info("StoplossTrigger: {}%", option.stoplossTriggerPercent * 100)
    logger.info("MarginRatio: {}%", option.marginRatio * 100)

    return option

#################### main ####################
js = readJsonSetting("trade_setting.json")
initApi('api.txt')
logger.add('logs/log.log', level='INFO')
logger.info("CatchBot: {} | BucketBot: {} | Symbols: {}", js['useCatchBot'], js['useBucketBot'], len(js['symbols']))


if js['useCatchBot']:
    option = parseCatchOption(js['catch'][0])   # 1번 DI 타겟

    for coin in js["symbols"]:
        t = threading.Thread(target = startCatchBot, args = (coin, option))
        t.start()


if js['useBucketBot']:
    for coin in js["symbols"]:
        t = threading.Thread(target = startBucketBot, args=(coin, js['bucket']))
        t.start()