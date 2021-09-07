# main.py
# 2021.08.28 ~ 
# Shin, SangYun

import sys
import json
import threading
from BucketBot import *
from CatchBot import *
from OrderInfo import *
from loguru import logger
from TelegramBot import *

def readJsonSetting(jsonFile):
    with open(jsonFile, "r") as file:
        return json.load(file)

def parseJsOption(jsOption):
    return OrderInfo(
        targetDI = jsOption['targetDI'],
        marginRatio = jsOption['marginRatio'],
        profitPercent = jsOption['profitPercent'],
        stoplossTriggerPercent = jsOption['stoplossTriggerPercent'],
        stoplossPercent = 0.001)

def startBucketBot(symbol, option):
    BucketBot(symbol, option).start()

def startCatchBot(symbol, option):
    CatchBot(symbol, option).start()

def getStartMsg():
    return "Start!!\nCatch: {} | Bucket: {} | Symbols: {}\n\
    BucketBot\n\
        - TargetDI: {:.1f}%\n\
        - profit: {:.1f}%\n\
        - stoplossTrigger: {:.1f}%\n\
        - marginRatio: {:.1f}%\n\
    CatchBot\n\
        - TargetDI: {:.1f}%\n\
        - profit: {:.1f}%\n\
        - stoplossTrigger: {:.1f}%\n\
        - marginRatio: {:.1f}%".format(js['useCatchBot'], js['useBucketBot'], len(js['symbols']), 
            bucketOption.targetDI*100, bucketOption.profitPercent*100, bucketOption.stoplossTriggerPercent*100, bucketOption.marginRatio*100,
            catchOption.targetDI*100, catchOption.profitPercent*100, catchOption.stoplossTriggerPercent*100, catchOption.marginRatio*100)

def panicSellAlarm(symbols, deltaForAlarm):
    prevPriceList = {}

    for symbol in symbols:
        prevPriceList[symbol] = Lib.getCurrentPrice(symbol)

    while True:
        time.sleep(5)

        for symbol in symbols:
            curPrice = Lib.getCurrentPrice(symbol)
            prevPrice = prevPriceList[symbol]
            deltaPercent = ((curPrice - prevPrice) / prevPrice) * 100
            
            if deltaPercent <= deltaForAlarm:
                logger.info("{:10} | {:10.2f}% 급락", symbol, deltaPercent)
                TelegramBot.sendMsg("{:10} | {:10.2f}% 급락".format(symbol, deltaPercent))

            prevPriceList[symbol] = curPrice
    
    
#################### main ####################
js = readJsonSetting("trade_setting.json")
Lib.init(js['binanceApi']['key'], js['binanceApi']['secret'])
catchOption = parseJsOption(js['catch'][0])   # 1번 DI 타겟
bucketOption = parseJsOption(js['bucket'])

logger.remove()
logger.add('logs/log.log', level = js['log']['fileLevel'])
logger.add(sys.stderr, level = js['log']['consoleLevel'])
logger.info("CatchBot: {} | BucketBot: {} | Symbols: {}", js['useCatchBot'], js['useBucketBot'], len(js['symbols']))
TelegramBot.init(js['telegramToken'])

if js['useCatchBot']:
    for coin in js["symbols"]:
        threading.Thread(target = startCatchBot, args = (coin, catchOption)).start()

if js['useBucketBot']:    
    for coin in js["symbols"]:
        threading.Thread(target = startBucketBot, args=(coin, bucketOption)).start()

msg = getStartMsg()
logger.info("TelegramOn: {}", TelegramBot.isChatOn)
logger.info(msg)
TelegramBot.sendMsg(msg)

if js['panicSellAlarm']['use']:
    threading.Thread(target = panicSellAlarm, args=(js["symbols"], js['panicSellAlarm']['deltaPercent'])).start()