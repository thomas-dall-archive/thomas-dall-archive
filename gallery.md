---
title: Art Gallery
layout: default
permalink: /gallery/
---

# Art Gallery
#### The MSPAINT Machinations of Thomas Dall

<div class="masonry-container">

  {% assign images = site.static_files | where_exp: 'item', 'item.path contains "/assets/art/" or item.path contains "/assets/ai-slop/"' %}

  {% for image in images %}
    {% if image.extname == ".jpg" or image.extname == ".jpeg" or image.extname == ".png" or image.extname == ".gif" %}

      {% comment %}Subfolder detection (works even if no subfolders){% endcomment %}
      {% assign path_parts = image.path | split: '/' %}
      
      {% capture index %}{{ path_parts.size | minus: 2 }}{% endcapture %}
      {% assign subfolder = path_parts[index] | replace: '-', ' ' | replace: '_', ' ' | capitalize %}

      {% if subfolder != prev_subfolder and subfolder != nil %}
        <h2 class="gallery-section">{{ subfolder }}</h2>
        {% assign prev_subfolder = subfolder %}
      {% endif %}

      {% assign image_data = site.data.artworks | where: "path", image.path | first %}

      <div class="gallery-item">
        <a href="{{ image.path | relative_url }}" class="lightbox-link" data-lightbox="artgallery">
          <img src="{{ image.path | relative_url }}" 
               alt="{{ image_data.title | default: image.basename | replace: '-', ' ' | replace: '_', ' ' }}" 
               loading="lazy">
        </a>
        <div class="image-info">
          <strong>{{ image_data.title | default: image.basename | replace: '-', ' ' | replace: '_', ' ' }}</strong>
          {% if image_data.medium %}<br><small>{{ image_data.medium }}</small>{% endif %}
          {% if image_data.description %}<br><small>{{ image_data.description }}</small>{% endif %}
        </div>
      </div>

    {% endif %}
  {% endfor %}

</div>

{% if images.size == 0 %}
  <p><em>No images found yet. </em></p>
{% endif %}

{% include lightbox.html %}