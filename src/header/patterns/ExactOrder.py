# -*- coding: utf-8 -*-

from typing import (
	List,
	Tuple,
)
from ..Error import Error
from ..Pattern import Pattern


class ExactOrder(Pattern):
	"""
	Require the header to equal the specified names in the same order.
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
		if tuple(value) != self.names:
			raise Error('Header names do not match the specified order', value)
		return value

	def __repr__(self) -> str:
		return 'ExactOrder({})'.format(', '.join(repr(name) for name in self.names))
