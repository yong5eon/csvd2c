from unittest import (
	TestCase,
	main,
)
from csvd2c.column import Validator
from csvd2c.column.patterns import (
	IfUndecodable,
	RejectSurrogates,
	TryRecoverEncoding,
)


class TryRecoverEncodingTests(TestCase):
	"""
	Verify candidate fallthrough and preservation of recovered text.
	"""

	def test_failed_candidate_then_success(self) -> None:
		value: str = '홍길동'.encode('cp949').decode('utf-8', errors='surrogateescape')
		self.assertEqual(TryRecoverEncoding('ascii')(value), value)
		self.assertEqual(
			Validator(
				IfUndecodable(
					TryRecoverEncoding('ascii'),
					TryRecoverEncoding('cp949'),
					TryRecoverEncoding('cp1258'),
				),
				RejectSurrogates(),
			)(value),
			'홍길동',
		)
		return

	def test_vietnamese(self) -> None:
		value: str = 'Công ty'.encode('cp1258').decode('utf-8', errors='surrogateescape')
		self.assertEqual(TryRecoverEncoding('cp1258')(value), 'Công ty')
		return

	def test_unchanged_and_unrecoverable(self) -> None:
		for value in (
			'normal',
			'홍길동',
			'\ufffd',
			'',
		):
			self.assertEqual(TryRecoverEncoding('cp1258')(value), value)
		self.assertEqual(TryRecoverEncoding('utf-8')('\udcff'), '\udcff')
		with self.assertRaises(ValueError):
			Validator(TryRecoverEncoding('utf-8'), RejectSurrogates())('\udcff')
		return

	def test_invalid_configuration(self) -> None:
		with self.assertRaises(LookupError):
			TryRecoverEncoding('unknown-encoding')
		return


if __name__ == '__main__':
	main()
