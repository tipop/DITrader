class OrderInfo:
    def __init__(self, targetDI, marginRatio, profitPercent, stoplossTriggerPercent, stoplossPercent):
        self.targetDI = targetDI
        self.marginRatio = marginRatio
        self.profitPercent = profitPercent
        self.stoplossTriggerPercent = stoplossTriggerPercent
        self.stoplossPercent = stoplossPercent