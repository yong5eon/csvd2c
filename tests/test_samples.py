from ast import parse
from os import environ
from pathlib import Path
from subprocess import (
	CompletedProcess,
	run,
)
from sys import executable
from tempfile import TemporaryDirectory
from unittest import (
	TestCase,
	main,
)


class SampleTests(TestCase):
	"""
	Run every standalone sample using the installed public package.
	"""

	def test_all_samples(self) -> None:
		root: Path = Path(__file__).resolve().parents[1]
		samples: list[Path] = sorted((root / 'samples').glob('*.py'))
		self.assertEqual(len(samples), 24)
		env: dict[str, str] = dict(environ)
		env['PYTHONIOENCODING'] = 'utf-8'
		with TemporaryDirectory() as directory:
			for sample in samples:
				with self.subTest(sample=sample.name):
					parse(sample.read_text(encoding='utf-8'), feature_version=(
						3,
						9,
					))
					result: CompletedProcess[str] = run(
						[
							executable,
							'-I',
							str(sample),
						],
						cwd=directory,
						env=env,
						capture_output=True,
						text=True,
						encoding='utf-8',
						timeout=30,
					)
					self.assertEqual(
						result.returncode,
						0,
						'{}\n{}\n{}'.format(sample.name, result.stdout, result.stderr),
					)
					self.assertTrue(result.stdout.strip(), 'Sample must show its result')
		return


if __name__ == '__main__':
	main()
