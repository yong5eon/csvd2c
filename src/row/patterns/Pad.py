# -*- coding: utf-8 -*-

from typing import List
from ..Pattern import Pattern


class Pad(Pattern):
	"""
	Return a copy padded with value at the end until it has count columns.

	Records with count or more columns retain all their values.
	"""

	def __init__(
		self,
		count: int,
		value: str = '',
	) -> None:
		if type(count) is not int:
			raise TypeError('count must be an integer')
		if count < 0:
			raise ValueError('count must be nonnegative')
		if not isinstance(value, str):
			raise TypeError('value must be a string')
		self.count = count
		self.value = value
		return

	def __call__(
		self,
		value: List[str],
		row: int,
	) -> List[str]:
		return value + [self.value] * max(0, self.count - len(value))

	def __repr__(self) -> str:
		return 'Pad({!r}, {!r})'.format(self.count, self.value)
