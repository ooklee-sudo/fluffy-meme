# Wayback verification: access failed (2026-11-04)

The Wayback Machine (web.archive.org) could not be reached from this session, so
no archived snapshots were checked. No verification results were produced, and
nothing in `llm_api_lifecycle/data/` was changed. The datasets remain verified
only against live vendor pages.

## Access check

Command (Step 0):

    curl -sS -o /dev/null -w "%{http_code}" "https://web.archive.org/cdx/search/cdx?url=ai.google.dev/gemini-api/docs/deprecations&limit=3"

Result: 9 attempts between 2026-11-04T08:49:59Z and 08:53:10Z, spaced 5–60 s apart.
Every attempt failed the same way:

    curl: (35) Recv failure: Connection reset by peer
    000

Verbose output (`curl -v --http1.1`) shows the proxy accepts the CONNECT
(`HTTP/1.1 200 Connection Established`), curl sends the TLS Client Hello, and the
connection is reset about 10 s later, before any TLS reply:

    * CONNECT tunnel established, response 200
    * TLSv1.3 (OUT), TLS handshake, Client hello (1):
    * Recv failure: Connection reset by peer
    * OpenSSL SSL_connect: Connection reset by peer in connection to web.archive.org:443

## Agent proxy status (`curl -sS "$HTTPS_PROXY/__agentproxy/status"`)

`recentRelayFailures` entries for archive hosts (all `web.archive.org:443`):

| ts (UTC) | kind | detail |
|---|---|---|
| 2026-11-04T08:49:59.168Z | ws_closed_mid_exchange | tunnel closed (code 1006) after 3s; 517 B sent, 39 B received, client reading, 0 B still queued in the relay |
| 2026-11-04T08:50:14.481Z | ws_closed_mid_exchange | tunnel closed (code 1006) after 10s; 517 B sent, 39 B received, client reading, 0 B still queued in the relay |
| 2026-11-04T08:50:29.760Z | ws_closed_mid_exchange | tunnel closed (code 1006) after 10s; 517 B sent, 39 B received, client reading, 0 B still queued in the relay |
| 2026-11-04T08:50:52.642Z | ws_closed_mid_exchange | tunnel closed (code 1006) after 10s; 517 B sent, 39 B received, client reading, 0 B still queued in the relay |
| 2026-11-04T08:51:22.926Z | ws_closed_mid_exchange | tunnel closed (code 1006) after 10s; 517 B sent, 39 B received, client reading, 0 B still queued in the relay |
| 2026-11-04T08:51:53.239Z | ws_closed_mid_exchange | tunnel closed (code 1006) after 10s; 517 B sent, 39 B received, client reading, 0 B still queued in the relay |
| 2026-11-04T08:52:43.797Z | ws_closed_mid_exchange | tunnel closed (code 1006) after 10s; 517 B sent, 39 B received, client reading, 0 B still queued in the relay |
| 2026-11-04T08:53:10.242Z | ws_closed_mid_exchange | tunnel closed (code 1006) after 10s; 517 B sent, 39 B received, client reading, 0 B still queued in the relay |

The proxy's CONNECT succeeds, but the upstream tunnel to web.archive.org closes
(WebSocket code 1006, abnormal closure) after 39 bytes. The proxy README says
that pattern means the relay or egress tunnel dropped the connection, not that
the remote service refused the request.

## Other hosts, for context

- `https://archive.org/` → HTTP 200 (the main archive.org host is reachable).
- `https://archive.org/wayback/available?url=ai.google.dev/gemini-api/docs/deprecations&timestamp=20261002`
  → HTTP 200, but the body was `"archived_snapshots": {}`. This is **not**
  evidence that no snapshots exist: this endpoint is backed by the same Wayback
  service that cannot be reached, and it returns no snapshots for pages that are
  known to be heavily archived. It was not used for verification.
- `https://ai.google.dev/` → `CONNECT tunnel failed, response 403` (blocked by
  the environment's network policy; live vendor pages also cannot be fetched from here).

## Effect on the manuscript

None of the claims listed for verification (Gemini stable median notice 147 days
(n=12), previews 28 days, Anthropic 63 days, OpenAI 182 days; the October 2026
no-notice redirects of gemini-3.5-flash and gemini-3.7-flash; Claude Sonnet 4
notice 62 days vs 183 days on Bedrock; Gemini 3.6/3.7/3.8 Flash introductory
pricing and the 1 Jan 2027 price rise; 2.0 Flash / Flash-Lite list prices) has
been checked against archived pages. They still rest on the live pages retrieved
on 2026-11-04 and on third-party sources.

## To retry

Run the task again from a session where web.archive.org is reachable (the
outcome of Step 0 above should be `200`). If the failure persists across
sessions, the environment's network settings or egress for web.archive.org
should be checked.
