# -*- coding: utf-8 -*-

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

		def __call__(self, col: str) -> str:
			if not eq(col, self.compare):
				raise ValueError('{} is not equal to {}'.format(col, self.compare))
			return col # if true, return parameter
	"""
	@abstractmethod
	def __call__(self, col: str) -> str:
		raise NotImplementedError('Subclasses must implement this method')

	def __repr__(self):
		return '{}()'.format(self.__class__.__name__)
