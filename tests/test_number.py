import unittest
from decimal import Decimal

from hyprtk_calc.number import (
    CalcError,
    MAX_PRECISION,
    all_bases,
    clamp_precision,
    format_base,
    format_number,
    integral,
    parse_literal,
    round_to,
    work_precision,
)


class Literals(unittest.TestCase):
    def test_decimal_is_exact(self):
        self.assertEqual(parse_literal("0.1"), Decimal("0.1"))
        self.assertEqual(str(parse_literal("1.10")), "1.10")
        self.assertEqual(parse_literal("1e-3"), Decimal("0.001"))

    def test_bases(self):
        self.assertEqual(parse_literal("0x1f"), Decimal(31))
        self.assertEqual(parse_literal("0b1010"), Decimal(10))
        self.assertEqual(parse_literal("0o17"), Decimal(15))

    def test_underscores(self):
        self.assertEqual(parse_literal("1_000"), Decimal(1000))


class Formatting(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(format_number(Decimal(7), 12), "7")
        self.assertEqual(format_number(Decimal("0.5"), 12), "0.5")
        self.assertEqual(format_number(Decimal("1.2300"), 12), "1.23")
        self.assertEqual(format_number(Decimal("-0"), 12), "0")

    def test_precision(self):
        self.assertEqual(format_number(Decimal("0.3333333333333"), 6), "0.333333")
        self.assertEqual(format_number(Decimal("2.5"), 1), "2")   # half to even
        self.assertEqual(format_number(Decimal("3.5"), 1), "4")

    def test_grouping(self):
        value = Decimal("1234567.891")
        self.assertEqual(format_number(value, 12), "1234567.891")
        self.assertEqual(format_number(value, 12, grouping="thin"), "1\u2009234\u2009567.891")
        self.assertEqual(format_number(value, 12, grouping="comma"), "1,234,567.891")
        self.assertEqual(format_number(Decimal("-1234"), 12, grouping="comma"), "-1,234")

    def test_scientific_outside_the_plain_range(self):
        self.assertEqual(format_number(Decimal("1.2345e15"), 5), "1.2345e+15")
        self.assertEqual(format_number(Decimal("1e-12"), 12), "1e-12")
        self.assertEqual(format_number(Decimal("9.99e12"), 3), "9.99e+12")
        self.assertEqual(format_number(Decimal("9.99e11"), 3), "999000000000")

    def test_special_values(self):
        self.assertEqual(format_number(Decimal("Infinity")), "∞")
        self.assertEqual(format_number(Decimal("-Infinity")), "-∞")
        self.assertEqual(format_number(Decimal("NaN")), "not a number")

    def test_bases(self):
        self.assertEqual(format_base(Decimal(255), 16), "0xFF")
        self.assertEqual(format_base(Decimal(255), 2), "0b11111111")
        self.assertEqual(format_base(Decimal(255), 8), "0o377")
        self.assertEqual(format_base(Decimal(-31), 16), "-0x1F")
        self.assertEqual(format_base(Decimal(255), 2, grouping="thin"), "0b1111 1111")

    def test_fractional_value_in_another_base(self):
        with self.assertRaises(CalcError):
            format_base(Decimal("1.5"), 16)

    def test_all_bases(self):
        bases = all_bases(Decimal(255))
        self.assertEqual(bases[16], "0xFF")
        self.assertEqual(bases[10], "255")
        self.assertEqual(bases[8], "0o377")
        self.assertEqual(bases[2], "0b11111111")
        self.assertEqual(all_bases(Decimal("1.5"))[16], "—")


class Precision(unittest.TestCase):
    def test_clamp(self):
        self.assertEqual(clamp_precision(1), 3)
        self.assertEqual(clamp_precision(999), MAX_PRECISION)
        self.assertEqual(clamp_precision("12"), 12)
        self.assertEqual(clamp_precision(None), 12)

    def test_work_precision_has_guard_digits(self):
        self.assertGreater(work_precision(12), 12)
        self.assertLessEqual(work_precision(MAX_PRECISION), MAX_PRECISION + 12)

    def test_round_to(self):
        self.assertEqual(round_to(Decimal("1.23456"), 3), Decimal("1.23"))
        self.assertEqual(round_to(Decimal("9.999"), 1), Decimal("10"))


class Integers(unittest.TestCase):
    def test_integral(self):
        self.assertEqual(integral(Decimal("12.000")), 12)
        self.assertEqual(integral(Decimal(-3)), -3)

    def test_not_integral(self):
        with self.assertRaises(CalcError):
            integral(Decimal("1.2"))
        with self.assertRaises(CalcError):
            integral(Decimal("Infinity"))


if __name__ == "__main__":
    unittest.main()
