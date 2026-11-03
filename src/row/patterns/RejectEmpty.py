# -*- coding: utf-8 -*-

from typing import List
from ..Error import Error
from ..Pattern import Pattern


class RejectEmpty(Pattern):
	"""
	Reject empty records or records whose fields are all exactly empty strings.

	Whitespace-only fields are not empty. No automatic row skipping occurs.
	"""

	def __call__(
		self,
		value: List[str],
		row: int,
	) -> List[str]:
		if not any(field != '' for field in value):
			raise Error('Empty record is not allowed', row, value)
		return value
