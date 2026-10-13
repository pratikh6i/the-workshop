# Repository Utility Scripts 🛠️

This directory contains automation and operational utility scripts for **The Workshop**.

---

## 🛡️ Cloud Security & Auditing

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
