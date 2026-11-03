# -*- coding: utf-8 -*-

from decimal import Decimal
from re import (
	compile,
	escape,
)
from typing import (
	Optional,
	Union,
)
from ..Pattern import Pattern
from ..Error import Error


class Number(Pattern):
	"""
	Normalize finite decimal notation with explicitly configured separators.

	Require integer digits and, if present, fractional digits. Grouping uses
	three digits per group. Exponents and surrounding whitespace are rejected.
	"""

	def __init__(
		self,
		*,
		decimal: str = '.',
		thousands: Optional[str] = None,
	) -> None:
		for separator in (
			decimal,
			thousands,
		):
			if separator is not None and (
				not isinstance(separator, str)
				or len(separator) != 1
				or separator.isalnum()
				or separator in '+-'
			):
				raise ValueError('Separators must be single non-alphanumeric characters')
		if decimal is None or decimal == thousands:
			raise ValueError('Decimal separator is required and must differ from thousands')
		integer: str = r'[0-9]+'
		if thousands is not None:
			integer = r'(?:[0-9]+|[0-9]{1,3}(?:' + escape(thousands) + r'[0-9]{3})+)'
		self.expression = compile(r'[+-]?' + integer + '(?:' + escape(decimal) + r'[0-9]+)?')
		self.decimal = decimal
		self.thousands = thousands
		return

	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		try:
			result: str = self.normalize(value)
		except ValueError as cause:
			raise Error(str(cause), row, column, value)
		return result

	def normalize(self, col: str) -> str:
		"""
		Normalize a decimal string without record context or error handling.
		"""
		if self.expression.fullmatch(col) is None:
			raise ValueError('Value is not a valid decimal with the configured grouping')
		text: str = col
		if self.thousands is not None:
			text = text.replace(self.thousands, '')
		text = text.replace(self.decimal, '.')
		value: Decimal = Decimal(text)
		if value.is_zero():
			return '0'
		result: str = format(value, 'f')
		if '.' in result:
			result = result.rstrip('0').rstrip('.')
		return result
