---
title: 2019 November 22 - Thomas Dall as imBed chatting with teenagers
layout: default
permalink: /evidence-lockers/2019_11_22_Chatting_With_Teens/
---

# Evidence Locker: 2019_11_22_Chatting_With_Teens
#### Discord Messages Between Thomas Dall and Teenagers as young as 13

Thomas Dall DMs with "Kota" from the "Kota Files" that he denies even knowing. Also Thomas Dall participating in a teenage dating server, there is identity resolution between Thomas as he posts his demographics and speaks about his experiences with "STALKING GANGS." Furthermore it was revealed and the Discord Mod Ruben that Thomas was kicked from the "What is Life" server because he was being "creepy towards girls"

It's important to remember that Thomas self-admits he's 32 years old while talking to teens.

Ages: 
"Eddie and Julia:" a couple that use one discord account - 15
"SopelSky:" boy - 15
"Kota:" girl - 17

<div class="gallery-grid">

  {% assign images = site.static_files | where_exp: 'item', 'item.path contains "/assets/evidence/2019_11_22_Chatting_With_Teens/"' %}

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