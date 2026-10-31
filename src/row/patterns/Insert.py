# -*- coding: utf-8 -*-

from typing import List
from ..Pattern import Pattern


class Insert(Pattern):
	"""
	Insert a string into a copy using Python list.insert index semantics.
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

	def __call__(self, row: List[str]) -> List[str]:
		result: List[str] = row.copy()
		result.insert(self.index, self.value)
		return result

	def __repr__(self) -> str:
		return 'Insert({!r}, {!r})'.format(self.index, self.value)
