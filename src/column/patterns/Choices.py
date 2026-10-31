# -*- coding: utf-8 -*-

from typing import Optional
from ..Pattern import Pattern
from ..Error import Error


class Choices(Pattern):
	"""
	Require exact membership in the configured strings.
	"""

	def __init__(self, *values: str, error: Optional[Error] = None) -> None:
		if any(not isinstance(value, str) for value in values):
			raise TypeError('Choices must be strings')
		if error is not None and not isinstance(error, Error):
			raise TypeError('error must be a column Error instance or None')
		self.values = frozenset(values)
		self.error = error
		return

	def __call__(self, col: str) -> str:
		if col not in self.values:
			if self.error is not None:
				return self.error(col)
			raise ValueError('Value is not an allowed choice')
		return col
