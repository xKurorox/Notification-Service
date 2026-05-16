from jinja2 import Template, Environment, StrictUndefined, UndefinedError
from typing import Optional

def render_template(template: str, variables: Optional[dict] = None):
    t = Template(template, undefined=StrictUndefined)
    try:
        result = t.render(variables or {})
    except UndefinedError as e:
        raise ValueError(f"Missing template variable: {e}")
    return result
