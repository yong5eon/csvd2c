# -*- coding: utf-8 -*-

from csv import (
	Error,
	reader as csv_reader,
)
from io import (
	BufferedReader,
	RawIOBase,
	StringIO,
)
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import (
	List,
	Optional,
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


class Strip(ColumnPattern):
	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		return value.strip()


class Upper(ColumnPattern):
	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		return value.upper()


class Reverse(RowPattern):
	def __call__(
		self,
		value: List[str],
		row: int,
	) -> List[str]:
		return list(reversed(value))


class Reject(ColumnPattern):
	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		raise ColumnError('Rejected value', row, column, value)


class Stop(ColumnPattern):
	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		raise StopIteration('Validator stopped')


class VirtualCSV(RawIOBase):
	"""
	Generate a virtual 200GiB CSV without allocating the file.
	"""

	def __init__(self) -> None:
		super().__init__()
		self.remaining = 200 * 1024 ** 3
		self.consumed = 0
		return

	def readable(self) -> bool:
		return True

	def readinto(self, buffer: bytearray) -> int:
		size: int = min(len(buffer), self.remaining)
		buffer[:size] = (b'x\n' * ((size + 1) // 2))[:size]
		self.remaining -= size
		self.consumed += size
		return size


class CSVTests(TestCase):
	"""
	Verify streaming, resource ownership, headers, and validation.
	"""

	def setUp(self) -> None:
		self.directory = TemporaryDirectory()
		self.addCleanup(self.directory.cleanup)
		self.path: Path = Path(self.directory.name) / 'input.csv'
		self.path.write_bytes(b'name,note\n a , b \nc,d\n')
		return

	def test_header_returns_stored_copy_without_consuming(self) -> None:
		csv = CSV(header=HeaderValidator())
		with csv.open(str(self.path)) as opened:
			self.assertIs(opened, csv)
			self.assertEqual(csv.header(), ['name', 'note'])
			self.assertEqual(csv.header(), ['name', 'note'])
			self.assertEqual(csv.row(), [' a ', ' b '])
			self.assertEqual(csv.row(), ['c', 'd'])
			self.assertEqual(csv.header(), ['name', 'note'])
		return

	def test_read_modes_preserve_decoding_and_csv_newlines(self) -> None:
		self.path.write_bytes('name,note\r\n홍길동,"a\r\nb"\r\n'.encode('cp949'))
		for mode in (
			'rb',
			'r',
			'rt',
		):
			with self.subTest(mode=mode):
				csv = CSV(
					encoding='cp949',
					header=HeaderValidator(),
				)
				with csv.open(str(self.path), mode):
					self.assertEqual(csv.row(), ['홍길동', 'a\r\nb'])
					csv.close()
				with self.assertRaises(RuntimeError):
					csv.row()
		return

	def test_escapechar_matches_standard_reader_in_all_read_modes(self) -> None:
		source: str = (
			'id\tvalue\n'
			'1\t"Acme \\"quoted\\" name"\n'
			'2\tleft\\\tright\n'
			'3\tback\\\\slash\n'
			'4\t"line one\nline two"\n'
		)
		self.path.write_bytes(source.encode('utf-8'))
		expected: List[List[str]] = list(
			csv_reader(
				StringIO(source, newline=''),
				delimiter='\t',
				escapechar='\\',
				strict=True,
			)
		)
		self.assertEqual(
			expected,
			[
				['id', 'value'],
				['1', 'Acme "quoted" name'],
				['2', 'left\tright'],
				['3', 'back\\slash'],
				['4', 'line one\nline two'],
			],
		)
		for mode in (
			'rb',
			'r',
			'rt',
		):
			with self.subTest(mode=mode):
				csv = CSV(
					delimiter='\t',
					escapechar='\\',
					strict=True,
					header=HeaderValidator(),
				)
				self.assertEqual(csv.escapechar, '\\')
				with csv.open(str(self.path), mode):
					self.assertEqual(csv.header(), expected[0])
					self.assertEqual(list(csv.rows()), expected[1:])
		return

	def test_escapechar_preserves_row_and_column_validation_order(self) -> None:
		self.path.write_bytes(b'1\t" Acme \\"quoted\\" "\n')
		csv = CSV(
			delimiter='\t',
			escapechar='\\',
			strict=True,
			row=RowValidator(Reverse()),
			column=(ColumnValidator(Strip()),),
		)
		with csv.open(str(self.path)):
			self.assertEqual(csv.row(), ['Acme "quoted"', '1'])
		return

	def test_escapechar_defaults_to_none_and_preserves_doublequote(self) -> None:
		self.path.write_bytes(b'id,name\n1,"Acme ""quoted"" name"\n')
		csv = CSV(header=HeaderValidator())
		self.assertIsNone(csv.escapechar)
		with csv.open(str(self.path)):
			self.assertEqual(csv.header(), ['id', 'name'])
			self.assertEqual(csv.row(), ['1', 'Acme "quoted" name'])
		return

	def test_invalid_escapechar_propagates_reader_error(self) -> None:
		csv = CSV(escapechar='xx')
		with self.assertRaises(TypeError):
			with csv.open(str(self.path)):
				self.fail('Invalid escapechar must be rejected')
		return

	def test_rejected_modes_do_not_modify_file(self) -> None:
		original: bytes = self.path.read_bytes()
		for mode in (
			'w',
			'wb',
			'a',
			'r+',
			'invalid',
		):
			with self.subTest(mode=mode):
				csv = CSV()
				with self.assertRaises(ValueError):
					with csv.open(str(self.path), mode):
						self.fail('Unsupported modes must fail')
				self.assertEqual(self.path.read_bytes(), original)
		return

	def test_stream_and_validation_order(self) -> None:
		csv = CSV(
			header=HeaderValidator(),
			row=RowValidator(Reverse()),
			column=(ColumnValidator(Strip()),),
		)
		with csv.open(str(self.path)):
			self.assertEqual(
				list(csv.rows()),
				[
					['b', ' a '],
					['d', 'c'],
				],
			)
		return

	def test_header_return_is_a_copy(self) -> None:
		csv = CSV(
			header=HeaderValidator(),
			column={'name': ColumnValidator(Strip())},
		)
		with csv.open(str(self.path)):
			header: Optional[List[str]] = csv.header()
			assert header is not None
			header[0] = 'changed'
			self.assertEqual(csv.header(), ['name', 'note'])
			self.assertEqual(csv.row(), ['a', ' b '])
		return

	def test_rows_and_row_share_position(self) -> None:
		csv = CSV(header=HeaderValidator())
		with csv.open(str(self.path)):
			self.assertEqual(csv.row(), [' a ', ' b '])
			self.assertEqual(list(csv.rows()), [['c', 'd']])
			self.assertEqual(list(csv.rows()), [])
			with self.assertRaises(StopIteration):
				csv.row()
		return

	def test_open_does_not_consume_header(self) -> None:
		csv = CSV()
		with csv.open(str(self.path)):
			self.assertEqual(csv.row(), ['name', 'note'])
		return

	def test_named_columns_require_header(self) -> None:
		csv = CSV(column={'name': ColumnValidator(Strip())})
		with csv.open(str(self.path)):
			self.assertIsNone(csv.header())
			with self.assertRaisesRegex(RuntimeError, 'Inject a header Validator'):
				csv.rows()
			with self.assertRaisesRegex(RuntimeError, 'Inject a header Validator'):
				csv.row()
			self.assertEqual(csv.row(column=()), ['name', 'note'])
		with csv.open(str(self.path), header=HeaderValidator()):
			self.assertEqual(csv.row(), ['a', ' b '])
		return

	def test_missing_and_duplicate_header_names(self) -> None:
		for header in (
			b'other,note\n',
			b'name,name\n',
		):
			with self.subTest(header=header):
				self.path.write_bytes(header + b'a,b\n')
				csv = CSV(
					header=HeaderValidator(),
					column={'name': ColumnValidator(Strip())},
				)
				with csv.open(str(self.path)):
					with self.assertRaisesRegex(ValueError, 'exactly once'):
						csv.row()
		return

	def test_tuple_only_validates_prefix(self) -> None:
		csv = CSV(
			header=HeaderValidator(),
			column=(ColumnValidator(Strip()),),
		)
		with csv.open(str(self.path)):
			self.assertEqual(csv.row(), ['a', ' b '])
		return

	def test_row_runs_before_columns(self) -> None:
		csv = CSV(
			header=HeaderValidator(),
			row=RowValidator(Reverse()),
			column=(ColumnValidator(Strip(), Upper()),),
		)
		with csv.open(str(self.path)):
			self.assertEqual(csv.row(), ['B', ' a '])
		return

	def test_row_overrides_do_not_change_defaults(self) -> None:
		csv = CSV(
			header=HeaderValidator(),
			row=RowValidator(Reverse()),
		)
		with csv.open(str(self.path)):
			self.assertEqual(csv.row(row=RowValidator()), [' a ', ' b '])
			self.assertEqual(csv.row(), ['d', 'c'])
		return

	def test_column_overrides_and_none_use_defaults(self) -> None:
		csv = CSV(
			header=HeaderValidator(),
			column=(ColumnValidator(Upper()),),
		)
		with csv.open(str(self.path)):
			self.assertEqual(
				csv.row(column=(ColumnValidator(Strip()),)),
				['a', ' b '],
			)
			self.assertEqual(csv.row(column=None), ['C', 'd'])
		return

	def test_rows_overrides_and_constructor_unchanged(self) -> None:
		csv = CSV(
			header=HeaderValidator(),
			row=RowValidator(Reverse()),
			column=(ColumnValidator(Upper()),),
		)
		with csv.open(str(self.path)):
			rows = csv.rows(row=RowValidator(), column=(ColumnValidator(Strip()),))
			self.assertEqual(next(rows), ['a', ' b '])
			rows.close()
			self.assertEqual(csv.row(), ['D', 'c'])
		return

	def test_missing_column_after_row_validation(self) -> None:
		self.path.write_bytes(b'a\nb,c\n')
		csv = CSV(column=(ColumnValidator(), ColumnValidator()))
		with csv.open(str(self.path)):
			with self.assertRaisesRegex(RowError, 'index 1') as context:
				csv.row()
			self.assertEqual(context.exception.row, 1)
			self.assertEqual(context.exception.value, ['a'])
			self.assertEqual(csv.row(), ['b', 'c'])
		return

	def test_column_count_not_implicitly_enforced(self) -> None:
		self.path.write_bytes(b'a,b\nx,y,z\n')
		csv = CSV(header=HeaderValidator())
		with csv.open(str(self.path)):
			self.assertEqual(csv.row(), ['x', 'y', 'z'])
		return

	def test_validator_errors_propagate(self) -> None:
		csv = CSV(column=(ColumnValidator(Reject()),))
		with csv.open(str(self.path)):
			with self.assertRaisesRegex(ColumnError, 'Rejected value'):
				next(csv.rows())
		return

	def test_validator_stop_iteration_is_not_eof(self) -> None:
		csv = CSV(column=(ColumnValidator(Stop()),))
		with csv.open(str(self.path)):
			with self.assertRaisesRegex(RuntimeError, 'generator raised StopIteration'):
				next(csv.rows())
		return

	def test_empty_file(self) -> None:
		self.path.write_bytes(b'')
		csv = CSV()
		with csv.open(str(self.path)):
			self.assertEqual(list(csv.rows()), [])
			with self.assertRaises(StopIteration):
				csv.row()
		return

	def test_tsv_quotes_and_embedded_newline(self) -> None:
		self.path.write_bytes(
			'name\tnote\r\nKim\t"a\tb\r\nc"\r\n'.encode('utf-8-sig')
		)
		csv = CSV(
			encoding='utf-8-sig',
			delimiter='\t',
			header=HeaderValidator(),
		)
		with csv.open(str(self.path)):
			self.assertEqual(csv.header(), ['name', 'note'])
			self.assertEqual(csv.row(), ['Kim', 'a\tb\r\nc'])
		return

	def test_cp949(self) -> None:
		self.path.write_bytes('이름\n홍길동\n'.encode('cp949'))
		csv = CSV(
			encoding='cp949',
			header=HeaderValidator(),
		)
		with csv.open(str(self.path)):
			self.assertEqual(csv.header(), ['이름'])
			self.assertEqual(csv.row(), ['홍길동'])
		return

	def test_strict_decode_and_surrogateescape(self) -> None:
		self.path.write_bytes(b'name\nx\xff\n')
		csv = CSV(errors='strict')
		with csv.open(str(self.path)):
			with self.assertRaises(UnicodeDecodeError):
				csv.row()
		csv = CSV(errors='surrogateescape')
		with csv.open(str(self.path), header=HeaderValidator()):
			record: List[str] = csv.row()
			self.assertEqual(
				record[0].encode('utf-8', errors='surrogateescape'),
				b'x\xff',
			)
		return

	def test_parse_error_propagates(self) -> None:
		self.path.write_bytes(b'name\n"unterminated\n')
		csv = CSV(header=HeaderValidator())
		with csv.open(str(self.path)):
			with self.assertRaises(Error):
				csv.row()
		return

	def test_read_without_open(self) -> None:
		csv = CSV(header=HeaderValidator())
		self.assertIsNone(csv.header())
		for read in (
			csv.row,
			csv.rows,
		):
			with self.assertRaises(RuntimeError):
				read()
		return

	def test_nested_open_rejected_and_reopen_allowed(self) -> None:
		csv = CSV()
		with csv.open(str(self.path)):
			with self.assertRaises(RuntimeError):
				with csv.open(str(self.path)):
					self.fail('Nested open must fail')
			self.assertEqual(csv.row(), ['name', 'note'])
		with csv.open(str(self.path)):
			self.assertEqual(csv.row(), ['name', 'note'])
		return

	def test_context_closes_file_on_exception(self) -> None:
		binary = open(self.path, 'rb')
		csv = CSV()
		with patch('builtins.open', return_value=binary):
			with self.assertRaisesRegex(ValueError, 'body failure'):
				with csv.open(str(self.path)):
					raise ValueError('body failure')
		self.assertTrue(binary.closed)
		with self.assertRaises(RuntimeError):
			csv.row()
		return

	def test_explicit_close_invalidates_reads_and_is_idempotent(self) -> None:
		csv = CSV()
		csv.close()
		binary = open(self.path, 'rb')
		with patch('builtins.open', return_value=binary):
			with csv.open(str(self.path), header=HeaderValidator()):
				self.assertEqual(csv.header(), ['name', 'note'])
				rows = csv.rows()
				csv.close()
				self.assertTrue(binary.closed)
				self.assertIsNone(csv.header_data)
				self.assertIsNone(csv.header())
				csv.close()
				with self.assertRaises(RuntimeError):
					csv.row()
				with self.assertRaises(RuntimeError):
					next(rows)
		with csv.open(str(self.path)):
			self.assertEqual(csv.row(), ['name', 'note'])
		return

	def test_old_context_does_not_close_reopened_stream(self) -> None:
		csv = CSV()
		old = csv.open(str(self.path))
		old.__enter__()
		csv.close()
		with csv.open(str(self.path)):
			old.__exit__(None, None, None)
			self.assertEqual(csv.row(), ['name', 'note'])
		return

	def test_stale_iterator_after_close_or_reopen(self) -> None:
		csv = CSV()
		with csv.open(str(self.path)):
			rows = csv.rows()
		with self.assertRaises(RuntimeError):
			next(rows)
		with csv.open(str(self.path)):
			rows = csv.rows()
		with csv.open(str(self.path)):
			with self.assertRaises(RuntimeError):
				next(rows)
			self.assertEqual(csv.row(), ['name', 'note'])
		return

	def test_header_read_does_not_invalidate_iterator(self) -> None:
		csv = CSV(header=HeaderValidator())
		with csv.open(str(self.path)):
			rows = csv.rows()
			self.assertEqual(csv.header(), ['name', 'note'])
			self.assertEqual(next(rows), [' a ', ' b '])
		return

	def test_invalid_configuration(self) -> None:
		with self.assertRaises(TypeError):
			CSV(column=[])  # type: ignore[arg-type]
		with self.assertRaises(TypeError):
			CSV(row=ColumnValidator())  # type: ignore[arg-type]
		csv = CSV(delimiter='invalid')
		with self.assertRaises(TypeError):
			with csv.open(str(self.path)):
				self.fail('Invalid delimiter must fail')
		return

	def test_virtual_200gib_stream_reads_only_a_buffer(self) -> None:
		raw = VirtualCSV()
		binary = BufferedReader(raw)
		csv = CSV()
		with patch('builtins.open', return_value=binary):
			with csv.open(str(self.path)):
				rows = csv.rows()
				self.assertEqual(raw.consumed, 0)
				for index in range(10):
					self.assertEqual(next(rows), ['x'])
				self.assertLessEqual(raw.consumed, 64 * 1024)
		self.assertTrue(raw.closed)
		return


if __name__ == '__main__':
	main()
