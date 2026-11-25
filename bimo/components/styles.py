# Small container for one ANSI style code.
class _Style:
    def __init__(self, value):
        self.value = int(value)

    def __repr__(self):
        return f"styles.{self.value}"

# Standard text styles.
class styles:

    # ANSI CODES 

    DEFAULT = _Style(0)
    BOLD = _Style(1)
    FAINT = _Style(2)
    CURSIVE = _Style(3)
    UNDERLINE = _Style(4)
    FLASHING = _Style(5)
    INVERT = _Style(7)
    MARKED = _Style(9)




    