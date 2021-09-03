class OrderInfo:
    def __init__(self, symbol, targetDI, marginRatio, profitPercent, stoplossTriggerPercent, stoplossPercent):
        self.symbol = symbol
        self.targetDI = targetDI
        self.marginRatio = marginRatio
        self.profitPercent = profitPercent
        self.stoplossTriggerPercent = stoplossTriggerPercent
        self.stoplossPercent = stoplossPercent