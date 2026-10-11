#!/bin/bash
h=$1; o=/tmp/gha/out/$h.jsonl
[ -s "$o" ] && exit 0
for try in 1 2 3; do
  curl -sS -m 300 https://data.gharchive.org/$h.json.gz | gzip -dc | grep -E '"type":"(PullRequestEvent|PullRequestReviewEvent|PullRequestReviewCommentEvent)"' | python3 /tmp/gha/code/extract.py > $o.tmp && mv $o.tmp $o && exit 0
  sleep 3
done
echo "FAILED $h" >> /tmp/gha/failed.txt
