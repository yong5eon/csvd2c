# -*- coding: utf-8 -*-

from typing import (
	List,
	Tuple,
)
from ..Pattern import Pattern
from ..Error import Error


class RejectHeader(Pattern):
	"""
	Reject a record exactly matching the specified header names in order.
	"""

	def __init__(
		self,
		*names: str,
	) -> None:
		for name in names:
			if not isinstance(name, str):
				raise TypeError('Header names must be strings')
		self.names: Tuple[str, ...] = names
		return

	def __call__(
		self,
		value: List[str],
		row: int,
	) -> List[str]:
		if tuple(value) == self.names:
			raise Error('Repeated header record is not allowed', row, value)
		return value
