#!/usr/bin/env python3

"""
Unit tests for jira_bless_poller.py.

All Jira API calls and subprocess invocations are replaced with fakes so
no network access or real bless_test_results binary is needed.

Run with:
    python3 -m pytest test_jira_bless_poller.py -v
or:
    python3 test_jira_bless_poller.py
"""

import getpass
import os, sys, tempfile, unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(__file__))
import jira_bless_poller as jbp

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_issue(key, machine_name, description, summary="Test bless request"):
    """Build a minimal fake Jira issue dict as returned by search_issues."""
    return {
        "key": key,
        "fields": {
            "summary": summary,
            "description": description,
            "components": [{"name": machine_name}] if machine_name else [],
        },
    }

FAKE_FIELD_MAP = {"Description": "description", "Components": "components"}

def _make_parsed_args(**overrides):
    """Return an argparse-like namespace suitable for feeding to _main_func."""
    import argparse
    defaults = dict(
        email="e@e.com", token="tok", machine="mappy",
        root=None, dry_run=False, bless_dry_run=False,
        tickets=None, test_connection=False, user=None, action=None,
        no_transition=False, close_ticket=None, comment=None,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)

###############################################################################
class TestResolveToken(unittest.TestCase):
###############################################################################

    def test_literal_token(self):
        self.assertEqual(jbp._resolve_token("mytoken123"), "mytoken123")

    def test_literal_token_strips_whitespace(self):
        self.assertEqual(jbp._resolve_token("  mytoken  "), "mytoken")

    def test_reads_from_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("  filetoken\n")
            name = f.name
        try:
            self.assertEqual(jbp._resolve_token(name), "filetoken")
        finally:
            os.unlink(name)

    def test_path_like_missing_file_exits(self):
        with self.assertRaises(SystemExit):
            jbp._resolve_token("/nonexistent/path/to/token")

    def test_tilde_path_missing_file_exits(self):
        with self.assertRaises(SystemExit):
            jbp._resolve_token("~/nonexistent_jira_token_xyz")

###############################################################################
class TestExtractTextLines(unittest.TestCase):
###############################################################################

    def test_none_returns_empty(self):
        self.assertEqual(jbp.extract_text_lines(None), [])

    def test_plain_string(self):
        self.assertEqual(jbp.extract_text_lines("a\nb\nc"), ["a", "b", "c"])

    def test_blank_lines_ignored(self):
        self.assertEqual(jbp.extract_text_lines("a\n\n  \nb"), ["a", "b"])

    def test_single_line(self):
        self.assertEqual(jbp.extract_text_lines("only one"), ["only one"])

    def test_adf_doc(self):
        adf = {
            "type": "doc", "version": 1,
            "content": [
                {"type": "paragraph", "content": [
                    {"type": "text", "text": "line one"},
                ]},
                {"type": "paragraph", "content": [
                    {"type": "text", "text": "line two"},
                ]},
            ],
        }
        self.assertEqual(jbp.extract_text_lines(adf), ["line one", "line two"])

    def test_adf_skips_non_text_nodes(self):
        adf = {
            "type": "doc", "version": 1,
            "content": [
                {"type": "paragraph", "content": [
                    {"type": "hardBreak"},
                    {"type": "text", "text": "hello"},
                ]},
            ],
        }
        self.assertEqual(jbp.extract_text_lines(adf), ["hello"])

###############################################################################
class TestExtractMachineNames(unittest.TestCase):
###############################################################################

    def test_none_returns_none(self):
        self.assertIsNone(jbp.extract_machine_names(None))

    def test_string_lowercased(self):
        self.assertEqual(jbp.extract_machine_names("Mappy"), "mappy")

    def test_dict_with_name(self):
        self.assertEqual(jbp.extract_machine_names({"name": "Chrysalis"}), "chrysalis")

    def test_dict_with_value(self):
        self.assertEqual(jbp.extract_machine_names({"value": "Frontier"}), "frontier")

    def test_dict_with_display_name(self):
        self.assertEqual(jbp.extract_machine_names({"displayName": "PM-CPU"}), "pm-cpu")

    def test_list_uses_first_element(self):
        self.assertEqual(jbp.extract_machine_names([{"name": "Mappy"}, {"name": "other"}]), "mappy")

    def test_empty_list_returns_none(self):
        self.assertIsNone(jbp.extract_machine_names([]))

###############################################################################
class TestParseSuite(unittest.TestCase):
###############################################################################

    def test_simple(self):
        self.assertEqual(jbp.parse_suite("e3sm_developer_next_gnu"), ("JNextDeveloper", "gnu"))

    def test_testid_with_underscores(self):
        self.assertEqual(jbp.parse_suite("e3sm_eamxx_v3_main_oneapi"), ("JMainEamxx_v3", "oneapi"))

    def test_compiler_is_last_word(self):
        _, compiler = jbp.parse_suite("e3sm_any_test_id_here_next_oneapi")
        self.assertEqual(compiler, "oneapi")

    def test_branch_is_second_to_last(self):
        test_id, _ = jbp.parse_suite("e3sm_any_test_id_here_next_oneapi")
        self.assertTrue(test_id.startswith("JNext"))

    def test_j_prefix(self):
        test_id, _ = jbp.parse_suite("e3sm_developer_next_gnu")
        self.assertTrue(test_id.startswith("J"))

    def test_branch_capitalized(self):
        test_id, _ = jbp.parse_suite("e3sm_developer_next_gnu")
        self.assertIn("Next", test_id)

    def test_testid_capitalized(self):
        test_id, _ = jbp.parse_suite("e3sm_developer_next_gnu")
        self.assertIn("Developer", test_id)

    def test_too_short_raises(self):
        with self.assertRaises(ValueError):
            jbp.parse_suite("e3sm_gnu")

    def test_three_parts_raises(self):
        # Needs at least 4 parts: e3sm, testid, branch, compiler
        with self.assertRaises(ValueError):
            jbp.parse_suite("e3sm_next_gnu")

###############################################################################
class TestBuildBlessCmd(unittest.TestCase):
###############################################################################

    def test_root_passed_to_command(self):
        cmd = jbp.build_bless_cmd("e3sm_developer_next_gnu", ["ERS*"], "both", root="/my/root")
        self.assertIn("-r", cmd)
        self.assertEqual(cmd[cmd.index("-r") + 1], "/my/root")

    def test_no_root_omits_r_flag(self):
        cmd = jbp.build_bless_cmd("e3sm_developer_next_gnu", ["ERS*"], "both", root=None)
        self.assertNotIn("-r", cmd)

    def test_action_both(self):
        cmd = jbp.build_bless_cmd("e3sm_developer_next_gnu", ["ERS*"], "both")
        self.assertIn("-t", cmd)
        self.assertEqual(cmd[cmd.index("-t") + 1], "JNextDeveloper")
        self.assertIn("-c", cmd)
        self.assertEqual(cmd[cmd.index("-c") + 1], "gnu")
        self.assertIn("-f", cmd)
        self.assertIn("'ERS*'", cmd)
        self.assertNotIn("--hist-only", cmd)
        self.assertNotIn("-n", cmd)

    def test_force_flag_always_present(self):
        for cases in [["*"], ["ERS*"], ["ERS*", "SMS*"]]:
            cmd = jbp.build_bless_cmd("e3sm_developer_next_gnu", cases, "both")
            self.assertEqual(cmd.count("-f"), 1, f"Expected exactly one -f for cases={cases}")

    def test_action_hists(self):
        cmd = jbp.build_bless_cmd("e3sm_developer_next_gnu", ["ERS*"], "hists")
        self.assertIn("--hist-only", cmd)
        self.assertNotIn("-n", cmd)

    def test_action_nmls(self):
        cmd = jbp.build_bless_cmd("e3sm_developer_next_gnu", ["ERS*"], "nmls")
        self.assertIn("-n", cmd)
        self.assertNotIn("--hist-only", cmd)

    def test_multiple_cases(self):
        # Cases are positional args after -f, not repeated -f flags
        cmd = jbp.build_bless_cmd("e3sm_s_next_gnu", ["ERS*", "SMS*", "PET*"], "both")
        self.assertEqual(cmd.count("-f"), 1)
        f_idx = cmd.index("-f")
        self.assertEqual(cmd[f_idx + 1], "'ERS*'")
        self.assertEqual(cmd[f_idx + 2], "'SMS*'")
        self.assertEqual(cmd[f_idx + 3], "'PET*'")

    def test_wildcard_case_omits_case_args(self):
        cmd = jbp.build_bless_cmd("e3sm_developer_next_gnu", ["*"], "both")
        self.assertIn("-f", cmd)
        self.assertNotIn("*", cmd)

    def test_wildcard_case_with_action_still_adds_flag(self):
        cmd = jbp.build_bless_cmd("e3sm_developer_next_gnu", ["*"], "hists")
        self.assertIn("-f", cmd)
        self.assertNotIn("*", cmd)
        self.assertIn("--hist-only", cmd)

    def test_suite_comes_after_t_flag(self):
        cmd = jbp.build_bless_cmd("e3sm_dev_next_gnu", ["*"], "both")
        self.assertEqual(cmd[cmd.index("-t") + 1], "JNextDev")

    def test_bless_dry_run_adds_dry_run_flag(self):
        cmd = jbp.build_bless_cmd("e3sm_developer_next_gnu", ["ERS*"], "both", bless_dry_run=True)
        self.assertIn("--dry-run", cmd)

    def test_no_bless_dry_run_omits_dry_run_flag(self):
        cmd = jbp.build_bless_cmd("e3sm_developer_next_gnu", ["ERS*"], "both", bless_dry_run=False)
        self.assertNotIn("--dry-run", cmd)

    def test_excludes_added_to_command(self):
        cmd = jbp.build_bless_cmd("e3sm_developer_next_gnu", ["ERS*"], "both", excludes=["ERS_Ls*"])
        self.assertIn("--exclude", cmd)
        exclude_idx = cmd.index("--exclude")
        self.assertEqual(cmd[exclude_idx + 1], "ERS_Ls*")

    def test_multiple_excludes_added_to_command(self):
        cmd = jbp.build_bless_cmd("e3sm_developer_next_gnu", ["ERS*"], "both", excludes=["ERS_Ls*", "SMS*"])
        self.assertIn("--exclude", cmd)
        exclude_idx = cmd.index("--exclude")
        self.assertEqual(cmd[exclude_idx + 1], "ERS_Ls*")
        self.assertEqual(cmd[exclude_idx + 2], "SMS*")

    def test_no_excludes_omits_exclude_flag(self):
        cmd = jbp.build_bless_cmd("e3sm_developer_next_gnu", ["ERS*"], "both", excludes=None)
        self.assertNotIn("--exclude", cmd)

###############################################################################
class TestProcessAction(unittest.TestCase):
###############################################################################

    def test_root_forwarded_to_build_cmd(self):
        with patch.object(jbp, "_invoke_bless", return_value=True) as mock_invoke:
            jbp.process_action("e3sm_developer_next_gnu, BOTH, ERS*", root="/custom/root")
            _, _, _, root, _ = mock_invoke.call_args[0]
            self.assertEqual(root, "/custom/root")

    def test_too_few_parts_returns_false(self):
        self.assertFalse(jbp.process_action("only_suite, NML"))

    def test_bad_task_returns_false(self):
        self.assertFalse(jbp.process_action("e3sm_suite_gnu, BADTASK, ERS*"))

    def test_bad_suite_format_returns_false(self):
        # Suite with too few parts to parse
        self.assertFalse(jbp.process_action("badname, BOTH, ERS*"))

    def test_dry_run_returns_true_without_running(self):
        with patch.object(jbp, "_invoke_bless") as mock_invoke:
            result = jbp.process_action("e3sm_dev_suite_gnu, BOTH, ERS*", dry_run=True)
            self.assertTrue(result)
            mock_invoke.assert_not_called()

    def test_nml_task_passes_nmls_action(self):
        with patch.object(jbp, "_invoke_bless", return_value=True) as mock_invoke:
            result = jbp.process_action("e3sm_dev_suite_gnu, NML, ERS*")
            self.assertTrue(result)
            _, _, action, _, _ = mock_invoke.call_args[0]
            self.assertEqual(action, "nmls")

    def test_hist_task_passes_hists_action(self):
        with patch.object(jbp, "_invoke_bless", return_value=True) as mock_invoke:
            result = jbp.process_action("e3sm_dev_suite_gnu, HIST, SMS*")
            self.assertTrue(result)
            _, _, action, _, _ = mock_invoke.call_args[0]
            self.assertEqual(action, "hists")

    def test_both_task_passes_both_action(self):
        with patch.object(jbp, "_invoke_bless", return_value=True) as mock_invoke:
            result = jbp.process_action("e3sm_dev_suite_gnu, BOTH, *")
            self.assertTrue(result)
            _, _, action, _, _ = mock_invoke.call_args[0]
            self.assertEqual(action, "both")

    def test_multiple_case_globs(self):
        with patch.object(jbp, "_invoke_bless", return_value=True) as mock_invoke:
            jbp.process_action("e3sm_dev_suite_gnu, BOTH, ERS*, SMS*, PET*")
            _, cases, _, _, _ = mock_invoke.call_args[0]
            self.assertEqual(cases, ["ERS*", "SMS*", "PET*"])

    def test_command_failure_returns_false(self):
        with patch.object(jbp, "_invoke_bless", return_value=False):
            self.assertFalse(jbp.process_action("e3sm_dev_suite_gnu, BOTH, ERS*"))

    def test_task_case_insensitive(self):
        with patch.object(jbp, "_invoke_bless", return_value=True) as mock_invoke:
            result = jbp.process_action("e3sm_dev_suite_gnu, hist, ERS*")
            self.assertTrue(result)
            _, _, action, _, _ = mock_invoke.call_args[0]
            self.assertEqual(action, "hists")

    def test_compiler_extracted_from_suite(self):
        with patch.object(jbp, "_invoke_bless", return_value=True) as mock_invoke:
            jbp.process_action("e3sm_developer_next_gnu, BOTH, *")
            suite, _, _, _, _ = mock_invoke.call_args[0]
            self.assertEqual(suite, "e3sm_developer_next_gnu")

    def test_bless_dry_run_calls_invoke_with_flag(self):
        with patch.object(jbp, "_invoke_bless", return_value=True) as mock_invoke:
            result = jbp.process_action("e3sm_dev_suite_gnu, BOTH, ERS*", bless_dry_run=True)
            self.assertTrue(result)
            mock_invoke.assert_called_once()
            self.assertTrue(mock_invoke.call_args[1]["bless_dry_run"])

    def test_dry_run_takes_priority_over_bless_dry_run(self):
        # --dry-run (print only) should prevent _invoke_bless from being called at all,
        # even if --bless-dry-run is also set.
        with patch.object(jbp, "_invoke_bless") as mock_invoke:
            result = jbp.process_action("e3sm_dev_suite_gnu, BOTH, ERS*",
                                        dry_run=True, bless_dry_run=True)
            self.assertTrue(result)
            mock_invoke.assert_not_called()

    def test_excludes_parsed_from_action_string(self):
        with patch.object(jbp, "_invoke_bless", return_value=True) as mock_invoke:
            jbp.process_action("e3sm_dev_suite_gnu, BOTH, ERS*, -ERS_Ls*")
            args, kwargs = mock_invoke.call_args
            self.assertEqual(kwargs.get("excludes"), ["ERS_Ls*"])

    def test_multiple_excludes_parsed(self):
        with patch.object(jbp, "_invoke_bless", return_value=True) as mock_invoke:
            jbp.process_action("e3sm_dev_suite_gnu, BOTH, ERS*, -ERS_Ls*, -SMS*")
            args, kwargs = mock_invoke.call_args
            self.assertEqual(kwargs.get("excludes"), ["ERS_Ls*", "SMS*"])

    def test_excludes_separated_from_includes(self):
        with patch.object(jbp, "_invoke_bless", return_value=True) as mock_invoke:
            jbp.process_action("e3sm_dev_suite_gnu, BOTH, ERS*, SMS*, -ERS_Ls*")
            args, kwargs = mock_invoke.call_args
            cases = args[1]  # cases is 2nd positional arg
            self.assertEqual(cases, ["ERS*", "SMS*"])
            self.assertEqual(kwargs.get("excludes"), ["ERS_Ls*"])

    def test_no_excludes_passes_none(self):
        with patch.object(jbp, "_invoke_bless", return_value=True) as mock_invoke:
            jbp.process_action("e3sm_dev_suite_gnu, BOTH, ERS*")
            args, kwargs = mock_invoke.call_args
            self.assertIsNone(kwargs.get("excludes"))

###############################################################################
class TestInvokeBless(unittest.TestCase):
###############################################################################

    _SUITE = "e3sm_developer_next_gnu"   # test_id=JNextDeveloper, compiler=gnu

    def _mock_cime(self, return_value=True):
        """Return a context manager that provides a mock CIME bless function."""
        mock_fn = MagicMock(return_value=return_value)
        modules = {
            "CIME":                    MagicMock(),
            "CIME.bless_test_results": MagicMock(bless_test_results=mock_fn),
            "CIME.utils":              MagicMock(CIMEError=Exception),
        }
        return patch.dict("sys.modules", modules), mock_fn

    def test_cime_api_used_when_available(self):
        cm, mock_fn = self._mock_cime(return_value=True)
        with cm, patch.object(jbp, "_setup_cime_path", return_value=True):
            result = jbp._invoke_bless(self._SUITE, ["ERS*"], "both", "/root/J", "")
        self.assertTrue(result)
        mock_fn.assert_called_once()

    def test_cime_api_receives_correct_params(self):
        cm, mock_fn = self._mock_cime(return_value=True)
        with cm, patch.object(jbp, "_setup_cime_path", return_value=True):
            jbp._invoke_bless(self._SUITE, ["ERS*", "SMS*"], "nmls", "/root/J", "")
        kwargs = mock_fn.call_args[1]
        self.assertEqual(kwargs["test_root"], "/root/J")
        self.assertEqual(kwargs["compiler"], "gnu")
        self.assertEqual(kwargs["test_id"], "JNextDeveloper")
        self.assertTrue(kwargs["namelists_only"])
        self.assertFalse(kwargs["hist_only"])
        self.assertTrue(kwargs["force"])
        self.assertEqual(kwargs["bless_tests"], ["ERS*", "SMS*"])
        self.assertFalse(kwargs["dry_run"])

    def test_cime_bless_dry_run_forwarded(self):
        cm, mock_fn = self._mock_cime(return_value=True)
        with cm, patch.object(jbp, "_setup_cime_path", return_value=True):
            jbp._invoke_bless(self._SUITE, ["ERS*"], "both", "/root/J", "", bless_dry_run=True)
        self.assertTrue(mock_fn.call_args[1]["dry_run"])

    def test_cime_wildcard_passes_none_bless_tests(self):
        cm, mock_fn = self._mock_cime(return_value=True)
        with cm, patch.object(jbp, "_setup_cime_path", return_value=True):
            jbp._invoke_bless(self._SUITE, ["*"], "both", "/root/J", "")
        self.assertIsNone(mock_fn.call_args[1]["bless_tests"])

    def test_cime_hist_only_param(self):
        cm, mock_fn = self._mock_cime(return_value=True)
        with cm, patch.object(jbp, "_setup_cime_path", return_value=True):
            jbp._invoke_bless(self._SUITE, ["*"], "hists", "/root/J", "")
        kwargs = mock_fn.call_args[1]
        self.assertTrue(kwargs["hist_only"])
        self.assertFalse(kwargs["namelists_only"])

    def test_cime_excludes_forwarded(self):
        cm, mock_fn = self._mock_cime(return_value=True)
        with cm, patch.object(jbp, "_setup_cime_path", return_value=True):
            jbp._invoke_bless(self._SUITE, ["ERS*"], "both", "/root/J", "", excludes=["ERS_Ls*"])
        kwargs = mock_fn.call_args[1]
        self.assertEqual(kwargs["exclude"], ["ERS_Ls*"])

    def test_subprocess_fallback_with_excludes(self):
        mock_result = MagicMock(returncode=0, stdout="", stderr="")
        with patch.object(jbp, "_setup_cime_path", return_value=False), \
             patch("subprocess.run", return_value=mock_result) as mock_run:
            jbp._invoke_bless(self._SUITE, ["ERS*"], "both", "/root/J", "", excludes=["ERS_Ls*"])
        cmd = mock_run.call_args[0][0]
        self.assertIn("--exclude", cmd)
        exclude_idx = cmd.index("--exclude")
        self.assertEqual(cmd[exclude_idx + 1], "ERS_Ls*")

    def test_subprocess_fallback_when_cime_unavailable(self):
        mock_result = MagicMock(returncode=0, stdout="", stderr="")
        with patch.object(jbp, "_setup_cime_path", return_value=False), \
             patch("subprocess.run", return_value=mock_result) as mock_run:
            result = jbp._invoke_bless(self._SUITE, ["ERS*"], "both", "/root/J", "")
        self.assertTrue(result)
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        self.assertIn("-t", cmd)
        self.assertIn("JNextDeveloper", cmd)
        self.assertIn("-c", cmd)
        self.assertIn("gnu", cmd)
        self.assertIn("-f", cmd)

    def test_subprocess_fallback_nmls(self):
        mock_result = MagicMock(returncode=0, stdout="", stderr="")
        with patch.object(jbp, "_setup_cime_path", return_value=False), \
             patch("subprocess.run", return_value=mock_result) as mock_run:
            jbp._invoke_bless(self._SUITE, ["ERS*"], "nmls", "/root/J", "")
        cmd = mock_run.call_args[0][0]
        self.assertIn("-n", cmd)
        self.assertNotIn("--hist-only", cmd)

    def test_subprocess_fallback_hists(self):
        mock_result = MagicMock(returncode=0, stdout="", stderr="")
        with patch.object(jbp, "_setup_cime_path", return_value=False), \
             patch("subprocess.run", return_value=mock_result) as mock_run:
            jbp._invoke_bless(self._SUITE, ["ERS*"], "hists", "/root/J", "")
        cmd = mock_run.call_args[0][0]
        self.assertIn("--hist-only", cmd)
        self.assertNotIn("-n", cmd)

    def test_subprocess_fallback_wildcard_omits_cases(self):
        mock_result = MagicMock(returncode=0, stdout="", stderr="")
        with patch.object(jbp, "_setup_cime_path", return_value=False), \
             patch("subprocess.run", return_value=mock_result) as mock_run:
            jbp._invoke_bless(self._SUITE, ["*"], "both", "/root/J", "")
        cmd = mock_run.call_args[0][0]
        self.assertNotIn("*", cmd)
        self.assertIn("-f", cmd)

    def test_subprocess_returns_false_on_nonzero_exit(self):
        mock_result = MagicMock(returncode=1, stdout="", stderr="error")
        with patch.object(jbp, "_setup_cime_path", return_value=False), \
             patch("subprocess.run", return_value=mock_result):
            result = jbp._invoke_bless(self._SUITE, ["ERS*"], "both", "/root/J", "")
        self.assertFalse(result)

    def test_subprocess_bless_dry_run_adds_flag(self):
        mock_result = MagicMock(returncode=0, stdout="", stderr="")
        with patch.object(jbp, "_setup_cime_path", return_value=False), \
             patch("subprocess.run", return_value=mock_result) as mock_run:
            jbp._invoke_bless(self._SUITE, ["ERS*"], "both", "/root/J", "", bless_dry_run=True)
        cmd = mock_run.call_args[0][0]
        self.assertIn("--dry-run", cmd)

    def test_subprocess_no_bless_dry_run_omits_flag(self):
        mock_result = MagicMock(returncode=0, stdout="", stderr="")
        with patch.object(jbp, "_setup_cime_path", return_value=False), \
             patch("subprocess.run", return_value=mock_result) as mock_run:
            jbp._invoke_bless(self._SUITE, ["ERS*"], "both", "/root/J", "", bless_dry_run=False)
        cmd = mock_run.call_args[0][0]
        self.assertNotIn("--dry-run", cmd)

###############################################################################
class TestUserSubstitution(unittest.TestCase):
###############################################################################

    def _run_main(self, extra_args, root_from_resolve, user=None):
        """
        Exercise _main_func's user-substitution logic without real Jira or bless.
        Returns the root that would be passed to poll_jira_bless.
        """
        base_args = ["prog", "-e", "e@e.com", "-t", "tok", "-m", "mappy"]
        if user:
            base_args += ["-u", user]
        base_args += extra_args

        captured = {}
        def fake_poll(**kwargs):
            captured.update(kwargs)
            return True

        with patch.object(jbp, "parse_command_line",
                          return_value=_make_namespace(base_args, root_from_resolve)), \
             patch.object(jbp, "_resolve_root", return_value=root_from_resolve), \
             patch.object(jbp, "poll_jira_bless", side_effect=fake_poll), \
             patch("sys.exit"):
            jbp._main_func("test")

        return captured.get("root")

    def test_user_replaces_current_user_in_root(self):
        current = getpass.getuser()
        root = f"/home/{current}/scratch/J"
        with patch("getpass.getuser", return_value=current), \
             patch.object(jbp, "_resolve_root", return_value=root), \
             patch.object(jbp, "poll_jira_bless", return_value=True) as mock_poll, \
             patch("sys.exit"):
            args = _make_parsed_args(root=root, user="e3sm-jenkins")
            with patch.object(jbp, "parse_command_line", return_value=args):
                jbp._main_func("test")
        actual_root = mock_poll.call_args[1]["root"]
        self.assertEqual(actual_root, f"/home/e3sm-jenkins/scratch/J")

    def test_no_user_leaves_root_unchanged(self):
        current = getpass.getuser()
        root = f"/home/{current}/scratch/J"
        with patch.object(jbp, "_resolve_root", return_value=root), \
             patch.object(jbp, "poll_jira_bless", return_value=True) as mock_poll, \
             patch("sys.exit"):
            args = _make_parsed_args(root=root, user=None)
            with patch.object(jbp, "parse_command_line", return_value=args):
                jbp._main_func("test")
        actual_root = mock_poll.call_args[1]["root"]
        self.assertEqual(actual_root, root)

    def test_user_replaces_all_occurrences(self):
        current = getpass.getuser()
        root = f"/home/{current}/data/{current}/J"
        with patch("getpass.getuser", return_value=current), \
             patch.object(jbp, "_resolve_root", return_value=root), \
             patch.object(jbp, "poll_jira_bless", return_value=True) as mock_poll, \
             patch("sys.exit"):
            args = _make_parsed_args(root=root, user="jenkins")
            with patch.object(jbp, "parse_command_line", return_value=args):
                jbp._main_func("test")
        actual_root = mock_poll.call_args[1]["root"]
        self.assertEqual(actual_root, "/home/jenkins/data/jenkins/J")

###############################################################################
class TestResolveRoot(unittest.TestCase):
###############################################################################

    def test_cime_path_used_when_available(self):
        mock_machines = MagicMock()
        mock_machines.return_value.get_value.return_value = "/scratch/jenkins"
        with patch.dict("sys.modules", {"CIME": MagicMock(), "CIME.XML": MagicMock(),
                                        "CIME.XML.machines": MagicMock(Machines=mock_machines)}), \
             patch.object(jbp, "_setup_cime_path", return_value=True):
            root = jbp._resolve_root("mappy")
        self.assertEqual(root, "/scratch/jenkins/J")

    def test_falls_back_to_machine_roots_when_cime_fails(self):
        with patch.object(jbp, "_setup_cime_path", return_value=False):
            root = jbp._resolve_root("mappy")
        self.assertEqual(root, jbp.MACHINE_ROOTS["mappy"])

    def test_returns_none_for_unknown_machine_without_cime(self):
        with patch.object(jbp, "_setup_cime_path", return_value=False):
            root = jbp._resolve_root("unknownmachine")
        self.assertIsNone(root)

    def test_cime_exception_falls_back_to_machine_roots(self):
        mock_machines = MagicMock(side_effect=Exception("CIME exploded"))
        with patch.dict("sys.modules", {"CIME": MagicMock(), "CIME.XML": MagicMock(),
                                        "CIME.XML.machines": MagicMock(Machines=mock_machines)}), \
             patch.object(jbp, "_setup_cime_path", return_value=True):
            root = jbp._resolve_root("mappy")
        self.assertEqual(root, jbp.MACHINE_ROOTS["mappy"])

###############################################################################
class TestMachineRoots(unittest.TestCase):
###############################################################################

    def test_mappy_has_default_root(self):
        self.assertIn("mappy", jbp.MACHINE_ROOTS)
        self.assertTrue(jbp.MACHINE_ROOTS["mappy"])

    def test_poll_uses_root_in_command(self):
        issues = [_make_issue("SES-1", "mappy", "e3sm_developer_next_gnu, BOTH, ERS*")]
        with patch.object(jbp, "_auth_headers", return_value={}), \
             patch.object(jbp, "discover_field_ids", return_value=FAKE_FIELD_MAP), \
             patch.object(jbp, "search_issues", return_value=issues), \
             patch.object(jbp, "_invoke_bless", return_value=True) as mock_invoke, \
             patch.object(jbp, "add_comment", return_value=None), \
             patch.object(jbp, "transition_issue", return_value="done"):
            jbp.poll_jira_bless("u@e.com", "tok", "mappy", False, "/a/b")
            _, _, _, root, _ = mock_invoke.call_args[0]
            self.assertEqual(root, "/a/b")

###############################################################################
class TestPollJiraBless(unittest.TestCase):
###############################################################################

    def _run_poll(self, issues, machine="mappy", dry_run=False, bless_dry_run=False,
                  root="/fake/root", tickets=None, bless_succeeds=True, no_transition=False):
        """
        Run poll_jira_bless with all Jira I/O and bless invocation mocked out.
        Returns (success, mock_invoke, mock_comment, mock_transition).
        """
        with patch.object(jbp, "_auth_headers",      return_value={}), \
             patch.object(jbp, "discover_field_ids",  return_value=FAKE_FIELD_MAP), \
             patch.object(jbp, "search_issues",       return_value=issues), \
             patch.object(jbp, "_invoke_bless",       return_value=bless_succeeds) as mock_invoke, \
             patch.object(jbp, "add_comment",         return_value=None) as mock_comment, \
             patch.object(jbp, "transition_issue",    return_value="done") as mock_transition:
            success = jbp.poll_jira_bless("user@example.com", "token", machine, dry_run, root,
                                          bless_dry_run=bless_dry_run, tickets=tickets,
                                          no_transition=no_transition)
            return success, mock_invoke, mock_comment, mock_transition

    def test_no_tickets_returns_success(self):
        success, mock_invoke, _, _ = self._run_poll([])
        self.assertTrue(success)
        mock_invoke.assert_not_called()

    def test_matching_ticket_runs_bless(self):
        issues = [_make_issue("SES-1", "mappy", "e3sm_developer_next_gnu, BOTH, ERS*")]
        success, mock_invoke, _, _ = self._run_poll(issues, machine="mappy")
        self.assertTrue(success)
        mock_invoke.assert_called_once()
        suite, cases, action, root, _ = mock_invoke.call_args[0]
        self.assertEqual(suite, "e3sm_developer_next_gnu")
        self.assertIn("ERS*", cases)

    def test_wrong_machine_skips_ticket(self):
        issues = [_make_issue("SES-1", "chrysalis", "e3sm_developer_next_gnu, BOTH, ERS*")]
        success, mock_invoke, _, _ = self._run_poll(issues, machine="mappy")
        self.assertTrue(success)
        mock_invoke.assert_not_called()

    def test_no_machine_set_skips_ticket(self):
        issues = [_make_issue("SES-1", None, "e3sm_developer_next_gnu, BOTH, ERS*")]
        success, mock_invoke, _, _ = self._run_poll(issues, machine="mappy")
        self.assertTrue(success)
        mock_invoke.assert_not_called()

    def test_empty_description_skips_ticket(self):
        issues = [_make_issue("SES-1", "mappy", "")]
        success, mock_invoke, _, _ = self._run_poll(issues, machine="mappy")
        self.assertTrue(success)
        mock_invoke.assert_not_called()

    def test_multiple_actions_each_run(self):
        desc = "e3sm_suite_a_gnu, BOTH, ERS*\ne3sm_suite_b_intel, HIST, SMS*"
        issues = [_make_issue("SES-1", "mappy", desc)]
        success, mock_invoke, _, _ = self._run_poll(issues, machine="mappy")
        self.assertTrue(success)
        self.assertEqual(mock_invoke.call_count, 2)

    def test_multiple_tickets_only_matching_machine_run(self):
        issues = [
            _make_issue("SES-1", "mappy",    "e3sm_suite_a_gnu, BOTH, *"),
            _make_issue("SES-2", "chrysalis", "e3sm_suite_b_intel, BOTH, *"),
            _make_issue("SES-3", "mappy",    "e3sm_suite_c_gnu, NML, ERS*"),
        ]
        success, mock_invoke, _, _ = self._run_poll(issues, machine="mappy")
        self.assertTrue(success)
        self.assertEqual(mock_invoke.call_count, 2)

    def test_dry_run_does_not_call_invoke(self):
        issues = [_make_issue("SES-1", "mappy", "e3sm_suite_a_gnu, BOTH, ERS*")]
        success, mock_invoke, _, _ = self._run_poll(issues, machine="mappy", dry_run=True)
        self.assertTrue(success)
        mock_invoke.assert_not_called()

    def test_failed_action_returns_failure(self):
        issues = [_make_issue("SES-1", "mappy", "e3sm_suite_a_gnu, BOTH, ERS*")]
        success, _, _, _ = self._run_poll(issues, machine="mappy", bless_succeeds=False)
        self.assertFalse(success)

    def test_machine_match_is_case_insensitive(self):
        issues = [_make_issue("SES-1", "Mappy", "e3sm_suite_a_gnu, BOTH, *")]
        success, mock_invoke, _, _ = self._run_poll(issues, machine="mappy")
        self.assertTrue(success)
        mock_invoke.assert_called_once()

    def test_ticket_filter_limits_processing(self):
        issues = [
            _make_issue("SES-1", "mappy", "e3sm_suite_a_gnu, BOTH, *"),
            _make_issue("SES-2", "mappy", "e3sm_suite_b_gnu, BOTH, *"),
            _make_issue("SES-3", "mappy", "e3sm_suite_c_gnu, BOTH, *"),
        ]
        success, mock_invoke, _, _ = self._run_poll(issues, tickets=["SES-2"])
        self.assertTrue(success)
        self.assertEqual(mock_invoke.call_count, 1)

    def test_ticket_filter_is_case_insensitive(self):
        issues = [_make_issue("SES-42", "mappy", "e3sm_suite_a_gnu, BOTH, *")]
        success, mock_invoke, _, _ = self._run_poll(issues, tickets=["ses-42"])
        self.assertTrue(success)
        mock_invoke.assert_called_once()

    def test_ticket_filter_no_match_runs_nothing(self):
        issues = [_make_issue("SES-1", "mappy", "e3sm_suite_a_gnu, BOTH, *")]
        success, mock_invoke, _, _ = self._run_poll(issues, tickets=["SES-99"])
        self.assertTrue(success)
        mock_invoke.assert_not_called()

    def test_no_ticket_filter_processes_all(self):
        issues = [
            _make_issue("SES-1", "mappy", "e3sm_suite_a_gnu, BOTH, *"),
            _make_issue("SES-2", "mappy", "e3sm_suite_b_gnu, BOTH, *"),
        ]
        success, mock_invoke, _, _ = self._run_poll(issues, tickets=None)
        self.assertTrue(success)
        self.assertEqual(mock_invoke.call_count, 2)

    def test_successful_bless_closes_ticket(self):
        issues = [_make_issue("SES-1", "mappy", "e3sm_suite_a_gnu, BOTH, *")]
        _, _, mock_comment, mock_transition = self._run_poll(issues)
        mock_comment.assert_called_once_with({}, "SES-1", unittest.mock.ANY)
        mock_transition.assert_called_once_with(
            {}, "SES-1", jbp.RESOLVE_TRANSITION_NAMES, label="resolve")

    def test_comment_contains_captured_output(self):
        issues = [_make_issue("SES-1", "mappy", "e3sm_suite_a_gnu, BOTH, *")]
        _, _, mock_comment, _ = self._run_poll(issues)
        comment_text = mock_comment.call_args[0][2]
        # The captured output should include the action line printed during processing
        self.assertIn("Processing action", comment_text)

    def test_failed_bless_marks_ticket_inactive(self):
        issues = [_make_issue("SES-1", "mappy", "e3sm_suite_a_gnu, BOTH, *")]
        _, _, mock_comment, mock_transition = self._run_poll(issues, bless_succeeds=False)
        mock_comment.assert_called_once_with({}, "SES-1", unittest.mock.ANY)
        mock_transition.assert_called_once_with(
            {}, "SES-1", jbp.INACTIVE_TRANSITION_NAMES, label="inactive")

    def test_failed_bless_comment_contains_output(self):
        issues = [_make_issue("SES-1", "mappy", "e3sm_suite_a_gnu, BOTH, *")]
        _, _, mock_comment, _ = self._run_poll(issues, bless_succeeds=False)
        comment_text = mock_comment.call_args[0][2]
        self.assertIn("Processing action", comment_text)

    def test_dry_run_does_not_transition_ticket(self):
        issues = [_make_issue("SES-1", "mappy", "e3sm_suite_a_gnu, BOTH, *")]
        _, _, mock_comment, mock_transition = self._run_poll(issues, dry_run=True)
        mock_comment.assert_not_called()
        mock_transition.assert_not_called()

    def test_bless_dry_run_does_not_transition_ticket(self):
        issues = [_make_issue("SES-1", "mappy", "e3sm_suite_a_gnu, BOTH, *")]
        _, _, mock_comment, mock_transition = self._run_poll(issues, bless_dry_run=True)
        mock_comment.assert_not_called()
        mock_transition.assert_not_called()

    def test_partial_failure_marks_ticket_inactive(self):
        """If any action fails, the ticket should be marked inactive (not closed)."""
        desc = "e3sm_suite_a_gnu, BOTH, ERS*\ne3sm_suite_b_gnu, BOTH, SMS*"
        issues = [_make_issue("SES-1", "mappy", desc)]
        # First action succeeds, second fails
        side_effects = [True, False]
        with patch.object(jbp, "_auth_headers",     return_value={}), \
             patch.object(jbp, "discover_field_ids", return_value=FAKE_FIELD_MAP), \
             patch.object(jbp, "search_issues",      return_value=issues), \
             patch.object(jbp, "_invoke_bless",      side_effect=side_effects), \
             patch.object(jbp, "add_comment",        return_value=None) as mock_comment, \
             patch.object(jbp, "transition_issue",   return_value="on hold") as mock_transition:
            jbp.poll_jira_bless("u@e.com", "tok", "mappy", False, "/root")
        mock_comment.assert_called_once()
        mock_transition.assert_called_once_with(
            {}, "SES-1", jbp.INACTIVE_TRANSITION_NAMES, label="inactive")

    def test_no_transition_skips_resolve(self):
        issues = [_make_issue("SES-1", "mappy", "e3sm_suite_a_gnu, BOTH, *")]
        _, _, mock_comment, mock_transition = self._run_poll(issues, no_transition=True)
        mock_comment.assert_called_once()   # comment still posted
        mock_transition.assert_not_called()

    def test_no_transition_skips_inactive(self):
        issues = [_make_issue("SES-1", "mappy", "e3sm_suite_a_gnu, BOTH, *")]
        _, _, mock_comment, mock_transition = self._run_poll(
            issues, bless_succeeds=False, no_transition=True)
        mock_comment.assert_called_once()   # comment still posted
        mock_transition.assert_not_called()

###############################################################################

###############################################################################
class TestDirectActionMode(unittest.TestCase):
###############################################################################
    """Tests for the --action mode that bypasses Jira."""

    _ROOT = "/scratch/J"

    def _run_main_with_action(self, action_str, **ns_overrides):
        """Run _main_func with --action set, return what process_action received."""
        captured = {}
        def fake_process(action, indent, dry_run, bless_dry_run, root):
            captured["action"]       = action
            captured["dry_run"]      = dry_run
            captured["bless_dry_run"]= bless_dry_run
            captured["root"]         = root
            return True

        args = _make_parsed_args(action=action_str, root=self._ROOT, **ns_overrides)
        with patch.object(jbp, "parse_command_line", return_value=args), \
             patch.object(jbp, "_resolve_root",      return_value=self._ROOT), \
             patch.object(jbp, "process_action",     side_effect=fake_process), \
             patch("sys.exit"):
            jbp._main_func("test")
        return captured

    def test_action_mode_calls_process_action(self):
        captured = self._run_main_with_action("e3sm_developer_next_gnu, BOTH, ERS*")
        self.assertEqual(captured["action"], "e3sm_developer_next_gnu, BOTH, ERS*")

    def test_action_mode_passes_root(self):
        captured = self._run_main_with_action("e3sm_developer_next_gnu, BOTH, ERS*")
        self.assertEqual(captured["root"], self._ROOT)

    def test_action_mode_forwards_dry_run(self):
        captured = self._run_main_with_action("e3sm_developer_next_gnu, BOTH, ERS*", dry_run=True)
        self.assertTrue(captured["dry_run"])

    def test_action_mode_forwards_bless_dry_run(self):
        captured = self._run_main_with_action("e3sm_developer_next_gnu, BOTH, ERS*", bless_dry_run=True)
        self.assertTrue(captured["bless_dry_run"])

    def test_action_mode_does_not_call_poll_jira(self):
        args = _make_parsed_args(action="e3sm_developer_next_gnu, BOTH, ERS*", root=self._ROOT)
        with patch.object(jbp, "parse_command_line", return_value=args), \
             patch.object(jbp, "_resolve_root",      return_value=self._ROOT), \
             patch.object(jbp, "process_action",     return_value=True), \
             patch.object(jbp, "poll_jira_bless")    as mock_poll, \
             patch("sys.exit"):
            jbp._main_func("test")
        mock_poll.assert_not_called()

    def test_no_email_token_allowed_with_action(self):
        """--action mode must not crash when email/token are absent."""
        args = _make_parsed_args(action="e3sm_developer_next_gnu, BOTH, ERS*",
                                 root=self._ROOT, email=None, token=None)
        with patch.object(jbp, "parse_command_line", return_value=args), \
             patch.object(jbp, "_resolve_root",      return_value=self._ROOT), \
             patch.object(jbp, "process_action",     return_value=True), \
             patch("sys.exit") as mock_exit:
            jbp._main_func("test")
        # Should exit 0, not exit 1 (no "missing email/token" error)
        mock_exit.assert_called_with(0)

###############################################################################

###############################################################################
class TestCloseTicket(unittest.TestCase):
###############################################################################
    """Tests for the --close-ticket mode."""

    def test_close_ticket_transitions_and_comments(self):
        with patch.object(jbp, "add_comment", return_value=None) as mock_comment, \
             patch.object(jbp, "transition_issue", return_value="resolved") as mock_trans:
            success = jbp.close_ticket("e@e.com", "tok", "SES-42", comment_text="Manual close")
        self.assertTrue(success)
        mock_comment.assert_called_once()
        mock_trans.assert_called_once()

    def test_close_ticket_uppercase_id(self):
        with patch.object(jbp, "add_comment", return_value=None), \
             patch.object(jbp, "transition_issue", return_value="resolved") as mock_trans:
            jbp.close_ticket("e@e.com", "tok", "ses-99", comment_text="test")
        # Verify the ticket ID was uppercased
        call_args = mock_trans.call_args[0]
        self.assertEqual(call_args[1], "SES-99")

    def test_close_ticket_without_comment(self):
        with patch.object(jbp, "add_comment", return_value=None) as mock_comment, \
             patch.object(jbp, "transition_issue", return_value="resolved"):
            jbp.close_ticket("e@e.com", "tok", "SES-42")
        mock_comment.assert_not_called()

    def test_close_ticket_no_transition_skips_transition(self):
        with patch.object(jbp, "add_comment", return_value=None), \
             patch.object(jbp, "transition_issue") as mock_trans:
            success = jbp.close_ticket("e@e.com", "tok", "SES-42",
                                      comment_text="test", no_transition=True)
        self.assertTrue(success)
        mock_trans.assert_not_called()

    def test_close_ticket_main_func_mode(self):
        """Test --close-ticket through _main_func."""
        args = _make_parsed_args(close_ticket="SES-100", comment="Closed manually", email="e@e.com", token="tok")
        with patch.object(jbp, "parse_command_line", return_value=args), \
             patch.object(jbp, "add_comment", return_value=None), \
             patch.object(jbp, "transition_issue", return_value="resolved"), \
             patch("sys.exit") as mock_exit:
            jbp._main_func("test")
        mock_exit.assert_called_with(0)

###############################################################################

if __name__ == "__main__":
    unittest.main()
