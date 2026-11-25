# Small container for one ANSI color code.
class _Color:
    def __init__(self, value):
        self.value = int(value)

    def __repr__(self):
        return f"colors.{self.value}"

# Standard foreground colors.
class colors:

    # ANSI CODES 
    DEFAULT = _Color(39)
    BLACK = _Color(30)
    RED = _Color(31)
    GREEN = _Color(32)
    YELLOW = _Color(33)
    BLUE = _Color(34)
    PURPLE = _Color(35)
    CYAN = _Color(36)
    GRAY = _Color(37)



    