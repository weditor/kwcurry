
class CalcBaseError(Exception):
    pass


# 无法回答
class CannotAnswerError(CalcBaseError):
    def __init__(self, msg):
        self.msg = msg
        super(CannotAnswerError, self).__init__()

    def __str__(self):
        return self.msg


class NotSupportCalcError(CalcBaseError):
    """不支持运算符"""
    def __init__(self, data, calc):
        self.data = data
        self.calc = calc

    def __str__(self):
        return "unsupported calc type (%s) for data (%s)" % (self.calc, self.data)

