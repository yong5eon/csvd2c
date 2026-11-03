# -*- coding: utf-8 -*-

from typing import (
	List,
	Union,
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


class ColumnCheck(ColumnPattern):
	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		raise ColumnError('Rejected column', row, column, value)


class ConditionTests(TestCase):
	"""
	Test conditional corrections and raised row errors.
	"""

	def test_merge_and_boundaries(self) -> None:
		row = ['a', 'b', 'c', 'd']
		self.assertEqual(Merge(1, 3)(row, 1), ['a', 'b,c', 'd'])
		self.assertEqual(Merge(-3, -1, sep='|')(row, 1), ['a', 'b|c', 'd'])
		self.assertEqual(Merge(0, 4, sep='')(row, 1), ['abcd'])
		self.assertEqual(Merge(1, 2)(row, 1), row)
		self.assertEqual(row, ['a', 'b', 'c', 'd'])
		for start, stop in (
			(0, 0),
			(2, 1),
			(-5, 2),
			(0, 5),
		):
			with self.assertRaises(Error):
				Merge(start, stop)(row, 1)
		return

	def test_split(self) -> None:
		row = ['a', 'b,c,,d']
		self.assertEqual(Split(-1)(row, 1), ['a', 'b', 'c', '', 'd'])
		self.assertEqual(Split(1, maxsplit=1)(row, 1), ['a', 'b', 'c,,d'])
		self.assertEqual(Split(1, maxsplit=0)(row, 1), row)
		self.assertEqual(Split(0, sep=None)([' a  b '], 1), ['a', 'b'])
		self.assertEqual(row, ['a', 'b,c,,d'])
		with self.assertRaises(Error):
			Split(0)([], 1)
		return

	def test_replace(self) -> None:
		row = ['a', 'b']
		self.assertEqual(Replace(-1, 'x')(row, 1), ['a', 'x'])
		self.assertEqual(row, ['a', 'b'])
		with self.assertRaises(Error):
			Replace(2, 'x')(row, 1)
		return

	def test_conditional_composition(self) -> None:
		validator = Validator(
			IfLength(4, Merge(1, 3), Replace(0, 'fixed')),
			Length(3),
		)
		self.assertEqual(validator(['a', 'b', 'c', 'd'], 1), ['fixed', 'b,c', 'd'])
		self.assertEqual(validator(['a', 'b', 'c'], 1), ['a', 'b', 'c'])
		with self.assertRaises(Error):
			validator(['a'], 1)
		return

	def test_reject_empty_and_header(self) -> None:
		for row in (
			[],
			[''],
			['', ''],
		):
			with self.assertRaises(Error):
				RejectEmpty()(row, 1)
		for row in (
			[' '],
			['', 'a'],
		):
			self.assertIs(RejectEmpty()(row, 1), row)
		with self.assertRaises(Error):
			RejectHeader('a', 'b')(['a', 'b'], 1)
		self.assertEqual(RejectHeader('a', 'b')(['b', 'a'], 1), ['b', 'a'])
		return

	def test_errors_carry_row_context(self) -> None:
		for pattern in (
			Length(2),
			Remove(3),
			Reorder(1),
			Merge(0, 3),
			Split(2),
			Replace(2, 'x'),
			RejectEmpty(),
			RejectHeader(''),
			IfLength(1, Length(2)),
		):
			with self.subTest(pattern=pattern):
				row: List[str] = ['']
				with self.assertRaises(Error) as context:
					pattern(row, 5)
				self.assertNotIsInstance(context.exception, ValueError)
				self.assertEqual(context.exception.value, [''])
				self.assertEqual(context.exception.row, 5)
				self.assertTrue(context.exception.message)
				self.assertEqual(row, [''])
		with self.assertRaises(ColumnError) as context:
			ColumnCheck()('a', 2, 'name')
		self.assertEqual(context.exception.value, 'a')
		self.assertEqual(context.exception.row, 2)
		self.assertEqual(context.exception.column, 'name')
		return

	def test_configuration_errors_are_immediate(self) -> None:
		for factory in (
			lambda: Merge(True, 2),
			lambda: Split(0, sep=''),
			lambda: Replace(0, None),
			lambda: IfLength(-1),
			lambda: RejectHeader(1),
		):
			with self.assertRaises((TypeError, ValueError)):
				factory()
		return


if __name__ == '__main__':
	main()
