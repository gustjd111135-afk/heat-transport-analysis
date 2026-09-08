# -*- coding: utf-8 -*-
"""
[3단계] K-means 군집분석(취약 3유형) + 전국 choropleth + 탄소 시나리오.
- 입력: out/risk_index.csv
- 행정경계 GeoJSON은 공개 저장소에서 자동 다운로드.
- 결과: out/ 아래 PNG 및 유형이 추가된 risk_index_clustered.csv
"""
import os, sys, requests
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def korean_font():
    for path in ["/usr/share/fonts/truetype/nanum/NanumGothic.ttf", "NanumGothic.ttf"]:
        if os.path.exists(path):
            fm.fontManager.addfont(path)
            plt.rcParams["font.family"] = fm.FontProperties(fname=path).get_name()
            break
    plt.rcParams["axes.unicode_minus"] = False

def download(url, path):
    if not os.path.exists(path):
        print(f"  다운로드: {os.path.basename(path)}")
        open(path, "wb").write(requests.get(url, timeout=90).content)
    return path

def main():
    korean_font()
    m = pd.read_csv(f"{config.OUT_DIR}/risk_index.csv")

    # --- K-means 3유형 ---
    F = pd.DataFrame({"배차": np.log1p(m["svc_adj"]), "폭염": m["폭염일수"], "고령": m["고령비율"]})
    Z = StandardScaler().fit_transform(F)
    m["cluster"] = KMeans(n_clusters=3, random_state=1, n_init=20).fit_predict(Z)
    m.to_csv(f"{config.OUT_DIR}/risk_index_clustered.csv", index=False, encoding="utf-8-sig")

    # 군집 산점도
    fig, ax = plt.subplots(figsize=(8, 6))
    for c in sorted(m["cluster"].unique()):
        d = m[m["cluster"] == c]
        ax.scatter(d["폭염일수"], d["고령비율"], s=np.log1p(d["svc_adj"]) * 22, alpha=0.7,
                   edgecolor="k", linewidth=0.3, label=f"유형 {c}")
    ax.set_xlabel("폭염일수 (6~9월)"); ax.set_ylabel("고령비율 (%)")
    ax.set_title("K-means 군집분석: 이동취약 3유형 (점 크기=배차 부실도)")
    ax.legend(); plt.tight_layout()
    plt.savefig(f"{config.OUT_DIR}/cluster.png", dpi=150, bbox_inches="tight"); plt.close()

    # --- 전국 choropleth ---
    try:
        import geopandas as gpd
        gj = download(config.SIGUNGU_GEOJSON_URL, f"{config.DATA_DIR}/sigungu.geojson")
        gdf = gpd.read_file(gj)
        nm = {("횡성군" if r["군"] == "원주시/횡성군" else r["군"]): r["이동포기위험지수"] for _, r in m.iterrows()}
        gdf["idx"] = gdf["name"].map(nm)
        fig, ax = plt.subplots(figsize=(9, 11))
        gdf.plot(ax=ax, color="#eeeeee", edgecolor="white", linewidth=0.3)
        gdf[gdf["idx"].notna()].plot(ax=ax, column="idx", cmap="RdYlGn_r", edgecolor="#555",
                                     linewidth=0.4, legend=True)
        ax.set_title("전국 농어촌 이동포기 위험 지수"); ax.axis("off")
        plt.tight_layout(); plt.savefig(f"{config.OUT_DIR}/choropleth.png", dpi=150, bbox_inches="tight"); plt.close()
    except Exception as e:
        print("  (지도 생략 - geopandas 미설치 또는 다운로드 실패):", e)

    # --- 탄소 시나리오 ---
    stops = 130 + 172 + 114  # 상위 3군 우선후보 정류장(보고서 참조)
    ann = lambda n: n * config.ROUND_TRIP_KM * config.EMISSION_FACTOR * config.OPERATING_DAYS / 1000 * stops
    print("탄소 절감 추정(tCO2/년):", {f"{n}대": round(ann(n)) for n in (2, 3, 4)})
    print(f"\n[완료] out/ 에 결과 저장")

if __name__ == "__main__":
    main()
