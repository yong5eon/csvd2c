# -*- coding: utf-8 -*-

from typing import Union

from abc import (
	ABC,
	abstractmethod,
)

__all__ = (
	'Pattern',
)


class Pattern(ABC):
	"""
	Pattern Interface Class for Column Validator

	Sample:
	from operator import eq

	class SamplePattern(Pattern):
		def __init__(self, compare):
			super(SamplePattern, self).__init__()
			self.compare = compare
			return

		def __call__(
			self,
			value: str,
			row: int,
			column: Union[int, str],
		) -> str:
			if not eq(value, self.compare):
				raise Error('{} is not equal to {}'.format(value, self.compare), row, column, value)
			return value # if true, return parameter
	"""
	@abstractmethod
	def __call__(
		self,
		value: str,
		row: int,
		column: Union[int, str],
	) -> str:
		raise NotImplementedError('Subclasses must implement this method')

	def __repr__(self):
		return '{}()'.format(self.__class__.__name__)
