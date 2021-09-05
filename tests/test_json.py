"""Test JSON."""
import unittest
from . import validate_json_format
import os
import fnmatch


class TestSettings(unittest.TestCase):
    """Test JSON settings."""

    def _get_json_files(self, pattern, folder='.'):
        """Get JSON files."""

        for root, dirnames, filenames in os.walk(folder):
            for filename in fnmatch.filter(filenames, pattern):
                yield os.path.join(root, filename)
            dirnames[:] = [d for d in dirnames if d not in ('.svn', '.git', '.tox')]

    def test_json_settings(self):
        """Test each JSON file."""

        patterns = (
            '*.sublime-settings',
            '*.sublime-keymap',
            '*.sublime-commands',
            '*.sublime-menu',
            '*.sublime-theme',
            '*.sublime-color-scheme'
        )

        for pattern in patterns:
            for f in self._get_json_files(pattern):
                self.assertFalse(
                    validate_json_format.CheckJsonFormat(False, True).check_format(f),
                    "%s does not comform to expected format!" % f
                )
