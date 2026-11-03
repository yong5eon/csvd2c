# -*- coding: utf-8 -*-

from codecs import lookup
from typing import Union
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
	) -> None:
		for encoding in (
			stored_encoding,
			original_encoding,
		):
			codec = lookup(encoding)
			if not isinstance(codec.decode(b'', 'strict')[0], str):
				raise ValueError('Recode requires text encodings')
		self.stored_encoding = stored_encoding
		self.original_encoding = original_encoding
		return

	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		try:
			return value.encode(self.stored_encoding, errors='strict').decode(
				self.original_encoding,
				errors='strict',
			)
		except UnicodeError:
			raise Error('Value cannot be recoded through the configured encodings', row, column, value)
