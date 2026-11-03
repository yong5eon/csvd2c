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
			value: Decimal = bound if isinstance(bound, Decimal) else Decimal(self.number.normalize(str(bound)))
			if not value.is_finite():
				raise ValueError('Range bounds must be finite')
			bounds.append(value)
		self.minimum: Optional[Decimal] = bounds[0]
		self.maximum: Optional[Decimal] = bounds[1]
		if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
			raise ValueError('minimum cannot exceed maximum')
		return

	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		try:
			number: Decimal = Decimal(self.number.normalize(value))
		except ValueError as cause:
			raise Error(str(cause), row, column, value)
		if (
			(self.minimum is not None and number < self.minimum)
			or (self.maximum is not None and number > self.maximum)
		):
			raise Error('Value is outside the configured numeric range', row, column, value)
		return value
