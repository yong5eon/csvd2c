# -*- coding: utf-8 -*-

from typing import Optional
from ..Pattern import Pattern
from ..Error import Error


class RejectCharacters(Pattern):
	"""
	Reject any character in an explicitly supplied string of characters.
	"""

	def __init__(
		self,
		chars: str,
		*,
		error: Optional[Error] = None,
	) -> None:
		if not isinstance(chars, str):
			raise TypeError('chars must be a string')
		if error is not None and not isinstance(error, Error):
			raise TypeError('error must be a column Error instance or None')
		self.chars = frozenset(chars)
		self.error = error
		return

	def __call__(self, col: str) -> str:
		if any(char in self.chars for char in col):
			if self.error is not None:
				return self.error(col)
			raise ValueError('Value contains a rejected character')
		return col
