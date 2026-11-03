from pathlib import Path
from inspect import (
	getmembers,
	signature,
)
from tempfile import TemporaryDirectory
from typing import (
	List,
	Tuple,
	Union,
	get_type_hints,
)
from unittest import (
	TestCase,
	main,
)
from csvd2c import (
	CSV,
	Error,
)
from csvd2c.header import Validator as HeaderValidator
from csvd2c.row import (
	Error as RowError,
	Pattern as RowPattern,
	Validator as RowValidator,
)
from csvd2c.row.patterns import (
	IfLength,
	Insert,
	Length,
	Merge,
	Remove,
	Reorder,
	Split,
)
from csvd2c.column import (
	Error as ColumnError,
	Pattern as ColumnPattern,
	Validator as ColumnValidator,
)
from csvd2c.row import patterns as row_patterns
from csvd2c.column import patterns as column_patterns
from csvd2c.column.patterns import (
	IfEmpty,
	IfMatch,
	Required,
	Strip,
)


class CustomError(Error):
	pass


class RejectAll(ColumnPattern):
	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		raise CustomError('Rejected by custom Pattern')


class MutateRow(RowPattern):
	def __call__(
		self,
		value: List[str],
		row: int,
	) -> List[str]:
		value[:] = ['changed']
		return value


class ErrorContextTests(TestCase):
	def setUp(self) -> None:
		self.directory = TemporaryDirectory()
		self.addCleanup(self.directory.cleanup)
		self.path: Path = Path(self.directory.name) / 'input.csv'
		return

	def test_common_base_and_attributes(self) -> None:
		self.assertTrue(issubclass(Error, Exception))
		self.assertFalse(issubclass(Error, ValueError))
		self.assertTrue(issubclass(RowError, Error))
		self.assertTrue(issubclass(ColumnError, Error))
		self.assertTrue(issubclass(CustomError, Error))

		error: Error = Error('base failure')
		self.assertEqual(error.message, 'base failure')
		self.assertEqual(str(error), 'base failure')

		row_error: RowError = RowError('row failure', 3, ['a', 'b'])
		self.assertEqual(row_error.message, 'row failure')
		self.assertEqual(row_error.row, 3)
		self.assertEqual(row_error.value, ['a', 'b'])
		self.assertEqual(str(row_error), 'row failure')

		column_error: ColumnError = ColumnError('column failure', 4, 'name', 'x')
		self.assertEqual(column_error.message, 'column failure')
		self.assertEqual(column_error.row, 4)
		self.assertEqual(column_error.column, 'name')
		self.assertEqual(column_error.value, 'x')
		self.assertEqual(str(column_error), 'column failure')

		with self.assertRaises(Error) as context:
			ColumnValidator(RejectAll())('a', 1, 0)
		self.assertIsInstance(context.exception, CustomError)
		self.assertEqual(context.exception.message, 'Rejected by custom Pattern')
		return

	def test_error_classes_are_not_callable(self) -> None:
		for error in (
			Error('failure'),
			RowError('failure', 1, []),
			ColumnError('failure', 1, 0, ''),
		):
			with self.subTest(error=error):
				self.assertFalse(callable(error))
		return

	def test_public_callable_contracts(self) -> None:
		for base, validator, patterns, expected in (
			(RowPattern, RowValidator, row_patterns, {'value': List[str], 'row': int, 'return': List[str]}),
			(ColumnPattern, ColumnValidator, column_patterns, {'value': str, 'row': int, 'column': Union[int, str], 'return': str}),
		):
			classes = [base, validator]
			classes.extend(
				value for name, value in getmembers(patterns)
				if isinstance(value, type) and issubclass(value, base)
			)
			for cls in classes:
				with self.subTest(cls=cls):
					self.assertEqual(get_type_hints(cls.__call__), expected)
					parameters = signature(cls.__call__).parameters
					for name in ('row', 'column'):
						if name in expected:
							self.assertIs(parameters[name].default, parameters[name].empty)
		return

	def test_pattern_input_not_chain_start(self) -> None:
		validator: ColumnValidator = ColumnValidator(
			Strip(),
			IfEmpty(Required()),
		)
		with self.assertRaises(ColumnError) as context:
			validator('   ', 7, 'name')
		self.assertEqual(context.exception.value, '')
		self.assertEqual(context.exception.row, 7)
		self.assertEqual(context.exception.column, 'name')
		row_validator: RowValidator = RowValidator(
			MutateRow(),
			IfLength(1, Length(2)),
		)
		with self.assertRaises(RowError) as row_context:
			row_validator(['initial'], 8)
		self.assertEqual(row_context.exception.value, ['changed'])
		self.assertEqual(row_context.exception.row, 8)
		return

	def test_nested_exception_propagates(self) -> None:
		with self.assertRaises(RowError) as context:
			RowValidator(IfLength(1, Length(2)))(['a'], 1)
		self.assertEqual(context.exception.value, ['a'])
		self.assertEqual(context.exception.row, 1)
		with self.assertRaises(ColumnError) as column_context:
			ColumnValidator(
				Strip(),
				IfMatch('', Required()),
			)(' ', 4, 0)
		self.assertEqual(column_context.exception.value, '')
		self.assertEqual(column_context.exception.row, 4)
		self.assertEqual(column_context.exception.column, 0)
		return

	def test_csv_modes_and_last_physical_line(self) -> None:
		self.path.write_text('name,note\n   ,"first\nsecond"\nok,next\n', encoding='utf-8')
		for mode in (
			'rb',
			'r',
			'rt',
		):
			csv: CSV = CSV(
				header=HeaderValidator(),
				column={'name': ColumnValidator(Strip(), Required())},
			)
			with self.subTest(mode=mode), csv.open(str(self.path), mode):
				with self.assertRaises(ColumnError) as context:
					csv.row()
				self.assertEqual(context.exception.value, '')
				self.assertEqual(context.exception.row, 3)
				self.assertEqual(context.exception.column, 'name')
				self.assertEqual(csv.row(), ['ok', 'next'])
		return

	def test_numeric_column_and_rows_overrides(self) -> None:
		self.path.write_text(' \n \n', encoding='utf-8')
		cols: Tuple[ColumnValidator, ...] = (
			ColumnValidator(Strip(), Required()),
		)
		with CSV().open(str(self.path)) as csv:
			for line in (
				1,
				2,
			):
				with self.assertRaises(ColumnError) as context:
					next(csv.rows(column=cols))
				self.assertEqual(context.exception.value, '')
				self.assertEqual(context.exception.row, line)
				self.assertEqual(context.exception.column, 0)
			self.assertEqual(list(csv.rows(column=cols)), [])
		return

	def test_row_changes_define_column_positions(self) -> None:
		validator: ColumnValidator = ColumnValidator(Strip(), Required())
		cases: Tuple[Tuple[RowValidator, str], ...] = (
			(RowValidator(Reorder(1, 0)), 'ok, \n'),
			(RowValidator(Merge(0, 2, sep='')), ' , \n'),
			(RowValidator(Split(0, sep='|')), '|ok\n'),
			(RowValidator(Insert(0, ' ')), 'ok\n'),
			(RowValidator(Remove(0)), 'ok, \n'),
		)
		for row, text in cases:
			self.path.write_text(text, encoding='utf-8')
			with self.subTest(row=row), CSV(row=row, column=(validator,)).open(str(self.path)) as csv:
				with self.assertRaises(ColumnError) as context:
					csv.row()
				self.assertEqual(context.exception.value, '')
				self.assertEqual(context.exception.row, 1)
				self.assertEqual(context.exception.column, 0)
		return

	def test_named_column_keeps_existing_header_index(self) -> None:
		self.path.write_text('left,right\nok, \n', encoding='utf-8')
		csv: CSV = CSV(
			header=HeaderValidator(),
			row=RowValidator(Reorder(1, 0)),
			column={'left': ColumnValidator(Strip(), Required())},
		)
		with csv.open(str(self.path)):
			with self.assertRaises(ColumnError) as context:
				csv.row()
		self.assertEqual(context.exception.value, '')
		self.assertEqual(context.exception.row, 2)
		self.assertEqual(context.exception.column, 'left')
		return

	def test_row_failure_can_resume(self) -> None:
		self.path.write_text('a\nb,c\n', encoding='utf-8')
		csv: CSV = CSV(row=RowValidator(Length(2)))
		with csv.open(str(self.path)):
			with self.assertRaises(RowError) as context:
				csv.row()
			self.assertEqual(context.exception.value, ['a'])
			self.assertEqual(context.exception.row, 1)
			self.assertEqual(csv.row(), ['b', 'c'])
		return

	def test_legacy_calls_are_not_retried(self) -> None:
		with self.assertRaises(TypeError):
			RowValidator()(['a'])  # type: ignore[call-arg]
		with self.assertRaises(TypeError):
			ColumnValidator()('a')  # type: ignore[call-arg]
		return


if __name__ == '__main__':
	main()
