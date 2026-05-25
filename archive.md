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
    {% for post in group.items %}
      <li>
        <a href="{{ post.url | relative_url }}">{{ post.date | date: "%Y-%m-%d" }} - {{ post.title }}</a>
      </li>
    {% endfor %}
  </ul>
{% endfor %}

[⬅️ Back to Main Feed]({{ '/' | relative_url }})
