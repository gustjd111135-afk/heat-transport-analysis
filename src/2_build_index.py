# -*- coding: utf-8 -*-
"""
[2단계] 세 데이터를 결합해 「이동포기 위험 지수」 산출.
- 입력: out/bus_service.csv, data/elderly.csv, data/kma_asos.csv
- 서비스 취약도 = 단일노선비율 × 노선당정류장 (배차 보정)
- 세 변수 min-max 정규화 후 동일가중(1/3) 합산 → 0~100 지수
- 결과: out/risk_index.csv
"""
import os, sys, re
import numpy as np, pandas as pd
from collections import defaultdict
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def base(n): return re.sub(r"(군|시|구)$", "", str(n))

def load_elderly():
    df = pd.read_csv(f"{config.DATA_DIR}/elderly.csv", encoding="cp949", low_memory=False)
    agec = [c for c in df.columns if re.match(r"(\d+)세", c) and int(re.match(r"(\d+)", c).group(1)) >= 65]
    for c in ["계"] + agec:
        df[c] = pd.to_numeric(df[c].astype(str).str.replace(",", ""), errors="coerce").fillna(0)
    df["고령"] = df[agec].sum(axis=1)
    d = df[df["읍면동명"].astype(str).str.strip().ne("")]
    g = d.groupby(["시도명", "시군구명"], as_index=False).agg(총인구=("계", "sum"), 고령=("고령", "sum"))
    g["고령비율"] = g["고령"] / g["총인구"] * 100
    return g

def load_heat():
    w = pd.read_csv(f"{config.DATA_DIR}/kma_asos.csv", sep="\t", encoding="cp949")
    w.columns = ["지점", "지점명", "일시", "tmax"][:len(w.columns)]
    w["tmax"] = pd.to_numeric(w["tmax"], errors="coerce")
    heat = {base(n): int(c) for n, c in w[w["tmax"] >= config.HEATWAVE_TEMP].groupby("지점명").size().items()}
    for n in w["지점명"].unique():
        heat.setdefault(base(n), 0)
    return heat

def main():
    bus = pd.read_csv(f"{config.OUT_DIR}/bus_service.csv")
    g = load_elderly()
    heat = load_heat()

    e_map = {base(r["시군구명"]): r["고령비율"] for _, r in g.iterrows()}
    p_map = {base(r["시군구명"]): config.sido_to_prov(r["시도명"]) for _, r in g.iterrows()}
    pv = defaultdict(list)
    for n, c in heat.items():
        p = config.STATION_TO_PROV.get(n)
        if p:
            pv[p].append(c)
    prov_heat = {p: np.mean(v) for p, v in pv.items()}

    rec = []
    for _, r in bus.iterrows():
        key = base(str(r["군"]).split("/")[-1])
        e = e_map.get(key)
        if e is None:
            continue
        h = heat.get(key, prov_heat.get(p_map.get(key)))
        rec.append({"군": r["군"], "도": p_map.get(key), "단일노선비율": r["단일노선비율"],
                    "노선당정류장": r["노선당정류장"], "폭염일수": h, "고령비율": e,
                    "lat": r["lat"], "lon": r["lon"],
                    "svc_adj": r["단일노선비율"] * r["노선당정류장"]})
    m = pd.DataFrame(rec)

    norm = lambda s: (s - s.min()) / (s.max() - s.min())
    m["n_svc"], m["n_heat"], m["n_old"] = norm(m["svc_adj"]), norm(m["폭염일수"]), norm(m["고령비율"])
    m["이동포기위험지수"] = ((m["n_svc"] + m["n_heat"] + m["n_old"]) / 3 * 100).round(1)
    m = m.sort_values("이동포기위험지수", ascending=False).reset_index(drop=True)
    m.insert(0, "순위", m.index + 1)
    m.to_csv(f"{config.OUT_DIR}/risk_index.csv", index=False, encoding="utf-8-sig")

    print(m.head(10)[["순위", "군", "도", "폭염일수", "고령비율", "이동포기위험지수"]].to_string(index=False))
    print(f"\n[완료] {len(m)}개 군 → {config.OUT_DIR}/risk_index.csv")

if __name__ == "__main__":
    main()
