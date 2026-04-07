# 발표 자료 초안 (2026-02-26 13:59)

## 1) 검증 대상
- 총 모델 수: 5
- 테스트 방식: Template 검증 -> 룰 기반 수정/정규화 -> 재검증

## 2) 핵심 결과
- 초기 총 에러: 1031
- 룰/정규화 후 잔여 에러: 0
- 감소 에러 수: 1031
- 감소율: 100.00%

## 3) 모델별 성과(요약)
- IDTA 02019-1-0_Template_PlantAssetManagement.json: 271 -> 0 (감소 271, 100.00%)
- IDTA 02029-1_Template_Sensor4.0_MeasurementValue.json: 35 -> 0 (감소 35, 100.00%)
- IDTA 02046-1-0_Template_WWMD.json: 103 -> 0 (감소 103, 100.00%)
- IDTA_02049_Template_QualityControlForMachining.json: 406 -> 0 (감소 406, 100.00%)
- IDTA02026-1-0_Template_ProvisionOf3DModels.json: 216 -> 0 (감소 216, 100.00%)

## 4) 주요 룰 기여도
- Normalize identifier to allowed pattern: 584건
- Normalize IEC61360 dataSpecification reference: 442건

## 5) 발표에 포함할 파일
- kpi_overview.csv (한 장 KPI)
- model_detail.csv (모델별 성과 표)
- rule_breakdown_total.csv (룰 기여도)
- change_examples.csv (전/후 샘플)
