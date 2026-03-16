document.getElementById('go').addEventListener('click', doSearch);
document.getElementById('search').addEventListener('keypress', function(e) {
  if (e.key === 'Enter') doSearch();
});

function doSearch() {
  const q = document.getElementById('search').value.trim();
  if (!q) return;

  const results = document.getElementById('results');
  results.innerHTML = '<p style="font-size:12px;color:rgba(255,255,255,0.4);">Searching...</p>';

  fetch('https://indiestack.ai/api/tools/search?q=' + encodeURIComponent(q) + '&limit=5')
    .then(r => r.json())
    .then(data => {
      if (!data.tools || data.tools.length === 0) {
        results.innerHTML = '<p style="font-size:12px;color:rgba(255,255,255,0.4);">No results found.</p>';
        return;
      }
      results.innerHTML = data.tools.map(t =>
        '<a href="' + (t.indiestack_url || ('https://indiestack.ai/tool/' + t.slug)) + '" target="_blank" class="result-item">' +
        '<strong>' + t.name + '</strong>' +
        '<span>' + (t.tagline || '') + '</span>' +
        '</a>'
      ).join('');
    })
    .catch(function() {
      results.innerHTML = '<p style="font-size:12px;color:rgba(255,255,255,0.4);">Something went wrong.</p>';
    });
}
