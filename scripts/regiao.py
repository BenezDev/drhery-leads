#!/usr/bin/env python3
"""
Determina quais municipios pertencem de fato a area de cobertura do DDD 17.

Criterio derivado dos proprios dados, sem lista externa nem limiar arbitrario:
para cada municipio conta-se a proporcao de estabelecimentos com telefone DDD 17
sobre o total de estabelecimentos com telefone. Municipios da area 17 ficam com
proporcao alta; os de fora aparecem so por empresas que cadastraram um numero 17.
"""
import importlib.util, json, os, sys
from collections import Counter

spec = importlib.util.spec_from_file_location("ex", os.path.join(os.path.dirname(__file__), "extrair.py"))
ex = importlib.util.module_from_spec(spec); spec.loader.exec_module(ex)

CORTE = 0.30   # >=30% dos telefones do municipio no DDD 17

def main():
    total, d17 = Counter(), Counter()
    for i in range(10):
        p = os.path.join(ex.RAW, f"Estabelecimentos{i}.zip")
        if not os.path.exists(p):
            continue
        for r in ex.linhas(p):
            if len(r) < 30:
                continue
            m = r[20].strip()
            if not m:
                continue
            t1, t2 = r[22].strip(), r[24].strip()
            if not (t1 or t2) or (t1 in ("", "0") and t2 in ("", "0")):
                continue
            total[m] += 1
            if r[21].strip() == "17" or r[23].strip() == "17":
                d17[m] += 1
        print(f"[regiao] partição {i} lida", flush=True)

    municipios = {c.strip(): d.strip() for c, d in
                  (r[:2] for r in ex.linhas(os.path.join(ex.RAW, "Municipios.zip")) if len(r) >= 2)}

    area = {}
    for m, n in d17.items():
        prop = n / total[m] if total[m] else 0
        if prop >= CORTE and total[m] >= 20:
            area[m] = {"nome": municipios.get(m.lstrip("0").zfill(4), "") or municipios.get(m, ""),
                       "prop": round(prop, 4), "estab": total[m], "ddd17": n}

    out = os.path.join(ex.OUT, "area_ddd17.json")
    json.dump(area, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"\nmunicípios na área do DDD 17: {len(area)}")
    top = sorted(area.items(), key=lambda x: -x[1]["ddd17"])[:12]
    for m, v in top:
        print(f"  {v['nome'][:28]:<28} {v['prop']*100:5.1f}%  ({v['ddd17']}/{v['estab']})")
    print(f"-> {out}")

if __name__ == "__main__":
    main()
