{% macro _temp(a, b) %}
    template rc beats=3 notes={{ a }} {
        common: .B {{ b }} {{ b }}
    }
    template rc beats=1 notes={{ a }} {
        common: {{ b }}
    }
    template rc beats=2 notes={{ a }} {
        common: .B {{ b }}
    }
    template rc beats=4 notes={{ a }} {
        common: .B {{ b }} {{ b }} {{ b }}
    }
{% endmacro %}
{{ _temp(3, '[1 3 5]') }}
{{ _temp(4, '[1 3 5 7]') }}


