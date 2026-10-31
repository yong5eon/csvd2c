from typing import List
from csvd2c.row import (
	Error as RowError,
	Validator as RowValidator,
)
from csvd2c.row.patterns import Length
from csvd2c.column import (
	Error as ColumnError,
	Validator as ColumnValidator,
)
from csvd2c.column.patterns import (
	Map,
	Required,
)


class FillMissingDate(RowError):
	"""
	Fill only the confirmed single missing trailing date, never arbitrary gaps.
	"""

	def __call__(
		self,
		row: List[str],
	) -> List[str]:
		if len(row) != 1:
			raise ValueError('Cannot safely fill this record')
		print('Explicitly filling a missing date:', repr(row))
		return row + ['']


class UnknownStatus(ColumnError):
	"""
	Record the unknown value and return a business-approved explicit marker.
	"""

	def __call__(
		self,
		col: str,
	) -> str:
		print('Unknown status:', repr(col))
		return 'UNKNOWN'


def main() -> None:
	row_validator: RowValidator = RowValidator(
		Length(2, error=FillMissingDate()),
		Length(2),
	)
	assert row_validator(['Kim']) == [
		'Kim',
		'',
	]
	column_validator: ColumnValidator = ColumnValidator(
		Map({'active': 'A'}, error=UnknownStatus()),
		Required(),
	)
	assert column_validator('unrecognized') == 'UNKNOWN'
	assert column_validator('active') == 'A'
	return


if __name__ == '__main__':
	main()
