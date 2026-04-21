import json
import re
import os

# 1. 加载 pinyin_map.json
with open('pinyin_map.json', 'r', encoding='utf-8') as f:
    pinyin_data = json.load(f)

# 2. 提取韵母
shengmu_list_for_split = ['zh', 'ch', 'sh', 'b', 'p', 'm', 'f', 'd', 't', 'n', 'l', 'g', 'k', 'h', 'j', 'q', 'x', 'r', 'z', 'c', 's', 'y', 'w']
tone_marks = {
    'ā': 'a', 'á': 'a', 'ǎ': 'a', 'à': 'a',
    'ō': 'o', 'ó': 'o', 'ǒ': 'o', 'ò': 'o',
    'ē': 'e', 'é': 'e', 'ě': 'e', 'è': 'e',
    'ī': 'i', 'í': 'i', 'ǐ': 'i', 'ì': 'i',
    'ū': 'u', 'ú': 'u', 'ǔ': 'u', 'ù': 'u',
    'ǖ': 'ü', 'ǘ': 'ü', 'ǚ': 'ü', 'ǜ': 'ü'
}

def remove_tone(p):
    res = ""
    for c in p: res += tone_marks.get(c, c)
    return res

def split_pinyin(p):
    base = remove_tone(p)
    for sm in shengmu_list_for_split:
        if base.startswith(sm): return sm, base[len(sm):]
    return '', base

yunmu_set = set()
for p in pinyin_data:
    _, y = split_pinyin(p)
    if y: yunmu_set.add(y)

# 常用顺序
standard_yunmu = ['a', 'o', 'e', 'i', 'u', 'ü', 'ai', 'ei', 'ui', 'ao', 'ou', 'iu', 'ie', 'üe', 'er', 'an', 'en', 'in', 'un', 'ün', 'ang', 'eng', 'ing', 'ong', 'ia', 'ua', 'uo', 'uai', 'ian', 'iang', 'iong', 'uan', 'uang', 'iao']
yunmu_list = [y for y in standard_yunmu if y in yunmu_set]
for y in sorted(list(yunmu_set)):
    if y not in yunmu_list: yunmu_list.append(y)

# 3. 读取 index.html
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 数据段替换
data_start_tag = '// ==================== 数据 ===================='
canvas_start_tag = '// ==================== Canvas 设置 ===================='

start_idx = html.find(data_start_tag)
end_idx = html.find(canvas_start_tag)

if start_idx != -1 and end_idx != -1:
    # 使用紧凑 JSON 减少文件行数
    pinyin_data_js = json.dumps(pinyin_data, ensure_ascii=False)
    yunmu_js = json.dumps(yunmu_list, ensure_ascii=False)
    
    new_data_section = f"""{data_start_tag}
        const shengmu = ['', 'b', 'p', 'm', 'f', 'd', 't', 'n', 'l', 'g', 'k', 'h', 'j', 'q', 'x', 'zh', 'ch', 'sh', 'r', 'z', 'c', 's', 'y', 'w'];
        const yunmu = {yunmu_js};

        // 拼音数据库
        const pinyinData = {pinyin_data_js};

        const toneChars = {{
            'a': ['ā', 'á', 'ǎ', 'à'], 'o': ['ō', 'ó', 'ǒ', 'ò'], 'e': ['ē', 'é', 'ě', 'è'],
            'i': ['ī', 'í', 'ǐ', 'ì'], 'u': ['ū', 'ú', 'ǔ', 'ù'], 'ü': ['ǖ', 'ǘ', 'ǚ', 'ǜ']
        }};

        function markPinyin(base, tone) {{
            if (tone < 1 || tone > 4) return base;
            const idx = tone - 1;
            let res = base.replace('ü', 'v'); 
            if (res.includes('a')) res = res.replace('a', toneChars['a'][idx]);
            else if (res.includes('o')) res = res.replace('o', toneChars['o'][idx]);
            else if (res.includes('e')) res = res.replace('e', toneChars['e'][idx]);
            else if (res.includes('iu')) res = res.replace('u', toneChars['u'][idx]);
            else if (res.includes('ui')) res = res.replace('i', toneChars['i'][idx]);
            else if (res.includes('i')) res = res.replace('i', toneChars['i'][idx]);
            else if (res.includes('u')) res = res.replace('u', toneChars['u'][idx]);
            else if (res.includes('v')) res = res.replace('v', toneChars['ü'][idx]);
            return res.replace('v', 'ü');
        }}

        const validPinyinMap = {{}};
        const validPinyinSet = new Set();
        (function buildValid() {{
            const smList = ['zh', 'ch', 'sh', 'b', 'p', 'm', 'f', 'd', 't', 'n', 'l', 'g', 'k', 'h', 'j', 'q', 'x', 'r', 'z', 'c', 's', 'y', 'w'];
            const toneMap = {{
                'ā': 'a', 'á': 'a', 'ǎ': 'a', 'à': 'a',
                'ō': 'o', 'ó': 'o', 'ǒ': 'o', 'ò': 'o',
                'ē': 'e', 'é': 'e', 'ě': 'e', 'è': 'e',
                'ī': 'i', 'í': 'i', 'ǐ': 'i', 'ì': 'i',
                'ū': 'u', 'ú': 'u', 'ǔ': 'u', 'ù': 'u',
                'ǖ': 'ü', 'ǘ': 'ü', 'ǚ': 'ü', 'ǜ': 'ü'
            }};
            function split(p) {{
                let b = "";
                for (let c of p) b += toneMap[c] || c;
                let s = "";
                for (let sm of smList) {{ if (b.startsWith(sm)) {{ s = sm; break; }} }}
                return {{ s, y: b.substring(s.length) }};
            }}

            for (let p in pinyinData) {{
                const {{ s, y }} = split(p);
                const si = shengmu.indexOf(s);
                const yi = yunmu.indexOf(y);
                if (si >= 0 && yi >= 0) {{
                    if (!validPinyinMap[si]) validPinyinMap[si] = [];
                    if (!validPinyinMap[si].includes(yi)) validPinyinMap[si].push(yi);
                    validPinyinSet.add(s + y);
                }}
            }}
        }})();

        function pickValidPinyin() {{
            const shengmuKeys = Object.keys(validPinyinMap).map(Number);
            const si = shengmuKeys[Math.floor(Math.random() * shengmuKeys.length)];
            const yunmuOptions = validPinyinMap[si];
            const yi = yunmuOptions[Math.floor(Math.random() * yunmuOptions.length)];
            return {{ shengmuIdx: si, yunmuIdx: yi }};
        }}
"""
    html = html[:start_idx] + new_data_section + "        " + html[end_idx:]

# 替换 showTonesPanel
old_show_tones_pattern = r'function showTonesPanel\(\) \{.*?\}'
new_show_tones = """function showTonesPanel() {
            const s = shengmu[state.finalShengmuIdx] || '';
            const y = yunmu[state.finalYunmuIdx] || '';
            let base = s + y;

            const panel = document.getElementById('tonesPanel');
            const list = document.getElementById('tonesList');
            const title = document.getElementById('panelTitle');

            title.textContent = `拼音 ${base} 的常用字`;
            list.innerHTML = '';

            for (let i = 1; i <= 4; i++) {
                const tonedKey = markPinyin(base, i);
                const chars = pinyinData[tonedKey] || [];
                const char = chars.length > 0 ? chars[Math.floor(Math.random() * chars.length)] : '--';

                const item = document.createElement('div');
                item.className = 'tone-item';
                item.innerHTML = `
                    <span class="toned-pinyin">${tonedKey}</span>
                    <span class="sample-char">${char}</span>
                `;

                item.onclick = () => {
                    speak(char !== '--' ? char : tonedKey);
                };
                list.appendChild(item);
            }

            panel.classList.add('show');
        }"""

html = re.sub(old_show_tones_pattern, new_show_tones, html, flags=re.DOTALL)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("index.html 更新完成。")
