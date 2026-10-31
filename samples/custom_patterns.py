from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List
from csvd2c import CSV
from csvd2c.column import (
	Pattern as ColumnPattern,
	Validator as ColumnValidator,
)
from csvd2c.column.patterns import (
	Required,
	Strip,
)
from csvd2c.row import (
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
		col: str,
	) -> str:
		prefix = 'Company:'
		if not col.startswith(prefix):
			raise ValueError('Expected the confirmed company prefix')
		return col[len(prefix):]


class AppendSource(RowPattern):
	"""
	Add provenance without mutating the source record.
	"""

	def __call__(
		self,
		row: List[str],
	) -> List[str]:
		return row + ['provider-A']


def main() -> None:
	with TemporaryDirectory() as directory:
		path: Path = Path(directory) / 'input.csv'
		path.write_text('name\nCompany: Example\n', encoding='utf-8')
		csv: CSV = CSV(
			row=RowValidator(Length(1), AppendSource(), Length(2)),
			cols=(ColumnValidator(RemoveProviderPrefix(), Strip(), Required()),),
		)
		with csv.open(str(path)):
			assert csv.header() == ['name']
			record: dict[str, str] = csv.row(header=(
				'name',
				'source',
			))
			assert record == {
				'name': 'Example',
				'source': 'provider-A',
			}
			print(record)
	return


if __name__ == '__main__':
	main()
