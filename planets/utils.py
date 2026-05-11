def separate_first_line(obj):
    first_line = obj.text.splitlines()[0] if obj.text else ''
    lines = obj.text.splitlines()
    remaining_text = "\n".join(lines[1:])  # все строки, кроме первой
    return first_line, remaining_text