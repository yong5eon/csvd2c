from csvd2c.row import Validator
from csvd2c.row.patterns import (
	IfLength,
	Length,
	Merge,
	Split,
)


def main() -> None:
	"""
	Merge known unquoted address fragments, or split a known combined field.
	"""
	validator: Validator = Validator(
		IfLength(4, Merge(1, 3, sep=',')),
		IfLength(5, Merge(1, 4, sep=',')),
		Length(3),
	)
	assert validator([
		'Kim',
		'Seoul',
		'Gangnam',
		'2026-01-10',
	]) == [
		'Kim',
		'Seoul,Gangnam',
		'2026-01-10',
	]
	assert validator([
		'Kim',
		'Seoul',
		'Gangnam',
		'Street',
		'2026-01-10',
	]) == [
		'Kim',
		'Seoul,Gangnam,Street',
		'2026-01-10',
	]
	assert validator([
		'Kim',
		'Seoul',
		'2026-01-10',
	]) == [
		'Kim',
		'Seoul',
		'2026-01-10',
	]
	assert Split(1, sep='|', maxsplit=1)([
		'Kim',
		'Seoul|Gangnam|Street',
	]) == [
		'Kim',
		'Seoul',
		'Gangnam|Street',
	]
	print('Merge uses exclusive stop; positions must come from confirmed input rules')
	return


if __name__ == '__main__':
	main()
