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

def startCatchBot(symbols, option):
    CatchBot(symbols, option).start()

def getStartMsg():
    return "CatchBot Start!!\nSymbols: {}\n\
    - TargetDI: {:.1f}%\n\
    - profit: {:.1f}%\n\
    - stoplossTrigger: {:.1f}%\n\
    - marginRatio: {:.1f}%".format(
        len(js['symbols']),
        catchOption.targetDI*100,
        catchOption.profitPercent*100, 
        catchOption.stoplossTriggerPercent*100, 
        catchOption.marginRatio*100)

def panicSellAlarm(symbols, deltaForAlarm):
    prevPriceList = {}

    for symbol in symbols:
        try:
            prevPriceList[symbol] = Lib.getCurrentPrice(symbol)
            time.sleep(0.2)
        except Exception as ex:
            logger.warning("{:10} | Raised an exception. {}", symbol, repr(ex))
            continue

    while True:
        time.sleep(5)

        for symbol in symbols:
            try:
                curPrice = Lib.getCurrentPrice(symbol)
                prevPrice = prevPriceList[symbol]
                deltaPercent = ((curPrice - prevPrice) / prevPrice) * 100
                
                if deltaPercent <= deltaForAlarm:
                    logger.info("{:10} | {:10.2f}% 급락", symbol, deltaPercent)
                    TelegramBot.sendMsg("{:10} | {:10.2f}% 급락".format(symbol, deltaPercent))

                prevPriceList[symbol] = curPrice
                time.sleep(0.2)

            except Exception as ex:
                logger.warning("{:10} | Raised an exception. {}", symbol, repr(ex))
                time.sleep(2)
                continue
    
#################### main ####################
js = readJsonSetting("trade_setting.json")
Lib.init(js['binanceApi']['key'], js['binanceApi']['secret'])
catchOption = parseJsOption(js['catch'][0])   # 1번 DI 타겟

logger.remove()
logger.add('logs/log.log', level = js['log']['fileLevel'])
logger.add(sys.stderr, level = js['log']['consoleLevel'])
logger.info("Symbols: {}", len(js['symbols']))
TelegramBot.init(js['telegramToken'])

if js['useCatchBot']:
    threading.Thread(target = startCatchBot, args = (js["symbols"], catchOption)).start()

if js['panicSellAlarm']['use']:
    threading.Thread(target = panicSellAlarm, args=(js["symbols"], js['panicSellAlarm']['deltaPercent'])).start()

msg = getStartMsg()
logger.info("TelegramOn: {}", TelegramBot.isChatOn)
logger.info(msg)
TelegramBot.sendMsg(msg)