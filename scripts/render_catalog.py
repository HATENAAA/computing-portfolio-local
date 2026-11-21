"""Render the shared public and local catalogue from the project records."""

import html
import json
from pathlib import Path

from review_cases import CASES

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = {
    'vision': 'Vision and reconstruction',
    'systems': 'Interaction and systems',
    'geospatial': 'Maps and spatial data',
    'signal': 'Signals and instruments',
}
CAPTIONS = {
    'hsi': 'Pavia Centre ×4, same region: ERCSR on the left and MCArb-ERCSR on the right.',
    'vrfitai': 'The VRFitAI studio with two suspended training bags.',
    'manufacturing': 'The manufacturing homepage with a preview of the inventory reconciliation screen.',
    'firewatch': 'The image workbench displaying a frame from an annotated video.',
    'signal': 'Simulated signals sampled at 1,024 Hz. Amber shows the input and ice blue the filtered output.',
    'city': 'The Shanghai historic sites atlas with a walk traced along the pedestrian network.',
    'bathymetry': 'Held-out predictions and reference depths for a synthetic example.',
    'medical': 'The patient and doctor views of the team’s health-screening system.',
}
SEARCH_ALIASES = {
    'hsi': 'MCArb ERCSR SSPSR Pavia Centre Chikusei ROSIS PSNR SAM 插值 光谱',
    'vrfitai': 'WebXR DeepSeek 试练 沙袋 训练恢复',
    'manufacturing': 'BOM MES 库存对账 预留 流水 制造执行',
    'firewatch': 'FURG YOLO ONNX 检测框 检测评测 火灾 视频事件',
    'signal': 'Welch H1 FFT PhysioNet MIT-BIH 心电 混叠 示波器',
    'city': '上海 步行路线 路网 OpenStreetMap 一大纪念馆',
    'bathymetry': 'SVR SVM 支持向量回归 ICESat-2 Sentinel-2 光子 轨迹',
    'medical': '体检 预约 号源 医生 报告',
}
def bilingual(en, zh, tag='span', attributes=''):
    return f'<{tag}{attributes} data-en="{html.escape(en)}">{html.escape(zh)}</{tag}>'


def app_link(project, contents, style, hidden=''):
    return (f'<a {hidden}class="{style}" data-app="{project}" data-app-path="/" '
            f'href="projects/offline.html?project={project}&amp;path=/" '
            f'target="_blank" rel="noopener">{contents}</a>')


def launch_directory(projects):
    links = []
    for item in projects:
        project = item['id']
        title = bilingual(*CASES[project][0], 'strong')
        status = bilingual('Checking', '正在检查', attributes=f' class="status" data-service="{project}" data-state="unknown"')
        links.append(app_link(project, title + status, 'launch-tile'))
    return '\n'.join(links)


def card(item, featured):
    e = html.escape
    project = item['id']
    (en_title, zh_title), (en_role, zh_role), (en_summary, _) = CASES[project][:3]
    title_id = f'project-title-{project}'
    detail = f'projects/review/{project}-zh.html'
    category = bilingual(CATEGORIES[item['category']], item['categoryLabel'])
    title = bilingual(en_title, zh_title)
    role = bilingual(en_role, zh_role, 'p', ' class="project-role"')
    terms = e(' '.join((en_title, zh_title, item['title'], item['stack'], item['categoryLabel'],
                        CATEGORIES[item['category']], SEARCH_ALIASES[project])))
    local_label = ('Run full system', '运行完整系统') if project == 'medical' else ('Open local app', '运行本地应用')
    secondary = app_link(project, bilingual(*local_label), 'launch-app', 'hidden data-local-only ')
    award = bilingual('Outstanding Project · Summer Practicum', item['award'],
                      attributes=' class="project-award"') if item.get('award') else ''
    loading = 'loading="eager"' if featured else 'loading="lazy"'
    return f'''<article class="project" id="project-{project}" data-id="{project}" data-category="{item["category"]}" data-terms="{terms}" aria-labelledby="{title_id}">
  <div class="index-cover"><img src="preview/{e(item["image"])}" alt="{e(item["caption"])}" data-en-alt="{e(CAPTIONS[project])}" width="1440" height="900" {loading}></div>
  <div class="index-copy">
    <div class="project-meta">{category}{role}{award}</div>
    <h3 id="{title_id}">{title}</h3>
    {bilingual(en_summary, item['summary'], 'p', ' class="project-summary"')}
    <p class="project-stack">{e(item['stack'])}</p>
    <div class="card-actions">
      <a class="case-link" data-case href="{detail}" aria-describedby="{title_id}" data-en="View project →">查看项目 →</a>
      {secondary}
    </div>
  </div>
</article>'''


def render(dest=ROOT):
    projects = json.loads((ROOT / 'assets/projects.json').read_text(encoding='utf-8'))
    cards = '\n'.join(card(item, featured=index < 2) for index, item in enumerate(projects))
    template = (ROOT / 'scripts/catalog.template.html').read_text(encoding='utf-8')
    dest.mkdir(parents=True, exist_ok=True)
    count = len(projects)
    count_label = bilingual(f'{count} projects', f'{count} 个项目')
    text = (template.replace('{{PROJECT_CARDS}}', cards)
            .replace('{{PROJECT_COUNT}}', count_label)
            .replace('{{LOCAL_LAUNCHERS}}', launch_directory(projects)))
    (dest / 'index.html').write_bytes(text.encode('utf-8'))
    if dest.resolve() == ROOT:
        (dest / 'local.html').write_bytes(text.encode('utf-8'))


if __name__ == '__main__':
    render()
