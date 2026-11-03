# 검증 실패 위치 정보 제공

## 기능 추가

검증 실패 예외에 실패한 값, 파일 라인 번호와 열 식별자가 담깁니다. 실패한 레코드를 찾아 기록하거나 건너뛰기 쉬워집니다.

- `csvd2c.row.Error`: `message`, `row`, `value`(실패한 Pattern에 들어온 행)
- `csvd2c.column.Error`: `message`, `row`, `column`, `value`(실패한 Pattern에 들어온 값)
- 두 클래스는 공통 `csvd2c.Error`를 상속하며, `csvd2c.Error`는 `Exception`을 상속합니다.

`row`는 레코드를 모두 읽은 마지막 물리 라인 번호이며 1부터 시작합니다. 인용 개행으로 2~3번 라인에 걸친 레코드는 3입니다. `column`은 튜플로 지정한 열이면 0부터 시작하는 인덱스, 이름으로 지정한 열이면 컬럼명입니다. `value`는 앞선 Pattern을 거친 뒤 실패한 Pattern이 받은 값입니다. 예를 들어 `Strip` 다음 `Required`가 실패하면 `""`입니다.

```python
from csvd2c import CSV
from csvd2c.column import Error as ColumnError, Validator
from csvd2c.column.patterns import Required, Strip
from csvd2c.row import Error as RowError

csv = CSV(cols={"name": Validator(Strip(), Required())})
with csv.open("input.csv"):
  csv.header()
  while True:
    try:
      record = csv.row()
    except ColumnError as error:
      print(error.row, error.column, repr(error.value), error.message)
      continue
    except RowError as error:
      print(error.row, error.value, error.message)
      continue
    except StopIteration:
      break
```

## 동작 변경

- 데이터 검증 실패가 `ValueError` 대신 `csvd2c.row.Error` 또는 `csvd2c.column.Error`로 발생합니다. 생성자 설정 오류는 기존처럼 `TypeError`·`ValueError`입니다.
- 행 검증 후 열 Validator가 지정한 위치의 값이 레코드에 없으면 `ValueError` 대신 `csvd2c.row.Error`가 발생합니다. 잡은 뒤 다음 `row()`로 계속 읽을 수 있습니다.
- Pattern의 `error=` 인자와 호출형 Error 처리기를 제거했습니다. 기록·복구·건너뛰기는 `try`/`except`로 처리합니다.
- 행 Pattern·Validator는 `(value, row)`, 열 Pattern·Validator는 `(value, row, column)`으로 호출합니다. CSV에 Validator를 주입하면 위치가 자동으로 전달됩니다.

## 마이그레이션

- `except ValueError`로 검증 실패를 처리하던 코드는 `csvd2c.row.Error`, `csvd2c.column.Error` 또는 `csvd2c.Error`로 바꾸세요.
- `Required(error=handler)`처럼 `error=`를 넘기던 코드는 인자를 제거하고 호출하는 쪽에서 예외를 처리하세요.
- 사용자 정의 Pattern의 `__call__`은 행이면 `(value, row)`, 열이면 `(value, row, column)` 인자를 받고, 실패 시 `Error(message, row, value)` 또는 `Error(message, row, column, value)`를 발생시키세요.
- Validator를 직접 호출하는 코드는 `validator(row, 1)`, `validator(value, 1, 0)`처럼 위치를 함께 전달하세요.
