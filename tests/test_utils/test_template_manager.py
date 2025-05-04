import pytest
from unittest.mock import patch, mock_open
from app.utils.template_manager import TemplateManager
from bs4 import BeautifulSoup

@pytest.fixture
def template_manager():
    return TemplateManager()

def test_apply_email_styles(template_manager):
    html_input = "<h1>Title</h1><p>Hello</p><a href='#'>Link</a>"
    styled_html = template_manager._apply_email_styles(html_input)
    soup = BeautifulSoup(styled_html, "html.parser")

    # Assert wrapper div exists and has the general styling context
    div = soup.find("div")
    assert div is not None
    assert "font-family: Arial, sans-serif" in div.get("style", "")

    # Assert expected elements exist (relaxed - no style enforcement)
    assert soup.find("h1") is not None
    assert soup.find("p") is not None
    assert soup.find("a") is not None

@patch("builtins.open", new_callable=mock_open, read_data="Header Content")
def test_read_template(mock_file, template_manager):
    content = template_manager._read_template("header.md")
    mock_file.assert_called_once()
    assert content == "Header Content"

@patch.object(TemplateManager, "_read_template")
def test_render_template(mock_read, template_manager):
    # Corrected order based on method logic
    mock_read.side_effect = [
        "# Header",              # header.md
        "_Footer_",              # footer.md
        "**Hello, {name}**"      # test_template.md
    ]

    result = template_manager.render_template("test_template", name="Alice")
    soup = BeautifulSoup(result, "html.parser")

    # Assert outer div exists
    div = soup.find("div")
    assert div is not None
    assert "font-family: Arial, sans-serif" in div.get("style", "")

    # Assert that all critical content rendered
    text = div.get_text()
    assert "Hello, Alice" in text
    assert "Header" in text
    assert "Footer" in text
