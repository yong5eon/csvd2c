# -*- coding: utf-8 -*-

from typing import Optional
from ..Pattern import Pattern
from ..Error import Error


class RejectReplacementCharacter(Pattern):
	"""
	Reject U+FFFD without treating ordinary question marks as corruption.
	"""

	def __init__(self, *, error: Optional[Error] = None) -> None:
		if error is not None and not isinstance(error, Error):
			raise TypeError('error must be a column Error instance or None')
		self.error = error
		return

	def __call__(self, col: str) -> str:
		if '\ufffd' in col:
			if self.error is not None:
				return self.error(col)
			raise ValueError('Value contains the Unicode replacement character')
		return col
