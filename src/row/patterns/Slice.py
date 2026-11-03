# -*- coding: utf-8 -*-

from typing import (
	List,
	Optional,
)
from ..Pattern import Pattern


class Slice(Pattern):
	"""
	Return a sliced copy using Python slicing semantics.

	Out-of-range bounds are clipped. Negative bounds and steps are supported.
	"""

	def __init__(
		self,
		start: Optional[int] = None,
		stop: Optional[int] = None,
		step: Optional[int] = None,
	) -> None:
		for value in (
			start,
			stop,
			step,
		):
			if value is not None and type(value) is not int:
				raise TypeError('Slice bounds and step must be integers or None')
		if step == 0:
			raise ValueError('Slice step cannot be zero')
		self.selection: slice = slice(start, stop, step)
		return

	def __call__(
		self,
		value: List[str],
		row: int,
	) -> List[str]:
		return value[self.selection]

	def __repr__(self) -> str:
		return 'Slice({!r}, {!r}, {!r})'.format(
			self.selection.start,
			self.selection.stop,
			self.selection.step,
		)
