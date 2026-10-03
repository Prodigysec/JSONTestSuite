"""The inventory reports setup prerequisites separately from run commands."""

import contextlib
import io
import json
import sys
import unittest
from unittest.mock import patch

import inventory_parser_tools


class InventoryTests(unittest.TestCase):
    def test_setup_resolution_is_separate_from_invocation(self):
        registry = {"mode": {"commands": [sys.executable, "adapter.py"],
                             "setup": ["jsonsuite-definitely-missing-tool", "build"]}}
        output = io.StringIO()
        with patch.object(inventory_parser_tools, "programs", registry), contextlib.redirect_stdout(output):
            inventory_parser_tools.main()
        mode = json.loads(output.getvalue())["modes"][0]
        self.assertEqual(mode["resolved"], sys.executable)
        self.assertEqual(mode["setup_executable"], "jsonsuite-definitely-missing-tool")
        self.assertIsNone(mode["setup_resolved"])


if __name__ == "__main__":
    unittest.main()
