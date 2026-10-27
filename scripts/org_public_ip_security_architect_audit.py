#!/usr/bin/env python3
"""
org_public_ip_security_architect_audit.py
=========================================
GCP Compute Instance Public IP & Cloud Security Architecture Deep Auditor
Strictly READ-ONLY, Ultra High-Speed Multi-Threaded, Enterprise Scale.

From a Cloud Security Architecture POV, this script evaluates:
  1. Exposure: Does the VM have a Public IP (Static Reserved vs Ephemeral Dynamic)? Is VM RUNNING or STOPPED?
  2. Ingress Attack Surface: Are firewall rules allowing SSH (22), RDP (3389), or all ports from 0.0.0.0/0?
  3. Reverse DNS (PTR): Does the Public IP resolve to an external domain / FQDN?
  4. Blast Radius & Lateral Movement:
     - What Service Account is attached? Is it the default compute SA?
     - What IAM roles does the SA hold across the project?
     - If compromised via public IP, can an attacker move laterally and take over the project?
  5. System Hardening:
     - Project-wide SSH keys blocked?
     - Serial port console access disabled?
     - Shielded VM (Secure Boot, vTPM, Integrity Monitoring) enabled?
     - Deletion protection enabled?

Performance & Fail-Safe Features:
  - Automatically skips all system projects starting with 'sys-' (prevents scanning thousands of internal projects).
  - Explicitly detects if Compute API (compute.googleapis.com) is disabled on a project and skips gracefully.
  - Short-circuit optimization: Only queries IAM & Firewalls if a project actually contains Public IP VMs.
  - Real-time terminal progress tracking and instant alerts when Public IP VMs are found.
  - 100% Python 3 standard library: zero third-party dependencies required.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from datetime import datetime
import json
import os
import re
import socket
import subprocess
import sys
import threading
from typing import Any, Dict, List, Optional, Set, Tuple

# Fast DNS timeout for PTR lookups
socket.setdefaulttimeout(1.0)

# Human-readable API scopes mapping
SCOPE_MAPPING = {
    "https://www.googleapis.com/auth/cloud-platform": "cloud-platform (Full API Access)",
    "https://www.googleapis.com/auth/compute": "Compute Engine (Read/Write)",
    "https://www.googleapis.com/auth/compute.readonly": "Compute Engine (Read Only)",
    "https://www.googleapis.com/auth/devstorage.full_control": "Cloud Storage (Full Control)",
    "https://www.googleapis.com/auth/devstorage.read_write": "Cloud Storage (Read/Write)",
    "https://www.googleapis.com/auth/devstorage.read_only": "Cloud Storage (Read Only)",
    "https://www.googleapis.com/auth/bigquery": "BigQuery (Full)",
    "https://www.googleapis.com/auth/logging.write": "Logging (Write)",
    "https://www.googleapis.com/auth/logging.admin": "Logging (Admin)",
    "https://www.googleapis.com/auth/monitoring": "Monitoring (Full)",
    "https://www.googleapis.com/auth/monitoring.write": "Monitoring (Write)",
    "https://www.googleapis.com/auth/sqlservice.admin": "Cloud SQL (Admin)",
    "https://www.googleapis.com/auth/iam": "IAM (Full)",
}


class ScanStats:
    """Thread-safe statistics and progress tracking."""
    def __init__(self, total_projects: int):
        self.lock = threading.Lock()
        self.total_projects = total_projects
        self.scanned = 0
        self.public_vms = 0
        self.compute_disabled = 0
        self.permission_denied = 0
        self.errors = 0

    def increment_scanned(self) -> Tuple[int, int]:
        with self.lock:
            self.scanned += 1
            return self.scanned, self.total_projects

    def record_public_vms(self, count: int):
        with self.lock:
            self.public_vms += count

    def record_compute_disabled(self):
        with self.lock:
            self.compute_disabled += 1

    def record_permission_denied(self):
        with self.lock:
            self.permission_denied += 1

    def record_error(self):
        with self.lock:
            self.errors += 1


def run_gcloud_json(cmd: List[str], timeout: int = 25) -> Tuple[int, List[dict], str]:
    """
    Execute read-only gcloud command returning (returncode, json_data, stderr).
    Strictly fail-safe with subprocess timeout.
    """
    full_cmd = ["gcloud"] + cmd + ["--format=json", "--quiet"]
    try:
        proc = subprocess.run(
            full_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False
        )
        if proc.returncode != 0:
            return proc.returncode, [], proc.stderr.strip()

        stdout = proc.stdout.strip()
        if not stdout:
            return 0, [], ""
        return 0, json.loads(stdout), ""
    except subprocess.TimeoutExpired:
        return -1, [], "Command timed out"
    except json.JSONDecodeError:
        return -2, [], "Failed to parse JSON response"
    except Exception as e:
        return -3, [], str(e)


def reverse_dns_lookup(ip_address: str) -> str:
    """Check if IP resolves to an external domain (PTR lookup) with fast 1.0s timeout."""
    if not ip_address or ip_address in ("N/A", "None", "-") or "Released" in ip_address:
        return "None"
    try:
        hostname, _, _ = socket.gethostbyaddr(ip_address)
        return hostname
    except Exception:
        return "No PTR Record Found"


def discover_org_projects(org_id: str) -> List[str]:
    """
    Discover all active projects under a GCP Organization.
    Filters out system projects (starting with 'sys-') immediately.
    """
    sys.stdout.write(f"\n⚡ Discovering all projects under Organization: {org_id}...\n")
    sys.stdout.flush()

    raw_projects = []

    # Method 1: Cloud Asset Inventory search (fastest across entire Org hierarchy including all folders)
    retcode, asset_projects, stderr = run_gcloud_json([
        "asset", "search-all-resources",
        f"--scope=organizations/{org_id}",
        "--asset-types=cloudresourcemanager.googleapis.com/Project",
        "--query=state:ACTIVE"
    ], timeout=60)

    if retcode == 0 and asset_projects:
        for p in asset_projects:
            name_str = p.get("name", "")
            pid = name_str.split("/")[-1] if "/" in name_str else ""
            attrs = p.get("additionalAttributes") or {}
            proj_id = attrs.get("projectId") or pid
            if proj_id and proj_id not in raw_projects:
                raw_projects.append(proj_id)

    # Method 2: Fallback to projects list if Asset Inventory is disabled or unpermitted
    if not raw_projects:
        sys.stdout.write("   Cloud Asset Inventory returned no results; falling back to Resource Manager project list...\n")
        sys.stdout.flush()
        retcode, proj_list, stderr = run_gcloud_json([
            "projects", "list",
            "--filter=lifecycleState=ACTIVE"
        ], timeout=60)

        for p in proj_list:
            pid = p.get("projectId")
            # If parent org ID matches or child of org
            parent = p.get("parent", {})
            parent_id = str(parent.get("id", ""))
            if parent_id == org_id or not parent_id:
                if pid and pid not in raw_projects:
                    raw_projects.append(pid)
            elif pid and pid not in raw_projects:
                raw_projects.append(pid)

    total_discovered = len(raw_projects)
    sys.stdout.write(f"   Total active projects found: {total_discovered}\n")

    # Filter out system projects ('sys-*')
    non_sys_projects = []
    sys_skipped = 0
    for p in raw_projects:
        if p.startswith("sys-"):
            sys_skipped += 1
        else:
            non_sys_projects.append(p)

    sys.stdout.write(f"   ⏩ Filtered out {sys_skipped} internal system projects (starting with 'sys-').\n")
    sys.stdout.write(f"   🎯 Queued {len(non_sys_projects)} candidate projects for security auditing.\n\n")
    sys.stdout.flush()
    return non_sys_projects


def check_compute_and_list_instances(project_id: str) -> Tuple[str, List[dict]]:
    """
    Queries instances in project and detects if Compute API is disabled or inaccessible.
    Returns:
      status: 'OK', 'COMPUTE_DISABLED', 'PERMISSION_DENIED', 'ERROR'
      instances: list of instances if OK
    """
    retcode, data, stderr = run_gcloud_json(["compute", "instances", "list", f"--project={project_id}"])
    if retcode == 0:
        return "OK", data

    err_lower = stderr.lower()
    if (
        "not enabled" in err_lower
        or "service_disabled" in err_lower
        or "access not configured" in err_lower
        or "has not been used in project" in err_lower
    ):
        return "COMPUTE_DISABLED", []

    if "permission denied" in err_lower or "403" in err_lower:
        return "PERMISSION_DENIED", []

    return "ERROR", []


def get_project_iam_policy(project_id: str) -> Dict[str, List[str]]:
    """Fetch IAM policy for the project to map Service Account -> Roles."""
    sa_roles: Dict[str, List[str]] = {}
    retcode, policy_data, _ = run_gcloud_json(["projects", "get-iam-policy", project_id])
    if retcode != 0 or not policy_data or not isinstance(policy_data, dict):
        return sa_roles

    bindings = policy_data.get("bindings", [])
    for b in bindings:
        role = b.get("role", "")
        for member in b.get("members", []):
            if member.startswith("serviceAccount:"):
                sa = member.split("serviceAccount:", 1)[1]
                sa_roles.setdefault(sa, []).append(role)
    return sa_roles


def get_static_ips(project_id: str) -> Dict[str, str]:
    """Fetch reserved external IP addresses in the project."""
    retcode, addresses, _ = run_gcloud_json(["compute", "addresses", "list", f"--project={project_id}"])
    ip_map = {}
    if retcode == 0 and addresses:
        for addr in addresses:
            ip = addr.get("address")
            name = addr.get("name", "unnamed")
            if ip:
                ip_map[ip] = name
    return ip_map


def get_ingress_firewall_rules(project_id: str) -> List[dict]:
    """Fetch all active ingress firewall rules open to 0.0.0.0/0."""
    retcode, rules, _ = run_gcloud_json([
        "compute", "firewall-rules", "list",
        f"--project={project_id}",
        "--filter=direction=INGRESS AND disabled=false"
    ])
    open_rules = []
    if retcode == 0 and rules:
        for r in rules:
            source_ranges = r.get("sourceRanges", [])
            if "0.0.0.0/0" in source_ranges or "::/0" in source_ranges:
                open_rules.append(r)
    return open_rules


def check_instance_firewall_exposure(instance_tags: List[str], instance_sa: str, open_rules: List[dict]) -> str:
    """Determine what ports are exposed to the open internet (0.0.0.0/0) for this VM."""
    exposed_ports = set()
    open_to_all = False
    matching_rule_names = []

    for r in open_rules:
        target_tags = r.get("targetTags", [])
        target_sas = r.get("targetServiceAccounts", [])
        rule_name = r.get("name", "rule")

        applies = False
        # Rule applies if no target tags/SAs specified (applies to ALL VMs in VPC)
        if not target_tags and not target_sas:
            applies = True
        elif target_tags and any(t in instance_tags for t in target_tags):
            applies = True
        elif target_sas and instance_sa in target_sas:
            applies = True

        if applies:
            matching_rule_names.append(rule_name)
            allowed = r.get("allowed", [])
            for al in allowed:
                proto = al.get("IPProtocol", "").lower()
                ports = al.get("ports", [])
                if proto == "all":
                    open_to_all = True
                elif ports:
                    for p in ports:
                        exposed_ports.add(f"{proto}/{p}")
                else:
                    exposed_ports.add(f"{proto}/all")

    if open_to_all:
        return f"🚨 CRITICAL: ALL PORTS OPEN TO 0.0.0.0/0 via [{', '.join(matching_rule_names)}]"

    if exposed_ports:
        port_list = sorted(list(exposed_ports))
        has_ssh = any("22" in p for p in port_list)
        has_rdp = any("3389" in p for p in port_list)
        prefix = "🚨 CRITICAL: " if (has_ssh or has_rdp) else "⚠️ WARNING: "
        flag = []
        if has_ssh:
            flag.append("SSH(22)")
        if has_rdp:
            flag.append("RDP(3389)")
        other = [p for p in port_list if not ("22" in p or "3389" in p)]
        flag_str = ", ".join(flag + other)
        return f"{prefix}Open to 0.0.0.0/0 [{flag_str}] via [{', '.join(matching_rule_names)}]"

    return "🛡️ Direct Ingress Protected (No matching 0.0.0.0/0 ingress firewall rules)"


def evaluate_lateral_movement_risk(sa_email: str, sa_roles: List[str], scopes: List[str], has_public_ip: bool) -> str:
    """Assess attack blast radius and lateral movement potential if this VM is compromised."""
    if not has_public_ip:
        return "LOW (Internal VM only - No direct public ingress attack surface)"

    critical_roles = ["roles/owner", "roles/editor", "roles/iam.securityAdmin", "roles/resourcemanager.organizationAdmin"]
    high_roles = ["admin", "writer", "storage.admin", "bigquery.admin", "compute.admin", "container.admin"]

    is_default_sa = "@developer.gserviceaccount.com" in sa_email
    has_full_scope = any("cloud-platform" in s for s in scopes) or not scopes

    is_crit_role = any(any(cr in r.lower() for cr in critical_roles) for r in sa_roles)
    is_high_role = any(any(hr in r.lower() for hr in high_roles) for r in sa_roles)

    if (is_default_sa and (has_full_scope or is_crit_role)) or is_crit_role:
        return (
            "🚨 CRITICAL BLAST RADIUS: Attacker achieving shell/RCE can query Instance Metadata API "
            "(http://metadata.google.internal) to extract SA token and achieve FULL PROJECT CONTROL "
            f"(Holds: {', '.join(sa_roles) if sa_roles else 'Default Compute SA with Editor scope'}). Immediate lateral movement risk!"
        )

    if is_high_role or is_default_sa:
        return (
            f"⚠️ HIGH BLAST RADIUS: Attached SA ({sa_email}) holds privileged roles ({', '.join(sa_roles) or 'Default SA'}). "
            "Attacker can move laterally to access cloud databases, GCS buckets, and internal services."
        )

    if sa_roles:
        return f"🟡 MEDIUM: SA holds specific project roles ({', '.join(sa_roles)}). Scope restricted."

    return "🟢 LOW: No significant project IAM roles assigned directly to SA or SA is unattached."


def get_metadata_val(metadata_dict: Optional[dict], key: str) -> str:
    if not metadata_dict or "items" not in metadata_dict:
        return ""
    for item in metadata_dict.get("items", []):
        if item.get("key") == key:
            return str(item.get("value", ""))
    return ""


def process_project(project_id: str, stats: ScanStats, only_public: bool = True) -> List[Dict[str, Any]]:
    """
    Scan a single project's instances and build architectural audit rows.
    Implements fast short-circuiting:
      1. Check Compute API and list instances.
      2. If API disabled -> Log and exit immediately.
      3. If 0 instances or 0 public IP instances -> Exit immediately (avoids 3 redundant API calls).
      4. If public IP instances exist -> Fetch static IPs, firewall rules, and IAM policy.
    """
    # Step 1: Query compute instances
    compute_status, instances = check_compute_and_list_instances(project_id)
    cur_done, total = stats.increment_scanned()

    if compute_status == "COMPUTE_DISABLED":
        stats.record_compute_disabled()
        sys.stdout.write(f"[{cur_done:>4}/{total}] [-] [{project_id}] ⚠️  Compute API is disabled - Skipped\n")
        sys.stdout.flush()
        return []

    if compute_status == "PERMISSION_DENIED":
        stats.record_permission_denied()
        sys.stdout.write(f"[{cur_done:>4}/{total}] [!] [{project_id}] 🔒 Permission Denied (Missing compute.instances.list) - Skipped\n")
        sys.stdout.flush()
        return []

    if compute_status == "ERROR":
        stats.record_error()
        sys.stdout.write(f"[{cur_done:>4}/{total}] [!] [{project_id}] ❌ Error querying instances - Skipped\n")
        sys.stdout.flush()
        return []

    if not instances:
        # Zero instances in project
        sys.stdout.write(f"[{cur_done:>4}/{total}] [i] [{project_id}] 0 Compute Instances found\n")
        sys.stdout.flush()
        return []

    # Check if ANY instance in this project has a public IP configuration
    has_any_public = False
    for inst in instances:
        for nic in inst.get("networkInterfaces", []):
            if nic.get("accessConfigs"):
                has_any_public = True
                break
        if has_any_public:
            break

    if only_public and not has_any_public:
        sys.stdout.write(f"[{cur_done:>4}/{total}] [i] [{project_id}] {len(instances)} VM(s) found (All Private / 0 Public IPs)\n")
        sys.stdout.flush()
        return []

    # Step 2: ONLY for projects with public IP VMs, query project-level metadata (IAM, addresses, firewalls)
    sa_roles_map = get_project_iam_policy(project_id)
    static_ips_map = get_static_ips(project_id)
    open_fw_rules = get_ingress_firewall_rules(project_id)

    results = []

    for inst in instances:
        try:
            name = inst.get("name", "unnamed")
            zone = inst.get("zone", "").split("/")[-1]
            status = inst.get("status", "UNKNOWN")

            # Networking analysis
            public_ip = "N/A"
            public_ip_type = "None"
            private_ips = []
            has_public_ip_config = False

            nics = inst.get("networkInterfaces", [])
            for nic in nics:
                int_ip = nic.get("networkIP")
                if int_ip:
                    private_ips.append(int_ip)

                for ac in nic.get("accessConfigs", []):
                    has_public_ip_config = True
                    nat_ip = ac.get("natIP")
                    addr_link = ac.get("address")

                    if nat_ip:
                        public_ip = nat_ip
                        if nat_ip in static_ips_map:
                            public_ip_type = f"Static Reserved ({static_ips_map[nat_ip]})"
                        elif addr_link and "addresses/" in addr_link:
                            public_ip_type = f"Static Reserved ({addr_link.split('/')[-1]})"
                        else:
                            public_ip_type = "Ephemeral (Dynamic)"
                    else:
                        public_ip = "None (Released while stopped)"
                        public_ip_type = "Ephemeral Config (Allocates on Start)"

            if only_public and not has_public_ip_config:
                continue

            # Reverse DNS PTR lookup
            ptr_hostname = reverse_dns_lookup(public_ip)

            # Service Account & Scopes
            sa_email = "None"
            sa_scopes = "None"
            raw_scopes = []
            sa_list = inst.get("serviceAccounts", [])
            if sa_list:
                sa_email = sa_list[0].get("email", "None")
                raw_scopes = sa_list[0].get("scopes", [])
                formatted_scopes = [SCOPE_MAPPING.get(s, s.split("/")[-1]) for s in raw_scopes]
                sa_scopes = "; ".join(formatted_scopes) if formatted_scopes else "None"

            sa_roles = sa_roles_map.get(sa_email, [])
            sa_roles_str = "; ".join(sa_roles) if sa_roles else "No Direct Project Roles (or default permissions)"

            # Tags & Ingress Exposure Analysis
            tags_list = inst.get("tags", {}).get("items", [])
            fw_exposure = check_instance_firewall_exposure(tags_list, sa_email, open_fw_rules)

            # Lateral Movement Assessment
            has_live_public = (public_ip != "N/A" and "Released" not in public_ip and status == "RUNNING")
            lateral_risk = evaluate_lateral_movement_risk(sa_email, sa_roles, raw_scopes, has_live_public)

            # Hardening configurations
            metadata = inst.get("metadata", {})
            block_ssh_keys = get_metadata_val(metadata, "block-project-ssh-keys").lower()
            ssh_keys_blocked = "Blocked (Hardened)" if block_ssh_keys in ["true", "1"] else "Allowed / Not Set (Project SSH keys apply)"

            serial_port_val = get_metadata_val(metadata, "serial-port-enable").lower()
            serial_port_status = "Enabled (RISK)" if serial_port_val in ["true", "1"] else "Disabled"

            del_prot = "Enabled" if inst.get("deletionProtection", False) else "Disabled"

            # Shielded VM
            sic = inst.get("shieldedInstanceConfig", {})
            secure_boot = "TRUE" if sic.get("enableSecureBoot") else "FALSE"
            vtpm = "TRUE" if sic.get("enableVtpm") else "FALSE"
            integrity_monitoring = "TRUE" if sic.get("enableIntegrityMonitoring") else "FALSE"

            # Confidential Compute
            conf_comp = "TRUE" if inst.get("confidentialInstanceConfig", {}).get("enableConfidentialCompute") else "FALSE"

            # OS Config Agent
            os_config_meta = get_metadata_val(metadata, "enable-osconfig").lower()
            os_config_status = "Enabled" if os_config_meta in ["true", "1"] else "Disabled / Not Configured"

            # Architectural Recommendation
            recommendations = []
            if status in ["STOPPED", "TERMINATED"]:
                recommendations.append(
                    "VM is STOPPED: Public IP finding is caused by leftover accessConfig on the NIC. "
                    "Action: Run 'gcloud compute instances delete-access-config' to remove the external IP definition. "
                    "This permanently eliminates the finding without deleting the instance."
                )
            elif status == "RUNNING":
                if "Static" in public_ip_type:
                    recommendations.append(
                        f"VM is actively running with Static Public IP [{public_ip}]. "
                        "Action: Migrate public ingress to an external Cloud Load Balancer with Cloud Armor WAF. "
                        "Use Cloud IAP for administrative SSH access and delete the public IP."
                    )
                else:
                    recommendations.append(
                        f"VM is actively running with Ephemeral Public IP [{public_ip}]. "
                        "Action: If VM only requires outbound internet access (package updates/third-party APIs), "
                        "deploy Cloud NAT and remove the public IP. Use Cloud IAP for SSH."
                    )

            if "CRITICAL" in fw_exposure:
                recommendations.append("URGENT: Port 22/3389 is exposed to 0.0.0.0/0. Restrict ingress firewall rule immediately.")

            if "CRITICAL BLAST RADIUS" in lateral_risk:
                recommendations.append("URGENT: Replace Default Compute Service Account with a custom least-privilege service account.")

            # Construct row matching customer template + security architecture fields
            row = {
                "Project ID": project_id,
                "Instance Name": name,
                "Zone": zone,
                "Instance Status": status,
                "Public IP Type": public_ip_type,
                "Public IP Address": public_ip,
                "Reverse DNS (PTR)": ptr_hostname,
                "Firewall Ingress Exposure (0.0.0.0/0)": fw_exposure,
                "Blast Radius & Lateral Movement Risk": lateral_risk,
                "Public IP Required Yes/No": "",
                "If Yes Justification for Public IP.": "",
                "Service Account": sa_email,
                "Service Account Roles": sa_roles_str,
                "API Scopes": sa_scopes,
                "Deletion Protection": del_prot,
                "Project-Wide SSH Keys Blocked": ssh_keys_blocked,
                "OS Config": os_config_status,
                "Confidential Compute": conf_comp,
                "Secure Boot": secure_boot,
                "vTPM": vtpm,
                "Integrity Monitoring": integrity_monitoring,
                "Serial Port": serial_port_status,
                "OS Config Status": os_config_status,
                "Architecture Guidance & Action Plan": " ".join(recommendations),
                "Customer Review / Justifications": "",
            }

            results.append(row)
            stats.record_public_vms(1)

            # Live terminal alert for discovered Public IP VM
            fw_flag = "🚨 CRITICAL FW" if "CRITICAL" in fw_exposure else ("⚠️ WARNING FW" if "WARNING" in fw_exposure else "🛡️ FW OK")
            sa_flag = "🚨 DEFAULT SA" if "@developer.gserviceaccount.com" in sa_email else "SA Custom"
            sys.stdout.write(
                f"[{cur_done:>4}/{total}] 🚨 FOUND PUBLIC IP VM: [{project_id}] {name} ({status}) | "
                f"IP: {public_ip} ({public_ip_type}) | {fw_flag} | {sa_flag}\n"
            )
            sys.stdout.flush()

        except Exception as e:
            sys.stdout.write(f"[{cur_done:>4}/{total}] [!] Error processing instance {inst.get('name')}: {e}\n")
            sys.stdout.flush()

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive GCP Compute Security Architecture Auditor for VM Public IPs (Ultra Fast & Strictly Read-Only)."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--org-id", help="GCP Organization ID (numeric string e.g. 653633894707)")
    group.add_argument("--folder-id", help="GCP Folder ID (numeric string)")
    group.add_argument("--projects", help="Comma-separated GCP project IDs to inspect")
    group.add_argument("--scc-csv", help="Path to exported Security Command Center findings CSV")

    parser.add_argument("-w", "--workers", type=int, default=16, help="Parallel worker threads (default: 16 for high speed)")
    parser.add_argument("-o", "--output", default="", help="Output CSV path (default: auto-timestamped)")
    parser.add_argument("--all-vms", action="store_true", help="Include all VMs (default: only VMs with Public IPs)")

    args = parser.parse_args()

    print("=" * 85)
    print("   GCP CLOUD SECURITY ARCHITECTURE AUDITOR: PUBLIC IP & BLAST RADIUS SCANNER   ")
    print("   Strictly READ-ONLY | High-Concurrency Multi-Threaded | Enterprise Scale     ")
    print("=" * 85)

    projects_to_scan = []
    org_id_used = ""

    if args.scc_csv:
        if not os.path.isfile(args.scc_csv):
            sys.stderr.write(f"Error: SCC CSV file not found: {args.scc_csv}\n")
            sys.exit(1)
        with open(args.scc_csv, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for r in reader:
                p = r.get("Project Name") or r.get("Project ID")
                if p and p not in projects_to_scan and not p.startswith("sys-"):
                    projects_to_scan.append(p)
    elif args.projects:
        projects_to_scan = [p.strip() for p in args.projects.split(",") if p.strip() and not p.strip().startswith("sys-")]
    elif args.org_id:
        org_id_used = args.org_id.strip()
        projects_to_scan = discover_org_projects(org_id_used)
    elif args.folder_id:
        sys.stdout.write(f"Fetching projects in folder: {args.folder_id}...\n")
        retcode, res, _ = run_gcloud_json(["projects", "list", f"--filter=parent.id={args.folder_id} AND lifecycleState=ACTIVE"])
        for p in res:
            pid = p.get("projectId")
            if pid and not pid.startswith("sys-") and pid not in projects_to_scan:
                projects_to_scan.append(pid)
    else:
        # User requested interactive prompt asking for org id
        print("\nEnter GCP Organization ID to audit the entire organization.")
        print("(Or leave blank and type 'projects' to specify individual project IDs)")
        user_input = input("Enter GCP Organization ID: ").strip()

        if user_input.lower() == "projects":
            p_in = input("Enter Project IDs (comma-separated): ").strip()
            projects_to_scan = [p.strip() for p in p_in.split(",") if p.strip() and not p.strip().startswith("sys-")]
        elif user_input:
            org_id_used = user_input
            projects_to_scan = discover_org_projects(org_id_used)
        else:
            sys.stderr.write("No Organization ID provided. Exiting.\n")
            sys.exit(1)

    if not projects_to_scan:
        sys.stderr.write("No valid target projects to scan. Exiting.\n")
        sys.exit(1)

    stats = ScanStats(len(projects_to_scan))

    print(f"🚀 Launching high-speed scan across {len(projects_to_scan)} candidate projects with {args.workers} workers...")
    print("🔒 Mode: STRICTLY READ-ONLY | Short-circuit optimization active\n")

    all_data = []
    start_time = datetime.now()

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_project, p, stats, not args.all_vms): p for p in projects_to_scan}
        for fut in as_completed(futures):
            p = futures[fut]
            try:
                rows = fut.result()
                if rows:
                    all_data.extend(rows)
            except Exception as e:
                stats.record_error()
                sys.stdout.write(f"[!] Project {p} thread exception: {e}\n")

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = args.output or f"gcp_org_public_ip_security_architecture_audit_{timestamp_str}.csv"

    elapsed = (datetime.now() - start_time).total_seconds()

    print("\n" + "=" * 85)
    print(" AUDIT EXECUTION SUMMARY")
    print("=" * 85)
    if org_id_used:
        print(f" Organization ID            : {org_id_used}")
    print(f" Projects Audited           : {len(projects_to_scan)}")
    print(f" Compute API Disabled       : {stats.compute_disabled} projects (gracefully skipped)")
    print(f" Permission Denied Projects : {stats.permission_denied} projects")
    print(f" Public IP VMs Discovered   : {len(all_data)}")
    print(f" Total Scan Time            : {elapsed:.2f} seconds")

    if all_data:
        headers = list(all_data[0].keys())
        with open(output_filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(all_data)

        print(f" Detailed CSV Report Saved  : {os.path.abspath(output_filename)}")
        print("=" * 85)
        print(f"\n✅ SUCCESS: Found {len(all_data)} VM instances with Public IPs across the organization.")
        print(f"👉 Review the CSV file '{output_filename}' for full blast radius & action plan details.\n")
    else:
        print(f" Report Status              : No Public IP VMs discovered across scanned projects.")
        print("=" * 85 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Execution interrupted by user. Exiting cleanly.")
        sys.exit(0)
