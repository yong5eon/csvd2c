from decimal import Decimal
from csvd2c.column.patterns import (
	Currency,
	Number,
)


def main() -> None:
	"""
	Handle one confirmed provider format, not a general currency interval parser.
	"""
	value = 'VN$ 10,000,000 - VN$ 20,000,000'
	# The provider confirms spaced hyphen separation and VN$ meaning VND.
	parts: list[str] = value.split(' - ')
	if len(parts) != 2:
		raise ValueError('Expected exactly two interval endpoints')
	currency: Currency = Currency({'VN$': 'VND'})
	number: Number = Number(thousands=',')
	low_code, low_text = currency(parts[0], 1, 0).split(' ', 1)
	high_code, high_text = currency(parts[1], 1, 0).split(' ', 1)
	if low_code != high_code:
		raise ValueError('Interval currencies differ')
	low: str = number(low_text, 1, 0)
	high: str = number(high_text, 1, 0)
	if Decimal(low) > Decimal(high):
		raise ValueError('Lower bound exceeds upper bound')
	result: str = '{} {} - {} {}'.format(low_code, low, high_code, high)
	assert result == 'VND 10000000 - VND 20000000'
	print(result)
	return


if __name__ == '__main__':
	main()
