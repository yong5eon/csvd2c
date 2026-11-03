from json import (
	dumps,
	loads,
)
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import (
	Dict,
	List,
	Union,
)
from csvd2c import CSV
from csvd2c.header import Validator as HeaderValidator
from csvd2c.row import (
	Error as RowError,
	Validator as RowValidator,
)
from csvd2c.row.patterns import (
	Length,
	RejectEmpty,
	RejectHeader,
)
from csvd2c.column import (
	Error as ColumnError,
	Validator as ColumnValidator,
)
from csvd2c.column.patterns import (
	Required,
	Strip,
)

HEADER = (
	'name',
	'date',
)


def main() -> None:
	"""
	Inject validators into CSV, log rejected records, and resume with the next record.
	"""
	with TemporaryDirectory() as directory:
		path: Path = Path(directory) / 'input.csv'
		rejected_path: Path = Path(directory) / 'rejected.jsonl'
		path.write_text('name,date\nKim,1-10\n\nname,date\nLee\nPark,23-Feb\n', encoding='utf-8')
		csv: CSV = CSV(
			header=HeaderValidator(),
			row=RowValidator(
				RejectEmpty(),
				RejectHeader(*HEADER),
				Length(len(HEADER)),
			),
			column={
				'name': ColumnValidator(Strip(), Required()),
				'date': ColumnValidator(Strip(), Required()),
			},
		)
		accepted: int = 0
		rejected: int = 0
		with csv.open(str(path)), rejected_path.open('x', encoding='utf-8') as output:
			assert csv.header() == list(HEADER)
			while True:
				try:
					result: Dict[str, str] = dict(zip(HEADER, csv.row()))
				except StopIteration:
					break
				except (RowError, ColumnError) as error:
					item: Dict[str, Union[int, str, List[str]]] = {
						'row': error.row,
						'value': error.value,
						'message': error.message,
					}
					if isinstance(error, ColumnError):
						item['column'] = error.column
					output.write(dumps(item, ensure_ascii=True) + '\n')
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
				assert 'row' in item and 'value' in item and 'message' in item
				print('Rejected:', item)
	return


if __name__ == '__main__':
	main()
