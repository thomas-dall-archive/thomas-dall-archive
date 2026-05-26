---
layout: default
title: Commentary & Satire Archive
permalink: /commentary/
---

# 📺 Commentary & Satire Archive

[⬅️ Back to Main Feed]({{ '/' | relative_url }}) | [📂 View Forensic Database]({{ '/archive/' | relative_url }})

<hr>

{% assign commentary_posts = site.categories.commentary %}
{% assign grouped_posts = commentary_posts | group_by: "channel" %}

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

{% if commentary_posts.size == 0 %}
  <p><em>No commentary entries have been synchronized to this node yet.</em></p>
{% endif %}

<hr>

[⬅️ Back to Main Feed]({{ '/' | relative_url }}) | [📂 View Forensic Database]({{ '/archive/' | relative_url }})
