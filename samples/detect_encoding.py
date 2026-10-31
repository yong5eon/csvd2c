from pathlib import Path
from tempfile import TemporaryDirectory
from csvd2c import (
	CSV,
	detect_encoding,
)


def main() -> None:
	"""
	Check an ordered sample, then decode the full stream using that choice.
	"""
	with TemporaryDirectory() as directory:
		path: Path = Path(directory) / 'input.csv'
		path.write_bytes('이름\n홍길동\n'.encode('cp949'))
		encoding: str = detect_encoding(str(path), 'utf-8', 'cp949')
		assert encoding == 'cp949'
		with CSV(encoding=encoding).open(str(path)) as csv:
			assert csv.header() == ['이름']
			assert csv.row() == ['홍길동']
		path.write_bytes(b'name\nKim\n')
		# ASCII is valid in both codecs; order determines the result.
		assert detect_encoding(str(path), 'cp949', 'utf-8') == 'cp949'
		try:
			detect_encoding(str(path))
		except ValueError as error:
			print('Missing candidates:', error)
		else:
			raise AssertionError('Expected candidate error')
		print('Sample detection does not verify the entire file or identify the true encoding')
	return


if __name__ == '__main__':
	main()
