# -*- coding: utf-8 -*-

from typing import (
	List,
	Tuple,
)
from ..Pattern import Pattern
from ..Error import Error


class Reorder(Pattern):
	"""
	Return a reordered copy, requiring every column exactly once.

	Negative indices follow Python indexing. Coverage and duplicate checks
	are performed against each record after normalizing negative indices.
	"""

	def __init__(self, *indices: int) -> None:
		for index in indices:
			if type(index) is not int:
				raise TypeError('indices must be integers')
		self.indices: Tuple[int, ...] = indices
		return

	def __call__(
		self,
		value: List[str],
		row: int,
	) -> List[str]:
		size: int = len(value)
		if len(self.indices) != size:
			raise Error('Reorder must specify every column exactly once', row, value)
		normalized: List[int] = []
		for index in self.indices:
			position: int = index + size if index < 0 else index
			if position < 0 or position >= size:
				raise Error('Column index {} is out of range'.format(index), row, value)
			normalized.append(position)
		if len(set(normalized)) != size:
			raise Error('Reorder indices refer to duplicate columns', row, value)
		return [value[index] for index in normalized]

	def __repr__(self) -> str:
		return 'Reorder({})'.format(', '.join(repr(index) for index in self.indices))
