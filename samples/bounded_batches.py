from pathlib import Path
from tempfile import TemporaryDirectory
from typing import (
	Iterator,
	List,
)
from csvd2c import CSV
from csvd2c.header import Validator as HeaderValidator


def batches(
	records: Iterator[List[str]],
	size: int,
) -> Iterator[List[List[str]]]:
	"""
	Accumulate at most size records per batch; record byte size is not bounded.
	"""
	if size <= 0:
		raise ValueError('Batch size must be positive')
	batch: List[List[str]] = []
	for record in records:
		batch.append(record)
		if len(batch) == size:
			yield batch
			batch = []
	if batch:
		yield batch
	return


def main() -> None:
	"""
	Feed bounded batches to an existing task without accumulating all records.
	"""
	with TemporaryDirectory() as directory:
		path: Path = Path(directory) / 'input.csv'
		with path.open('x', encoding='utf-8') as output:
			output.write('id\n')
			for index in range(23):
				output.write(str(index) + '\n')
		total = 0
		sizes: list[int] = []
		with CSV(header=HeaderValidator()).open(str(path)) as csv:
			for batch in batches(csv.rows(), size=10):
				assert len(batch) <= 10
				# Replace this output with the existing task's batch storage call.
				print('Batch:', len(batch))
				sizes.append(len(batch))
				total += len(batch)
		assert sizes == [
			10,
			10,
			3,
		]
		assert total == 23
	return


if __name__ == '__main__':
	main()
