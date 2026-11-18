import unittest
from decimal import Decimal

from hyprtk_calc.evaluator import Context, evaluate, tokenize
from hyprtk_calc.number import CalcError


def run(text, **kwargs):
    return evaluate(text, Context(**kwargs))


class Arithmetic(unittest.TestCase):
    def test_precedence(self):
        self.assertEqual(run("1+2*3"), Decimal(7))
        self.assertEqual(run("(1+2)*3"), Decimal(9))
        self.assertEqual(run("8/4/2"), Decimal(1))

    def test_exact_decimal(self):
        # The whole reason for Decimal: 0.1 + 0.2 is 0.3, not 0.30000000000000004
        self.assertEqual(run("0.1+0.2"), Decimal("0.3"))
        self.assertEqual(run("1.1*3"), Decimal("3.3"))

    def test_power_is_right_associative(self):
        self.assertEqual(run("2^3^2"), Decimal(512))

    def test_unary_binds_looser_than_power(self):
        self.assertEqual(run("-2^2"), Decimal(-4))
        self.assertEqual(run("(-2)^2"), Decimal(4))

    def test_factorial(self):
        self.assertEqual(run("5!"), Decimal(120))
        self.assertEqual(run("-3!"), Decimal(-6))
        self.assertEqual(run("3!!"), Decimal(720))  # (3!)! = 6!

    def test_percent_is_a_unit(self):
        self.assertEqual(run("50%"), Decimal("0.5"))
        self.assertEqual(run("50*10%"), Decimal(5))

    def test_implicit_multiplication(self):
        self.assertEqual(run("2pi", precision=12), Decimal("6.28318530718"))
        self.assertEqual(run("3(4+5)"), Decimal(27))
        self.assertEqual(run("(2)(3)"), Decimal(6))
        self.assertEqual(run("2 sin(30)", angle="deg"), Decimal(1))

    def test_typed_operators(self):
        self.assertEqual(run("6 ÷ 3 × 2 − 1"), Decimal(3))
        self.assertEqual(run("2 · 3"), Decimal(6))

    def test_nested_and_long(self):
        self.assertEqual(run("((((1+2))))"), Decimal(3))
        self.assertEqual(run("+".join(["1"] * 200)), Decimal(200))


class Functions(unittest.TestCase):
    def test_trig_follows_the_angle_unit(self):
        self.assertEqual(run("sin(30)", angle="deg"), Decimal("0.5"))
        self.assertEqual(run("cos(0)", angle="rad"), Decimal(1))
        self.assertEqual(run("tan(50)", angle="grad"), Decimal(1))

    def test_inverse_trig_returns_the_chosen_unit(self):
        self.assertEqual(run("asin(1)", angle="deg"), Decimal(90))
        self.assertEqual(run("asin(1)", angle="rad", precision=12), Decimal("1.57079632679"))

    def test_logs(self):
        self.assertEqual(run("log(100)"), Decimal(2))
        self.assertEqual(run("log(8,2)"), Decimal(3))
        self.assertEqual(run("ln(e)"), Decimal(1))
        self.assertEqual(run("log2(1024)"), Decimal(10))

    def test_roots(self):
        self.assertEqual(run("sqrt(9)"), Decimal(3))
        self.assertEqual(run("cbrt(27)"), Decimal(3))
        self.assertEqual(run("root(16,4)"), Decimal(2))

    def test_bare_argument_calls(self):
        self.assertEqual(run("sqrt 9"), Decimal(3))
        self.assertEqual(run("sin 30", angle="deg"), Decimal("0.5"))
        self.assertEqual(run("√9"), Decimal(3))

    def test_rounding_functions(self):
        self.assertEqual(run("round(2.5)"), Decimal(2))  # banker's rounding
        self.assertEqual(run("round(3.5)"), Decimal(4))
        self.assertEqual(run("round(1.2345,2)"), Decimal("1.23"))
        self.assertEqual(run("floor(-1.5)"), Decimal(-2))
        self.assertEqual(run("ceil(-1.5)"), Decimal(-1))

    def test_combinatorics(self):
        self.assertEqual(run("ncr(5,2)"), Decimal(10))
        self.assertEqual(run("npr(5,2)"), Decimal(20))
        self.assertEqual(run("gcd(12,18)"), Decimal(6))
        self.assertEqual(run("lcm(4,6)"), Decimal(12))

    def test_min_max_abs_sign(self):
        self.assertEqual(run("max(1,7,3)"), Decimal(7))
        self.assertEqual(run("min(1,7,3)"), Decimal(1))
        self.assertEqual(run("abs(-4)"), Decimal(4))
        self.assertEqual(run("sign(-4)"), Decimal(-1))


class Bits(unittest.TestCase):
    def test_literals(self):
        self.assertEqual(run("0xff"), Decimal(255))
        self.assertEqual(run("0b1010"), Decimal(10))
        self.assertEqual(run("0o17"), Decimal(15))
        self.assertEqual(run("1_000_000"), Decimal(1000000))

    def test_operators(self):
        self.assertEqual(run("5 & 3"), Decimal(1))
        self.assertEqual(run("5 | 2"), Decimal(7))
        self.assertEqual(run("5 xor 3"), Decimal(6))
        self.assertEqual(run("~5"), Decimal(-6))
        self.assertEqual(run("1 << 10"), Decimal(1024))
        self.assertEqual(run("1024 >> 4"), Decimal(64))

    def test_operator_word_is_not_a_variable(self):
        # `xor` must not be swallowed by implicit multiplication
        self.assertEqual(run("5 xor 3 + 1"), Decimal(1))

    def test_bitwise_needs_integers(self):
        with self.assertRaises(CalcError):
            run("5 & 1.5")


class ContextAndNames(unittest.TestCase):
    def test_ans(self):
        context = Context(precision=12)
        context.ans = Decimal(41)
        self.assertEqual(evaluate("ans+1", context), Decimal(42))

    def test_variables(self):
        context = Context(precision=12, variables={"x": Decimal(6)})
        self.assertEqual(evaluate("2x", context), Decimal(12))

    def test_constants(self):
        self.assertEqual(run("pi", precision=5), Decimal("3.1416"))
        self.assertEqual(run("tau", precision=5), Decimal("6.2832"))
        self.assertEqual(run("e", precision=5), Decimal("2.7183"))

    def test_unknown_name(self):
        with self.assertRaises(CalcError) as caught:
            run("nope + 1")
        self.assertIn("not defined", str(caught.exception))


class Errors(unittest.TestCase):
    def check(self, text, fragment):
        with self.assertRaises(CalcError) as caught:
            run(text)
        self.assertIn(fragment, str(caught.exception))

    def test_messages(self):
        self.check("1/0", "division by zero")
        self.check("2+", "ends too early")
        self.check("(1+2", "expected ')'")
        self.check("1)", "unexpected ')'")
        self.check("sqrt(-1)", "not real")
        self.check("foo(2)", "not a function")
        self.check("fact(-1)", "whole numbers")
        self.check("0x", "base prefix")
        self.check("1..2", "unexpected '.'")
        self.check("", "nothing to calculate")
        self.check("   ", "nothing to calculate")
        self.check("5 $ 3", "unexpected character")

    def test_deep_nesting_is_contained(self):
        with self.assertRaises(CalcError):
            run("(" * 900 + "1" + ")" * 900)


class Tokenizer(unittest.TestCase):
    def test_kinds(self):
        kinds = [token.kind for token in tokenize("1 + sin(2)")]
        self.assertEqual(kinds, ["num", "op", "name", "lparen", "num", "rparen"])

    def test_double_star_is_power(self):
        self.assertEqual(run("2**10"), Decimal(1024))


class Precision(unittest.TestCase):
    def test_display_precision(self):
        self.assertEqual(run("1/3", precision=6), Decimal("0.333333"))
        self.assertEqual(run("1/3", precision=20), Decimal("0.33333333333333333333"))

    def test_float_functions_are_cleaned_by_the_display_rounding(self):
        # math.sin(math.radians(30)) is 0.49999999999999994
        self.assertEqual(run("sin(30)", precision=12, angle="deg"), Decimal("0.5"))
        self.assertEqual(str(run("sqrt(2)", precision=12)), "1.41421356237")


if __name__ == "__main__":
    unittest.main()
