---
layout: default
title: Shirt Hygiene Tracker
---

# 👕 Shirt Hygiene Tracker
*Monitoring wardrobe changes and hygiene streaks. The timer resets when a new shirt is verified.*

<div style="background: #111; border: 1px solid #333; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
    <h2 style="color: #aaa; margin-top: 0;">Current Streak</h2>
    <h1 style="color: #e74c3c; font-size: 48px; margin: 10px 0;"><span id="days-worn">0</span> Days</h1>
    <p style="color: #888;">Last changed: <span id="last-changed-date">Loading...</span></p>
    <img id="current-shirt-img" src="" style="max-width: 100%; border-radius: 5px; margin-top: 15px; border: 2px solid #444;">
</div>

### 🗄️ Historical Log
<div id="history-log" style="display: flex; flex-direction: column; gap: 15px;">
    </div>

<script>
  fetch('./shirt_data.json')
    .then(res => res.json())
    .then(data => {
      // Sort by newest first
      data.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
      
      const current = data[0];
      const currentObjDate = new Date(current.timestamp);
      const today = new Date();
      
      // Calculate Days Worn
      const diffTime = Math.abs(today - currentObjDate);
      const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
      
      document.getElementById('days-worn').innerText = diffDays;
      document.getElementById('last-changed-date').innerText = currentObjDate.toLocaleDateString() + " at " + currentObjDate.toLocaleTimeString();
      document.getElementById('current-shirt-img').src = current.image_url;

      // Build History Log
      const historyContainer = document.getElementById('history-log');
      data.forEach((item, index) => {
        if(index === 0) return; // Skip the current one for the history list
        
        const thisChange = new Date(item.timestamp);
        const nextChange = new Date(data[index-1].timestamp);
        const daysLasted = Math.floor(Math.abs(nextChange - thisChange) / (1000 * 60 * 60 * 24));

        historyContainer.innerHTML += `
            <div style="background: #1a1a1a; padding: 15px; border-radius: 5px; display: flex; align-items: center; gap: 20px;">
                <img src="${item.image_url}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 5px;">
                <div>
                    <strong style="color: #3498db;">Worn for ${daysLasted} days</strong><br>
                    <small style="color: #666;">Logged: ${thisChange.toLocaleDateString()}</small><br>
                    <span style="color: #ccc;">${item.notes || 'No notes provided.'}</span>
                </div>
            </div>
        `;
      });
    });
</script>
