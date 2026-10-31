# -*- coding: utf-8 -*-

from typing import (
	List,
	Optional,
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

	def __init__(self, *indices: int, error: Optional[Error] = None) -> None:
		if error is not None and not isinstance(error, Error):
			raise TypeError('error must be a row Error instance or None')
		self.error = error
		for index in indices:
			if type(index) is not int:
				raise TypeError('indices must be integers')
		self.indices: Tuple[int, ...] = indices
		return

	def __call__(self, row: List[str]) -> List[str]:
		size: int = len(row)
		if len(self.indices) != size:
			if self.error is not None:
				return self.error(row.copy())
			raise ValueError('Reorder must specify every column exactly once')
		normalized: List[int] = []
		for index in self.indices:
			position: int = index + size if index < 0 else index
			if position < 0 or position >= size:
				if self.error is not None:
					return self.error(row.copy())
				raise ValueError('Column index {} is out of range'.format(index))
			normalized.append(position)
		if len(set(normalized)) != size:
			if self.error is not None:
				return self.error(row.copy())
			raise ValueError('Reorder indices refer to duplicate columns')
		return [row[index] for index in normalized]

	def __repr__(self) -> str:
		return 'Reorder({})'.format(', '.join(repr(index) for index in self.indices))
