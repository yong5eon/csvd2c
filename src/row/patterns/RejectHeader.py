# -*- coding: utf-8 -*-

from typing import (
	List,
	Optional,
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
		error: Optional[Error] = None,
	) -> None:
		if error is not None and not isinstance(error, Error):
			raise TypeError('error must be a row Error instance or None')
		self.error = error
		for name in names:
			if not isinstance(name, str):
				raise TypeError('Header names must be strings')
		self.names: Tuple[str, ...] = names
		return

	def __call__(self, row: List[str]) -> List[str]:
		if tuple(row) == self.names:
			if self.error is not None:
				return self.error(row.copy())
			raise ValueError('Repeated header record is not allowed')
		return row
