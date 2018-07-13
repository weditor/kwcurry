import inspect
import operator as op
import copy
from errors import NotSupportCalcError
# __all__ = ['whatis', 'ensure_calculable', 'get_out_args', "Calculable", "Const", "Variable", "Curry"]


def whatis(obj, **kwargs):
    if hasattr(obj, "what"):
        return obj.what(**kwargs)
    return obj


def maxof(obj, **kwargs):
    if hasattr(obj, "max"):
        return obj.max(**kwargs)
    return obj


class Range:
    def __init__(self, min_value, max_value):
        self._min_value = min_value
        self._max_value = max_value

    def __str__(self):
        return f'({self._min_value}, {self._max_value})'

    def __repr__(self):
        return f'({self._min_value}, {self._max_value})'

    def min(self, **kwargs):
        return self._min_value

    def max(self, **kwargs):
        return self._max_value


class Union:
    def __init__(self, values):
        self.values = values


class NotUnion:
    def __init__(self, values):
        self.values = values

class Answer:
    def __init__(self, results):
        self._conditions = results[: -1]
        self._result = results[-1]

    def value(self):
        return self._result

    def conditions(self):
        return self._conditions


def fmap(func, formula=None, flip=False, is_boolean=False, reverse_func=None):
    """
    映射内置二元计算函数为Function, 如 __add__,
    :param func:
    :param flip: 参数是否对调
    :return:
    """
    if not flip:
        def _applier(self, other):
            if not isinstance(other, Calculable):
                other = Const(other)
            new_func = WrapFunction(
                lambda a, b: func(a, b),
                formula.replace("self", "%(a)s").replace("other", '%(b)s'),
            )
            return Curry(Function(new_func, a=self, b=other, _is_boolean=is_boolean))
        return _applier
    else:
        def _applier(self, other):
            if not isinstance(other, Calculable):
                other = Const(other)
            new_func = WrapFunction(
                lambda a, b: func(a, b),
                formula.replace("self", "%{a}").replace("other", '%{b}'))
            return Curry(Function(new_func, a=self, b=other))
    return _applier


def unary_fmap(func, formula=None):
    """映射内置一元计算函数为Function, 如 取负数的函数 __neg__,"""
    def _applier(self):
        return Function(lambda a: func(a), a=self)
    return _applier


def get_out_args(callables):
    result = set()
    for c in callables:
        result |= getattr(c, "_out_args", set())
    return result


class Calculable(object):

    def __call__(self, **kwargs):
        raise NotImplementedError("please implement __call__ .")

    def _ensure_callable(self, f):
        return

    __add__ = fmap(op.add, "self + other")
    __mul__ = fmap(op.mul, "self * other")
    __sub__ = fmap(op.sub, "self - other")
    __mod__ = fmap(op.mod, "self %% other")
    __pow__ = fmap(op.pow, "self ** other")

    __and__ = fmap(op.and_, "self & other")
    __or__ = fmap(op.or_, "self | other")
    __xor__ = fmap(op.xor, "self ^ other")

    __div__ = fmap(op.truediv, "self / other")
    __divmod__ = fmap(divmod, "self / other")
    __floordiv__ = fmap(op.floordiv, "self // other")
    __truediv__ = fmap(op.truediv, "self / other")

    # __lshift__ = fmap(op.lshift, "self << other")
    # __rshift__ = fmap(op.rshift, "self >> other")

    __lt__ = fmap(op.lt, "self < other", is_boolean=True)
    __le__ = fmap(op.le, "self <= other", is_boolean=True)
    __gt__ = fmap(op.gt, "self > other", is_boolean=True)
    __ge__ = fmap(op.ge, "self >= other", is_boolean=True)
    __eq__ = fmap(op.eq, "self == other", is_boolean=True)
    __ne__ = fmap(op.ne, "self != other", is_boolean=True)

    __contains__ = fmap(op.contains, "other in self", True)

    __neg__ = unary_fmap(op.neg, "-self")
    __pos__ = unary_fmap(op.pos, "+self")
    __invert__ = unary_fmap(op.invert, "~self")

    __radd__ = fmap(op.add, "other + self", True)
    __rmul__ = fmap(op.mul, "other * self", True)
    __rsub__ = fmap(op.sub, "other - self", True)
    __rmod__ = fmap(op.mod, "other %% self", True)
    __rpow__ = fmap(op.pow, "other ** self", True)
    __rdiv__ = fmap(op.truediv, "other / self", True)
    __rdivmod__ = fmap(divmod, "other / self", True)
    __rtruediv__ = fmap(op.truediv, "other / self", True)
    __rfloordiv__ = fmap(op.floordiv, "other / self", True)

    __rlshift__ = fmap(op.lshift, "other << self", True)
    __rrshift__ = fmap(op.rshift, "other >> self", True)

    __rand__ = fmap(op.and_, "other & self", True)
    __ror__ = fmap(op.or_, "other | self", True)
    __rxor__ = fmap(op.xor, "other ^ self", True)


class Const(Calculable):
    """常量"""
    _out_args = set()

    def __init__(self, value):
        self._value = value

    def __call__(self, **kwargs):
        return self._value

    def what(self, **kwargs):
        return self._value

    def what_of(self, key, **kwargs):
        if key in kwargs:
            return kwargs[key]

    def ask(self):
        yield [self._value]


class Variable(Calculable):
    """变量, 带有一个名称"""
    def __init__(self, name=None):
        self._name = name
        self._out_args = {name}

    def __call__(self, **kwargs):
        return kwargs[self._name]

    def what(self, **kwargs):
        if self._name in kwargs:
            return kwargs[self._name]
        else:
            return '{%s}' % self._name

    def how_to(self, value=True):
        return


class WrapFunction(Calculable):
    def __init__(self, func, formula=None, out_args=None, is_boolean=False):
        # super(WrapFunction, self).__init__(func)
        self._is_boolean = is_boolean
        self._formula = formula or "_"
        self._func = func
        self._out_args = out_args
        if out_args is None:
            self._out_args = set(inspect.signature(func).parameters.keys())
        self. _inner_args = {}

    def __call__(self, **kwargs):
        kwargs = self._get_args(**kwargs)
        if self._out_args - set(kwargs.keys()):
            raise Exception("arg not match reqire (%s), bug get (%s)" % (self._out_args, kwargs))
        return self._func(**kwargs)

    def what(self, **kwargs):
        return self._formula % kwargs

    def _get_args(self, **kwargs):
        kw = {}
        for k, v in kwargs.items():
            if k not in self._out_args:
                continue
            kw[k] = v
        return kw

    def how_to_bool(self, value):
        # todo:
        value = bool(value)
        if not self._is_boolean:
            raise NotSupportCalcError(self.__class__.__name__, 'how_to_bool')
        if value:
            yield self.what()
        else:
            yield f"not ({self.what()})"


class Function(Calculable):
    """
    用于包装一个Function/WrapFunction,
    其中kwargs是这个函数的参数, 参数也是Calculable
    """
    def __init__(self, func, _is_boolean=False, **kwargs):
        # super(Function, self).__init__(func, out_args=set())

        self._is_boolean = _is_boolean

        if not isinstance(func, Calculable):
            self._func = WrapFunction(func)
        else:
            self._func = func
        self._inner_args = kwargs
        all_args = copy.copy(getattr(func, '_out_args', set()))
        for k, v in kwargs.items():
            all_args |= getattr(v, '_out_args', set())
        self._out_args = all_args - set(self._inner_args.keys())

    def __call__(self, **kwargs):
        kwargs = self._get_args(**kwargs)
        if self._out_args - set(kwargs.keys()):
            raise Exception("arg not match reqire (%s), bug get (%s)" % (self._out_args, kwargs))
        inner_args = {k: v(**kwargs) if callable(v) else v for k, v in self._inner_args.items()}
        return self._func(**inner_args)

    def what(self, **kwargs):
        kwargs = self._get_args(**kwargs)
        inner_args = {k: v.what(**kwargs) if isinstance(v, Calculable) else v for k, v in self._inner_args.items()}
        return self._func.what(**inner_args)

    def _get_args(self, **kwargs):
        kw = {}
        for k, v in kwargs.items():
            if k not in self._out_args:
                continue
            kw[k] = v
        return kw

    def how_to_bool(self, value, **kwargs):
        kwargs = self._get_args(**kwargs)
        inner_args = {k: v.what(**kwargs) if isinstance(v, Calculable) else v for k, v in self._inner_args.items()}
        return self._func.what(**inner_args)

        if not self._is_boolean:
            raise NotSupportCalcError(self.__class__.__name__, 'how_to_bool')
        if value:
            yield self.what()
        else:
            yield f"not ({self.what()})"

    # def ask(self, **kwargs):
    #     is isinstance(self._func, WrapFunction)

class Curry(Calculable):
    """可以将一个kwargs参数的函数进行科里化"""
    def __init__(self, func, **kwargs):
        """kwargs是科里化的值。"""
        self._func = func

        # 调用内部函数(self._func)时，加的额外参数。
        self._inner_args = kwargs
        # 封装后的函数出参
        self._out_args = set()
        if isinstance(func, (Calculable, )):
            self._out_args = set(func._out_args) - set(self._inner_args.keys())

    def _get_args(self, **kwargs):
        kw = {}
        for k, v in kwargs.items():
            if k not in self._out_args:
                continue
            kw[k] = v
        return kw

    def _call_func(self, func, **kwargs):
        return func(**kwargs, **self._inner_args)

    def __call__(self, **kwargs):
        kwargs = self._get_args(**kwargs)
        if len(kwargs) != len(self._out_args):
            if not kwargs:
                return self
            return Curry(func=self, **kwargs)

        if not isinstance(self._func, tuple):
            return self._call_func(self._func, **kwargs)

    def what(self, **kwargs):
        return self._func.what(**kwargs, **self._inner_args)

    def how_to_bool(self, value):
        return self._func.how_to_bool(bool(value))

    def ask(self, **kwargs):
        return self._func.ask(**kwargs)


def ensure_calculable(obj):
    if not callable(obj):
        return Const(obj)
    if not isinstance(obj, Calculable):
        return WrapFunction(obj)
    if not isinstance(obj, Curry) and not isinstance(obj, Const):
        return Curry(obj)
    return obj


if __name__ == '__main__':

    # f = Function(lambda a, b: op.add(a, b), a=Const(9), b=Variable('x'))
    # print(f(x=8))

    # f = (Variable('x') + Const(9))*Variable("y")

    # f = (Variable("x") + 9) * Variable('y')
    # f = f(y=2)
    # g = f/Variable("y")
    #
    # print(f)
    # print(f(x=-2))
    # print(g(x=-2, y=3))

    print(Range(6,7))
