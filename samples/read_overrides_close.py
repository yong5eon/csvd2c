from pathlib import Path
from tempfile import TemporaryDirectory
from csvd2c import CSV
from csvd2c.header import Validator as HeaderValidator
from csvd2c.column import Validator
from csvd2c.column.patterns import (
	Strip,
	Upper,
)


def main() -> None:
	"""
	Override validators per call, explicitly close, and reopen the same instance.
	"""
	with TemporaryDirectory() as directory:
		path: Path = Path(directory) / 'input.csv'
		path.write_text('name,note\n a , b \nc,d\n', encoding='utf-8')
		csv: CSV = CSV(column={'name': Validator(Upper())})
		with csv.open(str(path), header=HeaderValidator()):
			record: list[str] = csv.row(column=(Validator(Strip()),))
			assert record == [
				'a',
				' b ',
			]
			assert csv.row(column=None) == [
				'C',
				'd',
			]
			csv.close()
			csv.close()
			try:
				csv.row()
			except RuntimeError as error:
				print('Read after close:', error)
			else:
				raise AssertionError('Expected closed stream error')
		with csv.open(str(path)):
			# Without a header Validator, the header record is read as data.
			for record in csv.rows(column={}):
				print('Explicitly disabled column validation:', record)
	return


if __name__ == '__main__':
	main()
