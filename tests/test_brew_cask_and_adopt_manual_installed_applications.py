import sys
import os
import unittest
from unittest.mock import patch

# Add the 'brew_cask_and_adopt_manual_installed_applications' folder to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'brew_cask_and_adopt_manual_installed_applications'))

import brew_cask_and_adopt_manual_installed_applications

class TestBrewCaskAndAdopt(unittest.TestCase):

    @patch('brew_cask_and_adopt_manual_installed_applications.subprocess.run')
    def test_brew_search(self, mock_subprocess_run):
        # Mock the subprocess output for the brew search
        mock_subprocess_run.return_value.stdout = "google-chrome\n"
        result = brew_cask_and_adopt_manual_installed_applications.brew_search('google-chrome')
        self.assertIsInstance(result, list)
        self.assertIn('google-chrome', result)

    def test_list_installed_apps(self):
        # Assuming you want to test the `list_installed_apps` function from your script
        apps = brew_cask_and_adopt_manual_installed_applications.list_installed_apps('/Applications')
        # Mock or use a controlled environment for testing; this is just an example.
        self.assertIsInstance(apps, list)  # Verify the return type is a list

    def test_brew_search(self):
        # Assuming you want to test the `brew_search` function from your script
        result = brew_cask_and_adopt_manual_installed_applications.brew_search('google-chrome')
        # Check that it returns a list (even if it may be empty in your test environment)
        self.assertIsInstance(result, list)

    def test_is_default_apple_app(self):
        # Test the function `is_default_apple_app`
        self.assertTrue(brew_cask_and_adopt_manual_installed_applications.is_default_apple_app('safari'))
        self.assertFalse(brew_cask_and_adopt_manual_installed_applications.is_default_apple_app('google-chrome'))

if __name__ == '__main__':
    unittest.main()
