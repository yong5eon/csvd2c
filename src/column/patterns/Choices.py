# -*- coding: utf-8 -*-

from typing import Union
from ..Pattern import Pattern
from ..Error import Error


class Choices(Pattern):
	"""
	Require exact membership in the configured strings.
	"""

	def __init__(self, *values: str) -> None:
		if any(not isinstance(value, str) for value in values):
			raise TypeError('Choices must be strings')
		self.values = frozenset(values)
		return

	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		if value not in self.values:
			raise Error('Value is not an allowed choice', row, column, value)
		return value
