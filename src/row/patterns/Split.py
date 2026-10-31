# -*- coding: utf-8 -*-

from typing import (
	List,
	Optional,
)
from ..Pattern import Pattern
from ..Error import Error


class Split(Pattern):
	"""
	Split one column using str.split and return a new record.
	"""

	def __init__(
		self,
		index: int,
		*,
		sep: Optional[str] = ',',
		maxsplit: int = -1,
		error: Optional[Error] = None,
	) -> None:
		if error is not None and not isinstance(error, Error):
			raise TypeError('error must be a row Error instance or None')
		self.error = error
		if type(index) is not int or type(maxsplit) is not int:
			raise TypeError('index and maxsplit must be integers')
		if sep is not None and not isinstance(sep, str):
			raise TypeError('sep must be a string or None')
		if sep == '':
			raise ValueError('sep cannot be empty')
		self.index = index
		self.sep = sep
		self.maxsplit = maxsplit
		return

	def __call__(self, row: List[str]) -> List[str]:
		if not -len(row) <= self.index < len(row):
			if self.error is not None:
				return self.error(row.copy())
			raise ValueError('Split column index is out of range')
		index: int = self.index % len(row)
		return row[:index] + row[index].split(self.sep, self.maxsplit) + row[index + 1:]
