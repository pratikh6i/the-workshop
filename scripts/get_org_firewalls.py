#!/usr/bin/env python3
"""
get_org_firewalls.py
Strictly READ-ONLY & Ultra-Fast GCP Organization Firewall Inventory
Retrieves complete details including attached VPC Network Name.
"""

import argparse
import concurrent.futures
import csv
import json
import os
import re
import shutil
import subprocess
import sys
from typing import Dict, List, Optional


def find_gcloud() -> str:
    """Find gcloud path."""
    gcloud = shutil.which("gcloud")
    if gcloud:
        return gcloud
    for p in [
        "/google/google-cloud-sdk/bin/gcloud",  # Standard Cloud Shell path
        os.path.expanduser("~/google-cloud-sdk/bin/gcloud"),
        "/opt/homebrew/bin/gcloud",
        "/usr/local/bin/gcloud",
        "/usr/bin/gcloud",
    ]:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return "gcloud"


def run_gcloud_json(gcloud_bin: str, args: List[str]) -> List[dict]:
    """Execute strictly read-only gcloud command returning JSON."""
    cmd = [gcloud_bin] + args + ["--format=json"]
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        if proc.returncode != 0:
            if proc.stderr:
                sys.stderr.write(f"Warning: {proc.stderr.strip()[:300]}\n")
            return []
        out = proc.stdout.strip()
        if not out:
            return []
        return json.loads(out)
    except Exception as e:
        sys.stderr.write(f"Error executing command: {e}\n")
        return []


def fetch_projects(gcloud_bin: str, scope: str) -> Dict[str, dict]:
    """Fetch all projects across the organization scope."""
    sys.stderr.write(f"⚡ [1/2] Fetching project directory from {scope}...\n")
    data = run_gcloud_json(
        gcloud_bin,
        [
            "asset", "search-all-resources",
            f"--scope={scope}",
            "--asset-types=cloudresourcemanager.googleapis.com/Project"
        ]
    )
    mapping: Dict[str, dict] = {}
    for p in data:
        full_name = p.get("name", "")
        proj_id = full_name.split("/")[-1] if "/" in full_name else ""
        proj_display = p.get("displayName") or proj_id
        proj_num = p.get("project", "").replace("projects/", "")
        labels = p.get("labels") or {}

        info = {
            "id": proj_id,
            "name": proj_display,
            "labels": labels
        }
        if proj_id:
            mapping[proj_id] = info
        if proj_num:
            mapping[proj_num] = info
    sys.stderr.write(f"   Found {len(data)} projects in catalog.\n")
    return mapping


def fetch_firewalls(gcloud_bin: str, scope: str) -> List[dict]:
    """
    Fetch all firewall rules across the organization in one shot.
    CRITICAL: --read-mask=* ensures 'versionedResources' is included,
    which contains the attached VPC network URI ('resource.network').
    """
    sys.stderr.write(f"⚡ [2/2] Fetching all firewall rules & VPC mappings across {scope}...\n")
    rules = run_gcloud_json(
        gcloud_bin,
        [
            "asset", "search-all-resources",
            f"--scope={scope}",
            "--asset-types=compute.googleapis.com/Firewall",
            "--read-mask=*"
        ]
    )
    sys.stderr.write(f"   Found {len(rules)} firewall rules.\n")
    return rules


def extract_vpc_network(rule: dict) -> str:
    """
    Extract the clean VPC network name from rule metadata.
    In Cloud Asset Inventory, network is inside versionedResources[].resource.network.
    """
    # 1. Check versionedResources (returned with --read-mask=*)
    for vr in rule.get("versionedResources", []):
        res = vr.get("resource")
        if isinstance(res, str):
            try:
                res = json.loads(res)
            except Exception:
                res = {}
        if isinstance(res, dict):
            net = res.get("network")
            if net:
                return str(net).rstrip("/").split("/")[-1]

    # 2. Check resource.data.network (REST API format)
    res_obj = rule.get("resource", {})
    if isinstance(res_obj, dict):
        res_data = res_obj.get("data", {})
        if isinstance(res_data, dict) and "network" in res_data and res_data["network"]:
            return str(res_data["network"]).rstrip("/").split("/")[-1]

    # 3. Check additionalAttributes
    add_attrs = rule.get("additionalAttributes") or {}
    if isinstance(add_attrs, dict) and "network" in add_attrs and add_attrs["network"]:
        return str(add_attrs["network"]).rstrip("/").split("/")[-1]

    # 4. Check top-level
    if "network" in rule and rule["network"]:
        return str(rule["network"]).rstrip("/").split("/")[-1]

    return "-"


def parse_firewall(rule: dict, project_map: Dict[str, dict]) -> dict:
    raw_name = rule.get("name", "")
    rule_name = rule.get("displayName") or raw_name.split("/")[-1]
    display_name = rule.get("displayName") or rule_name

    # Extract project ID from URI e.g. //compute.googleapis.com/projects/MY_PROJ/...
    matched_proj = re.search(r"projects/([^/]+)/", raw_name)
    raw_proj_str = rule.get("project", "").replace("projects/", "")
    extracted_proj_id = matched_proj.group(1) if matched_proj else raw_proj_str

    proj_info = project_map.get(extracted_proj_id) or project_map.get(raw_proj_str) or {}
    project_id = proj_info.get("id") or extracted_proj_id or "-"
    project_name = proj_info.get("name") or project_id

    # Extract VPC Network Name
    vpc_network = extract_vpc_network(rule)

    location = rule.get("location") or "global"
    description = (rule.get("description") or "-").replace("\r", " ").replace("\n", " ")

    # Labels fallback
    rule_labels = rule.get("labels") or {}
    proj_labels = proj_info.get("labels") or {}

    def find_val(key_name: str, fallback: str = "-") -> str:
        for k, v in rule_labels.items():
            if k.lower() == key_name.lower():
                return str(v)
        for k, v in proj_labels.items():
            if k.lower() == key_name.lower():
                return str(v)
        return fallback

    customer = find_val("customer", "-")
    domain = find_val("domain", "-")
    platform = find_val("platform", "GCP")

    return {
        "display_name": display_name,
        "rule_name": rule_name,
        "vpc_network": vpc_network,
        "location": location,
        "description": description,
        "customer": customer,
        "domain": domain,
        "platform": platform,
        "project_id": project_id,
        "project_name": project_name,
    }


def main():
    parser = argparse.ArgumentParser(description="Strictly READ-ONLY GCP Org Firewall Auditor")
    parser.add_argument("--org-id", required=True, help="Numeric Organization ID e.g. 653633894707")
    parser.add_argument("--format", choices=["csv", "table", "tsv"], default="table")

    args = parser.parse_args()
    gcloud_bin = find_gcloud()
    scope = f"organizations/{args.org_id}"

    # Concurrently fetch in parallel for Flash Speed
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        f_proj = ex.submit(fetch_projects, gcloud_bin, scope)
        f_fire = ex.submit(fetch_firewalls, gcloud_bin, scope)
        proj_map = f_proj.result()
        raw_firewalls = f_fire.result()

    rows = [parse_firewall(r, proj_map) for r in raw_firewalls]
    rows.sort(key=lambda x: (x["project_id"], x["rule_name"]))

    headers = [
        "Display Name",
        "Rule Name",
        "VPC Network Name",
        "Location",
        "Description",
        "Customer",
        "Domain",
        "Platform",
        "Project ID",
        "Project Name"
    ]
    keys = [
        "display_name",
        "rule_name",
        "vpc_network",
        "location",
        "description",
        "customer",
        "domain",
        "platform",
        "project_id",
        "project_name"
    ]

    if args.format == "csv":
        writer = csv.writer(sys.stdout)
        writer.writerow(headers)
        for r in rows:
            writer.writerow([r[k] for k in keys])
    elif args.format == "tsv":
        print("\t".join(headers))
        for r in rows:
            print("\t".join(str(r[k]) for k in keys))
    else:
        print(" | ".join(headers))
        print(" | ".join(["---"] * len(headers)))
        for r in rows:
            print(" | ".join(str(r[k]) for k in keys))

    sys.stderr.write(f"\nDone! Processed {len(rows)} firewall rules.\n")


if __name__ == "__main__":
    main()
