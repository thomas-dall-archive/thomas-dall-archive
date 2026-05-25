---
layout: default
title: Forensic Database by Source
permalink: /archive/:path/
---

# 📂 Forensic Database by Source

{% for category in site.categories %}
  {% capture cat_name %}{{ category | first }}{% endcapture %}
  
  {% if cat_name == "Thomas" or cat_name == "commentary" %}
    {% continue %}
  {% endif %}

  ### 📁 {{ cat_name }}
  <ul>
    {% for post in category | last %}
      <li>
        <a href="{{ post.url | relative_url }}">{{ post.date | date: "%Y-%m-%d" }} - {{ post.title }}</a>
      </li>
    {% endfor %}
  </ul>
{% endfor %}

[⬅️ Back to Main Feed]({{ '/' | relative_url }})
