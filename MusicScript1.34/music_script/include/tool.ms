{% macro bpm(val) %}{{ 60 / float(val) }}{% endmacro %}

{% macro sum(score, times) %}
    {% for i in range(int(times)) %}
        {% if not loop.first %}+{% endif %}{{ score }}
    {% endfor %}
{% endmacro %}
