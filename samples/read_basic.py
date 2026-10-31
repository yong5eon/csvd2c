from pathlib import Path
from tempfile import TemporaryDirectory
from csvd2c import CSV


def main() -> None:
	"""
	Read a header, one record, and the remaining records without accumulation.
	"""
	with TemporaryDirectory() as directory:
		path: Path = Path(directory) / 'input.csv'
		path.write_text('name,date\nKim,1-10\nLee,23-Feb\n', encoding='utf-8')
		csv: CSV = CSV()
		with csv.open(str(path)):
			header: list[str] = csv.header()
			assert header == [
				'name',
				'date',
			]
			record: list[str] = csv.row()
			assert record == [
				'Kim',
				'1-10',
			]
			print('First:', record)
			for record in csv.rows():
				assert record == [
					'Lee',
					'23-Feb',
				]
				print('Remaining:', record)
			try:
				csv.row()
			except StopIteration:
				print('End of file')
			else:
				raise AssertionError('Expected EOF')
	return


if __name__ == '__main__':
	main()
