---
title: Art Gallery
layout: default
permalink: /gallery/
---

<h1>Art Gallery</h1>

<div class="gallery-grid">
  {% assign art_images = site.static_files 
      | where_exp: "item", "item.path contains '/assets/art/'" 
      | where_exp: "item", "item.extname == '.jpg' or item.extname == '.jpeg' or item.extname == '.png' or item.extname == '.gif'" %}
  
  {% for image in art_images %}
    <a href="{{ image.path | relative_url }}" target="_blank">
      <img src="{{ image.path | relative_url }}" 
           alt="{{ image.basename | replace: '-', ' ' | replace: '_', ' ' }}" 
           loading="lazy">
    </a>
  {% endfor %}
</div>

{% if art_images.size == 0 %}
  <p><em>No images found yet</em></p>
{% endif %}