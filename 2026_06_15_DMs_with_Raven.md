---
title: 2026 June 15 - DMs With Raven
layout: default
permalink: /evidence-lockers/2026_06_15_DMs_with_Raven/
---

# Evidence Locker: 2026_06_15_DMs_with_Raven
#### Discord Messages Between Thomas Dall and "Raven" who is was 15 years old

Thomas Dall has had a long standing e-relationship with a girl on discord who goes by "Raven" he has said many explict things. He is aware she is underage as the evidence shows.

<div class="gallery-grid">

  {% assign images = site.static_files | where_exp: 'item', 'item.path contains "/assets/evidence/2026_06_15_DMs_with_Raven/"' %}

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
  <p><em>No images found yet.</em></p>
{% endif %}

{% include lightbox.html %}