#!/usr/bin/env python3
"""
jira_bless_poller.py

Polls the SES Jira project for open bless-test-results requests and
executes them on the machine named in each ticket.  After running,
the ticket is commented with the command output and transitioned to
resolved.

Environment variables (required):
  JIRA_EMAIL       - Atlassian account email
  JIRA_API_TOKEN   - Atlassian API token
                     (create one at https://id.atlassian.com/manage-profile/security/api-tokens)

Environment variables (optional):
  JIRA_MACHINE       - Override the machine name used for matching
                       (default: socket.gethostname())
  JIRA_NO_VERIFY_SSL - Set to '1' to disable SSL certificate verification
                       (useful behind corporate TLS-inspecting proxies)

Jira fields read per ticket:
  "List of Test Cases that DIFF'd"        - one regex pattern per line, passed to -f
  "Machine"                                - the machine this ticket targets
  "Test Suites - Developer & Integration"  - comma-separated list of test suites;
                                             one bless_test_results command is run
                                             per suite, using -t <suite>
  "Action"                                 - checkbox/select: 'hists', 'nmls', or 'both'
                                             hists -> --hist-only
                                             nmls  -> -n
                                             both  -> no extra flag (default)
"""

import base64
import json
import os
import socket
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

JIRA_BASE_URL = "https://e3sm.atlassian.net"
PROJECT_KEY   = "SES"
BLESS_SCRIPT  = "./Tools/bless_test_results"

FIELD_CASES   = "List of Test Cases that DIFF'd"
FIELD_MACHINE = "Machine"
FIELD_SUITES  = "Test Suites - Developer & Integration"
FIELD_ACTION  = "Action"

# Only tickets not yet resolved/done/closed are considered.
JQL = (
    f"project = {PROJECT_KEY} "
    "AND status not in (Resolved, Done, Closed) "
    "ORDER BY created ASC"
)

# Transition names to try when resolving (first match wins, case-insensitive).
RESOLVE_TRANSITION_NAMES = [
    "resolved",
    "resolve request",
    "resolve",
    "done",
    "close",
]

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _ssl_context():
    if os.environ.get("JIRA_NO_VERIFY_SSL", "").strip() == "1":
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    return None


def _auth_headers():
    email = os.environ.get("JIRA_EMAIL", "").strip()
    token = os.environ.get("JIRA_API_TOKEN", "").strip()
    if not email or not token:
        sys.exit(
            "Error: JIRA_EMAIL and JIRA_API_TOKEN must be set.\n"
            "  export JIRA_EMAIL=you@example.com\n"
            "  export JIRA_API_TOKEN=<token>"
        )
    creds = base64.b64encode(f"{email}:{token}".encode()).decode()
    return {
        "Authorization": f"Basic {creds}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }


def _http(method, path, headers, payload=None, params=None):
    url = f"{JIRA_BASE_URL}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(payload).encode() if payload is not None else None
    req  = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=_ssl_context()) as resp:
            body = resp.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {exc.code} {method} {url}: {body}") from exc


def jira_get(path, headers, params=None):
    return _http("GET", path, headers, params=params)


def jira_post(path, headers, payload):
    return _http("POST", path, headers, payload=payload)

# ---------------------------------------------------------------------------
# Jira field/issue helpers
# ---------------------------------------------------------------------------

def discover_field_ids(headers):
    """Return {display_name: field_id} for every field in the instance."""
    return {f["name"]: f["id"] for f in jira_get("/rest/api/3/field", headers)}


def search_issues(headers, jql, extra_field_ids):
    """Fetch all issues matching *jql*, requesting summary + extra_field_ids."""
    all_issues, start_at = [], 0
    wanted = ",".join(["summary"] + extra_field_ids)
    while True:
        page = jira_get("/rest/api/3/search", headers, {
            "jql":        jql,
            "startAt":    start_at,
            "maxResults": 50,
            "fields":     wanted,
        })
        chunk = page.get("issues", [])
        all_issues.extend(chunk)
        start_at += len(chunk)
        if start_at >= page.get("total", 0):
            break
    return all_issues


def add_comment(headers, issue_key, text):
    """Post a plain-text comment (Atlassian Document Format)."""
    jira_post(f"/rest/api/3/issue/{issue_key}/comment", headers, {
        "body": {
            "type":    "doc",
            "version": 1,
            "content": [
                {
                    "type":    "paragraph",
                    "content": [{"type": "text", "text": text}],
                }
            ],
        }
    })


def transition_issue(headers, issue_key):
    """Try each name in RESOLVE_TRANSITION_NAMES; return matched name or None."""
    data       = jira_get(f"/rest/api/3/issue/{issue_key}/transitions", headers)
    name_to_id = {t["name"].lower(): t["id"] for t in data.get("transitions", [])}
    for name in RESOLVE_TRANSITION_NAMES:
        if name in name_to_id:
            jira_post(f"/rest/api/3/issue/{issue_key}/transitions", headers, {
                "transition": {"id": name_to_id[name]}
            })
            return name
    print(f"  [{issue_key}] WARNING: no resolve transition found. "
          f"Available: {list(name_to_id.keys())}")
    return None

# ---------------------------------------------------------------------------
# Field value extractors
# ---------------------------------------------------------------------------

def extract_text_lines(value):
    """Return non-empty lines from a plain-text or ADF (rich-text) field."""
    if value is None:
        return []
    if isinstance(value, str):
        return [ln.strip() for ln in value.splitlines() if ln.strip()]
    # Atlassian Document Format
    if isinstance(value, dict) and value.get("type") == "doc":
        lines = []
        for block in value.get("content", []):
            for inline in block.get("content", []):
                if inline.get("type") == "text":
                    text = inline.get("text", "").strip()
                    if text:
                        lines.append(text)
        return lines
    return []


def extract_machine_names(value):
    """Return a list of lowercase machine name strings from any Jira field shape."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value.lower()]
    if isinstance(value, dict):
        name = value.get("value") or value.get("name") or value.get("displayName", "")
        return [name.lower()] if name else []
    if isinstance(value, list):
        names = []
        for item in value:
            names.extend(extract_machine_names(item))
        return names
    return [str(value).lower()]


def extract_action(value):
    """
    Map a checkbox/select Jira field to one of 'hists', 'nmls', or 'both'.

    For list (checkbox) fields, both boxes checked => 'both'.
    Unrecognised or missing values default to 'both'.
    """
    VALID = {"hists", "nmls", "both"}

    if value is None:
        return "both"
    if isinstance(value, str):
        v = value.lower().strip()
        return v if v in VALID else "both"
    if isinstance(value, dict):
        v = (value.get("value") or value.get("name", "")).lower().strip()
        return v if v in VALID else "both"
    if isinstance(value, list):
        selected = set()
        for item in value:
            if isinstance(item, dict):
                v = (item.get("value") or item.get("name", "")).lower().strip()
                selected.add(v)
        if "hists" in selected and "nmls" in selected:
            return "both"
        if "hists" in selected:
            return "hists"
        if "nmls" in selected:
            return "nmls"
        return "both"
    return "both"

# ---------------------------------------------------------------------------
# bless runner
# ---------------------------------------------------------------------------

def build_bless_cmd(suite, cases, action):
    """Construct the bless_test_results argument list for one test suite."""
    cmd = [BLESS_SCRIPT, "-t", suite]
    for case in cases:
        cmd += ["-f", case]
    if action == "hists":
        cmd.append("--hist-only")
    elif action == "nmls":
        cmd.append("-n")
    # action == "both": no extra flag
    return cmd


def run_bless(suite, cases, action):
    cmd = build_bless_cmd(suite, cases, action)
    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    headers         = _auth_headers()
    current_machine = os.environ.get("JIRA_MACHINE", socket.gethostname()).lower()

    print(f"Polling {JIRA_BASE_URL} | project: {PROJECT_KEY} | machine: {current_machine}")

    # Map display names to REST field IDs
    print("Discovering field IDs...")
    field_map   = discover_field_ids(headers)
    cases_fid   = field_map.get(FIELD_CASES)
    machine_fid = field_map.get(FIELD_MACHINE)
    suites_fid  = field_map.get(FIELD_SUITES)
    action_fid  = field_map.get(FIELD_ACTION)

    if not cases_fid:
        sys.exit(f"Error: Jira field '{FIELD_CASES}' not found in the instance.")
    if not machine_fid:
        sys.exit(f"Error: Jira field '{FIELD_MACHINE}' not found in the instance.")
    if not suites_fid:
        sys.exit(f"Error: Jira field '{FIELD_SUITES}' not found in the instance.")
    if not action_fid:
        print(f"[WARN] Field '{FIELD_ACTION}' not found; all tickets will default to action='both'.")

    fids    = [fid for fid in [cases_fid, machine_fid, suites_fid, action_fid] if fid]
    issues  = search_issues(headers, JQL, fids)
    print(f"Found {len(issues)} open ticket(s) in {PROJECT_KEY}.")

    processed = 0
    for issue in issues:
        key    = issue["key"]
        fields = issue["fields"]
        summary = fields.get("summary", "")
        print(f"\n[{key}] {summary}")

        # Check machine match
        machine_names = extract_machine_names(fields.get(machine_fid))
        if not machine_names:
            print(f"  No machine set, skipping.")
            continue
        if current_machine not in machine_names:
            print(f"  Machine {machine_names} != '{current_machine}', skipping.")
            continue

        # Extract cases
        cases = extract_text_lines(fields.get(cases_fid))
        if not cases:
            print(f"  No test cases found, skipping.")
            continue

        # Extract test suites (comma-separated string)
        suites_raw = fields.get(suites_fid) or ""
        if isinstance(suites_raw, str):
            suites = [s.strip() for s in suites_raw.split(",") if s.strip()]
        else:
            suites = extract_text_lines(suites_raw)
        if not suites:
            print(f"  No test suites found, skipping.")
            continue

        # Extract action
        action = extract_action(fields.get(action_fid) if action_fid else None)

        print(f"  suites : {suites}")
        print(f"  cases  : {cases}")
        print(f"  action : {action}")

        suite_sections = []
        overall_rc = 0
        for suite in suites:
            returncode, output = run_bless(suite, cases, action)
            if returncode != 0:
                overall_rc = returncode
            status  = "SUCCESS" if returncode == 0 else f"FAILED (exit {returncode})"
            cmd_str = " ".join(build_bless_cmd(suite, cases, action))
            suite_sections.append(
                f"--- Suite: {suite} ({status}) ---\n"
                f"Command: {cmd_str}\n\n"
                f"{output.strip()}"
            )

        overall_status = "SUCCESS" if overall_rc == 0 else f"FAILED (exit {overall_rc})"
        comment = f"bless_test_results {overall_status}\n\n" + "\n\n".join(suite_sections)

        print(f"  Overall status: {overall_status}. Resolving ticket...")
        add_comment(headers, key, comment)
        matched_transition = transition_issue(headers, key)
        if matched_transition:
            print(f"  Transitioned via '{matched_transition}'.")

        processed += 1

    print(f"\nDone. {processed} ticket(s) processed on '{current_machine}'.")


if __name__ == "__main__":
    main()
