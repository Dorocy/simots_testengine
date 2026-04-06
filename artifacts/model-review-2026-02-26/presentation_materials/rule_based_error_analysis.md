# 룰 기반 에러 분석 문서

## 1. 목적
이 문서는 `LLM`이 아닌 `Rule-based`로 고정 처리되는 에러를 정리한 자료다.
핵심은 다음 3가지다.
- 어떤 에러를 룰로 판정하는지
- 어떤 정답(보정값)으로 고치는지
- 어떤 경로(path)에 패치를 적용하는지

## 2. 이번 5개 모델에서의 실제 적용 결과
- 대상 모델: 5개
- 초기 에러: 1,031건
- 룰/정규화 후 에러: 0건
- 주요 적용 룰
  - `Normalize identifier to allowed pattern`: 584건
  - `Normalize IEC61360 dataSpecification reference`: 442건

참고: 이번 데이터셋에서는 위 2개 룰이 대부분을 차지했다.

## 3. 룰 카탈로그 (정답 기반)
| 에러 시그널(메시지) | 룰 이름(summary) | 보정 로직(정답) | 패치 경로 규칙 |
|---|---|---|---|
| `definition is missing` | Add missing definition | `[{"language":"en","text":"arbitary definition custom"}]` 추가 | `<location>/embeddedDataSpecifications(또는 snake_case)/0/dataSpecificationContent(또는 snake_case)/definition` |
| `definition.language is missing english` | Add English definition | `definition`을 영어 엔트리 포함 값으로 치환 | 위와 동일 |
| `AASc-3a-002 ... English language is missing` | Ensure English preferred name | `preferredName[0] = {"language":"en","text":"arbitrary"}` 보장 | `<location>/preferredName(또는 preferred_name)/0` |
| `does not contain a language according to BCP46` | Normalize language to BCP47 tag | `language = "en"` | `<location>/language` (이미 `/language`면 그대로) |
| `String '...' does not match pattern [a-zA-Z][a-zA-Z0-9_]*` | Normalize identifier to allowed pattern | 금지 문자 -> `_`, 연속 `_` 축약, 시작이 영문 아니면 `A_` prefix | `location` 자체 필드에 replace |
| `Property 'text' must not be empty` | Replace empty text | `text = "arbitrary"` | `<location>/text` |
| `AASd-123 ... first key must be one of AasIdentifiables` | Use ExternalReference for GlobalReference/EMPTY | `type = "ExternalReference"` | `<location>/type` |
| `is not a valid TypeOfFaxNumber` | Normalize TypeOfFaxNumber value | 메시지 값 추출 후 공백 정리, 없으면 기본 코드 사용 | `<location>/value` |
| `cannot convert to lang string: no value` | Add missing lang string value | `value = [{"language":"en","text":"arbitrary"}]` | `<location>/value` |
| `cannot convert to string: no value` | Add missing string value | `value = "arbitrary"` | `<location>/value` |
| `dataSpecification/keys[0] has unexpected value ... expected ...` | Normalize IEC61360 dataSpecification reference | `expected` URL로 canonical 치환 | `<location>/dataSpecification(또는 data_specification)/keys/0/value` |

## 4. 핵심 정답 규칙(발표용 요약)
- 패턴 위반 문자열: `/` 등 특수문자 -> `_` (`SMT/Cardinality -> SMT_Cardinality`)
- IEC61360 참조: 항상 `expected` canonical URL 사용
- 빈 텍스트: `"arbitrary"`
- 언어 코드: `"en"` 기본 보정 (BCP46/47 실패 시)
- 영어 필수 필드: 영어 엔트리 강제 추가

## 5. 왜 룰 기반이 유효한가
- 동일한 에러 시그널에 대해 동일한 정답을 적용 가능
- 위치(`location`) 기반 patch라 수정 대상이 명확함
- 대량 반복 오류에 대해 빠르고 일관된 처리 가능

## 6. LLM으로 넘겨야 하는 경우
- 에러 메시지에서 canonical 정답을 확정할 수 없는 케이스
- 문맥 해석이 필요한 자유 텍스트/도메인 판단 케이스
- 룰 매칭에 실패한 예외 케이스
