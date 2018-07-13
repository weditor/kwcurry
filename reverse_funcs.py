
import sympy


x = sympy.symbols('x')

f = (x + 1)**2

ret = sympy.solve(f, x)
print(ret)


