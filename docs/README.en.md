# csvd2c user guide

[한국어](./README.md)

This guide covers CSV record reads, row/column cleansing rules, and error handling rules. See the [project introduction](../README.en.md) for installation and quick start and the [samples index](../samples/README.en.md) for complete runnable examples.

## Reading and cleansing flow

A Validator executes its Patterns in order. Row Patterns operate on column counts, positions, and contents; column Patterns operate on individual strings.

```mermaid
flowchart LR
  A["File bytes"] --> B["Text decoding"]
  B --> C["CSV record parsing"]
  C --> D["Row Validator"]
  D --> E["Column Validator"]
  E --> F["Return list"]
```

When a header Validator is injected, `open()` reads and validates the first record as the header. Subsequent `row()` or `rows()` calls read records and apply row validation before column validation. Errors propagate to the caller.

## Contents

- [Usage rules](#usage-rules): encoding candidate checks, modes, output types, and lifetime
- [Read range](#read-range): selecting records with `offset` and `limit`
- [Header validation](#header-validation): header Validator injection, provided Patterns, renaming, and migration
- [Row structure Patterns](#row-structure-patterns): reordering, merging, splitting, and error handling
- [Column Patterns](#column-patterns): text, dates, numbers, currencies, and encoding recovery
- [Processing principles](#processing-principles): original-data preservation and large-input constraints

## Usage rules

- `detect_encoding(path, *args)` checks an initial sample of up to 1MiB in candidate order and returns the first success. One additional byte determines whether the sample reaches EOF. Missing candidates, empty files, and failure of all candidates are errors. BOMs do not automatically select candidates; use `utf-8-sig` for UTF-8 BOM handling. Sample success guarantees neither the actual encoding nor whole-file validity.
- `CSV.open(path)` wraps a binary file in `TextIOWrapper` and closes it on context exit. Without a header Validator, it does not consume the first record.
- `open(path, mode="rb", header=None, offset=None, limit=None)` supports read-only `rb`, `r`, and `rt`. Text modes use the constructor's encoding, errors, and newline settings. Write, append, and update modes are rejected before opening the file. See [header validation](#header-validation) for `header` and [read range](#read-range) for `offset` and `limit`.
- `close()` immediately closes the current stream and clears the header, reading state, and range. Repeated calls are safe; generators from a closed stream cannot be reused.
- `header()` reads no record and returns a copy of the header validated by `open()`, or `None` without header validation.
- `row()` returns the next record as a list. `rows()` is a generator of remaining records as lists. Both share the file position and must be used inside the open context. Without a header Validator, the first result of a file with a header is the header record.
- `row()` raises `StopIteration` at EOF; `rows()` ends normally.
- Constructor `row` and `column` configure row and column Validators. `row(row=..., column=...)` and `rows(row=..., column=...)` override them only for that call. Omitted arguments or `None` use constructor settings; no settings means no validation.
- Dictionary `column` validates only named columns of the validated header and requires a header Validator. Missing or duplicate selected names are errors. Tuple `column` validates only the specified prefix.
- Row validation runs before column validation. Header/record column count equality is not enforced automatically; define structural rules in row Patterns. Missing selected record columns are errors.
- `rows()` selects validators and header mapping when called. Closing the context or reopening the file invalidates existing generators.
- Use `delimiter="\t"` for TSV. The default delimiter is comma, with `strict=True` CSV parsing. `escapechar` defaults to `None`; set `escapechar="\\"` to read input such as quoted fields containing backslash-escaped quotes. Parsing and configuration errors follow Python's standard `csv.reader`.

For example, if the first record in `input.tsv` is a header and the next record is `1<TAB>"Acme \"quoted\" name"`, this configuration reads the data row as `['1', 'Acme "quoted" name']`:

```python
from csvd2c import CSV
from csvd2c.header import Validator as HeaderValidator

with CSV(
  delimiter="\t",
  escapechar="\\",
  strict=True,
  header=HeaderValidator(),
).open("input.tsv") as data:
  print(data.row())
```

- Decoding, parsing, and validation errors propagate. Consumed records are not automatically retried, and errors are not automatically recovered.
- `surrogateescape` preserves undecodable bytes but does not repair them. Validate these values before sending them to a database. Already stored `�` requires separate validation.
- Input is not loaded in full, but oversized records can increase memory usage. Do not indiscriminately increase the CSV parser's field size limit.

## Read range

`offset` is the number of records to skip, and `limit` is the maximum number of records to read with `row()` and `rows()`. You can process part of a file without counting records yourself or reading records to discard with an empty Validator.

### Configuration

Set the range only on the `CSV` constructor and `open()`. `row()` and `rows()` take no range arguments.

| Location | Arguments | Meaning |
| --- | --- | --- |
| Constructor | `offset=0`, `limit=None` | Default range for every `open()`. `limit=None` means no limit |
| `open()` | `offset=None`, `limit=None` | Applies to this open only. Omitted or `None` uses the constructor value |

- Values are non-negative integers. Non-integers and `True`/`False` raise `TypeError`; negative values raise `ValueError`. `open()` values are checked before the file is opened.
- `offset` and `limit` are overridden independently. For example, a constructor `limit=100` with `open(path, offset=200)` reads with `offset=200, limit=100`.
- `None` on `open()` means the constructor value, so a constructor `limit` cannot be removed on `open()`. If some files must be read without a limit, do not set `limit` on the constructor; set it on each `open()` instead.
- Counting restarts on every `open()`. No range or progress from a previous open remains.

### Record positions

Positions start at 0. The unit is a logical record, not a physical line, so a record with a newline inside a quoted field counts once. csvd2c does not decide whether the first record is a header. A header read by `open()` with a header Validator is not counted; otherwise the first record of the file is position 0.

| File line | Content | With header Validator | Without header Validator |
| --- | --- | --- | --- |
| 1 | `id,name` | Header (not counted) | 0 |
| 2 | `1,Kim` | 0 | 1 |
| 3 | `2,Lee` | 1 | 2 |

### Reading flow

Each `row()` call, and each record requested by `rows()`, is processed in this order:

```mermaid
flowchart TD
  A["Record requested"] --> B{"limit reached?"}
  B -- Yes --> C["End: row() raises StopIteration, rows() stops"]
  B -- No --> D{"offset records left to skip?"}
  D -- Yes --> E["Read a record and discard it without validation"] --> D
  D -- No --> F["Read a record, use 1 of the limit"]
  F --> G["Row Validator → column Validators"]
  G --> H["Return a list or raise a validation Error"]
```

- The offset records are read and discarded on the first record request. `open()` does not read them. Skipped records are not validated by row or column Validators, but decoding and parsing errors propagate because the record boundary cannot be determined. An offset larger than the number of records ends reading immediately.
- The limit counts records read, not successful records. Records that fail row or column validation count as one each. Decoding or parsing errors that yield no record are not counted.
- After the limit is reached, the next record is not read, so a parsing error in that record is not raised. `limit=0` reads no record, including the offset records.
- `row()` and `rows()` share the same range state. Mixed calls, or calling `rows()` again after a validation failure, continue within the same range.
- Without a range, reading continues to the end of the file as before.

### Example

This example creates a temporary file and reads two records at a time. The third record fails validation because its name is empty, but it still counts toward the limit.

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from csvd2c import CSV
from csvd2c.column import (
  Error as ColumnError,
  Validator as ColumnValidator,
)
from csvd2c.column.patterns import Required
from csvd2c.header import Validator as HeaderValidator

with TemporaryDirectory() as directory:
  path = Path(directory) / "input.csv"
  path.write_bytes(b"id,name\n1,Kim\n2,Lee\n3,\n4,Park\n5,Choi\n")
  csv = CSV(
    header=HeaderValidator(),
    column={"name": ColumnValidator(Required())},
    limit=2,
  )
  for offset in (0, 2, 4):
    with csv.open(str(path), offset=offset):
      page = []
      while True:
        try:
          page.append(csv.row())
        except ColumnError as error:
          print("rejected line", error.row)
        except StopIteration:
          break
      print(offset, page)
```

Expected output:

```text
0 [['1', 'Kim'], ['2', 'Lee']]
rejected line 4
2 [['4', 'Park']]
4 [['5', 'Choi']]
```

See [read_range.py](../samples/read_range.py) for a complete runnable sample.

## Header validation

csvd2c does not decide whether the first record is a header. With a header Validator, the first record is treated as the header; without one, every record is read as data.

### Injection and behavior

A header Validator is a `csvd2c.header.Validator`, passed as `header` to the constructor or `open()`. The constructor value is the default; a value passed to `open()` applies only while that file is open. Passing `None` or omitting it uses the constructor value, and reopening the file uses the constructor value again.

```mermaid
flowchart TD
  Open["open()"] --> Has{"Header Validator?"}
  Has -- no --> Ready["Enter context; header() is None"]
  Has -- yes --> Read["Read first record"]
  Read -- no record --> Empty["header.Error(value=None); close file"]
  Read --> Validate["Run header Validator"]
  Validate -- failure --> Fail["Propagate header.Error; close file"]
  Validate -- success --> Store["Store result as header; enter context"]
```

- With a header Validator, `open()` reads and validates the first record before entering the `with` block. The first `row()` reads the second record.
- On failure, the exception propagates from `open()` and the file is closed. The failed header is not stored. An empty file raises `csvd2c.header.Error` with `value` set to `None`.
- The Validator's return value becomes the header names. `header()` returns a copy without reading records.
- Named column Validators (dictionary `column`) locate columns by the stored header. Each name must occur exactly once; otherwise the first `row()` or `rows()` raises `ValueError`.

Header Patterns and Validators take a list of header names and return a list of names: `__call__(value: List[str]) -> List[str]`, without line numbers or column identifiers. Failures raise `csvd2c.header.Error(message, value)`, a subclass of the common `csvd2c.Error`; `value` is the header passed to the failing Pattern.

### Provided Patterns

Import from `csvd2c.header.patterns`. Names are compared exactly, without changing case or whitespace.

| Pattern | Rejects when |
| --- | --- |
| `RejectEmpty()` | A name is exactly empty. A header without fields passes |
| `RejectDuplicate()` | A name occurs more than once |
| `Length(count)` | The number of names differs from `count` |
| `Includes(*names)` | A specified name is missing. Extra names and order are not checked |
| `Exact(*names)` | The names differ from the specified names when order is ignored. Repeated names count separately |
| `ExactOrder(*names)` | The names differ from the specified names in value or order |

`Exact("a", "b")` accepts `b,a` and rejects `a,a,b`. To reject an empty header line (zero fields), combine `Length` or a name-list check. The header `RejectEmpty` shares only its name with the row Pattern `csvd2c.row.patterns.RejectEmpty`; use aliases when importing both. BOMs and trailing empty headers are not corrected automatically; read UTF-8 BOM files with `encoding="utf-8-sig"`.

```python
from csvd2c import CSV
from csvd2c.column import Validator
from csvd2c.column.patterns import Required
from csvd2c.header import Error as HeaderError
from csvd2c.header import Validator as HeaderValidator
from csvd2c.header.patterns import (
  ExactOrder,
  RejectDuplicate,
  RejectEmpty,
)

csv = CSV(
  header=HeaderValidator(RejectEmpty(), RejectDuplicate(), ExactOrder("name", "date")),
  column={"name": Validator(Required())},
)
try:
  with csv.open("input.csv"):
    print(csv.header())
    for record in csv.rows():
      print(record)
except HeaderError as error:
  print("Invalid header:", error.value, error.message)
```

If `input.csv` starts with `name,date`, this prints the header and data records. Otherwise it does not enter the `with` block and prints `Invalid header:`.

### Renaming

The header Validator's return value becomes the header names, so a custom Pattern can rename columns for named column mapping. A renaming Pattern is not provided.

```python
from typing import Dict, List
from csvd2c.header import Pattern, Validator

class Rename(Pattern):
  def __init__(self, names: Dict[str, str]) -> None:
    self.names = dict(names)

  def __call__(self, value: List[str]) -> List[str]:
    return [self.names.get(name, name) for name in value]

validator = Validator(Rename({"customer name": "name"}))
assert validator(["customer name", "date"]) == ["name", "date"]
```

With this Validator injected, `column={"name": ...}` applies to the `customer name` column.

### Migration

| Previous usage | Now |
| --- | --- |
| `csv.header()` consumed the first record as the header | Inject `CSV(header=HeaderValidator())` or `open(path, header=HeaderValidator())`, then read it with `csv.header()` |
| Repeated `header()` calls consumed further records | Not supported. Read data records with `row()` |
| `cols=` | `column=` |
| `row(header=...)` or `rows(header=...)` returned dictionaries | Convert the list yourself, for example `dict(zip(csv.header(), record))` |

## Validation positions and error contracts

Row `Pattern` and `Validator` use `__call__(value: List[str], row: int) -> List[str]`; column implementations use `__call__(value: str, row: int, column: Union[int, str]) -> str`, omitting `self` here. Direct calls require position arguments. Existing one-argument custom Patterns must be migrated to these signatures.

Injecting Validators into CSV supplies positions automatically. Line numbers are 1-based physical file lines, captured after reading the entire record. A quoted record spanning lines 2–3 reports line 3, not the precise offending character or a logical record number. Tuple column validators receive a 0-based index; named validators receive the configured name.

Validation failures are reported as exceptions:

| Class | Base | Constructor | Attributes |
| --- | --- | --- | --- |
| `csvd2c.Error` | `Exception` | `message` | `message` |
| `csvd2c.row.Error` | `csvd2c.Error` | `message, row, value: List[str]` | `message`, `row`, `value` |
| `csvd2c.column.Error` | `csvd2c.Error` | `message, row, column, value: str` | `message`, `row`, `column`, `value` |

`value` is the input of the failing Pattern. If `Strip` transforms `"   "` into `""` and `Required` fails, `value` is `""`. File-original and chain-start snapshots are not retained. Column validation uses the row after row transformations, without tracing fields back to earlier positions. Raise or subclass `csvd2c.Error` for failures without an identifiable position.

```python
from csvd2c.column import Error, Validator
from csvd2c.column.patterns import Required, Strip

validator = Validator(Strip(), Required())
try:
  validator("   ", 2, "name")
except Error as error:
  assert (error.row, error.column, error.value) == (2, "name", "")
  assert error.message == "A nonempty value is required"
```

The per-Pattern `error=` arguments and callable Error handlers have been removed. Callers log, recover, or skip with `try`/`except`. Data validation failures are no longer `ValueError`; replace `except ValueError` with `csvd2c.row.Error`, `csvd2c.column.Error`, or the common `csvd2c.Error`. Configuration errors still raise `TypeError` or `ValueError` immediately. If a record lacks a position selected by a column Validator after row validation, `csvd2c.row.Error` is raised.

Custom Patterns may raise these classes or their subclasses on failure, or return values without raising.

To log failed records and continue, inject Validators directly into CSV, catch only validation errors, and call `row()` again, as in the [rejection sample](../samples/reject_records.py). The same `rows()` generator cannot resume after an exception. Parsing and file decoding failures are not validation errors; positions and source text are not guessed.

```mermaid
flowchart LR
  CSV["CSV: record and final line"] --> Row["Row Validator: value and line"]
  Row --> Col["Column Validator: changed value and position"]
  Col --> Pattern["Pattern: current input"]
  Pattern -- failure --> Raise["raise row.Error / column.Error"]
  Raise --> Caller["Caller except: log or skip"]
```

## Row structure Patterns

Available row Patterns are imported from `csvd2c.row.patterns`:

- `Length(count)`: require exactly count columns; mismatch raises row Error.
- `Truncate(count)`: remove trailing excess columns; keep all values when count or fewer columns exist.
- `Pad(count, value="")`: append the specified string for missing columns; keep all values when count or more columns exist.
- `Insert(index, value)`: insert a string using Python `list.insert`, including index clipping.
- `Remove(index)`: remove one column using Python indexing; out-of-range indices raise row Error.
- `Reorder(*indices)`: require every column exactly once; reject missing, duplicate, and out-of-range indices.
- `Slice(start=None, stop=None, step=None)`: Python slicing with clipping and negative indices/steps; reject zero step.
- `Merge(start, stop, sep=",")`: merge a nonempty, in-range slice with exclusive stop.
- `Split(index, sep=",", maxsplit=-1)`: split one field using `str.split`.
- `Replace(index, value)`: replace one field with an explicit string.
- `IfLength(count, *patterns)`: run nested Patterns only for matching input counts.
- `RejectEmpty()`: reject empty records or records consisting entirely of empty strings, not whitespace.
- `RejectHeader(*names)`: reject exact header repetitions, including order.

On data failure, Length, Remove, Reorder, Merge, Split, Replace, RejectEmpty, and RejectHeader raise `csvd2c.row.Error` carrying the Pattern's input row and line number. Configuration errors still raise `TypeError` or `ValueError` immediately. No automatic skipping occurs. Insert, Slice, Pad, and Truncate have no data failures.

```python
from csvd2c.row import Validator
from csvd2c.row.patterns import (
  IfLength,
  Length,
  Merge,
)

validator = Validator(
  IfLength(4, Merge(1, 3, sep=",")),
  Length(3),
)
```

Nonmatching counts pass unchanged. Nested exceptions propagate. Compose a final Length check when needed.

Transformations return new lists; `Length` returns the original list unchanged. Negative indices are supported, and `Reorder` checks duplicates after normalization. Callers specify correction positions and values without automatic inference.

```python
from csvd2c.row import Validator
from csvd2c.row.patterns import (
  Length,
  Remove,
)

validator = Validator(
  Remove(1),
  Length(2),
)
result: list[str] = validator(["Kim", "unused", "1-10"], 1)
```

Use this example only when the second column is confirmed to be unwanted.

Explicitly compose trailing truncation and padding when this policy is appropriate:

```python
from csvd2c.row import Validator
from csvd2c.row.patterns import (
  Length,
  Pad,
  Truncate,
)

validator = Validator(
  Truncate(2),
  Pad(2),
  Length(2),
)
```

Counts must be nonnegative integers and padding values must be strings. Both Patterns return new lists without modifying input. This policy does not repair missing middle columns or incorrectly split fields. Preserve the source separately because truncated values are absent from the result.

## Column Patterns

Import from `csvd2c.column.patterns`. Patterns accept a string, line number, and column identifier and return a string, including normalized dates and numbers. Configuration errors are immediate. Data validation failures raise `csvd2c.column.Error` carrying the Pattern's input string and position.

| Pattern | Behavior |
| --- | --- |
| `Strip(chars=None)` | Strip surrounding whitespace or selected characters |
| `CollapseWhitespace()` | Collapse Unicode whitespace runs to one space, without trimming |
| `Replace(old, new, count=-1)` | Literal str.replace semantics |
| `RegexReplace(expression, replacement, count=0, flags=0)` | Regex substitution; zero replaces all matches |
| `Lower()`, `Upper()`, `CaseFold()` | Unicode case transformations |
| `UnicodeNormalize(form="NFC")` | NFC, NFD, NFKC, or NFKD normalization |
| `Required()` | Reject exactly empty strings |
| `Length(minimum=0, maximum=None)` | Inclusive code point length bounds |
| `Regex(expression, flags=0)` | Require fullmatch |
| `Choices(*values)` | Exact allowed string membership |
| `RejectCharacters(chars)` | Reject explicitly selected characters |
| `RejectSurrogates()` | Reject U+D800 through U+DFFF, including surrogateescape markers |
| `RejectReplacementCharacter()` | Reject U+FFFD, not ordinary question marks |
| `Map(values)` | Copy a string mapping and reject unknown values |
| `Default(value)` | Replace exactly empty strings |
| `Date(*formats, output="%Y-%m-%d")` | Parse complete dates and reject distinct interpretations |
| `Number(decimal=".", thousands=None)` | Validate grouping and normalize through Decimal |
| `Range(minimum=None, maximum=None)` | Inclusive numeric bounds, preserving input text |
| `Recode(stored_encoding, original_encoding)` | Reverse an explicitly known misdecoding path |
| `Currency(mapping=None)` | Normalize currency prefixes to ISO 4217 codes, preserving amount formatting |
| `IfEmpty(*patterns)` | Apply nested Patterns only to empty strings |
| `IfMatch(expression, *patterns, flags=0)` | Apply nested Patterns only on fullmatch |
| `IfUndecodable(*patterns)` | Apply nested Patterns only for U+DC80 through U+DCFF markers |
| `RecoverEncoding(source, read_encoding="utf-8")` | Restore field bytes with surrogateescape and strictly decode the specified source |
| `TryRecoverEncoding(source, read_encoding="utf-8")` | Try only marked fields; preserve the input on codec failure |

Required, Length, Regex, Choices, the three rejection checks, Map, Date, Number, Range, Currency, Recode, and RecoverEncoding raise `csvd2c.column.Error` on failure. Conditional Patterns propagate nested exceptions.

```python
from csvd2c.column import Validator
from csvd2c.column.patterns import (
  Date,
  Number,
  Range,
  Required,
  Strip,
)

name_validator = Validator(Strip(), Required())
date_validator = Validator(Date("%Y-%m-%d", "%d/%m/%Y"))
amount_validator = Validator(
  Number(thousands=","),
  Range(minimum=0, maximum=1000000),
)
```

### Important constraints

For fields known to originate in CP1258 and read through UTF-8 with surrogateescape:

```python
from csvd2c import CSV
from csvd2c.column import Validator
from csvd2c.column.patterns import (
  IfUndecodable,
  RecoverEncoding,
  RejectSurrogates,
)
from csvd2c.header import Validator as HeaderValidator

csv = CSV(
  encoding="utf-8",
  errors="surrogateescape",
  header=HeaderValidator(),
  column={
    "description": Validator(
      IfUndecodable(RecoverEncoding("cp1258")),
      RejectSurrogates(),
    ),
  },
)
```

RecoverEncoding re-encodes using the original reading codec with surrogateescape, then strictly decodes source. Failures raise `csvd2c.column.Error`. Apply before stripping, replacement, or Unicode normalization. Results are strings; encode UTF-8 at output. Missing markers do not prove correctness, and successful source decoding does not identify its actual encoding. This cannot repair mixed encodings inside a field, already replaced characters, or information removed by BOM/newline transformations.

Currency validates the 178 codes in the [SIX ISO 4217 List One](https://www.six-group.com/dam/download/financial-information/data-center/iso-currrency/lists/list-one.xml) snapshot published 2026-09-17, including fund, metal, testing, and no-currency codes. It performs no runtime network requests. Withdrawn codes are excluded; future changes require updating the snapshot.

Immutable module constants `CURRENCY_CODES` (code set) and `CURRENCY_ALIASES` (prefix-to-code mapping) are exported from `csvd2c.column.patterns` and the Currency module. The mapping includes code identity mappings and 3,310 aliases. Names, plural variants, and symbols come from [pinned Unicode CLDR data](https://github.com/unicode-org/cldr-json/tree/7d2b9cb11cec08f4d333ad73209deb3df0711c3b/cldr-json/cldr-numbers-full/main) for en, ko, ja, zh, de, fr, es, ar, ru, and hi. Shared aliases are excluded except for existing explicit symbol policies. This is not exhaustive coverage of every regional abbreviation. Unicode-3.0 notices are retained in the data module.

```python
from csvd2c.column.patterns import Currency

currency = Currency()
result: str = currency("CA$1,000", 1, "amount")  # CAD 1,000
custom = Currency({"C$": "CAD"})
```

- Won/fullwidth won maps to KRW, bare dollar/fullwidth dollar to USD, bare yen/fullwidth yen to JPY, euro to EUR, pound/fullwidth pound to GBP, Indian rupee to INR, and ruble to RUB. Bare dollar and yen interpretation is an explicit project policy, not a unique international meaning.
- Country aliases include CA$, AU$, US$, NZ$, HK$, SG$, JP¥, CN¥, CA＄, AU＄, US＄, JP￥, and CN￥. CA/AU/JP/CN followed only by replacement characters or surrogate code points maps to CAD/AUD/JPY/CNY. This identifies currency from the prefix rather than restoring lost symbols.
- Custom mappings are copied, case-sensitive prefix-to-current-code mappings. They override aliases but cannot redirect existing ISO codes. Longer aliases take precedence.
- `US Dollar 100`, `미국 달러 100`, and `日本円 100` normalize to USD, USD, and JPY respectively. Aliases are input interpretation policies, not part of the ISO code standard.
- Output is `CODE amount`, trimming only amount boundaries. The amount must begin with an ASCII digit or `+`, `-`, `.`, `,`, or `(`. Numerical validity is not checked. Unknown prefixes, absent amounts, and damage in amounts raise `csvd2c.column.Error`. Ordinary question marks are not inferred as damaged symbols.
- Number cannot process the entire Currency result directly; separate the code and amount before numeric normalization.

- Date requires exactly one year (%Y or %y), month (%m, %b, or %B), and day (%d). Only these directives and literal %% are supported. Years are not inferred. %y follows Python's century rule. Month names depend on the process locale, which the library does not change.
- Multiple formats resolving to distinct dates are rejected; identical interpretations are accepted.
- Number requires integer digits and fractional digits after any decimal separator. It rejects `.5`, `1.`, exponents, NaN, Infinity, surrounding whitespace, and malformed three-digit grouping. Apply Strip or UnicodeNormalize explicitly when appropriate.
- Number preserves decimal precision without float rounding, removes trailing fractional zeros, and normalizes negative zero. Separators are explicit, never inferred or indiscriminately removed.
- Range uses ungrouped notation. Apply Number first for other formats. Bounds accept finite Decimal, integer, or numeric strings; floats and dates are not supported.
- Recode performs `col.encode(stored_encoding).decode(original_encoding)` strictly. Success does not prove correctness and cannot restore replaced characters. It is separate from file encoding detection.

### Ordered encoding recovery

`TryRecoverEncoding(source, read_encoding="utf-8")` tries only fields with surrogateescape markers. Codec failure preserves the input for the next candidate; success returns Unicode text. Recovered fields without markers pass unchanged. The first successful candidate wins, without language detection. Example: `Validator(IfUndecodable(TryRecoverEncoding("cp949"), TryRecoverEncoding("cp1258")), RejectSurrogates())`.

Callers choose the candidate order and final damage checks. See [column_recover_encoding.py](../samples/column_recover_encoding.py) for a complete reading example.

## Processing principles

- Process large inputs incrementally without accumulating the entire input or output. Record and batch sizes affect memory usage; actual 200GB performance has not been validated.
- Preserve original data and distinguish corrections and their reasons.
- Do not guess ambiguous dates or damaged text.
- Distinguish decoding, CSV parsing, structural, and column validation failures.
- Callers implement classification and storage of accepted, corrected, and review-required data. [reject_records.py](../samples/reject_records.py) demonstrates logging rejected values and reasons separately.

## License

Distributed under the [GNU General Public License v3.0](../LICENSE).
