---
layout: default
title: "Live Observation Room"
---
# 📡 Live Observation Room
{% if site.data.stream.id == "OFFLINE" %}
    <p><em>The Observation Room is currently offline.</em></p>
{% else %}
    <div class="video-container">
        <iframe src="https://rumble.com/embed/v{{ site.data.stream.id }}/?pub=4pe3y4" ...></iframe>
    </div>
{% endif %}
