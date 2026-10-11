#!/bin/bash
# usage: hour2.sh <hour> <outdir>
h=$1; d=$2; o=$d/$h.jsonl
[ -s "$o" ] && exit 0
for try in 1 2 3; do
  curl -sS -m 300 https://data.gharchive.org/$h.json.gz | gzip -dc | grep -E '"type":"(PullRequestEvent|PullRequestReviewEvent|PullRequestReviewCommentEvent)"' | python3 /tmp/gha/code/extract_f.py > $o.tmp && mv $o.tmp $o && exit 0
  sleep 3
done
echo "FAILED $h" >> $d/failed.txt
