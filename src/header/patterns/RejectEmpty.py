# -*- coding: utf-8 -*-

from typing import List
from ..Error import Error
from ..Pattern import Pattern


class RejectEmpty(Pattern):
	"""
	Reject a header containing an exactly empty name.

	Whitespace-only names are not empty. A header without fields passes;
	use Length to reject it.
	"""

	def __call__(
		self,
		value: List[str],
	) -> List[str]:
		if '' in value:
			raise Error('Header names cannot be empty', value)
		return value
