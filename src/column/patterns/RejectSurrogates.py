# -*- coding: utf-8 -*-

from typing import Optional
from ..Pattern import Pattern
from ..Error import Error


class RejectSurrogates(Pattern):
	"""
	Reject all surrogate code points, including surrogateescape byte markers.
	"""

	def __init__(self, *, error: Optional[Error] = None) -> None:
		if error is not None and not isinstance(error, Error):
			raise TypeError('error must be a column Error instance or None')
		self.error = error
		return

	def __call__(self, col: str) -> str:
		if any('\ud800' <= char <= '\udfff' for char in col):
			if self.error is not None:
				return self.error(col)
			raise ValueError('Value contains surrogate code points')
		return col
