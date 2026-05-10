---
layout: default
title: Video Archive
permalink: /video-archive/
---

<div class="archive-container">
  {% if site.data.videos %}
    <div class="video-grid">
      {% for video in site.data.videos %}
        <div class="video-card">
          <div class="video-wrapper">
            <iframe 
              src="https://www.youtube.com/embed/{{ video.id }}" 
              frameborder="0" 
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
              allowfullscreen>
            </iframe>
          </div>
          <div class="video-info">
            <h3 class="video-title">{{ video.title }}</h3>
            <span class="video-date">Intercepted: {{ video.date }}</span>
          </div>
        </div>
      {% endfor %}
    </div>
  {% else %}
    <p class="no-videos">No intercepted transmissions found yet. Running scan...</p>
  {% endif %}
</div>

 
