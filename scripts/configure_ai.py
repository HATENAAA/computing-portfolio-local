"""Configure the local server's AI key without echoing it to the terminal."""
from pathlib import Path
import getpass
import json
import os
import re
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def save_key(path, key):
    text = path.read_text() if path.exists() else ''
    values = {'AI_API_KEY': key}
    if not re.search(r'^AI_BASE_URL=\S+', text, re.M):
        values['AI_BASE_URL'] = 'https://api.deepseek.com'
    if not re.search(r'^AI_MODEL=\S+', text, re.M):
        values['AI_MODEL'] = 'deepseek-flash'
    lines = text.splitlines()
    for name, value in values.items():
        lines = [line for line in lines if not re.match(r'^\s*(?:export\s+)?' + name + r'\s*=', line)]
        lines.append(name + '=' + json.dumps(value))
    fd, temporary = tempfile.mkstemp(prefix='.ai-config-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as file:
            file.write('\n'.join(lines) + '\n')
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)

def main():
    if not sys.stdin.isatty():
        raise SystemExit('请双击“配置AI助手.command”，在终端中填写API Key。')
    print('VRFitAI · DeepSeek助手配置\n')
    print('请在 https://platform.deepseek.com/api_keys 创建API Key。')
    print('输入时不会显示字符；Key仅保存到本机vrfitai/.env。')
    key = getpass.getpass('粘贴API Key并按回车：').strip()
    if not key:
        print('没有输入Key，配置保持不变。')
        return
    if any(c.isspace() for c in key):
        raise SystemExit('API Key含空白字符，请检查后重新配置。')
    save_key(ROOT/'vrfitai/.env', key)
    print('\n配置已保存。返回助手页并点击“重新检查配置”即可使用。')
    print('进入VRFitAI的助手页检查配置；接口与模型可在.env中修改。')

if __name__ == '__main__':
    main()
