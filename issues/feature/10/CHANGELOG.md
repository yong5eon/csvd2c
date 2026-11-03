# 헤더 검증기 주입 지원

## 기능 추가

헤더 레코드를 검증하는 헤더 Validator를 주입할 수 있습니다. 파일마다 헤더를 직접 비교하는 코드를 작성하지 않아도 됩니다.

- `csvd2c.header` 패키지에 `Validator`, `Pattern`, `Error`가 추가되었습니다.
- `csvd2c.header.patterns`에서 다음 Pattern을 조합할 수 있습니다. 이름은 대소문자·공백을 바꾸지 않고 정확히 비교합니다.

| Pattern | 거부 조건 |
| --- | --- |
| `RejectEmpty()` | 빈 이름이 있음 |
| `RejectDuplicate()` | 같은 이름이 두 번 이상 있음 |
| `Length(count)` | 이름 개수가 `count`와 다름 |
| `Includes(*names)` | 지정한 이름 중 없는 것이 있음 |
| `Exact(*names)` | 순서를 무시했을 때 지정한 이름 목록과 다름 |
| `ExactOrder(*names)` | 지정한 이름과 순서까지 같지 않음 |

```python
from csvd2c import CSV
from csvd2c.header import Error as HeaderError
from csvd2c.header import Validator as HeaderValidator
from csvd2c.header.patterns import ExactOrder, RejectDuplicate

csv = CSV(header=HeaderValidator(RejectDuplicate(), ExactOrder("name", "date")))
try:
  with csv.open("input.csv"):
    print(csv.header())
    for record in csv.rows():
      print(record)
except HeaderError as error:
  print("Invalid header:", error.value, error.message)
```

- 헤더 Validator는 생성자와 `open()`의 `header` 인자로 받습니다. `open()`에 넘긴 값은 그 파일을 여는 동안에만 적용됩니다.
- 헤더 Validator가 있으면 `open()`이 첫 레코드를 헤더로 읽어 검증합니다. 실패하면 `csvd2c.header.Error`가 발생하고 파일이 닫힙니다. 파일이 비어 있으면 `value`가 `None`인 같은 Error가 발생합니다.
- Validator가 반환한 이름이 헤더가 되므로, 사용자 정의 Pattern으로 이름을 바꿔 이름 기반 컬럼 Validator에 사용할 수 있습니다.

## 동작 변경

- `header()`는 더 이상 레코드를 읽지 않습니다. `open()`에서 검증한 헤더를 반환하며, 헤더 Validator가 없으면 `None`을 반환합니다.
- 헤더 Validator 없이 헤더가 있는 파일을 읽으면 첫 `row()`·`rows()` 결과는 헤더 레코드입니다.
- 컬럼 Validator 인자 `cols`의 이름이 `column`으로 바뀌었습니다. 생성자와 `row()`·`rows()`에 모두 적용됩니다.
- `row()`·`rows()`의 `header` 인자가 제거되어 항상 list를 반환합니다.

## 마이그레이션

| 이전 사용법 | 변경 후 |
| --- | --- |
| `csv.header()`로 첫 레코드를 헤더로 읽기 | `CSV(header=HeaderValidator())` 또는 `csv.open(path, header=HeaderValidator())`로 주입한 뒤 `csv.header()`로 조회 |
| `header()` 반복 호출로 다음 레코드 읽기 | 데이터 레코드는 `row()`로 읽기 |
| `cols=` | `column=` |
| `row(header=...)`·`rows(header=...)`로 dict 받기 | list를 받아 `dict(zip(csv.header(), record))`처럼 직접 변환 |

이름 기반 컬럼 Validator(`column`이 dict)를 쓰려면 헤더 Validator를 주입해야 합니다. 검사 없이 헤더만 읽으려면 Pattern 없는 `HeaderValidator()`를 사용하세요.
