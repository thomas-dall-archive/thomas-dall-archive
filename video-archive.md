---
layout: default
title: Video Archive
permalink: /video-archive/
---

<style>
  /* BREAK OUT: This forces the container to be wider than the theme default */
  .archive-container {
    max-width: 1200px !important; 
    margin-left: auto;
    margin-right: auto;
    padding: 10px 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  }
  
  .video-grid {
    display: grid;
    grid-template-columns: 1fr; /* 1 column on mobile */
    gap: 20px;
    margin-top: 20px;
  }

  /* 2 columns on tablets */
  @media (min-width: 750px) {
    .video-grid {
      grid-template-columns: 1fr 1fr;
    }
  }

  /* 3 columns on desktops */
  @media (min-width: 1100px) {
    .video-grid {
      grid-template-columns: 1fr 1fr 1fr;
    }
  }

  .video-card {
    background: #111;
    border: 1px solid #222;
    border-radius: 4px;
    overflow: hidden;
    transition: border 0.2s ease-in-out;
  }

  .video-card:hover {
    border-color: #ffc107;
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
    padding: 12px;
    background: #1a1a1a;
  }

  .video-title {
    margin: 0 0 5px 0;
    font-size: 0.9rem !important; /* Slightly smaller for 3-up layout */
    color: #ffc107 !important;
    line-height: 1.3;
    font-weight: 600;
  }

  .video-date {
    display: block;
    font-size: 0.75rem;
    color: #777;
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
