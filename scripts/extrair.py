#!/usr/bin/env python3
"""
Extrai leads do DDD 17 a partir dos Dados Abertos CNPJ da Receita Federal.

Estratégia em 3 passadas para nunca carregar a base inteira em RAM:
  1) Estabelecimentos*.zip -> filtra DDD 17, guarda registros + set de cnpj_basico
  2) Empresas*.zip         -> pega razao social/porte APENAS dos cnpj_basico do set
  3) Simples.zip           -> flag MEI/Simples APENAS dos cnpj_basico do set

Fonte: https://arquivos.receitafederal.gov.br  (dados abertos, competencia 2026-08)
"""
import csv, io, json, os, re, sys, zipfile
from collections import Counter, defaultdict

DDD_ALVO = "17"
RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "out")
RAW, OUT = os.path.abspath(RAW), os.path.abspath(OUT)
os.makedirs(OUT, exist_ok=True)

SITUACAO = {"01": "NULA", "02": "ATIVA", "03": "SUSPENSA", "04": "INAPTA", "08": "BAIXADA"}
PORTE    = {"00": "NAO INFORMADO", "01": "MICRO EMPRESA", "03": "PEQUENO PORTE", "05": "DEMAIS"}
MATRIZ   = {"1": "MATRIZ", "2": "FILIAL"}

# telefones-lixo que aparecem muito na base (placeholders)
LIXO = re.compile(r'^(\d)\1+$')          # 11111111, 000000000...
SEQ  = {"12345678", "123456789", "987654321", "12345679"}

# a base da RF traz nomes com aspas soltas e espacos duplicados
LIMPA_BORDA = re.compile(r'^[\"\'\s]+|[\"\'\s]+$')
LIMPA_MULTI = re.compile(r'\s{2,}')


def limpa(v):
    """Normaliza campo textual vindo da Receita."""
    return LIMPA_MULTI.sub(" ", LIMPA_BORDA.sub("", v or ""))


# Empresario individual/MEI tem a razao social como "<inscricao> <NOME>" ou
# "<NOME> <CPF>". O numero e removido: nao serve para prospeccao e, no caso do
# CPF, e dado pessoal que nao ha razao para replicar (minimizacao - LGPD).
PREFIXO_NUM = re.compile(r'^\d[\d.\-/]{6,17}\s+(?=\S)')
SUFIXO_CPF  = re.compile(r'\s+\d{9,14}$')


def sem_inscricao(v):
    """Remove numero de inscricao (CNPJ/CPF) do inicio ou fim do nome."""
    limpo = SUFIXO_CPF.sub("", PREFIXO_NUM.sub("", v or ""))
    return limpo if limpo.strip() else (v or "")


SEM_NOME = "NÃO DETECTADO"
# CPF/CNPJ grudado no nome sem espaco separando
NUM_COLADO = re.compile(r'\s*\d{6,}\s*')


def nome_exibicao(fantasia, razao):
    """Nome legivel, ou SEM_NOME quando o cadastro nao traz nada aproveitavel.

    A Receita aceita qualquer coisa no campo: ha registros com '*', '-', '3152'
    e iniciais soltas. Marcar como nao detectado e mais honesto do que exibir
    lixo ou repetir o CNPJ que ja esta na coluna ao lado.
    """
    n = NUM_COLADO.sub(" ", sem_inscricao(fantasia or razao)).strip(" -.")
    if len(re.sub(r'[^A-Za-zÀ-ÿ]', "", n)) < 3:
        return SEM_NOME
    return LIMPA_MULTI.sub(" ", n)


def linhas(zip_path):
    """Itera linhas de um zip da RF (1 CSV interno, latin-1, ';' com aspas)."""
    with zipfile.ZipFile(zip_path) as z:
        nome = z.namelist()[0]
        with z.open(nome) as fh:
            txt = io.TextIOWrapper(fh, encoding="latin-1", newline="")
            for row in csv.reader(txt, delimiter=";", quotechar='"'):
                yield row


def norm_fone(ddd, fone):
    """Normaliza e classifica. Retorna (e164, tipo) ou (None, motivo_descarte)."""
    ddd = (ddd or "").strip().lstrip("0")
    fone = re.sub(r"\D", "", (fone or "").strip())
    if ddd != DDD_ALVO:
        return None, "ddd"
    if not fone or fone in ("0", "00"):
        return None, "vazio"
    if LIXO.match(fone) or fone in SEQ:
        return None, "lixo"

    if len(fone) == 9 and fone[0] == "9":
        tipo = "MOVEL"
    elif len(fone) == 8 and fone[0] in "6789":
        fone, tipo = "9" + fone, "MOVEL"      # legado pre-nono-digito
    elif len(fone) == 8 and fone[0] in "2345":
        tipo = "FIXO"
    else:
        return None, "formato"
    return f"55{ddd}{fone}", tipo


def main():
    # ---------- tabelas auxiliares ----------
    municipios = {c.strip(): d.strip() for c, d in
                  (r[:2] for r in linhas(os.path.join(RAW, "Municipios.zip")) if len(r) >= 2)}
    cnaes = {c.strip(): d.strip() for c, d in
             (r[:2] for r in linhas(os.path.join(RAW, "Cnaes.zip")) if len(r) >= 2)}
    print(f"[aux] {len(municipios)} municipios, {len(cnaes)} cnaes", flush=True)

    # ---------- passada 1: estabelecimentos ----------
    regs, descartes = [], Counter()
    vistos = set()          # dedup por (telefone, cnpj)
    basicos = set()

    for i in range(10):
        p = os.path.join(RAW, f"Estabelecimentos{i}.zip")
        if not os.path.exists(p):
            print(f"[!] faltando {p}", flush=True); continue
        n0 = len(regs)
        for r in linhas(p):
            if len(r) < 30:
                continue
            if r[21].strip() != DDD_ALVO and r[23].strip() != DDD_ALVO:
                continue
            cnpj = f"{r[0]}{r[1]}{r[2]}"
            fones = []
            for ddd, fone, rot in ((r[21], r[22], "principal"), (r[23], r[24], "secundario")):
                e164, tipo = norm_fone(ddd, fone)
                if e164:
                    fones.append((e164, tipo, rot))
                else:
                    descartes[tipo] += 1
            if not fones:
                continue
            mun = municipios.get(r[20].strip().lstrip("0").zfill(4), "") or municipios.get(r[20].strip(), "")
            base = {
                "cnpj": cnpj,
                "cnpj_basico": r[0],
                "fantasia": limpa(r[4].strip()),
                "situacao": SITUACAO.get(r[5].strip(), r[5].strip()),
                "abertura": r[10].strip(),
                "cnae": r[11].strip(),
                "cnae_desc": cnaes.get(r[11].strip(), ""),
                "tipo_unid": MATRIZ.get(r[3].strip(), ""),
                "logradouro": limpa(f"{r[13]} {r[14]} {r[15]}".strip()),
                "bairro": limpa(r[17].strip()),
                "cep": r[18].strip(),
                "uf": r[19].strip(),
                "cidade": mun,
                "email": r[27].strip().lower(),
            }
            for e164, tipo, rot in fones:
                chave = (e164, cnpj)
                if chave in vistos:
                    continue
                vistos.add(chave)
                regs.append({**base, "telefone": e164, "tipo_fone": tipo, "origem_fone": rot})
            basicos.add(r[0])
        print(f"[estab {i}] +{len(regs)-n0:>7} registros (acum {len(regs)})", flush=True)

    print(f"[1] {len(regs)} linhas telefone / {len(basicos)} empresas distintas", flush=True)

    # ---------- passada 2: empresas ----------
    emp = {}
    for i in range(10):
        p = os.path.join(RAW, f"Empresas{i}.zip")
        if not os.path.exists(p):
            print(f"[!] faltando {p}", flush=True); continue
        for r in linhas(p):
            if len(r) < 6 or r[0] not in basicos:
                continue
            emp[r[0]] = {"razao_social": sem_inscricao(limpa(r[1])),
                         "porte": PORTE.get(r[5].strip(), ""),
                         "capital": r[4].strip().replace(",", ".")}
    print(f"[2] {len(emp)} empresas enriquecidas", flush=True)

    # ---------- passada 3: simples/MEI ----------
    mei = {}
    p = os.path.join(RAW, "Simples.zip")
    if os.path.exists(p):
        for r in linhas(p):
            if len(r) < 5 or r[0] not in basicos:
                continue
            mei[r[0]] = {"simples": r[1].strip() == "S", "mei": r[4].strip() == "S"}
    print(f"[3] {len(mei)} registros Simples/MEI", flush=True)

    # ---------- join + saida ----------
    for g in regs:
        b = g["cnpj_basico"]
        e = emp.get(b, {}); m = mei.get(b, {})
        g["razao_social"] = e.get("razao_social", "")
        g["porte"] = e.get("porte", "")
        g["capital"] = e.get("capital", "")
        g["mei"] = m.get("mei", False)
        g["simples"] = m.get("simples", False)
        g["nome"] = nome_exibicao(g["fantasia"], g["razao_social"])
        g["fonte"] = "Receita Federal - Dados Abertos CNPJ 2026-08"

    regs.sort(key=lambda x: (x["cidade"], x["nome"]))

    cols = ["telefone", "tipo_fone", "nome", "razao_social", "fantasia", "cnpj", "situacao",
            "porte", "mei", "simples", "cnae", "cnae_desc", "cidade", "uf", "bairro",
            "logradouro", "cep", "email", "abertura", "capital", "tipo_unid",
            "origem_fone", "fonte"]
    csv_path = os.path.join(OUT, "leads_ddd17.csv")
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore", delimiter=";")
        w.writeheader(); w.writerows(regs)

    with open(os.path.join(OUT, "leads_ddd17.json"), "w", encoding="utf-8") as f:
        json.dump(regs, f, ensure_ascii=False)

    # ---------- relatorio ----------
    ativos = [r for r in regs if r["situacao"] == "ATIVA"]
    rel = {
        "total": len(regs),
        "ativos": len(ativos),
        "moveis": sum(1 for r in regs if r["tipo_fone"] == "MOVEL"),
        "fixos": sum(1 for r in regs if r["tipo_fone"] == "FIXO"),
        "mei": sum(1 for r in regs if r["mei"]),
        "com_email": sum(1 for r in regs if r["email"]),
        "cidades": Counter(r["cidade"] for r in regs).most_common(),
        "cnaes": Counter(r["cnae_desc"] for r in regs).most_common(30),
        "situacoes": Counter(r["situacao"] for r in regs).most_common(),
        "descartes": dict(descartes),
    }
    with open(os.path.join(OUT, "relatorio.json"), "w", encoding="utf-8") as f:
        json.dump(rel, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*46}\nTOTAL........: {rel['total']:>8}\nATIVOS.......: {rel['ativos']:>8}")
    print(f"MOVEIS.......: {rel['moveis']:>8}\nFIXOS........: {rel['fixos']:>8}")
    print(f"MEI..........: {rel['mei']:>8}\nCOM EMAIL....: {rel['com_email']:>8}")
    print(f"CIDADES......: {len(rel['cidades']):>8}\n{'='*46}")
    print(f"-> {csv_path}")


if __name__ == "__main__":
    main()
