#!/usr/bin/env python3
"""
Gera uma versao de demonstracao da pagina com dados FICTICIOS.

Serve para duas coisas: tirar as screenshots do README sem expor telefone,
nome ou e-mail de ninguem, e permitir que quem clona o repositorio veja a
interface sem antes baixar os 6,6 GB da Receita.

Telefones usam faixas obviamente falsas (90000-xxxx / 3000-xxxx) e os e-mails
o dominio example.com, reservado pela RFC 2606 justamente para exemplos.
Cidades e CNAEs sao reais - sao informacao publica, nao dado pessoal.
"""
import importlib.util, json, os, random, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("g", os.path.join(AQUI, "gerar_html.py"))
g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)

CIDADES = ["SAO JOSE DO RIO PRETO", "BARRETOS", "CATANDUVA", "VOTUPORANGA",
           "BEBEDOURO", "FERNANDOPOLIS", "OLIMPIA", "MIRASSOL", "JALES",
           "NOVO HORIZONTE", "JOSE BONIFACIO", "GUAIRA", "MONTE APRAZIVEL"]
CNAES = [("4781400", "Comércio varejista de artigos do vestuário"),
         ("9602501", "Cabeleireiros, manicure e pedicure"),
         ("5611201", "Restaurantes e similares"),
         ("4399103", "Obras de alvenaria"),
         ("4712100", "Comércio varejista de mercadorias em geral"),
         ("8630501", "Atividade médica ambulatorial"),
         ("4520001", "Serviços de manutenção e reparação de automóveis"),
         ("0111301", "Cultivo de arroz"),
         ("4930202", "Transporte rodoviário de carga"),
         ("6920601", "Atividades de contabilidade")]
RAMOS = ["COMERCIO", "SERVICOS", "TRANSPORTES", "AGRICOLA", "DISTRIBUIDORA",
         "OFICINA", "MERCADO", "PADARIA", "CLINICA", "CONSTRUTORA"]
SOBRE = ["ALFA", "BETA", "CENTRAL", "UNIAO", "PRIMAVERA", "HORIZONTE", "AURORA",
         "PLANALTO", "PIONEIRA", "MODELO", "IDEAL", "REAL", "NOVA ERA"]
PORTES = ["MICRO EMPRESA", "PEQUENO PORTE", "DEMAIS"]
SITS = ["ATIVA"] * 8 + ["BAIXADA", "INAPTA"]


def main(n=600):
    random.seed(17)
    regs = []
    for i in range(n):
        movel = random.random() < .48
        tel = f"5517{'9000' + f'{i:05d}'[-5:] if movel else '3000' + f'{i:04d}'}"
        tel = f"5517900{i:05d}" if movel else f"55173000{i:04d}"
        cnae, desc = random.choice(CNAES)
        nome = f"{random.choice(RAMOS)} {random.choice(SOBRE)} {i:03d}"
        mei = random.random() < .35
        regs.append({
            "telefone": tel, "tipo_fone": "MOVEL" if movel else "FIXO",
            "nome": nome if random.random() > .02 else "NÃO DETECTADO",
            "razao_social": f"{nome} LTDA", "fantasia": nome,
            "cnpj": f"{10000000 + i:08d}000{random.randint(100,199)}"[:14].ljust(14, "0"),
            "situacao": random.choice(SITS), "porte": random.choice(PORTES),
            "mei": mei, "simples": random.random() < .6,
            "cnae": cnae, "cnae_desc": desc,
            "cidade": random.choice(CIDADES), "uf": "SP", "regiao": True,
            "bairro": random.choice(["CENTRO", "JARDIM AMERICA", "VILA NOVA", "DISTRITO INDUSTRIAL"]),
            "logradouro": f"RUA EXEMPLO {random.randint(1, 999)}",
            "cep": f"150{random.randint(10000, 99999)}"[:8],
            "email": f"contato{i:03d}@example.com" if random.random() < .55 else "",
            "abertura": f"20{random.randint(10,24):02d}0101", "capital": "1000",
            "tipo_unid": "MATRIZ", "origem_fone": "principal",
            "fonte": "DADOS FICTÍCIOS — demonstração da interface",
        })

    tmp = os.path.join(AQUI, "..", "data", "demo")
    os.makedirs(tmp, exist_ok=True)
    json.dump(regs, open(os.path.join(tmp, "leads_ddd17.json"), "w", encoding="utf-8"),
              ensure_ascii=False)

    g.OUT = os.path.abspath(tmp)
    g.DEST = os.path.abspath(os.path.join(AQUI, "..", "demo.html"))
    g.main()
    print(f"-> {g.DEST}  ({n} registros fictícios)")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 600)
