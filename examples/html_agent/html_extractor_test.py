import subprocess
from typing import Optional, Tuple

import pytest

# Path to the test HTML file
HTML_FILE_PATH = "../../test.html"


# Helper function to run the CLI tool and capture output
def run_html_extractor(args: list) -> Tuple[Optional[str], Optional[str]]:
    command = ["python", "html_extractor.py", *args]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return (
            result.stdout,
            None,
        )  # Return stdout and None for stderr to indicate no error
    except subprocess.CalledProcessError as e:
        return (
            None,
            e.stderr,
        )  # Return None for stdout and stderr to indicate an error occurred


# Test for invalid HTML file
def test_invalid_file():
    stdout, stderr = run_html_extractor(["nonexistent.html"])
    assert stdout is None  # Expecting no stdout content
    assert "FileNotFoundError" in stderr  # Expecting the specific error to be in stderr


@pytest.mark.parametrize(
    "focus_arg, expected_text, should_exist",
    [
        ("", "container", True),
        ("Unique text here.", "Unique text here.", True),
        ("Repeated text.", "Repeated text.", True),
        ("Nested text.", "Nested text.", True),
        ("Non-existent", "Non-existent", False),
    ],
)
def test_focus(focus_arg, expected_text, should_exist):
    args = [HTML_FILE_PATH, "--focus", focus_arg]
    stdout, _ = run_html_extractor(args)
    if should_exist:
        assert expected_text in stdout
    else:
        assert expected_text not in stdout


# Existing imports and helper functions ...


# Test --css_selector functionality
@pytest.mark.parametrize(
    "css_selector, expected_element",
    [
        ("", "container"),  # No filter, so 'container' class should be in the output
        ("p", "<p>Unique text here.</p>"),  # p elements
        (
            ".nested-span",
            '<span class="nested-span">Nested text.</span>',
        ),  # Class selector
        ("div > span", "<span>Repeated text.</span>"),  # Child combinator
        (
            ".non-existent",
            "\n",
        ),  # No matching elements should result in an empty or unchanged output
    ],
)
def test_css_selector(css_selector, expected_element):
    args = [HTML_FILE_PATH, "--css_selector", css_selector]
    stdout, _ = run_html_extractor(args)
    if expected_element:
        assert expected_element in stdout
    else:
        assert (
            "container" in stdout
        )  # Assumes 'container' appears by default when no matching elements
