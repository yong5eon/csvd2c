# -*- coding: utf-8 -*-

from typing import List
from ..Pattern import Pattern
from ..Error import Error


class Replace(Pattern):
	"""
	Replace one column with an explicit string in a new record.
	"""

	def __init__(
		self,
		index: int,
		value: str,
	) -> None:
		if type(index) is not int:
			raise TypeError('index must be an integer')
		if not isinstance(value, str):
			raise TypeError('value must be a string')
		self.index = index
		self.value = value
		return

	def __call__(
		self,
		value: List[str],
		row: int,
	) -> List[str]:
		if not -len(value) <= self.index < len(value):
			raise Error('Replace column index is out of range', row, value)
		result: List[str] = value.copy()
		result[self.index] = self.value
		return result
