# -*- coding: utf-8 -*-

from typing import Union
from ..Pattern import Pattern
from ..Error import Error


class RejectCharacters(Pattern):
	"""
	Reject any character in an explicitly supplied string of characters.
	"""

	def __init__(
		self,
		chars: str,
	) -> None:
		if not isinstance(chars, str):
			raise TypeError('chars must be a string')
		self.chars = frozenset(chars)
		return

	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		if any(char in self.chars for char in value):
			raise Error('Value contains a rejected character', row, column, value)
		return value
