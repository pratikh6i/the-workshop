#!/usr/bin/env bash
# ==============================================================================
# get_org_firewalls.sh
# ==============================================================================
# STRICTLY READ-ONLY & SUPERMAN FLASH SPEED FAST
# Fetches all firewall rules across an entire GCP Organization in a single query
# via Google Cloud Asset Inventory, including attached VPC Network Name.
#
# Output Columns:
# Display Name | Rule Name | VPC Network Name | Location | Description | Customer | Domain | Platform | Project ID | Project Name
# ==============================================================================

set -euo pipefail

ORG_ID="${1:-}"

if [[ -z "$ORG_ID" ]]; then
    # Try auto-detecting organization ID
    ORG_ID=$(gcloud organizations list --format="value(name)" 2>/dev/null | head -n 1 | sed 's/organizations\///' || true)
fi

if [[ -z "$ORG_ID" ]]; then
    echo "Usage: $0 <ORGANIZATION_ID>" >&2
    echo "Example: $0 653633894707" >&2
    exit 1
fi

SCOPE="organizations/${ORG_ID}"
echo "⚡ Querying Cloud Asset Inventory across ${SCOPE} (Read-Only & Ultra-Fast)..." >&2

# Print Header
echo "Display Name | Rule Name | VPC Network Name | Location | Description | Customer | Domain | Platform | Project ID | Project Name"
echo "---|---|---|---|---|---|---|---|---|---"

# Fetch all firewall assets in a single call across the entire org using --read-mask=*
gcloud asset search-all-resources \
    --scope="${SCOPE}" \
    --asset-types="compute.googleapis.com/Firewall" \
    --read-mask="*" \
    --format="json" | jq -r '
    .[] |
    (
        (.name | split("/") | .[-1]) as $rname |
        (.displayName // $rname) as $display |
        ((.name | capture("projects/(?<p>[^/]+)/").p) // (.project | split("/") | .[-1])) as $proj_id |
        (.versionedResources[0].resource.network // .resource.data.network // .additionalAttributes.network // .network // "-") as $net_full |
        ($net_full | split("/") | .[-1]) as $vpc |
        (.location // "global") as $loc |
        ((.description // "-") | gsub("[\r\n|]"; " ")) as $desc |
        (.labels.customer // "-") as $cust |
        (.labels.domain // "-") as $dom |
        (.labels.platform // "GCP") as $plat |
        [$display, $rname, $vpc, $loc, $desc, $cust, $dom, $plat, $proj_id, $proj_id] | join(" | ")
    )
'
