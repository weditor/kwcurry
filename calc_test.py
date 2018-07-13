# from base import *
from extra import *


testf1 = Variable("x") + 3
testf2 = Variable("x") + Variable("y") + 3


is_teen = Select(
    Variable("年龄") > 18,
    Variable("x") * Variable("x"),
    Variable("x") + Variable("x")
)


can_buy_insure = Select(
    Variable("投保类型") == "续保",
    Between(Variable("年龄"), 1, 99),
    Between(Variable("年龄"), 1, 60),
)

age_value = Select(
    Variable("投保类型") == "续保",
    Range(1, 99),
    Range(1, 60),
)


if __name__ == '__main__':
    """
    """
    # # 基础测试
    # print(Variable("x").what())
    # print(testf2.what())
    #
    # # 测试是不是成年人
    # print(is_teen.what())
    # f = is_teen(年龄=17)
    # print("年龄=17: ", f.what())
    # print(f(x=10))

    # # 是否可以买保险
    # print(can_buy_insure(投保类型="续保", 年龄=100))
    # print(can_buy_insure(投保类型="续保", 年龄=90))
    # print(can_buy_insure(投保类型="首保", 年龄=90))
    # print(can_buy_insure(投保类型="首保", 年龄=5))
    # print(can_buy_insure.what())
    # print(can_buy_insure(年龄=5).what())
    # # print(can_buy_insure.what_of("年龄").what())
    #
    # # 年龄范围
    # print(age_value.what())
    # print(age_value(投保类型="首保"))
    # # 首保最大值.
    # print(maxof(age_value(投保类型="首保")))

    print("满足什么条件可以投保")
    for args in can_buy_insure.how_to_bool(True):
        print(args)

    print("--------------")
    for args in age_value.ask():
        print(args)


