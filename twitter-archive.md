---
layout: default
title: "Tim Dooley | Transmissions Archive (X.com)"
permalink: /twitter-archive/
---

# 🐦 Transmissions Archive (X.com)
**Entity:** @Rational_Potato (Tim Dooley)  
**Status:** Static Data Vault (Offline Mirror)

This database contains a searchable, offline mirror of the subject's microblogging history. It bypasses platform virtualization and protects against spontaneous deletion or account suspension.

---

<style>
    /* Scoped CSS just for the search bar and tweet cards */
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
    }
    .tweet-date {
        font-size: 0.85em;
        color: #888;
        display: block;
        margin-bottom: 8px;
    }
    .tweet-text {
        white-space: pre-wrap; /* Preserves exact paragraph spacing */
        font-size: 0.95em;
        line-height: 1.5;
    }
    #statsDisplay { color: #888; font-size: 0.9em; margin-bottom: 15px; }
</style>

<input type="text" id="searchBar" placeholder="Query the vault (e.g., 'potato', 'FBI', 'God')...">
<div id="statsDisplay">Initializing database connection...</div>
<div id="timeline"></div>

<script>
    let allTweets = [];

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

        // Only render the first 100 on load to prevent the browser from lagging
        // The rest will instantly appear when searched
        const displayLimit = Math.min(tweetsToRender.length, 100);

        for (let i = 0; i < displayLimit; i++) {
            const tweet = tweetsToRender[i];
            const niceDate = new Date(tweet.date).toLocaleString();
            
            const card = document.createElement('div');
            card.className = 'tweet-card';
            card.innerHTML = `
                <span class="tweet-date">[ID: ${tweet.id}] - ${niceDate}</span>
                <div class="tweet-text">${escapeHTML(tweet.text)}</div>
            `;
            container.appendChild(card);
        }
        
        if (tweetsToRender.length > 100) {
            const notice = document.createElement('div');
            notice.style.color = "#888";
            notice.style.fontSize = "0.85em";
            notice.innerText = `...and ${tweetsToRender.length - 100} more hidden. Use the search bar to filter.`;
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
