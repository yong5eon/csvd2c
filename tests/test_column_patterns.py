# -*- coding: utf-8 -*-

from decimal import Decimal
from locale import (
	LC_TIME,
	setlocale,
)
from pathlib import Path
from re import (
	error as RegexError,
	IGNORECASE,
)
from tempfile import TemporaryDirectory
from unittest import (
	TestCase,
	main,
)
from csvd2c import CSV
from csvd2c.column import (
	Error,
	Validator,
)
from csvd2c.column.patterns import (
	CaseFold,
	Choices,
	CollapseWhitespace,
	Date,
	Default,
	IfEmpty,
	IfMatch,
	Length,
	Lower,
	Map,
	Number,
	Range,
	Recode,
	Regex,
	RegexReplace,
	RejectCharacters,
	RejectReplacementCharacter,
	RejectSurrogates,
	Replace,
	Required,
	Strip,
	UnicodeNormalize,
	Upper,
)


class Recover(Error):
	"""
	Record the rejected value and return an explicit replacement.
	"""

	def __init__(self) -> None:
		self.values: list[str] = []
		return

	def __call__(self, col: str) -> str:
		self.values.append(col)
		return 'recovered'


class Fail(Error):
	def __call__(self, col: str) -> str:
		raise RuntimeError('Handler failure')


class ColumnPatternTests(TestCase):
	"""
	Verify string transformations, strict validation, and handler boundaries.
	"""

	def test_string_transformations(self) -> None:
		self.assertEqual(Strip()('\t 이름 \n'), '이름')
		self.assertEqual(Strip('_')('__abc__'), 'abc')
		self.assertEqual(CollapseWhitespace()(' \ta\n\nb '), ' a b ')
		self.assertEqual(Replace('x', 'y', 1)('xx'), 'yx')
		self.assertEqual(Replace('', '-')('a'), '-a-')
		self.assertEqual(RegexReplace(r'([0-9]+)', r'[\1]')('a12b3'), 'a[12]b[3]')
		self.assertEqual(RegexReplace('a', 'b', count=1, flags=IGNORECASE)('Aa'), 'ba')
		self.assertEqual(Lower()('ABC'), 'abc')
		self.assertEqual(Upper()('abc'), 'ABC')
		self.assertEqual(CaseFold()('Straße'), 'strasse')
		self.assertEqual(UnicodeNormalize()('e\u0301'), 'é')
		self.assertEqual(UnicodeNormalize('NFKC')('１２３'), '123')
		self.assertEqual(Default('missing')(''), 'missing')
		self.assertEqual(Default('missing')(' '), ' ')
		return

	def test_required_length_regex_choices(self) -> None:
		self.assertEqual(Required()(' '), ' ')
		with self.assertRaises(ValueError):
			Required()('')
		for value in ('a', 'ab'):
			self.assertEqual(Length(1, 2)(value), value)
		for value in ('', 'abc'):
			with self.assertRaises(ValueError):
				Length(1, 2)(value)
		self.assertEqual(Length(1, 1)('한'), '한')
		self.assertEqual(Regex(r'[0-9]+')('123'), '123')
		with self.assertRaises(ValueError):
			Regex(r'[0-9]+')('a123')
		self.assertEqual(Regex('yes', flags=IGNORECASE)('YES'), 'YES')
		self.assertEqual(Choices('예', '아니오')('예'), '예')
		with self.assertRaises(ValueError):
			Choices('Y')('y')
		with self.assertRaises(ValueError):
			Choices()('')
		return

	def test_damage_checks(self) -> None:
		with self.assertRaises(ValueError):
			RejectCharacters('\x00?')('a?')
		self.assertEqual(RejectCharacters('')('?'), '?')
		for char in (
			'\ud800',
			'\udc80',
			'\udcff',
			'\udfff',
		):
			with self.assertRaises(ValueError):
				RejectSurrogates()('a' + char)
		for value in ('한글😀', '\ud7ff', '\ue000', '?'):
			self.assertEqual(RejectSurrogates()(value), value)
		with self.assertRaises(ValueError):
			RejectReplacementCharacter()('a\ufffdb')
		self.assertEqual(RejectReplacementCharacter()('?'), '?')
		return

	def test_map_copies_configuration(self) -> None:
		mapping = {'예': 'Y', '': ''}
		pattern = Map(mapping)
		mapping['예'] = 'changed'
		self.assertEqual(pattern('예'), 'Y')
		self.assertEqual(pattern(''), '')
		with self.assertRaises(ValueError):
			pattern('unknown')
		return

	def test_dates_and_ambiguity(self) -> None:
		pattern = Date('%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%d')
		self.assertEqual(pattern('2024-02-29'), '2024-02-29')
		self.assertEqual(pattern('29/02/2024'), '2024-02-29')
		self.assertEqual(Date('%Y-%m-%d', output='%d/%m/%Y')('2024-02-29'), '29/02/2024')
		for value in ('2023-02-29', '2024-13-01', '1-10', 'Feb-23'):
			with self.assertRaises(ValueError):
				pattern(value)
		ambiguous = Date('%d/%m/%Y', '%m/%d/%Y')
		with self.assertRaisesRegex(ValueError, 'multiple'):
			ambiguous('01/02/2024')
		self.assertEqual(ambiguous('02/02/2024'), '2024-02-02')
		return

	def test_date_month_names_use_locale(self) -> None:
		previous: str = setlocale(LC_TIME)
		try:
			setlocale(LC_TIME, 'C')
			pattern = Date('%d-%b-%Y', '%d %B %Y')
			self.assertEqual(pattern('23-Feb-2024'), '2024-02-23')
			self.assertEqual(pattern('23 February 2024'), '2024-02-23')
		finally:
			setlocale(LC_TIME, previous)
		return

	def test_numbers(self) -> None:
		for value, expected in (
			('00123.4500', '123.45'),
			('-0.000', '0'),
			('+123', '123'),
			('1000', '1000'),
			('0.00000000000000000001', '0.00000000000000000001'),
			('123456789012345678901234567890.123456789', '123456789012345678901234567890.123456789'),
		):
			self.assertEqual(Number()(value), expected)
		self.assertEqual(Number(thousands=',')('1,234,567.8900'), '1234567.89')
		self.assertEqual(Number(decimal=',', thousands='.')('-1.234,50'), '-1234.5')
		self.assertEqual(Number(thousands=' ')('1 234.00'), '1234')
		for value in (
			'',
			' 123',
			'123 ',
			'.5',
			'1.',
			'NaN',
			'Infinity',
			'1e3',
			'１２３',
			'1,23',
			'1234,567',
			'1,,234',
			'1.2,345',
		):
			with self.assertRaises(ValueError):
				Number(thousands=',')(value)
		return

	def test_numeric_ranges(self) -> None:
		pattern = Range('1.5', Decimal('2.5'))
		for value in ('1.5', '2', '2.500'):
			self.assertEqual(pattern(value), value)
		for value in ('1.49', '2.51', 'NaN', 'abc', '1,000'):
			with self.assertRaises(ValueError):
				pattern(value)
		self.assertEqual(Range(maximum=0)('-100'), '-100')
		self.assertEqual(Range(minimum=0)('0'), '0')
		return

	def test_recode_known_path(self) -> None:
		original = '홍길동 café'
		corrupt: str = original.encode('utf-8').decode('latin-1')
		self.assertEqual(Recode('latin-1', 'utf-8')(corrupt), original)
		with self.assertRaises(ValueError):
			Recode('ascii', 'utf-8')('한')
		with self.assertRaises(ValueError):
			Recode('latin-1', 'utf-8')('ÿ')
		self.assertEqual(Recode('utf-8', 'utf-8')('\ufffd'), '\ufffd')
		return

	def test_conditionals(self) -> None:
		self.assertEqual(IfEmpty(Default('x'), Upper())(''), 'X')
		self.assertEqual(IfEmpty(Default('x'))(' '), ' ')
		self.assertEqual(IfMatch(r'[a-z]+', Upper())('abc'), 'ABC')
		self.assertEqual(IfMatch(r'[a-z]+', Upper())('abc1'), 'abc1')
		with self.assertRaises(ValueError):
			IfEmpty(Required())('')
		with self.assertRaises(ValueError):
			IfMatch('x', Choices('y'))('x')
		return

	def test_error_handlers_receive_original_values(self) -> None:
		handler = Recover()
		cases = (
			(Required(error=handler), ''),
			(Length(2, error=handler), 'a'),
			(Regex('x', error=handler), 'a'),
			(Choices('x', error=handler), 'a'),
			(RejectCharacters('?', error=handler), '?'),
			(RejectSurrogates(error=handler), '\udcff'),
			(RejectReplacementCharacter(error=handler), '\ufffd'),
			(Map({}, error=handler), 'a'),
			(Date('%Y-%m-%d', error=handler), 'invalid'),
			(Number(error=handler), 'invalid'),
			(Range(0, 1, error=handler), '2'),
			(Range(0, 1, error=handler), 'invalid'),
			(Recode('ascii', 'utf-8', error=handler), '한'),
		)
		for pattern, value in cases:
			self.assertEqual(pattern(value), 'recovered')
		self.assertEqual(handler.values, [value for pattern, value in cases])
		for pattern, value in (
			(Required(error=Fail()), ''),
			(Date('%Y-%m-%d', error=Fail()), 'invalid'),
			(Number(error=Fail()), 'invalid'),
			(Range(0, 1, error=Fail()), 'invalid'),
			(Recode('ascii', 'utf-8', error=Fail()), '한'),
		):
			with self.assertRaisesRegex(RuntimeError, 'Handler failure'):
				pattern(value)
		return

	def test_success_does_not_invoke_handler(self) -> None:
		handler = Recover()
		for pattern, value in (
			(Required(error=handler), 'a'),
			(Length(1, error=handler), 'a'),
			(Regex('a', error=handler), 'a'),
			(Choices('a', error=handler), 'a'),
			(RejectCharacters('?', error=handler), 'a'),
			(RejectSurrogates(error=handler), '한'),
			(RejectReplacementCharacter(error=handler), '?'),
			(Map({'a': 'a'}, error=handler), 'a'),
			(Date('%Y-%m-%d', error=handler), '2024-01-01'),
			(Number(error=handler), '1'),
			(Range(0, 2, error=handler), '1'),
			(Recode('utf-8', 'utf-8', error=handler), '한'),
		):
			self.assertEqual(pattern(value), value)
		self.assertEqual(handler.values, [])
		return

	def test_configuration_errors_are_immediate(self) -> None:
		handler = Recover()
		for factory in (
			lambda: Strip(1),
			lambda: Replace('a', 1),
			lambda: RegexReplace('(', 'a'),
			lambda: RegexReplace('(a)', r'\2'),
			lambda: UnicodeNormalize('invalid'),
			lambda: Length(-1, error=handler),
			lambda: Length(3, 2, error=handler),
			lambda: Map({'a': 1}, error=handler),
			lambda: Required(error='invalid'),
			lambda: Regex('[', error=handler),
			lambda: Choices(1, error=handler),
			lambda: RejectCharacters(1, error=handler),
			lambda: Date(error=handler),
			lambda: Date('%m-%d', error=handler),
			lambda: Date('%Y-%m-%d %H', error=handler),
			lambda: Date('%Y-%m-%d', output='%Q', error=handler),
			lambda: Date('%Y-%Y-%m-%d', error=handler),
			lambda: Date('%Y-%m-%d%%%', error=handler),
			lambda: Number(decimal=',', thousands=',', error=handler),
			lambda: Number(decimal='a', error=handler),
			lambda: Range(error=handler),
			lambda: Range(2, 1, error=handler),
			lambda: Range(Decimal('Infinity'), error=handler),
			lambda: Range(1.2, error=handler),
			lambda: Recode('unknown', 'utf-8', error=handler),
			lambda: Default(None),
		):
			with self.assertRaises((TypeError, ValueError, LookupError, RegexError)):
				factory()
		self.assertEqual(handler.values, [])
		return

	def test_csv_pipeline(self) -> None:
		with TemporaryDirectory() as directory:
			path = Path(directory) / 'input.csv'
			path.write_text(
				'name,date,amount\n Alice ,29/02/2024,"1,234.500"\n',
				encoding='utf-8',
			)
			csv = CSV(cols={
				'name': Validator(Strip(), Required(), Upper()),
				'date': Validator(Date('%d/%m/%Y')),
				'amount': Validator(Number(thousands=','), Range(0, 2000)),
			})
			with csv.open(str(path)):
				header = csv.header()
				self.assertEqual(
					list(csv.rows(header=header)),
					[{'name': 'ALICE', 'date': '2024-02-29', 'amount': '1234.5'}],
				)
		return


if __name__ == '__main__':
	main()
