from csvd2c.column.patterns import Recode


def main() -> None:
	"""
	Reverse a known misdecoding path in text that contains no surrogate markers.
	"""
	original = 'Công ty café'
	corrupt: str = original.encode('utf-8').decode('latin-1')
	result: str = Recode('latin-1', 'utf-8')(corrupt, 1, 0)
	assert result == original
	assert Recode('utf-8', 'utf-8')('\ufffd', 1, 0) == '\ufffd'
	print('Recovered:', ascii(result))
	print('Already replaced characters are not repaired; do not guess codec paths')
	return


if __name__ == '__main__':
	main()
