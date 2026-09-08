# -*- coding: utf-8 -*-
"""
[1단계] TAGO OpenAPI로 전국 '군' 단위 버스 정류장·노선 수집.
- config.SERVICE_KEY 필요 (다시 수집할 때만).
- 결과: out/bus_service.csv  (군별 정류장수·단일노선비율·노선당정류장·중심좌표)
- 요청 폭주 시 응답 누락을 재시도(retry_empty)로 보정.
"""
import os, sys, time, collections
import requests, numpy as np, pandas as pd
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

BASE = "http://apis.data.go.kr/1613000/BusRouteInfoInqireService"
sess = requests.Session()

def tago(op, params, retry_empty=False):
    p = {"serviceKey": config.SERVICE_KEY, "numOfRows": 3000, "pageNo": 1, "_type": "json"}
    p.update(params)
    for _ in range(6):
        try:
            b = sess.get(f"{BASE}/{op}", params=p, timeout=25).json()["response"]["body"]["items"]
            if b in ("", None):
                if retry_empty:
                    time.sleep(0.4); continue
                return []
            it = b["item"]; return it if isinstance(it, list) else [it]
        except Exception:
            time.sleep(0.5)
    return []

def main():
    cities = tago("getCtyCodeList", {})
    targets = {c["citycode"]: c["cityname"] for c in cities if c["cityname"].endswith("군")}
    rows = []
    for code, name in targets.items():
        routes = tago("getRouteNoList", {"cityCode": code}, retry_empty=True)
        sr = collections.defaultdict(set); meta = {}
        for rt in routes:
            for st in tago("getRouteAcctoThrghSttnList",
                           {"cityCode": code, "routeId": rt["routeid"]}, retry_empty=True):
                sr[st["nodeid"]].add(rt["routeid"])
                if st.get("gpslati"):
                    meta[st["nodeid"]] = (float(st["gpslati"]), float(st["gpslong"]))
        if not sr:
            continue
        rc = [len(v) for v in sr.values()]
        la = [m[0] for m in meta.values()]; lo = [m[1] for m in meta.values()]
        rows.append({"군": name, "n_routes": len(routes), "n_stops": len(sr),
                     "단일노선비율": round(sum(1 for x in rc if x == 1) / len(rc) * 100, 2),
                     "노선당정류장": round(len(sr) / len(routes), 3),
                     "lat": round(np.mean(la), 5), "lon": round(np.mean(lo), 5)})
        print(f"  수집: {name} (정류장 {len(sr)})")
    os.makedirs(config.OUT_DIR, exist_ok=True)
    pd.DataFrame(rows).to_csv(f"{config.OUT_DIR}/bus_service.csv", index=False, encoding="utf-8-sig")
    print(f"[완료] {len(rows)}개 군 → {config.OUT_DIR}/bus_service.csv")

if __name__ == "__main__":
    main()
