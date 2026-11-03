from csvd2c.row import Validator
from csvd2c.row.patterns import (
	Insert,
	Length,
	Remove,
	Reorder,
	Replace,
	Slice,
)


def main() -> None:
	"""
	Compose explicit structural rules while preserving the input.
	"""
	original: list[str] = [
		'date',
		'unused',
		'name',
	]
	validator: Validator = Validator(
		Length(3),
		Remove(1),
		Reorder(1, 0),
		Insert(2, 'status'),
		Replace(-1, 'active'),
		Slice(0, 3),
		Length(3),
	)
	result: list[str] = validator(original, 1)
	assert result == [
		'name',
		'date',
		'active',
	]
	assert original == [
		'date',
		'unused',
		'name',
	]
	assert Slice(step=-1)([
		'a',
		'b',
	], 1) == [
		'b',
		'a',
	]
	print(result)
	return


if __name__ == '__main__':
	main()
