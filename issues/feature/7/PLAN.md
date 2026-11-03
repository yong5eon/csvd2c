# Pattern 입력값과 위치 전달 작업 계획

## 기준과 현재 상태

[요구사항 명세](./REQUIREMENTS.md)를 구현 기준으로 삼고, 브랜치와 병합 대상은 [README](./README.md)의 메타데이터를 따른다.

구현·검증 완료. 초기 구현의 호출형 Error 처리기는 사용자 지시에 따라 예외 클래스로 정정했다. 전체 테스트 124개가 통과했으며 커밋·푸시·병합은 수행하지 않는다.

## 구현 방향

- 행 Pattern·Validator: `__call__(self, value: List[str], row: int) -> List[str]`
- 열 Pattern·Validator: `__call__(self, value: str, row: int, column: Union[int, str]) -> str`
- Error는 예외 클래스: 공통 `Error(Exception)(message)`, 행 `Error(message, row, value)`, 열 `Error(message, row, column, value)`. Error에 `__call__`을 두지 않는다.
- 원본값은 각 Pattern의 입력값이다. 앞선 Pattern의 반환값을 다음 Pattern에 전달하며 최초 값 스냅샷·역추적·별도 맥락 실행 계층은 추가하지 않는다.
- Pattern의 `error=` 인자를 제거한다. 기록·복구·건너뛰기는 호출자가 `try`/`except`로 처리한다.
- 공통 Error는 `src/Error.py`에 정의하고 행·열 Error가 상속한다. 서로 다른 행·열 시그니처를 무리하게 하나의 광범위한 인자 계약으로 통합하지 않고, 공통 기반에 필요한 최소 책임만 둔다. 실제 부모 계약과 행·열 재정의의 타입 호환성을 확인한다.
- 사용자 지시에 따라 Error는 예외 클래스다. 공통 `Error(Exception)`를 행·열 Error가 상속하고, Pattern의 `error=`는 제거했다.

## 수행 순서

### 1. Error 상속과 공개 호출 계약 변경

관련 요구사항: R1·R5, 인수 기준: A1·A1-2·A1-3.

- `src/Error.py`에 공통 Error를 정의하고 [행 Error](../../../src/row/Error.py)·[열 Error](../../../src/column/Error.py)의 상속을 연결한다.
- [패키지 진입점](../../../src/__init__.py)과 행·열 패키지의 공개 내보내기를 갱신한다.
- 행·열 Error와 [행 Pattern](../../../src/row/Pattern.py)·[열 Pattern](../../../src/column/Pattern.py)의 `__call__`을 확정된 시그니처로 변경한다.
- 공통 Error의 식별 불가능한 실패 처리 계약은 최소한으로 구현하고, 위치를 임의로 생성하지 않는 사용 예시·테스트를 함께 마련한다.
- 기존 사용자 정의 Error·Pattern과 직접 호출이 새 위치 인자를 받도록 바뀌어야 함을 확인한다. 구형 호출 재시도나 자동 시그니처 감지는 추가하지 않는다.

### 2. Validator와 기본 Pattern 연결

선행 단계: 1. 관련 요구사항: R1·R3·R4·R5.

- [행 Validator](../../../src/row/Validator.py)·[열 Validator](../../../src/column/Validator.py)가 값과 위치를 각 Pattern에 전달하도록 변경한다.
- 모든 기본 Pattern의 호출 시그니처와 내부 Pattern 직접 호출을 새 계약에 맞춘다. 순수 변환의 동작이나 거부 조건은 추가하지 않는다.
- R4의 행·열 검증 Pattern은 실패 시 해당 Pattern의 입력값과 위치를 담은 Error를 발생시킨다.
- `Range`의 내부 `Number` 호출 등 조합 호출과 인코딩 복구 Pattern의 상속·재정의를 함께 갱신한다. 생성자 설정 검증을 위해 Pattern을 호출하는 경로는 레코드 위치를 조작하지 않도록 설정 검증과 구분한다.
- `IfEmpty`·`IfMatch`·`IfUndecodable`·`IfLength`가 중첩 실행에 동일한 위치와 그 시점의 값을 전달하도록 변경한다.
- [IfLength](../../../src/row/patterns/IfLength.py)의 광범위한 `ValueError` 재처리를 제거하여 중첩 Pattern의 예외를 그대로 전파한다. 새로운 예외 체계나 재시도 계층으로 해결하지 않는다.
- 모든 Pattern의 `error=` 제거와 데이터 실패의 `ValueError` → 행·열 Error 변경을 사용 문서·샘플에 호환성 변경으로 명시한다.
- `TryRecoverEncoding`의 후보 실패 시 입력 유지 계약을 보존한다.

### 3. CSV의 라인 번호와 열 식별자 전달

선행 단계: 2. 관련 요구사항: R2·R3·R5.

- [CSV](../../../src/CSV.py)의 `row()`·`iterate()`에서 레코드를 읽은 직후 표준 `csv.reader.line_num`을 확보하고 `validate()`로 전달한다.
- `reader`의 타입은 실제 사용 API에 맞게 선언하여 `line_num` 접근을 타입 안전하게 처리한다. 현재 `Iterator[List[str]]` 선언을 근거 없는 캐스트나 `getattr` 기본값으로 우회하지 않는다.
- `column_indices()`의 열 선택 정보가 실제 접근용 인덱스와 Error 전달용 식별자를 함께 유지하도록 수정한다. 튜플 지정은 숫자 인덱스, 이름 지정은 지정한 컬럼명을 전달한다.
- 행 검증 이후 변경된 행의 선택 위치에 열 Validator를 적용한다. 출력용 헤더와 입력 헤더의 역할은 유지한다.
- 파일 파싱·디코딩 실패, 누락 컬럼 등 CSV 자체 오류를 Pattern 검증 실패와 혼동하거나 이번 범위에서 임의로 재분류하지 않는다.
- `row()`·`rows()`의 생성자 설정과 호출별 override 모두에서 값·위치 전달을 확인한다.

### 4. 테스트와 사용자 예시 갱신

선행 단계: 3. 관련 요구사항: R1~R6.

- 기존 [테스트](../../../tests)와 [샘플](../../../samples)의 사용자 정의 Error·Pattern 및 모든 직접 호출에 위치 인자를 반영한다.
- 검증값을 기록하는 Error를 이용해 입력값·라인 번호·열 식별자를 직접 대조한다.
- 사용자 정의 Pattern이 행·열 Error를 발생시키고 호출자가 예외를 잡아 기록·계속 읽기 하는 예시를 갱신한다.
- 먼저 변경 대상 테스트를 묶어 실행하고, 호출 계약이 소스·샘플 전반에 영향을 주므로 마지막에 기존 Python 테스트 전체를 실행한다.

### 5. 사용 문서와 작업 결과 정리

선행 단계: 4. 관련 요구사항: R5·R6.

- [한국어 매뉴얼](../../../docs/README.md)·[영어 매뉴얼](../../../docs/README.en.md) 및 관련 주제 문서에 변경된 호출 계약·라인 번호 의미·Pattern 입력값 기준과 마이그레이션 방법을 반영한다.
- 루트 README와 샘플 안내의 직접 호출 예시를 확인하여 영향이 있는 부분만 갱신한다.
- 의미 있는 코드 변경은 `implements/`, 검증·문서 확인은 `tasks/`에 수행 중 기록한다.
- 실제 수행 결과로 `IMPLEMENTS.md`·`TASKS.md`를 갱신하고, 사용자 영향과 호출 계약 변경을 이슈 `CHANGELOG.md`에 정리한다.
- 인수 기준 충족, 변경 범위와 문서 링크를 확인하고 이 계획의 단계 상태를 갱신한다. 커밋·푸시·병합은 별도 요청 없이는 수행하지 않는다.

## 인수 기준별 검증

| 인수 기준 | 검증 방법 |
| --- | --- |
| A1·A1-1 | 행·열 직접 호출과 Error 수신값을 확인하고 숫자 인덱스·문자열 컬럼명이 정확한 타입과 값으로 전달되는지 대조 |
| A1-2·A1-3·A5 | 공통 Error 상속과 식별 불가능한 실패 처리, 열 정보가 없는 행 실패, 헤더 없는 숫자 열 식별 및 명시적 위치 직접 호출 확인 |
| A2 | 일반 CSV·헤더 이후·인용 개행 합성 CSV를 읽고 실제 마지막 물리 라인 번호와 Error 수신 번호 대조 |
| A3·A4 | `Strip → Required`에서 `""` 수신, 앞선 행 변환 후 입력 행 수신, 중첩 Pattern의 값·위치 전달 확인 |
| A6 | 행 재정렬·병합·분할·삽입·삭제 후 변경된 열 값과 위치로 검증되는지 확인 |
| A7·A8 | R4 대상 실패 분기의 Error 발생과 속성 확인, 설정 오류·순수 변환·후보 인코딩 복구의 기존 결과 회귀 검증 |
| A9·A10 | `error=` 제거·데이터 실패 예외 타입 확인, 중첩 `IfLength`의 예외 전파 확인 |
| A11·A12 | 인용 개행 레코드 실패 후 다음 `row()` 읽기, 파싱·파일 디코딩 오류가 기존 경로로 전파되는지 확인 |
| A13 | 변경된 사용자 정의 Error·Pattern·CSV 주입 샘플 실행, 한국어·영어 안내와 실제 API 일치·상대 링크 확인 |

## 호환성 주의사항

기존 한 인자 Pattern·Validator 직접 호출, `error=` 인자와 호출형 Error 처리기, 데이터 실패의 `except ValueError`는 변경 대상이다. 새 계약으로 수정한 예시를 제공하되 구형 호출을 자동으로 유지하는 호환 계층은 만들지 않는다.

데이터 마이그레이션이나 운영 배포는 이 계획에 포함하지 않는다. 검증 실패 시 이번 작업에서 만든 변경만 수정하며 사용자 변경이나 다른 이슈의 변경을 되돌리지 않는다.
