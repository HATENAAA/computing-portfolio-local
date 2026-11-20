class FirewatchNavigation extends HTMLElement {
  connectedCallback() {
    const tasks = [
      ['image', '/', '图像检测', 'image'],
      ['video', '/video', '视频任务', 'video'],
      ['model', '/model', '模型对照', 'model'],
      ['evaluation', '/evaluation', '检测评测', 'evaluation'],
    ];
    const header = document.createElement('header');
    header.className = 'fw-rail-inner';
    const brand = document.createElement('a');
    brand.className = 'fw-brand';
    brand.href = '/';
    brand.textContent = '火焰检测';
    header.append(brand);
    const nav = document.createElement('nav');
    nav.setAttribute('aria-label', '火焰检测功能导航');
    for (const [id, href, label, icon] of tasks) {
      const link = document.createElement('a');
      const mark = document.createElement('i');
      mark.className = 'fw-nav-icon icon-' + icon;
      mark.setAttribute('aria-hidden', 'true');
      link.href = href;
      link.append(mark, label);
      if (id === this.getAttribute('current')) link.setAttribute('aria-current', 'page');
      nav.append(link);
    }
    header.append(nav);
    this.replaceChildren(header);
  }
}
customElements.define('fw-navigation', FirewatchNavigation);
