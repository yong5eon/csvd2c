# -*- coding: utf-8 -*-

from typing import Optional
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
		*,
		error: Optional[Error] = None,
	) -> None:
		if type(minimum) is not int or minimum < 0:
			raise ValueError('minimum must be a nonnegative integer')
		if maximum is not None and (type(maximum) is not int or maximum < minimum):
			raise ValueError('maximum must be an integer not less than minimum')
		if error is not None and not isinstance(error, Error):
			raise TypeError('error must be a column Error instance or None')
		self.minimum = minimum
		self.maximum = maximum
		self.error = error
		return

	def __call__(self, col: str) -> str:
		if len(col) < self.minimum or (
			self.maximum is not None and len(col) > self.maximum
		):
			if self.error is not None:
				return self.error(col)
			raise ValueError('Value length is outside the configured bounds')
		return col
