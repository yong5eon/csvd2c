# -*- coding: utf-8 -*-

from typing import Union
from ..Pattern import Pattern
from ..Error import Error


class RejectSurrogates(Pattern):
	"""
	Reject all surrogate code points, including surrogateescape byte markers.
	"""

	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		if any('\ud800' <= char <= '\udfff' for char in value):
			raise Error('Value contains surrogate code points', row, column, value)
		return value
