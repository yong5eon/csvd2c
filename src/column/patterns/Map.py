# -*- coding: utf-8 -*-

from typing import (
	Mapping,
	Union,
)
from ..Pattern import Pattern
from ..Error import Error


class Map(Pattern):
	"""
	Map exact strings to strings using a copied lookup table.
	"""

	def __init__(
		self,
		values: Mapping[str, str],
	) -> None:
		if any(
			not isinstance(key, str) or not isinstance(value, str)
			for key, value in values.items()
		):
			raise TypeError('Map keys and values must be strings')
		self.values = dict(values)
		return

	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		if value not in self.values:
			raise Error('Value has no configured mapping', row, column, value)
		return self.values[value]
