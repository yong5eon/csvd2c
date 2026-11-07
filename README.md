# csvd2c

[English](./README.en.md)

csvd2c는 **CSV Dirty to Clean**의 약자로, 불규칙한 CSV·TSV 데이터를 스트리밍 방식으로 읽고 정제하는 Python 라이브러리입니다. ETL(추출·변환·적재) 과정에서 행 구조와 컬럼 값을 명시한 규칙에 따라 검증·변환할 때 사용합니다.

[사용 매뉴얼](./docs/README.md) · [실행 샘플](./samples/README.md) · [릴리즈 및 변경 이력](https://github.com/yong5eon/csvd2c/releases)

## 주요 기능

- CSV·TSV 순차 읽기: `next(csv)` 또는 반복문으로 list 레코드를 한 건씩 반환
- 헤더 검증: `open()` 시 첫 레코드를 헤더로 검증, 빈·중복 이름과 이름 목록·순서 검사
- 읽기 범위: 생성자와 `open()`의 `offset`·`limit`으로 읽을 레코드 구간 지정
- 원문 조회: `raw()`로 검증 전 필드 목록을 복사해 조회하고 실패 레코드 보관에 활용
- 행 정제: 컬럼 수 검사, 삽입·제거·재배치·병합·분리, 반복 헤더와 빈 행 검사
- 컬럼 정제: 공백·Unicode 정규화, 값 검증·매핑, 날짜·숫자·통화 표기 통일
- 인코딩 처리: 파일 앞부분의 후보 검사와 `surrogateescape`로 보존한 필드 바이트의 조건부 복구
- 규칙 조합: `Validator`로 여러 `Pattern`을 순서대로 실행하고 사용자 정의 `Pattern` 연결

## 설치

Python 3.10 이상이 필요합니다. Python 3.9의 표준 `csv.writer`는 필드 안 escape 문자를 올바르게 보존하지 못하므로, 원문 필드의 CSV 왕복을 위해 최소 지원 버전을 높였습니다.

```shell
pip install csvd2c
```

## 빠른 시작

실행 디렉터리에 다음 내용을 가진 UTF-8 파일 `input.csv`를 준비합니다.

```csv
name,date
 Example ,2026-01-10
 Sample ,2026-02-23
```

이름의 앞뒤 공백을 제거하고 필수값을 검사하면서 레코드를 순차적으로 읽습니다.

```python
from csvd2c import CSV
from csvd2c.column import Validator
from csvd2c.column.patterns import (
  Required,
  Strip,
)
from csvd2c.header import Validator as HeaderValidator
from csvd2c.header.patterns import ExactOrder
from csvd2c.row import Validator as RowValidator
from csvd2c.row.patterns import Length

csv = CSV(
  encoding="utf-8",
  header=HeaderValidator(ExactOrder("name", "date")),
  row=RowValidator(Length(2)),
  column={"name": Validator(Strip(), Required())},
)

with csv.open("input.csv"):
  print(csv.header())
  for record in csv:
    print(record)
```

기대 출력:

```text
['name', 'date']
['Example', '2026-01-10']
['Sample', '2026-02-23']
```

헤더 Validator를 주입했으므로 `open()`이 첫 레코드를 헤더로 읽고 `name,date` 순서인지 검증합니다. `header()`는 검증된 헤더를 반환하고 반복문은 나머지 레코드를 읽습니다. `next(csv)`로 한 건씩 읽을 수도 있습니다. 이름 기반 `column`에 지정한 `name`은 헤더에 정확히 한 번 있어야 합니다. 날짜는 별도 `Date` 규칙을 넣지 않았으므로 원문 문자열로 유지됩니다. TSV는 `CSV(delimiter="\t")`로 설정합니다.

## 사용 규칙

- `header=`에 헤더 Validator를 주입하면 `open()`이 첫 레코드를 헤더로 읽어 검증합니다. 실패하면 `csvd2c.header.Error`가 발생하고 파일이 닫힙니다. 주입하지 않으면 `open()`은 레코드를 읽지 않습니다.
- `header()`는 레코드를 읽지 않고 검증된 헤더의 복사본을 반환합니다. 헤더 검증을 하지 않았으면 `None`입니다.
- `raw()`는 마지막 데이터 레코드의 검증 전 필드 목록을 복사해 반환합니다. 초기 상태·레코드를 얻지 못한 읽기·종료 후에는 `None`입니다. 자세한 갱신 규칙과 저장 예시는 [원문 레코드 조회](./docs/README.md#원문-레코드-조회)를 참고하세요.
- `next(csv)`와 `row()`는 다음 레코드 하나를, `rows()`는 남은 레코드를 list로 순차 반환합니다. 세 방식은 읽기 위치와 생성자 Validator를 공유합니다. 헤더 Validator 없이 헤더가 있는 파일을 읽으면 첫 결과는 헤더 레코드입니다.
- `row` Validator를 먼저 실행하고 그 결과에 `column` Validator를 적용합니다. `column`이 dict이면 검증된 헤더의 이름 기준, tuple이면 앞쪽 컬럼부터 적용합니다.
- `row()`·`rows()`의 `row=`·`column=`는 해당 호출의 설정을 교체합니다. `open()`의 `header=`는 그 파일에만 적용됩니다. 생략하거나 `None`을 전달하면 생성자 설정을 사용합니다.
- `next(csv)`와 `row()`는 파일 끝에서 `StopIteration`을 발생시키며, `rows()`와 반복문은 정상 종료합니다.
- 생성자와 `open()`의 `offset`·`limit`으로 `next(csv)`·`row()`·`rows()`가 읽을 레코드 구간을 지정합니다. 위치는 0부터 세고, 헤더 Validator로 읽은 헤더는 세지 않습니다. 검증에 실패한 레코드도 limit에 포함되며, limit을 채우면 `next(csv)`·`row()`는 `StopIteration`을 발생시키고 `rows()`는 종료합니다.
- `close()` 또는 컨텍스트 종료 후 `next(csv)`를 호출하면 `RuntimeError`가 발생합니다. 같은 `CSV` 인스턴스를 다시 열면 새 파일의 읽기 위치에서 시작합니다. 닫기 전 생성한 `rows()` generator는 재사용할 수 없습니다.

헤더 Pattern, 이름 변경과 이전 사용법의 마이그레이션은 [헤더 검증](./docs/README.md#헤더-검증)을, 범위 계산의 상세 규칙은 [읽기 범위](./docs/README.md#읽기-범위)를, 설정별 제약과 상세 동작은 [사용 규칙 상세 설명](./docs/README.md#사용-규칙)을 참고하세요.

### 읽기 설정과 반환값

생성자의 `field_size_limit=None`은 현재 표준 CSV 필드 제한을 유지합니다. 정수 `0`부터 공개 상수 `MAX_FIELD_SIZE` (`2_147_483_647`)까지 지정할 수 있습니다. 범위 밖은 `ValueError`, 잘못된 타입은 `TypeError`이며, 읽는 필드가 제한을 넘으면 `csv.Error`입니다. 설정은 다른 reader에도 영향을 주고 종료 후 복원되지 않으며 메모리 안전을 보장하지 않습니다. 예제와 자세한 제약은 [필드 크기 제한](./docs/README.md#필드-크기-제한)을 참고하세요.

`CSV`의 기본 설정은 `encoding="utf-8"`, `errors="strict"`, `newline=""`, `delimiter=","`, `strict=True`입니다. `open(path, mode="rb", header=None, offset=None, limit=None)`는 `rb`·`r`·`rt`만 지원합니다. 바이너리 모드에서는 `TextIOWrapper`로 디코딩하며, 텍스트 모드도 같은 인코딩·오류·개행 설정을 적용합니다. 쓰기·추가·갱신 모드는 파일을 열기 전에 거부합니다.

`next(csv)`, `row()`와 `rows()`는 항상 list 레코드를 반환합니다. dict가 필요하면 검증된 헤더와 직접 연결합니다.

```python
from csvd2c import CSV
from csvd2c.header import Validator as HeaderValidator

with CSV(header=HeaderValidator()).open("input.csv") as csv:
  header = csv.header() or []
  for record in csv.rows():
    print(dict(zip(header, record)))
```

`column`의 이름이 검증된 헤더에 없거나 중복되면 오류이며, tuple 설정은 지정한 앞쪽 컬럼만 처리합니다. 생성자 설정을 사용하지 않으려면 호출별 `column={}` 또는 `column=()`를 명시합니다.

`close()`는 스트림과 헤더·읽기 상태를 초기화하며 반복 호출해도 안전합니다. `rows()`는 호출 시 검증 설정과 헤더 매핑을 선택하므로, 닫기·재개 이후에는 기존 generator를 사용할 수 없습니다.

## 행 구조 Pattern

`csvd2c.row.patterns`에서 가져옵니다. 행 Pattern은 `list[str]`를 받아 `list[str]`를 반환합니다. 치환은 새 list를 만들며, 검사만 하는 Pattern은 성공 시 입력을 그대로 유지합니다.

| Pattern | 동작 |
| --- | --- |
| `Length(count)` | 정확한 컬럼 수 검사 |
| `Insert(index, value)` | Python `list.insert` 규칙으로 값 삽입 |
| `Remove(index)` | 지정한 컬럼 제거, 음수 인덱스 지원 |
| `Reorder(*indices)` | 모든 컬럼을 정확히 한 번 지정하여 재배치 |
| `Slice(start=None, stop=None, step=None)` | Python 슬라이싱, 0 step 거부 |
| `Truncate(count)` | 뒤쪽 초과 컬럼 제거 |
| `Pad(count, value="")` | 뒤쪽 부족 컬럼만 지정값으로 채움 |
| `Merge(start, stop, sep=",")` | stop을 제외한 연속 구간을 한 컬럼으로 병합 |
| `Split(index, sep=",", maxsplit=-1)` | 한 컬럼을 `str.split` 규칙으로 분리 |
| `Replace(index, value)` | 한 컬럼을 명시한 값으로 교체 |
| `IfLength(count, *patterns)` | 컬럼 수가 일치할 때만 내부 규칙 적용 |
| `RejectEmpty()` | 빈 레코드 또는 모두 빈 문자열인 레코드 거부 |
| `RejectHeader(*names)` | 값과 순서가 같은 반복 헤더 거부 |

예를 들어 제공처의 주소 필드가 인용되지 않은 쉼표 때문에 두 컬럼으로 나뉜다는 사실이 확인되었다면 다음처럼 처리합니다.

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
result: list[str] = validator([
  "Example",
  "Seoul",
  "Gangnam",
  "2026-01-10",
], 1)
assert result == ["Example", "Seoul,Gangnam", "2026-01-10"]
```

`IfLength`는 개수가 다르면 원래 행을 유지합니다. `Merge`는 비어 있거나 범위를 벗어난 구간을 거부합니다. 위치는 자동으로 추정하지 않습니다.

뒤쪽 초과·누락이 확인된 데이터에는 `Validator(Truncate(2), Pad(2), Length(2))`처럼 조합할 수 있습니다. 중간 컬럼 누락은 복구하지 않으며, `Truncate`로 버린 값은 결과에서 사라지므로 원본을 보존하세요. `RejectEmpty`는 공백만 있는 문자열을 빈 값으로 간주하지 않습니다.

## 컬럼 Pattern

`csvd2c.column.patterns`에서 가져옵니다. 입력과 출력은 모두 문자열입니다. 날짜·숫자도 Python 날짜 객체나 float가 아니라 정규화된 문자열로 반환합니다.

| Pattern | 동작 |
| --- | --- |
| `Strip`, `CollapseWhitespace` | 앞뒤 공백 제거·연속 공백 축약 |
| `Replace`, `RegexReplace` | 문자열·정규식 치환 |
| `Lower`, `Upper`, `CaseFold` | 대소문자 변환 |
| `UnicodeNormalize` | NFC·NFD·NFKC·NFKD 정규화 |
| `Required`, `Length`, `Regex`, `Choices` | 필수값·코드 포인트 길이·전체 정규식 일치·허용값 검사 |
| `RejectCharacters` | 지정한 문자 거부 |
| `RejectSurrogates`, `RejectReplacementCharacter` | surrogate와 U+FFFD 검사 |
| `Map`, `Default` | 정확한 문자열 매핑·빈 문자열 기본값 |
| `Date` | 완전한 날짜 검사와 출력 형식 통일 |
| `Number`, `Range` | 숫자 문자열 정규화·최소/최대 포함 검사 |
| `Currency` | 통화 접두부를 ISO 4217 코드로 변환 |
| `Recode` | 확인된 오디코딩 경로를 역변환 |
| `IfEmpty`, `IfMatch`, `IfUndecodable` | 조건에 맞을 때만 내부 규칙 적용 |
| `RecoverEncoding`, `TryRecoverEncoding` | 보존한 필드 바이트의 지정 인코딩 복구·후보 복구 |

### 날짜와 숫자

```python
from csvd2c.column import Validator
from csvd2c.column.patterns import (
  Date,
  Number,
  Range,
  Strip,
)

date = Validator(Strip(), Date("%Y-%m-%d", "%d/%m/%Y"))
amount = Validator(
  Strip(),
  Number(thousands=","),
  Range(minimum=0, maximum=1000000),
)
assert date(" 29/02/2024 ", 1, "date") == "2024-02-29"
assert amount(" 1,234.500 ", 1, "amount") == "1234.5"
```

- `Date`는 연도·월·일을 각각 포함한 형식을 요구합니다. `1-10`, `Feb-23` 같은 값에 연도를 임의로 채우지 않습니다. 여러 형식에서 서로 다른 날짜로 해석되면 오류입니다.
- 문자 월 이름 `%b`·`%B`는 프로세스 로캘에 영향을 받습니다. 라이브러리는 로캘을 변경하지 않습니다.
- `Number(decimal=".", thousands=None)`는 구분자를 자동으로 추정하지 않습니다. 천 단위는 3자리 그룹을 검사하며, `.5`·`1.`·지수 표기·NaN·Infinity·앞뒤 공백을 거부합니다.
- `Number`는 부동소수점 반올림 없이 소수부 끝의 0을 제거하고 음수 0을 `0`으로 반환합니다.
- `Range`는 유한 Decimal·정수·숫자 문자열 경계값을 지원하며 float나 날짜 비교는 지원하지 않습니다. 그룹 구분자가 있으면 먼저 `Number`로 정규화합니다.

### 통화

```python
from csvd2c.column.patterns import (
  CURRENCY_ALIASES,
  CURRENCY_CODES,
  Currency,
  Number,
)

currency = Currency({"VN$": "VND"})
assert currency("CA$1,000", 1, "amount") == "CAD 1,000"
code, amount = currency("VN$ 10,000,000", 1, "amount").split(" ", 1)
assert code == "VND"
assert Number(thousands=",")(amount, 1, "amount") == "10000000"
assert "VND" in CURRENCY_CODES
assert CURRENCY_ALIASES["VND"] == "VND"
```

`Currency`는 포함된 ISO 4217 코드와 CLDR의 다국어 이름·기호를 사용하며 실행 중 네트워크에 접근하지 않습니다. `CURRENCY_CODES`와 `CURRENCY_ALIASES`는 읽기 전용입니다. 데이터 출처와 고지는 [상세 매뉴얼](./docs/README.md)에 설명되어 있습니다.

단독 `$`는 USD, `¥`는 JPY로 처리하는 명시적 정책입니다. 제공처의 의미가 다르면 사용자 매핑으로 재정의하세요. 매핑은 복사하며 ISO 코드 자체를 다른 코드로 바꿀 수 없습니다. `VN$` 같은 표기는 제공처가 VND라고 확인한 경우에만 위처럼 추가합니다.

통화 접두부만 변환하고 금액 형식은 유지합니다. 숫자 유효성 검사는 하지 않으며, 금액이 없거나 손상되면 오류입니다. `Currency` 결과 전체에는 `Number`를 바로 적용할 수 없습니다. `VN$ 금액 - VN$ 금액` 같은 구간은 [구간 샘플](./samples/column_currency_interval.py)처럼 끝점을 나누어 처리합니다.

### 인코딩 복구

파일 전체가 같은 인코딩이라면 `detect_encoding("input.csv", "utf-8-sig", "cp949")`로 후보를 검사한 뒤 선택한 인코딩으로 읽을 수 있습니다. BOM은 자동으로 우선 처리하지 않으며, 후보가 없거나 파일이 비었거나 모든 후보가 실패하면 오류입니다.

UTF-8 읽기에서 실패한 바이트를 보존하려면 `errors="surrogateescape"`를 명시합니다. 그 필드를 지정한 인코딩으로 복구하는 예입니다.

```python
from csvd2c.column import Validator
from csvd2c.column.patterns import (
  RejectReplacementCharacter,
  RejectSurrogates,
  TryRecoverEncoding,
)

validator = Validator(
  TryRecoverEncoding("ascii"),
  TryRecoverEncoding("cp949"),
  RejectSurrogates(),
  RejectReplacementCharacter(),
)
raw: bytes = "홍길동".encode("cp949")
preserved: str = raw.decode("utf-8", errors="surrogateescape")
assert validator(preserved, 1, "name") == "홍길동"
```

`TryRecoverEncoding`은 U+DC80~U+DCFF 표식이 있는 값만 시도합니다. 실패하면 입력을 유지해 다음 후보가 처리하고, 성공해 표식이 사라지면 뒤의 후보는 변환하지 않습니다. 예제의 ASCII 후보는 실패하므로 cp949가 처리합니다. 실제 후보 순서는 제공처 정책에 따라 정하세요. cp1258처럼 많은 바이트를 받아들이는 인코딩은 잘못된 후보여도 성공할 수 있습니다.

원본 인코딩이 확인되었다면 `IfUndecodable(RecoverEncoding("cp1258"))`를 사용합니다. `RecoverEncoding`은 실패를 오류로 보고하고, `TryRecoverEncoding`은 codec 실패에 한해 원본을 유지합니다. 복구는 `Strip`·치환·Unicode 정규화 전에 적용하세요.

결과는 Unicode `str`이며 UTF-8 바이트가 아닙니다. 출력 단계에서 인코딩합니다. 이미 `�`로 대체된 값, 한 필드 안의 혼합 인코딩, BOM·개행 처리로 제거된 정보는 자동 복원하지 못합니다. `Recode(stored_encoding, original_encoding)`는 이미 잘못 디코딩된 문자열의 확인된 경로를 strict 재인코딩·디코딩으로 되돌리는 별도 규칙입니다.

## 사용자 정의 규칙과 오류 처리

행 Pattern·Validator는 `__call__(value: List[str], row: int) -> List[str]`, 열 구현은 `__call__(value: str, row: int, column: Union[int, str]) -> str` 계약입니다. 직접 호출과 기존 사용자 정의 Pattern은 새 위치 인자를 반영해야 합니다. CSV에 Validator를 주입하면 위치가 자동으로 전달됩니다. 라인 번호는 레코드의 마지막 물리 라인, 열 식별자는 숫자 인덱스 또는 지정한 컬럼명입니다.

검증 실패는 `csvd2c.row.Error(message, row, value)` 또는 `csvd2c.column.Error(message, row, column, value)` 예외로 발생하며, 둘 다 `csvd2c.Error(Exception)`를 상속합니다. `value`는 실패한 Pattern에 들어온 값이므로 `Strip → Required`의 실패값은 공백을 제거한 `""`입니다. Pattern별 `error=` 인자는 제거했고 데이터 실패는 더 이상 `ValueError`가 아니므로 `try`/`except`로 처리하세요. 생성자 설정 오류는 기존처럼 `TypeError`·`ValueError`로 즉시 발생합니다. 자세한 계약과 마이그레이션은 [검증 위치와 오류 처리 계약](./docs/README.md#검증-위치와-오류-처리-계약)을 참고하세요.

[사용자 정의 Pattern](./samples/custom_patterns.py)과 [오류 처리](./samples/custom_errors.py)에 완전한 예제가 있습니다. 실패한 레코드를 기록하며 계속 처리하려면 [거부 기록 샘플](./samples/reject_records.py)처럼 Validator를 CSV에 직접 주입하고 검증 오류를 잡은 뒤 다음 `row()`를 호출하세요. 검증 예외가 발생한 동일한 `rows()` generator는 재사용할 수 없으며 파싱·디코딩 오류 이후에는 행 경계를 추측하며 계속 읽지 않습니다.

## 사용 시 주의사항

- 기본 디코딩 정책은 `errors="strict"`입니다. 디코딩·파싱·검증 오류는 전파하며 자동으로 행을 건너뛰지 않습니다.
- `detect_encoding()`은 앞부분 최대 1MiB를 후보 순서대로 검사합니다. 첫 성공은 실제 인코딩이나 전체 파일의 유효성을 보장하지 않습니다.
- `TryRecoverEncoding`도 언어를 감지하지 않습니다. 복구 후보 중 첫 디코딩 성공을 사용하며, 이미 `�`로 대체된 정보는 복원하지 못합니다.
- 파일 전체를 리스트로 모으지 마세요. 한 레코드의 크기와 배치 크기도 메모리에 영향을 줍니다. 실제 200GB 파일의 성능 검증은 아직 수행하지 않았습니다.
- 현재 `CSV`는 읽기 전용입니다. 출력 저장과 거부 기록 관리는 호출자가 구현합니다.

## 매뉴얼과 샘플

[사용 매뉴얼](./docs/README.md)에서 사용 규칙, 행·컬럼 Pattern과 오류 처리의 세부 동작을 확인할 수 있습니다.

[샘플 안내](./samples/README.md)는 독립 실행 예제 22개를 제공합니다. 작은 합성 데이터로 CSV·TSV 읽기, 날짜·숫자·통화 처리, 인코딩 복구, 사용자 정의 규칙, 거부 기록, 스트리밍 저장과 제한 배치를 실행하고 결과를 확인할 수 있습니다.

## 라이선스

[GNU General Public License v3.0](./LICENSE)에 따라 배포됩니다. 포함된 통화 별칭 데이터의 Unicode-3.0 고지는 [CurrencyData.py](./src/column/patterns/CurrencyData.py)에 보존되어 있습니다.
