import jsbeautifier

def beautify_js(raw_js: str) -> str:
    """
    Takes minified or poorly formatted JS code and runs it through jsbeautifier
    to make it readable for human analysis and better regex matching.
    """
    opts = jsbeautifier.default_options()
    opts.indent_size = 2
    opts.space_in_empty_paren = True
    return jsbeautifier.beautify(raw_js, opts)
