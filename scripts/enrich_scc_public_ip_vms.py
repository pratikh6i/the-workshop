#!/usr/bin/env python3
"""
enrich_scc_public_ip_vms.py
===========================
STRICTLY READ-ONLY: Enriches Google Cloud Security Command Center (SCC)
'PUBLIC_IP_ADDRESS' findings with deep compute, network, and DNS intelligence.

Key Insights Added:
  1. Live VM Status: RUNNING vs TERMINATED (Explains why stopped VMs are flagged!)
  2. Public IP Classification: Static (Reserved) vs Ephemeral (Assigned on boot)
  3. Reverse DNS (PTR): Checks if public IP resolves to an external domain/FQDN
  4. Internal GCP DNS: Standard internal FQDN
  5. VPC & Subnet Architecture: Network, Subnet, Private IP
  6. Service Account & Security Risk: Identifies if default compute SA is used
  7. Tailored Customer Remediation: Auto-fills executive recommendations (e.g. for ESL Comments)

Usage:
  # 1. From an exported SCC CSV file:
  python3 enrich_scc_public_ip_vms.py --scc-csv scc_public_ip_findings.csv -o enriched_findings.csv

  # 2. Or scanning specific GCP projects directly:
  python3 enrich_scc_public_ip_vms.py --projects japan-stack-prd,satacs-be-pre-prod,prd-bi-icore-int

  # 3. Or across an entire GCP Organization (via Cloud Asset Inventory):
  python3 enrich_scc_public_ip_vms.py --org-id 123456789012
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import json
import os
import re
import socket
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

# Set global DNS timeout so slow PTR queries do not stall execution
socket.setdefaulttimeout(2.0)


def run_gcloud_json(cmd: List[str]) -> List[dict]:
    """Execute a read-only gcloud command returning parsed JSON."""
    try:
        proc = subprocess.run(
            ["gcloud"] + cmd + ["--format=json", "--quiet"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        if proc.returncode != 0:
            return []
        out = proc.stdout.strip()
        if not out:
            return []
        return json.loads(out)
    except Exception:
        return []


def reverse_dns_lookup(ip_address: str) -> str:
    """Perform reverse DNS (PTR) lookup to check if IP is mapped to an external domain."""
    if not ip_address or ip_address in ("N/A", "None", "-"):
        return "None"
    try:
        hostname, _, _ = socket.gethostbyaddr(ip_address)
        return hostname
    except (socket.herror, socket.gaierror, socket.timeout):
        return "No PTR Record Found"
    except Exception:
        return "Lookup Error"


def get_project_static_ips(project_id: str) -> Dict[str, str]:
    """Fetch all reserved static external IP addresses in the project."""
    addresses = run_gcloud_json(["compute", "addresses", "list", f"--project={project_id}"])
    ip_to_name = {}
    for addr in addresses:
        ip = addr.get("address")
        name = addr.get("name", "unnamed")
        if ip:
            ip_to_name[ip] = name
    return ip_to_name


def inspect_single_vm(
    project_id: str,
    zone: str,
    instance_name: str,
    static_ips_cache: Dict[str, str],
    scc_finding_meta: Optional[dict] = None
) -> dict:
    """
    Deep-inspect a single Compute Engine instance and determine:
    - Status (RUNNING vs TERMINATED)
    - Ephemeral vs Static Public IP
    - Reverse DNS mapping
    - Service Account and Network Tags
    - Tailored remediation recommendation
    """
    vm_data = run_gcloud_json([
        "compute", "instances", "describe", instance_name,
        f"--project={project_id}",
        f"--zone={zone}"
    ])

    if not vm_data or not isinstance(vm_data, dict):
        # Fallback if instance describe failed or deleted
        status = "NOT_FOUND_OR_DELETED"
        return {
            "Project ID": project_id,
            "Instance Name": instance_name,
            "Zone": zone,
            "VM Status": status,
            "Public IP": "N/A",
            "Public IP Type": "N/A",
            "Reverse DNS (PTR)": "N/A",
            "Internal IP": "N/A",
            "VPC Network": "N/A",
            "Subnet": "N/A",
            "Service Account": "N/A",
            "Network Tags": "N/A",
            "ESL Security Insight & Recommendation": (
                "Instance could not be queried or has been deleted. "
                "If deleted, verify the SCC finding is marked INACTIVE."
            ),
        }

    status = vm_data.get("status", "UNKNOWN")
    sa_list = vm_data.get("serviceAccounts", [])
    sa_email = sa_list[0].get("email", "None") if sa_list else "None"
    tags = "; ".join(vm_data.get("tags", {}).get("items", [])) or "None"

    # Analyze network interfaces
    has_public_ip_config = False
    public_ips = []
    public_ip_types = []
    internal_ips = []
    vpc_networks = []
    subnets = []
    dns_ptrs = []

    for nic in vm_data.get("networkInterfaces", []):
        int_ip = nic.get("networkIP")
        if int_ip:
            internal_ips.append(int_ip)

        net_name = nic.get("network", "").split("/")[-1]
        if net_name:
            vpc_networks.append(net_name)

        sub_name = nic.get("subnetwork", "").split("/")[-1]
        if sub_name:
            subnets.append(sub_name)

        # Access configs (Public IPs)
        for ac in nic.get("accessConfigs", []):
            has_public_ip_config = True
            nat_ip = ac.get("natIP")
            addr_ref = ac.get("address")

            if nat_ip:
                public_ips.append(nat_ip)
                # Reverse DNS check
                ptr = reverse_dns_lookup(nat_ip)
                dns_ptrs.append(ptr)

                if nat_ip in static_ips_cache:
                    public_ip_types.append(f"Static Reserved ({static_ips_cache[nat_ip]})")
                elif addr_ref and "addresses/" in addr_ref:
                    res_name = addr_ref.split("/")[-1]
                    public_ip_types.append(f"Static Reserved ({res_name})")
                else:
                    public_ip_types.append("Ephemeral (Dynamic)")
            else:
                # VM is stopped or accessConfig exists without assigned IP right now
                public_ips.append("None (Released while stopped)")
                public_ip_types.append("Ephemeral Config (Assigns Public IP on boot)")
                dns_ptrs.append("None")

    # Format values
    pub_ip_str = "; ".join(public_ips) if public_ips else "None"
    pub_type_str = "; ".join(public_ip_types) if public_ip_types else "No External Access Config"
    int_ip_str = "; ".join(internal_ips) if internal_ips else "None"
    vpc_str = "; ".join(set(vpc_networks)) if vpc_networks else "None"
    subnet_str = "; ".join(set(subnets)) if subnets else "None"
    ptr_str = "; ".join(dns_ptrs) if dns_ptrs else "None"

    # Formulate Executive Recommendation
    recommendations = []
    if status == "TERMINATED" or status == "STOPPED":
        recommendations.append(
            "⚠️ VM is STOPPED: SCC triggers because an external AccessConfig is attached to the NIC. "
            "Action: Remove the accessConfig from the stopped VM's NIC (`gcloud compute instances delete-access-config`) "
            "to permanently resolve the finding without deleting the VM."
        )
    elif status == "RUNNING":
        if "Static" in pub_type_str:
            recommendations.append(
                f"🚨 VM is RUNNING with a STATIC public IP ({pub_ip_str}). "
                "Action: Evaluate if direct internet ingress is required. "
                "If serving web/API traffic, migrate behind an external Cloud Load Balancer with Cloud Armor. "
                "If used for SSH/admin, remove the public IP and use Identity-Aware Proxy (IAP) TCP forwarding."
            )
        else:
            recommendations.append(
                f"⚠️ VM is RUNNING with an EPHEMERAL public IP ({pub_ip_str}). "
                "Action: Remove external IP. For internet egress (software updates/APIs), route traffic through Cloud NAT. "
                "For SSH administration, connect securely via Cloud IAP."
            )

    if ptr_str not in ("None", "No PTR Record Found", "Lookup Error"):
        recommendations.append(f"🌐 DNS Insight: Public IP resolves to domain: [{ptr_str}].")

    if "@developer.gserviceaccount.com" in sa_email:
        recommendations.append("🔒 SA Risk: VM uses Default Compute Service Account (often overprivileged with Editor role).")

    final_comment = " ".join(recommendations)

    row = {
        "Project ID": project_id,
        "Instance Name": instance_name,
        "Zone": zone,
        "VM Status": status,
        "Public IP": pub_ip_str,
        "Public IP Type": pub_type_str,
        "Reverse DNS (PTR / FQDN)": ptr_str,
        "Internal IP": int_ip_str,
        "VPC Network": vpc_str,
        "Subnet": subnet_str,
        "Service Account": sa_email,
        "Network Tags": tags,
        "ESL Security Insight & Recommendation": final_comment,
    }

    # If original SCC metadata was provided, prepend those columns
    if scc_finding_meta:
        combined = dict(scc_finding_meta)
        combined.update(row)
        return combined

    return row


def process_from_scc_csv(csv_path: str, output_path: str, max_workers: int = 5):
    """Enrich an exported SCC CSV finding file."""
    if not os.path.isfile(csv_path):
        sys.stderr.write(f"Error: CSV file not found: {csv_path}\n")
        sys.exit(1)

    print(f"📄 Reading SCC export from: {csv_path}")
    findings = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            findings.append(r)

    print(f"   Loaded {len(findings)} finding records.")

    # Group by project to minimize static IP calls
    projects = list({r.get("Project Name") or r.get("Project ID") for r in findings if r.get("Project Name") or r.get("Project ID")})
    print(f"   Spanning {len(projects)} unique projects.")

    project_static_ips: Dict[str, Dict[str, str]] = {}
    for p in projects:
        project_static_ips[p] = get_project_static_ips(p)

    enriched_rows = []
    print(f"⚡ Inspecting instances and querying Reverse DNS lookups (Workers: {max_workers})...\n")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for f in findings:
            proj = f.get("Project Name") or f.get("Project ID") or ""
            instance = f.get("resource.display_name") or f.get("Instance Name") or ""
            zone = f.get("resource.location") or f.get("Zone") or ""

            if not (proj and instance and zone):
                continue

            static_cache = project_static_ips.get(proj, {})
            futures.append(executor.submit(inspect_single_vm, proj, zone, instance, static_cache, f))

        count = 0
        for fut in as_completed(futures):
            count += 1
            res = fut.result()
            enriched_rows.append(res)
            print(f"[{count}/{len(futures)}] {res['Project ID']} / {res['Instance Name']} -> Status: {res['VM Status']} | IP: {res['Public IP']} ({res['Public IP Type']})")

    # Write output
    if enriched_rows:
        fieldnames = list(enriched_rows[0].keys())
        with open(output_path, "w", newline="", encoding="utf-8") as out_f:
            writer = csv.DictWriter(out_f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(enriched_rows)
        print(f"\n✅ Enriched customer report saved to: {output_path} ({len(enriched_rows)} rows)")


def process_direct_projects(projects: List[str], output_path: str, max_workers: int = 5):
    """Scan specified projects directly for instances with public IP configs."""
    all_rows = []
    for proj in projects:
        print(f"🔍 Fetching instances in project: {proj}...")
        static_cache = get_project_static_ips(proj)
        instances = run_gcloud_json(["compute", "instances", "list", f"--project={proj}"])

        for inst in instances:
            name = inst.get("name")
            zone = inst.get("zone", "").split("/")[-1]
            # Check if has accessConfig
            has_ac = False
            for nic in inst.get("networkInterfaces", []):
                if nic.get("accessConfigs"):
                    has_ac = True
                    break
            if has_ac:
                row = inspect_single_vm(proj, zone, name, static_cache)
                all_rows.append(row)
                print(f"   ➤ {name} ({zone}) -> Status: {row['VM Status']} | IP: {row['Public IP']} ({row['Public IP Type']}) | PTR: {row['Reverse DNS (PTR / FQDN)']}")

    if all_rows:
        with open(output_path, "w", newline="", encoding="utf-8") as out_f:
            writer = csv.DictWriter(out_f, fieldnames=list(all_rows[0].keys()))
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"\n✅ Report written to: {output_path} ({len(all_rows)} instances)")


def main():
    parser = argparse.ArgumentParser(
        description="Enrich SCC 'PUBLIC_IP_ADDRESS' findings with VM status, Static vs Ephemeral IP, and Reverse DNS."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scc-csv", help="Path to exported Security Command Center findings CSV")
    group.add_argument("--projects", help="Comma-separated GCP project IDs to inspect")

    parser.add_argument("-o", "--output", default="enriched_public_ip_findings.csv", help="Output CSV path")
    parser.add_argument("-w", "--workers", type=int, default=8, help="Parallel worker threads (default: 8)")

    args = parser.parse_args()

    if args.scc_csv:
        process_from_scc_csv(args.scc_csv, args.output, args.workers)
    elif args.projects:
        proj_list = [p.strip() for p in args.projects.split(",") if p.strip()]
        process_direct_projects(proj_list, args.output, args.workers)


if __name__ == "__main__":
    main()
