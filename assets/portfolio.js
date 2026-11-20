const catalog = document.querySelector('[data-catalog]');
if (catalog) {
  const initial = new URLSearchParams(location.search);
  const english = initial.get('lang') === 'en' ||
    (!initial.has('lang') && location.protocol !== 'file' && !document.documentElement.hasAttribute('data-local-hub'));
  if (english) {
    document.documentElement.lang = 'en';
    document.title = 'Technical portfolio · Jiawei Wang';
    for (const node of catalog.querySelectorAll('[data-en]')) node.textContent = node.dataset.en;
    for (const node of catalog.querySelectorAll('[data-en-alt]')) node.alt = node.dataset.enAlt;
    for (const node of catalog.querySelectorAll('[data-en-aria-label]')) node.setAttribute('aria-label', node.dataset.enAriaLabel);
    for (const node of catalog.querySelectorAll('[data-en-placeholder]')) node.placeholder = node.dataset.enPlaceholder;
    for (const link of catalog.querySelectorAll('[data-en-href]')) link.href = link.dataset.enHref;
    for (const link of catalog.querySelectorAll('[data-case]')) link.href = link.getAttribute('href').replace('-zh.html', '-en.html');
  }

  const language = catalog.querySelector('[data-language]');
  language.textContent = english ? '中文' : 'English';
  language.lang = language.hreflang = english ? 'zh' : 'en';

  function updateLanguageLink() {
    const alternate = new URL(location.href);
    alternate.searchParams.set('lang', english ? 'zh' : 'en');
    language.href = alternate.href;
  }

  const filters = [...catalog.querySelectorAll('[data-filter]')];
  const cards = [...catalog.querySelectorAll('[data-category]')];
  const input = catalog.querySelector('#project-query');
  const countNode = catalog.querySelector('#project-count');
  const empty = catalog.querySelector('#empty-projects');
  let field = 'all';

  function renderProjects() {
    const words = input.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    for (const button of filters) button.setAttribute('aria-pressed', String(button.dataset.filter === field));
    let count = 0;
    for (const card of cards) {
      const terms = card.dataset.terms.toLocaleLowerCase();
      card.hidden = (field !== 'all' && card.dataset.category !== field) || !words.every(word => terms.includes(word));
      if (!card.hidden) count++;
    }
    empty.hidden = count !== 0;
    countNode.textContent = english ? count + (count === 1 ? ' project' : ' projects') : count + ' 个项目';
  }

  function storeFilters() {
    renderProjects();
    const url = new URL(location.href);
    const query = input.value.trim();
    if (field === 'all') url.searchParams.delete('field');
    else url.searchParams.set('field', field);
    if (query) url.searchParams.set('q', query);
    else url.searchParams.delete('q');
    if (url.href !== location.href) {
      try { history.replaceState(null, '', url); } catch {}
    }
    updateLanguageLink();
  }

  function restore() {
    const state = new URLSearchParams(location.search);
    field = filters.find(button => button.dataset.filter === state.get('field'))?.dataset.filter || 'all';
    input.value = state.get('q') || '';
    renderProjects();
    updateLanguageLink();
  }

  catalog.querySelector('.project-tools').hidden = false;
  for (const button of filters) button.onclick = () => { field = button.dataset.filter; storeFilters(); };
  input.addEventListener('input', storeFilters);
  restore();
  window.addEventListener('pageshow', restore);
  window.addEventListener('popstate', restore);
  window.addEventListener('hashchange', updateLanguageLink);

  for (const link of catalog.querySelectorAll('[data-case]')) {
    const base = link.href;
    link.addEventListener('click', () => {
      const destination = new URL(base);
      const state = new URLSearchParams(location.search);
      for (const key of ['field', 'q']) if (state.has(key)) destination.searchParams.set(key, state.get(key));
      link.href = destination.href;
    });
  }

  const menu = catalog.querySelector('.run-menu');
  menu.addEventListener('keydown', event => {
    if (event.key === 'Escape' && menu.open) {
      menu.open = false;
      menu.querySelector('summary').focus();
    }
  });
  menu.addEventListener('click', event => {
    if (event.target.closest('a')) menu.open = false;
  });
  document.addEventListener('click', event => {
    if (!menu.contains(event.target)) menu.open = false;
  });
}
