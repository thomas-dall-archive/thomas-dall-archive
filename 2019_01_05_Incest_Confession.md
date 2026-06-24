---
title: 2019 January 05 - Thomas Dall's Incest Confession
layout: default
permalink: /evidence-lockers/2019_01_05_Incest_Confession/
---

# Evidence Locker: 2019_01_05_Incest_Confession
#### Initial Revelation About Thomas Dall's Confession With His Six Year Old Sister

<div class="gallery-grid">

  {% assign images = site.static_files | where_exp: 'item', 'item.path contains "/assets/evidence/2019_01_05_Incest_Confession/"' %}

  {% for image in images %}
    {% if image.extname == ".jpg" or image.extname == ".jpeg" or image.extname == ".png" or image.extname == ".gif" %}

      {% assign image_data = site.data.artworks | where: "path", image.path | first %}

      <div class="gallery-item">
        <a href="{{ image.path | relative_url }}" class="lightbox-link" data-lightbox="evidence">
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
  <p><em>No images found yet. Add them to <code>assets/evidence/locker1/</code>.</em></p>
{% endif %}

{% include lightbox.html %}