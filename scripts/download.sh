#!/usr/bin/env bash
# Baixa os Dados Abertos CNPJ (Receita Federal) - competência 2026-08
set -u
TOKEN="gn672Ad4CF8N6TK"
BASE="https://arquivos.receitafederal.gov.br/public.php/webdav/Dados/Cadastros/CNPJ/2026-08"
DEST="$(cd "$(dirname "$0")/.." && pwd)/data/raw"
mkdir -p "$DEST"

get(){
  local f="$1" dst="$DEST/$1"
  # pula se já existe com tamanho igual ao remoto
  local remote local_sz
  remote=$(curl -sI -m 30 -u "$TOKEN:" "$BASE/$f" | grep -i '^content-length' | tr -d '\r' | awk '{print $2}')
  if [ -f "$dst" ]; then
    local_sz=$(stat -c%s "$dst")
    [ "$local_sz" = "$remote" ] && { echo "SKIP  $f (já completo)"; return 0; }
  fi
  curl -s --retry 5 --retry-delay 3 -C - -m 3600 -u "$TOKEN:" -o "$dst" "$BASE/$f" \
    && echo "OK    $f ($(du -h "$dst"|cut -f1))" || echo "FALHA $f"
}
export -f get; export TOKEN BASE DEST

FILES=""
for i in 0 1 2 3 4 5 6 7 8 9; do FILES="$FILES Estabelecimentos$i.zip Empresas$i.zip"; done
FILES="$FILES Simples.zip Municipios.zip Cnaes.zip"

printf '%s\n' $FILES | xargs -P 4 -I{} bash -c 'get "$@"' _ {}
echo "=== DOWNLOAD FINALIZADO ==="
du -sh "$DEST"
