# -*- coding: utf-8 -*-

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import (
	TestCase,
	main,
)

from csvd2c import CSV
from csvd2c.row import Validator
from csvd2c.row.patterns import (
	Insert,
	Length,
	Pad,
	Remove,
	Reorder,
	Slice,
	Truncate,
)


class RowPatternTests(TestCase):
	"""
	Verify row structure rules, boundaries, composition, and input preservation.
	"""

	def test_length(self) -> None:
		for row in (
			[],
			['a'],
			['a', 'b'],
		):
			self.assertIs(Length(len(row))(row), row)
			with self.assertRaises(ValueError):
				Length(len(row) + 1)(row)
		with self.assertRaises(ValueError):
			Length(-1)
		with self.assertRaises(TypeError):
			Length(True)
		return

	def test_insert_matches_python_and_preserves_input(self) -> None:
		for index in (
			-100,
			-1,
			0,
			1,
			100,
		):
			for row in (
				[],
				['a', 'b'],
			):
				original = row.copy()
				expected = row.copy()
				expected.insert(index, 'x')
				actual = Insert(index, 'x')(row)
				self.assertEqual(actual, expected)
				self.assertEqual(row, original)
				self.assertIsNot(actual, row)
		return

	def test_remove_matches_python_and_preserves_input(self) -> None:
		for index in (
			-2,
			-1,
			0,
			1,
		):
			row = ['a', 'b']
			expected = row.copy()
			expected.pop(index)
			self.assertEqual(Remove(index)(row), expected)
			self.assertEqual(row, ['a', 'b'])
		for index in (
			-3,
			2,
		):
			with self.assertRaises(ValueError):
				Remove(index)(['a', 'b'])
		with self.assertRaises(ValueError):
			Remove(0)([])
		return

	def test_reorder(self) -> None:
		row = ['a', 'b', 'c']
		self.assertEqual(Reorder(2, 0, 1)(row), ['c', 'a', 'b'])
		self.assertEqual(Reorder(-1, -3, -2)(row), ['c', 'a', 'b'])
		self.assertEqual(row, ['a', 'b', 'c'])
		self.assertEqual(Reorder()([]), [])
		for pattern in (
			Reorder(0, 1),
			Reorder(0, 1, 1),
			Reorder(0, 1, -2),
		):
			with self.assertRaises(ValueError):
				pattern(row)
		for pattern in (
			Reorder(0, 1, 3),
			Reorder(0, 1, -4),
		):
			with self.assertRaises(ValueError):
				pattern(row)
		return

	def test_slice_matches_python_and_preserves_input(self) -> None:
		row = ['a', 'b', 'c']
		for bounds in (
			(None, None, None),
			(1, 3, None),
			(-2, None, None),
			(-100, 100, 2),
			(None, None, -1),
			(2, 1, None),
		):
			actual = Slice(*bounds)(row)
			self.assertEqual(actual, row[slice(*bounds)])
			self.assertIsNot(actual, row)
			self.assertEqual(row, ['a', 'b', 'c'])
		self.assertEqual(Slice()([]), [])
		with self.assertRaises(ValueError):
			Slice(step=0)
		return

	def test_invalid_configuration(self) -> None:
		for factory in (
			lambda: Insert(True, 'x'),
			lambda: Insert(0, 1),
			lambda: Remove('0'),
			lambda: Reorder(0, '1'),
			lambda: Slice(start='0'),
			lambda: Slice(step=True),
		):
			with self.assertRaises(TypeError):
				factory()
		return

	def test_truncate_boundaries_and_input_preservation(self) -> None:
		for row in (
			[],
			['a'],
			['a', 'b'],
			['a', 'b', 'c'],
		):
			for count in (
				0,
				2,
				4,
			):
				with self.subTest(row=row, count=count):
					original = row.copy()
					actual = Truncate(count)(row)
					self.assertEqual(actual, row[:count])
					self.assertEqual(row, original)
					self.assertIsNot(actual, row)
		return

	def test_pad_boundaries_and_input_preservation(self) -> None:
		for row in (
			[],
			['a'],
			['a', 'b'],
			['a', 'b', 'c'],
		):
			for count in (
				0,
				2,
				4,
			):
				for value in (
					'',
					'missing',
				):
					with self.subTest(row=row, count=count, value=value):
						original = row.copy()
						actual = Pad(count, value)(row)
						self.assertEqual(
							actual,
							row + [value] * max(0, count - len(row)),
						)
						self.assertEqual(row, original)
						self.assertIsNot(actual, row)
		self.assertEqual(Pad(2)(['a']), ['a', ''])
		return

	def test_truncate_and_pad_invalid_configuration(self) -> None:
		for factory in (
			Truncate,
			Pad,
		):
			with self.assertRaises(ValueError):
				factory(-1)
			for count in (
				True,
				1.5,
				'2',
			):
				with self.assertRaises(TypeError):
					factory(count)
		with self.assertRaises(TypeError):
			Pad(2, None)
		return

	def test_truncate_pad_length_composition_in_csv(self) -> None:
		with TemporaryDirectory() as directory:
			path = Path(directory) / 'input.csv'
			path.write_text(
				'name,date\nKim,1-10,extra\nLee\nPark,23-Feb\n',
				encoding='utf-8',
			)
			csv = CSV(row=Validator(Truncate(2), Pad(2), Length(2)))
			with csv.open(str(path)):
				header = csv.header()
				self.assertEqual(
					list(csv.rows(header=header)),
					[
						{'name': 'Kim', 'date': '1-10'},
						{'name': 'Lee', 'date': ''},
						{'name': 'Park', 'date': '23-Feb'},
					],
				)
		return

	def test_composition(self) -> None:
		row = ['b', 'unused', 'a']
		validator = Validator(
			Length(3),
			Remove(1),
			Reorder(1, 0),
			Insert(2, 'c'),
			Slice(0, 2),
			Length(2),
		)
		self.assertEqual(validator(row), ['a', 'b'])
		self.assertEqual(row, ['b', 'unused', 'a'])
		return

	def test_csv_dictionary_output_after_structure_correction(self) -> None:
		with TemporaryDirectory() as directory:
			path = Path(directory) / 'input.csv'
			path.write_text('name,date\nKim,unused,1-10\n', encoding='utf-8')
			csv = CSV(row=Validator(Remove(1), Length(2)))
			with csv.open(str(path)):
				header = csv.header()
				self.assertEqual(
					csv.row(header=header),
					{'name': 'Kim', 'date': '1-10'},
				)
		return

	def test_representations(self) -> None:
		self.assertEqual(repr(Length(2)), 'Length(2)')
		self.assertEqual(repr(Insert(1, 'x')), "Insert(1, 'x')")
		self.assertEqual(repr(Remove(-1)), 'Remove(-1)')
		self.assertEqual(repr(Reorder(1, 0)), 'Reorder(1, 0)')
		self.assertEqual(repr(Slice()), 'Slice(None, None, None)')
		self.assertEqual(repr(Truncate(2)), 'Truncate(2)')
		self.assertEqual(repr(Pad(2)), "Pad(2, '')")
		self.assertEqual(repr(Pad(2, 'missing')), "Pad(2, 'missing')")
		return


if __name__ == '__main__':
	main()
