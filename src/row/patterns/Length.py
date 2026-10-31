# -*- coding: utf-8 -*-

from typing import (
	List,
	Optional,
)
from ..Error import Error
from ..Pattern import Pattern


class Length(Pattern):
	"""
	Require exactly count columns and return the original record unchanged.
	"""

	def __init__(self, count: int, *, error: Optional[Error] = None) -> None:
		if error is not None and not isinstance(error, Error):
			raise TypeError('error must be a row Error instance or None')
		self.error = error
		if type(count) is not int:
			raise TypeError('count must be an integer')
		if count < 0:
			raise ValueError('count must be nonnegative')
		self.count = count
		return

	def __call__(self, row: List[str]) -> List[str]:
		if len(row) != self.count:
			if self.error is not None:
				return self.error(row.copy())
			raise ValueError(
				'Expected {} columns, found {}'.format(self.count, len(row))
			)
		return row

	def __repr__(self) -> str:
		return 'Length({!r})'.format(self.count)
