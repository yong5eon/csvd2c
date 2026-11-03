from csv import writer
from _csv import writer as Writer
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional
from csvd2c import CSV
from csvd2c.header import Validator as HeaderValidator
from csvd2c.column import Validator
from csvd2c.column.patterns import (
	Required,
	Strip,
	Upper,
)


def main() -> None:
	"""
	Stream cleaned records to UTF-8 CSV using the standard library writer.

	CSV itself is read-only. Output is created exclusively to avoid overwrite.
	"""
	with TemporaryDirectory() as directory:
		path: Path = Path(directory) / 'input.csv'
		output_path: Path = Path(directory) / 'clean.csv'
		with path.open('x', encoding='utf-8', newline='') as source:
			source_writer: Writer = writer(source)
			source_writer.writerow([
				'id',
				'name',
			])
			for index in range(1000):
				source_writer.writerow([
					str(index),
					' company ',
				])
		csv: CSV = CSV(
			header=HeaderValidator(),
			column={'name': Validator(Strip(), Required(), Upper())},
		)
		count = 0
		with csv.open(str(path)), output_path.open('x', encoding='utf-8', newline='') as output:
			header: Optional[list[str]] = csv.header()
			assert header is not None
			output_writer: Writer = writer(output)
			output_writer.writerow(header)
			for record in csv.rows():
				output_writer.writerow(record)
				count += 1
		assert count == 1000
		with CSV(header=HeaderValidator()).open(str(output_path)) as result:
			assert result.header() == [
				'id',
				'name',
			]
			assert result.row() == [
				'0',
				'COMPANY',
			]
		print('Exported records:', count)
		print('Small synthetic input only; this is not a 200GB performance test')
	return


if __name__ == '__main__':
	main()
