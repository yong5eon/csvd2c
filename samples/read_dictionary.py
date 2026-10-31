from pathlib import Path
from tempfile import TemporaryDirectory
from csvd2c import CSV


def main() -> None:
	"""
	Map values by position without renaming the stored validation header.
	"""
	with TemporaryDirectory() as directory:
		path: Path = Path(directory) / 'input.csv'
		path.write_text('name,date\nKim,1-10\nLee,23-Feb\n', encoding='utf-8')
		csv: CSV = CSV()
		with csv.open(str(path)):
			header: list[str] = csv.header()
			record: dict[str, str] = csv.row(header=header)
			assert record == {
				'name': 'Kim',
				'date': '1-10',
			}
			for record in csv.rows(header=(
				'company',
				'raw_date',
			)):
				assert record == {
					'company': 'Lee',
					'raw_date': '23-Feb',
				}
				print(record)
		with csv.open(str(path)):
			# No implicit header consumption: this maps the first record itself.
			first: dict[str, str] = csv.row(header=(
				'first',
				'second',
			))
			assert first == {
				'first': 'name',
				'second': 'date',
			}
	return


if __name__ == '__main__':
	main()
