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
  let link = document.querySelector("link[rel~='icon']");
  if (!link) {
      link = document.createElement('link');
      link.rel = 'icon';
      document.head.appendChild(link);
  }
  link.href = "data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>👕</text></svg>";
  const fetchUrl = './shirt_data.json?t=' + new Date().getTime();

  fetch(fetchUrl)
    .then(res => {
      if (!res.ok) throw new Error("Database file not found (HTTP " + res.status + ")");
      return res.json();
    })
    .then(data => {
      if (!data || data.length === 0) throw new Error("Database is empty.");

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
      historyContainer.innerHTML = ""; // Clear out anything old
      
      data.forEach((item, index) => {
        if(index === 0) return; // Skip the current one for the history list
        
        const thisChange = new Date(item.timestamp);
        // If there is a previous shirt in the list, calculate how long THIS shirt lasted
        const nextChange = data[index - 1] ? new Date(data[index - 1].timestamp) : new Date();
        const daysLasted = Math.floor(Math.abs(nextChange - thisChange) / (1000 * 60 * 60 * 24));

        historyContainer.innerHTML += `
            <div style="background: #1a1a1a; padding: 15px; border-radius: 5px; display: flex; align-items: center; gap: 20px; margin-bottom: 10px; border: 1px solid #333;">
                <img src="${item.image_url}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 5px;">
                <div>
                    <strong style="color: #3498db;">Worn for ${daysLasted} days</strong><br>
                    <small style="color: #666;">Logged: ${thisChange.toLocaleDateString()}</small><br>
                    <span style="color: #ccc;">${item.notes || 'No notes provided.'}</span>
                </div>
            </div>
        `;
      });
    })
    .catch(err => {
      // Print the exact error directly to the screen so we know what's broken
      document.getElementById('last-changed-date').innerHTML = `<span style="color: red; font-weight: bold;">ERROR: ${err.message}</span>`;
    });
</script>
