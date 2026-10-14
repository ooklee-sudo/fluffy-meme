#!/bin/bash
# usage: fetch_duka.sh SYMBOL OUTDIR START END   (dates YYYY-MM-DD, inclusive). Month is zero-indexed in the Dukascopy path.
SYM=$1; OUT=$2; S=$3; E=$4; mkdir -p "$OUT"
d="$S"; list=()
while [ "$(date -d "$d" +%s)" -le "$(date -d "$E" +%s)" ]; do
  y=$(date -d "$d" +%Y); m=$(printf "%02d" $(( 10#$(date -d "$d" +%m) - 1 ))); dd=$(date -d "$d" +%d)
  for h in $(seq -w 0 23); do echo "$y $m $dd $h $(date -d "$d" +%Y%m%d)"; done
  d=$(date -I -d "$d + 1 day")
done > "$OUT/_todo.txt"
fetch(){ y=$1; m=$2; dd=$3; h=$4; tag=$5; f="$2/../$tag"; }
export SYM OUT
cat "$OUT/_todo.txt" | xargs -P 8 -L 1 bash -c '
y=$0; m=$1; dd=$2; h=$3; tag=$4; f="$OUT/${tag}_${h}.bi5"
[ -s "$f" ] || [ -e "$f.empty" ] && exit 0
for i in 1 2 3 4 5 6; do
  code=$(curl -sS -m 40 -A Mozilla/5.0 -o "$f.tmp" -w "%{http_code}" "https://datafeed.dukascopy.com/datafeed/$SYM/$y/$m/$dd/${h}h_ticks.bi5" 2>/dev/null)
  if [ "$code" = "200" ]; then if [ -s "$f.tmp" ]; then mv "$f.tmp" "$f"; else rm -f "$f.tmp"; touch "$f.empty"; fi; exit 0; fi
  if [ "$code" = "404" ]; then rm -f "$f.tmp"; touch "$f.empty"; exit 0; fi
  sleep 2
done
rm -f "$f.tmp"; echo "FAIL $f" >> "$OUT/_fail.txt"
'
echo done > "$OUT/_done"
