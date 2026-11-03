from csvd2c.column import (
	Error,
	Validator,
)
from csvd2c.column.patterns import (
	Date,
	Strip,
)


def main() -> None:
	"""
	Normalize complete dates and expose ambiguous or missing-year values.
	"""
	validator: Validator = Validator(
		Strip(),
		Date('%Y-%m-%d', '%d/%m/%Y', output='%Y-%m-%d'),
	)
	assert validator(' 29/02/2024 ', 1, 0) == '2024-02-29'
	for value in (
		'1-10',
		'Feb-23',
		'23-Feb',
		'23 Feb',
		'2023-02-29',
	):
		try:
			validator(value, 1, 0)
		except Error as error:
			print('Needs review:', repr(value), error)
		else:
			raise AssertionError('Incomplete or invalid date was accepted')
	try:
		Date('%d/%m/%Y', '%m/%d/%Y')('01/02/2024', 1, 0)
	except Error as error:
		print('Ambiguous date:', error)
	else:
		raise AssertionError('Ambiguous date was accepted')
	assert Date('%d/%m/%Y', '%m/%d/%Y')('02/02/2024', 1, 0) == '2024-02-02'
	return


if __name__ == '__main__':
	main()
