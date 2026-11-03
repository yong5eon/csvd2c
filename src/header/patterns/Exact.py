# -*- coding: utf-8 -*-

from typing import (
	List,
	Tuple,
)
from ..Error import Error
from ..Pattern import Pattern


class Exact(Pattern):
	"""
	Require the header to contain exactly the specified names in any order.

	Repeated names are counted separately, so a,a,b differs from a,b.
	Names are compared exactly.
	"""

	def __init__(self, *names: str) -> None:
		for name in names:
			if not isinstance(name, str):
				raise TypeError('Header names must be strings')
		self.names: Tuple[str, ...] = names
		return

	def __call__(
		self,
		value: List[str],
	) -> List[str]:
		if sorted(value) != sorted(self.names):
			raise Error('Header names do not match the specified names', value)
		return value

	def __repr__(self) -> str:
		return 'Exact({})'.format(', '.join(repr(name) for name in self.names))
