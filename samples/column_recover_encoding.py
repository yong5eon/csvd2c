from pathlib import Path
from tempfile import TemporaryDirectory
from csvd2c import CSV
from csvd2c.column import Validator
from csvd2c.column.patterns import (
	IfUndecodable,
	RecoverEncoding,
	RejectReplacementCharacter,
	RejectSurrogates,
	TryRecoverEncoding,
)


def main() -> None:
	"""
	Recover confirmed source bytes before any normalization and keep valid UTF-8.
	"""
	with TemporaryDirectory() as directory:
		path: Path = Path(directory) / 'input.csv'
		path.write_bytes(
			b'id,description\n'
			+ '1,Công ty\n'.encode('cp1258')
			+ '2,Công ty\n'.encode('utf-8')
		)
		csv: CSV = CSV(
			encoding='utf-8',
			errors='surrogateescape',
			cols={
				'description': Validator(
					IfUndecodable(RecoverEncoding('cp1258')),
					RejectSurrogates(),
					RejectReplacementCharacter(),
				),
			},
		)
		with csv.open(str(path)):
			header: list[str] = csv.header()
			for record in csv.rows(header=header):
				assert record['description'] == 'Công ty'
				print(ascii(record))
		korean: str = '홍길동'.encode('cp949').decode('utf-8', errors='surrogateescape')
		candidates: Validator = Validator(
			IfUndecodable(
				TryRecoverEncoding('ascii'),
				TryRecoverEncoding('cp949'),
			),
			RejectSurrogates(),
		)
		assert candidates(korean) == '홍길동'
		print('Candidate order is policy, not language detection; first success wins')
	return


if __name__ == '__main__':
	main()
