---
layout: default
title: Evidence Archive
---

# Live Evidence Archive
This gallery is automatically updated every 24 hours to track new uploads from monitored accountability channels.

<hr>

<div id="video-gallery" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; margin-top: 20px;">
    </div>

<script>
  // Point this to your archive.json file
  fetch('./archive.json')
    .then(response => {
      if (!response.ok) throw new Error("Archive data not found");
      return response.json();
    })
    .then(data => {
      const container = document.getElementById('video-gallery');
      
      // Sort: Newest IDs (usually later uploads) at the top
      data.reverse().forEach(video => {
        container.innerHTML += `
          <div style="border: 1px solid #333; border-radius: 12px; padding: 15px; background: #111; transition: transform 0.2s; cursor: pointer;" 
               onmouseover="this.style.transform='scale(1.02)'" 
               onmouseout="this.style.transform='scale(1)'">
            <a href="${video.url}" target="_blank" style="text-decoration: none; color: #eee;">
              <img src="${video.thumbnail}" width="100%" style="border-radius: 8px; border: 1px solid #444;">
              <h3 style="font-size: 15px; margin: 12px 0 5px 0; line-height: 1.4;">${video.title}</h3>
              <span style="font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 1px;">Source: YouTube</span>
            </a>
          </div>
        `;
      });
    })
    .catch(err => {
      document.getElementById('video-gallery').innerHTML = "<p>Archive currently updating or unavailable. Check back shortly.</p>";
    });
</script>
