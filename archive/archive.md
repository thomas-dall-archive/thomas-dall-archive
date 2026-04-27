---
layout: default
title: Video Evidence Archive
---

# Live Evidence Archive
*This page automatically syncs new content from monitored channels every 24 hours.*

<div id="video-gallery" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; margin-top: 30px;">
    </div>

<script>
  fetch('./archive.json')
    .then(res => res.json())
    .then(data => {
      const container = document.getElementById('video-gallery');
      data.reverse().forEach(v => {
        container.innerHTML += `
          <div style="border: 1px solid #333; border-radius: 8px; padding: 10px; background: #111;">
            <a href="${v.url}" target="_blank" style="text-decoration: none; color: #eee;">
              <img src="${v.thumbnail}" width="100%" style="border-radius: 4px;">
              <h4 style="font-size: 14px; margin: 10px 0 0 0;">${v.title}</h4>
            </a>
          </div>`;
      });
    });
</script>
