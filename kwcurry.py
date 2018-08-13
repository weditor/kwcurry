# -*- encoding: utf-8 -*-

from __future__ import print_function, absolute_import, unicode_literals
import copy
import operator as op
import inspect


def _ensure_callable(obj):
    if isinstance(obj, KwCalc):
        return obj
    if callable(obj):
        return SimpleFunc(obj)
    return Const(obj)


def fmap(func, formular, reverse=False):
    def apply(self, other):
        if reverse:
            return KwFunc(lambda a, b: func(b, a), self, other)
        else:
            return KwFunc(func, self, other)
    return apply


def check_kwargs(func):
    def _func(self, **kwargs):
        useless = set(kwargs.keys()) - self._out_keywords
        if useless:
            raise TypeError("Unexpected keyword %s" % useless)
        if not kwargs and self._out_keywords:
            return self
        if self._out_keywords - set(kwargs.keys()):
            return KwCurry(self, **kwargs)
        kw = copy.copy(self._kwargs)
        kw.update(kwargs)
        return func(self, **kw)
    return _func


class KwCalc(object):
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

    __lt__ = fmap(op.lt, "self < other")
    __le__ = fmap(op.le, "self <= other")
    __gt__ = fmap(op.gt, "self > other")
    __ge__ = fmap(op.ge, "self >= other")
    __eq__ = fmap(op.eq, "self == other")
    __ne__ = fmap(op.ne, "self != other")

    __contains__ = fmap(op.contains, "other in self", True)

    # __neg__ = unary_fmap(op.neg, "-self")
    # __pos__ = unary_fmap(op.pos, "+self")
    # __invert__ = unary_fmap(op.invert, "~self")

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

    def _call_func(self, func, **kwargs):
        kw = {k: v for k, v in kwargs.items() if k in func._out_keywords}
        return func(**kw)


class KwFunc(KwCalc):

    def __init__(self, func, left, right, **kwargs):
        self._func = func
        self._left = _ensure_callable(left)
        self._right = _ensure_callable(right)
        self._kwargs = kwargs
        self._out_keywords = set(self._left._out_keywords) | set(self._right._out_keywords) - set(self._kwargs.keys())

    @check_kwargs
    def __call__(self, *args, **kwargs):
        left = self._call_func(self._left, **kwargs)
        right = self._call_func(self._right, **kwargs)
        return self._func(left, right)


class SimpleFunc(KwCalc):
    def __init__(self, func, **kwargs):
        self._func = func
        self._kwargs = kwargs
        all_args = set(inspect.signature(func).parameters.keys())

        useless_kwargs = set(kwargs.keys()) - set(all_args)
        if useless_kwargs:
            raise TypeError("{func} got unexpected keyword argument {args}".format(
                func=self._func, args=useless_kwargs))

        self._out_keywords = set(all_args) - set(kwargs.keys())
        self._kwargs = kwargs

    @check_kwargs
    def __call__(self, *args, **kwargs):
        kw = copy.copy(self._kwargs)
        kw.update(kwargs)
        return self._func(**kw)


class Const(KwCalc):
    def __init__(self, value):
        self._value = value
        self._out_keywords = set()
        self._kwargs = {}

    @check_kwargs
    def __call__(self, **kwargs):
        return self._value


class Variable(KwCalc):
    def __init__(self, name):
        self._name = name
        self._out_keywords = {self._name}
        self._kwargs = {}

    @check_kwargs
    def __call__(self, **kwargs):
        return kwargs[self._name]


# todo: add determine **kwargs,
# todo: add functools
# todo: execute part of functions when kwargs is enough
class KwCurry(KwCalc):
    def __init__(self, func, **kwargs):
        self._func = _ensure_callable(func)
        self._kwargs = kwargs
        self._out_keywords = self._func._out_keywords - set(kwargs.keys())

    @check_kwargs
    def __call__(self, **kwargs):
        kw = copy.copy(kwargs)
        kw.update(self._kwargs)
        return self._call_func(self._func, **kw)


def kwcurry(func):
    return KwCurry(func)


if __name__ == '__main__':
    @kwcurry
    def add(a, b):
        return a + b

    f = Variable('a') + Variable('b') + 10 - Variable('b')/2
    print(f(a=9, b=8))
    f1 = f(b=8)
    print(f1(a=9))
    print(f1(a=10))

    F = add
    print(F(a=9)(b=8))
    print(F(a=9)(b=8, c=8))
