# -*- coding: utf-8 -*-

from codecs import lookup
from typing import Optional
from ..Pattern import Pattern
from ..Error import Error


class Recode(Pattern):
	"""
	Reverse an explicitly known misdecoding path using strict codecs.

	Success does not establish correctness and cannot recover replaced bytes.
	"""

	def __init__(
		self,
		stored_encoding: str,
		original_encoding: str,
		*,
		error: Optional[Error] = None,
	) -> None:
		for encoding in (
			stored_encoding,
			original_encoding,
		):
			codec = lookup(encoding)
			if not isinstance(codec.decode(b'', 'strict')[0], str):
				raise ValueError('Recode requires text encodings')
		if error is not None and not isinstance(error, Error):
			raise TypeError('error must be a column Error instance or None')
		self.stored_encoding = stored_encoding
		self.original_encoding = original_encoding
		self.error = error
		return

	def __call__(self, col: str) -> str:
		try:
			return col.encode(self.stored_encoding, errors='strict').decode(
				self.original_encoding,
				errors='strict',
			)
		except UnicodeError as cause:
			if self.error is not None:
				return self.error(col)
			raise ValueError('Value cannot be recoded through the configured encodings') from cause
