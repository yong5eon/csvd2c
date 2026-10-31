# -*- coding: utf-8 -*-

from decimal import Decimal
from typing import (
	Optional,
	List,
	Union,
)
from ..Pattern import Pattern
from ..Error import Error
from .Number import Number


class Range(Pattern):
	"""
	Check inclusive numeric bounds and return the original string.

	Input uses ungrouped decimal notation; apply Number first for other formats.
	Bounds accept finite Decimal, integer, or ungrouped decimal strings.
	"""

	def __init__(
		self,
		minimum: Optional[Union[Decimal, int, str]] = None,
		maximum: Optional[Union[Decimal, int, str]] = None,
		*,
		error: Optional[Error] = None,
	) -> None:
		if minimum is None and maximum is None:
			raise ValueError('At least one range bound is required')
		self.number = Number()
		bounds: List[Optional[Decimal]] = []
		for bound in (
			minimum,
			maximum,
		):
			if bound is None:
				bounds.append(None)
				continue
			if not isinstance(bound, (Decimal, str)) and type(bound) is not int:
				raise TypeError('Range bounds must be Decimal, integer, string, or None')
			value: Decimal = bound if isinstance(bound, Decimal) else Decimal(self.number(str(bound)))
			if not value.is_finite():
				raise ValueError('Range bounds must be finite')
			bounds.append(value)
		self.minimum: Optional[Decimal] = bounds[0]
		self.maximum: Optional[Decimal] = bounds[1]
		if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
			raise ValueError('minimum cannot exceed maximum')
		if error is not None and not isinstance(error, Error):
			raise TypeError('error must be a column Error instance or None')
		self.error = error
		return

	def __call__(self, col: str) -> str:
		try:
			value: Decimal = Decimal(self.number(col))
		except ValueError:
			if self.error is not None:
				return self.error(col)
			raise
		if (
			(self.minimum is not None and value < self.minimum)
			or (self.maximum is not None and value > self.maximum)
		):
			if self.error is not None:
				return self.error(col)
			raise ValueError('Value is outside the configured numeric range')
		return col
