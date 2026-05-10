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
    /* Forces 1 column on mobile, 2 columns on desktop */
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
    background: #0a0a0a;
    border: 1px solid #00ff0033;
    border-radius: 2px;
    overflow: hidden;
    transition: all 0.3s ease;
  }

  .video-card:hover {
    border-color: #00ff00;
    box-shadow: 0 0 20px rgba(0, 255, 0, 0.15);
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
    background: #111;
    border-top: 1px solid #00ff0022;
  }

  .video-title {
    margin: 0 0 10px 0;
    font-size: 1rem !important;
    color: #00ff00 !important;
    text-shadow: 0 0 5px rgba(0, 255, 0, 0.5);
    line-height: 1.4;
    text-transform: uppercase;
  }

  .video-date {
    display: block;
    font-size: 0.8rem;
    color: #555;
    font-weight: bold;
  }

  .status-tag {
    color: #00ff00;
    font-size: 0.7rem;
    margin-bottom: 5px;
    display: block;
    opacity: 0.8;
  }
</style>

<div class="archive-container">
  <p style="color: #00ff00;">> INITIALIZING ARCHIVE_RECOVERY_PROTOCOL...</p>
  <p style="color: #00ff00;">> LOADED: {{ site.data.videos.size }} DATA_PACKETS</p>

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
            <span class="status-tag">[RECOVERED_FILE]</span>
            <h3 class="video-title">{{ video.title }}</h3>
            <span class="video-date">TIMESTAMP: {{ video.date }}</span>
          </div>
        </div>
      {% endfor %}
    </div>
  {% else %}
    <div style="border: 1px solid #ff0000; padding: 40px; text-align: center; background: rgba(255,0,0,0.05);">
      <p style="color: #ff0000; font-weight: bold;">
        [ERROR] NO INTERCEPTIONS FOUND<br>
        <span style="font-size: 0.8rem; color: #888;">CHECK CRAWLER LOGS FOR CONNECTION TIMEOUTS.</span>
      </p>
    </div>
  {% endif %}
</div>
