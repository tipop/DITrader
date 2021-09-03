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
import telegram

def readJsonSetting(jsonFile):
    with open(jsonFile, "r") as file:
        return json.load(file)
        
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
Lib.init(js['binanceApi']['key'], js['binanceApi']['secret'])

telegramBot = telegram.Bot(js['telegramToken'])
updates = telegramBot.getUpdates()
#telegramBot.sendMessage(chat_id = updates[0].message.chat_id, text = "")

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