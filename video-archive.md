---
layout: default
title: Video Archive
permalink: /video-archive/
---

<style>
  /* Forensic Archive Styling */
  .archive-container {
    padding: 10px 0;
    font-family: 'Monaco', 'Courier New', monospace;
  }
  
  .video-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 25px;
    margin-top: 20px;
  }

  .video-card {
    background: #111;
    border: 1px solid #333;
    border-radius: 4px;
    overflow: hidden;
    transition: all 0.3s ease;
  }

  .video-card:hover {
    border-color: #00ff00;
    box-shadow: 0 0 15px rgba(0, 255, 0, 0.2);
  }

  .video-wrapper {
    position: relative;
    padding-bottom: 56.25%; /* 16:9 Aspect */
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
    margin: 0 0 8px 0;
    font-size: 0.95rem !important;
    color: #00ff00 !important; /* Terminal Green */
    line-height: 1.3;
    font-weight: bold;
  }

  .video-date {
    display: block;
    font-size: 0.75rem;
    color: #888;
    letter-spacing: 1px;
  }

  .status-tag {
    color: #00ff00;
    font-size: 0.7rem;
    margin-bottom: 5px;
    display: block;
  }
</style>

<div class="archive-container">
  <p>🔍 [STATUS: SCANNING DATABASE...]</p>

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
            <span class="status-tag">STATUS: INTERCEPTED</span>
            <h3 class="video-title">{{ video.title }}</h3>
            <span class="video-date">LOG_DATE: {{ video.date }}</span>
          </div>
        </div>
      {% endfor %}
    </div>
  {% else %}
    <div style="border: 1px dashed #444; padding: 40px; text-align: center;">
      <p class="no-videos" style="color: #666;">
        NO DATA PACKETS FOUND.<br>
        <span style="font-size: 0.8rem;">Ensure youtube_crawler.py is executing correctly.</span>
      </p>
    </div>
  {% endif %}
</div>
