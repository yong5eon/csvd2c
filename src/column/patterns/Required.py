# -*- coding: utf-8 -*-

from typing import Union
from ..Pattern import Pattern
from ..Error import Error


class Required(Pattern):
	"""
	Reject exactly empty strings; strip whitespace separately when needed.
	"""

	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		if value == '':
			raise Error('A nonempty value is required', row, column, value)
		return value
