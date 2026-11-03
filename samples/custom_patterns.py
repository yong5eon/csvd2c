from pathlib import Path
from tempfile import TemporaryDirectory
from typing import (
	List,
	Union,
)
from csvd2c import CSV
from csvd2c.header import Validator as HeaderValidator
from csvd2c.column import (
	Error as ColumnError,
	Pattern as ColumnPattern,
	Validator as ColumnValidator,
)
from csvd2c.column.patterns import (
	Required,
	Strip,
)
from csvd2c.row import (
	Error as RowError,
	Pattern as RowPattern,
	Validator as RowValidator,
)
from csvd2c.row.patterns import Length


class RemoveProviderPrefix(ColumnPattern):
	"""
	Remove the exact prefix confirmed in this provider's company field.
	"""

	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		prefix = 'Company:'
		if not value.startswith(prefix):
			raise ColumnError(
				'Expected the confirmed company prefix',
				row,
				column,
				value,
			)
		return value[len(prefix):]


class RejectComment(RowPattern):
	"""
	Reject provider comment records whose first field starts with '#'.
	"""

	def __call__(
		self,
		value: List[str],
		row: int,
	) -> List[str]:
		if value and value[0].startswith('#'):
			raise RowError(
				'Comment records are not data',
				row,
				value,
			)
		return value


class AppendSource(RowPattern):
	"""
	Add provenance without mutating the source record.
	"""

	def __call__(
		self,
		value: List[str],
		row: int,
	) -> List[str]:
		return value + ['provider-A']


def main() -> None:
	with TemporaryDirectory() as directory:
		path: Path = Path(directory) / 'input.csv'
		path.write_text('name\nCompany: Example\nExample Ltd\n#provider note\n', encoding='utf-8')
		csv: CSV = CSV(
			header=HeaderValidator(),
			row=RowValidator(RejectComment(), Length(1), AppendSource(), Length(2)),
			column=(ColumnValidator(RemoveProviderPrefix(), Strip(), Required()),),
		)
		with csv.open(str(path)):
			assert csv.header() == ['name']
			record: dict[str, str] = dict(zip(
				(
					'name',
					'source',
				),
				csv.row(),
			))
			assert record == {
				'name': 'Example',
				'source': 'provider-A',
			}
			print(record)
			try:
				csv.row()
			except ColumnError as error:
				assert error.row == 3
				assert error.column == 0
				assert error.value == 'Example Ltd'
				print('Rejected:', error.row, error.column, repr(error.value), error.message)
			else:
				raise AssertionError('Expected a column error')
			try:
				csv.row()
			except RowError as error:
				assert error.row == 4
				assert error.value == ['#provider note']
				print('Rejected row:', error.row, error.value, error.message)
			else:
				raise AssertionError('Expected a row error')
	return


if __name__ == '__main__':
	main()
