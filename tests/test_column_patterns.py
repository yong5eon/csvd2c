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
from csvd2c.header import Validator as HeaderValidator
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


class ColumnPatternTests(TestCase):
	"""
	Verify string transformations, strict validation, and raised column errors.
	"""

	def test_string_transformations(self) -> None:
		self.assertEqual(Strip()('\t 이름 \n', 1, 0), '이름')
		self.assertEqual(Strip('_')('__abc__', 1, 0), 'abc')
		self.assertEqual(CollapseWhitespace()(' \ta\n\nb ', 1, 0), ' a b ')
		self.assertEqual(Replace('x', 'y', 1)('xx', 1, 0), 'yx')
		self.assertEqual(Replace('', '-')('a', 1, 0), '-a-')
		self.assertEqual(RegexReplace(r'([0-9]+)', r'[\1]')('a12b3', 1, 0), 'a[12]b[3]')
		self.assertEqual(RegexReplace('a', 'b', count=1, flags=IGNORECASE)('Aa', 1, 0), 'ba')
		self.assertEqual(Lower()('ABC', 1, 0), 'abc')
		self.assertEqual(Upper()('abc', 1, 0), 'ABC')
		self.assertEqual(CaseFold()('Straße', 1, 0), 'strasse')
		self.assertEqual(UnicodeNormalize()('e\u0301', 1, 0), 'é')
		self.assertEqual(UnicodeNormalize('NFKC')('１２３', 1, 0), '123')
		self.assertEqual(Default('missing')('', 1, 0), 'missing')
		self.assertEqual(Default('missing')(' ', 1, 0), ' ')
		return

	def test_required_length_regex_choices(self) -> None:
		self.assertEqual(Required()(' ', 1, 0), ' ')
		with self.assertRaises(Error):
			Required()('', 1, 0)
		for value in ('a', 'ab'):
			self.assertEqual(Length(1, 2)(value, 1, 0), value)
		for value in ('', 'abc'):
			with self.assertRaises(Error):
				Length(1, 2)(value, 1, 0)
		self.assertEqual(Length(1, 1)('한', 1, 0), '한')
		self.assertEqual(Regex(r'[0-9]+')('123', 1, 0), '123')
		with self.assertRaises(Error):
			Regex(r'[0-9]+')('a123', 1, 0)
		self.assertEqual(Regex('yes', flags=IGNORECASE)('YES', 1, 0), 'YES')
		self.assertEqual(Choices('예', '아니오')('예', 1, 0), '예')
		with self.assertRaises(Error):
			Choices('Y')('y', 1, 0)
		with self.assertRaises(Error):
			Choices()('', 1, 0)
		return

	def test_damage_checks(self) -> None:
		with self.assertRaises(Error):
			RejectCharacters('\x00?')('a?', 1, 0)
		self.assertEqual(RejectCharacters('')('?', 1, 0), '?')
		for char in (
			'\ud800',
			'\udc80',
			'\udcff',
			'\udfff',
		):
			with self.assertRaises(Error):
				RejectSurrogates()('a' + char, 1, 0)
		for value in ('한글😀', '\ud7ff', '\ue000', '?'):
			self.assertEqual(RejectSurrogates()(value, 1, 0), value)
		with self.assertRaises(Error):
			RejectReplacementCharacter()('a\ufffdb', 1, 0)
		self.assertEqual(RejectReplacementCharacter()('?', 1, 0), '?')
		return

	def test_map_copies_configuration(self) -> None:
		mapping = {'예': 'Y', '': ''}
		pattern = Map(mapping)
		mapping['예'] = 'changed'
		self.assertEqual(pattern('예', 1, 0), 'Y')
		self.assertEqual(pattern('', 1, 0), '')
		with self.assertRaises(Error):
			pattern('unknown', 1, 0)
		return

	def test_dates_and_ambiguity(self) -> None:
		pattern = Date('%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%d')
		self.assertEqual(pattern('2024-02-29', 1, 0), '2024-02-29')
		self.assertEqual(pattern('29/02/2024', 1, 0), '2024-02-29')
		self.assertEqual(Date('%Y-%m-%d', output='%d/%m/%Y')('2024-02-29', 1, 0), '29/02/2024')
		for value in ('2023-02-29', '2024-13-01', '1-10', 'Feb-23'):
			with self.assertRaises(Error):
				pattern(value, 1, 0)
		ambiguous = Date('%d/%m/%Y', '%m/%d/%Y')
		with self.assertRaisesRegex(Error, 'multiple'):
			ambiguous('01/02/2024', 1, 0)
		self.assertEqual(ambiguous('02/02/2024', 1, 0), '2024-02-02')
		return

	def test_date_month_names_use_locale(self) -> None:
		previous: str = setlocale(LC_TIME)
		try:
			setlocale(LC_TIME, 'C')
			pattern = Date('%d-%b-%Y', '%d %B %Y')
			self.assertEqual(pattern('23-Feb-2024', 1, 0), '2024-02-23')
			self.assertEqual(pattern('23 February 2024', 1, 0), '2024-02-23')
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
			self.assertEqual(Number()(value, 1, 0), expected)
		self.assertEqual(Number(thousands=',')('1,234,567.8900', 1, 0), '1234567.89')
		self.assertEqual(Number(decimal=',', thousands='.')('-1.234,50', 1, 0), '-1234.5')
		self.assertEqual(Number(thousands=' ')('1 234.00', 1, 0), '1234')
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
			with self.assertRaises(Error):
				Number(thousands=',')(value, 1, 0)
		return

	def test_numeric_ranges(self) -> None:
		pattern = Range('1.5', Decimal('2.5'))
		for value in ('1.5', '2', '2.500'):
			self.assertEqual(pattern(value, 1, 0), value)
		for value in ('1.49', '2.51', 'NaN', 'abc', '1,000'):
			with self.assertRaises(Error):
				pattern(value, 1, 0)
		self.assertEqual(Range(maximum=0)('-100', 1, 0), '-100')
		self.assertEqual(Range(minimum=0)('0', 1, 0), '0')
		return

	def test_recode_known_path(self) -> None:
		original = '홍길동 café'
		corrupt: str = original.encode('utf-8').decode('latin-1')
		self.assertEqual(Recode('latin-1', 'utf-8')(corrupt, 1, 0), original)
		with self.assertRaises(Error):
			Recode('ascii', 'utf-8')('한', 1, 0)
		with self.assertRaises(Error):
			Recode('latin-1', 'utf-8')('ÿ', 1, 0)
		self.assertEqual(Recode('utf-8', 'utf-8')('\ufffd', 1, 0), '\ufffd')
		return

	def test_conditionals(self) -> None:
		self.assertEqual(IfEmpty(Default('x'), Upper())('', 1, 0), 'X')
		self.assertEqual(IfEmpty(Default('x'))(' ', 1, 0), ' ')
		self.assertEqual(IfMatch(r'[a-z]+', Upper())('abc', 1, 0), 'ABC')
		self.assertEqual(IfMatch(r'[a-z]+', Upper())('abc1', 1, 0), 'abc1')
		with self.assertRaises(Error):
			IfEmpty(Required())('', 1, 0)
		with self.assertRaises(Error):
			IfMatch('x', Choices('y'))('x', 1, 0)
		return

	def test_errors_carry_original_context(self) -> None:
		cases = (
			(Required(), ''),
			(Length(2), 'a'),
			(Regex('x'), 'a'),
			(Choices('x'), 'a'),
			(RejectCharacters('?'), '?'),
			(RejectSurrogates(), '\udcff'),
			(RejectReplacementCharacter(), '\ufffd'),
			(Map({}), 'a'),
			(Date('%Y-%m-%d'), 'invalid'),
			(Number(), 'invalid'),
			(Range(0, 1), '2'),
			(Range(0, 1), 'invalid'),
			(Recode('ascii', 'utf-8'), '한'),
		)
		for pattern, value in cases:
			with self.subTest(pattern=pattern, value=value):
				with self.assertRaises(Error) as context:
					pattern(value, 7, 'name')
				self.assertNotIsInstance(context.exception, ValueError)
				self.assertEqual(context.exception.value, value)
				self.assertEqual(context.exception.row, 7)
				self.assertEqual(context.exception.column, 'name')
				self.assertTrue(context.exception.message)
		return

	def test_success_returns_input(self) -> None:
		for pattern, value in (
			(Required(), 'a'),
			(Length(1), 'a'),
			(Regex('a'), 'a'),
			(Choices('a'), 'a'),
			(RejectCharacters('?'), 'a'),
			(RejectSurrogates(), '한'),
			(RejectReplacementCharacter(), '?'),
			(Map({'a': 'a'}), 'a'),
			(Date('%Y-%m-%d'), '2024-01-01'),
			(Number(), '1'),
			(Range(0, 2), '1'),
			(Recode('utf-8', 'utf-8'), '한'),
		):
			self.assertEqual(pattern(value, 1, 0), value)
		return

	def test_configuration_errors_are_immediate(self) -> None:
		for factory in (
			lambda: Strip(1),
			lambda: Replace('a', 1),
			lambda: RegexReplace('(', 'a'),
			lambda: RegexReplace('(a)', r'\2'),
			lambda: UnicodeNormalize('invalid'),
			lambda: Length(-1),
			lambda: Length(3, 2),
			lambda: Map({'a': 1}),
			lambda: Regex('['),
			lambda: Choices(1),
			lambda: RejectCharacters(1),
			lambda: Date(),
			lambda: Date('%m-%d'),
			lambda: Date('%Y-%m-%d %H'),
			lambda: Date('%Y-%m-%d', output='%Q'),
			lambda: Date('%Y-%Y-%m-%d'),
			lambda: Date('%Y-%m-%d%%%'),
			lambda: Number(decimal=',', thousands=','),
			lambda: Number(decimal='a'),
			lambda: Range(),
			lambda: Range(2, 1),
			lambda: Range(Decimal('Infinity')),
			lambda: Range(1.2),
			lambda: Recode('unknown', 'utf-8'),
			lambda: Default(None),
		):
			with self.assertRaises((TypeError, ValueError, LookupError, RegexError)):
				factory()
		return

	def test_csv_pipeline(self) -> None:
		with TemporaryDirectory() as directory:
			path = Path(directory) / 'input.csv'
			path.write_text(
				'name,date,amount\n Alice ,29/02/2024,"1,234.500"\n',
				encoding='utf-8',
			)
			csv = CSV(
				header=HeaderValidator(),
				column={
					'name': Validator(Strip(), Required(), Upper()),
					'date': Validator(Date('%d/%m/%Y')),
					'amount': Validator(Number(thousands=','), Range(0, 2000)),
				},
			)
			with csv.open(str(path)):
				self.assertEqual(csv.header(), ['name', 'date', 'amount'])
				self.assertEqual(
					list(csv.rows()),
					[{
						'name': 'ALICE',
						'date': '2024-02-29',
						'amount': '1234.5',
					}],
				)
		return


if __name__ == '__main__':
	main()
