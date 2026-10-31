from decimal import Decimal
from csvd2c.column import Validator
from csvd2c.column.patterns import (
	Number,
	Range,
	Strip,
)


def main() -> None:
	"""
	Use explicit grouping and decimal separators with precise numeric bounds.
	"""
	amount: Validator = Validator(Strip(), Number(thousands=','), Range(0, Decimal('1000000')))
	assert amount(' 1,234.500 ') == '1234.5'
	assert Number(decimal=',', thousands='.')('-1.234,50') == '-1234.5'
	assert Number()('-0.000') == '0'
	assert Number()('123456789012345678901234567890.00100') == '123456789012345678901234567890.001'
	for value in (
		'1,23',
		'NaN',
		'1e3',
		'-1',
		'1,000,001',
	):
		try:
			amount(value)
		except ValueError as error:
			print('Rejected amount:', value, error)
		else:
			raise AssertionError('Invalid amount was accepted')
	return


if __name__ == '__main__':
	main()
