# -*- coding: utf-8 -*-

from typing import List
from ..Error import Error
from ..Pattern import Pattern


class RejectDuplicate(Pattern):
	"""
	Reject a header containing the same name more than once.
	"""

	def __call__(
		self,
		value: List[str],
	) -> List[str]:
		if len(set(value)) != len(value):
			raise Error('Header names must be unique', value)
		return value
