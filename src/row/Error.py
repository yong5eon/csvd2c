# -*- coding: utf-8 -*-

from typing import List
from ..Error import Error as BaseError

__all__ = (
	'Error',
)


class Error(BaseError):
	"""
	Raised when a row Pattern rejects its input row.

	value is the row passed to the failing Pattern and row is the last
	physical line number of the record.
	"""

	def __init__(
		self,
		message: str,
		row: int,
		value: List[str],
	) -> None:
		super().__init__(message)
		self.row = row
		self.value = value
		return
