from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List
from csvd2c import CSV
from csvd2c.header import Validator as HeaderValidator
from csvd2c.column import (
	Error as ColumnError,
	Validator as ColumnValidator,
)
from csvd2c.column.patterns import Required


def main() -> None:
	"""
	Read pages of records with offset and limit, counting rejected records toward the limit.
	"""
	with TemporaryDirectory() as directory:
		path: Path = Path(directory) / 'input.csv'
		path.write_bytes(b'id,name\n1,Kim\n2,"Lee\nJr."\n3,\n4,Park\n5,Choi\n')
		csv: CSV = CSV(
			header=HeaderValidator(),
			column={'name': ColumnValidator(Required())},
			limit=2,
		)
		pages: List[List[List[str]]] = []
		for offset in (
			0,
			2,
			4,
		):
			with csv.open(str(path), offset=offset):
				page: List[List[str]] = []
				while True:
					try:
						page.append(csv.row())
					except StopIteration:
						break
					except ColumnError as error:
						print('Rejected at line', error.row, 'but counted toward the limit')
				print('Page from offset', offset, ':', page)
				pages.append(page)
		assert pages == [
			[
				['1', 'Kim'],
				['2', 'Lee\nJr.'],
			],
			[
				['4', 'Park'],
			],
			[
				['5', 'Choi'],
			],
		]
		with csv.open(str(path), offset=1, limit=0):
			assert list(csv.rows()) == []
		with CSV().open(str(path), limit=1) as raw:
			first: List[str] = raw.row()
			assert first == ['id', 'name']
			print('Without a header Validator, position 0 is the header line:', first)
	return


if __name__ == '__main__':
	main()
