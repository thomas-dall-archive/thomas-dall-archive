---
layout: default
title: Primary Source Transcript Search
---

# 🎙️ Primary Source Transcript Search
**Subject:** Tim Dooley (Main Channel: @ThePotatoofLife)  
*This database indexes the spoken word from the subject's primary broadcasts. Use this tool to verify admissions and public statements in their original context.*

<div style="background: #1a1a1a; padding: 15px; border-radius: 5px; border: 1px solid #333; margin-bottom: 25px;">
    <input type="text" id="transcriptSearch" placeholder="Search keywords (e.g., 'adonai', 'jail', 'assault')..." style="width: 100%; padding: 15px; background: #000; color: #00ff00; border: 1px solid #444; font-family: monospace; font-size: 16px;">
    <p style="font-size: 12px; color: #888; margin-top: 10px;">Results are pulled directly from the verified primary channel transcript logs. Click a result to jump to the exact timestamp.</p>
</div>

<div id="search-results">
    <p style="color: #666;">Enter a search term to begin forensic analysis...</p>
</div>

<script>
  // Updated fetch path to look within the same directory for the JSON data
  fetch('./primary_transcripts.json')
    .then(res => res.json())
    .then(data => {
      const searchInput = document.getElementById('transcriptSearch');
      const resultsContainer = document.getElementById('search-results');

      searchInput.addEventListener('input', () => {
        const query = searchInput.value.toLowerCase();
        resultsContainer.innerHTML = '';

        if (query.length < 3) return;

        let matchCount = 0;

        data.forEach(video => {
            // Check if the video has a lines array (granular search) or just text (block search)
            if (video.lines) {
                video.lines.forEach(line => {
                    if (line.text.toLowerCase().includes(query)) {
                        matchCount++;
                        appendResult(video, line.text, line.time, line.seconds);
                    }
                });
            } else if (video.text && video.text.toLowerCase().includes(query)) {
                // Fallback for block-text transcripts
                matchCount++;
                appendResult(video, video.text.substring(0, 200) + "...", "Video Start", 0);
            }
        });

        if (matchCount === 0) {
            resultsContainer.innerHTML = '<p>No matching statements found in primary channel transcripts.</p>';
        }
      });

      function appendResult(video, text, timeLabel, seconds) {
        resultsContainer.innerHTML += `
            <div style="border-left: 4px solid #3498db; background: #111; padding: 15px; margin-bottom: 10px; border-radius: 0 5px 5px 0;">
                <small style="color: #666; text-transform: uppercase; letter-spacing: 1px;">Source: ${video.date || 'Archives'} | ${video.title || 'Primary Broadcast'}</small><br>
                <p style="color: #eee; margin: 10px 0;">"...${text}..."</p>
                <a href="${video.url}&t=${seconds}s" target="_blank" style="color: #3498db; font-weight: bold; text-decoration: none;">View Original Footage (${timeLabel}) →</a>
            </div>
        `;
      }
    });
</script>
