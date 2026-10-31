# -*- coding: utf-8 -*-

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List
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


class Recover(Error):
	def __init__(self) -> None:
		self.values: List[str] = []
		return

	def __call__(self, col: str) -> str:
		self.values.append(col)
		return 'replacement'


class Fail(Error):
	def __call__(self, col: str) -> str:
		raise RuntimeError('Handler failure')


class EncodingRecoveryTests(TestCase):
	"""
	Verify byte preservation, conditional recovery, and streaming integration.
	"""

	def test_cp1258_recovery(self) -> None:
		original: str = 'Công ty'
		raw: bytes = original.encode('cp1258')
		col: str = raw.decode('utf-8', errors='surrogateescape')
		self.assertEqual(RecoverEncoding('cp1258')(col), original)
		self.assertEqual(
			Validator(
				IfUndecodable(RecoverEncoding('cp1258')),
				RejectSurrogates(),
			)(col),
			original,
		)
		return

	def test_cp949_and_read_encoding_override(self) -> None:
		raw: bytes = '홍길동'.encode('cp949')
		col: str = raw.decode('utf-8', errors='surrogateescape')
		self.assertEqual(RecoverEncoding('cp949')(col), '홍길동')
		utf8: bytes = 'Công ty'.encode('utf-8')
		col = utf8.decode('ascii', errors='surrogateescape')
		self.assertEqual(
			RecoverEncoding('utf-8', read_encoding='ascii')(col),
			'Công ty',
		)
		return

	def test_valid_multibyte_sequences_are_preserved_before_recovery(self) -> None:
		raw: bytes = b'\xc3\xa9\xff'
		col: str = raw.decode('utf-8', errors='surrogateescape')
		self.assertEqual(col.encode('utf-8', errors='surrogateescape'), raw)
		self.assertEqual(RecoverEncoding('latin-1')(col), raw.decode('latin-1'))
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
			self.assertEqual(pattern(value), value)
		for marker in (
			'\udc80',
			'\udcff',
		):
			self.assertEqual(pattern('a' + marker), 'A' + marker)
		return

	def test_replacement_characters_are_not_repaired(self) -> None:
		self.assertEqual(RecoverEncoding('utf-8')('\ufffd'), '\ufffd')
		with self.assertRaises(ValueError):
			Validator(
				IfUndecodable(RecoverEncoding('cp1258')),
				RejectReplacementCharacter(),
			)('\ufffd')
		return

	def test_failures_and_handlers(self) -> None:
		handler = Recover()
		for value in (
			'\udcff',
			'\ud800',
		):
			with self.assertRaises(ValueError):
				RecoverEncoding('utf-8')(value)
			self.assertEqual(
				RecoverEncoding('utf-8', error=handler)(value),
				'replacement',
			)
		self.assertEqual(handler.values, ['\udcff', '\ud800'])
		with self.assertRaisesRegex(RuntimeError, 'Handler failure'):
			IfUndecodable(RecoverEncoding('utf-8', error=Fail()))('\udcff')
		with self.assertRaises(ValueError):
			IfUndecodable(RecoverEncoding('utf-8'))('\udcff')
		return

	def test_configuration_errors(self) -> None:
		with self.assertRaises(LookupError):
			RecoverEncoding('unknown-encoding')
		with self.assertRaises(TypeError):
			RecoverEncoding('utf-8', error='invalid')
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
