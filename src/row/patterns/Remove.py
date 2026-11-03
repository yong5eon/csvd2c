# -*- coding: utf-8 -*-

from typing import List
from ..Error import Error
from ..Pattern import Pattern


class Remove(Pattern):
	"""
	Remove a column from a copy using Python list.pop index semantics.
	"""

	def __init__(self, index: int) -> None:
		if type(index) is not int:
			raise TypeError('index must be an integer')
		self.index = index
		return

	def __call__(
		self,
		value: List[str],
		row: int,
	) -> List[str]:
		if not -len(value) <= self.index < len(value):
			raise Error('Column index {} is out of range'.format(self.index), row, value)
		result: List[str] = value.copy()
		result.pop(self.index)
		return result

	def __repr__(self) -> str:
		return 'Remove({!r})'.format(self.index)
