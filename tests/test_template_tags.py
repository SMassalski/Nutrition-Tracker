import pytest
from django.template import Context, Template, TemplateSyntaxError


class TestFirstInstanceOf:
    def test_returns_first_truthy_value(self):
        context = Context({"a": 0, "b": 1})
        template_str = """
        {% load core_tags %}
        {% first_instance_of a b %}
        """
        result = Template(template_str).render(context).strip()

        assert result == "1"

    def test_no_args_raises_error(self):
        template_str = """
                {% load core_tags %}
                {% first_instance_of %}
                """
        with pytest.raises(TemplateSyntaxError):
            Template(template_str).render(Context())

    def test_returns_first_truthy_value_instance_if_as_used(self):
        context = Context({"a": {}, "b": {"b2": "value"}})
        template_str = """
        {% load core_tags %}
        {% first_instance_of a b as var %}
        {{ var.b2 }}
        """
        result = Template(template_str).render(context).strip()

        assert result == "value"

    def test_returns_empty_str_if_none_are_truthy(self):
        context = Context({"a": {}, "b": False})
        template_str = """
                {% load core_tags %}
                {% first_instance_of a b as var %}
                {{ var }}
                """
        result = Template(template_str).render(context).strip()

        assert result == ""
