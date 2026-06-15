---
layout: default
title: "Live Observation Room"
---

# 📡 Live Observation Room

{% if site.data.stream.id == "OFFLINE" %}
    <p><em>The Observation Room is currently offline.</em></p>
{% else %}
    <div class="video-container" style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%;">
        <iframe src="https://rumble.com/embed/v{{ site.data.stream.id }}/?pub=4pe3y4" 
                style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;" 
                frameborder="0" allowfullscreen>
        </iframe>
    </div>
{% endif %}
