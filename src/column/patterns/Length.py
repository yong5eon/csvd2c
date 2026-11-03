# -*- coding: utf-8 -*-

from typing import (
	Optional,
	Union,
)
from ..Pattern import Pattern
from ..Error import Error


class Length(Pattern):
	"""
	Check inclusive Unicode code point length bounds, not byte length.
	"""

	def __init__(
		self,
		minimum: int = 0,
		maximum: Optional[int] = None,
	) -> None:
		if type(minimum) is not int or minimum < 0:
			raise ValueError('minimum must be a nonnegative integer')
		if maximum is not None and (type(maximum) is not int or maximum < minimum):
			raise ValueError('maximum must be an integer not less than minimum')
		self.minimum = minimum
		self.maximum = maximum
		return

	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		if len(value) < self.minimum or (
			self.maximum is not None and len(value) > self.maximum
		):
			raise Error('Value length is outside the configured bounds', row, column, value)
		return value
