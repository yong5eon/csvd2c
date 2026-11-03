from csvd2c.column import (
	Error,
	Validator,
)
from csvd2c.column.patterns import (
	Choices,
	Default,
	IfEmpty,
	IfMatch,
	Length,
	Map,
	Regex,
	Required,
	Strip,
	Upper,
)


def main() -> None:
	"""
	Validate IDs and normalize exact status mappings and empty values.
	"""
	identifier: Validator = Validator(Strip(), Required(), Length(3, 8), Regex(r'[A-Z][0-9]+'))
	assert identifier(' A123 ', 1, 0) == 'A123'
	try:
		identifier('invalid', 1, 0)
	except Error as error:
		print('Rejected ID:', error)
	else:
		raise AssertionError('Expected invalid ID')
	status: Validator = Validator(
		Strip(),
		IfEmpty(Default('unknown')),
		IfMatch(r'[a-z]+', Upper()),
		Map({
			'ACTIVE': 'A',
			'UNKNOWN': 'U',
		}),
		Choices('A', 'U'),
	)
	assert status(' active ', 1, 0) == 'A'
	assert status(' ', 1, 0) == 'U'
	print('Validated ID and mapped statuses')
	return


if __name__ == '__main__':
	main()
