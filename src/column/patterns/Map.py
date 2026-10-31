# -*- coding: utf-8 -*-

from typing import (
	Mapping,
	Optional,
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
		*,
		error: Optional[Error] = None,
	) -> None:
		if any(
			not isinstance(key, str) or not isinstance(value, str)
			for key, value in values.items()
		):
			raise TypeError('Map keys and values must be strings')
		if error is not None and not isinstance(error, Error):
			raise TypeError('error must be a column Error instance or None')
		self.values = dict(values)
		self.error = error
		return

	def __call__(self, col: str) -> str:
		if col not in self.values:
			if self.error is not None:
				return self.error(col)
			raise ValueError('Value has no configured mapping')
		return self.values[col]
