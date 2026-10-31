# -*- coding: utf-8 -*-

from typing import (
	List,
	Optional,
)
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
		*,
		error: Optional[Error] = None,
	) -> None:
		if error is not None and not isinstance(error, Error):
			raise TypeError('error must be a row Error instance or None')
		self.error = error
		if type(index) is not int:
			raise TypeError('index must be an integer')
		if not isinstance(value, str):
			raise TypeError('value must be a string')
		self.index = index
		self.value = value
		return

	def __call__(self, row: List[str]) -> List[str]:
		if not -len(row) <= self.index < len(row):
			if self.error is not None:
				return self.error(row.copy())
			raise ValueError('Replace column index is out of range')
		result: List[str] = row.copy()
		result[self.index] = self.value
		return result
