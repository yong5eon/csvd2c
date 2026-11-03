# -*- coding: utf-8 -*-

from inspect import getmembers
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import (
	Dict,
	List,
	Optional,
	get_type_hints,
)
from unittest import (
	TestCase,
	main,
)

from csvd2c import (
	CSV,
	Error as BaseError,
)
from csvd2c.header import (
	Error,
	Pattern,
	Validator,
)
from csvd2c.header import patterns as header_patterns
from csvd2c.header.patterns import (
	Exact,
	ExactOrder,
	Includes,
	Length,
	RejectDuplicate,
	RejectEmpty,
)
from csvd2c.column import Validator as ColumnValidator
from csvd2c.column.patterns import (
	Strip,
	Upper,
)
from csvd2c.row import Validator as RowValidator


class Rename(Pattern):
	def __init__(
		self,
		names: Dict[str, str],
	) -> None:
		super().__init__()
		self.names: Dict[str, str] = dict(names)
		return

	def __call__(
		self,
		value: List[str],
	) -> List[str]:
		return [self.names.get(name, name) for name in value]


class Record(Pattern):
	def __init__(self) -> None:
		super().__init__()
		self.calls: List[List[str]] = []
		return

	def __call__(
		self,
		value: List[str],
	) -> List[str]:
		self.calls.append(list(value))
		return value


class HeaderValidationTests(TestCase):
	"""
	Verify header validation on open and the stored header contract.
	"""

	def setUp(self) -> None:
		self.directory = TemporaryDirectory()
		self.addCleanup(self.directory.cleanup)
		self.path: Path = Path(self.directory.name) / 'input.csv'
		self.path.write_bytes(b'name,note\n a , b \nc,d\n')
		return

	def test_open_validates_first_record(self) -> None:
		pattern = Record()
		csv = CSV(header=Validator(pattern))
		with csv.open(str(self.path)):
			self.assertEqual(pattern.calls, [['name', 'note']])
			self.assertEqual(csv.header(), ['name', 'note'])
			self.assertEqual(csv.row(), [' a ', ' b '])
			self.assertEqual(list(csv.rows()), [['c', 'd']])
		self.assertEqual(pattern.calls, [['name', 'note']])
		return

	def test_header_stores_validator_result(self) -> None:
		csv = CSV(header=Validator(Rename({'name': 'person'})))
		with csv.open(str(self.path)):
			self.assertEqual(csv.header(), ['person', 'note'])
		return

	def test_failure_raises_error_with_pattern_input(self) -> None:
		csv = CSV(
			header=Validator(
				Rename({'note': 'name'}),
				RejectDuplicate(),
			),
		)
		with self.assertRaises(Error) as context:
			with csv.open(str(self.path)):
				self.fail('Header validation must fail before entering the context')
		self.assertIsInstance(context.exception, BaseError)
		self.assertEqual(context.exception.value, ['name', 'name'])
		self.assertIsNone(csv.reader)
		self.assertIsNone(csv.text)
		self.assertIsNone(csv.header())
		with csv.open(str(self.path), header=Validator()):
			self.assertEqual(csv.header(), ['name', 'note'])
			self.assertEqual(csv.row(), [' a ', ' b '])
		return

	def test_failure_closes_file(self) -> None:
		csv = CSV(header=Validator(Length(1)))
		with self.assertRaises(Error):
			with csv.open(str(self.path)):
				self.fail('Header validation must fail')
		self.assertIsNone(csv.reader)
		# Renaming succeeds on Windows only when no handle remains open.
		moved: Path = self.path.with_name('moved.csv')
		self.path.rename(moved)
		self.assertTrue(moved.exists())
		return

	def test_other_pattern_exceptions_propagate_and_close(self) -> None:
		class Fail(Pattern):
			def __call__(
				self,
				value: List[str],
			) -> List[str]:
				raise KeyError('custom failure')

		csv = CSV(header=Validator(Fail()))
		with self.assertRaises(KeyError):
			with csv.open(str(self.path)):
				self.fail('Header validation must fail')
		self.assertIsNone(csv.reader)
		self.assertIsNone(csv.text)
		return

	def test_empty_file_raises_error_without_value(self) -> None:
		self.path.write_bytes(b'')
		csv = CSV(header=Validator())
		with self.assertRaises(Error) as context:
			with csv.open(str(self.path)):
				self.fail('An empty file has no header')
		self.assertIsNone(context.exception.value)
		self.assertIsNone(csv.reader)
		self.assertIsNone(csv.text)
		return

	def test_open_override_applies_only_to_that_open(self) -> None:
		csv = CSV(header=Validator(Rename({'name': 'constructor'})))
		with csv.open(str(self.path), header=Validator(Rename({'name': 'override'}))):
			self.assertEqual(csv.header(), ['override', 'note'])
		self.assertIsNone(csv.header())
		with csv.open(str(self.path)):
			self.assertEqual(csv.header(), ['constructor', 'note'])
		with csv.open(str(self.path), header=None):
			self.assertEqual(csv.header(), ['constructor', 'note'])
		return

	def test_override_without_constructor_validator(self) -> None:
		csv = CSV()
		with csv.open(str(self.path), header=Validator()):
			self.assertEqual(csv.header(), ['name', 'note'])
		with csv.open(str(self.path)):
			self.assertIsNone(csv.header())
			self.assertEqual(csv.row(), ['name', 'note'])
		return

	def test_non_validator_header_is_rejected(self) -> None:
		for value in (
			RowValidator(),
			RejectEmpty(),
			['name'],
		):
			with self.subTest(value=value):
				with self.assertRaises(TypeError):
					CSV(header=value)  # type: ignore[arg-type]
				csv = CSV()
				with self.assertRaises(TypeError):
					with csv.open(str(self.path), header=value):  # type: ignore[arg-type]
						self.fail('Invalid header Validator must fail')
				self.assertIsNone(csv.reader)
		return

	def test_without_header_validator(self) -> None:
		csv = CSV()
		with csv.open(str(self.path)):
			self.assertIsNone(csv.header())
			self.assertEqual(csv.row(), ['name', 'note'])
			self.assertIsNone(csv.header())
		return

	def test_header_is_repeatable_copy(self) -> None:
		csv = CSV(header=Validator())
		with csv.open(str(self.path)):
			first: Optional[List[str]] = csv.header()
			second: Optional[List[str]] = csv.header()
			self.assertEqual(first, second)
			self.assertIsNot(first, second)
			assert first is not None
			first.append('changed')
			first[0] = 'changed'
			self.assertEqual(csv.header(), ['name', 'note'])
			self.assertEqual(csv.row(), [' a ', ' b '])
		return

	def test_renamed_header_maps_named_columns(self) -> None:
		csv = CSV(
			header=Validator(Rename({'name': 'person'})),
			column={'person': ColumnValidator(Strip(), Upper())},
		)
		with csv.open(str(self.path)):
			self.assertEqual(csv.row(), ['A', ' b '])
		with csv.open(str(self.path)):
			with self.assertRaisesRegex(ValueError, 'exactly once'):
				csv.row(column={'name': ColumnValidator(Strip())})
		return

	def test_named_column_duplicate_and_missing_names(self) -> None:
		for names, column in (
			({'note': 'name'}, 'name'),
			({}, 'missing'),
		):
			with self.subTest(column=column):
				csv = CSV(
					header=Validator(Rename(names)),
					column={column: ColumnValidator(Strip())},
				)
				with csv.open(str(self.path)):
					with self.assertRaisesRegex(ValueError, 'exactly once'):
						csv.row()
					with self.assertRaisesRegex(ValueError, 'exactly once'):
						csv.rows()
					self.assertEqual(csv.row(column=()), [' a ', ' b '])
		return

	def test_named_column_without_header_is_rejected(self) -> None:
		csv = CSV(column={'name': ColumnValidator(Strip())})
		with csv.open(str(self.path)):
			for read in (
				csv.row,
				csv.rows,
			):
				with self.assertRaisesRegex(RuntimeError, 'Inject a header Validator'):
					read()
			self.assertEqual(csv.row(column=()), ['name', 'note'])
		csv = CSV()
		with csv.open(str(self.path)):
			with self.assertRaisesRegex(RuntimeError, 'Inject a header Validator'):
				csv.rows(column={'name': ColumnValidator(Strip())})
		return

	def test_column_keyword(self) -> None:
		csv = CSV(
			header=Validator(),
			column=(ColumnValidator(Strip()),),
		)
		with csv.open(str(self.path)):
			self.assertEqual(csv.row(), ['a', ' b '])
			self.assertEqual(
				list(csv.rows(column=(ColumnValidator(Upper()),))),
				[['C', 'd']],
			)
		with csv.open(str(self.path), header=Validator()):
			self.assertEqual(
				csv.row(column={'note': ColumnValidator(Strip())}),
				[' a ', 'b'],
			)
		return

	def test_cols_keyword_is_removed(self) -> None:
		with self.assertRaises(TypeError):
			CSV(cols=())  # type: ignore[call-arg]
		csv = CSV()
		with csv.open(str(self.path)):
			with self.assertRaises(TypeError):
				csv.row(cols=())  # type: ignore[call-arg]
			with self.assertRaises(TypeError):
				csv.rows(cols=())  # type: ignore[call-arg]
			self.assertEqual(csv.row(), ['name', 'note'])
		return

	def test_output_header_keyword_is_removed(self) -> None:
		csv = CSV(header=Validator())
		with csv.open(str(self.path)):
			with self.assertRaises(TypeError):
				csv.row(header=('first', 'second'))  # type: ignore[call-arg]
			with self.assertRaises(TypeError):
				csv.rows(header=('first', 'second'))  # type: ignore[call-arg]
			record: List[str] = csv.row()
			self.assertIsInstance(record, list)
			self.assertEqual(record, [' a ', ' b '])
			for item in csv.rows():
				self.assertIsInstance(item, list)
		return

	def test_validator_rejects_non_pattern(self) -> None:
		for value in (
			ColumnValidator(),
			'name',
			Validator(),
		):
			with self.subTest(value=value):
				with self.assertRaises(RuntimeError):
					Validator(value)  # type: ignore[arg-type]
		return

	def test_validator_applies_patterns_in_order(self) -> None:
		validator = Validator(
			Rename({'a': 'b'}),
			Rename({'b': 'c'}),
		)
		self.assertEqual(validator(['a']), ['c'])
		self.assertEqual(Validator()(['a']), ['a'])
		self.assertEqual(
			repr(Validator(RejectEmpty(), Length(1))),
			'Validator(RejectEmpty(), Length(1))',
		)
		return

	def test_public_callable_contracts(self) -> None:
		expected: Dict[str, object] = {
			'value': List[str],
			'return': List[str],
		}
		classes: List[type] = [
			Pattern,
			Validator,
		]
		classes.extend(
			value for name, value in getmembers(header_patterns)
			if isinstance(value, type) and issubclass(value, Pattern)
		)
		self.assertEqual(len(classes), 8)
		for cls in classes:
			with self.subTest(cls=cls):
				self.assertEqual(get_type_hints(cls.__call__), expected)
		self.assertTrue(issubclass(Error, BaseError))
		error = Error('failure', ['a'])
		self.assertEqual(error.message, 'failure')
		self.assertEqual(error.value, ['a'])
		self.assertEqual(str(error), 'failure')
		with self.assertRaises(TypeError):
			Pattern()  # type: ignore[abstract]
		return


class HeaderPatternTests(TestCase):
	"""
	Verify each header Pattern's success, failure, and configuration rules.
	"""

	def assert_rejects(
		self,
		pattern: Pattern,
		value: List[str],
	) -> None:
		with self.assertRaises(Error) as context:
			pattern(value)
		self.assertEqual(context.exception.value, value)
		self.assertIsInstance(context.exception.message, str)
		return

	def test_reject_empty(self) -> None:
		value: List[str] = ['a', ' ']
		self.assertIs(RejectEmpty()(value), value)
		self.assertEqual(RejectEmpty()([]), [])
		self.assert_rejects(RejectEmpty(), ['a', ''])
		self.assert_rejects(RejectEmpty(), [''])
		return

	def test_reject_duplicate(self) -> None:
		value: List[str] = ['a', 'A', 'a ']
		self.assertIs(RejectDuplicate()(value), value)
		self.assertEqual(RejectDuplicate()([]), [])
		self.assert_rejects(RejectDuplicate(), ['a', 'b', 'a'])
		self.assert_rejects(RejectDuplicate(), ['', ''])
		return

	def test_length(self) -> None:
		value: List[str] = ['a', 'b']
		self.assertIs(Length(2)(value), value)
		self.assertEqual(Length(0)([]), [])
		self.assert_rejects(Length(1), [])
		self.assert_rejects(Length(1), value)
		self.assert_rejects(Length(3), value)
		with self.assertRaises(ValueError):
			Length(-1)
		for count in (
			'1',
			1.0,
			True,
			None,
		):
			with self.subTest(count=count):
				with self.assertRaises(TypeError):
					Length(count)  # type: ignore[arg-type]
		return

	def test_includes(self) -> None:
		value: List[str] = ['c', 'a', 'b']
		self.assertIs(Includes('a', 'b')(value), value)
		self.assertIs(Includes()(value), value)
		self.assert_rejects(Includes('a', 'd'), value)
		self.assert_rejects(Includes('A'), value)
		self.assert_rejects(Includes('a'), [' a'])
		return

	def test_exact(self) -> None:
		value: List[str] = ['b', 'a']
		self.assertIs(Exact('a', 'b')(value), value)
		self.assertEqual(Exact()([]), [])
		self.assert_rejects(Exact('a', 'b', 'c'), value)
		self.assert_rejects(Exact('a'), value)
		self.assert_rejects(Exact('A', 'b'), value)
		self.assert_rejects(Exact('a ', 'b'), value)
		self.assert_rejects(Exact('a', 'b'), ['a', 'a', 'b'])
		self.assertEqual(Exact('b', 'a', 'a')(['a', 'a', 'b']), ['a', 'a', 'b'])
		self.assert_rejects(Exact('a', 'a', 'b'), ['a', 'b', 'b'])
		return

	def test_exact_order(self) -> None:
		value: List[str] = ['a', 'b']
		self.assertIs(ExactOrder('a', 'b')(value), value)
		self.assertEqual(ExactOrder()([]), [])
		self.assert_rejects(ExactOrder('b', 'a'), value)
		self.assert_rejects(ExactOrder('a'), value)
		self.assert_rejects(ExactOrder('a', 'B'), value)
		self.assert_rejects(ExactOrder('a', ' b'), value)
		return

	def test_non_string_names_are_rejected(self) -> None:
		for factory in (
			Includes,
			Exact,
			ExactOrder,
		):
			for name in (
				1,
				None,
				b'a',
			):
				with self.subTest(factory=factory, name=name):
					with self.assertRaises(TypeError):
						factory('a', name)  # type: ignore[arg-type]
		return

	def test_patterns_in_validator(self) -> None:
		validator = Validator(
			Length(3),
			RejectEmpty(),
			RejectDuplicate(),
			Includes('id'),
			Exact('name', 'id', 'date'),
			ExactOrder('id', 'name', 'date'),
		)
		self.assertEqual(validator(['id', 'name', 'date']), ['id', 'name', 'date'])
		with self.assertRaises(Error) as context:
			validator(['id', 'date', 'name'])
		self.assertEqual(context.exception.value, ['id', 'date', 'name'])
		return

	def test_representations(self) -> None:
		self.assertEqual(repr(RejectEmpty()), 'RejectEmpty()')
		self.assertEqual(repr(RejectDuplicate()), 'RejectDuplicate()')
		self.assertEqual(repr(Length(2)), 'Length(2)')
		self.assertEqual(repr(Includes('a', 'b')), "Includes('a', 'b')")
		self.assertEqual(repr(Exact('a')), "Exact('a')")
		self.assertEqual(repr(ExactOrder('a', 'b')), "ExactOrder('a', 'b')")
		return


if __name__ == '__main__':
	main()
