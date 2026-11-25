
# \033[código_estilo;color_texto;color_behind

from bimo import colors
from bimo.components.colors import _Color

from bimo import styles
from bimo.components.styles import _Style

from bimo.components.design import desing

from bimo.tools.text.functions.analitics.similarword import similar_word


class text:

    @staticmethod
    def write(content: str | list[str] = "", design: desing | None = None, **kwargs):
        if design is None:
            design = desing(**kwargs)
        return print(design.apply(content))

    @staticmethod
    def paint(content: str | list[str], design: desing | None = None, **kwargs) -> str:


        if design is None:
            design = desing(**kwargs)
        try:
            return design.apply(content)
        except:
            print(f"No design applied. Use a valid design() --> Right now you got this '{design}'")
            print(f"For this content : {content}")
            return "....."


    @staticmethod
    def mark(content: str,
            targets: str | list[str] = None,
            design: desing | None = None,
            similar: bool = False,
            **kwargs) -> str:

        if design is None:
            design = desing(**kwargs)

        # normalizar targets
        if targets is None:
            targets = []
        elif isinstance(targets, str):
            targets = [targets]
        targets = set(targets)

        # si no hay nada que marcar y no se piden similares → pintar todo
        if not targets and not similar:
            return design.apply(content)

        # similares sobre texto LIMPIO
        if similar:
            similars = similar_word(content=content)   # lista
            targets.update(similars)                   # ✅ update, no add

        # pintar palabra por palabra (una sola pasada)
        import re
        pattern = re.compile(r"\w+", re.UNICODE)
        return pattern.sub(
            lambda m: design.apply(m.group(0)) if m.group(0) in targets else m.group(0),
            content,
        )
