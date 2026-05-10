---
layout: default
title: Video Archive
permalink: /video-archive/
---

<style>
  .archive-container {
    padding: 10px 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  }
  
  .video-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 25px;
    margin-top: 20px;
  }

  @media (min-width: 700px) {
    .video-grid {
      grid-template-columns: 1fr 1fr;
    }
  }

  .video-card {
    background: #111;
    border: 1px solid #222;
    border-radius: 6px;
    overflow: hidden;
    transition: border 0.2s ease-in-out;
  }

  .video-card:hover {
    border-color: #ffc107; /* Match your image color */
  }

  .video-wrapper {
    position: relative;
    padding-bottom: 56.25%;
    height: 0;
    background: #000;
  }

  .video-wrapper iframe {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
  }

  .video-info {
    padding: 15px;
    background: #1a1a1a;
  }

  .video-title {
    margin: 0 0 8px 0;
    font-size: 1rem !important;
    color: #ffc107 !important; /* Match your image color */
    line-height: 1.4;
    font-weight: 600;
  }

  .video-date {
    display: block;
    font-size: 0.85rem;
    color: #888;
  }
</style>

<div class="archive-container">
  {% if site.data.videos.size > 0 %}
    <div class="video-grid">
      {% for video in site.data.videos %}
        <div class="video-card">
          <div class="video-wrapper">
            <iframe 
              src="https://www.youtube.com/embed/{{ video.id }}" 
              frameborder="0" 
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
    <p style="text-align: center; color: #666; padding: 50px;">
      No videos logged in the database.
    </p>
  {% endif %}
</div>
