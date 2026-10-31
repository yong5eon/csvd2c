# -*- coding: utf-8 -*-

from typing import (
	List,
	Optional,
)
from unittest import (
	TestCase,
	main,
)
from csvd2c.row import (
	Error,
	Validator,
)
from csvd2c.column import (
	Error as ColumnError,
	Pattern as ColumnPattern,
)
from csvd2c.row.patterns import (
	IfLength,
	Length,
	Merge,
	RejectEmpty,
	RejectHeader,
	Remove,
	Reorder,
	Replace,
	Split,
)


class Recover(Error):
	"""
	Return explicit replacement data and track calls.
	"""

	def __init__(self) -> None:
		self.calls = 0
		return

	def __call__(self, row: List[str]) -> List[str]:
		self.calls += 1
		row[:] = ['recovered']
		return row


class Raise(Error):
	def __call__(self, row: List[str]) -> List[str]:
		raise RuntimeError('Handler failed')


class ColumnRecover(ColumnError):
	def __call__(self, col: str) -> str:
		return 'recovered'


class ColumnCheck(ColumnPattern):
	def __init__(self, *, error: Optional[ColumnError] = None) -> None:
		if error is not None and not isinstance(error, ColumnError):
			raise TypeError('error must be a column Error instance or None')
		self.error = error
		return

	def __call__(self, col: str) -> str:
		if self.error is not None:
			return self.error(col)
		raise ValueError('Rejected column')


class ConditionTests(TestCase):
	"""
	Test conditional corrections and explicit Error handling.
	"""

	def test_merge_and_boundaries(self) -> None:
		row = ['a', 'b', 'c', 'd']
		self.assertEqual(Merge(1, 3)(row), ['a', 'b,c', 'd'])
		self.assertEqual(Merge(-3, -1, sep='|')(row), ['a', 'b|c', 'd'])
		self.assertEqual(Merge(0, 4, sep='')(row), ['abcd'])
		self.assertEqual(Merge(1, 2)(row), row)
		self.assertEqual(row, ['a', 'b', 'c', 'd'])
		for start, stop in (
			(0, 0),
			(2, 1),
			(-5, 2),
			(0, 5),
		):
			with self.assertRaises(ValueError):
				Merge(start, stop)(row)
		return

	def test_split(self) -> None:
		row = ['a', 'b,c,,d']
		self.assertEqual(Split(-1)(row), ['a', 'b', 'c', '', 'd'])
		self.assertEqual(Split(1, maxsplit=1)(row), ['a', 'b', 'c,,d'])
		self.assertEqual(Split(1, maxsplit=0)(row), row)
		self.assertEqual(Split(0, sep=None)([' a  b ']), ['a', 'b'])
		self.assertEqual(row, ['a', 'b,c,,d'])
		with self.assertRaises(ValueError):
			Split(0)([])
		return

	def test_replace(self) -> None:
		row = ['a', 'b']
		self.assertEqual(Replace(-1, 'x')(row), ['a', 'x'])
		self.assertEqual(row, ['a', 'b'])
		with self.assertRaises(ValueError):
			Replace(2, 'x')(row)
		return

	def test_conditional_composition(self) -> None:
		validator = Validator(
			IfLength(4, Merge(1, 3), Replace(0, 'fixed')),
			Length(3),
		)
		self.assertEqual(validator(['a', 'b', 'c', 'd']), ['fixed', 'b,c', 'd'])
		self.assertEqual(validator(['a', 'b', 'c']), ['a', 'b', 'c'])
		with self.assertRaises(ValueError):
			validator(['a'])
		return

	def test_reject_empty_and_header(self) -> None:
		for row in (
			[],
			[''],
			['', ''],
		):
			with self.assertRaises(ValueError):
				RejectEmpty()(row)
		for row in (
			[' '],
			['', 'a'],
		):
			self.assertIs(RejectEmpty()(row), row)
		with self.assertRaises(ValueError):
			RejectHeader('a', 'b')(['a', 'b'])
		self.assertEqual(RejectHeader('a', 'b')(['b', 'a']), ['b', 'a'])
		return

	def test_error_handlers(self) -> None:
		handler = Recover()
		for pattern in (
			Length(2, error=handler),
			Remove(3, error=handler),
			Reorder(1, error=handler),
			Merge(0, 3, error=handler),
			Split(2, error=handler),
			Replace(2, 'x', error=handler),
			RejectEmpty(error=handler),
			RejectHeader('', error=handler),
			IfLength(1, Length(2), error=handler),
		):
			row = ['']
			self.assertEqual(pattern(row), ['recovered'])
			self.assertEqual(row, [''])
		self.assertEqual(handler.calls, 9)
		self.assertEqual(Length(1, error=handler)(['a']), ['a'])
		self.assertEqual(handler.calls, 9)
		with self.assertRaisesRegex(RuntimeError, 'Handler failed'):
			Length(2, error=Raise())(['a'])
		self.assertEqual(ColumnCheck(error=ColumnRecover())('a'), 'recovered')
		with self.assertRaises(ValueError):
			ColumnCheck()('a')
		return

	def test_configuration_errors_are_immediate(self) -> None:
		handler = Recover()
		for factory in (
			lambda: Merge(True, 2, error=handler),
			lambda: Split(0, sep='', error=handler),
			lambda: Replace(0, None, error=handler),
			lambda: IfLength(-1, error=handler),
			lambda: RejectHeader(1, error=handler),
		):
			with self.assertRaises((TypeError, ValueError)):
				factory()
		self.assertEqual(handler.calls, 0)
		with self.assertRaises(TypeError):
			Length(1, error=ColumnRecover())
		with self.assertRaises(TypeError):
			ColumnCheck(error=handler)
		return


if __name__ == '__main__':
	main()
