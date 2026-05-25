---
layout: default
title: Forensic Database by Source
permalink: /archive/:path/
---

# 📂 Forensic Database by Source

{% assign primary_posts = site.categories.Thomas %}
{% assign grouped_posts = primary_posts | group_by: "channel" %}

{% for group in grouped_posts %}
  ### 📁 {{ group.name }}
  <ul>
    {% for item in group.items %}
      <li>
        <a href="{{ item.url | relative_url }}">{{ item.date | date: "%Y-%m-%d" }} - {{ item.title }}</a>
      </li>
    {% endfor %}
  </ul>
{% endfor %}

[⬅️ Back to Main Feed]({{ '/' | relative_url }})
