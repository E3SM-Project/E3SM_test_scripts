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

    def test_action_both(self):
        cmd = jbp.build_bless_cmd("e3sm_developer_next_gnu", ["ERS*"], "both")
        self.assertIn("-t", cmd)
        self.assertEqual(cmd[cmd.index("-t") + 1], "JNextDeveloper")
        self.assertIn("-c", cmd)
        self.assertEqual(cmd[cmd.index("-c") + 1], "gnu")
        self.assertIn("-f", cmd)
        self.assertIn("ERS*", cmd)
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
        self.assertEqual(cmd[f_idx + 1], "ERS*")
        self.assertEqual(cmd[f_idx + 2], "SMS*")
        self.assertEqual(cmd[f_idx + 3], "PET*")

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

###############################################################################
class TestProcessAction(unittest.TestCase):
###############################################################################

    def test_too_few_parts_returns_false(self):
        self.assertFalse(jbp.process_action("only_suite, NML"))

    def test_bad_task_returns_false(self):
        self.assertFalse(jbp.process_action("e3sm_suite_gnu, BADTASK, ERS*"))

    def test_bad_suite_format_returns_false(self):
        # Suite with too few parts to parse
        self.assertFalse(jbp.process_action("badname, BOTH, ERS*"))

    def test_dry_run_returns_true_without_running(self):
        with patch("subprocess.run") as mock_run:
            result = jbp.process_action("e3sm_dev_suite_gnu, BOTH, ERS*", dry_run=True)
            self.assertTrue(result)
            mock_run.assert_not_called()

    def test_nml_task_passes_n_flag(self):
        mock_result = MagicMock(returncode=0, stdout="ok\n", stderr="")
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = jbp.process_action("e3sm_dev_suite_gnu, NML, ERS*")
            self.assertTrue(result)
            cmd = mock_run.call_args[0][0]
            self.assertIn("-n", cmd)
            self.assertNotIn("--hist-only", cmd)

    def test_hist_task_passes_hist_only_flag(self):
        mock_result = MagicMock(returncode=0, stdout="ok\n", stderr="")
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = jbp.process_action("e3sm_dev_suite_gnu, HIST, SMS*")
            self.assertTrue(result)
            cmd = mock_run.call_args[0][0]
            self.assertIn("--hist-only", cmd)
            self.assertNotIn("-n", cmd)

    def test_both_task_passes_no_extra_flag(self):
        mock_result = MagicMock(returncode=0, stdout="ok\n", stderr="")
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = jbp.process_action("e3sm_dev_suite_gnu, BOTH, *")
            self.assertTrue(result)
            cmd = mock_run.call_args[0][0]
            self.assertNotIn("-n", cmd)
            self.assertNotIn("--hist-only", cmd)

    def test_multiple_case_globs(self):
        mock_result = MagicMock(returncode=0, stdout="", stderr="")
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            jbp.process_action("e3sm_dev_suite_gnu, BOTH, ERS*, SMS*, PET*")
            cmd = mock_run.call_args[0][0]
            # Cases are positional args after the single -f flag
            f_idx = cmd.index("-f")
            self.assertEqual(cmd[f_idx + 1], "ERS*")
            self.assertEqual(cmd[f_idx + 2], "SMS*")
            self.assertEqual(cmd[f_idx + 3], "PET*")

    def test_command_failure_returns_false(self):
        mock_result = MagicMock(returncode=1, stdout="", stderr="error output")
        with patch("subprocess.run", return_value=mock_result):
            self.assertFalse(jbp.process_action("e3sm_dev_suite_gnu, BOTH, ERS*"))

    def test_task_case_insensitive(self):
        mock_result = MagicMock(returncode=0, stdout="", stderr="")
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = jbp.process_action("e3sm_dev_suite_gnu, hist, ERS*")
            self.assertTrue(result)
            cmd = mock_run.call_args[0][0]
            self.assertIn("--hist-only", cmd)

    def test_compiler_extracted_from_suite(self):
        mock_result = MagicMock(returncode=0, stdout="", stderr="")
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            jbp.process_action("e3sm_developer_next_gnu, BOTH, *")
            cmd = mock_run.call_args[0][0]
            self.assertEqual(cmd[cmd.index("-t") + 1], "JNextDeveloper")
            self.assertEqual(cmd[cmd.index("-c") + 1], "gnu")

###############################################################################
class TestPollJiraBless(unittest.TestCase):
###############################################################################

    def _run_poll(self, issues, machine="mappy", dry_run=False):
        """
        Run poll_jira_bless with all Jira I/O mocked out.
        Returns (success, subprocess_calls).
        """
        mock_proc = MagicMock(returncode=0, stdout="blessed\n", stderr="")
        with patch.object(jbp, "_auth_headers", return_value={}), \
             patch.object(jbp, "discover_field_ids", return_value=FAKE_FIELD_MAP), \
             patch.object(jbp, "search_issues", return_value=issues), \
             patch("subprocess.run", return_value=mock_proc) as mock_run:
            success = jbp.poll_jira_bless("user@example.com", "token", machine, dry_run)
            return success, mock_run

    def test_no_tickets_returns_success(self):
        success, mock_run = self._run_poll([])
        self.assertTrue(success)
        mock_run.assert_not_called()

    def test_matching_ticket_runs_bless(self):
        issues = [_make_issue("SES-1", "mappy", "e3sm_developer_next_gnu, BOTH, ERS*")]
        success, mock_run = self._run_poll(issues, machine="mappy")
        self.assertTrue(success)
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        self.assertIn("JNextDeveloper", cmd)
        self.assertIn("gnu", cmd)
        self.assertIn("ERS*", cmd)

    def test_wrong_machine_skips_ticket(self):
        issues = [_make_issue("SES-1", "chrysalis", "e3sm_developer_next_gnu, BOTH, ERS*")]
        success, mock_run = self._run_poll(issues, machine="mappy")
        self.assertTrue(success)
        mock_run.assert_not_called()

    def test_no_machine_set_skips_ticket(self):
        issues = [_make_issue("SES-1", None, "e3sm_developer_next_gnu, BOTH, ERS*")]
        success, mock_run = self._run_poll(issues, machine="mappy")
        self.assertTrue(success)
        mock_run.assert_not_called()

    def test_empty_description_skips_ticket(self):
        issues = [_make_issue("SES-1", "mappy", "")]
        success, mock_run = self._run_poll(issues, machine="mappy")
        self.assertTrue(success)
        mock_run.assert_not_called()

    def test_multiple_actions_each_run(self):
        desc = "e3sm_suite_a_gnu, BOTH, ERS*\ne3sm_suite_b_intel, HIST, SMS*"
        issues = [_make_issue("SES-1", "mappy", desc)]
        success, mock_run = self._run_poll(issues, machine="mappy")
        self.assertTrue(success)
        self.assertEqual(mock_run.call_count, 2)

    def test_multiple_tickets_only_matching_machine_run(self):
        issues = [
            _make_issue("SES-1", "mappy",    "e3sm_suite_a_gnu, BOTH, *"),
            _make_issue("SES-2", "chrysalis", "e3sm_suite_b_intel, BOTH, *"),
            _make_issue("SES-3", "mappy",    "e3sm_suite_c_gnu, NML, ERS*"),
        ]
        success, mock_run = self._run_poll(issues, machine="mappy")
        self.assertTrue(success)
        self.assertEqual(mock_run.call_count, 2)

    def test_dry_run_does_not_call_subprocess(self):
        issues = [_make_issue("SES-1", "mappy", "e3sm_suite_a_gnu, BOTH, ERS*")]
        success, mock_run = self._run_poll(issues, machine="mappy", dry_run=True)
        self.assertTrue(success)
        mock_run.assert_not_called()

    def test_failed_action_returns_failure(self):
        issues = [_make_issue("SES-1", "mappy", "e3sm_suite_a_gnu, BOTH, ERS*")]
        mock_proc = MagicMock(returncode=1, stdout="", stderr="error")
        with patch.object(jbp, "_auth_headers", return_value={}), \
             patch.object(jbp, "discover_field_ids", return_value=FAKE_FIELD_MAP), \
             patch.object(jbp, "search_issues", return_value=issues), \
             patch("subprocess.run", return_value=mock_proc):
            success = jbp.poll_jira_bless("user@example.com", "token", "mappy", False)
        self.assertFalse(success)

    def test_machine_match_is_case_insensitive(self):
        issues = [_make_issue("SES-1", "Mappy", "e3sm_suite_a_gnu, BOTH, *")]
        success, mock_run = self._run_poll(issues, machine="mappy")
        self.assertTrue(success)
        mock_run.assert_called_once()

###############################################################################

if __name__ == "__main__":
    unittest.main()
