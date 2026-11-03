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
	Sequence,
	Tuple,
	Union,
	TYPE_CHECKING,
	overload,
)

if TYPE_CHECKING:
	from _csv import Reader

from .row import Validator as RowValidator
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
		row: Optional[RowValidator] = None,
		cols: Optional[
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
		self.check_validators(row, cols)
		self.row_validator = row
		self.column_validators = cols
		self.reader: Optional['Reader'] = None
		self.text: Optional[TextIOWrapper] = None
		self.header_data: Optional[List[str]] = None
		return

	@contextmanager
	def open(
		self,
		path: str,
		mode: str = 'rb',
	) -> Generator['CSV', None, None]:
		"""
		Open a file for reading and close it on context exit.

		Support rb (default), r, and rt. Binary mode uses TextIOWrapper;
		text modes apply the same encoding, errors, and newline settings.
		No record is consumed automatically. Nested opens on the same CSV
		instance are rejected. File, decoding, and parsing errors propagate.
		"""
		if self.reader is not None:
			raise RuntimeError('This CSV instance is already open')
		if mode not in ('rb', 'r', 'rt'):
			raise ValueError('mode must be rb, r, or rt')

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

	def header(self) -> List[str]:
		"""
		Consume the next unvalidated record and use it as the current header.

		Repeated calls consume additional records. Raise StopIteration at EOF.
		The returned list is a copy so callers cannot change column mapping.
		"""
		source: 'Reader' = self.require_reader()
		self.header_data = next(source)
		return self.header_data.copy()

	@overload
	def row(
		self,
		*,
		header: None = None,
		row: Optional[RowValidator] = None,
		cols: Optional[Union[
			Dict[str, ColumnValidator],
			Tuple[ColumnValidator, ...],
		]] = None,
	) -> List[str]:
		...

	@overload
	def row(
		self,
		*,
		header: Sequence[str],
		row: Optional[RowValidator] = None,
		cols: Optional[Union[
			Dict[str, ColumnValidator],
			Tuple[ColumnValidator, ...],
		]] = None,
	) -> Dict[str, str]:
		...

	@overload
	def row(
		self,
		*,
		header: Optional[Sequence[str]],
		row: Optional[RowValidator] = None,
		cols: Optional[Union[
			Dict[str, ColumnValidator],
			Tuple[ColumnValidator, ...],
		]] = None,
	) -> Union[List[str], Dict[str, str]]:
		...

	def row(
		self,
		*,
		header: Optional[Sequence[str]] = None,
		row: Optional[RowValidator] = None,
		cols: Optional[
			Union[
				Dict[str, ColumnValidator],
				Tuple[ColumnValidator, ...],
			]
		] = None,
	) -> Union[List[str], Dict[str, str]]:
		"""
		Consume and validate one record, raising StopIteration at EOF.

		None uses the constructor setting. Overrides apply only to this call.
		Validation failures propagate after the record has been consumed.
		An explicit header maps validated values to keys in their current order.
		It does not consume a file header or change named validator mapping.
		"""
		source: 'Reader' = self.require_reader()
		output_header: Optional[Tuple[str, ...]] = self.prepare_header(header)
		row_validator, column_validators = self.resolve_validators(row, cols)
		indices: List[Tuple[int, Union[int, str], ColumnValidator]] = self.column_indices(column_validators)
		record: List[str] = next(source)
		line: int = source.line_num
		record = self.validate(record, line, row_validator, indices)
		return self.format_record(record, output_header)

	@overload
	def rows(
		self,
		*,
		header: None = None,
		row: Optional[RowValidator] = None,
		cols: Optional[Union[
			Dict[str, ColumnValidator],
			Tuple[ColumnValidator, ...],
		]] = None,
	) -> Generator[List[str], None, None]:
		...

	@overload
	def rows(
		self,
		*,
		header: Sequence[str],
		row: Optional[RowValidator] = None,
		cols: Optional[Union[
			Dict[str, ColumnValidator],
			Tuple[ColumnValidator, ...],
		]] = None,
	) -> Generator[Dict[str, str], None, None]:
		...

	@overload
	def rows(
		self,
		*,
		header: Optional[Sequence[str]],
		row: Optional[RowValidator] = None,
		cols: Optional[Union[
			Dict[str, ColumnValidator],
			Tuple[ColumnValidator, ...],
		]] = None,
	) -> Generator[Union[List[str], Dict[str, str]], None, None]:
		...

	def rows(
		self,
		*,
		header: Optional[Sequence[str]] = None,
		row: Optional[RowValidator] = None,
		cols: Optional[
			Union[
				Dict[str, ColumnValidator],
				Tuple[ColumnValidator, ...],
			]
		] = None,
	) -> Generator[Union[List[str], Dict[str, str]], None, None]:
		"""
		Stream remaining records without accumulating results in memory.

		Overrides and header mapping are captured when this method is called.
		The iterator must be consumed inside the open context. It cannot be
		reused after the file is closed, reopened, or the header is changed.
		An explicit output header is copied at call time and maps validated
		values to keys without rearranging columns.
		"""
		source: 'Reader' = self.require_reader()
		output_header: Optional[Tuple[str, ...]] = self.prepare_header(header)
		row_validator, column_validators = self.resolve_validators(row, cols)
		indices: List[Tuple[int, Union[int, str], ColumnValidator]] = self.column_indices(column_validators)
		return self.iterate(source, self.header_data, row_validator, indices, output_header)

	def prepare_header(
		self,
		header: Optional[Sequence[str]],
	) -> Optional[Tuple[str, ...]]:
		if header is None:
			return None
		if isinstance(header, str):
			raise TypeError('header must be a sequence of column names, not a string')
		names: Tuple[str, ...] = tuple(header)
		for name in names:
			if not isinstance(name, str):
				raise TypeError('Output column names must be strings')
		if len(set(names)) != len(names):
			raise ValueError('Output column names must be unique')
		return names

	def format_record(
		self,
		record: List[str],
		header: Optional[Tuple[str, ...]],
	) -> Union[List[str], Dict[str, str]]:
		if header is None:
			return record
		if len(record) != len(header):
			raise ValueError(
				'Output header has {} columns, but the validated record has {}'.format(
					len(header),
					len(record),
				)
			)
		return dict(zip(header, record))

	def require_reader(self) -> 'Reader':
		if self.reader is None:
			raise RuntimeError('Open the CSV file before reading records')
		return self.reader

	def check_validators(
		self,
		row: Optional[RowValidator],
		cols: Optional[
			Union[
				Dict[str, ColumnValidator],
				Tuple[ColumnValidator, ...],
			]
		],
	) -> None:
		if row is not None and not isinstance(row, RowValidator):
			raise TypeError('row must be a row Validator or None')
		if cols is not None:
			if isinstance(cols, dict):
				for name, validator in cols.items():
					if not isinstance(name, str):
						raise TypeError('Column names must be strings')
					if not isinstance(validator, ColumnValidator):
						raise TypeError('Column validators must be column Validator instances')
			elif isinstance(cols, tuple):
				for validator in cols:
					if not isinstance(validator, ColumnValidator):
						raise TypeError('Column validators must be column Validator instances')
			else:
				raise TypeError('cols must be a dictionary, a tuple, or None')
		return

	def resolve_validators(
		self,
		row: Optional[RowValidator],
		cols: Optional[
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
		self.check_validators(row, cols)
		return (
			self.row_validator if row is None else row,
			self.column_validators if cols is None else cols,
		)

	def column_indices(
		self,
		cols: Optional[
			Union[
				Dict[str, ColumnValidator],
				Tuple[ColumnValidator, ...],
			]
		],
	) -> List[Tuple[int, Union[int, str], ColumnValidator]]:
		if cols is None:
			return []
		if isinstance(cols, tuple):
			return [
				(
					index,
					index,
					validator,
				)
				for index, validator in enumerate(cols)
			]
		if not cols:
			return []
		if self.header_data is None:
			raise RuntimeError('Call header() before using named column validators')
		indices: List[Tuple[int, Union[int, str], ColumnValidator]] = []
		for name, validator in cols.items():
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
				raise ValueError(
					'Column index {} is missing from a record with {} columns'.format(
						index,
						len(record),
					)
				)
			record[index] = validator(record[index], line, column)
		return record

	def iterate(
		self,
		source: 'Reader',
		header: Optional[List[str]],
		row: Optional[RowValidator],
		indices: List[Tuple[int, Union[int, str], ColumnValidator]],
		output_header: Optional[Tuple[str, ...]],
	) -> Generator[Union[List[str], Dict[str, str]], None, None]:
		while True:
			if self.reader is not source or self.header_data is not header:
				raise RuntimeError('The CSV context or header has changed')
			try:
				record: List[str] = next(source)
				line: int = source.line_num
			except StopIteration:
				return
			record = self.validate(record, line, row, indices)
			yield self.format_record(record, output_header)
