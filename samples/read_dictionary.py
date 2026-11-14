from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional
from csvd2c import CSV
from csvd2c.header import Validator as HeaderValidator


def main() -> None:
	"""
	Read mapping records from row() and rows() with header validation.
	"""
	with TemporaryDirectory() as directory:
		path: Path = Path(directory) / 'input.csv'
		path.write_text('name,date\nKim,1-10\nLee,23-Feb\n', encoding='utf-8')
		csv: CSV = CSV(header=HeaderValidator())
		with csv.open(str(path)):
			header: Optional[list[str]] = csv.header()
			assert header is not None
			assert header == [
				'name',
				'date',
			]
			record: dict[str, str] = dict(csv.row())
			assert record == {
				'name': 'Kim',
				'date': '1-10',
			}
			print(record)
			for values in csv.rows():
				record = dict(values)
				assert record == {
					'name': 'Lee',
					'date': '23-Feb',
				}
				print(record)
		with csv.open(str(path)):
			# Use different keys by re-mapping the named result.
			base: dict[str, str] = dict(csv.row())
			first: dict[str, str] = {
				'company': base['name'],
				'raw_date': base['date'],
			}
			assert first == {
				'company': 'Kim',
				'raw_date': '1-10',
			}
			print(first)
	return


if __name__ == '__main__':
	main()
