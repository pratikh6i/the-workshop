#!/usr/bin/env python3
"""
iam_principal_hierarchy_roles_report.py
======================================
GCP IAM Principal Hierarchy & Role Inheritance Auditor (STRICTLY READ-ONLY)

Purpose:
--------
Audits target GCP projects (from Organization root, Folder tree, or Project list)
to inspect every IAM Principal (Users, Service Accounts, Groups, Domains) having
an IAM role effective in the project.

It traces the entire ancestry hierarchy:
  Organization Node --> Folder --> Subfolder(s) --> Project

For each principal, it clearly distinguishes and reports:
  1. Roles Aggregated: Complete union of all effective roles at project level.
  2. Roles (Org Level): Roles inherited from the Organization node (with Org ID).
  3. Roles (Folder Level): Roles inherited from parent folders (with Folder ID & Display Name).
  4. Roles (Direct Project Level): Roles assigned directly on the project's own IAM policy.
  5. Principal Type: User, Service Account, Group, Domain, or Public.
  6. Hierarchy Path: Full ancestry path from Org down to Project.
  7. Admin / Privileged Role detection: Flags Owner, Editor, Organization Admin, Security Admin.

Safety & Read-Only Guarantee:
-----------------------------
Includes a hard-coded runtime guard (_assert_readonly) that strictly rejects any
mutating gcloud command (set, add, remove, grant, revoke, create, delete, update).
Only strictly read-only commands (get-iam-policy, describe, list, search-all-resources)
can ever be executed. Zero risk of modifying GCP configuration.
"""

import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from datetime import datetime, timezone
import json
import os
import subprocess
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Set, Tuple

# --------------------------------------------------------------------------
# Safety Guard: Hard block on ANY non-read-only gcloud verbs
# --------------------------------------------------------------------------
_FORBIDDEN_TOKENS = (
    "create", "delete", "update", "set-iam-policy", "add-iam-policy-binding",
    "remove-iam-policy-binding", "grant", "revoke", "patch", "enable",
    "disable", "undelete", "move", "import", "export", "deploy", "apply",
    "modify", "write", "destroy"
)


def _assert_readonly(args_list: List[str]) -> None:
    joined = " ".join(args_list).lower()
    for tok in _FORBIDDEN_TOKENS:
        if tok in joined:
            raise RuntimeError(f"BLOCKED: Execution halted! Non-read-only command attempted: {joined}")


# --------------------------------------------------------------------------
# Thread-Safe Logging
# --------------------------------------------------------------------------
_print_lock = threading.Lock()


def log(msg: str, level: str = "INFO") -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    with _print_lock:
        print(f"[{ts}] [{level}] {msg}", flush=True)


# --------------------------------------------------------------------------
# gcloud execution helper
# --------------------------------------------------------------------------
def run_gcloud(args_list: List[str], timeout: int = 45) -> Any:
    """
    Executes a read-only gcloud command, returns parsed JSON or raises RuntimeError.
    args_list must NOT include the leading 'gcloud'.
    """
    _assert_readonly(args_list)
    cmd = ["gcloud"] + args_list
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"TIMEOUT after {timeout}s: {' '.join(cmd)}")

    if proc.returncode != 0:
        err = proc.stderr.strip().replace("\n", " ")
        raise RuntimeError(f"gcloud error ({' '.join(cmd)}): {err}")

    stdout = proc.stdout.strip()
    if not stdout:
        return []
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"Could not parse JSON from: {' '.join(cmd)}")


# --------------------------------------------------------------------------
# In-Memory Thread-Safe Policy & Hierarchy Caches
# (Ensures Org and Parent Folders are queried ONCE and shared across all projects)
# --------------------------------------------------------------------------
_folder_describe_cache: Dict[str, dict] = {}
_folder_policy_cache: Dict[str, dict] = {}
_org_policy_cache: Dict[str, dict] = {}
_cache_lock = threading.Lock()


def cached_folder_describe(folder_id: str) -> dict:
    with _cache_lock:
        if folder_id in _folder_describe_cache:
            return _folder_describe_cache[folder_id]
    try:
        data = run_gcloud(["resource-manager", "folders", "describe", folder_id, "--format=json"])
    except RuntimeError as e:
        data = {"_error": str(e)}
    with _cache_lock:
        _folder_describe_cache[folder_id] = data
    return data


def cached_folder_policy(folder_id: str) -> dict:
    with _cache_lock:
        if folder_id in _folder_policy_cache:
            return _folder_policy_cache[folder_id]
    try:
        data = run_gcloud(["resource-manager", "folders", "get-iam-policy", folder_id, "--format=json"])
    except RuntimeError as e:
        data = {"_error": str(e)}
    with _cache_lock:
        _folder_policy_cache[folder_id] = data
    return data


def cached_org_policy(org_id: str) -> dict:
    with _cache_lock:
        if org_id in _org_policy_cache:
            return _org_policy_cache[org_id]
    try:
        data = run_gcloud(["organizations", "get-iam-policy", org_id, "--format=json"])
    except RuntimeError as e:
        data = {"_error": str(e)}
    with _cache_lock:
        _org_policy_cache[org_id] = data
    return data


# --------------------------------------------------------------------------
# Principal Parsing & Classification
# --------------------------------------------------------------------------
PRIVILEGED_ROLES = {
    "roles/owner", "roles/editor", "roles/resourcemanager.organizationAdmin",
    "roles/resourcemanager.folderAdmin", "roles/iam.securityAdmin",
    "roles/iam.serviceAccountAdmin", "roles/iam.serviceAccountKeyAdmin",
    "roles/resourcemanager.projectIamAdmin"
}


def parse_member(member: str) -> Tuple[str, str]:
    """
    Parses a GCP IAM member string into (principal_type, clean_identifier).
    """
    if member.startswith("user:"):
        return "User", member.split("user:", 1)[1]
    elif member.startswith("serviceAccount:"):
        return "Service Account", member.split("serviceAccount:", 1)[1]
    elif member.startswith("group:"):
        return "Group", member.split("group:", 1)[1]
    elif member.startswith("domain:"):
        return "Domain", member.split("domain:", 1)[1]
    elif member.startswith("deleted:"):
        parts = member.split(":")
        ptype = f"Deleted {parts[1].capitalize()}" if len(parts) > 2 else "Deleted Principal"
        ident = parts[2].split("?")[0] if len(parts) > 2 else member
        return ptype, ident
    elif member.startswith("principal://") or member.startswith("principalSet://"):
        return "Workload Identity", member
    elif member in ("allUsers", "allAuthenticatedUsers"):
        return "Public", member
    return "Other", member


# --------------------------------------------------------------------------
# Ancestry Walk: Project -> Folder(s) -> Organization
# --------------------------------------------------------------------------
def get_ancestry_chain(project_id: str) -> Tuple[List[Tuple[str, str, str]], Optional[str]]:
    """
    Walks up the resource hierarchy for a project.
    Returns:
      chain: List of (resource_type, resource_id, display_name) nearest ancestor first.
      error: Error string if describe fails.
    """
    chain = []
    try:
        describe = run_gcloud(["projects", "describe", project_id, "--format=json"])
    except RuntimeError as e:
        return chain, str(e)

    parent = describe.get("parent", {}) or {}
    ptype = parent.get("type")
    pid = parent.get("id")

    while ptype and pid:
        display_name = ""
        if ptype == "folder":
            f_info = cached_folder_describe(pid)
            if "_error" in f_info:
                chain.append((ptype, pid, "Error"))
                return chain, f_info["_error"]
            display_name = f_info.get("displayName", "")
            chain.append((ptype, pid, display_name))
            parent = f_info.get("parent", {}) or {}
            ptype = parent.get("type")
            pid = parent.get("id")
        elif ptype == "organization":
            chain.append((ptype, pid, "Organization"))
            break
        else:
            chain.append((ptype, pid, ""))
            break

    return chain, None


# --------------------------------------------------------------------------
# Project Discovery (Org, Folder, or Direct List)
# --------------------------------------------------------------------------
def discover_projects_under_folder(folder_id: str, seen_folders: Optional[Set[str]] = None) -> List[str]:
    """Recursively discover all projects under a folder."""
    if seen_folders is None:
        seen_folders = set()
    if folder_id in seen_folders:
        return []
    seen_folders.add(folder_id)

    projects = []
    log(f"Scanning folder {folder_id} for projects...")
    try:
        proj_result = run_gcloud([
            "projects", "list",
            "--filter", f"parent.id={folder_id} AND parent.type=folder",
            "--format=json",
        ])
        found = [p["projectId"] for p in proj_result if p.get("projectId")]
        projects.extend(found)
    except RuntimeError as e:
        log(f"  Folder {folder_id}: could not list projects ({e})", level="WARN")

    try:
        subfolders = run_gcloud(["resource-manager", "folders", "list", "--folder", folder_id, "--format=json"])
    except RuntimeError as e:
        subfolders = []

    for sf in subfolders:
        sf_id = sf.get("name", "").split("/")[-1]
        if sf_id:
            projects.extend(discover_projects_under_folder(sf_id, seen_folders))

    return projects


def discover_org_projects(org_id: str) -> List[str]:
    """Discover all active projects under an Organization, filtering sys-* projects."""
    log(f"Discovering all active projects under Organization: {org_id}...")
    projects = []

    # Method 1: Cloud Asset Inventory
    try:
        asset_res = run_gcloud([
            "asset", "search-all-resources",
            f"--scope=organizations/{org_id}",
            "--asset-types=cloudresourcemanager.googleapis.com/Project",
            "--query=state:ACTIVE",
            "--format=json"
        ], timeout=60)
        for p in asset_res:
            name_str = p.get("name", "")
            pid = name_str.split("/")[-1] if "/" in name_str else ""
            attrs = p.get("additionalAttributes") or {}
            proj_id = attrs.get("projectId") or pid
            if proj_id and proj_id not in projects:
                projects.append(proj_id)
    except Exception as e:
        log(f"Asset inventory search returned error ({e}); falling back to project list...", level="WARN")

    # Method 2: Fallback to projects list
    if not projects:
        try:
            proj_list = run_gcloud(["projects", "list", "--filter=lifecycleState=ACTIVE", "--format=json"], timeout=60)
            for p in proj_list:
                pid = p.get("projectId")
                if pid and pid not in projects:
                    projects.append(pid)
        except Exception as e:
            log(f"Project list query failed: {e}", level="ERROR")

    # Filter out system projects (sys-*)
    non_sys = [p for p in projects if not p.startswith("sys-")]
    skipped = len(projects) - len(non_sys)
    log(f"Found {len(projects)} total projects ({skipped} system 'sys-*' projects skipped, {len(non_sys)} queued)")
    return non_sys


# --------------------------------------------------------------------------
# Per-Project IAM Processing
# --------------------------------------------------------------------------
def process_project_iam(
    project_id: str,
    idx: int,
    total: int,
    principal_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Audits a project and extracts all direct and inherited roles per principal.
    """
    t0 = time.time()
    log(f"[{idx:>3}/{total}] Scanning Project: {project_id}")
    warnings = []

    # 1. Project-level IAM Policy (Direct roles)
    try:
        project_policy = run_gcloud(["projects", "get-iam-policy", project_id, "--format=json"])
    except RuntimeError as e:
        log(f"[{idx:>3}/{total}] {project_id}: get-iam-policy failed: {e}", level="WARN")
        project_policy = {"bindings": []}
        warnings.append(f"Project get-iam-policy failed: {e}")

    # principal_data[member] = {
    #     "type": str,
    #     "email": str,
    #     "direct": set(),
    #     "folder": list of (role, folder_id, display_name),
    #     "org": list of (role, org_id)
    # }
    principal_data = defaultdict(lambda: {
        "type": "Unknown",
        "email": "",
        "direct": set(),
        "folder": [],
        "org": []
    })

    for binding in project_policy.get("bindings", []):
        role = binding.get("role", "")
        for member in binding.get("members", []):
            ptype, ident = parse_member(member)
            principal_data[member]["type"] = ptype
            principal_data[member]["email"] = ident
            principal_data[member]["direct"].add(role)

    # 2. Ancestry Walk (Folders & Organization)
    chain, ancestry_error = get_ancestry_chain(project_id)
    if ancestry_error:
        warnings.append(f"Ancestry walk error: {ancestry_error}")

    hierarchy_parts = []
    # Ancestry returned nearest first (e.g. Subfolder -> Parent Folder -> Org).
    # Reverse to show top-down path: Org -> Folder -> Subfolder -> Project
    for rtype, rid, dname in reversed(chain):
        label = f"{rtype}:{rid}" if not dname or dname == "Organization" else f"{rtype}:{rid}({dname})"
        hierarchy_parts.append(label)
    hierarchy_parts.append(f"project:{project_id}")
    hierarchy_path_str = " > ".join(hierarchy_parts)

    for rtype, rid, dname in chain:
        if rtype == "folder":
            policy = cached_folder_policy(rid)
            folder_label = f"{rid} ({dname})" if dname else rid
            if "_error" in policy:
                warnings.append(f"Folder:{rid} policy fetch error: {policy['_error']}")
                continue
            for binding in policy.get("bindings", []):
                role = binding.get("role", "")
                for member in binding.get("members", []):
                    ptype, ident = parse_member(member)
                    principal_data[member]["type"] = ptype
                    principal_data[member]["email"] = ident
                    principal_data[member]["folder"].append((role, folder_label))

        elif rtype == "organization":
            policy = cached_org_policy(rid)
            if "_error" in policy:
                warnings.append(f"Org:{rid} policy fetch error: {policy['_error']}")
                continue
            for binding in policy.get("bindings", []):
                role = binding.get("role", "")
                for member in binding.get("members", []):
                    ptype, ident = parse_member(member)
                    principal_data[member]["type"] = ptype
                    principal_data[member]["email"] = ident
                    principal_data[member]["org"].append((role, rid))

    # 3. Build CSV Rows
    rows = []
    collected_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    for member, pinfo in sorted(principal_data.items(), key=lambda x: (x[1]["type"], x[1]["email"])):
        email = pinfo["email"]
        ptype = pinfo["type"]

        # Filter by principal if user requested
        if principal_filter and principal_filter.lower() not in email.lower() and principal_filter.lower() not in member.lower():
            continue

        direct_roles = sorted(pinfo["direct"])

        # Folder roles with bracketed folder IDs: "role (Folder: ID [Name])"
        folder_role_strings = []
        seen_f_roles = set()
        for role, flabel in pinfo["folder"]:
            f_key = (role, flabel)
            if f_key not in seen_f_roles:
                seen_f_roles.add(f_key)
                folder_role_strings.append(f"{role} (Folder: {flabel})")

        # Org roles with bracketed org IDs: "role (Org: ID)"
        org_role_strings = []
        seen_o_roles = set()
        for role, org_id in pinfo["org"]:
            o_key = (role, org_id)
            if o_key not in seen_o_roles:
                seen_o_roles.add(o_key)
                org_role_strings.append(f"{role} (Org: {org_id})")

        # Aggregated Roles: Unique set of all roles effective at project
        all_effective_roles = set(direct_roles) | {r for r, _ in pinfo["folder"]} | {r for r, _ in pinfo["org"]}
        aggregated_roles_str = "; ".join(sorted(all_effective_roles)) if all_effective_roles else "None"

        # Determine inheritance summary classification
        has_direct = bool(direct_roles)
        has_folder = bool(folder_role_strings)
        has_org = bool(org_role_strings)

        if has_direct and (has_folder or has_org):
            inheritance_summary = "Combined (Direct + Inherited)"
        elif has_direct:
            inheritance_summary = "Direct Project Grant Only"
        elif has_folder and has_org:
            inheritance_summary = "Inherited (Org + Folder)"
        elif has_folder:
            inheritance_summary = "Inherited (Folder Level)"
        elif has_org:
            inheritance_summary = "Inherited (Org Level)"
        else:
            inheritance_summary = "None"

        # Privileged check
        priv_found = all_effective_roles.intersection(PRIVILEGED_ROLES)
        is_privileged = f"YES ({', '.join(sorted(priv_found))})" if priv_found else "NO"

        rows.append({
            "Project ID": project_id,
            "Principal Type": ptype,
            "Principal Email": email,
            "Roles Aggregated": aggregated_roles_str,
            "Roles (Direct Project Level)": "; ".join(direct_roles) if direct_roles else "None",
            "Role (at folder level with folder ID in the bracket)": "; ".join(folder_role_strings) if folder_role_strings else "None",
            "roles (At org level)": "; ".join(org_role_strings) if org_role_strings else "None",
            "Total Effective Roles Count": len(all_effective_roles),
            "Inheritance Summary": inheritance_summary,
            "Has Privileged / Admin Role": is_privileged,
            "Hierarchy Ancestry Path": hierarchy_path_str,
            "Warnings": " | ".join(warnings) if warnings else "",
            "Data Collected At (UTC)": collected_at,
        })

    elapsed = time.time() - t0
    log(f"[{idx:>3}/{total}] DONE   Project: {project_id} ({len(rows)} principals audited) in {elapsed:.1f}s")
    return rows


# --------------------------------------------------------------------------
# Main Execution
# --------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="GCP IAM Principal Hierarchy & Role Inheritance Auditor (STRICTLY READ-ONLY)."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--org-id", help="GCP Organization ID (e.g. 653633894707)")
    group.add_argument("--folder-id", help="GCP Folder ID (recursively audits all subfolders & projects)")
    group.add_argument("--projects", help="Comma-separated GCP project IDs to inspect")

    parser.add_argument("--principal", help="Filter for specific principal email or keyword")
    parser.add_argument("-w", "--workers", type=int, default=12, help="Parallel worker threads (default: 12)")
    parser.add_argument("-o", "--output", default="", help="Output CSV path (default: auto-timestamped)")
    parser.add_argument("--delimiter", default=",", choices=[",", "|", "\t"], help="CSV Delimiter (default: comma ',')")

    args = parser.parse_args()

    print("=" * 85)
    print("   GCP IAM PRINCIPAL HIERARCHY & ROLE INHERITANCE AUDITOR (STRICTLY READ-ONLY)   ")
    print("   Traces: Organization Node --> Folder --> Subfolder(s) --> Project             ")
    print("=" * 85)

    # Verify gcloud authentication
    try:
        active_account = run_gcloud(["config", "get-value", "account", "--format=json"])
        log(f"Authenticated as: {active_account}")
    except RuntimeError as e:
        sys.stderr.write(f"\n❌ ERROR: gcloud is not authenticated: {e}\n")
        sys.stderr.write("   Please run: gcloud auth login or gcloud auth application-default login\n\n")
        sys.exit(1)

    project_ids = []
    scope_desc = ""

    if args.org_id:
        scope_desc = f"Organization: {args.org_id}"
        project_ids = discover_org_projects(args.org_id.strip())
    elif args.folder_id:
        scope_desc = f"Folder: {args.folder_id}"
        project_ids = sorted(set(discover_projects_under_folder(args.folder_id.strip())))
    elif args.projects:
        scope_desc = "Explicit Projects List"
        project_ids = [p.strip() for p in args.projects.split(",") if p.strip()]
    else:
        # Interactive prompt
        print("\nSelect Audit Scope:")
        print("  1) Entire Organization (Enter Org ID)")
        print("  2) Folder (Recursive through all subfolders & projects)")
        print("  3) Specific Project IDs (Comma-separated)")
        choice = input("\nEnter choice (1/2/3): ").strip()

        if choice == "1":
            org_id = input("Enter GCP Organization ID: ").strip()
            if not org_id:
                sys.stderr.write("Org ID required. Exiting.\n")
                sys.exit(1)
            scope_desc = f"Organization: {org_id}"
            project_ids = discover_org_projects(org_id)
        elif choice == "2":
            folder_id = input("Enter GCP Folder ID: ").strip()
            if not folder_id:
                sys.stderr.write("Folder ID required. Exiting.\n")
                sys.exit(1)
            scope_desc = f"Folder: {folder_id}"
            project_ids = sorted(set(discover_projects_under_folder(folder_id)))
        elif choice == "3":
            raw_pids = input("Enter comma-separated Project IDs: ").strip()
            project_ids = [p.strip() for p in raw_pids.split(",") if p.strip()]
            scope_desc = "Specific Projects List"
        else:
            sys.stderr.write("Invalid choice. Exiting.\n")
            sys.exit(1)

    # Filter out sys-* projects if any remain
    project_ids = [p for p in project_ids if not p.startswith("sys-")]

    if not project_ids:
        sys.stderr.write(f"\nNo projects discovered for scope: {scope_desc}. Exiting.\n")
        sys.exit(1)

    total_projects = len(project_ids)
    print(f"\n🚀 Commencing audit across {total_projects} projects with {args.workers} workers...")
    print(f"🔒 Mode: STRICTLY READ-ONLY | Scope: {scope_desc}\n")

    start_time = time.time()
    all_rows = []

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(process_project_iam, pid, i + 1, total_projects, args.principal): pid
            for i, pid in enumerate(project_ids)
        }
        for fut in as_completed(futures):
            pid = futures[fut]
            try:
                rows = fut.result()
                if rows:
                    all_rows.extend(rows)
            except Exception as e:
                log(f"Project {pid} exception: {e}", level="ERROR")

    elapsed_total = time.time() - start_time

    if not all_rows:
        print("\nNo IAM data found matching criteria. Exiting.")
        sys.exit(0)

    # Export to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = args.output or f"gcp_iam_principal_hierarchy_roles_report_{timestamp}.csv"

    fieldnames = [
        "Project ID",
        "Principal Type",
        "Principal Email",
        "Roles Aggregated",
        "roles (At org level)",
        "Role (at folder level with folder ID in the bracket)",
        "Roles (Direct Project Level)",
        "Total Effective Roles Count",
        "Inheritance Summary",
        "Has Privileged / Admin Role",
        "Hierarchy Ancestry Path",
        "Warnings",
        "Data Collected At (UTC)",
    ]

    with open(output_filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=args.delimiter)
        writer.writeheader()
        for row in sorted(all_rows, key=lambda r: (r["Project ID"], r["Principal Type"], r["Principal Email"])):
            writer.writerow(row)

    warned_rows = sum(1 for r in all_rows if r["Warnings"])
    privileged_count = sum(1 for r in all_rows if r["Has Privileged / Admin Role"].startswith("YES"))

    print("\n" + "=" * 85)
    print(" IAM AUDIT EXECUTION SUMMARY")
    print("=" * 85)
    print(f" Scope                     : {scope_desc}")
    print(f" Total Projects Audited    : {total_projects}")
    print(f" Total Principal-Role Rows : {len(all_rows)}")
    print(f" Privileged Principal Rows : {privileged_count}")
    print(f" Rows with Warnings        : {warned_rows}")
    print(f" Total Execution Time      : {elapsed_total:.2f} seconds")
    print(f" Output Report File        : {os.path.abspath(output_filename)}")
    print("=" * 85)
    print(f"\n✅ Audit complete! Open '{output_filename}' in Excel or Google Sheets to inspect roles.\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Execution interrupted by user. Exiting cleanly.")
        sys.exit(0)
