#!/usr/bin/env python3

"""
Poll the SES Jira project for open bless-test-results tickets and run
bless_test_results for any ticket targeting this machine.

Each ticket's test suites (comma-separated field) each get their own
bless_test_results -t <suite> -f <case> ... invocation.  When all suites
finish the ticket is commented with the command output and transitioned
to Resolved.

Jira fields read per ticket:
  "List of Test Cases that DIFF'd"        - one regex pattern per line -> -f
  "Machine"                                - must match --machine
  "Test Suites - Developer & Integration"  - comma-separated -> one run per suite (-t)
  "Action"                                 - hists  -> --hist-only
                                             nmls   -> -n
                                             both   -> (no extra flag, default)
"""

import argparse, base64, json, os, socket, ssl, subprocess, sys, urllib.error, urllib.parse, urllib.request
import pathlib

JIRA_BASE_URL = "https://e3sm.atlassian.net"
PROJECT_KEY   = "SES"
BLESS_SCRIPT  = "./Tools/bless_test_results"

FIELD_CASES   = "List of Test Cases that DIFF'd"
FIELD_MACHINE = "Components"
FIELD_SUITES  = "Test Suites - Developer & Integration"
FIELD_ACTION  = "Action"

JQL = (
    f"project = {PROJECT_KEY} "
    "AND status not in (Resolved, Done, Closed) "
    "ORDER BY created ASC"
)

RESOLVE_TRANSITION_NAMES = ["resolved", "resolve request", "resolve", "done", "close"]

###############################################################################
def _ssl_ctx():
###############################################################################
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode    = ssl.CERT_NONE
    return ctx

###############################################################################
def _resolve_token(token):
###############################################################################
    """Return the token string. If token is a readable file path, read it from there."""
    token = token.strip()
    path  = pathlib.Path(token)
    # Treat it as a file path if it looks like one (absolute, home-relative, or
    # contains a path separator) so we can give a useful error if the file is missing.
    looks_like_path = (
        token.startswith(("/", "~", "./", "../"))
        or os.sep in token
    )
    if looks_like_path:
        resolved = path.expanduser()
        if not resolved.is_file():
            sys.exit(f"Error: --token looks like a file path but '{resolved}' does not exist.")
        return resolved.read_text().strip()
    if path.is_file():
        return path.read_text().strip()
    return token

###############################################################################
def _auth_headers(email, token):
###############################################################################
    creds = base64.b64encode(f"{email.strip()}:{_resolve_token(token)}".encode()).decode()
    return {
        "Authorization": f"Basic {creds}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }

###############################################################################
def _http(method, path, headers, payload=None, params=None):
###############################################################################
    url = f"{JIRA_BASE_URL}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(payload).encode() if payload is not None else None
    req  = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=_ssl_ctx()) as resp:
            body = resp.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {exc.code} {method} {url}: {body}") from exc

###############################################################################
def _jira_get(path, headers, params=None):
###############################################################################
    return _http("GET", path, headers, params=params)

###############################################################################
def _jira_post(path, headers, payload):
###############################################################################
    return _http("POST", path, headers, payload=payload)

###############################################################################
def discover_field_ids(headers):
###############################################################################
    """Return {display_name: field_id} for every field in the Jira instance."""
    return {f["name"]: f["id"] for f in _jira_get("/rest/api/3/field", headers)}

###############################################################################
def search_issues(headers, jql, extra_field_ids):
###############################################################################
    """Fetch all issues matching jql, requesting summary + extra_field_ids."""
    all_issues, start_at = [], 0
    wanted = ",".join(["summary"] + extra_field_ids)
    while True:
        page  = _jira_get("/rest/api/3/search", headers, {
            "jql": jql, "startAt": start_at, "maxResults": 50, "fields": wanted,
        })
        chunk = page.get("issues", [])
        all_issues.extend(chunk)
        start_at += len(chunk)
        if start_at >= page.get("total", 0):
            break
    return all_issues

###############################################################################
def add_comment(headers, issue_key, text):
###############################################################################
    """Post a plain-text comment in Atlassian Document Format."""
    _jira_post(f"/rest/api/3/issue/{issue_key}/comment", headers, {
        "body": {
            "type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}],
        }
    })

###############################################################################
def transition_issue(headers, issue_key):
###############################################################################
    """Try each name in RESOLVE_TRANSITION_NAMES; return matched name or None."""
    data       = _jira_get(f"/rest/api/3/issue/{issue_key}/transitions", headers)
    name_to_id = {t["name"].lower(): t["id"] for t in data.get("transitions", [])}
    for name in RESOLVE_TRANSITION_NAMES:
        if name in name_to_id:
            _jira_post(f"/rest/api/3/issue/{issue_key}/transitions", headers,
                       {"transition": {"id": name_to_id[name]}})
            return name
    print(f"  [{issue_key}] WARNING: no resolve transition found. "
          f"Available: {list(name_to_id.keys())}")
    return None

###############################################################################
def extract_text_lines(value):
###############################################################################
    """Return non-empty lines from a plain-text or Atlassian Document Format field."""
    if value is None:
        return []
    if isinstance(value, str):
        return [ln.strip() for ln in value.splitlines() if ln.strip()]
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

###############################################################################
def extract_machine_names(value):
###############################################################################
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

###############################################################################
def extract_action(value):
###############################################################################
    """
    Map a checkbox/select Jira field to 'hists', 'nmls', or 'both'.
    Both checkboxes checked => 'both'.  Missing/unrecognised => 'both'.
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
        selected = {(item.get("value") or item.get("name", "")).lower().strip()
                    for item in value if isinstance(item, dict)}
        if "hists" in selected and "nmls" in selected:
            return "both"
        if "hists" in selected:
            return "hists"
        if "nmls" in selected:
            return "nmls"
        return "both"
    return "both"

###############################################################################
def build_bless_cmd(suite, cases, action):
###############################################################################
    """Return the bless_test_results argv list for one test suite."""
    cmd = [BLESS_SCRIPT, "-t", suite]
    for case in cases:
        cmd += ["-f", case]
    if action == "hists":
        cmd.append("--hist-only")
    elif action == "nmls":
        cmd.append("-n")
    return cmd

###############################################################################
def test_connection(email, token):
###############################################################################
    """Verify credentials and confirm the required Jira fields are reachable."""
    token   = _resolve_token(token)
    headers = _auth_headers(email, token)
    email   = email.strip()

    print(f"Testing connection to {JIRA_BASE_URL} ...")
    print(f"  Email    : {email}")

    # Verify authentication via the /myself endpoint
    try:
        myself = _jira_get("/rest/api/3/myself", headers)
        print(f"  Auth OK  : logged in as {myself.get('displayName')} ({myself.get('emailAddress')})")
    except RuntimeError as exc:
        print(f"  Auth FAIL: {exc}")
        return False

    # Confirm the project exists
    try:
        proj = _jira_get(f"/rest/api/3/project/{PROJECT_KEY}", headers)
        print(f"  Project  : {proj.get('name')} ({PROJECT_KEY}) found")
        return True
    except RuntimeError as exc:
        print(f"  Project FAIL: {exc}")
        return False

###############################################################################
def poll_jira_bless(email, token, machine, dry_run):
###############################################################################

    headers = _auth_headers(email, token)
    machine = machine.lower()

    print(f"Polling {JIRA_BASE_URL} | project: {PROJECT_KEY} | machine: {machine}")

    print("Discovering field IDs...")
    field_map   = discover_field_ids(headers)
    #cases_fid   = field_map.get(FIELD_CASES)
    machine_fid = field_map.get(FIELD_MACHINE)
    #suites_fid  = field_map.get(FIELD_SUITES)
    #action_fid  = field_map.get(FIELD_ACTION)

    # if not cases_fid:
    #     sys.exit(f"Error: Jira field '{FIELD_CASES}' not found in the instance.\nAvailable fields: {sorted(field_map.keys())}")
    if not machine_fid:
        sys.exit(f"Error: Jira field '{FIELD_MACHINE}' not found in the instance.\nAvailable fields: {sorted(field_map.keys())}")
    # if not suites_fid:
    #     sys.exit(f"Error: Jira field '{FIELD_SUITES}' not found in the instance.\nAvailable fields: {sorted(field_map.keys())}")
    # if not action_fid:
    #     print(f"[WARN] Field '{FIELD_ACTION}' not found; defaulting action to 'both' for all tickets.")

    fids   = [fid for fid in [machine_fid] if fid] #[cases_fid, machine_fid, suites_fid, action_fid] if fid]
    issues = search_issues(headers, JQL, fids)
    print(f"Found {len(issues)} open ticket(s) in {PROJECT_KEY}.")

    processed = 0
    for issue in issues:
        key     = issue["key"]
        fields  = issue["fields"]
        summary = fields.get("summary", "")
        print(f"\n[{key}] {summary}")

        machine_names = extract_machine_names(fields.get(machine_fid))
        if not machine_names:
            print("  No machine set, skipping.")
            continue
        if machine not in machine_names:
            print(f"  Machine {machine_names} != '{machine}', skipping.")
            continue

        cases = extract_text_lines(fields.get(cases_fid))
        if not cases:
            print("  No test cases found, skipping.")
            continue

        suites_raw = fields.get(suites_fid) or ""
        suites = ([s.strip() for s in suites_raw.split(",") if s.strip()]
                  if isinstance(suites_raw, str)
                  else extract_text_lines(suites_raw))
        if not suites:
            print("  No test suites found, skipping.")
            continue

        action = extract_action(fields.get(action_fid) if action_fid else None)

        print(f"  suites : {suites}")
        print(f"  cases  : {cases}")
        print(f"  action : {action}")

        suite_sections, overall_rc = [], 0
        for suite in suites:
            cmd = build_bless_cmd(suite, cases, action)
            if dry_run:
                print(f"  DRY-RUN: {' '.join(cmd)}")
                suite_sections.append(f"--- Suite: {suite} (DRY-RUN) ---\nCommand: {' '.join(cmd)}")
            else:
                print(f"  Running: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    overall_rc = result.returncode
                status = "SUCCESS" if result.returncode == 0 else f"FAILED (exit {result.returncode})"
                suite_sections.append(
                    f"--- Suite: {suite} ({status}) ---\n"
                    f"Command: {' '.join(cmd)}\n\n"
                    f"{(result.stdout + result.stderr).strip()}"
                )

        if dry_run:
            print("  DRY-RUN: skipping Jira comment and transition.")
        else:
            overall_status = "SUCCESS" if overall_rc == 0 else f"FAILED (exit {overall_rc})"
            comment = f"bless_test_results {overall_status}\n\n" + "\n\n".join(suite_sections)
            print(f"  Overall status: {overall_status}. Resolving ticket...")
            add_comment(headers, key, comment)
            matched = transition_issue(headers, key)
            if matched:
                print(f"  Transitioned via '{matched}'.")

        processed += 1

    print(f"\nDone. {processed} ticket(s) processed on '{machine}'.")
    return processed >= 0

###############################################################################
def parse_command_line(args, description):
###############################################################################
    parser = argparse.ArgumentParser(
        usage="""\n{0} --email <email> --token <token> [--machine <name>]
OR
{0} --help

\033[1mEXAMPLES:\033[0m
    \033[1;32m# Poll Jira for bless requests on the current machine\033[0m
    > {0} --email you@example.com --token <api-token>

    \033[1;32m# Specify a machine name explicitly\033[0m
    > {0} --email you@example.com --token <api-token> --machine mappy

    \033[1;32m# Dry-run: print commands without executing or modifying tickets\033[0m
    > {0} --email you@example.com --token <api-token> --dry-run

    \033[1;32m# Test credentials and confirm all required Jira fields exist\033[0m
    > {0} --email you@example.com --token <api-token> --test-connection
""".format(pathlib.Path(args[0]).name),
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-e", "--email",
        required=True,
        help="Atlassian account email for Jira authentication. "
             "Get an API token at https://id.atlassian.com/manage-profile/security/api-tokens",
    )

    parser.add_argument(
        "-t", "--token",
        required=True,
        help="Atlassian API token, or a path to a file containing the token.",
    )

    parser.add_argument(
        "-m", "--machine",
        default=socket.gethostname(),
        help="Machine name to match against Jira ticket Machine field "
             "(default: current hostname).",
    )

    parser.add_argument(
        "-n", "--dry-run",
        default=False,
        action="store_true",
        help="Print the bless commands that would be run without executing them "
             "or modifying any Jira tickets.",
    )

    parser.add_argument(
        "--test-connection",
        default=False,
        action="store_true",
        help="Test authentication and confirm all required Jira fields are reachable, then exit.",
    )

    return parser.parse_args(args[1:])

###############################################################################
def _main_func(description):
###############################################################################
    args = parse_command_line(sys.argv, description)
    if args.test_connection:
        success = test_connection(args.email, args.token)
    else:
        success = poll_jira_bless(**{k: v for k, v in vars(args).items()
                                     if k != "test_connection"})
    sys.exit(0 if success else 1)

###############################################################################

if __name__ == "__main__":
    _main_func(__doc__)
