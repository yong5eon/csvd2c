# -*- coding: utf-8 -*-

from typing import Union
from ..Pattern import Pattern
from ..Error import Error


class RejectReplacementCharacter(Pattern):
	"""
	Reject U+FFFD without treating ordinary question marks as corruption.
	"""

	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		if '\ufffd' in value:
			raise Error('Value contains the Unicode replacement character', row, column, value)
		return value
