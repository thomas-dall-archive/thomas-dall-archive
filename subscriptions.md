---
layout: default
title: "Subscriptions Vault"
permalink: /subscriptions/
---

# 📺 Subscribed Channels
**Source:** YouTube Subscriptions Registry  
**Status:** Static Mirror

This page displays a searchable archive of all indexed channel subscriptions, including descriptions and channel metadata.

---

<style>
    /* Scoped CSS for the channel search and grid cards */
    #searchBar {
        width: 100%;
        padding: 12px;
        margin-bottom: 20px;
        background-color: #1a1a1a;
        border: 1px solid #444;
        color: #fff;
        font-family: inherit;
        border-radius: 4px;
        box-sizing: border-box;
    }
    #searchBar:focus { outline: none; border-color: #777; }
    
    .channel-card {
        background-color: #111;
        border: 1px solid #333;
        border-left: 3px solid #ff0000; /* YouTube red accent line */
        padding: 15px;
        margin-bottom: 15px;
        transition: background-color 0.2s, border-color 0.2s;
        display: flex;
        gap: 15px;
        align-items: flex-start;
    }
    
    .channel-thumb {
        width: 64px;
        height: 64px;
        border-radius: 50%;
        border: 1px solid #444;
        flex-shrink: 0;
    }
    
    .channel-content {
        flex-grow: 1;
    }
    
    .channel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        border-bottom: 1px dashed #222;
        padding-bottom: 6px;
    }
    
    .channel-title {
        font-size: 1.1em;
        font-weight: bold;
        color: #fff;
        text-decoration: none;
    }
    .channel-title:hover {
        color: #ff4444;
        text-decoration: underline;
    }
    
    .sub-date {
        color: #666;
        font-size: 0.8em;
    }
    
    .channel-description {
        white-space: pre-wrap;
        overflow-wrap: break-word;
        word-break: break-word;
        font-size: 0.9em;
        line-height: 1.4;
        color: #ccc;
        max-width: 100%;
    }
    
    #statsDisplay { color: #888; font-size: 0.9em; margin-bottom: 15px; }
</style>

<input type="text" id="searchBar" placeholder="Search subscribed channels (e.g., 'Politics', 'Viking', 'True Crime')...">
<div id="statsDisplay">Initializing subscription feed...</div>
<div id="subscriptions-grid"></div>

<script>
    let allSubscriptions = [];

    // Make sure this points to the correct location of your subscriptions JSON file
    fetch('{{ "/youtube_vault.json" | relative_url }}')
        .then(response => response.json())
        .then(data => {
            // Extract the subscriptions array from the root object
            allSubscriptions = data.subscriptions || [];
            
            // Sort alphabetically by channel title
            allSubscriptions.sort((a, b) => a.snippet.title.localeCompare(b.snippet.title));
            
            renderChannels(allSubscriptions);
        })
        .catch(error => {
            document.getElementById('subscriptions-grid').innerHTML = `<p style="color: red;">Error loading subscription data: ${error}</p>`;
        });

    function renderChannels(channelsToRender) {
        const container = document.getElementById('subscriptions-grid');
        const stats = document.getElementById('statsDisplay');
        container.innerHTML = ''; 
        
        stats.innerText = `Displaying ${channelsToRender.length} subscribed channels.`;

        channelsToRender.forEach(sub => {
            const snippet = sub.snippet;
            const channelId = snippet.resourceId.channelId;
            const channelUrl = `https://youtube.com/channel/${channelId}`;
            const niceDate = new Date(snippet.publishedAt).toLocaleDateString();
            
            // Fallback default thumbnail handling if properties are missing
            const thumbUrl = snippet.thumbnails?.medium?.url || snippet.thumbnails?.default?.url || '';

            const card = document.createElement('div');
            card.className = 'channel-card';
            
            card.innerHTML = `
                <img src="${thumbUrl}" alt="${escapeHTML(snippet.title)} logo" class="channel-thumb" loading="lazy">
                <div class="channel-content">
                    <div class="channel-header">
                        <a href="${channelUrl}" target="_blank" class="channel-title">
                            ${escapeHTML(snippet.title)}
                        </a>
                        <span class="sub-date">Subscribed: ${niceDate}</span>
                    </div>
                    <div class="channel-description">${escapeHTML(snippet.description || 'No description provided.')}</div>
                </div>
            `;
            container.appendChild(card);
        });
    }

    document.getElementById('searchBar').addEventListener('keyup', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const filteredChannels = allSubscriptions.filter(sub => 
            sub.snippet.title.toLowerCase().includes(searchTerm) || 
            (sub.snippet.description && sub.snippet.description.toLowerCase().includes(searchTerm))
        );
        renderChannels(filteredChannels);
    });

    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, 
            tag => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'}[tag] || tag)
        );
    }
</script>
