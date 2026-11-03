# -*- coding: utf-8 -*-

from typing import (
	List,
	Tuple,
)
from ..Error import Error
from ..Pattern import Pattern


class Includes(Pattern):
	"""
	Require every specified name to appear in the header.

	Additional names and order are not checked. Names are compared exactly.
	"""

	def __init__(self, *names: str) -> None:
		for name in names:
			if not isinstance(name, str):
				raise TypeError('Header names must be strings')
		self.names: Tuple[str, ...] = names
		return

	def __call__(
		self,
		value: List[str],
	) -> List[str]:
		missing: List[str] = [name for name in self.names if name not in value]
		if missing:
			raise Error('Header is missing names: {}'.format(', '.join(missing)), value)
		return value

	def __repr__(self) -> str:
		return 'Includes({})'.format(', '.join(repr(name) for name in self.names))
