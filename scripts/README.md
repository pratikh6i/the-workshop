# Repository Utility Scripts 🛠️

This directory contains automation and operational utility scripts for **The Workshop**.

---

## 🛡️ Cloud Security & Auditing

### `gcp_api_key_asset_scanner.py` ⭐
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
