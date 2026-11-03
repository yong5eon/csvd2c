from csvd2c.column import Validator
from csvd2c.column.patterns import (
	CaseFold,
	CollapseWhitespace,
	Lower,
	RegexReplace,
	Replace,
	Strip,
	UnicodeNormalize,
	Upper,
)


def main() -> None:
	"""
	Normalize text explicitly without applying codec recovery after alteration.
	"""
	validator: Validator = Validator(
		UnicodeNormalize('NFKC'),
		CollapseWhitespace(),
		Strip(),
		Replace('Company', 'Co.'),
		RegexReplace(r'\b([0-9]+)\b', r'[\1]'),
	)
	result: str = validator(' \tＡ Company\n １２３ ', 1, 0)
	assert result == 'A Co. [123]'
	assert UnicodeNormalize('NFC')('e\u0301', 1, 0) == 'é'
	assert CaseFold()('Straße', 1, 0) == 'strasse'
	assert Lower()('ABC', 1, 0) == 'abc'
	assert Upper()('abc', 1, 0) == 'ABC'
	print(result)
	return


if __name__ == '__main__':
	main()
