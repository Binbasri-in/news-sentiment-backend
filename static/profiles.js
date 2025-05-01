async function fetchProfiles() {
    const res = await fetch("/profiles/");
    const data = await res.json();
    console.log(data); // Print the result into the console
    const list = document.getElementById("profile-list");
    list.innerHTML = "";
    data.forEach(p => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${p.name}</td>
        <td><a href="${p.base_url}" target="_blank">${p.base_url}</a></td>
        <td>${p.language}</td>
        <td>${p.crawling_strategy}</td>
        <td>${p.crawling_state || "Idle"}</td>
        <td>${p.last_crawling || "N/A"}</td>
        <!-- <td>
          <button class="btn btn-sm ${p.active ? 'btn-success' : 'btn-secondary'}" onclick="toggleActive('${p.name}', ${p.active})">
            ${p.active ? 'Active' : 'Inactive'}
          </button>
        </td> -->
        <td>
          <button class="btn btn-sm btn-primary" onclick="performCrawling('${p.name}')">🌐 Crawl</button>
          <button class="btn btn-sm btn-info" onclick="performAnalysis('${p.name}')">📊 Analyze</button>
          <button class="btn btn-sm btn-danger" onclick="deleteProfile('${p.name}')">🗑️</button>
        </td>
      `;
      list.appendChild(row);
    });
  }
  
  document.getElementById("profile-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.target;
    const profile = {
      name: form.name.value,
      base_url: form.base_url.value,
      language: form.language.value,
      crawling_strategy: form.crawling_strategy.value
    };
    await fetch("/profiles/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile)
    });
    form.reset();
    fetchProfiles();
  });
  
  async function deleteProfile(name) {
    await fetch(`/profiles/${name}`, { method: "DELETE" });
    fetchProfiles();
  }
  
  async function toggleActive(name, currentState) {
    await fetch(`/profiles/${name}/toggle-active`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ active: !currentState })
    });
    fetchProfiles();
  }
  
  async function performCrawling(name) {
    await fetch(`/profiles/${name}/crawl`, { method: "POST" });
    fetchProfiles();
  }
  
  async function performAnalysis(name) {
    await fetch(`/profiles/${name}/analyze`, { method: "POST" });
    fetchProfiles();
  }

// call profiles on load
window.onload = function() {
    fetchProfiles();
};