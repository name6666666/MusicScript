{% macro _chord(notes, root, trans=0, bass=None) %}[
    {% if bass is not none %}
        {{ bass }}
    {% else %}
        {{ root }}
    {% endif %}
    {% for i in range(int(trans)) %}
        {% set notes = notes[1:] + [notes[0] + 12] %}
    {% endfor %}
    {% set match = re.match('^([.\']*)([^.\']+)', root) %}
    {% set a = match.group(1) %}
    {% set b = match.group(2) %}
    {% for i in notes %}
        {{ a }}{{ i * 's' }}{{ b }}
    {% endfor %}
]{% endmacro %}


{% macro min(root, trans=0, bass=None) %}{{ _chord([0, 3, 7], root, trans, bass) }}{% endmacro %}
{% macro maj(root, trans=0, bass=None) %}{{ _chord([0, 4, 7], root, trans, bass) }}{% endmacro %}
{% macro dim(root, trans=0, bass=None) %}{{ _chord([0, 3, 6], root, trans, bass) }}{% endmacro %}
{% macro aug(root, trans=0, bass=None) %}{{ _chord([0, 4, 8], root, trans, bass) }}{% endmacro %}
{% macro maj7(root, trans=0, bass=None) %}{{ _chord([0, 4, 7, 11], root, trans, bass) }}{% endmacro %}
{% macro min7(root, trans=0, bass=None) %}{{ _chord([0, 3, 7, 10], root, trans, bass) }}{% endmacro %}
{% macro dom7(root, trans=0, bass=None) %}{{ _chord([0, 4, 7, 10], root, trans, bass) }}{% endmacro %}
{% macro dim7(root, trans=0, bass=None) %}{{ _chord([0, 3, 6, 9], root, trans, bass) }}{% endmacro %}
{% macro m7b5(root, trans=0, bass=None) %}{{ _chord([0, 3, 6, 10], root, trans, bass) }}{% endmacro %}
{% macro sus2(root, trans=0, bass=None) %}{{ _chord([0, 2, 7], root, trans, bass) }}{% endmacro %}
{% macro sus4(root, trans=0, bass=None) %}{{ _chord([0, 5, 7], root, trans, bass) }}{% endmacro %}
{% macro add9(root, trans=0, bass=None) %}{{ _chord([0, 4, 7, 14], root, trans, bass) }}{% endmacro %}
{% macro maj6(root, trans=0, bass=None) %}{{ _chord([0, 4, 7, 9], root, trans, bass) }}{% endmacro %}
{% macro m6(root, trans=0, bass=None) %}{{ _chord([0, 3, 7, 9], root, trans, bass) }}{% endmacro %}
