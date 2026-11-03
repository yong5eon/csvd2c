# -*- coding: utf-8 -*-

from typing import List
from ..Pattern import Pattern


class Truncate(Pattern):
	"""
	Return a copy with trailing columns beyond count removed.

	Records with count or fewer columns retain all their values.
	"""

	def __init__(self, count: int) -> None:
		if type(count) is not int:
			raise TypeError('count must be an integer')
		if count < 0:
			raise ValueError('count must be nonnegative')
		self.count = count
		return

	def __call__(
		self,
		value: List[str],
		row: int,
	) -> List[str]:
		return value[:self.count]

	def __repr__(self) -> str:
		return 'Truncate({!r})'.format(self.count)
