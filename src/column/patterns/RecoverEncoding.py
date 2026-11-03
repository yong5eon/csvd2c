# -*- coding: utf-8 -*-

from codecs import lookup
from typing import Union
from ..Pattern import Pattern
from ..Error import Error


class RecoverEncoding(Pattern):
	"""
	Recover field bytes using surrogateescape and decode a specified source.

	read_encoding must match the codec originally used to read the field.
	Apply before transformations that alter its original characters. Return
	a string, not UTF-8 bytes. Success does not establish the source encoding
	or restore previously replaced characters. This processes the whole
	field, not independently encoded fragments within one field.
	"""

	def __init__(
		self,
		source: str,
		*,
		read_encoding: str = 'utf-8',
	) -> None:
		for encoding in (
			source,
			read_encoding,
		):
			codec = lookup(encoding)
			if not isinstance(codec.decode(b'', 'strict')[0], str):
				raise ValueError('RecoverEncoding requires text encodings')
		self.source = source
		self.read_encoding = read_encoding
		return

	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		try:
			raw: bytes = value.encode(self.read_encoding, errors='surrogateescape')
			return raw.decode(self.source, errors='strict')
		except UnicodeError:
			raise Error('Field bytes cannot be recovered with the configured encodings', row, column, value)
