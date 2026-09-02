#!/usr/bin/env python3
"""
Gera a pagina HTML de leads (arquivo unico, offline, sem CDN).

Os dados vao embutidos como JSON colunar -> gzip -> base64, e sao
descomprimidos no browser via DecompressionStream (API nativa).
Isso mantem o arquivo abrivel por file:// (fetch de .json local
seria bloqueado por CORS) sem estourar o tamanho.
"""
import base64, gzip, json, os, sys
from collections import Counter

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "out"))
DEST = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "drhery_leads.html"))


def dicionarizar(regs, campo):
    vals = sorted({r.get(campo, "") or "" for r in regs})
    idx = {v: i for i, v in enumerate(vals)}
    return vals, idx


def main():
    src = os.path.join(OUT, "leads_ddd17.json")
    regs = json.load(open(src, encoding="utf-8"))
    print(f"[html] {len(regs)} registros carregados")

    cidades, ic = dicionarizar(regs, "cidade")
    cnaes,   in_ = dicionarizar(regs, "cnae_desc")
    bairros, ib = dicionarizar(regs, "bairro")
    situacoes, isit = dicionarizar(regs, "situacao")
    portes,  ip = dicionarizar(regs, "porte")

    rows = []
    for r in regs:
        flags = ((1 if r.get("mei") else 0) | (2 if r.get("simples") else 0)
                 | (4 if r.get("regiao") else 0))
        rows.append([
            r["telefone"][2:],                      # tira "55", fica DDD+numero
            1 if r["tipo_fone"] == "MOVEL" else 0,
            r.get("nome", ""),
            r.get("cnpj", ""),
            ic[r.get("cidade", "") or ""],
            in_[r.get("cnae_desc", "") or ""],
            isit[r.get("situacao", "") or ""],
            ip[r.get("porte", "") or ""],
            flags,
            ib[r.get("bairro", "") or ""],
            r.get("email", ""),
            r.get("logradouro", ""),
            r.get("cep", ""),
            r.get("abertura", ""),
            r.get("cnae", ""),
        ])

    payload = {
        "meta": {
            "fonte": "Receita Federal - Dados Abertos CNPJ, competencia 2026-08",
            "url": "https://arquivos.receitafederal.gov.br",
            "ddd": "17",
            "total": len(rows),
        },
        "dic": {"cidade": cidades, "cnae": cnaes, "bairro": bairros,
                "situacao": situacoes, "porte": portes},
        "rows": rows,
    }

    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    comp = gzip.compress(raw, 9)
    b64 = base64.b64encode(comp).decode("ascii")
    print(f"[html] json {len(raw)/1e6:.1f}MB -> gzip {len(comp)/1e6:.1f}MB -> b64 {len(b64)/1e6:.1f}MB")

    html = TEMPLATE.replace("__DADOS__", b64)
    with open(DEST, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[html] gerado: {DEST} ({os.path.getsize(DEST)/1e6:.1f}MB)")


TEMPLATE = r"""<!doctype html>
<html lang="pt-BR"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DR.Hery "Potter" Leads</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#040705; --bg2:#070d09; --pan:#0a1210; --pan2:#0e1a14;
  --line:#16301f; --line2:#1f4a2d;
  --vd:#00ff6a; --vd2:#00c853; --vdim:#0a3a1e;
  --am:#f2ff00; --am2:#ffd000;
  --tx:#c8ffdd; --tx2:#6f9f82; --tx3:#5f9a73;
  --bad:#ff2d55; --mov:#f2ff00; --fix:#00ff6a;
  --mono:'JetBrains Mono','Fira Code','Cascadia Mono','Ubuntu Mono','DejaVu Sans Mono',Consolas,monospace;
}
html[data-t="light"]{
  --bg:#eef5ef; --bg2:#e4eee6; --pan:#fff; --pan2:#f2f8f3;
  --line:#c9ddcf; --line2:#9ec9ac; --vdim:#dff2e6;
  --vd:#00752f; --vd2:#006328; --am:#755f00; --am2:#63510a;
  --tx:#0d2417; --tx2:#3c6349; --tx3:#496a55;
  --mov:#755f00; --fix:#00752f; --bad:#b3001b;
}
/* no tema claro o glow neon vira ruido: some com ele */
html[data-t="light"] .stat b,html[data-t="light"] h1 .dr,
html[data-t="light"] h1 .hy,html[data-t="light"] tbody tr:hover .tel{text-shadow:none}
html[data-t="light"] header{box-shadow:none}
html[data-t="light"] .btn:hover,html[data-t="light"] .ic:hover,
html[data-t="light"] input:focus,html[data-t="light"] select:focus{box-shadow:none}
html,body{height:100%}
body{
  background:var(--bg); color:var(--tx); font:12.5px/1.5 var(--mono);
  display:flex; flex-direction:column; overflow:hidden;
  background-image:
    linear-gradient(rgba(0,255,106,.028) 1px,transparent 1px),
    linear-gradient(90deg,rgba(0,255,106,.028) 1px,transparent 1px);
  background-size:34px 34px;
}
html[data-t="light"] body{background-image:none}
/* scanlines */
body::after{
  content:"";position:fixed;inset:0;pointer-events:none;z-index:60;
  background:repeating-linear-gradient(180deg,rgba(0,0,0,.16) 0 1px,transparent 1px 3px);
  mix-blend-mode:multiply;opacity:.55;
}
html[data-t="light"] body::after{display:none}

/* ---------- header ---------- */
header{
  background:linear-gradient(180deg,var(--pan) 0%,var(--bg2) 100%);
  border-bottom:1px solid var(--line2);
  padding:9px 14px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;flex:none;
  box-shadow:0 0 26px rgba(0,255,106,.09);position:relative;
}
header::before{content:"";position:absolute;left:0;right:0;bottom:-1px;height:1px;
  background:linear-gradient(90deg,transparent,var(--vd),var(--am),var(--vd),transparent);opacity:.7}
.brand{display:flex;flex-direction:column;gap:1px;white-space:nowrap}
h1{font-size:18px;font-weight:700;letter-spacing:-.3px;position:relative;line-height:1.2}
h1 .dr{color:var(--am);text-shadow:0 0 9px rgba(242,255,0,.5)}
h1 .hy{color:var(--vd);text-shadow:0 0 11px rgba(0,255,106,.6)}
h1 .pt{color:var(--am2);font-style:italic}
h1 .ld{color:var(--vd2)}
h1::after{content:"_";color:var(--vd);animation:blink 1.1s steps(1) infinite}
@keyframes blink{50%{opacity:0}}
.glitch{position:relative;display:inline-block}
.glitch::before,.glitch::after{
  content:attr(data-txt);position:absolute;left:0;top:0;width:100%;
  pointer-events:none;opacity:.75;
}
.glitch::before{color:var(--am);clip-path:inset(0 0 58% 0);animation:gl1 4.2s infinite steps(1)}
.glitch::after{color:var(--vd);clip-path:inset(58% 0 0 0);animation:gl2 5.1s infinite steps(1)}
@keyframes gl1{0%,92%,100%{transform:translate(0)}94%{transform:translate(-2px,-1px)}97%{transform:translate(1px,1px)}}
@keyframes gl2{0%,90%,100%{transform:translate(0)}93%{transform:translate(2px,1px)}96%{transform:translate(-1px,-1px)}}
.sub{font-size:10px;color:var(--tx3);letter-spacing:.5px}
.sub b{color:var(--vd2)}

.stats{display:flex;gap:7px;flex-wrap:wrap;margin-left:auto;align-items:center}
.stat{
  background:var(--pan2);border:1px solid var(--line);border-left:2px solid var(--vd2);
  padding:3px 9px;font-size:10px;color:var(--tx2);white-space:nowrap;letter-spacing:.4px;
}
.stat b{color:var(--vd);font-size:12.5px;font-weight:700;display:block;
  text-shadow:0 0 8px rgba(0,255,106,.35)}
.stat.y{border-left-color:var(--am2)} .stat.y b{color:var(--am);text-shadow:0 0 8px rgba(242,255,0,.3)}

.btn{
  background:transparent;color:var(--vd);border:1px solid var(--line2);
  padding:5px 11px;font:inherit;font-size:11px;cursor:pointer;white-space:nowrap;
  letter-spacing:.6px;transition:.13s;
}
.btn:hover{border-color:var(--vd);background:var(--vdim);box-shadow:0 0 12px rgba(0,255,106,.28)}
.btn.p{border-color:var(--am2);color:var(--am)}
.btn.p:hover{border-color:var(--am);background:rgba(242,255,0,.08);box-shadow:0 0 14px rgba(242,255,0,.3)}

/* ---------- abas ---------- */
#abas{background:var(--bg2);border-bottom:1px solid var(--line);padding:0 14px;
  display:flex;gap:2px;align-items:flex-end;flex:none}
.aba{background:transparent;border:1px solid transparent;border-bottom:none;
  color:var(--tx3);padding:6px 16px;font:inherit;font-size:11px;cursor:pointer;
  letter-spacing:1px;transition:.13s;position:relative;top:1px}
.aba:hover{color:var(--vd2)}
.aba.on{color:var(--vd);border-color:var(--line2);background:var(--pan);
  box-shadow:0 -2px 0 var(--vd) inset}
#disparador{margin-left:auto;margin-bottom:4px}
#copiar{margin-bottom:4px}
.mail{color:var(--am);font-size:11.5px}
tbody tr:hover .mail{text-shadow:0 0 8px rgba(242,255,0,.4)}
#okcopy{position:fixed;bottom:18px;left:50%;transform:translateX(-50%);z-index:80;
  background:var(--pan);border:1px solid var(--vd);color:var(--vd);padding:7px 16px;
  font-size:11px;letter-spacing:1px;pointer-events:none;opacity:0;transition:opacity .2s}
#okcopy.on{opacity:1}

/* ---------- filtros ---------- */
#filtros{
  background:var(--pan);border-bottom:1px solid var(--line);
  padding:8px 14px;display:flex;gap:7px;flex-wrap:wrap;align-items:center;flex:none;
}
input,select{
  background:var(--bg);color:var(--tx);border:1px solid var(--line2);
  padding:5px 9px;font:inherit;font-size:11px;outline:none;transition:.13s;
}
input::placeholder{color:var(--tx3)}
input:focus,select:focus{border-color:var(--vd);box-shadow:0 0 0 1px var(--vdim),0 0 11px rgba(0,255,106,.2)}
select{max-width:215px;cursor:pointer}
select option{background:var(--bg);color:var(--tx)}
#q{flex:1;min-width:210px}
.chk{display:flex;align-items:center;gap:5px;font-size:10.5px;color:var(--tx2);
  cursor:pointer;user-select:none;white-space:nowrap;letter-spacing:.3px}
.chk:hover{color:var(--vd)}
.chk input{width:13px;height:13px;accent-color:var(--vd);cursor:pointer}

/* ---------- tabela ---------- */
#wrap{flex:1;overflow:auto;position:relative}
#wrap::-webkit-scrollbar{width:11px;height:11px}
#wrap::-webkit-scrollbar-track{background:var(--bg)}
#wrap::-webkit-scrollbar-thumb{background:var(--vdim);border:2px solid var(--bg)}
#wrap::-webkit-scrollbar-thumb:hover{background:var(--vd2)}
table{width:100%;min-width:1140px;border-collapse:collapse;table-layout:fixed}
thead th{
  position:sticky;top:0;z-index:2;background:var(--pan2);
  border-bottom:1px solid var(--line2);text-align:left;padding:6px 8px;
  font-size:10px;font-weight:700;color:var(--vd2);text-transform:uppercase;
  letter-spacing:1.1px;cursor:pointer;white-space:nowrap;user-select:none;
}
thead th:hover{color:var(--am);background:var(--vdim)}
thead th .ar{color:var(--am);margin-left:4px}
td{padding:5px 8px;border-bottom:1px solid rgba(22,48,31,.5);
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
tbody tr{transition:background .08s}
tbody tr:hover{background:var(--vdim);box-shadow:inset 3px 0 0 var(--vd)}
tr.done{opacity:.35}
tr.drop{opacity:.25;text-decoration:line-through var(--bad)}
.tel{font-weight:700;color:var(--vd);letter-spacing:.4px}
tbody tr:hover .tel{text-shadow:0 0 9px rgba(0,255,106,.55)}
.cnpj{color:var(--tx3);font-size:11px}
.nada{color:var(--tx3);font-style:italic;opacity:.75}
.tag{display:inline-block;padding:0 5px;font-size:9px;font-weight:700;letter-spacing:.7px;
  border:1px solid currentColor;line-height:15px}
.t-mov{color:var(--mov)} .t-fix{color:var(--fix)}
.t-mei{color:var(--am2);border-style:dashed}
.s-ATIVA{color:var(--vd)}
.s-BAIXADA,.s-NULA{color:var(--tx3)}
.s-INAPTA,.s-SUSPENSA{color:var(--am2)}
.acts{display:flex;gap:3px}
.ic{width:24px;height:22px;border:1px solid var(--line2);background:transparent;
  cursor:pointer;font-size:11px;line-height:1;display:grid;place-items:center;
  color:var(--tx2);text-decoration:none;padding:0;transition:.11s}
.ic:hover{border-color:var(--vd);color:var(--vd);box-shadow:0 0 9px rgba(0,255,106,.3)}
.ic.x:hover{border-color:var(--bad);color:var(--bad);box-shadow:0 0 9px rgba(255,45,85,.3)}
#vazio{padding:60px;text-align:center;color:var(--tx3);font-size:12px;letter-spacing:1px}

/* ---------- loader ---------- */
#load{position:fixed;inset:0;background:var(--bg);display:grid;place-items:center;z-index:99;text-align:center}
.bar{width:210px;height:3px;background:var(--vdim);margin:14px auto 0;overflow:hidden}
.bar i{display:block;height:100%;width:38%;background:linear-gradient(90deg,var(--vd),var(--am));
  animation:sl 1.05s ease-in-out infinite}
@keyframes sl{0%{transform:translateX(-100%)}100%{transform:translateX(360%)}}
#lmsg{color:var(--vd);font-size:11px;letter-spacing:2.2px;text-transform:uppercase}
#load .big{font-size:19px;font-weight:700;margin-bottom:4px}

@media(max-width:900px){.stats{width:100%;margin-left:0}}
</style></head><body>

<div id="load"><div>
  <div class="big"><span class="dr" style="color:#f2ff00">DR.</span><span style="color:#00ff6a">Hery</span> <span style="color:#ffd000;font-style:italic">"Potter"</span> <span style="color:#00c853">Leads</span></div>
  <div id="lmsg">decriptando base</div>
  <div class="bar"><i></i></div>
</div></div>

<header>
  <div class="brand">
    <h1><span class="glitch" data-txt='DR.Hery "Potter" Leads'><span class="dr">DR.</span><span class="hy">Hery</span> <span class="pt">"Potter"</span> <span class="ld">Leads</span></span></h1>
    <div class="sub">// DDD <b>17</b> · SÃO JOSÉ DO RIO PRETO E REGIÃO · ACESSO LIBERADO</div>
  </div>
  <div class="stats" id="stats"></div>
  <button class="btn" id="tema" title="Alternar tema">◐</button>
  <button class="btn p" id="exp">[ EXPORTAR CSV ]</button>
</header>

<div id="abas">
  <button class="aba on" data-aba="tel">▸ TELEFONES</button>
  <button class="aba" data-aba="email">▸ E-MAILS</button>
  <button class="btn p" id="disparador" hidden title="CSV pronto para importar no Disparador de E-mail">[ BAIXAR P/ DISPARADOR ]</button>
  <button class="btn" id="copiar" hidden>[ COPIAR E-MAILS ]</button>
</div>

<div id="filtros">
  <input id="q" placeholder="> buscar nome, cnpj, telefone, bairro, e-mail…" autocomplete="off">
  <select id="fcid"><option value="">todas as cidades</option></select>
  <select id="fcnae"><option value="">todos os segmentos</option></select>
  <select id="ftipo"><option value="">fixo + móvel</option><option value="1">só móvel</option><option value="0">só fixo</option></select>
  <select id="fsit"><option value="">todas as situações</option></select>
  <select id="fporte"><option value="">todos os portes</option></select>
  <label class="chk" title="Oculta empresas de fora que cadastraram um telefone 17"><input type="checkbox" id="fregiao" checked>só região 17</label>
  <label class="chk"><input type="checkbox" id="fmei">só MEI</label>
  <label class="chk"><input type="checkbox" id="femail">com e-mail</label>
  <button class="btn" id="limpar">[ LIMPAR ]</button>
</div>

<div id="wrap">
  <table>
    <colgroup id="cg"></colgroup>
    <thead id="th"><tr></tr></thead>
    <tbody id="tb"></tbody>
  </table>
  <div id="vazio" hidden>▓ nenhum alvo com esses filtros ▓</div>
</div>
<div id="okcopy"></div>

<script id="dados" type="application/gzip-base64">__DADOS__</script>
<script>
"use strict";
const $=s=>document.querySelector(s);
const LS_ST="leads17_status", LS_TEMA="leads17_tema", LS_ABA="leads17_aba";
const SEM_NOME="NÃO DETECTADO";
let D=null, IDX=[], VIEW=[], sortCol=-1, sortDir=1, aba="tel";

/* Cada aba e so um conjunto de colunas sobre os mesmos dados.
   's' e o indice do campo na linha, usado tambem para ordenar. */
const ABAS={
  tel:{ min:1140, cols:[
    {w:"150px",t:"Telefone",s:0},{w:"58px",t:"Tipo",s:1},{w:null,t:"Nome",s:2},
    {w:"164px",t:"CNPJ",s:3},{w:"152px",t:"Cidade",s:4},{w:"188px",t:"Segmento",s:5},
    {w:"82px",t:"Situação",s:6},{w:"98px",t:"Ações"}]},
  email:{ min:960, cols:[
    {w:null,t:"Nome",s:2},{w:"300px",t:"E-mail",s:10},{w:"152px",t:"Cidade",s:4},
    {w:"188px",t:"Segmento",s:5},{w:"82px",t:"Situação",s:6},{w:"76px",t:"Ações"}]}
};

/* localStorage falha em origem opaca (file:// restrito, modo privado, sandbox).
   Sem este wrapper a excecao deixa ST na TDZ e derruba a pagina inteira. */
const mem={}; let persiste=true;
const store={
  get(k){ try{ return localStorage.getItem(k); }catch(e){ persiste=false; return k in mem?mem[k]:null; } },
  set(k,v){ try{ localStorage.setItem(k,v); }catch(e){ persiste=false; mem[k]=v; } }
};
let ST={}; try{ ST=JSON.parse(store.get(LS_ST)||"{}")||{}; }catch(e){ ST={}; }

/* ---------- tema ---------- */
const temaSalvo=store.get(LS_TEMA);
if(temaSalvo) document.documentElement.dataset.t=temaSalvo;
$("#tema").onclick=()=>{
  const n=document.documentElement.dataset.t==="light"?"dark":"light";
  document.documentElement.dataset.t=n; store.set(LS_TEMA,n);
};

/* ---------- carga: base64 -> gzip -> json ---------- */
async function carregar(){
  const b64=$("#dados").textContent.trim();
  const bin=Uint8Array.from(atob(b64),c=>c.charCodeAt(0));
  const ds=new DecompressionStream("gzip");
  const buf=await new Response(new Blob([bin]).stream().pipeThrough(ds)).arrayBuffer();
  D=JSON.parse(new TextDecoder().decode(buf));
  IDX=D.rows.map((_,i)=>i);
  aba=abaInicial();
  document.querySelectorAll(".aba").forEach(b=>b.classList.toggle("on",b.dataset.aba===aba));
  $("#copiar").hidden = $("#disparador").hidden = aba!=="email";
  montarFiltros(); montarCabecalho(); aplicar();
  $("#load").remove();
}

function montarCabecalho(){
  const A=ABAS[aba];
  $("#cg").innerHTML=A.cols.map(c=>`<col${c.w?` style="width:${c.w}"`:""}>`).join("");
  $("#th").innerHTML="<tr>"+A.cols.map(c=>
    c.s===undefined?`<th>${c.t}</th>`:`<th data-s="${c.s}">${c.t}</th>`).join("")+"</tr>";
  document.querySelector("table").style.minWidth=A.min+"px";
  $("#th").querySelectorAll("th[data-s]").forEach(th=>th.onclick=()=>{
    const c=+th.dataset.s;
    sortDir = sortCol===c ? -sortDir : 1; sortCol=c;
    $("#th").querySelectorAll("th").forEach(x=>{const a=x.querySelector(".ar");if(a)a.remove()});
    th.insertAdjacentHTML("beforeend",`<span class="ar">${sortDir>0?"▲":"▼"}</span>`);
    aplicar();
  });
}

function abaInicial(){
  const h=location.hash.replace("#","");
  if(h==="email"||h==="tel") return h;
  return store.get(LS_ABA)==="email" ? "email" : "tel";
}

function trocarAba(nova){
  if(nova===aba)return;
  aba=nova; sortCol=-1;
  store.set(LS_ABA,aba);
  history.replaceState(null,"","#"+aba);
  document.querySelectorAll(".aba").forEach(b=>b.classList.toggle("on",b.dataset.aba===aba));
  $("#copiar").hidden = $("#disparador").hidden = aba!=="email";
  montarCabecalho(); aplicar();
}

function montarFiltros(){
  const add=(sel,arr)=>{const s=$(sel);arr.forEach((v,i)=>{if(!v)return;
    const o=document.createElement("option");o.value=i;o.textContent=v;s.appendChild(o)})};
  const cnt={}; D.rows.forEach(r=>cnt[r[4]]=(cnt[r[4]]||0)+1);
  const cs=$("#fcid");
  Object.keys(cnt).sort((a,b)=>cnt[b]-cnt[a]).forEach(i=>{
    if(!D.dic.cidade[i])return;
    const o=document.createElement("option");o.value=i;
    o.textContent=`${D.dic.cidade[i]} (${cnt[i].toLocaleString("pt-BR")})`;cs.appendChild(o)});
  add("#fcnae",D.dic.cnae); add("#fsit",D.dic.situacao); add("#fporte",D.dic.porte);
  const iA=D.dic.situacao.indexOf("ATIVA"); if(iA>=0) $("#fsit").value=iA;
}

/* ---------- filtro ---------- */
function aplicar(){
  const q=$("#q").value.trim().toLowerCase();
  const cid=$("#fcid").value, cnae=$("#fcnae").value, tipo=$("#ftipo").value;
  const sit=$("#fsit").value, porte=$("#fporte").value;
  const mei=$("#fmei").checked, email=$("#femail").checked;
  const reg=$("#fregiao").checked;
  const qs=q?q.split(/\s+/):null;

  VIEW=IDX.filter(i=>{
    const r=D.rows[i];
    if(cid!==""&&r[4]!=cid)return false;
    if(cnae!==""&&r[5]!=cnae)return false;
    if(tipo!==""&&r[1]!=tipo)return false;
    if(sit!==""&&r[6]!=sit)return false;
    if(porte!==""&&r[7]!=porte)return false;
    if(reg&&!(r[8]&4))return false;
    if(mei&&!(r[8]&1))return false;
    if(email&&!r[10])return false;
    if(qs){
      const h=(r[0]+" "+r[2]+" "+r[3]+" "+r[10]+" "+D.dic.bairro[r[9]]+" "+D.dic.cidade[r[4]]).toLowerCase();
      for(const t of qs) if(!h.includes(t)) return false;
    }
    return true;
  });
  if(aba==="email"){
    // a mesma empresa aparece uma vez por telefone; a lista de e-mail e por endereco
    const vistos=new Set();
    VIEW=VIEW.filter(i=>{
      const em=D.rows[i][10];
      if(!em||vistos.has(em))return false;
      vistos.add(em); return true;
    });
  }
  if(sortCol>=0){
    const c=sortCol;
    VIEW.sort((a,b)=>{
      let x=D.rows[a][c],y=D.rows[b][c];
      if(c===4){x=D.dic.cidade[x];y=D.dic.cidade[y]}
      if(c===5){x=D.dic.cnae[x];y=D.dic.cnae[y]}
      if(c===6){x=D.dic.situacao[x];y=D.dic.situacao[y]}
      return (x>y?1:x<y?-1:0)*sortDir;
    });
  }
  stats(); render(true);
}

function stats(){
  let mov=0,fix=0,mei=0,em=0,cid=new Set();
  VIEW.forEach(i=>{const r=D.rows[i];r[1]?mov++:fix++;if(r[8]&1)mei++;if(r[10])em++;cid.add(r[4])});
  const n=v=>v.toLocaleString("pt-BR");
  $("#stats").innerHTML = aba==="email"
    ? `<div class="stat y">E-MAILS ÚNICOS<b>${n(VIEW.length)}</b></div>`+
      `<div class="stat">MEI<b>${n(mei)}</b></div>`+
      `<div class="stat">CIDADES<b>${n(cid.size)}</b></div>`
    : `<div class="stat">ALVOS<b>${n(VIEW.length)}</b></div>`+
      `<div class="stat y">MÓVEL<b>${n(mov)}</b></div>`+
      `<div class="stat">FIXO<b>${n(fix)}</b></div>`+
      `<div class="stat y">MEI<b>${n(mei)}</b></div>`+
      `<div class="stat">E-MAIL<b>${n(em)}</b></div>`;
  $("#vazio").hidden=VIEW.length>0;
}

/* ---------- virtualizacao ---------- */
const LINHA=27, BUF=12;
function render(reset){
  const wrap=$("#wrap"), tb=$("#tb");
  if(reset) wrap.scrollTop=0;
  const vis=Math.ceil(wrap.clientHeight/LINHA)+BUF*2;
  const ini=Math.max(0,Math.floor(wrap.scrollTop/LINHA)-BUF);
  const fim=Math.min(VIEW.length,ini+vis);
  const vazio=ABAS[aba].cols.length;
  let h="";
  if(ini>0) h+=`<tr style="height:${ini*LINHA}px"><td colspan="${vazio}"></td></tr>`;
  for(let k=ini;k<fim;k++){
    const r=D.rows[VIEW[k]];
    const tel=r[0], st=ST[tel]||"";
    const cls=st==="ok"?"done":st==="x"?"drop":"";
    const sit=D.dic.situacao[r[6]];
    const nm=r[2]===SEM_NOME
      ? `<span class="nada">${SEM_NOME}</span>`
      : esc(r[2])+((r[8]&1)?' <span class="tag t-mei">MEI</span>':'');
    const marcar=`<button class="ic" data-a="ok" data-t="${tel}" title="Marcar contatado">✓</button>`+
                 `<button class="ic x" data-a="x" data-t="${tel}" title="Descartar / opt-out">✖</button>`;
    h+=`<tr class="${cls}" style="height:${LINHA}px">`;
    if(aba==="email"){
      h+=`<td title="${esc(r[2])}">${nm}</td>`+
         `<td class="mail" title="${esc(r[10])}">${esc(r[10])}</td>`+
         `<td>${esc(D.dic.cidade[r[4]])}</td>`+
         `<td title="${esc(D.dic.cnae[r[5]])}">${esc(D.dic.cnae[r[5]])}</td>`+
         `<td class="s-${sit}">${sit}</td>`+
         `<td><div class="acts"><a class="ic" href="mailto:${esc(r[10])}" title="Escrever">✉</a>${marcar}</div></td>`;
    }else{
      const fmt=tel.length===11
        ? `(${tel.slice(0,2)}) ${tel.slice(2,7)}-${tel.slice(7)}`
        : `(${tel.slice(0,2)}) ${tel.slice(2,6)}-${tel.slice(6)}`;
      h+=`<td class="tel">${fmt}</td>`+
         `<td><span class="tag ${r[1]?'t-mov':'t-fix'}">${r[1]?'MÓVEL':'FIXO'}</span></td>`+
         `<td title="${esc(r[2])}">${nm}</td>`+
         `<td class="cnpj">${cnpjF(r[3])}</td>`+
         `<td>${esc(D.dic.cidade[r[4]])}</td>`+
         `<td title="${esc(D.dic.cnae[r[5]])}">${esc(D.dic.cnae[r[5]])}</td>`+
         `<td class="s-${sit}">${sit}</td>`+
         `<td><div class="acts">`+
           `<a class="ic" href="tel:+55${tel}" title="Ligar">✆</a>`+
           `<a class="ic" href="https://wa.me/55${tel}" target="_blank" rel="noopener" title="WhatsApp">✉</a>`+
           marcar+`</div></td>`;
    }
    h+=`</tr>`;
  }
  if(fim<VIEW.length) h+=`<tr style="height:${(VIEW.length-fim)*LINHA}px"><td colspan="${vazio}"></td></tr>`;
  tb.innerHTML=h;
}
const esc=s=>String(s||"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const cnpjF=c=>c&&c.length===14?`${c.slice(0,2)}.${c.slice(2,5)}.${c.slice(5,8)}/${c.slice(8,12)}-${c.slice(12)}`:c;

/* ---------- eventos ---------- */
let raf=null;
$("#wrap").addEventListener("scroll",()=>{if(raf)return;raf=requestAnimationFrame(()=>{raf=null;render(false)})});
$("#tb").addEventListener("click",e=>{
  const b=e.target.closest("button[data-a]"); if(!b)return;
  const t=b.dataset.t, a=b.dataset.a;
  if(ST[t]===a) delete ST[t]; else ST[t]=a;
  store.set(LS_ST,JSON.stringify(ST));
  render(false); stats();
});
document.querySelectorAll(".aba").forEach(b=>b.onclick=()=>trocarAba(b.dataset.aba));
let deb=null;
["input","change"].forEach(ev=>$("#filtros").addEventListener(ev,e=>{
  clearTimeout(deb); deb=setTimeout(aplicar, e.target.id==="q"?180:0);
}));
$("#limpar").onclick=()=>{
  ["q","fcid","fcnae","ftipo","fsit","fporte"].forEach(i=>$("#"+i).value="");
  ["fmei","femail"].forEach(i=>$("#"+i).checked=false);
  $("#fregiao").checked=true;
  sortCol=-1; aplicar();
};
window.addEventListener("resize",()=>render(false));

/* ---------- export ---------- */
$("#exp").onclick=()=>{
  let cab,linha;
  if(aba==="email"){
    cab=["nome","email","cidade","bairro","segmento","cnae","situacao","porte","mei","cnpj","status"];
    linha=r=>[r[2],r[10],D.dic.cidade[r[4]],D.dic.bairro[r[9]],D.dic.cnae[r[5]],r[14],
              D.dic.situacao[r[6]],D.dic.porte[r[7]],(r[8]&1)?"SIM":"NAO",r[3],est(r[0])];
  }else{
    cab=["telefone","tipo","nome","cnpj","cidade","bairro","regiao_ddd17","segmento","cnae",
         "situacao","porte","mei","email","logradouro","cep","abertura","status","fonte"];
    linha=r=>["55"+r[0],r[1]?"MOVEL":"FIXO",r[2],r[3],D.dic.cidade[r[4]],D.dic.bairro[r[9]],
              (r[8]&4)?"SIM":"NAO",D.dic.cnae[r[5]],r[14],D.dic.situacao[r[6]],D.dic.porte[r[7]],
              (r[8]&1)?"SIM":"NAO",r[10],r[11],r[12],r[13],est(r[0]),D.meta.fonte];
  }
  const l=[cab.join(";")];
  VIEW.forEach(i=>l.push(linha(D.rows[i]).map(v=>`"${String(v||"").replace(/"/g,'""')}"`).join(";")));
  baixar(l.join("\r\n"), `drhery_${aba==="email"?"emails":"leads"}_ddd17_${hoje()}.csv`);
};
const est=t=>ST[t]==="ok"?"CONTATADO":ST[t]==="x"?"DESCARTADO":"";
const hoje=()=>new Date().toISOString().slice(0,10);
function baixar(txt,nome,mime,bom){
  // BOM ajuda o Excel a ler acento em .csv, mas corrompe o primeiro registro
  // de um .txt que vai ser lido por outro programa.
  const corpo = (bom===false ? txt : "\ufeff"+txt);
  const a=document.createElement("a");
  a.href=URL.createObjectURL(new Blob([corpo],{type:mime||"text/csv;charset=utf-8"}));
  a.download=nome; a.click(); setTimeout(()=>URL.revokeObjectURL(a.href),1000);
}

/* ---------- exportar para o Disparador de E-mail ----------
   Formato ditado pelo parser em ~/Área de trabalho/Email sender/server.py:
   - "email" e "nome" precisam desses nomes exatos (EMAIL_KEYS / NAME_KEYS)
   - toda coluna extra vira variável {{coluna}} no corpo da mensagem
   - a importação recusa acima de MAX_IMPORT_ROWS (200.000) por arquivo      */
const LIMITE_DISPARADOR=50000;
const EMAIL_OK=/^[^@\s,;<>]+@[^@\s,;<>]+\.[A-Za-z]{2,}$/;  // igual ao render.py

$("#disparador").onclick=()=>{
  const linhas=[];
  let invalidos=0;
  VIEW.forEach(i=>{
    const r=D.rows[i];
    const email=(r[10]||"").trim().toLowerCase();
    if(!EMAIL_OK.test(email)){ invalidos++; return; }
    // "NÃO DETECTADO" no lugar do nome viraria "Olá NÃO DETECTADO" no disparo;
    // em branco, o fallback {{nome|amigo}} do Disparador assume.
    const nome=r[2]===SEM_NOME?"":r[2];
    linhas.push([email,nome,D.dic.cidade[r[4]],D.dic.cnae[r[5]]]);
  });
  if(!linhas.length) return aviso("nenhum e-mail válido no filtro atual");

  const cab="email,nome,cidade,segmento";
  const csv=v=>`"${String(v||"").replace(/"/g,'""')}"`;
  const blocos=Math.ceil(linhas.length/LIMITE_DISPARADOR);
  const dia=hoje();

  for(let b=0;b<blocos;b++){
    const fatia=linhas.slice(b*LIMITE_DISPARADOR,(b+1)*LIMITE_DISPARADOR);
    const txt=[cab].concat(fatia.map(l=>l.map(csv).join(","))).join("\r\n");
    const nome = blocos>1
      ? `drhery_disparador_${dia}_parte${b+1}de${blocos}.csv`
      : `drhery_disparador_${dia}.csv`;
    // downloads em sequência: o navegador ignora vários disparados no mesmo tick
    setTimeout(()=>baixar(txt,nome),b*300);
  }

  const n=v=>v.toLocaleString("pt-BR");
  aviso(`✓ ${n(linhas.length)} e-mails em ${blocos} arquivo${blocos>1?"s":""}`+
        (invalidos?` · ${n(invalidos)} inválidos descartados`:""));
};

/* ---------- copiar e-mails ---------- */
function aviso(t){const e=$("#okcopy");e.textContent=t;e.classList.add("on");
  setTimeout(()=>e.classList.remove("on"),1800)}
$("#copiar").onclick=async()=>{
  const lista=VIEW.map(i=>D.rows[i][10]).filter(Boolean).join("; ");
  if(!lista) return aviso("nada para copiar");
  try{
    await navigator.clipboard.writeText(lista);
  }catch(e){
    // clipboard API exige contexto seguro; file:// cai aqui
    const ta=document.createElement("textarea");
    ta.value=lista; ta.style.position="fixed"; ta.style.opacity="0";
    document.body.appendChild(ta); ta.select();
    const ok=document.execCommand("copy"); ta.remove();
    if(!ok){ baixar(lista,`drhery_emails_${hoje()}.txt`,"text/plain;charset=utf-8",false); return aviso("copia bloqueada — baixei em .txt"); }
  }
  aviso(`✓ ${VIEW.length.toLocaleString("pt-BR")} e-mails copiados`);
};

/* Quem recebe o arquivo pode abrir num navegador antigo ou numa máquina sem
   memória sobrando. Nesses casos uma mensagem tecnica nao ajuda: diz o que fazer. */
function falha(titulo,texto){
  const el=$("#lmsg");
  if(!el)return;
  el.innerHTML=`<b style="color:var(--bad);font-size:13px">${titulo}</b>`+
    `<div style="color:var(--tx2);letter-spacing:0;text-transform:none;margin-top:9px;`+
    `max-width:420px;line-height:1.6;font-size:11.5px">${texto}</div>`;
  const b=document.querySelector(".bar"); if(b) b.style.display="none";
}

if(typeof DecompressionStream==="undefined"){
  falha("NAVEGADOR SEM SUPORTE",
    "Esta página precisa de um navegador mais recente.<br><br>"+
    "Abra o arquivo no <b>Google Chrome</b> ou <b>Microsoft Edge</b> atualizado "+
    "(versão de 2020 ou posterior). No Firefox, é necessária a versão 113 ou superior.<br><br>"+
    "Internet Explorer não funciona.");
}else{
  carregar().catch(e=>{
    const semMemoria = e instanceof RangeError ||
      /allocation|out of memory|Array buffer|invalid string length/i.test(e.message||"");
    if(semMemoria){
      falha("MEMÓRIA INSUFICIENTE",
        "A base é grande e o navegador não conseguiu carregá-la nesta máquina.<br><br>"+
        "Feche as outras abas e tente de novo. Se persistir, esta máquina precisa "+
        "de uma versão reduzida do arquivo.");
    }else{
      falha("NÃO FOI POSSÍVEL ABRIR",
        "O arquivo pode ter sido baixado pela metade ou alterado no envio.<br><br>"+
        "Baixe novamente e abra direto do computador (não de dentro do e-mail "+
        "ou do Google Drive).<br><br><span style='opacity:.6'>Detalhe técnico: "+
        `${(e.message||e).toString().slice(0,120)}</span>`);
    }
  });
}
</script></body></html>
"""

if __name__ == "__main__":
    main()
