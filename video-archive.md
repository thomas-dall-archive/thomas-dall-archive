---
layout: page
title: Video Archive
permalink: /archive/
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

<style>
  .archive-container {
    max-width: 1000px;
    margin: 0 auto;
    padding: 20px;
  }
  .video-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 30px;
  }
  .video-card {
    background: #1a1a1a;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    transition: transform 0.2s;
  }
  .video-card:hover {
    transform: translateY(-5px);
  }
  .video-wrapper {
    position: relative;
    padding-bottom: 56.25%; /* 16:9 Aspect Ratio */
    height: 0;
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
    color: #eee;
  }
  .video-title {
    margin: 0 0 10px 0;
    font-size: 1.1rem;
    line-height: 1.4;
  }
  .video-date {
    font-size: 0.8rem;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 1px;
  }
  .no-videos {
    text-align: center;
    color: #666;
    font-style: italic;
  }
</style>
 
