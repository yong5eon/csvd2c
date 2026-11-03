# -*- coding: utf-8 -*-

from pathlib import Path
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
	IfUndecodable,
	RecoverEncoding,
	RejectReplacementCharacter,
	RejectSurrogates,
	Upper,
)


class EncodingRecoveryTests(TestCase):
	"""
	Verify byte preservation, conditional recovery, and streaming integration.
	"""

	def test_cp1258_recovery(self) -> None:
		original: str = 'Công ty'
		raw: bytes = original.encode('cp1258')
		col: str = raw.decode('utf-8', errors='surrogateescape')
		self.assertEqual(RecoverEncoding('cp1258')(col, 1, 0), original)
		self.assertEqual(
			Validator(
				IfUndecodable(RecoverEncoding('cp1258')),
				RejectSurrogates(),
			)(col, 1, 0),
			original,
		)
		return

	def test_cp949_and_read_encoding_override(self) -> None:
		raw: bytes = '홍길동'.encode('cp949')
		col: str = raw.decode('utf-8', errors='surrogateescape')
		self.assertEqual(RecoverEncoding('cp949')(col, 1, 0), '홍길동')
		utf8: bytes = 'Công ty'.encode('utf-8')
		col = utf8.decode('ascii', errors='surrogateescape')
		self.assertEqual(
			RecoverEncoding('utf-8', read_encoding='ascii')(col, 1, 0),
			'Công ty',
		)
		return

	def test_valid_multibyte_sequences_are_preserved_before_recovery(self) -> None:
		raw: bytes = b'\xc3\xa9\xff'
		col: str = raw.decode('utf-8', errors='surrogateescape')
		self.assertEqual(col.encode('utf-8', errors='surrogateescape'), raw)
		self.assertEqual(RecoverEncoding('latin-1')(col, 1, 0), raw.decode('latin-1'))
		return

	def test_condition_boundaries_and_pass_through(self) -> None:
		pattern = IfUndecodable(Upper())
		for value in (
			'normal',
			'Công ty',
			'',
			'\ufffd',
			'\ud800',
			'\udc7f',
			'\udd00',
		):
			self.assertEqual(pattern(value, 1, 0), value)
		for marker in (
			'\udc80',
			'\udcff',
		):
			self.assertEqual(pattern('a' + marker, 1, 0), 'A' + marker)
		return

	def test_replacement_characters_are_not_repaired(self) -> None:
		self.assertEqual(RecoverEncoding('utf-8')('\ufffd', 1, 0), '\ufffd')
		with self.assertRaises(Error):
			Validator(
				IfUndecodable(RecoverEncoding('cp1258')),
				RejectReplacementCharacter(),
			)('\ufffd', 1, 0)
		return

	def test_failures_raise_column_error(self) -> None:
		for value in (
			'\udcff',
			'\ud800',
		):
			with self.assertRaises(Error) as context:
				RecoverEncoding('utf-8')(value, 4, 'description')
			self.assertEqual(context.exception.value, value)
			self.assertEqual(context.exception.row, 4)
			self.assertEqual(context.exception.column, 'description')
		with self.assertRaises(Error) as context:
			IfUndecodable(RecoverEncoding('utf-8'))('\udcff', 1, 0)
		self.assertEqual(context.exception.value, '\udcff')
		return

	def test_configuration_errors(self) -> None:
		with self.assertRaises(LookupError):
			RecoverEncoding('unknown-encoding')
		with self.assertRaises(RuntimeError):
			IfUndecodable('invalid')
		return

	def test_mixed_records_and_utf8_output(self) -> None:
		with TemporaryDirectory() as directory:
			path: Path = Path(directory) / 'input.csv'
			path.write_bytes(
				b'id,description\n'
				+ '1,Công ty\n'.encode('cp1258')
				+ '2,Công ty\n'.encode('utf-8')
			)
			csv = CSV(
				encoding='utf-8',
				errors='surrogateescape',
				cols={
					'description': Validator(
						IfUndecodable(RecoverEncoding('cp1258')),
						RejectSurrogates(),
					),
				},
			)
			with csv.open(str(path)):
				header = csv.header()
				result = list(csv.rows(header=header))
			self.assertEqual(
				result,
				[
					{'id': '1', 'description': 'Công ty'},
					{'id': '2', 'description': 'Công ty'},
				],
			)
			self.assertEqual(result[0]['description'].encode('utf-8'), 'Công ty'.encode('utf-8'))
		return


if __name__ == '__main__':
	main()
