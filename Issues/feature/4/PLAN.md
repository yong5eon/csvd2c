# 작업 계획

## 대상과 범위

- 작업 대상 저장소: `csvd2c`
- 작업 브랜치: `feature/4`
- 확인된 기준 브랜치: `master`
- 요구사항: [REQUIREMENTS.md](./REQUIREMENTS.md)
- 이슈 원문과 현재 동작: [README.md](./README.md)
- 병합 대상 브랜치는 아직 확정되지 않았으며, 이 계획에서는 병합·커밋·푸시를 수행하지 않습니다.

## 수행 순서

1. **`CSV` 생성자와 reader 연결**
   - `src/CSV.py` 생성자에 keyword-only `escapechar: Optional[str] = None`을 추가하고 인스턴스 설정으로 보관합니다.
   - `open()`의 `csv.reader` 생성에 해당 설정을 전달합니다.
   - `delimiter`, `strict`, 기본 `doublequote`, 파일 읽기 모드 및 예외 전파 동작은 유지합니다.
   - 선행 조건: 없음.

2. **회귀·기능 테스트 추가**
   - `tests/test_csv.py`에 이슈의 합성 TSV를 `strict=True`와 backslash `escapechar`로 읽어 기대 필드 값을 확인하는 테스트를 추가합니다.
   - `rb`, `r`, `rt` 각각에서 동일 설정이 적용되는지 검사합니다.
   - 이스케이프된 구분자·backslash 및 인용된 다중 물리행 입력의 결과를 같은 설정의 표준 `csv.reader`와 비교합니다.
   - `escapechar=None` 기본 동작, 기존 CSV·TSV와 `doublequote` 동작, row·column Validator 적용 순서를 회귀 확인합니다.
   - 잘못된 `escapechar` 설정이 표준 파서 오류로 드러나며 숨겨지지 않는지 검사합니다.
   - 선행 조건: 1단계.

3. **한국어·영어 사용 문서 갱신**
   - `docs/README.md`와 `docs/README.en.md`의 읽기 설정 설명에 `escapechar`와 기본값 `None`을 추가합니다.
   - 두 문서에 `CSV(delimiter="\t", escapechar="\\", strict=True)` 형태의 실제 동작과 일치하는 사용 예시를 제공합니다.
   - 기본 동작, `strict=True` 및 Python 표준 파서 오류 전파에 대한 기존 설명과 모순이 없는지 확인합니다.
   - 선행 조건: 1단계의 API 형태 확정.

4. **인수 기준 검증 및 변경 검토**
   - 우선 `python -m unittest discover -s tests -p "test_csv.py" -v`로 CSV 기능 테스트를 실행합니다.
   - 이어 `python -m unittest discover -s tests -p "test_*.py" -v`로 전체 회귀 테스트를 실행합니다.
   - 이슈 합성 입력의 필드 값, 세 읽기 모드, 표준 `csv.reader` 결과 비교, 기본값·Validator 순서 및 오류 전파를 요구사항의 인수 기준에 대조합니다.
   - 한국어·영어 문서의 옵션·예시 일치, 상대 링크, `git diff --check` 및 변경 범위를 확인합니다.
   - 선행 조건: 1~3단계.

## 인수 기준별 검증

| 인수 기준 | 검증 방법 |
| --- | --- |
| escape된 인용부호가 있는 TSV를 엄격 파싱 | 생성자에 `delimiter`, `escapechar`, `strict=True`를 지정한 테스트에서 정확한 필드 값 확인 |
| escape된 구분자·backslash·인용된 다중 물리행이 표준 파서와 일치 | 동일 입력과 옵션으로 `csv.reader`를 직접 호출해 레코드 결과 비교 |
| 세 파일 모드에서 설정 적용 | `rb`, `r`, `rt`별 테스트 실행 |
| 기본 `None`, 일반 CSV·TSV와 `doublequote` 동작 유지 | 기존 테스트와 기본값 회귀 테스트 실행 |
| row·column Validator 순서 유지 | 기존 순서 검증과 새 설정을 결합한 테스트 실행 |
| 잘못된 설정 오류 전파 | 잘못된 `escapechar`로 열 때 표준 파서 예외가 호출자에게 전달되는지 확인 |
| 한국어·영어 문서 동기화 | 두 매뉴얼의 기본값·API 예시·상대 링크를 서로 대조 |

## 제외 사항

- 별도 CSV 전처리·복구 로직, `strict=False` 우회 및 새로운 reader 옵션 추가
- 원본 데이터 전체 스캔, 운영 적재, 릴리즈·배포
- 병합 대상 브랜치가 확인되지 않은 상태에서의 병합
