---
layout: default
title: "Video Evidence Archive"
---

# 📼 Video Evidence Archive
*An automated, chronological collection of broadcasts and external commentary regarding Thomas Dall / Tim Dooley.*

<hr style="border-color: #444; margin-bottom: 30px;">

<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px;">
  {% if site.data.videos %}
    {% for video in site.data.videos %}
      <div style="background: #111; border: 1px solid #333; padding: 10px; border-radius: 5px;">
        <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; margin-bottom: 10px;">
          <iframe style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;" 
                  src="https://www.youtube.com/embed/{{ video.id }}" 
                  frameborder="0" allowfullscreen>
          </iframe>
        </div>
        <p style="font-size: 0.9em; margin: 0;"><strong>{{ video.title }}</strong></p>
        <p style="font-size: 0.8em; color: #888; margin: 0;">Logged: {{ video.date }}</p>
      </div>
    {% endfor %}
  {% else %}
    <p>No video evidence has been logged yet. The crawler runs every 6 hours.</p>
  {% endif %}
</div>
