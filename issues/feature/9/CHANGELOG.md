# 읽기 범위 offset·limit 지원

## 새 기능

파일의 일부 구간만 읽을 수 있도록 `CSV` 생성자와 `open()`에 `offset`·`limit`을 추가했습니다.

- AS-IS: 일부 구간만 처리하려면 건너뛸 레코드를 빈 Validator로 읽어 버리고, 처리한 레코드 수를 직접 세어 반복을 멈춰야 했습니다.
- TO-BE: `offset`으로 건너뛸 레코드 수를, `limit`으로 읽을 최대 레코드 수를 지정하면 `row()`·`rows()`가 해당 구간만 읽습니다.

```python
from csvd2c import CSV
from csvd2c.header import Validator as HeaderValidator

csv = CSV(header=HeaderValidator(), limit=1000)

with csv.open("input.csv", offset=2000):
  for record in csv.rows():
    print(record)
```

위 예제는 헤더 다음 레코드부터 0으로 세어 2000번째 위치부터 최대 1000건을 읽습니다. `input.csv`는 실행 위치에 있는 헤더 포함 CSV 파일을 뜻합니다.

## 동작 규칙

- 생성자 값이 기본이며, `open()`에 넘긴 값은 그 파일을 여는 동안에만 적용됩니다. `open()`에서 생략하거나 `None`을 넘기면 생성자 값을 사용하므로, 생성자에서 지정한 `limit`은 `open()`에서 해제할 수 없습니다.
- 위치는 0부터 셉니다. 헤더 Validator가 읽은 헤더는 세지 않으며, 헤더 Validator가 없으면 파일의 첫 레코드가 위치 0입니다. 인용된 필드 안의 개행이 있어도 1건입니다.
- 건너뛰는 레코드에는 행·컬럼 Validator를 적용하지 않습니다. 건너뛰는 중의 디코딩·파싱 오류는 그대로 발생합니다.
- limit은 성공 건수가 아니라 읽은 레코드 수입니다. 검증에 실패한 레코드도 포함하며, 디코딩·파싱 오류로 레코드를 받지 못한 경우는 포함하지 않습니다.
- limit을 채우면 `row()`는 `StopIteration`을 발생시키고 `rows()`는 종료하며, 다음 레코드는 읽지 않습니다. `limit=0`이면 아무 레코드도 읽지 않습니다.
- `row()`와 `rows()`를 섞어 호출해도 같은 범위 안에서 이어서 읽습니다. `open()`할 때마다 처음부터 다시 셉니다.
- 값은 0 이상의 정수여야 합니다. 정수가 아닌 값과 `True`·`False`는 `TypeError`, 음수는 `ValueError`가 발생합니다.

## 호환성

새 키워드 인자만 추가되었습니다. 범위를 지정하지 않으면 기존과 같이 동작하므로 기존 코드는 변경할 필요가 없습니다.

자세한 내용은 사용 매뉴얼의 `읽기 범위` 절과 `samples/read_range.py` 샘플을 참고하세요.
