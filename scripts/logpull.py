#!/usr/bin/env python3
"""
logpull.py - Bulk Cloud Logging reader with live progress, ETA, quota-aware
pacing, 429 backoff and resume. Output matches `gcloud logging read --format=json`
(a JSON array of LogEntry objects).

Usage:
  python3 logpull.py --project YOUR_PROJECT_ID \
    --filter 'resource.type="http_load_balancer" AND status>=400' \
    --days 30 --limit 200000 --out gcp_logs.json

If interrupted (Ctrl-C, network drop, Cloud Shell timeout), re-run the same
command with --resume and it continues from the last saved page without loss
or duplicates.
"""
import argparse
from collections import deque
from datetime import datetime, timedelta, timezone
import json
import os
import shutil
import sys
import time

API = "https://logging.googleapis.com/v2/entries:list"
SCOPE = "https://www.googleapis.com/auth/cloud-platform.read-only"
MAX_PAGE = 1000  # API hard cap for entries.list pageSize


# ----------------------------------------------------------------- helpers
def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def parse_ts(s):
    s = s.rstrip("Z")
    base, _, frac = s.partition(".")
    dt = datetime.strptime(base, "%Y-%m-%dT%H:%M:%S")
    if frac:
        dt = dt.replace(microsecond=int((frac + "000000")[:6]))
    return dt.replace(tzinfo=timezone.utc)


def fmt_dur(sec):
    if sec is None:
        return "--:--"
    sec = int(sec)
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def save_state(path, st):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(st, f)
    os.replace(tmp, path)


def get_session():
    try:
        import google.auth
        from google.auth.transport.requests import AuthorizedSession
    except ImportError:
        sys.stderr.write("ERROR: Missing dependency 'google-auth'. Run: pip install google-auth requests\n")
        sys.exit(1)

    try:
        creds, _ = google.auth.default(scopes=[SCOPE])
        return AuthorizedSession(creds)
    except Exception as e:
        sys.stderr.write(f"Authentication Error: {e}\n")
        sys.stderr.write("Fix: run 'gcloud auth application-default login' or run inside Google Cloud Shell.\n")
        sys.exit(2)


# ---------------------------------------------------------------- progress
class Progress:
    def __init__(self, start_dt, end_dt, limit, n0, cur_ts):
        self.start_dt, self.end_dt = start_dt, end_dt
        self.span = max((start_dt - end_dt).total_seconds(), 1.0)
        self.limit = limit
        self.n = self.n0 = n0
        self.cur_ts = cur_ts
        self.pages = 0
        self.reqs = 0
        self.throttled = 0
        self.done = False
        self.t0 = time.monotonic()
        self.samples = deque(maxlen=12)
        self.req_times = deque()
        self.tty = sys.stderr.isatty()

    def fraction(self):
        if self.done:
            return 1.0
        time_frac = (self.start_dt - self.cur_ts).total_seconds() / self.span
        limit_frac = self.n / self.limit if self.limit else 0.0
        return min(1.0, max(time_frac, limit_frac, 0.0))

    def mark(self):
        self.samples.append((time.monotonic(), self.fraction()))

    def eta(self):
        if self.done:
            return 0
        if len(self.samples) < 3:
            return None
        (t1, p1), (t2, p2) = self.samples[0], self.samples[-1]
        if p2 <= p1 or t2 <= t1:
            return None
        return (1.0 - p2) / ((p2 - p1) / (t2 - t1))

    def render(self, note="", log=False):
        now = time.monotonic()
        el = now - self.t0
        while self.req_times and now - self.req_times[0] > 60:
            self.req_times.popleft()
        p = self.fraction()
        w = 28
        fill = int(w * p)
        bar = "#" * fill + "-" * (w - fill)
        rate = (self.n - self.n0) / el if el > 0 else 0
        line = (
            f"[{bar}] {p * 100:5.1f}% | {self.n:,} entries | pg {self.pages} | "
            f"{rate:,.0f}/s | {len(self.req_times)}/60 req/min | "
            f"at {self.cur_ts:%m-%d %H:%M}Z | {fmt_dur(el)} elapsed | "
            f"ETA {fmt_dur(self.eta())}"
        )
        if note:
            line += f" | {note}"
        if self.tty:
            cols = shutil.get_terminal_size((120, 20)).columns - 1
            sys.stderr.write("\r" + line[:cols].ljust(cols))
            sys.stderr.flush()
        elif log:
            print(line, file=sys.stderr, flush=True)


class Pacer:
    """Keeps request starts >= 60/rpm seconds apart (stays under the quota)."""

    def __init__(self, rpm):
        self.interval = 60.0 / rpm
        self.last = 0.0

    def wait(self, prog):
        while True:
            remaining = self.last + self.interval - time.monotonic()
            if remaining <= 0:
                break
            prog.render(f"pacing {remaining:.1f}s")
            time.sleep(min(0.25, remaining))
        self.last = time.monotonic()


def countdown(prog, delay, label):
    end = time.monotonic() + delay
    while True:
        remaining = end - time.monotonic()
        if remaining <= 0:
            return
        prog.render(f"{label} {remaining:.0f}s")
        time.sleep(min(0.25, remaining))


# ------------------------------------------------------------------- fetch
def fetch(session, body, prog, pacer):
    attempt = 0
    while True:
        pacer.wait(prog)
        prog.req_times.append(time.monotonic())
        prog.reqs += 1
        prog.render("fetching...")
        try:
            r = session.post(API, json=body, timeout=120)
            status, text, retry_after = r.status_code, r.text, r.headers.get("Retry-After")
        except Exception as e:  # network error
            r, status, text, retry_after = None, 599, str(e), None

        if status == 200:
            return r.json()

        if status in (429, 500, 502, 503, 504, 599) and attempt < 8:
            if status == 429:
                prog.throttled += 1
            try:
                delay = float(retry_after)
            except (TypeError, ValueError):
                base = 15 if status == 429 else 2
                delay = min(60, base * 2 ** min(attempt, 3))
            attempt += 1
            countdown(prog, delay, f"HTTP {status}, retry {attempt}/8 in")
            continue

        sys.stderr.write("\n")
        sys.exit(f"API error {status}: {text[:600]}")


# ---------------------------------------------------------------- finalize
def finalize(jsonl_path, out_path):
    with open(jsonl_path) as src, open(out_path, "w") as dst:
        dst.write("[")
        first = True
        for line in src:
            line = line.strip()
            if not line:
                continue
            dst.write(line if first else ",\n" + line)
            first = False
        dst.write("]\n")


# -------------------------------------------------------------------- main
def parse_args():
    ap = argparse.ArgumentParser(
        description="Cloud Logging bulk reader with live progress, ETA, quota pacing, and resume capability."
    )
    ap.add_argument("--project", required=True, help="GCP Project ID to read logs from")
    ap.add_argument("--filter", required=True, help="Cloud Logging query filter expression")
    ap.add_argument("--days", type=float, default=30, help="Look-back window in days (default: 30)")
    ap.add_argument("--limit", type=int, default=210000, help="Max entries to fetch (default: 210000)")
    ap.add_argument("--out", required=True, help="Output JSON array file path (e.g., logs.json)")
    ap.add_argument(
        "--rpm", type=float, default=50,
        help="Max read requests/min. Quota is 60 req/min/project; keep headroom (default: 50)"
    )
    ap.add_argument("--page-size", type=int, default=MAX_PAGE, help=f"Entries per page (max: {MAX_PAGE})")
    ap.add_argument("--resume", action="store_true", help="Continue a previous interrupted run")
    return ap.parse_args()


def main():
    a = parse_args()
    if a.filter.count('"') % 2:
        sys.exit('Filter has an unbalanced double quote ("). Check the closing quote.')
    page_size = max(1, min(a.page_size, MAX_PAGE))

    part = a.out + ".jsonl.part"
    state_path = a.out + ".state.json"
    now = datetime.now(timezone.utc)
    st = {"project": a.project, "filter": a.filter, "start": iso(now),
          "end": iso(now - timedelta(days=a.days)), "last_ts": None, "ids": [], "count": 0}

    skip_ids = set()
    if a.resume and os.path.exists(state_path) and os.path.exists(part):
        st = json.load(open(state_path))
        if st["filter"] != a.filter or st["project"] != a.project:
            sys.exit("State file belongs to a different project/filter. Remove it or change --out.")
        skip_ids = set(st["ids"])
        print(f"Resuming from {st['last_ts']} with {st['count']:,} entries already saved.",
              file=sys.stderr)
    else:
        for p in (part, state_path):
            if os.path.exists(p):
                os.remove(p)

    start_dt, end_dt = parse_ts(st["start"]), parse_ts(st["end"])
    upper = st["last_ts"] or st["start"]
    body = {
        "resourceNames": [f"projects/{a.project}"],
        "filter": f'({a.filter}) AND timestamp>="{st["end"]}" AND timestamp<="{upper}"',
        "orderBy": "timestamp desc",
        "pageSize": page_size,
    }

    cur_ts = parse_ts(st["last_ts"]) if st["last_ts"] else start_dt
    prog = Progress(start_dt, end_dt, a.limit, st["count"], cur_ts)
    pacer = Pacer(a.rpm)
    session = get_session()

    print(f"Project: {a.project} | window: {st['end']} -> {st['start']} | "
          f"limit: {a.limit:,} | pace: {a.rpm:g} req/min | page: {page_size}", file=sys.stderr)

    try:
        with open(part, "a") as out:
            while True:
                data = fetch(session, body, prog, pacer)
                entries = data.get("entries", [])
                prog.pages += 1

                new = [e for e in entries
                       if not (skip_ids and e.get("insertId") in skip_ids
                               and e.get("timestamp") == st["last_ts"])]
                skip_ids = set()

                hit_limit = False
                room = a.limit - st["count"]
                if len(new) >= room:
                    new, hit_limit = new[:max(room, 0)], True

                for e in new:
                    out.write(json.dumps(e, separators=(",", ":")) + "\n")
                out.flush()
                os.fsync(out.fileno())

                if new:
                    last = new[-1]["timestamp"]
                    ids = {e["insertId"] for e in new if e["timestamp"] == last}
                    if last == st["last_ts"]:
                        ids |= set(st["ids"])
                    st.update(last_ts=last, ids=sorted(ids), count=st["count"] + len(new))
                    prog.cur_ts = parse_ts(last)
                    prog.n = st["count"]
                save_state(state_path, st)

                token = data.get("nextPageToken")
                if hit_limit or not token:
                    prog.done = True
                prog.mark()
                prog.render(log=True)
                if prog.done:
                    break
                body["pageToken"] = token
    except KeyboardInterrupt:
        sys.stderr.write("\n")
        sys.exit(f"Interrupted at {prog.n:,} entries. Progress saved. "
                 f"Re-run the same command with --resume.")

    sys.stderr.write("\nWriting final JSON array...\n")
    finalize(part, a.out)
    os.remove(part)
    os.remove(state_path)

    el = time.monotonic() - prog.t0
    size_mb = os.path.getsize(a.out) / 1_048_576
    print(f"Done: {st['count']:,} entries -> {a.out} ({size_mb:.1f} MB) | "
          f"{prog.reqs} requests, {prog.throttled} throttled (429) | {fmt_dur(el)}",
          file=sys.stderr)
    if st["count"] >= a.limit:
        print(f"WARNING: hit --limit ({a.limit:,}); older entries in the window were NOT fetched.",
              file=sys.stderr)


if __name__ == "__main__":
    main()
