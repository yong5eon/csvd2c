# -*- coding: utf-8 -*-

from typing import List
from ..Error import Error
from ..Pattern import Pattern


class Length(Pattern):
	"""
	Require exactly count columns and return the original record unchanged.
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
		if len(value) != self.count:
			raise Error(
				'Expected {} columns, found {}'.format(self.count, len(value)),
				row,
				value,
			)
		return value

	def __repr__(self) -> str:
		return 'Length({!r})'.format(self.count)
