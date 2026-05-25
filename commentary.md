---
layout: default
title: Commentary & Satire Archive
permalink: /commentary/
---

<div class="nav-links" style="margin-bottom: 20px;">
  [⬅️ Back to Main Feed]({{ '/' | relative_url }}) | [📂 View Forensic Database]({{ '/archive/' | relative_url }})
</div>

<div class="archive-header" style="margin-bottom: 30px; border-left: 4px solid #e74c3c; padding-left: 15px;">
    <p><em>Notice: This section contains community commentary, satirical breakdowns, and third-party analysis regarding the entity. These assets are categorized separately to preserve the pristine, unfiltered context of the primary forensic logs.</em></p>
</div>

<div class="posts-list">
  {% assign commentary_posts = site.categories.commentary %}
  {% if commentary_posts.size > 0 %}
    {% for post in commentary_posts %}
      <article class="post-item" style="margin-bottom: 40px; background: #111; padding: 20px; border-radius: 6px; border: 1px solid #222;">
        <h2 style="margin-top: 0;"><a href="{{ post.url | relative_url }}">{{ post.title }}</a></h2>
        <div class="post-meta" style="color: #888; font-size: 0.9em; margin-bottom: 15px;">
          <span>Published: {{ post.date | date: "%Y-%m-%d" }}</span>
        </div>

        <div class="video-preview" style="margin-bottom: 15px;">
          <div class="video-container" style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; background: #000; border-radius: 4px;">
            <iframe src="https://www.youtube.com/embed/{{ post.youtube_id }}" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;" allowfullscreen></iframe>
          </div>
        </div>

        <div class="post-excerpt" style="color: #ccc;">
          {{ post.excerpt | strip_html | truncatewords: 50 }}
        </div>
      </article>
    {% endfor %}
  {% else %}
    <p style="color: #888; font-style: italic;">No commentary entries have been synchronized to this node yet.</p>
  {% endif %}
</div> 

<div class="nav-links" style="margin-top: 30px;">
  [⬅️ Back to Main Feed]({{ '/' | relative_url }}) | [📂 View Forensic Database]({{ '/archive/' | relative_url }})
</div>
