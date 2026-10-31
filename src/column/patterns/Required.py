# -*- coding: utf-8 -*-

from typing import Optional
from ..Pattern import Pattern
from ..Error import Error


class Required(Pattern):
	"""
	Reject exactly empty strings; strip whitespace separately when needed.
	"""

	def __init__(self, *, error: Optional[Error] = None) -> None:
		if error is not None and not isinstance(error, Error):
			raise TypeError('error must be a column Error instance or None')
		self.error = error
		return

	def __call__(self, col: str) -> str:
		if col == '':
			if self.error is not None:
				return self.error(col)
			raise ValueError('A nonempty value is required')
		return col
