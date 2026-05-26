---
layout: default
title: Commentary & Satire Archive
permalink: /commentary/
---

# 📺 Commentary & Satire Archive

[⬅️ Back to Main Feed]({{ '/' | relative_url }}) | [📂 View Forensic Database]({{ '/archive/' | relative_url }})

{% assign commentary_posts = site.categories.commentary %}

### 📁 Community & Satire
<ul>
  {% for post in commentary_posts %}
    <li>
      <a href="{{ post.url | relative_url }}">{{ post.date | date: "%Y-%m-%d" }} - {{ post.title }}</a>
    </li>
  {% endfor %}
</ul>

[⬅️ Back to Main Feed]({{ '/' | relative_url }}) | [📂 View Forensic Database]({{ '/archive/' | relative_url }})
