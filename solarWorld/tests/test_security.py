from solarWorld.security import sanitize_rich_text


def test_allows_custom_style_span():
    result = str(sanitize_rich_text('<span class="custom-style">Марс</span>'))
    assert result == '<span class="custom-style">Марс</span>'


def test_allows_plain_span():
    result = str(sanitize_rich_text('<span>Марс</span>'))
    assert result == '<span>Марс</span>'


def test_strips_script_tags_and_event_handlers():
    result = str(sanitize_rich_text(
        '<span class="custom-style" onclick="alert(1)">Марс</span>'
        '<script>alert(1)</script>'
    ))

    assert result.startswith('<span class="custom-style">Марс</span>')
    assert '<script' not in result
    assert 'onclick' not in result


def test_drops_style_attribute():
    result = str(sanitize_rich_text(
        '<span class="custom-style" style="background:url(javascript:alert(1))">'
        'Марс</span>'
    ))

    assert result == '<span class="custom-style">Марс</span>'
    assert 'style=' not in result
    assert 'javascript' not in result


def test_drops_unknown_tags_but_keeps_text():
    result = str(sanitize_rich_text('<b>Жирный</b> текст'))
    assert result == 'Жирный текст'


def test_escapes_plain_text():
    result = str(sanitize_rich_text('1 < 2 & 3 > 2'))
    assert result == '1 &lt; 2 &amp; 3 &gt; 2'


def test_closes_unclosed_span():
    result = str(sanitize_rich_text('<span class="custom-style">Марс'))
    assert result == '<span class="custom-style">Марс</span>'
