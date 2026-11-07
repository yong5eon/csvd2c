# -*- coding: utf-8 -*-

from codecs import getincrementaldecoder
from .CSV import (
	CSV,
	MAX_FIELD_SIZE,
)
from .Error import Error

__all__ = (
	'detect_encoding',
	'CSV',
	'MAX_FIELD_SIZE',
	'Error',
)


def detect_encoding(
	path: str,
	*args: str,
) -> str:
	"""
	Return the first encoding that decodes the initial sample of up to 1MiB.

	Check candidates in order without automatic BOM-based selection.
	Raise ValueError if no candidates are provided, the file is empty, or all
	candidates fail. Propagate LookupError for unknown encodings and file
	access errors unchanged. Success does not guarantee the actual encoding
	or the validity of the entire file.
	"""
	if not args:
		raise ValueError('At least one encoding candidate is required')

	for encoding in args:
		getincrementaldecoder(encoding)

	sample_size = 1024 * 1024
	with open(path, 'rb') as binary:
		raw: bytes = binary.read(sample_size + 1)

	if not raw:
		raise ValueError('Cannot detect the encoding of an empty file')

	sample: bytes = raw[:sample_size]
	is_end: bool = len(raw) <= sample_size
	failures: list[str] = []
	for encoding in args:
		decoder = getincrementaldecoder(encoding)(errors='strict')
		try:
			# Reject an incomplete trailing character only at the actual end of the file.
			decoder.decode(sample, final=is_end)
		except UnicodeDecodeError as error:
			failures.append(
				'{}: byte {}, {}'.format(
					encoding,
					error.start,
					error.reason,
				)
			)
		else:
			return encoding

	raise ValueError(
		'Sample decoding failed for all encoding candidates: {}'.format('; '.join(failures))
	)
