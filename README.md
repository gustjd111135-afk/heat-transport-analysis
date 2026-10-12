# 폭염·배차·고령 결합 「이동포기 위험 지수」 — 농어촌 DRT 우선배치 분석

여름 폭염기에 대중교통 이용이 어려워 외출을 포기하는 농어촌 고령층이 밀집한 지역을
데이터로 규명하고, 수요응답형 교통(DRT)의 우선 도입 지역을 제시하는 개념검증(PoC) 분석 코드입니다.


## 핵심 개념
- **이동포기 위험 지수** = ①버스 서비스 취약도 + ②폭염일수 + ③고령비율 (각 1/3 동일가중, 0~100)
- **서비스 취약도** = 단일노선 정류장 비율 × 노선당 정류장 수(배차 뜸함 보정)
- **K-means 군집분석**으로 배차/폭염/고령 주도형 3유형 분류 → 유형별 맞춤 처방

## 폴더 구조
```
├── config.py              # API 키, 관측소→도 매핑, 상수
├── requirements.txt
├── src/
│   ├── 1_collect_bus.py   # TAGO로 전국 군 버스 정류장·노선 수집
│   ├── 2_build_index.py   # 고령·폭염 결합 → 위험 지수 산출
│   └── 3_cluster_and_map.py # K-means 군집 + 전국 지도 + 탄소 시나리오
├── data/                  # 입력 데이터(공개 자료)
│   ├── elderly.csv        # 행안부 지역별 연령별 인구 (data.go.kr/data/15097972)
│   └── kma/               # 기상청 ASOS 일 최고기온 (연도별)
│       ├── asos_2024.csv   #   2024 여름 (data.kma.go.kr)
│       ├── asos_2025.csv   #   2025 여름
│       └── asos_2026.csv   #   2026 여름
 (data.kma.go.kr)
└── out/
    ├── bus_service.csv     # TAGO 수집 결과(포함) — 2·3단계 즉시 실행 가능
    └── risk_index.csv      # 최종 위험 지수·순위(재현 결과)
```

## 실행 방법
```bash
pip install -r requirements.txt

# (선택) 버스 데이터 재수집 — config.py 에 TAGO 인증키 필요
python src/1_collect_bus.py

# 지수 산출 (out/bus_service.csv 포함되어 있어 키 없이 바로 실행 가능)
python src/2_build_index.py

# 군집분석 + 지도 (행정경계 GeoJSON 자동 다운로드)
python src/3_cluster_and_map.py
```
> `out/bus_service.csv` 를 포함했으므로 **인증키 없이 2·3단계만으로 전체 결과를 재현**할 수 있습니다.
> 1단계 재수집에만 공공데이터포털 TAGO 인증키가 필요합니다.

## 데이터 출처
| 데이터 | 제공기관 | 출처 |
|---|---|---|
| 버스 노선/정류소 | 국토교통부(TAGO) | data.go.kr/data/15098529 |
| 연령별 인구 | 행정안전부 | data.go.kr/data/15097972 |
| 일 최고기온(ASOS, 3개년) | 기상청 | data.kma.go.kr |
| 시군구/읍면동 경계 | 오픈 GeoJSON | southkorea-maps, vuski/admdongkor |

> 지도 라벨의 한글 표시를 위해 NanumGothic 등 한글 폰트 설치를 권장합니다(미설치 시에도 CSV 결과는 동일하게 재현됩니다).

## 한계
- 폭염일수는 2024~2026 3개년 평균(다년 평균으로 확장 가능).
- 배차간격 공식값의 불완전성으로 노선 구조를 대리지표로 사용(방향성 확인, 상관은 약함).
- 본 지수는 이동 포기를 직접 관측한 것이 아니라 위험 지역을 선별하는 스크리닝 도구.
