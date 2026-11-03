# -*- coding: utf-8 -*-

from typing import Union
from ..Error import Error as BaseError

__all__ = (
	'Error',
)


class Error(BaseError):
	"""
	Raised when a column Pattern rejects its input value.

	value is the string passed to the failing Pattern, row is the last
	physical line number of the record, and column is its index or name.
	"""

	def __init__(
		self,
		message: str,
		row: int,
		column: Union[int, str],
		value: str,
	) -> None:
		super().__init__(message)
		self.row = row
		self.column = column
		self.value = value
		return
