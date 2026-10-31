from csv import Error as CSVError
from json import (
	dumps,
	loads,
)
from pathlib import Path
from tempfile import TemporaryDirectory
from csvd2c import CSV
from csvd2c.row import Validator
from csvd2c.row.patterns import (
	Length,
	RejectEmpty,
	RejectHeader,
)


def main() -> None:
	"""
	Reject individual parsed records without masking decoding or parsing errors.
	"""
	with TemporaryDirectory() as directory:
		path: Path = Path(directory) / 'input.csv'
		rejected_path: Path = Path(directory) / 'rejected.jsonl'
		path.write_text('name,date\nKim,1-10\n\nname,date\nLee\nPark,23-Feb\n', encoding='utf-8')
		csv: CSV = CSV()
		accepted = 0
		rejected = 0
		with csv.open(str(path)), rejected_path.open('x', encoding='utf-8') as output:
			header: list[str] = csv.header()
			validator: Validator = Validator(RejectEmpty(), RejectHeader(*header), Length(len(header)))
			record_number = 1
			while True:
				try:
					original: list[str] = csv.row()
				except StopIteration:
					break
				except (
					CSVError,
					UnicodeDecodeError,
				):
					# Parsing boundaries may be unreliable; never resume blindly.
					raise
				record_number += 1
				try:
					result: list[str] = validator(original.copy())
				except ValueError as error:
					output.write(dumps({
						'record': record_number,
						'original': original,
						'reason': str(error),
					}, ensure_ascii=True) + '\n')
					rejected += 1
				else:
					print('Accepted:', result)
					accepted += 1
		assert accepted == 2
		assert rejected == 3
		with rejected_path.open(encoding='utf-8') as output:
			for line in output:
				item = loads(line)
				assert isinstance(item, dict)
				assert 'original' in item and 'reason' in item
				print('Rejected:', item)
	return


if __name__ == '__main__':
	main()
