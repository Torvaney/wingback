{% macro create_index(tbl, field) %}

  {{ after_commit(_create_index(tbl, field)) }}

{% endmacro %}


{% macro _create_index(tbl, field) %}

  {% if field is iterable and field is not string %}
    -- Multi-column indexes
    create index if not exists {{ tbl.name }}__index_on_{{ field|join('__') }} on {{ tbl.name }} ({{ field|join(', ') }})
  {% else %}
    -- Single column indexes
    create index if not exists {{ tbl.name }}__index_on_{{ field }} on {{ tbl.name }} ({{ field }})
  {% endif %}

{% endmacro %}
