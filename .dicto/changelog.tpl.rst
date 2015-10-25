{{version}}  {{current_date.date()}}
-----------------

{% for commit in git_version_commits -%}
{%- if commit.summary.strip().startswith('Adds')
      or commit.summary.strip().startswith('Fix')
      or commit.summary.strip().startswith('Improve') -%}
* {{commit.summary}}
{% endif -%}
{% endfor %}
