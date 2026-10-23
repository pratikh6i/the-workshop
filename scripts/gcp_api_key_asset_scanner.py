#!/usr/bin/env python3
"""
GCP API Key Inventory via Cloud Asset Inventory
================================================
STRICTLY READ-ONLY scanner designed for enterprise environments with hundreds
or thousands of Google Cloud projects.

Instead of making N+1 API calls per project (which hits rate limits and takes hours),
this script queries Google Cloud Asset Inventory across whole scopes:
  - Organizations (organizations/ORGANIZATION_ID)
  - Folders (folders/FOLDER_ID)
  - Projects (projects/PROJECT_ID)

Features:
  - Uses paginated searchAllResources (up to 500 results per page)
  - Resolves project numbers to project IDs across org/folder scopes
  - Identifies unrestricted APIs and unrestricted client application types
  - Calculates key age and highlights keys needing rotation (>90 days by default)
  - Infers environment (Prod, Stage, Dev, QA, Test)
  - Exports to both CSV and auto-formatted Excel (.xlsx with filters and freeze panes)
  - Strictly READ-ONLY: uses Google OAuth read-only scope and GET requests only

Usage:
  # Across entire organization:
  python3 gcp_api_key_asset_scanner.py -s organizations/123456789012
  # Or with convenience flag:
  python3 gcp_api_key_asset_scanner.py --org-id 123456789012

  # Across specific folder(s):
  python3 gcp_api_key_asset_scanner.py --folder-id 987654321

  # Multiple scopes and filtered project list:
  python3 gcp_api_key_asset_scanner.py -s organizations/123 -f target_projects.txt

  # Custom rotation threshold and timezone:
  python3 gcp_api_key_asset_scanner.py --org-id 123456789012 --rotation-days 60 --tz UTC
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
import json
import os
import re
import sys
import threading
import time

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    sys.stderr.write("ERROR: 'requests' package is required. Install with: pip install requests\n")
    sys.exit(1)

try:
    import google.auth
    from google.auth.exceptions import DefaultCredentialsError, RefreshError, TransportError
    from google.auth.transport.requests import Request as GoogleAuthRequest
except ImportError:
    sys.stderr.write("ERROR: 'google-auth' package is required. Install with: pip install google-auth\n")
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    sys.stderr.write("ERROR: 'pandas' package is required. Install with: pip install pandas\n")
    sys.exit(1)

READ_ONLY_SCOPE = ["https://www.googleapis.com/auth/cloud-platform.read-only"]
SEARCH_URL = "https://cloudasset.googleapis.com/v1/{scope}:searchAllResources"
KEY_TYPE = "apikeys.googleapis.com/Key"
PROJECT_TYPE = "cloudresourcemanager.googleapis.com/Project"

_print_lock = threading.Lock()
_token_lock = threading.Lock()


def log(msg, level="INFO"):
    """Thread-safe logging with timestamps."""
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    icon = {"INFO": "[i]", "OK": "[+]", "WARN": "[!]", "ERR": "[x]", "NET": "[~]"}.get(level, "[?]")
    with _print_lock:
        print(f"{ts} {icon} {msg}", flush=True)


def get_token(creds, force=False):
    """Thread-safe OAuth2 access token refresh."""
    with _token_lock:
        if force or not creds.valid or not creds.token:
            creds.refresh(GoogleAuthRequest())
        return creds.token


def make_session(pool_size):
    """Create requests.Session with connection pooling and exponential backoff retries."""
    s = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
        raise_on_status=False
    )
    s.mount("https://", HTTPAdapter(pool_connections=pool_size, pool_maxsize=pool_size, max_retries=retry))
    return s


def parse_timezone(tz_name):
    """Parse configured timezone name, returning (timezone_obj, display_suffix)."""
    tz_clean = (tz_name or "").strip().upper()
    if tz_clean in ("IST", "ASIA/KOLKATA"):
        return timezone(timedelta(hours=5, minutes=30)), "IST"
    if tz_clean in ("UTC", "GMT", "Z"):
        return timezone.utc, "UTC"
    if tz_clean in ("EST", "US/EASTERN"):
        return timezone(timedelta(hours=-5)), "EST"
    if tz_clean in ("EDT",):
        return timezone(timedelta(hours=-4)), "EDT"
    if tz_clean in ("CST", "US/CENTRAL"):
        return timezone(timedelta(hours=-6)), "CST"
    if tz_clean in ("CDT",):
        return timezone(timedelta(hours=-5)), "CDT"
    if tz_clean in ("PST", "US/PACIFIC"):
        return timezone(timedelta(hours=-8)), "PST"
    if tz_clean in ("PDT",):
        return timezone(timedelta(hours=-7)), "PDT"
    # Default fallback to IST (+05:30)
    return timezone(timedelta(hours=5, minutes=30)), "IST"


def get_environment(project_id):
    """Infer environment classification from project ID naming conventions."""
    n = (project_id or "").lower()
    if "prod" in n or "prd" in n:
        return "Prod"
    if "stage" in n or "stg" in n or "uat" in n:
        return "Stage/UAT"
    if "qa" in n:
        return "QA"
    if "dev" in n or "sandbox" in n or "sbx" in n:
        return "Dev"
    if "test" in n or "tst" in n:
        return "Test"
    return "Unknown"


def parse_ts(ts, tz_info, tz_label):
    """Return (formatted display string in target timezone, age in days)."""
    if not ts:
        return "N/A", "N/A"
    try:
        t = ts.strip()
        if t.endswith("Z"):
            t = t[:-1]
            if "." in t:
                base, frac = t.split(".", 1)
                t = f"{base}.{frac[:6]}"
            dt = datetime.fromisoformat(t).replace(tzinfo=timezone.utc)
        else:
            dt = datetime.fromisoformat(t)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        display_str = dt.astimezone(tz_info).strftime(f"%d-%m-%Y %I:%M %p {tz_label}")
        age_days = (datetime.now(timezone.utc) - dt).days
        return display_str, age_days
    except Exception:
        return ts, "N/A"


# --------------------------------------------------------------------------- #
# Paginated Cloud Asset Search (GET requests only - strictly read-only)
# --------------------------------------------------------------------------- #
def search_scope(scope, asset_type, read_mask, creds, session, quota_project, label):
    """Yield all search results for one scope, page by page, with error handling."""
    url = SEARCH_URL.format(scope=scope)
    page, total, token_refreshed, page_token = 0, 0, False, None
    t0 = time.time()

    while True:
        page += 1
        params = {"assetTypes": asset_type, "readMask": read_mask, "pageSize": 500}
        if page_token:
            params["pageToken"] = page_token

        headers = {
            "Authorization": f"Bearer {get_token(creds)}",
            "Accept": "application/json"
        }
        if quota_project:
            headers["X-Goog-User-Project"] = quota_project

        try:
            resp = session.get(url, headers=headers, params=params, timeout=(5, 60))
        except requests.exceptions.Timeout:
            raise RuntimeError(f"{scope}: request timed out on page {page}")
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(f"{scope}: network connection error: {str(e)[:150]}")
        except (RefreshError, TransportError) as e:
            raise RuntimeError(f"{scope}: auth token refresh failed: {e}")

        if resp.status_code == 401 and not token_refreshed:
            token_refreshed = True
            log(f"401 on {scope}; refreshing token and retrying...", "WARN")
            get_token(creds, force=True)
            page -= 1
            continue

        if resp.status_code != 200:
            msg = ""
            try:
                msg = resp.json().get("error", {}).get("message", "")
            except ValueError:
                msg = resp.text[:200]
            hint = {
                403: "Requires 'cloudasset.assets.searchAllResources' (roles/cloudasset.viewer) on this scope, "
                     "and Cloud Asset API enabled on the quota project.",
                404: "Scope not found - verify format (organizations/ID, folders/ID, or projects/ID).",
                400: "Bad request - verify scope syntax and asset type.",
                429: "Quota exhausted - consider lowering --workers flag.",
            }.get(resp.status_code, "")
            raise RuntimeError(f"{scope}: HTTP {resp.status_code} {msg[:200]} {('| ' + hint) if hint else ''}")

        try:
            data = resp.json()
        except ValueError:
            raise RuntimeError(f"{scope}: response was not valid JSON")

        results = data.get("results", [])
        total += len(results)
        log(f"{label} {scope}: page {page} -> {len(results)} result(s) (running total {total})", "NET")
        for r in results:
            yield r

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    log(f"{label} {scope}: completed, {total} result(s) in {time.time() - t0:.1f}s", "OK")


def fetch_scope(scope, read_mask, creds, session, quota_project):
    """Fetch API keys and build project number -> project ID mapping for a scope."""
    keys = list(search_scope(scope, KEY_TYPE, read_mask, creds, session, quota_project, "KEYS "))

    num_to_id = {}
    if not scope.startswith("projects/"):
        # For organization or folder scopes, resolve project numbers to human-readable project IDs
        for p in search_scope(
            scope,
            PROJECT_TYPE,
            "name,displayName,project,additionalAttributes",
            creds,
            session,
            quota_project,
            "PROJ "
        ):
            attrs = p.get("additionalAttributes") or {}
            pid = attrs.get("projectId") or p.get("displayName") or ""
            num = attrs.get("projectNumber") or (p.get("project", "").split("/")[-1])
            if not num:
                m = re.search(r"/projects/(\d+)", p.get("name", ""))
                num = m.group(1) if m else ""
            if num and pid:
                num_to_id[str(num)] = pid
        log(f"Mapped {len(num_to_id)} project number(s) to IDs for {scope}", "OK")

    return keys, num_to_id


# --------------------------------------------------------------------------- #
# Row Building & Restriction Analysis
# --------------------------------------------------------------------------- #
def build_row(item, project_id, tz_info, tz_label, rotation_days=90):
    """Extract and categorize security posture for an API Key asset."""
    versioned = item.get("versionedResources", [])
    res = versioned[0].get("resource", {}) if versioned else {}
    restr = res.get("restrictions", {}) or {}

    name = item.get("displayName") or res.get("displayName") or item.get("name", "").split("/")[-1]
    created, age = parse_ts(item.get("createTime") or res.get("createTime") or "", tz_info, tz_label)
    uid = res.get("uid") or item.get("name", "").split("/")[-1]

    # API Restrictions
    targets = restr.get("apiTargets", [])
    if targets:
        apis = ", ".join(t.get("service", "") for t in targets)
        api_status = "RESTRICTED"
    else:
        apis = "UNRESTRICTED (All APIs Accessible)"
        api_status = "UNRESTRICTED"

    # Application Restrictions
    parts = []
    if "browserKeyRestrictions" in restr:
        referrers = restr["browserKeyRestrictions"].get("allowedReferrers", [])
        parts.append(f"HTTP Referrers: [{', '.join(referrers)}]")
    if "serverKeyRestrictions" in restr:
        ips = restr["serverKeyRestrictions"].get("allowedIps", [])
        parts.append(f"IPs: [{', '.join(ips)}]")
    if "androidKeyRestrictions" in restr:
        apps = [a.get("packageName", "") for a in restr["androidKeyRestrictions"].get("allowedApplications", [])]
        parts.append(f"Android: [{', '.join(apps)}]")
    if "iosKeyRestrictions" in restr:
        bundles = restr["iosKeyRestrictions"].get("allowedBundleIds", [])
        parts.append(f"iOS: [{', '.join(bundles)}]")

    if parts:
        app_det = " | ".join(parts)
        app_status = "RESTRICTED"
    else:
        app_det = "UNRESTRICTED (No Client Restrictions)"
        app_status = "UNRESTRICTED"

    if age == "N/A":
        rotation = "UNKNOWN"
    elif age > rotation_days:
        rotation = f"NEEDS ROTATION (>{rotation_days}d)"
    else:
        rotation = "OK"

    return {
        "Project ID": project_id,
        "Env": get_environment(project_id),
        "Key name (Credential name)": name,
        "Created date": created,
        "Selected APIs": apis,
        "Application Restriction details": app_det,
        "API Restriction Status": api_status,
        "App Restriction Status": app_status,
        "Key Age (Days)": age,
        "Rotation Alert": rotation,
        "Key UID": uid,
    }


def simple_row(pid, label, detail="N/A", status="N/A"):
    """Helper row for empty or errored projects/scopes."""
    return {
        "Project ID": pid,
        "Env": get_environment(pid),
        "Key name (Credential name)": label,
        "Created date": "N/A",
        "Selected APIs": "N/A",
        "Application Restriction details": detail,
        "API Restriction Status": status,
        "App Restriction Status": status,
        "Key Age (Days)": "N/A",
        "Rotation Alert": status,
        "Key UID": "N/A",
    }


# --------------------------------------------------------------------------- #
# Main Entry Point
# --------------------------------------------------------------------------- #
def main():
    parser = argparse.ArgumentParser(
        description="Enterprise GCP API Key Inventory via Cloud Asset Inventory (Strictly Read-Only)."
    )
    parser.add_argument(
        "-s", "--scope", action="append", required=False,
        help="Scope: organizations/ID | folders/ID | projects/ID (repeatable or comma-separated)"
    )
    parser.add_argument("--org-id", help="Convenience flag for Organization ID (e.g. 123456789012)")
    parser.add_argument("--folder-id", help="Convenience flag for Folder ID (e.g. 987654321)")
    parser.add_argument(
        "-f", "--projects-file",
        help="Optional text file of Project IDs (one per line) to filter/report on"
    )
    parser.add_argument(
        "-p", "--projects",
        help="Optional comma-separated list of Project IDs to filter/report on"
    )
    parser.add_argument(
        "-w", "--workers", type=int, default=10,
        help="Parallel worker threads for multi-scope scanning (default: 10)"
    )
    parser.add_argument(
        "-o", "--output", default="gcp_api_keys_inventory",
        help="Base output filename prefix (default: 'gcp_api_keys_inventory')"
    )
    parser.add_argument(
        "--rotation-days", type=int, default=90,
        help="Age threshold in days for key rotation alerts (default: 90)"
    )
    parser.add_argument(
        "--tz", "--timezone", dest="timezone", default="IST",
        help="Display timezone for timestamps: IST, UTC, EST, CST, PST (default: 'IST')"
    )
    parser.add_argument(
        "--read-mask", default="*",
        help="Cloud Asset readMask (default: '*')"
    )
    parser.add_argument(
        "--quota-project",
        help="Project ID billed for API quota (needs Cloud Asset API enabled)"
    )
    args = parser.parse_args()

    tz_info, tz_label = parse_timezone(args.timezone)

    print("=" * 75)
    print("   GCP API KEYS AUDITOR (CLOUD ASSET INVENTORY - STRICTLY READ-ONLY)   ")
    print("=" * 75)

    # Consolidate scopes
    scopes = []
    if args.org_id:
        scopes.append(f"organizations/{args.org_id.strip()}")
    if args.folder_id:
        scopes.append(f"folders/{args.folder_id.strip()}")
    for s in (args.scope or []):
        scopes += [x.strip() for x in s.split(",") if x.strip()]

    # Interactive prompt fallback if no scope provided
    if not scopes:
        if sys.stdin.isatty():
            try:
                user_in = input("Enter scope(s) e.g. organizations/123456789012 (comma-separated): ")
                scopes = [x.strip() for x in user_in.split(",") if x.strip()]
            except (EOFError, KeyboardInterrupt):
                print()
                sys.exit(130)
        else:
            log("No scope provided. Please specify --scope, --org-id, or --folder-id.", "ERR")
            sys.exit(1)

    if not scopes:
        log("No scopes provided. Exiting.", "ERR")
        sys.exit(1)

    bad_scopes = [s for s in scopes if not re.match(r"^(organizations|folders|projects)/[^/\s]+$", s)]
    if bad_scopes:
        log(f"Invalid scope format: {bad_scopes}. Must be organizations/ID, folders/ID, or projects/ID", "ERR")
        sys.exit(1)

    # Optional project filtering
    wanted = []
    if args.projects_file:
        try:
            with open(args.projects_file, "r", encoding="utf-8") as fh:
                wanted += [line.strip() for line in fh if line.strip() and not line.startswith("#")]
        except OSError as e:
            log(f"Cannot read {args.projects_file}: {e}", "ERR")
            sys.exit(1)
    if args.projects:
        wanted += [p.strip() for p in args.projects.split(",") if p.strip()]

    wanted = list(dict.fromkeys(wanted))
    wanted_set = set(wanted)
    if wanted:
        log(f"Filtering to {len(wanted)} requested project ID(s)")

    log(f"Scopes ({len(scopes)}): {', '.join(scopes)}")
    log(f"Config: Timezone={tz_label} | Rotation Threshold={args.rotation_days} days | Mode=STRICTLY READ-ONLY")
    log("Loading Application Default Credentials (ADC)...")

    try:
        creds, adc_project = google.auth.default(scopes=READ_ONLY_SCOPE)
        get_token(creds, force=True)
    except DefaultCredentialsError as e:
        log(f"No usable credentials found: {e}", "ERR")
        log("Run 'gcloud auth application-default login' or execute within Cloud Shell.", "ERR")
        sys.exit(2)
    except (RefreshError, TransportError) as e:
        log(f"Authentication token refresh failed: {e}", "ERR")
        sys.exit(2)

    quota_project = args.quota_project or getattr(creds, "quota_project_id", None) or adc_project
    log(f"Authenticated successfully. Quota project: {quota_project or 'None'}", "OK")

    workers = max(1, min(args.workers, len(scopes)))
    session = make_session(workers)
    rows, errors = [], []
    found_projects = set()
    start_time = time.time()

    executor = ThreadPoolExecutor(max_workers=workers)
    futures = {
        executor.submit(fetch_scope, s, args.read_mask, creds, session, quota_project): s
        for s in scopes
    }
    completed_count = 0

    try:
        for fut in as_completed(futures):
            completed_count += 1
            scope = futures[fut]
            try:
                items, num_to_id = fut.result()
            except Exception as e:
                errors.append((scope, str(e)))
                log(f"[{completed_count}/{len(scopes)}] {scope} FAILED: {e}", "ERR")
                continue

            kept = 0
            for item in items:
                m = re.search(r"/projects/([^/]+)/", item.get("name", ""))
                num = m.group(1) if m else (item.get("project", "").split("/")[-1])
                if scope.startswith("projects/"):
                    pid = scope.split("/", 1)[1]
                else:
                    pid = num_to_id.get(str(num), f"projects/{num}")

                if wanted_set and pid not in wanted_set:
                    continue

                rows.append(build_row(item, pid, tz_info, tz_label, args.rotation_days))
                found_projects.add(pid)
                kept += 1

            if scope.startswith("projects/"):
                found_projects.add(scope.split("/", 1)[1])

            log(f"[{completed_count}/{len(scopes)}] {scope}: {len(items)} key(s) discovered, {kept} kept", "OK")

    except KeyboardInterrupt:
        log("Execution interrupted by user. Cancelling pending tasks and saving partial data...", "WARN")
        executor.shutdown(wait=False, cancel_futures=True)
    else:
        executor.shutdown(wait=True)

    # Append placeholder rows for requested/per-project scopes that had zero keys
    keyed_projects = {r["Project ID"] for r in rows}
    if wanted:
        for pid in wanted:
            if pid not in keyed_projects:
                rows.append(simple_row(pid, "[NO API KEYS FOUND]"))
    else:
        for s in scopes:
            if s.startswith("projects/") and s.split("/", 1)[1] not in keyed_projects:
                rows.append(simple_row(s.split("/", 1)[1], "[NO API KEYS FOUND]"))

    for scope, err in errors:
        rows.append(simple_row(scope, "[ERROR: SCOPE SCAN FAILED]", err[:200], "ERROR"))

    duration = time.time() - start_time
    log(f"Scan completed in {duration:.1f}s", "OK")

    if not rows:
        log("No data returned or exported.", "WARN")
        sys.exit(1 if errors else 0)

    # Data export
    df = pd.DataFrame(rows)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"{args.output}_{timestamp_str}.csv"
    xlsx_filename = f"{args.output}_{timestamp_str}.xlsx"

    try:
        df.to_csv(csv_filename, index=False)
        log(f"CSV exported: {os.path.abspath(csv_filename)}", "OK")
    except OSError as e:
        log(f"CSV export failed: {e}", "ERR")

    try:
        log("Generating formatted Excel workbook...")
        with pd.ExcelWriter(xlsx_filename, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="API Keys Inventory")
            ws = writer.sheets["API Keys Inventory"]
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                col_letter = col[0].column_letter
                ws.column_dimensions[col_letter].width = min(max_len + 4, 60)
        log(f"Excel exported: {os.path.abspath(xlsx_filename)}", "OK")
    except ImportError:
        log("Optional package 'openpyxl' not found (pip install openpyxl). Skipping Excel creation.", "WARN")
    except OSError as e:
        log(f"Excel export failed: {e}", "ERR")

    # Audit Summary
    real_keys = df[~df["Key name (Credential name)"].astype(str).str.startswith("[")]
    unmapped = real_keys[real_keys["Project ID"].astype(str).str.startswith("projects/")]

    print("\n" + "=" * 75)
    print(" SECURITY AUDIT SUMMARY")
    print("=" * 75)
    print(f" Scopes Scanned Successfully : {len(scopes) - len(errors)} / {len(scopes)}")
    print(f" Projects with API Keys      : {real_keys['Project ID'].nunique()}")
    print(f" Total API Keys Discovered   : {len(real_keys)}")
    if not real_keys.empty:
        unrestr_apis = (real_keys["API Restriction Status"] == "UNRESTRICTED").sum()
        unrestr_apps = (real_keys["App Restriction Status"] == "UNRESTRICTED").sum()
        needs_rot = real_keys["Rotation Alert"].astype(str).str.startswith("NEEDS").sum()
        print(f" ⚠️  Unrestricted (APIs)      : {unrestr_apis}")
        print(f" ⚠️  Unrestricted (Apps)      : {unrestr_apps}")
        print(f" 🔄 Needs Rotation (>{args.rotation_days}d)   : {needs_rot}")
    if wanted:
        print(f" Requested Projects (No Keys): {sum(1 for p in wanted if p not in keyed_projects)}")
    if len(unmapped):
        print(f" [!] Unresolved project IDs  : {len(unmapped)} (shown as projects/<number>)")
    for scope, err in errors:
        print(f" [x] Failed Scope: {scope} - {err[:140]}")
    print(f" Total Duration              : {duration:.1f}s")
    print("=" * 75, flush=True)

    if errors or completed_count < len(scopes):
        sys.exit(1)


if __name__ == "__main__":
    main()
