#!/bin/sh
# Slow, polite IDX collector for a rate-limited environment.
#
# Cloudflare on idx.co.id flags an IP after a short burst and keeps it flagged
# for several minutes. This wrapper therefore:
#   1. polls one cheap endpoint every 2 minutes until it stops returning the
#      "Just a moment..." challenge,
#   2. then collects the endpoints with a 75 s gap and NO retry loop, so a
#      single unlucky request cannot extend the block.
#
# Usage:  sh scripts/idx_slow_collect.sh

set -u

HOST="https://www.idx.co.id"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
PROBE="$HOST/primary/StockData/GetSecuritiesStock?start=0&length=1&language=id"

probe() {
  curl -s -o /tmp/idx_probe.out -w '%{http_code}' --max-time 25 -A "$UA" \
    -H 'Accept: application/json, text/plain, */*' \
    -H 'Accept-Language: id-ID,id;q=0.9' \
    -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' \
    -H 'Sec-Fetch-Site: same-origin' \
    -H "Referer: $HOST/id/market-data" "$PROBE"
}

echo "[$(date -u +%H:%M:%SZ)] waiting for Cloudflare to clear..."
i=0
while [ $i -lt 20 ]; do
  code=$(probe)
  if [ "$code" = "200" ]; then
    echo "[$(date -u +%H:%M:%SZ)] clear (HTTP 200) - starting collection"
    break
  fi
  i=$((i + 1))
  echo "[$(date -u +%H:%M:%SZ)] still blocked (HTTP $code), attempt $i/20, sleeping 120s"
  sleep 120
done

if [ "$code" != "200" ]; then
  echo "gave up waiting; run scripts/fetch_idx.py manually later" >&2
  exit 1
fi

# Give the just-used probe a moment, then collect slowly.
sleep 30
python3 scripts/fetch_idx.py --pace 75 --attempts 1
