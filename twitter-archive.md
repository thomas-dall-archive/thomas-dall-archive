---
layout: default
title: "Tim Dooley | Transmissions Archive (X.com)"
permalink: /twitter-archive/
---

# 📡 Transmissions Archive (X.com)
**Entity:** @Rational_Potato (Tim Dooley)  
**Status:** Static Data Vault (Offline Mirror)

This database contains a searchable, offline mirror of the subject's microblogging history. It bypasses platform virtualization and protects against spontaneous deletion or account suspension.

---

<style>
    /* Scoped CSS for search engine and tweet cards */
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
    
    .tweet-card {
        background-color: #111;
        border: 1px solid #333;
        border-left: 3px solid #555;
        padding: 15px;
        margin-bottom: 15px;
        transition: background-color 0.2s, border-color 0.2s;
        display: flex;
        flex-direction: column;
    }
    /* Highlights the card if a visitor uses a deep-link anchor URL */
    .tweet-card:target {
        border-left-color: #00ff00;
        background-color: #161a16;
    }
    
    .tweet-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.85em;
        margin-bottom: 10px;
        border-bottom: 1px dashed #222;
        padding-bottom: 6px;
    }
    
    .tweet-source-link {
        color: #888;
        text-decoration: none;
        display: inline-block;
    }
    .tweet-source-link:hover {
        color: #4a90e2;
        text-decoration: underline;
    }
    
    .anchor-link {
        text-decoration: none;
        opacity: 0.4;
        transition: opacity 0.2s;
    }
    .anchor-link:hover {
        opacity: 1;
    }
    
    .tweet-text {
        white-space: pre-wrap; /* Preserves exact paragraph spacing */
        font-size: 0.95em;
        line-height: 1.5;
        margin-bottom: 12px;
    }
    
    .tweet-footer {
        display: flex;
        justify-content: flex-end;
        font-size: 0.8em;
    }
    
    .view-on-x {
        color: #4a90e2;
        text-decoration: none;
        font-weight: bold;
    }
    .view-on-x:hover {
        text-decoration: underline;
    }
    
    #statsDisplay { color: #888; font-size: 0.9em; margin-bottom: 15px; }
</style>

<input type="text" id="searchBar" placeholder="Query the vault (e.g., 'potato', 'FBI', 'God')...">
<div id="statsDisplay">Initializing database connection...</div>
<div id="timeline"></div>

<script>
    let allTweets = [];
    const TARGET_USER = 'Rational_Potato';

    // Fetch the JSON from the repository root using Jekyll's relative_url filter
    fetch('{{ "/tweet_vault.json" | relative_url }}')
        .then(response => response.json())
        .then(data => {
            allTweets = Object.values(data);
            allTweets.sort((a, b) => new Date(b.date) - new Date(a.date));
            renderTweets(allTweets);
        })
        .catch(error => {
            document.getElementById('timeline').innerHTML = `<p style="color: red;">Error establishing database link: ${error}</p>`;
        });

    function renderTweets(tweetsToRender) {
        const container = document.getElementById('timeline');
        const stats = document.getElementById('statsDisplay');
        container.innerHTML = ''; 
        
        stats.innerText = `Displaying ${tweetsToRender.length} recorded transmissions.`;

        // Render first 100 on load to keep the page snappy; the rest match instantly via search
        const displayLimit = Math.min(tweetsToRender.length, 100);

        for (let i = 0; i < displayLimit; i++) {
            const tweet = tweetsToRender[i];
            const niceDate = new Date(tweet.date).toLocaleString();
            
            // Generate direct source link to X.com
            const sourceUrl = `https://x.com/${TARGET_USER}/status/${tweet.id}`;
            
            const card = document.createElement('div');
            card.className = 'tweet-card';
            card.id = `tweet-${tweet.id}`; // Sets up internal deep link anchors
            
            card.innerHTML = `
                <div class="tweet-header">
                    <a href="${sourceUrl}" target="_blank" class="tweet-source-link" title="Open original post on X.com">
                        🗁 [ID: ${tweet.id}] — ${niceDate}
                    </a>
                    <a href="#tweet-${tweet.id}" class="anchor-link" title="Copy local deep-link">🔗</a>
                </div>
                <div class="tweet-text">${escapeHTML(tweet.text)}</div>
                <div class="tweet-footer">
                    <a href="${sourceUrl}" target="_blank" class="view-on-x">[ VIEW ON X.COM ]</a>
                </div>
            `;
            container.appendChild(card);
        }
        
        if (tweetsToRender.length > 100) {
            const notice = document.createElement('div');
            notice.style.color = "#888";
            notice.style.fontSize = "0.85em";
            notice.style.padding = "10px 0";
            notice.style.textAlign = "center";
            notice.innerText = `...and ${tweetsToRender.length - 100} more transmissions indexed. Use the filter field above to pull older files from memory.`;
            container.appendChild(notice);
        }
    }

    document.getElementById('searchBar').addEventListener('keyup', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const filteredTweets = allTweets.filter(tweet => 
            tweet.text.toLowerCase().includes(searchTerm)
        );
        renderTweets(filteredTweets);
    });

    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, 
            tag => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'}[tag] || tag)
        );
    }
</script>
