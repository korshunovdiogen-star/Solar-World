import html
from html.parser import HTMLParser

from django.utils.safestring import mark_safe


ALLOWED_CLASSES = {'custom-style'}


class RichTextSanitizer(HTMLParser):
    """
    Оставляет только <span> и <span class="custom-style">.

    Всё остальное удаляется, а текст экранируется. Поэтому даже если
    в базе окажется <script>, он не выполнится.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._parts = []
        self._open_spans = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() != 'span':
            return

        classes = set()
        for name, value in attrs:
            if name.lower() == 'class' and value:
                classes.update(value.split())

        if classes & ALLOWED_CLASSES:
            self._parts.append('<span class="custom-style">')
        else:
            self._parts.append('<span>')
        self._open_spans += 1

    def handle_startendtag(self, tag, attrs):
        if tag.lower() != 'span':
            return
        self.handle_starttag(tag, attrs)
        self._parts.append('</span>')
        self._open_spans -= 1

    def handle_endtag(self, tag):
        if tag.lower() == 'span' and self._open_spans > 0:
            self._parts.append('</span>')
            self._open_spans -= 1

    def handle_data(self, data):
        self._parts.append(html.escape(data, quote=False))

    def handle_entityref(self, name):
        self._parts.append(f'&{name};')

    def handle_charref(self, name):
        self._parts.append(f'&#{name};')

    def handle_comment(self, data):
        pass

    def handle_decl(self, decl):
        pass

    def handle_pi(self, data):
        pass

    def unknown_decl(self, data):
        pass

    def get_html(self):
        # Если во входном тексте забыли закрыть span, закрываем его сами.
        self._parts.append('</span>' * self._open_spans)
        return ''.join(self._parts)


def sanitize_rich_text(value):
    """Возвращает безопасный HTML для текстов с разрешёнными span."""
    if not value:
        return ''

    parser = RichTextSanitizer()
    parser.feed(str(value))
    parser.close()
    return mark_safe(parser.get_html())
