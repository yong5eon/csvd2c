from csvd2c.column.patterns import (
	CURRENCY_ALIASES,
	CURRENCY_CODES,
	Currency,
	Number,
)


def main() -> None:
	"""
	Normalize confirmed currency aliases and process the amount separately.
	"""
	currency: Currency = Currency({
		'VN$': 'VND',
		'C$': 'CAD',
	})
	for value, expected in (
		(
			'￦1,000',
			'KRW 1,000',
		),
		(
			'CA$1,000',
			'CAD 1,000',
		),
		(
			'CN\ufffd1,000',
			'CNY 1,000',
		),
		(
			'미국 달러 100',
			'USD 100',
		),
		(
			'VN$ 10,000,000',
			'VND 10,000,000',
		),
	):
		assert currency(value, 1, 0) == expected
		print(currency(value, 1, 0))
	code, amount = currency('VN$ 10,000,000', 1, 0).split(' ', 1)
	assert code == 'VND'
	assert Number(thousands=',')(amount, 1, 0) == '10000000'
	assert 'VND' in CURRENCY_CODES
	assert CURRENCY_ALIASES['VND'] == 'VND'
	assert Currency()('$100', 1, 0) == 'USD 100'
	assert Currency({'$': 'CAD'})('$100', 1, 0) == 'CAD 100'
	print('Custom aliases are provider policies; bare dollar defaults to USD')
	return


if __name__ == '__main__':
	main()
