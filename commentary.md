---
layout: default
title: Commentary & Satire Archive
permalink: /commentary/
---

# 📺 Commentary & Satire Archive

[⬅️ Back to Main Feed]({{ '/' | relative_url }}) | [📂 View Forensic Database]({{ '/archive/' | relative_url }})

---

{% assign commentary_posts = site.categories.commentary | sort: 'date' | reverse %}

{% if commentary_posts.size > 0 %}
  {% for post in commentary_posts %}
    ### {{ post.date | date: "%Y-%m-%d" }} - [{{ post.title }}]({{ post.url | relative_url }})
  {% endfor %}
{% else %}
  _No commentary entries have been synchronized to this node yet._
{% endif %}

---

[⬅️ Back to Main Feed]({{ '/' | relative_url }}) | [📂 View Forensic Database]({{ '/archive/' | relative_url }})
