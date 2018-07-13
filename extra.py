
from base import *
from errors import CannotAnswerError
import sympy
import itertools


class Select(Calculable):
    def __init__(self, condition, choice1=None, choice2=None):
        self._condition = ensure_calculable(condition)
        self._choice1 = ensure_calculable(choice1)
        self._choice2 = ensure_calculable(choice2)

        self._out_args = get_out_args([self._condition, self._choice1, self._choice2])
        self._inner_args = {}

    def __call__(self, **kwargs):
        cond = self._condition(**kwargs)
        choice1 = self._choice1(**kwargs)
        choice2 = self._choice2(**kwargs)
        if isinstance(cond, Calculable):
            return Select(cond, choice1, choice2)
        if cond:
            return choice1
        else:
            return choice2

    def what(self, **kwargs):
        cond = self._condition(**kwargs)
        choice1 = self._choice1(**kwargs)
        choice2 = self._choice2(**kwargs)
        if isinstance(cond, Calculable):
            return f"if ({whatis(cond)}) then [{whatis(choice1)}] else [{whatis(choice2)}]"
        if cond:
            return whatis(choice1)
        else:
            return whatis(choice2)

    def how_to_bool(self, value=True):
        value = bool(value)
        cond = self._condition()
        choice1 = self._choice1()
        choice2 = self._choice2()

        conds = []
        if isinstance(cond, Calculable):
            conds = list(cond.how_to_bool(True))
        elif not cond:
            return

        if isinstance(choice1, Calculable):
            for args in choice1.how_to_bool(value):
                yield conds + args
        elif bool(choice1) == value:
            yield conds

        conds = []
        if isinstance(cond, Calculable):
            conds = list(cond.how_to_bool(False))
        elif cond:
            return
        if isinstance(choice2, Calculable):
            for args in choice2.how_to_bool(value):
                yield conds + args
        elif bool(choice2) == value:
            yield conds

    def ask(self, **kwargs):
        cond = self._condition(**kwargs)
        choice1 = self._choice1(**kwargs)
        choice2 = self._choice2(**kwargs)
        if not isinstance(choice1, Calculable) and not isinstance(choice2, Calculable):
            if choice1 == choice2:
                yield choice1
                return
        if isinstance(cond, Calculable):
            args = list(cond.how_to_bool(True))
            if isinstance(choice1, Calculable):
                for result in choice1.ask():
                    yield args + result
            else:
                yield args + [choice1]
            args = list(cond.how_to_bool(False))
            if isinstance(choice2, Calculable):
                for result in choice2.ask():
                    yield args + result
            else:
                yield args + [choice2]
            return
        if cond:
            if isinstance(choice1, Calculable):
                for result in choice1.ask():
                    yield result
            else:
                yield [choice1]
        else:
            if isinstance(choice2, Calculable):
                for result in choice2.ask():
                    yield result
            else:
                yield [choice2]


class And(Calculable):
    def __init__(self, condition, *conditions):
        self._conditions = [ensure_calculable(c) for c in ([condition] + conditions)]

        self._out_args = get_out_args(self._conditions)
        self._inner_args = {}

    def __call__(self, **kwargs):
        conditions = [cond(**kwargs) for cond in self._conditions]
        if not all(conditions):
            return False
        left_conditions = [cond for cond in conditions if isinstance(cond, Calculable)]
        if not left_conditions:
            return True
        return And(*left_conditions)

    def what(self, **kwargs):
        conditions = [cond(**kwargs) for cond in self._conditions]
        if not all(conditions):
            return False
        left_conditions = [cond for cond in conditions if isinstance(cond, Calculable)]
        if not left_conditions:
            return True
        return " and ".join([whatis(cond, **kwargs) for cond in left_conditions])

    def how_to_bool(self, value=True):
        value = bool(value)
        conditions = self._conditions
        result = []
        if value:
            for cond in conditions:
                result.append(list(cond.how_to_bool(True)))
            for args in itertools.product(*result):
                yield args
        else:
            for cond in conditions:
                for args in cond.how_to_bool(False):
                    yield args


class Or(Calculable):
    def __init__(self, condition, *conditions):
        self._conditions = [ensure_calculable(c) for c in ([condition] + conditions)]
        self._out_args = get_out_args(self._conditions)
        self._inner_args = {}

    def __call__(self, **kwargs):
        conditions = [cond(**kwargs) for cond in self._conditions]
        values = [cond for cond in conditions if not isinstance(cond, Calculable)]
        if any(values):
            return True
        left_conditions = [cond for cond in conditions if isinstance(cond, Calculable)]
        if not left_conditions:
            return False
        return Or(*left_conditions)

    def how_to_bool(self, value=True):
        value = bool(value)
        conditions = self._conditions
        result = []
        if not value:
            for cond in conditions:
                result.append(list(cond.how_to_bool(False)))
            for args in itertools.product(*result):
                yield args
        else:
            for cond in conditions:
                for args in cond.how_to_bool(True):
                    yield args


class Between(Calculable):
    def __init__(self, condition, min_value=None, max_value=None):
        self._condition = ensure_calculable(condition)
        self._min_value = ensure_calculable(min_value)
        self._max_value = ensure_calculable(max_value)

        self._out_args = get_out_args([self._condition, self._min_value, self._max_value])
        self._inner_args = {}

    def __call__(self, **kwargs):
        cond = self._condition(**kwargs)
        min_value = self._min_value(**kwargs)
        max_value = self._max_value(**kwargs)

        if isinstance(cond, Calculable):
            return Between(cond, min_value, max_value)
        if not isinstance(min_value, Calculable) and not isinstance(max_value, Calculable):
            return min_value < cond < max_value
        elif not isinstance(min_value, Calculable):
            if cond < min_value:
                return False
            else:
                return Between(cond, max_value=max_value)
        elif not isinstance(max_value, Calculable):
            if cond > max_value:
                return False
            else:
                return Between(cond, min_value=min_value)
        else:
            return Between(cond, min_value, max_value)

    def what(self, **kwargs):
        cond = self._condition(**kwargs)
        min_value = self._min_value(**kwargs)
        max_value = self._max_value(**kwargs)

        if isinstance(cond, Calculable):
            return f' {whatis(cond)} 在 ({min_value})~({max_value}) 范围内 '
        if not isinstance(min_value, Calculable) and not isinstance(max_value, Calculable):
            return f'{min_value < cond < max_value}'
        elif not isinstance(min_value, Calculable):
            if cond < min_value:
                return 'False'
            else:
                return f' {whatis(cond)} 小于 ({max_value}) '
        elif not isinstance(max_value, Calculable):
            if cond > max_value:
                return 'False'
            else:
                return f' {whatis(cond)} 大于 ({min_value}) '
        else:
            return f' {whatis(cond)} 在 ({min_value})~({max_value}) 范围内 '

    def ask(self, **kwargs):
        # todo:
        cond = self._condition(**kwargs)
        min_value = self._min_value(**kwargs)
        max_value = self._max_value(**kwargs)

        if isinstance(cond, Calculable):
            return Between(cond, min_value, max_value)
        if not isinstance(min_value, Calculable) and not isinstance(max_value, Calculable):
            return min_value < cond < max_value
        elif not isinstance(min_value, Calculable):
            if cond < min_value:
                return False
            else:
                return Between(cond, max_value=max_value)
        elif not isinstance(max_value, Calculable):
            if cond > max_value:
                return False
            else:
                return Between(cond, min_value=min_value)
        else:
            return Between(cond, min_value, max_value)

    def how_to_bool(self, value):
        value = bool(value)
        # cond = self._condition()
        # min_value = self._min_value()
        # max_value = self._max_value()

        if value:
            yield [self.what()]
        else:
            yield [f"not ({self.what()})"]
    # def what_of(self, key, **kwargs):
    #     if key in kwargs:
    #         return kwargs[key]
    #     cond = self._condition(**kwargs)
    #     min_value = self._min_value(**kwargs)
    #     max_value = self._max_value(**kwargs)
    #     if key not in getattr(cond, "_out_args", set()):
    #         return None
    #     if key in getattr(cond, "_out_args", set())\
    #             and key not in getattr(cond, "_out_args", set()) \
    #             and key not in getattr(cond, "_out_args", set()):
    #         return Const(Range(min_value, max_value))
    #     raise CannotAnswerError("cannot answer what of (%s), too complex!" % key)


