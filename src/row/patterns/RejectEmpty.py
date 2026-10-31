# -*- coding: utf-8 -*-

from typing import (
	List,
	Optional,
)
from ..Error import Error
from ..Pattern import Pattern


class RejectEmpty(Pattern):
	"""
	Reject empty records or records whose fields are all exactly empty strings.

	Whitespace-only fields are not empty. No automatic row skipping occurs.
	"""

	def __init__(self, *, error: Optional[Error] = None) -> None:
		if error is not None and not isinstance(error, Error):
			raise TypeError('error must be a row Error instance or None')
		self.error = error
		return

	def __call__(self, row: List[str]) -> List[str]:
		if not any(value != '' for value in row):
			if self.error is not None:
				return self.error(row.copy())
			raise ValueError('Empty record is not allowed')
		return row
