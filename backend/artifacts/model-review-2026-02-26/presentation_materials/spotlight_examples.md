# 발표용 변경 예시 (Spotlight)

아래는 실제 룰 적용으로 바뀐 대표 케이스입니다.

## 1. Normalize identifier to allowed pattern
- 모델: `IDTA 02019-1-0_Template_PlantAssetManagement`
- 경로: `/submodels/0/qualifiers/1/type`
- Before:
```json
"SMT/Cardinality"
```
- After:
```json
"SMT_Cardinality"
```

## 2. Normalize IEC61360 dataSpecification reference
- 모델: `IDTA 02019-1-0_Template_PlantAssetManagement`
- 경로: `/concept_descriptions/0/embedded_data_specifications/0/data_specification/keys/0/value`
- Before:
```json
"https://admin-shell.io/DataSpecificationTemplates/DataSpecificationIEC61360/3/0"
```
- After:
```json
"https://admin-shell.io/DataSpecificationTemplates/DataSpecificationIec61360/3"
```

