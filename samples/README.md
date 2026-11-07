# 실행 샘플

[English](./README.en.md)

csvd2c의 공개 API를 사용하는 독립 실행 예제 24개입니다. 작은 합성 데이터를 직접 만들고 결과를 `assert`로 확인합니다. 외부 서비스, DB, 고객 데이터는 사용하지 않습니다.

## 실행

Python 3.10 이상에서 `pip install csvd2c`로 패키지를 설치합니다. 샘플 실행 명령은 샘플 파일이 있는 저장소 루트를 기준으로 합니다.

```shell
pip install csvd2c
python samples/read_basic.py
python samples/column_recover_encoding.py
python samples/stream_export.py
```

아래 표에서 파일명을 골라 같은 방식으로 실행하세요. Windows CMD에서도 Python에 전달하는 상대 경로의 `/`를 사용할 수 있습니다. 모든 예제를 한 번에 검증하려면 다음 명령을 사용합니다.

```shell
python -m unittest discover -s tests -p "test_samples.py" -v
```

파일을 읽는 샘플은 `TemporaryDirectory` 안에 입력·출력을 만들고 종료 시 정리합니다. 나머지는 메모리의 작은 값만 처리합니다. 결과와 의도한 오류는 콘솔에 표시되며, 로컬 파일을 덮어쓰거나 네트워크에 접근하지 않습니다. 출력이 필요한 예제를 가져다 쓸 때는 임시 경로를 실제 경로로 바꾸고 보관 정책을 정하세요.

## 예제 목록

직접 호출 예제는 행에 라인 번호, 열에 라인 번호와 열 식별자를 함께 전달합니다. 메모리의 단일 입력 예제에서는 명시적으로 `1`, `0`을 지정합니다. 실제 파일을 읽을 때는 CSV에 Validator를 주입하면 마지막 물리 라인 번호와 숫자 인덱스 또는 컬럼명이 전달됩니다. Error의 값은 해당 Pattern의 입력값이며 최초 파일 값은 추적하지 않습니다.

### 읽기와 스트리밍

| 파일 | 참고할 내용 |
| --- | --- |
| [read_basic.py](./read_basic.py) | 헤더 Validator 주입, `header()`, `row()`, `rows()`, EOF, 날짜처럼 보이는 원문 유지 |
| [read_dictionary.py](./read_dictionary.py) | 헤더 Validator 사용 시 `row()`·`rows()`의 Mapping 반환 사용, 다른 키 이름으로 재매핑 |
| [header_validation.py](./header_validation.py) | `open()` 시 헤더 검증, `Length`·`RejectEmpty`·`RejectDuplicate`·`ExactOrder` 조합, 헤더 `Error` 처리, 이름을 바꾸는 사용자 정의 헤더 Pattern과 이름 기반 컬럼 검증 |
| [read_tsv_multiline.py](./read_tsv_multiline.py) | TSV, 인용된 탭, 필드 안 개행, UTF-8 BOM, `rb`/`r`/`rt` |
| [detect_encoding.py](./detect_encoding.py) | 후보 순서, cp949 파일, ASCII의 모호함, 후보 누락 오류 |
| [read_overrides_close.py](./read_overrides_close.py) | 이름·위치 기반 컬럼 검증, 호출별 교체, `None`과 `{}` 차이, 닫기·재개 |
| [stream_export.py](./stream_export.py) | `csv.writer`로 UTF-8 CSV 저장, 입력 전체를 쌓지 않는 처리 |
| [bounded_batches.py](./bounded_batches.py) | 최대 10행씩 전달, 마지막 잔여 배치, 기존 ETL 저장 작업 연결 위치 |
| [read_range.py](./read_range.py) | `open()`의 `offset`으로 구간 나눠 읽기, 생성자 `limit`, 검증 실패 레코드의 limit 포함, 인용 개행 레코드 1건, `limit=0`, 헤더 Validator가 없을 때의 위치 0 |

### 행 구조와 오류 처리

| 파일 | 참고할 내용 |
| --- | --- |
| [row_structure.py](./row_structure.py) | `Length`, `Remove`, `Reorder`, `Insert`, `Replace`, `Slice`, 원본 유지 |
| [row_padding.py](./row_padding.py) | 확인된 뒤쪽 초과·누락 컬럼에만 `Truncate`/`Pad` 적용 |
| [row_merge_split.py](./row_merge_split.py) | `IfLength`로 알려진 쉼표 파손 구조만 `Merge`, `Split`의 `maxsplit` |
| [reject_records.py](./reject_records.py) | CSV에 Validator 직접 주입, 행·열 `Error`의 입력값·라인·컬럼·메시지와 `raw()`의 검증 전 전체 필드를 JSONL로 기록하고 다음 `row()` 읽기 |
| [custom_errors.py](./custom_errors.py) | 행·열 `Error` 예외의 속성 확인, 공통 `Error`를 상속한 사용자 정의 예외 |
| [custom_patterns.py](./custom_patterns.py) | 행·컬럼 `Pattern` 상속, 사용자 정의 행·열 Pattern의 오류 발생, 행 처리 후 컬럼 처리, 출처 컬럼 추가 |

### 컬럼 정제와 검증

| 파일 | 참고할 내용 |
| --- | --- |
| [column_text.py](./column_text.py) | 공백·문자열·정규식 치환, 대소문자, Unicode 정규화 |
| [column_validation.py](./column_validation.py) | 필수값·길이·정규식·선택값·매핑, 빈 값과 조건부 처리 |
| [column_dates.py](./column_dates.py) | 완전한 날짜 변환, 연도 없는 값·잘못된 날짜·모호한 형식 거부 |
| [column_numbers.py](./column_numbers.py) | 지역별 소수점·천 단위 구분자, 정밀도 유지, 숫자 범위 |
| [column_currency.py](./column_currency.py) | 다국어 통화 별칭, 손상 접두부, 상수 조회, 사용자 매핑과 금액 분리 |
| [column_currency_interval.py](./column_currency_interval.py) | 제공처가 확인한 `VN$ 금액 - VN$ 금액`을 두 끝점으로 처리 |
| [column_damage.py](./column_damage.py) | surrogate·`�`·NUL 검사, 정상 물음표와 다국어 값 유지 |
| [column_recode.py](./column_recode.py) | 이미 잘못 디코딩된 문자열의 확인된 경로를 `Recode`로 되돌리기 |
| [column_recover_encoding.py](./column_recover_encoding.py) | UTF-8 읽기의 `surrogateescape`, cp1258 복구, 실패 시 다음 후보 시도 |

## 복사해서 사용할 때

- 인코딩 복구는 `Strip`·치환·Unicode 정규화보다 먼저 적용하세요. `TryRecoverEncoding`은 언어를 감지하지 않으며 첫 strict 디코딩 성공을 채택합니다. cp1258처럼 많은 바이트를 받아들이는 후보는 실제 인코딩을 구분하지 못할 수 있습니다. 이미 `�`로 대체된 바이트도 되살리지 못합니다.
- `Merge`·`Pad`·기본값·통화 별칭은 샘플에 명시된 제공처 정책입니다. 모든 불규칙한 CSV에 안전한 자동 복구가 아닙니다. `Currency`는 접두부만 처리하므로 금액 구간은 별도 정책으로 나눕니다.
- `Date`는 연도·월·일을 요구합니다. `1-10`, `Feb-23` 같은 값에 연도를 임의로 채우지 않습니다. `%b`/`%B`는 실행 환경의 로캘 영향을 받으므로 날짜 예제는 숫자 형식을 사용합니다.
- 오류 이후 다음 레코드를 계속 처리하려면 [reject_records.py](./reject_records.py)처럼 열린 컨텍스트 안에서 `row()`의 검증 오류를 잡고 `raw()`를 저장한 뒤 다음 레코드를 읽으세요. `rows()`에서 검증 예외가 발생한 generator는 재사용하지 않습니다. 파싱·디코딩 오류 이후에는 경계를 추측하며 읽기를 계속하지 않습니다. `row`는 레코드의 마지막 물리적 줄 번호입니다.
- 거부 기록에는 검증에 실패한 값과 검증 전 전체 필드가 들어갑니다. 실제 고객 데이터에서는 보관 위치·접근 권한·비식별화 정책을 확인하세요.
- 대용량 처리에서는 `list(csv.rows())` 대신 스트리밍이나 제한 배치를 사용하세요. 배치 한도는 행 수 기준이며 한 행의 바이트 크기를 제한하지 않습니다. 샘플의 소형 데이터 검증은 실제 200GB 처리 성능 검증이 아닙니다.
- 샘플 검증은 설치된 `csvd2c`를 다른 작업 디렉터리의 격리 subprocess에서 import합니다. `assert` 검증을 끄는 `python -O`는 사용하지 마세요.

전체 사용 규칙은 [사용 매뉴얼](../docs/README.md)을 참고하세요.
