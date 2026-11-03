from pathlib import Path
from tempfile import TemporaryDirectory
from typing import (
	Dict,
	List,
	Optional,
)
from csvd2c import CSV
from csvd2c.header import (
	Error as HeaderError,
	Pattern as HeaderPattern,
	Validator as HeaderValidator,
)
from csvd2c.header.patterns import (
	ExactOrder,
	Length,
	RejectDuplicate,
	RejectEmpty,
)
from csvd2c.column import Validator as ColumnValidator
from csvd2c.column.patterns import (
	Required,
	Strip,
	Upper,
)


class Rename(HeaderPattern):
	"""
	Rename provider header names before named column validators are mapped.
	"""

	def __init__(
		self,
		names: Dict[str, str],
	) -> None:
		super().__init__()
		self.names: Dict[str, str] = dict(names)
		return

	def __call__(
		self,
		value: List[str],
	) -> List[str]:
		return [self.names.get(name, name) for name in value]


def main() -> None:
	"""
	Validate the first record as a header when the file is opened.
	"""
	with TemporaryDirectory() as directory:
		path: Path = Path(directory) / 'input.csv'
		path.write_text('id,name,date\n1, Kim ,1-10\n2, Lee ,23-Feb\n', encoding='utf-8')
		csv: CSV = CSV(
			header=HeaderValidator(
				Length(3),
				RejectEmpty(),
				RejectDuplicate(),
				ExactOrder(
					'id',
					'name',
					'date',
				),
			),
			column={'name': ColumnValidator(Strip(), Required(), Upper())},
		)
		with csv.open(str(path)):
			header: Optional[List[str]] = csv.header()
			assert header == [
				'id',
				'name',
				'date',
			]
			print('Header:', header)
			records: List[List[str]] = []
			for record in csv.rows():
				print('Record:', record)
				records.append(record)
			assert records == [
				[
					'1',
					'KIM',
					'1-10',
				],
				[
					'2',
					'LEE',
					'23-Feb',
				],
			]
			assert csv.header() == header

		path.write_text('id,name,name\n1,Kim,Lee\n', encoding='utf-8')
		try:
			with csv.open(str(path)):
				raise AssertionError('Expected a header error')
		except HeaderError as error:
			assert error.value == [
				'id',
				'name',
				'name',
			]
			print('Rejected header:', error.message, error.value)
		assert csv.reader is None

		path.write_text('ID,Company Name\n1, Acme \n', encoding='utf-8')
		renamed: CSV = CSV(
			header=HeaderValidator(
				RejectEmpty(),
				Rename({
					'ID': 'id',
					'Company Name': 'name',
				}),
				RejectDuplicate(),
			),
			column={'name': ColumnValidator(Strip(), Upper())},
		)
		with renamed.open(str(path)):
			assert renamed.header() == [
				'id',
				'name',
			]
			renamed_record: List[str] = renamed.row()
			assert renamed_record == [
				'1',
				'ACME',
			]
			print('Renamed header:', renamed.header(), renamed_record)
	return


if __name__ == '__main__':
	main()
