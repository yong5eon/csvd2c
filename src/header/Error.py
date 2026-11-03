# -*- coding: utf-8 -*-

from typing import (
	List,
	Optional,
)
from ..Error import Error as BaseError

__all__ = (
	'Error',
)


class Error(BaseError):
	"""
	Raised when a header Pattern rejects its input header.

	value is the header passed to the failing Pattern, or None when the file
	has no record to read as a header.
	"""

	def __init__(
		self,
		message: str,
		value: Optional[List[str]],
	) -> None:
		super().__init__(message)
		self.value = value
		return
