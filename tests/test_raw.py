# -*- coding: utf-8 -*-

from csv import (
	Error as CSVError,
	reader,
	writer,
)
from inspect import signature
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import (
	Generator,
	List,
	Optional,
	get_type_hints,
)
from unittest import (
	TestCase,
	main,
)

from csvd2c import CSV
from csvd2c.header import (
	Error as HeaderError,
	Pattern as HeaderPattern,
	Validator as HeaderValidator,
)
from csvd2c.header.patterns import Length as HeaderLength
from csvd2c.row import (
	Error as RowError,
	Pattern as RowPattern,
	Validator as RowValidator,
)
from csvd2c.row.patterns import (
	Length,
	Reorder,
)
from csvd2c.column import (
	Error as ColumnError,
	Validator as ColumnValidator,
)
from csvd2c.column.patterns import (
	Required,
	Strip,
)


class ReverseInPlace(RowPattern):
	def __call__(
		self,
		value: List[str],
		row: int,
	) -> List[str]:
		value.reverse()
		return value


class UpperHeader(HeaderPattern):
	def __call__(
		self,
		value: List[str],
	) -> List[str]:
		return [field.upper() for field in value]


class RawTests(TestCase):
	"""
	Verify pre-validation snapshots and their read/lifetime boundaries.
	"""

	def setUp(self) -> None:
		self.directory: TemporaryDirectory[str] = TemporaryDirectory()
		self.addCleanup(self.directory.cleanup)
		self.path: Path = Path(self.directory.name) / 'input.csv'
		self.path.write_bytes(b' a , b \nc,d\n')
		return

	def test_public_signature(self) -> None:
		self.assertEqual(list(signature(CSV.raw).parameters), ['self'])
		self.assertEqual(get_type_hints(CSV.raw), {'return': Optional[List[str]]})
		return

	def test_success_and_independent_copies(self) -> None:
		for mode in (
			'rb',
			'r',
			'rt',
		):
			with self.subTest(mode=mode), CSV(limit=2).open(str(self.path), mode) as csv:
				record: List[str] = csv.row()
				original: List[str] = record.copy()
				first: Optional[List[str]] = csv.raw()
				second: Optional[List[str]] = csv.raw()
				assert first is not None and second is not None
				self.assertEqual(first, original)
				self.assertIsNot(first, second)
				first[0] = 'changed'
				first.pop()
				first.append('added')
				record.clear()
				self.assertEqual(csv.raw(), original)
				self.assertEqual(csv.row(), [
					'c',
					'd',
				])
				self.assertEqual(csv.raw(), [
					'c',
					'd',
				])
				with self.assertRaises(StopIteration):
					csv.row()
				self.assertIsNone(csv.raw())
		return

	def test_row_transformations_before_success_or_failure(self) -> None:
		for pattern in (
			ReverseInPlace(),
			Reorder(1, 0),
		):
			for fail in (
				False,
				True,
			):
				csv: CSV = CSV(
					row=RowValidator(pattern, Length(3 if fail else 2)),
					column=(ColumnValidator(Strip()),),
				)
				with self.subTest(pattern=pattern, fail=fail), csv.open(str(self.path)):
					if fail:
						with self.assertRaises(RowError) as context:
							csv.row()
						self.assertEqual(context.exception.value, [
							' b ',
							' a ',
						])
					else:
						self.assertEqual(csv.row(), [
							'b',
							' a ',
						])
					self.assertEqual(csv.raw(), [
						' a ',
						' b ',
					])
		return

	def test_column_failure_preserves_all_original_fields(self) -> None:
		self.path.write_bytes(b' a ,   \nc,d\n')
		for mode in (
			'rb',
			'r',
			'rt',
		):
			csv: CSV = CSV(column=(
				ColumnValidator(Strip()),
				ColumnValidator(Strip(), Required()),
			))
			with self.subTest(mode=mode), csv.open(str(self.path), mode):
				with self.assertRaises(ColumnError) as context:
					csv.row()
				self.assertEqual(context.exception.value, '')
				self.assertEqual(context.exception.column, 1)
				self.assertEqual(context.exception.row, 1)
				self.assertEqual(csv.raw(), [
					' a ',
					'   ',
				])
				self.assertEqual(csv.row(), [
					'c',
					'd',
				])
				self.assertEqual(csv.raw(), [
					'c',
					'd',
				])
		return

	def test_lifetime_and_empty_record(self) -> None:
		self.path.write_bytes(b'\n')
		csv: CSV = CSV()
		self.assertIsNone(csv.raw())
		csv.close()
		for reopen in range(2):
			with self.subTest(reopen=reopen), csv.open(str(self.path)):
				self.assertIsNone(csv.raw())
				self.assertEqual(csv.row(), [])
				self.assertEqual(csv.raw(), [])
				csv.close()
				self.assertIsNone(csv.raw())
				csv.close()
			self.assertIsNone(csv.raw())
		with csv.open(str(self.path)):
			csv.row()
		self.assertIsNone(csv.raw())
		with self.assertRaises(RowError):
			with csv.open(str(self.path)):
				csv.row(row=RowValidator(Length(1)))
		self.assertIsNone(csv.raw())
		return

	def test_header_and_offset_are_excluded(self) -> None:
		self.path.write_bytes(b'name\nskipped\nvalue\n')
		csv: CSV = CSV(
			header=HeaderValidator(UpperHeader()),
			offset=1,
		)
		with csv.open(str(self.path)):
			self.assertEqual(csv.header(), ['NAME'])
			self.assertIsNone(csv.raw())
			self.assertEqual(csv.row(), ['value'])
			self.assertEqual(csv.raw(), ['value'])
			self.assertEqual(csv.header(), ['NAME'])
			self.assertEqual(csv.header(), ['NAME'])
			self.assertEqual(csv.raw(), ['value'])
		with CSV().open(str(self.path)) as csv:
			self.assertEqual(csv.row(), ['name'])
			self.assertEqual(csv.raw(), ['name'])
		with self.assertRaises(HeaderError):
			with csv.open(str(self.path), header=HeaderValidator(HeaderLength(2))):
				self.fail('Header must fail before entering the context')
		self.assertIsNone(csv.raw())
		return

	def test_empty_file_offset_and_zero_limit(self) -> None:
		for content, offset, limit in (
			(
				b'',
				0,
				None,
			),
			(
				b'a\n',
				2,
				None,
			),
			(
				b'"bad"x\n',
				1,
				0,
			),
		):
			self.path.write_bytes(content)
			with self.subTest(content=content, offset=offset, limit=limit):
				with CSV(offset=offset, limit=limit).open(str(self.path)) as csv:
					with self.assertRaises(StopIteration):
						csv.row()
					self.assertIsNone(csv.raw())
					self.assertEqual(list(csv.rows()), [])
					self.assertIsNone(csv.raw())
		return

	def test_last_record_retained_until_next_read(self) -> None:
		self.path.write_bytes(b'ok\n"bad"x\n')
		with CSV(limit=1).open(str(self.path)) as csv:
			records: Generator[List[str], None, None] = csv.rows()
			self.assertEqual(next(records), ['ok'])
			self.assertEqual(csv.raw(), ['ok'])
			with self.assertRaises(StopIteration):
				next(records)
			self.assertIsNone(csv.raw())
		self.path.write_bytes(b'ok\n')
		with CSV().open(str(self.path)) as csv:
			self.assertEqual(csv.row(), ['ok'])
			self.assertEqual(csv.raw(), ['ok'])
			with self.assertRaises(StopIteration):
				csv.row()
			self.assertIsNone(csv.raw())
		return

	def test_parse_failure_clears_previous_raw(self) -> None:
		self.path.write_bytes(b'ok\n"bad"x\nnext\n')
		for stream in (
			False,
			True,
		):
			with self.subTest(stream=stream), CSV(limit=2).open(str(self.path)) as csv:
				self.assertEqual(csv.row(), ['ok'])
				self.assertEqual(csv.raw(), ['ok'])
				with self.assertRaises(CSVError):
					if stream:
						next(csv.rows())
					else:
						csv.row()
				self.assertIsNone(csv.raw())
				self.assertEqual(csv.row(), ['next'])
				self.assertEqual(csv.raw(), ['next'])
				with self.assertRaises(StopIteration):
					csv.row()
				self.assertIsNone(csv.raw())
		return

	def test_decode_failure_clears_previous_raw_in_all_modes(self) -> None:
		# More than one decoder buffer ensures a successful read precedes failure.
		self.path.write_bytes(b'ok\n' * 16384 + b'\xff\n')
		for mode in (
			'rb',
			'r',
			'rt',
		):
			for stream in (
				False,
				True,
			):
				with self.subTest(mode=mode, stream=stream), CSV().open(str(self.path), mode) as csv:
					self.assertEqual(csv.row(), ['ok'])
					self.assertEqual(csv.raw(), ['ok'])
					with self.assertRaises(UnicodeDecodeError):
						if stream:
							for record in csv.rows():
								self.assertEqual(csv.raw(), record)
						else:
							while True:
								self.assertEqual(csv.row(), ['ok'])
								self.assertEqual(csv.raw(), ['ok'])
					self.assertIsNone(csv.raw())
		return

	def test_offset_parse_and_decode_errors_do_not_expose_skipped_records(self) -> None:
		for content, error in (
			(
				b'skipped\n"bad"x\n',
				CSVError,
			),
			(
				b'ok\n' * 16384 + b'\xff\n',
				UnicodeDecodeError,
			),
		):
			self.path.write_bytes(content)
			for stream in (
				False,
				True,
			):
				with self.subTest(error=error, stream=stream):
					with CSV(offset=20000).open(str(self.path)) as csv:
						with self.assertRaises(error):
							if stream:
								next(csv.rows())
							else:
								csv.row()
						self.assertIsNone(csv.raw())
		return

	def test_row_loop_resumes_and_failures_consume_limit(self) -> None:
		self.path.write_bytes(b'one\n   ,bad\nok,good\nunread,last\n')
		csv: CSV = CSV(
			row=RowValidator(Length(2)),
			column=(ColumnValidator(Strip(), Required()),),
			limit=3,
		)
		rejected: List[Optional[List[str]]] = []
		accepted: List[List[str]] = []
		with csv.open(str(self.path)):
			while True:
				try:
					accepted.append(csv.row())
				except StopIteration:
					break
				except (
					RowError,
					ColumnError,
				):
					rejected.append(csv.raw())
			self.assertIsNone(csv.raw())
		self.assertEqual(rejected, [
			['one'],
			[
				'   ',
				'bad',
			],
		])
		self.assertEqual(accepted, [[
			'ok',
			'good',
		]])
		return

	def test_rows_failure_keeps_raw_and_generator_stays_exhausted(self) -> None:
		for content, error in (
			(
				b'one\nok,good\n',
				RowError,
			),
			(
				b'   ,bad\nok,good\n',
				ColumnError,
			),
		):
			self.path.write_bytes(content)
			expected: List[str] = next(reader(StringIO(content.decode('utf-8'))))
			csv: CSV = CSV(
				row=RowValidator(Length(2)),
				column=(ColumnValidator(Strip(), Required()),),
			)
			with self.subTest(error=error), csv.open(str(self.path)):
				records: Generator[List[str], None, None] = csv.rows()
				with self.assertRaises(error):
					next(records)
				self.assertEqual(csv.raw(), expected)
				self.assertEqual(list(records), [])
				self.assertEqual(csv.raw(), expected)
				self.assertEqual(csv.row(), [
					'ok',
					'good',
				])
				self.assertEqual(csv.raw(), [
					'ok',
					'good',
				])
		return

	def test_mixed_reads_and_normal_generator_exhaustion(self) -> None:
		self.path.write_bytes(b'a\nb\nc\n')
		with CSV().open(str(self.path)) as csv:
			self.assertEqual(csv.row(), ['a'])
			records: Generator[List[str], None, None] = csv.rows()
			self.assertEqual(csv.raw(), ['a'])
			self.assertEqual(next(records), ['b'])
			self.assertEqual(csv.raw(), ['b'])
			self.assertEqual(csv.row(), ['c'])
			self.assertEqual(csv.raw(), ['c'])
			self.assertEqual(list(records), [])
			self.assertIsNone(csv.raw())
		with CSV().open(str(self.path)) as csv:
			for record in csv.rows():
				self.assertEqual(csv.raw(), record)
			self.assertIsNone(csv.raw())
		return

	def test_dialect_round_trip_preserves_fields(self) -> None:
		source: str = ' left\\\tright \t"line one\r\nline two"\t"say \\"hi\\" \\\\ end"\r\n'
		self.path.write_bytes(source.encode('utf-8'))
		csv: CSV = CSV(
			delimiter='\t',
			escapechar='\\',
			column=(ColumnValidator(Strip()),),
		)
		with csv.open(str(self.path)):
			clean: List[str] = csv.row()
			raw: Optional[List[str]] = csv.raw()
			assert raw is not None
			self.assertEqual(raw, [
				' left\tright ',
				'line one\r\nline two',
				'say "hi" \\ end',
			])
			self.assertNotEqual(clean, raw)
			output: StringIO = StringIO(newline='')
			writer(output, delimiter='\t', escapechar='\\').writerow(raw)
			output.seek(0)
			self.assertEqual(next(reader(output, delimiter='\t', escapechar='\\')), raw)
		return


if __name__ == '__main__':
	main()
