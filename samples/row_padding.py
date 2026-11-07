from pathlib import Path
from tempfile import TemporaryDirectory
from typing import (
	Iterator,
)
from csvd2c import CSV
from csvd2c.header import Validator as HeaderValidator
from csvd2c.row import Validator
from csvd2c.row.patterns import (
	Length,
	Pad,
	Truncate,
)


def main() -> None:
	"""
	Apply an explicit trailing-only truncation and padding policy.
	"""
	with TemporaryDirectory() as directory:
		path: Path = Path(directory) / 'input.csv'
		path.write_text('name,date\nKim,1-10,extra\nLee\nPark,23-Feb\n', encoding='utf-8')
		csv: CSV = CSV(
			header=HeaderValidator(),
			row=Validator(Truncate(2), Pad(2), Length(2)),
		)
		expected: Iterator[dict[str, str]] = iter((
			{
				'name': 'Kim',
				'date': '1-10',
			},
			{
				'name': 'Lee',
				'date': '',
			},
			{
				'name': 'Park',
				'date': '23-Feb',
			},
		))
		with csv.open(str(path)):
			for values in csv.rows():
				record: dict[str, str] = dict(values)
				assert record == next(expected)
				print(record)
		assert Pad(3, 'missing')(['a'], 1) == [
			'a',
			'missing',
			'missing',
		]
		print('Only use this policy when extra or missing columns are at the end')
	return


if __name__ == '__main__':
	main()
