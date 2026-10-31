# -*- coding: utf-8 -*-

from typing import (
	List,
	Optional,
)
from ..Error import Error
from ..Pattern import Pattern


class Remove(Pattern):
	"""
	Remove a column from a copy using Python list.pop index semantics.
	"""

	def __init__(self, index: int, *, error: Optional[Error] = None) -> None:
		if error is not None and not isinstance(error, Error):
			raise TypeError('error must be a row Error instance or None')
		self.error = error
		if type(index) is not int:
			raise TypeError('index must be an integer')
		self.index = index
		return

	def __call__(self, row: List[str]) -> List[str]:
		if not -len(row) <= self.index < len(row):
			if self.error is not None:
				return self.error(row.copy())
			raise ValueError('Column index {} is out of range'.format(self.index))
		result: List[str] = row.copy()
		result.pop(self.index)
		return result

	def __repr__(self) -> str:
		return 'Remove({!r})'.format(self.index)
