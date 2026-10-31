from pathlib import Path
from tempfile import TemporaryDirectory
from csvd2c import CSV


def main() -> None:
	"""
	Read quoted tabs, embedded CRLF, and a UTF-8 BOM in all read modes.
	"""
	with TemporaryDirectory() as directory:
		path: Path = Path(directory) / 'input.tsv'
		path.write_bytes('name\tnote\r\nKim\t"line 1\tvalue\r\nline 2"\r\n'.encode('utf-8-sig'))
		for mode in (
			'rb',
			'r',
			'rt',
		):
			csv: CSV = CSV(encoding='utf-8-sig', delimiter='\t')
			with csv.open(str(path), mode=mode):
				assert csv.header() == [
					'name',
					'note',
				]
				record: list[str] = csv.row()
				assert record == [
					'Kim',
					'line 1\tvalue\r\nline 2',
				]
				print(mode, repr(record))
	return


if __name__ == '__main__':
	main()
