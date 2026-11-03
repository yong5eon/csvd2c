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
	) -> None:
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

	def __call__(
		self,
		value: List[str],
		row: int,
	) -> List[str]:
		if not -len(value) <= self.index < len(value):
			raise Error('Split column index is out of range', row, value)
		index: int = self.index % len(value)
		return value[:index] + value[index].split(self.sep, self.maxsplit) + value[index + 1:]
