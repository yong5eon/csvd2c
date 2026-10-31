# -*- coding: utf-8 -*-

from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import (
	TestCase,
	main,
)
from unittest.mock import patch

from csvd2c import detect_encoding


class EncodingTests(TestCase):
	"""
	Verify candidate priority, decoding errors, and bounded reads.
	"""

	def setUp(self) -> None:
		self.directory = TemporaryDirectory()
		self.addCleanup(self.directory.cleanup)
		self.path: Path = Path(self.directory.name) / 'input.csv'
		return

	def test_utf8(self) -> None:
		self.path.write_bytes('이름,날짜\n홍길동,1-10\n'.encode('utf-8'))
		self.assertEqual(detect_encoding(str(self.path), 'utf-8'), 'utf-8')
		return

	def test_cp949_after_utf8_failure(self) -> None:
		self.path.write_bytes('이름,날짜\n홍길동,1-10\n'.encode('cp949'))
		self.assertEqual(
			detect_encoding(str(self.path), 'utf-8', 'cp949'),
			'cp949',
		)
		return

	def test_first_success_wins(self) -> None:
		self.path.write_bytes(b'name,date\n')
		for candidates in (
			('utf-8', 'cp949'),
			('cp949', 'utf-8'),
		):
			with self.subTest(candidates=candidates):
				self.assertEqual(
					detect_encoding(str(self.path), *candidates),
					candidates[0],
				)
		return

	def test_bom_does_not_select_encoding(self) -> None:
		self.path.write_bytes('이름\n'.encode('utf-8-sig'))
		self.assertEqual(
			detect_encoding(str(self.path), 'utf-8', 'utf-8-sig'),
			'utf-8',
		)
		self.assertEqual(
			detect_encoding(str(self.path), 'utf-8-sig', 'utf-8'),
			'utf-8-sig',
		)
		return

	def test_no_candidates(self) -> None:
		with self.assertRaisesRegex(ValueError, 'encoding candidate is required'):
			detect_encoding(str(self.path))
		return

	def test_empty_file(self) -> None:
		self.path.write_bytes(b'')
		with self.assertRaisesRegex(ValueError, 'empty file'):
			detect_encoding(str(self.path), 'utf-8')
		return

	def test_unknown_candidate_is_not_hidden(self) -> None:
		self.path.write_bytes(b'name\n')
		with self.assertRaises(LookupError):
			detect_encoding(str(self.path), 'utf-8', 'unknown-encoding')
		return

	def test_missing_file(self) -> None:
		with self.assertRaises(FileNotFoundError):
			detect_encoding(str(self.path), 'utf-8')
		return

	def test_all_candidates_fail(self) -> None:
		self.path.write_bytes(b'\xff')
		with self.assertRaisesRegex(ValueError, 'utf-8.*cp949'):
			detect_encoding(str(self.path), 'utf-8', 'cp949')
		return

	def test_incomplete_character_at_end(self) -> None:
		for encoding in (
			'utf-8',
			'cp949',
		):
			with self.subTest(encoding=encoding):
				self.path.write_bytes('가'.encode(encoding)[:-1])
				with self.assertRaises(ValueError):
					detect_encoding(str(self.path), encoding)
		return

	def test_incomplete_character_at_sample_boundary(self) -> None:
		for encoding in (
			'utf-8',
			'cp949',
		):
			with self.subTest(encoding=encoding):
				self.path.write_bytes(
					b'a' * (1024 * 1024 - 1) + '가'.encode(encoding)
				)
				self.assertEqual(
					detect_encoding(str(self.path), encoding),
					encoding,
				)
		return

	def test_exact_sample_size_checks_end(self) -> None:
		self.path.write_bytes(b'a' * (1024 * 1024 - 1) + b'\xc3')
		with self.assertRaises(ValueError):
			detect_encoding(str(self.path), 'utf-8')
		return

	def test_bounded_read_and_invalid_data_after_sample(self) -> None:
		sample_size = 1024 * 1024
		stream = BytesIO(b'a' * sample_size + b'\xff')
		with patch('builtins.open', return_value=stream) as open_file:
			with patch.object(stream, 'read', wraps=stream.read) as read:
				self.assertEqual(
					detect_encoding(str(self.path), 'utf-8'),
					'utf-8',
				)
				read.assert_called_once_with(sample_size + 1)
			open_file.assert_called_once_with(str(self.path), 'rb')
		return


if __name__ == '__main__':
	main()
