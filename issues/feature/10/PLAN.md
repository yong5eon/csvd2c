# 헤더 검증기 주입 작업 계획

## 기준

계획 확정. 아래 순서대로 구현한다.

[요구사항 명세](./REQUIREMENTS.md)의 R1~R9를 구현 기준으로 삼는다. 브랜치와 병합 대상은 [README](./README.md)의 메타데이터를 따른다. 커밋·푸시·병합은 별도 요청 없이 수행하지 않는다.

## 변경 대상

| 대상 | 내용 |
| --- | --- |
| `src/header/` | 새 패키지: `Error.py`, `Pattern.py`, `Validator.py`, `patterns/`, `__init__.py` |
| `src/CSV.py` | 생성자·`open()`의 `header`, `open()` 시점 헤더 검증, `header()` 변경, `cols` → `column`, `row()`·`rows()`의 출력 `header` 제거 |
| `src/__init__.py` | 공개 내보내기 확인. 기존 `row`·`column`과 같이 `csvd2c.header`로 가져오게 한다 |
| `tests/` | `test_csv.py` 등 `header()`·`cols`·출력 `header`를 쓰는 테스트 5개 수정, 헤더 검증기 테스트 추가 |
| `samples/` | `header()`·`cols`·출력 `header`를 쓰는 샘플 수정, 헤더 검증 샘플 추가 |
| 문서 | `docs/README.md`·`docs/README.en.md`, 루트 `README.md`·`README.en.md`·`README.setup.md`, `samples/README.md`·`samples/README.en.md` |

`setup.py`는 `find_packages`로 `src` 하위 패키지를 모두 포함하므로 새 패키지를 위한 설정 변경은 필요 없다. wheel 설치 검증으로 확인한다.

## 수행 순서

### 1. `csvd2c.header` 패키지

관련 요구사항: R1·R7. 인수 기준: A8.

- `Error(BaseError)`: `__init__(self, message: str, value: Optional[List[str]])`, 속성 `message`, `value`.
- `Pattern(ABC)`: 추상 `__call__(self, value: List[str]) -> List[str]`.
- `Validator`: Pattern을 순서대로 적용하고 최종 반환값을 돌려준다. 기존 `row.Validator`와 같은 구조로 Pattern 타입을 검사한다.
- `patterns/`에 헤더 Pattern 6개를 추가한다. 실패 시 해당 Pattern의 입력 헤더를 담아 `Error`를 발생시키고, 성공하면 입력을 그대로 반환한다.

| Pattern | 실패 조건 |
| --- | --- |
| `RejectEmpty()` | 정확히 빈 문자열인 이름이 있음. 필드가 없는 `[]`는 통과 |
| `RejectDuplicate()` | 같은 이름이 두 번 이상 있음 |
| `Length(count)` | 헤더 이름 개수가 `count`와 다름. `count`는 0 이상의 정수이며 아니면 생성자에서 `TypeError`·`ValueError` |
| `Includes(*names)` | 지정한 이름 중 없는 것이 있음 |
| `Exact(*names)` | 정렬한 이름 목록이 지정한 이름 목록을 정렬한 것과 다름 |
| `ExactOrder(*names)` | 이름 목록이 지정한 순서와 정확히 같지 않음 |

- 지정 이름은 문자열만 허용하고, 그 외는 생성자에서 `TypeError`를 발생시킨다.
- Pattern 이름은 사용자 확인으로 확정했다. `RejectEmpty`는 행 Pattern `csvd2c.row.patterns.RejectEmpty`와 이름이 같지만 패키지가 달라 충돌하지 않는다. 함께 import할 때는 별칭을 쓴다.

### 2. CSV 헤더 검증과 header()

선행: 1. 관련 요구사항: R2·R3·R4·R5. 인수 기준: A1~A6.

- 생성자에 `header: Optional[HeaderValidator] = None`을 추가하고 타입을 검사한다.
- `open(path, mode='rb', header=None)`: 인자가 `None`이 아니면 그 파일에만 적용하고, 아니면 생성자 값을 쓴다. 적용 값은 `open()` 지역에서 결정하므로 닫은 뒤 다시 열면 생성자 값이 쓰인다.
- 적용할 헤더 검증기가 있으면 reader를 만든 직후 첫 레코드를 읽어 검증한다.
  - 레코드가 없으면 `HeaderError('...', None)`.
  - 검증기가 발생시킨 예외는 그대로 전파한다.
  - 예외가 나면 `ExitStack`이 파일을 닫고, reader·헤더 상태를 초기화한 뒤 컨텍스트를 열지 않는다.
  - 성공하면 반환값의 복사본을 현재 헤더로 저장한다.
- `header()`는 레코드를 읽지 않고 저장된 헤더의 복사본 또는 `None`을 반환한다. 반환 타입은 `Optional[List[str]]`.
- 이름 기반 열 매핑은 저장된 헤더를 사용한다. 매핑 조건의 `ValueError`는 유지하고, 헤더가 없을 때의 `RuntimeError` 문구를 헤더 검증기 주입 안내로 바꾼다.
- 헤더가 열려 있는 동안 바뀌지 않으므로, `rows()`의 헤더 변경 감지 조건은 reader 교체 감지만 남도록 정리한다.

### 3. cols → column, 출력 header 제거

선행: 2. 관련 요구사항: R6·R8. 인수 기준: A7·A9.

- 생성자와 `row()`·`rows()`의 `cols`를 `column`으로 바꾸고, 내부 메소드 인자와 오류 문구도 맞춘다. 호환 별칭은 두지 않는다.
- `row()`·`rows()`의 `header` 인자, `@overload` 6개, `prepare_header()`, `format_record()`를 제거한다. `row()`는 `List[str]`, `rows()`는 `Generator[List[str], None, None]`을 반환한다.

### 4. 테스트

선행: 3. 인수 기준: A1~A9.

- 기존 테스트에서 `csv.header()`로 헤더를 읽던 부분은 Pattern 없는 `HeaderValidator()` 주입으로, `cols=`는 `column=`으로 바꾼다.
- 출력 `header`·dict 반환을 검증하던 테스트는 기능 제거에 맞게 삭제하거나 list 반환 검증으로 바꾼다.
- `header()`를 반복 호출해 다음 레코드를 읽던 테스트는 새 계약(레코드 미소비, 같은 헤더 반환)으로 바꾼다.
- 새 테스트를 추가한다.

| 인수 기준 | 검증 방법 |
| --- | --- |
| A1 | 헤더 검증기 주입 후 `open()` 직후 `header()` 결과와 첫 `row()`가 두 번째 레코드인지 확인 |
| A2 | 검증 실패·빈 파일에서 `open()`이 `HeaderError`를 발생시키고 `value`가 각각 입력 헤더·`None`인지, 이후 같은 인스턴스로 다시 열 수 있는지 확인 |
| A3 | 생성자 값, `open()` 지정값, 재오픈 후 생성자 값 적용 확인 |
| A4 | 검증기 없이 `header()`가 `None`, 첫 `row()`가 첫 레코드인지 확인 |
| A5 | `header()` 반복 호출이 레코드를 소비하지 않고 복사본을 반환하는지 확인 |
| A6 | 이름을 바꾸는 사용자 Pattern으로 이름 기반 매핑, 기존 매핑 조건 `ValueError` 유지 확인 |
| A7 | `column=` 동작과 `cols=` 전달 시 `TypeError` 확인 |
| A8 | Pattern 6개의 성공·실패, 대소문자·공백 정확 비교, `a,a,b` 구성 비교, `[]`가 `RejectEmpty`는 통과하고 `Length`로 거부되는지 확인 |
| A9 | `row()`·`rows()`가 `header=`를 받지 않고 list를 반환하며, 검증기 없이 첫 결과가 헤더 레코드인지 확인 |

### 5. 샘플과 문서

선행: 4. 관련 요구사항: R9. 인수 기준: A10.

- `header()`·`cols`·출력 `header`를 쓰는 샘플을 새 API로 바꾼다. `read_dictionary.py`는 `dict(zip(csv.header(), record))`로 변환하는 예로 바꾼다.
- 헤더 Pattern 조합과 실패 처리를 보여 주는 샘플을 추가하고 샘플 안내 문서에 등록한다.
- 이름을 바꾸는 사용자 정의 헤더 Pattern 예시를 매뉴얼에 넣는다. 이름 변경용 Pattern은 제공하지 않는다.
- 한국어·영어 매뉴얼에 헤더 검증기 절과 `open()` 시점 검증 흐름(Mermaid)을 추가하고, `header()`·`column`·출력 `header` 제거의 마이그레이션 방법을 쓴다.
- 루트 README 세 개의 예제와 요약을 갱신한다.

### 6. 검증과 기록

- 전체 테스트를 실행한다. 샘플 실행 테스트를 포함한다.
- 일반 wheel로 설치해 `csvd2c.header` 패키지 포함과 import를 확인한다.
- Pyright로 변경 전 기준선과 비교해 신규 진단이 없는지 확인한다.
- 문서 Python 예제 실행, 상대 링크, `git diff --check`를 확인한다.
- `implements/`·`tasks/` 단계별 기록, `IMPLEMENTS.md`·`TASKS.md`, 고객용 `CHANGELOG.md`를 작성한다.

## 호환성 주의사항

`header()` 동작, `cols` 인자, `row()`·`rows()`의 출력 `header` 인자가 바뀌는 호환성 변경이다. 호환 계층은 만들지 않고 변경 로그와 매뉴얼에 마이그레이션 방법을 명시한다. 데이터 마이그레이션이나 운영 배포는 포함하지 않는다.
