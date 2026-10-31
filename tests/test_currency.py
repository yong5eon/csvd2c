# -*- coding: utf-8 -*-

from unittest import (
	TestCase,
	main,
)
from csvd2c.column import (
	Error,
	Validator,
)
from csvd2c.column.patterns import (
	CURRENCY_ALIASES,
	CURRENCY_CODES,
	Currency,
	Strip,
)


class Recover(Error):
	def __init__(self) -> None:
		self.values: list[str] = []
		return

	def __call__(self, col: str) -> str:
		self.values.append(col)
		return 'recovered'


class Fail(Error):
	def __call__(self, col: str) -> str:
		raise RuntimeError('Handler failure')


class CurrencyTests(TestCase):
	"""
	Verify ISO codes, prefix policies, explicit damage recovery, and preservation.
	"""

	def test_symbols_and_country_prefixes(self) -> None:
		for prefix, code in (
			('₩', 'KRW'),
			('￦', 'KRW'),
			('$', 'USD'),
			('＄', 'USD'),
			('CA$', 'CAD'),
			('AU$', 'AUD'),
			('US$', 'USD'),
			('NZ$', 'NZD'),
			('HK$', 'HKD'),
			('SG$', 'SGD'),
			('¥', 'JPY'),
			('￥', 'JPY'),
			('JP¥', 'JPY'),
			('CN¥', 'CNY'),
			('JP￥', 'JPY'),
			('CN￥', 'CNY'),
			('CA＄', 'CAD'),
			('AU＄', 'AUD'),
			('€', 'EUR'),
			('£', 'GBP'),
			('￡', 'GBP'),
			('₹', 'INR'),
			('₽', 'RUB'),
		):
			with self.subTest(prefix=prefix):
				self.assertEqual(Currency()(prefix + '1,000'), code + ' 1,000')
		return

	def test_entire_code_snapshot(self) -> None:
		self.assertEqual(len(Currency.codes), 178)
		for code in Currency.codes:
			self.assertEqual(Currency()(code + ' 1,000.00'), code + ' 1,000.00')
		for code in ('BGN', 'HRK', 'ZZZ'):
			with self.assertRaises(ValueError):
				Currency()(code + ' 100')
		return

	def test_constant_mappings_and_all_aliases(self) -> None:
		self.assertEqual(len(CURRENCY_CODES), 178)
		pattern = Currency()
		for code in CURRENCY_CODES:
			self.assertEqual(CURRENCY_ALIASES[code], code)
		for alias, code in CURRENCY_ALIASES.items():
			with self.subTest(alias=alias):
				self.assertIn(code, CURRENCY_CODES)
				self.assertEqual(pattern(alias + ' 1,000'), code + ' 1,000')
		return

	def test_readonly_constants_and_instance_overrides(self) -> None:
		with self.assertRaises(TypeError):
			CURRENCY_ALIASES['$'] = 'CAD'  # type: ignore[index]
		custom = Currency({'$': 'CAD'})
		self.assertEqual(custom('$100'), 'CAD 100')
		self.assertEqual(Currency()('$100'), 'USD 100')
		self.assertEqual(CURRENCY_ALIASES['$'], 'USD')
		return

	def test_local_names_and_shared_aliases(self) -> None:
		for alias, code in (
			('US Dollar', 'USD'),
			('Australian Dollar', 'AUD'),
			('미국 달러', 'USD'),
			('日本円', 'JPY'),
			('人民币', 'CNY'),
		):
			self.assertEqual(Currency()(alias + ' 100'), code + ' 100')
		for alias in ('kr', 'Rs'):
			self.assertNotIn(alias, CURRENCY_ALIASES)
		return

	def test_damage_with_country_prefix(self) -> None:
		for country, code in (
			('CA', 'CAD'),
			('AU', 'AUD'),
			('JP', 'JPY'),
			('CN', 'CNY'),
		):
			for marker in (
				'\ufffd',
				'\udc80',
				'\udcff',
				'\ufffd\udcff',
			):
				self.assertEqual(Currency()(country + marker + '1,000'), code + ' 1,000')
		return

	def test_preserves_amount_formatting(self) -> None:
		for amount in (
			'1,000.00',
			'-1.000,50',
			'(1 000)',
			'+12',
			'1  000',
		):
			self.assertEqual(Currency()('  KRW \t' + amount + ' \n'), 'KRW ' + amount)
		# Numerical validity is explicitly outside this Pattern's responsibility.
		self.assertEqual(Currency()('USD 1,23'), 'USD 1,23')
		return

	def test_rejects_unknown_and_unrecoverable_values(self) -> None:
		for value in (
			'',
			'1,000',
			'$',
			'CA?1,000',
			'CA1,000',
			'\ufffd1,000',
			'ZZ\ufffd1,000',
			'CA\ufffd$1,000',
			'USDollars100',
			'USD NaN',
			'USD 1\ufffd00',
			'$1\udcff00',
			'usd 100',
		):
			with self.assertRaises(ValueError):
				Currency()(value)
		return

	def test_custom_mapping_and_copy(self) -> None:
		mapping = {'C$': 'CAD', '$': 'AUD', 'odd': 'EUR', 'US dollars': 'USD'}
		pattern = Currency(mapping)
		mapping['C$'] = 'USD'
		self.assertEqual(pattern('C$100'), 'CAD 100')
		self.assertEqual(pattern('$100'), 'AUD 100')
		self.assertEqual(pattern('odd100'), 'EUR 100')
		self.assertEqual(pattern('US dollars 100'), 'USD 100')
		self.assertEqual(pattern('USD 100'), 'USD 100')
		return

	def test_configuration_and_handlers(self) -> None:
		handler = Recover()
		for mapping in (
			{'': 'USD'},
			{' $': 'USD'},
			{'$': 'ZZZ'},
			{'USD': 'AUD'},
			{'$': 1},
		):
			with self.assertRaises(ValueError):
				Currency(mapping, error=handler)
		self.assertEqual(handler.values, [])
		with self.assertRaises(TypeError):
			Currency(error='invalid')
		self.assertEqual(Currency(error=handler)('  bad '), 'recovered')
		self.assertEqual(handler.values, ['  bad '])
		self.assertEqual(Currency(error=handler)('$100'), 'USD 100')
		self.assertEqual(len(handler.values), 1)
		with self.assertRaisesRegex(RuntimeError, 'Handler failure'):
			Currency(error=Fail())('bad')
		return

	def test_validator_composition(self) -> None:
		self.assertEqual(Validator(Strip(), Currency())('  CA$1,000  '), 'CAD 1,000')
		return


if __name__ == '__main__':
	main()
