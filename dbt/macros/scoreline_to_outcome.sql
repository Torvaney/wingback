{% macro scoreline_to_outcome(home_goals, away_goals) %}

    case
      when {{ home_goals }} > {{ away_goals }} then 'Home win'
      when {{ home_goals }} = {{ away_goals }} then 'Draw'
      when {{ home_goals }} < {{ away_goals }} then 'Away win'
    end

{% endmacro %}
