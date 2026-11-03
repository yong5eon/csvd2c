from csvd2c.column import (
	Error,
	Validator,
)
from csvd2c.column.patterns import (
	RejectCharacters,
	RejectReplacementCharacter,
	RejectSurrogates,
)


def main() -> None:
	"""
	Detect stored replacement characters, preserved bytes, and explicit bans.
	"""
	validator: Validator = Validator(
		RejectSurrogates(),
		RejectReplacementCharacter(),
		RejectCharacters('\x00'),
	)
	assert validator('Company?', 1, 0) == 'Company?'
	assert validator('한글 中文 😀', 1, 0) == '한글 中文 😀'
	for value in (
		'before\ufffdafter',
		b'name\xff'.decode('utf-8', errors='surrogateescape'),
		'embedded\x00null',
	):
		try:
			validator(value, 1, 0)
		except Error as error:
			# ascii() safely displays surrogate markers on any console.
			print('Damaged field:', ascii(value), error)
		else:
			raise AssertionError('Expected damaged field rejection')
	return


if __name__ == '__main__':
	main()
