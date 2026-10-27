# Repository Utility Scripts 🛠️

This directory contains automation and operational utility scripts for **The Workshop**.

---

## 🛡️ Cloud Security & Auditing

### `logpull.py` ⭐
High-performance, quota-aware, and resumable **Bulk Cloud Logging reader**.

- **Reliability**: Self-paces to 50 requests/min (under GCP's 60 req/min quota) with exponential backoff on HTTP 429 and 5xx errors.
- **Observability**: Live terminal dashboard with progress bar, percentage, rate (entries/sec), request pacing, and estimated time to completion (ETA).
- **Crash-Resilience**: Continually flushes progress to disk (`.state.json` and `.jsonl.part`). Supports resuming interrupted jobs with `--resume` without data loss or duplicates.
- **Output Format**: Final output matches `gcloud logging read --format=json` (standard JSON array of `LogEntry` objects).

#### Usage:
```bash
# Pull Cloud Armor rate-limiting / security logs
python3 scripts/logpull.py \
  --project YOUR_PROJECT_ID \
  --filter 'resource.type="http_load_balancer" AND status>=400' \
  --days 30 \
  --limit 200000 \
  --out gcp_logs.json

# Resume interrupted run
python3 scripts/logpull.py \
  --project YOUR_PROJECT_ID \
  --filter 'resource.type="http_load_balancer" AND status>=400' \
  --days 30 \
  --limit 200000 \
  --out gcp_logs.json \
  --resume
```

---

### `org_public_ip_security_architect_audit.py` 🛡️⚡
Enterprise-scale, **strictly read-only**, ultra-high-speed multi-threaded GCP Cloud Security Architecture Auditor for Compute Engine VM instances.

- **Fastest in the Fleet**: Features short-circuit evaluation, fast DNS PTR timeouts, and high-concurrency worker threads. Automatically filters out system projects (`sys-*`) and detects disabled Compute APIs without stalling.
- **Deep Security Architecture Assessment**:
  - **Exposure**: Differentiates between Static Reserved vs Ephemeral Dynamic IPs, and RUNNING vs STOPPED instances (stopping accessConfig leaks).
  - **Ingress Attack Surface**: Scans project ingress firewall rules to alert on open `0.0.0.0/0` exposure for SSH (22), RDP (3389), or all ports.
  - **Lateral Movement & Blast Radius**: Inspects attached Service Accounts and evaluates project-level IAM roles and API scopes to quantify compromise blast radius.
  - **Reverse DNS (PTR)**: Performs automated PTR resolution to verify if public IPs map to external hostnames/domains.
  - **System Hardening**: Checks block-project-ssh-keys, serial port status, Shielded VM (Secure Boot, vTPM, Integrity Monitoring), and OS Config status.
- **Customer Review Template Ready**: Directly outputs 25 columns matching enterprise audit spreadsheets.

#### Usage:
```bash
# Interactive mode (prompts for Org ID)
python3 scripts/org_public_ip_security_architect_audit.py

# Non-interactive entire organization audit (high concurrency)
python3 scripts/org_public_ip_security_architect_audit.py --org-id YOUR_ORG_ID --workers 20

# Target specific projects
python3 scripts/org_public_ip_security_architect_audit.py --projects prd-project-1,prd-project-2

# Target specific folder
python3 scripts/org_public_ip_security_architect_audit.py --folder-id YOUR_FOLDER_ID
```

---

### `enrich_scc_public_ip_vms.py`
Enriches exported Security Command Center (SCC) findings CSVs (specifically `PUBLIC_IP_ADDRESS` findings) with live GCP metadata.

- **Enrichment**: Adds Static vs Ephemeral status, Reverse DNS PTR hostname, attached Service Account, Project-wide SSH keys blocking, and automated remediation action plans.
- **Usage**:
```bash
python3 scripts/enrich_scc_public_ip_vms.py --scc-csv scc_findings.csv -o enriched_scc_findings.csv
```

---

### `gcp_api_key_asset_scanner.py`
Enterprise-scale, **strictly read-only** GCP API Key Inventory script powered by **Google Cloud Asset Inventory (`searchAllResources`)**.

- **Speed**: Fetches 500 API keys per page across whole organizations or folders in seconds, avoiding N+1 project API call rate limits.
- **Safety**: Strictly read-only (`roles/cloudasset.viewer`, GET requests only).
- **Security Analysis**: Detects unrestricted APIs, unrestricted application types (IP, referrer, Android/iOS), key age, and 90-day rotation alerts.
- **Dual Export**: Exports to CSV and auto-formatted Excel (`.xlsx` with freeze panes and filters).

#### Usage:
```bash
# Scan entire organization
python3 scripts/gcp_api_key_asset_scanner.py --org-id YOUR_ORG_ID

# Scan specific folder
python3 scripts/gcp_api_key_asset_scanner.py --folder-id YOUR_FOLDER_ID

# Custom rotation threshold and timezone
python3 scripts/gcp_api_key_asset_scanner.py --org-id YOUR_ORG_ID --rotation-days 60 --tz UTC
```

---

### `get_org_firewalls.py`
High-speed, **strictly read-only** GCP Organization Firewall Inventory script.

- **Speed**: Uses Google Cloud Asset Inventory (`gcloud asset search-all-resources`) with multithreaded fetching to retrieve rules across hundreds of projects in seconds.
- **Safety**: 100% read-only (`roles/cloudasset.viewer`).
- **Complete Mapping**: Maps rules to their attached **VPC Network Name**, project ID, project name, location, and labels (`Customer`, `Domain`, `Platform`).

#### Usage:
```bash
# Table output
python3 scripts/get_org_firewalls.py --org-id YOUR_ORG_ID

# Export directly to CSV
python3 scripts/get_org_firewalls.py --org-id YOUR_ORG_ID --format csv > firewalls.csv

# Target a specific folder
python3 scripts/get_org_firewalls.py --folder-id YOUR_FOLDER_ID --format csv > folder_firewalls.csv
```

---

### `get_org_firewalls.sh`
Lightweight Bash + `jq` equivalent of the firewall inventory script for environments without Python.

#### Usage:
```bash
./scripts/get_org_firewalls.sh YOUR_ORG_ID
```

---

## 📝 Content Generation

### `new-day.js`
Generates starter MDX scaffolding for a new daily workshop module.

#### Usage:
```bash
node scripts/new-day.js <day-number> "<title>"
```
