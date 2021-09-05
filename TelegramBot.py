import telegram

class TelegramBot:
    def init(token):
        TelegramBot.telegramBot = telegram.Bot(token)
        TelegramBot.updates = TelegramBot.telegramBot.getUpdates()
        TelegramBot.isChatOn = len(TelegramBot.updates) > 0

    def sendMsg(msg):
        if TelegramBot.isChatOn:
            TelegramBot.telegramBot.sendMessage(TelegramBot.updates[0].message.chat_id, msg)