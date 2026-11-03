# -*- coding: utf-8 -*-

from csv import Error
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import (
	List,
	Union,
)
from unittest import (
	TestCase,
	main,
)
from unittest.mock import patch

from csvd2c import CSV
from csvd2c.header import Validator as HeaderValidator
from csvd2c.row import (
	Error as RowError,
	Pattern as RowPattern,
	Validator as RowValidator,
)
from csvd2c.column import (
	Error as ColumnError,
	Pattern as ColumnPattern,
	Validator as ColumnValidator,
)

PARSE_ERROR: bytes = b'"bad"x\n'


class RejectValue(ColumnPattern):
	"""
	Reject one value and record every value it receives.
	"""

	def __init__(
		self,
		value: str,
	) -> None:
		self.value = value
		self.seen: List[str] = []
		return

	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		self.seen.append(value)
		if value == self.value:
			raise ColumnError('Rejected value', row, column, value)
		return value


class RecordRows(RowPattern):
	"""
	Record every row passed to the row Validator.
	"""

	def __init__(self) -> None:
		self.seen: List[List[str]] = []
		return

	def __call__(
		self,
		value: List[str],
		row: int,
	) -> List[str]:
		self.seen.append(list(value))
		return value


class RangeTests(TestCase):
	"""
	Verify offset and limit read ranges.
	"""

	def setUp(self) -> None:
		self.directory = TemporaryDirectory()
		self.addCleanup(self.directory.cleanup)
		self.path: Path = Path(self.directory.name) / 'input.csv'
		self.path.write_bytes(b'id\nr0\nr1\nr2\nr3\nr4\n')
		return

	def write(
		self,
		*records: bytes,
	) -> None:
		self.path.write_bytes(b''.join(records))
		return

	def read_all(
		self,
		csv: CSV,
	) -> List[List[str]]:
		records: List[List[str]] = []
		while True:
			try:
				records.append(csv.row())
			except StopIteration:
				return records

	def test_range_is_only_in_constructor_and_open(self) -> None:
		csv = CSV(
			header=HeaderValidator(),
			offset=1,
			limit=2,
		)
		with csv.open(str(self.path)):
			with self.assertRaises(TypeError):
				csv.row(offset=1)  # type: ignore[call-arg]
			with self.assertRaises(TypeError):
				csv.rows(limit=1)  # type: ignore[call-arg]
			self.assertEqual(list(csv.rows()), [['r1'], ['r2']])
		return

	def test_invalid_values_are_rejected(self) -> None:
		for value in (
			1.0,
			'1',
			True,
			False,
		):
			with self.subTest(value=value):
				with self.assertRaises(TypeError):
					CSV(offset=value)  # type: ignore[arg-type]
				with self.assertRaises(TypeError):
					CSV(limit=value)  # type: ignore[arg-type]
		with self.assertRaises(TypeError):
			CSV(offset=None)  # type: ignore[arg-type]
		with self.assertRaises(ValueError):
			CSV(offset=-1)
		with self.assertRaises(ValueError):
			CSV(limit=-1)
		csv = CSV()
		with patch('builtins.open') as opened:
			for offset, limit, error in (
				(
					-1,
					None,
					ValueError,
				),
				(
					None,
					-1,
					ValueError,
				),
				(
					'1',
					None,
					TypeError,
				),
				(
					None,
					True,
					TypeError,
				),
			):
				with self.subTest(offset=offset, limit=limit):
					with self.assertRaises(error):
						with csv.open(str(self.path), offset=offset, limit=limit):  # type: ignore[arg-type]
							self.fail('Invalid range must fail')
			opened.assert_not_called()
		self.assertIsNone(csv.reader)
		return

	def test_constructor_defaults_open_overrides_and_reopen(self) -> None:
		csv = CSV(
			header=HeaderValidator(),
			offset=1,
			limit=2,
		)
		with csv.open(str(self.path)):
			self.assertEqual(self.read_all(csv), [['r1'], ['r2']])
		with csv.open(str(self.path), offset=3):
			self.assertEqual(self.read_all(csv), [['r3'], ['r4']])
		with csv.open(str(self.path), limit=1):
			self.assertEqual(self.read_all(csv), [['r1']])
		with csv.open(str(self.path), offset=0, limit=3):
			self.assertEqual(self.read_all(csv), [['r0'], ['r1'], ['r2']])
		with csv.open(str(self.path), offset=None, limit=None):
			self.assertEqual(self.read_all(csv), [['r1'], ['r2']])
		self.assertEqual(csv.offset, 1)
		self.assertEqual(csv.limit, 2)
		return

	def test_reopen_restarts_count(self) -> None:
		csv = CSV(limit=2)
		with csv.open(str(self.path)):
			self.assertEqual(csv.row(), ['id'])
		with csv.open(str(self.path)):
			self.assertEqual(self.read_all(csv), [['id'], ['r0']])
		return

	def test_position_zero_depends_on_header_validation(self) -> None:
		with CSV(header=HeaderValidator()).open(str(self.path), offset=0, limit=1) as csv:
			self.assertEqual(csv.header(), ['id'])
			self.assertEqual(self.read_all(csv), [['r0']])
		with CSV().open(str(self.path), offset=0, limit=1) as csv:
			self.assertIsNone(csv.header())
			self.assertEqual(self.read_all(csv), [['id']])
		with CSV().open(str(self.path), offset=1, limit=1) as csv:
			self.assertEqual(self.read_all(csv), [['r0']])
		return

	def test_quoted_newline_is_one_record(self) -> None:
		self.write(b'id\n"a\nb"\n"c\nd"\ne\n')
		with CSV(header=HeaderValidator()).open(str(self.path), offset=1, limit=1) as csv:
			self.assertEqual(self.read_all(csv), [['c\nd']])
		return

	def test_offset_skips_validation(self) -> None:
		row = RecordRows()
		column = RejectValue('r0')
		csv = CSV(
			header=HeaderValidator(),
			row=RowValidator(row),
			column=(ColumnValidator(column),),
			offset=2,
		)
		with csv.open(str(self.path)):
			self.assertEqual(csv.row(), ['r2'])
		self.assertEqual(row.seen, [['r2']])
		self.assertEqual(column.seen, ['r2'])
		return

	def test_offset_parse_error_propagates(self) -> None:
		self.write(b'id\n', PARSE_ERROR, b'r1\n')
		with CSV(header=HeaderValidator()).open(str(self.path), offset=1) as csv:
			with self.assertRaises(Error):
				csv.row()
		with CSV(header=HeaderValidator()).open(str(self.path), offset=1) as csv:
			with self.assertRaises(Error):
				list(csv.rows())
		return

	def test_offset_beyond_records_ends(self) -> None:
		with CSV(header=HeaderValidator()).open(str(self.path), offset=10) as csv:
			with self.assertRaises(StopIteration):
				csv.row()
		with CSV(header=HeaderValidator()).open(str(self.path), offset=10) as csv:
			self.assertEqual(list(csv.rows()), [])
		return

	def test_validation_failures_count_toward_limit(self) -> None:
		csv = CSV(
			header=HeaderValidator(),
			column=(ColumnValidator(RejectValue('r1')),),
			limit=3,
		)
		results: List[Union[List[str], int]] = []
		with csv.open(str(self.path)):
			while True:
				try:
					results.append(csv.row())
				except ColumnError as error:
					results.append(error.row)
				except StopIteration:
					break
		self.assertEqual(results, [['r0'], 3, ['r2']])
		return

	def test_row_validation_failure_counts_toward_limit(self) -> None:
		csv = CSV(
			header=HeaderValidator(),
			column=(
				ColumnValidator(),
				ColumnValidator(),
			),
			limit=1,
		)
		with csv.open(str(self.path)):
			with self.assertRaises(RowError):
				csv.row()
			with self.assertRaises(StopIteration):
				csv.row()
		return

	def test_parse_error_does_not_count_toward_limit(self) -> None:
		self.write(b'id\nr0\n', PARSE_ERROR, b'r2\nr3\n')
		with CSV(header=HeaderValidator()).open(str(self.path), limit=2) as csv:
			self.assertEqual(csv.row(), ['r0'])
			with self.assertRaises(Error):
				csv.row()
			self.assertEqual(csv.row(), ['r2'])
			with self.assertRaises(StopIteration):
				csv.row()
		return

	def test_limit_does_not_read_next_record(self) -> None:
		self.write(b'id\nr0\nr1\n', PARSE_ERROR)
		with CSV(header=HeaderValidator()).open(str(self.path), limit=2) as csv:
			self.assertEqual(self.read_all(csv), [['r0'], ['r1']])
			with self.assertRaises(StopIteration):
				csv.row()
		with CSV(header=HeaderValidator()).open(str(self.path), limit=2) as csv:
			self.assertEqual(list(csv.rows()), [['r0'], ['r1']])
			self.assertEqual(list(csv.rows()), [])
		return

	def test_limit_zero_reads_nothing(self) -> None:
		self.write(b'id\n', PARSE_ERROR, b'r1\n')
		with CSV(header=HeaderValidator()).open(str(self.path), offset=1, limit=0) as csv:
			with self.assertRaises(StopIteration):
				csv.row()
			self.assertEqual(list(csv.rows()), [])
			self.assertEqual(csv.reader.line_num, 1)  # type: ignore[union-attr]
		return

	def test_row_rows_and_mixed_reads_share_range(self) -> None:
		expected: List[List[str]] = [['r1'], ['r2'], ['r3']]
		csv = CSV(
			header=HeaderValidator(),
			offset=1,
			limit=3,
		)
		with csv.open(str(self.path)):
			self.assertEqual(self.read_all(csv), expected)
		with csv.open(str(self.path)):
			self.assertEqual(list(csv.rows()), expected)
		with csv.open(str(self.path)):
			mixed: List[List[str]] = [csv.row()]
			rows = csv.rows()
			mixed.append(next(rows))
			mixed.append(csv.row())
			mixed.extend(rows)
			self.assertEqual(mixed, expected)
		return

	def test_rows_resumes_after_validation_failure(self) -> None:
		csv = CSV(
			header=HeaderValidator(),
			column=(ColumnValidator(RejectValue('r2')),),
			offset=1,
			limit=3,
		)
		with csv.open(str(self.path)):
			records: List[List[str]] = []
			with self.assertRaises(ColumnError):
				for record in csv.rows():
					records.append(record)
			records.extend(csv.rows())
		self.assertEqual(records, [['r1'], ['r3']])
		return

	def test_unbounded_range_matches_default(self) -> None:
		with CSV(header=HeaderValidator()).open(str(self.path)) as csv:
			default: List[List[str]] = list(csv.rows())
		with CSV(header=HeaderValidator(), offset=0, limit=None).open(str(self.path)) as csv:
			self.assertEqual(list(csv.rows()), default)
		self.assertEqual(default, [['r0'], ['r1'], ['r2'], ['r3'], ['r4']])
		return


if __name__ == '__main__':
	main()
