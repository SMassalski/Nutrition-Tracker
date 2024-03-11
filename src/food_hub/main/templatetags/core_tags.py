"""Main app's core template tags."""
from django import template

register = template.Library()


@register.tag
def first_instance_of(parser, token):
    """Outputs the first argument that evaluates to `True`.

    Behaves like the `firstof` tag except, when the return value
    is stored in a variable, it is not rendered to a string.
    """

    args = token.split_contents()[1:]
    if len(args) == 0:
        raise template.exceptions.TemplateSyntaxError(
            "The `first_instance_of` tag requires at least one argument."
        )
    as_ = None
    if len(args) >= 2 and args[-2] == "as":
        as_ = args[-1]
        args = args[:-2]

    # compile_filter() applies template filters.
    return FirstInstanceOf([parser.compile_filter(arg) for arg in args], as_)


class FirstInstanceOf(template.Node):
    """Outputs the first argument that evaluates to `True`.

    Behaves like the `firstof` tag except, when the return value
    is stored in a variable, it is not rendered to a string.
    """

    # docstr-coverage: inherited
    def __init__(self, args, as_var=None):
        self.args = args
        self.as_var = as_var

    # docstr-coverage: inherited
    def render(self, context):
        ret = ""
        for arg in self.args:
            ret = arg.resolve(context, ignore_failures=True)
            if ret:
                break
        if not ret:  # Reset if no args are truthy
            ret = ""
        if self.as_var:
            context[self.as_var] = ret
            return ""
        return template.base.render_value_in_context(ret, context)
