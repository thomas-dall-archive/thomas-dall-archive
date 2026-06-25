---
layout: default
title: "Live Observation Room"
---

# 📡 Live Observation Room

{% if site.data.stream.id == "OFFLINE" %}
<div class="offline-placeholder" style="text-align: center; margin: 40px 0;">
    <img src="{{ '/assets/images/offline-placeholder.png' | relative_url }}" 
         alt="Observation Room Offline" 
         style="max-width: 300px; border-radius: 10px; margin-bottom: 15px;">
    <p><em>The Observation Room is currently offline.</em></p>
</div>
{% else %}
<div class="video-container" style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%;">
<iframe src="https://rumble.com/embed/v{{ site.data.stream.id }}/?pub=4pe3y4" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;" frameborder="0" allowfullscreen>
</iframe>
</div>
{% endif %}
