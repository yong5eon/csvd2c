# -*- coding: utf-8 -*-

from contextlib import (
	ExitStack,
	contextmanager,
)
from csv import reader
from io import TextIOWrapper
from typing import (
	Dict,
	Generator,
	List,
	Optional,
	Tuple,
	Union,
	TYPE_CHECKING,
)

if TYPE_CHECKING:
	from _csv import Reader

from .header import (
	Error as HeaderError,
	Validator as HeaderValidator,
)
from .row import (
	Error as RowError,
	Validator as RowValidator,
)
from .column import Validator as ColumnValidator

__all__ = (
	'CSV',
)


class CSV(object):
	"""
	Read CSV records incrementally and apply row and column validators.
	"""

	def __init__(
		self,
		*,
		encoding: str = 'utf-8',
		errors: str = 'strict',
		newline: str = '',
		delimiter: str = ',',
		escapechar: Optional[str] = None,
		strict: bool = True,
		header: Optional[HeaderValidator] = None,
		row: Optional[RowValidator] = None,
		column: Optional[
			Union[
				Dict[str, ColumnValidator],
				Tuple[ColumnValidator, ...],
			]
		] = None,
	) -> None:
		self.encoding = encoding
		self.errors = errors
		self.newline = newline
		self.delimiter = delimiter
		self.escapechar = escapechar
		self.strict = strict
		self.check_header(header)
		self.check_validators(row, column)
		self.header_validator = header
		self.row_validator = row
		self.column_validators = column
		self.reader: Optional['Reader'] = None
		self.text: Optional[TextIOWrapper] = None
		self.header_data: Optional[List[str]] = None
		return

	@contextmanager
	def open(
		self,
		path: str,
		mode: str = 'rb',
		header: Optional[HeaderValidator] = None,
	) -> Generator['CSV', None, None]:
		"""
		Open a file for reading and close it on context exit.

		Support rb (default), r, and rt. Binary mode uses TextIOWrapper;
		text modes apply the same encoding, errors, and newline settings.
		header overrides the constructor header Validator for this open only;
		None uses the constructor setting. When a header Validator applies,
		the first record is read and validated before the context is entered;
		a header Error closes the file. Otherwise no record is consumed.
		Nested opens on the same CSV instance are rejected. File, decoding,
		and parsing errors propagate.
		"""
		if self.reader is not None:
			raise RuntimeError('This CSV instance is already open')
		if mode not in ('rb', 'r', 'rt'):
			raise ValueError('mode must be rb, r, or rt')
		self.check_header(header)
		validator: Optional[HeaderValidator] = self.header_validator if header is None else header

		with ExitStack() as stack:
			if mode == 'rb':
				binary = stack.enter_context(open(path, 'rb'))
				text: TextIOWrapper = stack.enter_context(
					TextIOWrapper(
						binary,
						encoding=self.encoding,
						errors=self.errors,
						newline=self.newline,
					)
				)
			else:
				text = stack.enter_context(
					open(
						path,
						mode,
						encoding=self.encoding,
						errors=self.errors,
						newline=self.newline,
					)
				)
			self.reader = reader(
				text,
				delimiter=self.delimiter,
				escapechar=self.escapechar,
				strict=self.strict,
			)
			self.header_data = None
			self.text = text
			try:
				if validator is not None:
					self.header_data = self.read_header(self.reader, validator)
				yield self
			finally:
				if self.text is text:
					self.close()
		return

	def close(self) -> None:
		"""
		Close the current stream and invalidate its readers and header.

		Repeated calls are safe. Stream closing errors propagate, and context
		exit also closes the stream automatically.
		"""
		text: Optional[TextIOWrapper] = self.text
		try:
			if text is not None:
				text.close()
		finally:
			self.text = None
			self.reader = None
			self.header_data = None
		return

	def header(self) -> Optional[List[str]]:
		"""
		Return a copy of the validated header, or None without header validation.

		No record is consumed. The header is read and validated when open()
		applies a header Validator.
		"""
		if self.header_data is None:
			return None
		return self.header_data.copy()

	def row(
		self,
		*,
		row: Optional[RowValidator] = None,
		column: Optional[
			Union[
				Dict[str, ColumnValidator],
				Tuple[ColumnValidator, ...],
			]
		] = None,
	) -> List[str]:
		"""
		Consume and validate one record, raising StopIteration at EOF.

		None uses the constructor setting. Overrides apply only to this call.
		Validation failures propagate after the record has been consumed.
		"""
		source: 'Reader' = self.require_reader()
		row_validator, column_validators = self.resolve_validators(row, column)
		indices: List[Tuple[int, Union[int, str], ColumnValidator]] = self.column_indices(column_validators)
		record: List[str] = next(source)
		line: int = source.line_num
		return self.validate(record, line, row_validator, indices)

	def rows(
		self,
		*,
		row: Optional[RowValidator] = None,
		column: Optional[
			Union[
				Dict[str, ColumnValidator],
				Tuple[ColumnValidator, ...],
			]
		] = None,
	) -> Generator[List[str], None, None]:
		"""
		Stream remaining records without accumulating results in memory.

		Overrides are captured when this method is called. The iterator must
		be consumed inside the open context and cannot be reused after the
		file is closed or reopened.
		"""
		source: 'Reader' = self.require_reader()
		row_validator, column_validators = self.resolve_validators(row, column)
		indices: List[Tuple[int, Union[int, str], ColumnValidator]] = self.column_indices(column_validators)
		return self.iterate(source, row_validator, indices)

	def read_header(
		self,
		source: 'Reader',
		validator: HeaderValidator,
	) -> List[str]:
		try:
			record: List[str] = next(source)
		except StopIteration:
			raise HeaderError('The file has no record to use as a header', None) from None
		return list(validator(record))

	def require_reader(self) -> 'Reader':
		if self.reader is None:
			raise RuntimeError('Open the CSV file before reading records')
		return self.reader

	def check_header(
		self,
		header: Optional[HeaderValidator],
	) -> None:
		if header is not None and not isinstance(header, HeaderValidator):
			raise TypeError('header must be a header Validator or None')
		return

	def check_validators(
		self,
		row: Optional[RowValidator],
		column: Optional[
			Union[
				Dict[str, ColumnValidator],
				Tuple[ColumnValidator, ...],
			]
		],
	) -> None:
		if row is not None and not isinstance(row, RowValidator):
			raise TypeError('row must be a row Validator or None')
		if column is not None:
			if isinstance(column, dict):
				for name, validator in column.items():
					if not isinstance(name, str):
						raise TypeError('Column names must be strings')
					if not isinstance(validator, ColumnValidator):
						raise TypeError('Column validators must be column Validator instances')
			elif isinstance(column, tuple):
				for validator in column:
					if not isinstance(validator, ColumnValidator):
						raise TypeError('Column validators must be column Validator instances')
			else:
				raise TypeError('column must be a dictionary, a tuple, or None')
		return

	def resolve_validators(
		self,
		row: Optional[RowValidator],
		column: Optional[
			Union[
				Dict[str, ColumnValidator],
				Tuple[ColumnValidator, ...],
			]
		],
	) -> Tuple[
		Optional[RowValidator], Optional[
			Union[
				Dict[str, ColumnValidator],
				Tuple[ColumnValidator, ...],
			]
		]
	]:
		self.check_validators(row, column)
		return (
			self.row_validator if row is None else row,
			self.column_validators if column is None else column,
		)

	def column_indices(
		self,
		column: Optional[
			Union[
				Dict[str, ColumnValidator],
				Tuple[ColumnValidator, ...],
			]
		],
	) -> List[Tuple[int, Union[int, str], ColumnValidator]]:
		if column is None:
			return []
		if isinstance(column, tuple):
			return [
				(
					index,
					index,
					validator,
				)
				for index, validator in enumerate(column)
			]
		if not column:
			return []
		if self.header_data is None:
			raise RuntimeError('Inject a header Validator before using named column validators')
		indices: List[Tuple[int, Union[int, str], ColumnValidator]] = []
		for name, validator in column.items():
			count: int = self.header_data.count(name)
			if count != 1:
				raise ValueError(
					'Column {!r} must occur exactly once in the header; found {}'.format(
						name,
						count,
					)
				)
			indices.append((
				self.header_data.index(name),
				name,
				validator,
			))
		return indices

	def validate(
		self,
		record: List[str],
		line: int,
		row: Optional[RowValidator],
		indices: List[Tuple[int, Union[int, str], ColumnValidator]],
	) -> List[str]:
		if row is not None:
			record = row(record, line)
		for index, column, validator in indices:
			if index >= len(record):
				raise RowError(
					'Column index {} is missing from a record with {} columns'.format(
						index,
						len(record),
					),
					line,
					record,
				)
			record[index] = validator(record[index], line, column)
		return record

	def iterate(
		self,
		source: 'Reader',
		row: Optional[RowValidator],
		indices: List[Tuple[int, Union[int, str], ColumnValidator]],
	) -> Generator[List[str], None, None]:
		while True:
			if self.reader is not source:
				raise RuntimeError('The CSV context has changed')
			try:
				record: List[str] = next(source)
				line: int = source.line_num
			except StopIteration:
				return
			yield self.validate(record, line, row, indices)
