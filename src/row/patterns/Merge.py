# -*- coding: utf-8 -*-

from typing import (
	List,
	Optional,
)
from ..Pattern import Pattern
from ..Error import Error


class Merge(Pattern):
	"""
	Merge a nonempty [start:stop] range into one column in a new list.

	Negative bounds are supported; out-of-range bounds are rejected.
	"""

	def __init__(
		self,
		start: int,
		stop: int,
		*,
		sep: str = ',',
		error: Optional[Error] = None,
	) -> None:
		if error is not None and not isinstance(error, Error):
			raise TypeError('error must be a row Error instance or None')
		self.error = error
		if type(start) is not int or type(stop) is not int:
			raise TypeError('Merge bounds must be integers')
		if not isinstance(sep, str):
			raise TypeError('sep must be a string')
		self.start = start
		self.stop = stop
		self.sep = sep
		return

	def __call__(self, row: List[str]) -> List[str]:
		size: int = len(row)
		start: int = self.start + size if self.start < 0 else self.start
		stop: int = self.stop + size if self.stop < 0 else self.stop
		if not 0 <= start < stop <= size:
			if self.error is not None:
				return self.error(row.copy())
			raise ValueError('Merge requires a nonempty range within the record')
		return row[:start] + [self.sep.join(row[start:stop])] + row[stop:]
