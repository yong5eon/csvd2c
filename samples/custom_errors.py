from typing import Union
from csvd2c import Error
from csvd2c.row import (
	Error as RowError,
	Validator as RowValidator,
)
from csvd2c.row.patterns import Length
from csvd2c.column import (
	Error as ColumnError,
	Pattern as ColumnPattern,
	Validator as ColumnValidator,
)
from csvd2c.column.patterns import (
	Map,
	Required,
	Strip,
)


class ReviewRequired(Error):
	"""
	Application-specific failure that callers can still catch as csvd2c.Error.
	"""

	def __init__(
		self,
		message: str,
		reviewer: str,
	) -> None:
		super().__init__(message)
		self.reviewer = reviewer
		return


class RejectPending(ColumnPattern):
	"""
	Reject statuses that a person must confirm before import.
	"""

	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		if value == 'pending':
			raise ReviewRequired('Status {!r} requires review'.format(value), 'operations')
		return value


def main() -> None:
	row_validator: RowValidator = RowValidator(Length(2))
	try:
		row_validator(['Kim'], 1)
	except RowError as error:
		print('Row error:', error.row, error.value, error.message)
		assert error.row == 1
		assert error.value == ['Kim']
	else:
		raise AssertionError('Expected a row error')

	column_validator: ColumnValidator = ColumnValidator(
		Strip(),
		Required(),
		RejectPending(),
		Map({'active': 'A'}),
	)
	assert column_validator(' active ', 2, 'status') == 'A'
	try:
		column_validator(' unrecognized ', 3, 'status')
	except ColumnError as error:
		print('Column error:', error.row, error.column, repr(error.value), error.message)
		# value is the input of the failing Pattern, after Strip().
		assert error.value == 'unrecognized'
		assert error.column == 'status'
	else:
		raise AssertionError('Expected a column error')

	try:
		column_validator('pending', 4, 'status')
	except Error as error:
		assert isinstance(error, ReviewRequired)
		print('Custom error:', error.message, 'reviewer:', error.reviewer)
	else:
		raise AssertionError('Expected a custom error')
	return


if __name__ == '__main__':
	main()
