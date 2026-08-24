#!/usr/bin/env python3

"""
Poll the SES Jira project for open bless-test-results tickets and run
bless_test_results for any ticket targeting this machine.

Each ticket's test suites (comma-separated field) each get their own
bless_test_results -t <suite> -f <case> ... invocation.  When all suites
finish the ticket is commented with the command output and transitioned
to Resolved.

Jira fields read per ticket:
  "Components"  - must match --machine
  "Description" - comma-separated -> one run per suite (-t). Format is: $job, ${NML|HIST|BOTH}, $regex1, $regex2, ...
                - example: e3sm_developer_next_gnu, BOTH, *
"""

import argparse, base64, json, os, socket, ssl, subprocess, sys, urllib.error, urllib.parse, urllib.request
import pathlib

JIRA_BASE_URL = "https://e3sm.atlassian.net"
PROJECT_KEY   = "SES"
BLESS_SCRIPT  = "./Tools/bless_test_results"

FIELD_CASES   = "Description"
FIELD_MACHINE = "Components"

JQL = (
    f"project = {PROJECT_KEY} "
    "AND status not in (Resolved, Done, Closed) "
    "ORDER BY created ASC"
)

RESOLVE_TRANSITION_NAMES = ["resolved", "resolve request", "resolve", "done", "close"]

# Fallback root directories (last resort), keyed by lowercase machine name.
# Prefer CIME-derived CIME_OUTPUT_ROOT/J when possible.
MACHINE_ROOTS = {
    "mappy": "/ascldap/users/e3sm-jenkins/acme/scratch/J",
}

###############################################################################
def _setup_cime_path():
###############################################################################
    """
    Add the CIME Python library to sys.path if not already importable.
    Assumes the E3SM repo (containing cime/) lives two directories above this
    script's repo root (i.e. ../../../E3SM relative to this file).
    """
    try:
        import CIME  # noqa: F401 - already on path
        return True
    except ImportError:
        pass
    # Walk up from this file: .../E3SM_test_scripts/jenkins/bless_poll/jira_bless_poller.py
    # → repo root is 2 levels up, then sibling E3SM/cime holds CIME
    script_dir = pathlib.Path(__file__).resolve().parent
    for candidate in [
        script_dir.parent.parent / "E3SM" / "cime",  # sibling layout
        script_dir.parent.parent.parent / "E3SM" / "cime",  # one level deeper
        pathlib.Path("/E3SM/cime"),  # absolute fallback
    ]:
        if (candidate / "CIME").is_dir():
            sys.path.insert(0, str(candidate))
            try:
                import CIME  # noqa: F401
                return True
            except ImportError:
                sys.path.pop(0)
    return False

###############################################################################
def _resolve_root(machine):
###############################################################################
    """
    Determine the bless root directory for *machine* using the following
    priority order:

    1. CIME: instantiate a Machines object and read CIME_OUTPUT_ROOT, then
       append "J".
    2. MACHINE_ROOTS dict: hard-coded fallback values.
    3. Return None (caller must error out or require --root).
    """
    machine_key = machine.lower()

    # 1. Try CIME
    if _setup_cime_path():
        try:
            from CIME.XML.machines import Machines
            m = Machines(machine=machine_key)
            output_root = m.get_value("CIME_OUTPUT_ROOT")
            if output_root:
                print(f"Found working CIME machine {machine_key}!")
                return str(pathlib.Path(output_root) / "J")
        except Exception:
            pass

    else:
        print("WARNING: Could not import CIME, guessing root")

    # 2. Hard-coded fallback
    if machine_key in MACHINE_ROOTS:
        root = MACHINE_ROOTS[machine_key]
        print(f"Guessing root {root}")
        return root

    return None

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
    """
    Return the token string. If token is a readable file path, read it from there.
    """
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
    """
    Return {display_name: field_id} for every field in the Jira instance.
    """
    return {f["name"]: f["id"] for f in _jira_get("/rest/api/3/field", headers)}

###############################################################################
def search_issues(headers, jql, extra_field_ids):
###############################################################################
    """
    Fetch all issues matching jql, requesting summary + extra_field_ids.
    """
    all_issues, start_at = [], 0
    wanted = ",".join(["summary"] + extra_field_ids)
    while True:
        page  = _jira_get("/rest/api/3/search/jql", headers, {
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
    """
    Post a plain-text comment in Atlassian Document Format.
    """
    _jira_post(f"/rest/api/3/issue/{issue_key}/comment", headers, {
        "body": {
            "type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}],
        }
    })

###############################################################################
def transition_issue(headers, issue_key):
###############################################################################
    """
    Try each name in RESOLVE_TRANSITION_NAMES; return matched name or None.
    """
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
    """
    Return non-empty lines from a plain-text or Atlassian Document Format field.
    """
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
    """
    Return a lowercase machine name from any Jira field shape.
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value.lower()
    if isinstance(value, dict):
        name = value.get("value") or value.get("name") or value.get("displayName", "")
        return name.lower() if name else None
    if isinstance(value, list):
        if value:
            return extract_machine_names(value[0])
        else:
            return None
    return str(value).lower()

###############################################################################
def parse_suite(suite):
###############################################################################
    """
    Parse a suite name of the form e3sm_$testid_$branch_$compiler into
    (test_id, compiler).

    The compiler is the last underscore-separated word.
    The branch is the second-to-last word.
    The test_id is everything between the leading 'e3sm_' prefix and '_$branch_$compiler'.
    testid may itself contain underscores.

    The returned test_id is formatted as 'J' + branch.capitalize() + testid.capitalize(),
    matching the convention used by bless_test_results.

    Examples:
      'e3sm_developer_next_gnu'     -> ('JNextDeveloper', 'gnu')
      'e3sm_eamxx_v3_main_oneapi'   -> ('JMainEamxx_v3', 'oneapi')
    """
    parts = suite.split("_")
    # Need at least: e3sm, testid, branch, compiler (4 parts)
    if len(parts) < 4:
        raise ValueError(f"Suite name {suite!r} is too short to parse "
                         f"(expected e3sm_<testid>_<branch>_<compiler>)")

    compiler = parts[-1]
    branch   = parts[-2]
    # Everything between 'e3sm' prefix and '_branch_compiler'
    testid   = "_".join(parts[1:-2])

    if not testid:
        raise ValueError(f"Could not extract testid from suite name {suite!r}")

    test_id = f"J{branch.capitalize()}{testid.capitalize()}"
    return test_id, compiler

###############################################################################
def build_bless_cmd(suite, cases, action, root=None):
###############################################################################
    """
    Return the bless_test_results argv list for one test suite.
    Parses suite into test_id (-t) and compiler (-c).
    -f (force) is always added once.
    Case globs are positional arguments; omitted when cases is ["*"] (all cases).
    If root is provided it is passed as -r <root>.
    """
    test_id, compiler = parse_suite(suite)
    cmd = [BLESS_SCRIPT, "-t", test_id, "-c", compiler, "-f"]
    if root:
        cmd += ["-r", root]
    if cases != ["*"]:
        cmd += cases
    if action == "hists":
        cmd.append("--hist-only")
    elif action == "nmls":
        cmd.append("-n")
    return cmd

###############################################################################
def test_connection(email, token):
###############################################################################
    """
    Verify credentials and confirm the required Jira fields are reachable.
    """
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
def process_action(action, indent="", dry_run=False, root=None):
###############################################################################
    """
    Parse and execute a single bless action string of the form:
      "suite_name, task, case_glob [, case_glob ...]"
    where task is NML, HIST, or BOTH.  Return True on success.
    """
    TASK_MAP = {"NML": "nmls", "HIST": "hists", "BOTH": "both"}

    parts = [p.strip() for p in action.split(",")]
    if len(parts) < 3:
        print(f"{indent}ERROR: action must have at least 3 comma-separated fields "
              f"(suite, task, case): {action!r}")
        return False

    suite    = parts[0]
    task_raw = parts[1].upper()
    cases    = parts[2:]

    if task_raw not in TASK_MAP:
        print(f"{indent}ERROR: unknown task {task_raw!r}; expected one of {list(TASK_MAP.keys())}")
        return False

    try:
        cmd = build_bless_cmd(suite, cases, TASK_MAP[task_raw], root=root)
    except ValueError as exc:
        print(f"{indent}ERROR: {exc}")
        return False

    if dry_run:
        print(f"{indent}DRY-RUN: {' '.join(cmd)}")
        return True

    print(f"{indent}Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = (result.stdout + result.stderr).strip()
    if output:
        print(output)

    if result.returncode != 0:
        print(f"{indent}ERROR: {cmd} failed")
        return False

    print(f"{indent}SUCCESS!")
    return True

###############################################################################
def poll_jira_bless(email, token, machine, dry_run, root):
###############################################################################

    headers = _auth_headers(email, token)
    machine = machine.lower()

    print(f"Polling {JIRA_BASE_URL} | project: {PROJECT_KEY} | machine: {machine}")

    print("Discovering field IDs...")
    field_map   = discover_field_ids(headers)
    cases_fid   = field_map.get(FIELD_CASES)
    machine_fid = field_map.get(FIELD_MACHINE)

    if not cases_fid:
        sys.exit(f"Error: Jira field '{FIELD_CASES}' not found in the instance.\nAvailable fields: {sorted(field_map.keys())}")
    if not machine_fid:
        sys.exit(f"Error: Jira field '{FIELD_MACHINE}' not found in the instance.\nAvailable fields: {sorted(field_map.keys())}")

    fids   = [fid for fid in [cases_fid, machine_fid] if fid]
    issues = search_issues(headers, JQL, fids)
    print(f"Found {len(issues)} open ticket(s) in {PROJECT_KEY}:")

    # Process each open issue
    processed = 0
    errors = 0
    for issue in issues:
        indent  = "  "
        key     = issue["key"]
        fields  = issue["fields"]
        summary = fields.get("summary", "")
        print(f"{indent}[{key}] {summary}")

        # Check issue has machine name match
        indent += "  "
        machine_names = extract_machine_names(fields.get(machine_fid))
        if not machine_names:
            print(f"{indent}SKIP: No machine set")
            continue
        if machine != machine_names:
            print(f"{indent}SKIP: Machine {machine_names} != '{machine}'")
            continue
        else:
            print(f"{indent}FOUND matching ticket: [{key}] {summary}")

        # Get description field
        indent += "  "
        actions = extract_text_lines(fields.get(cases_fid))
        if not actions:
            print(f"{indent}SKIP: No test actions found")
            continue
        else:
            print(f"{indent}FOUND actions: {actions}")

        # Process actions
        indent += "  "
        for action in actions:
            action = action.strip()
            if action:
                print(f"{indent}Processing action: {action}")

                success = process_action(action, indent + "  ", dry_run=dry_run, root=root)
                if success:
                    processed += 1
                else:
                    errors += 1

    print(f"\nDone. Successfully processed {processed} actions on '{machine}'. There were {errors} errors.")
    return processed >= 0 and errors == 0

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
        default=os.environ.get("CIME_MACHINE", socket.gethostname()),
        help="Machine name to match against Jira ticket Machine field "
             "(default: $CIME_MACHINE env var, then current hostname).",
    )

    parser.add_argument(
        "-r", "--root",
        default=None,
        help="Root scratch directory passed to bless_test_results via -r. "
             "Defaults to CIME_OUTPUT_ROOT/J (via CIME), then a built-in "
             f"per-machine table (known: {list(MACHINE_ROOTS.keys())}).",
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
        if args.root is None:
            args.root = _resolve_root(args.machine)
        if args.root is None:
            print(f"ERROR: could not determine a root directory for machine {args.machine!r}. "
                  f"CIME lookup failed and machine is not in the built-in table "
                  f"({list(MACHINE_ROOTS.keys())}). Use -r/--root to specify one.")
            sys.exit(1)
        success = poll_jira_bless(**{k: v for k, v in vars(args).items()
                                     if k != "test_connection"})
    sys.exit(0 if success else 1)

###############################################################################

if __name__ == "__main__":
    _main_func(__doc__)
