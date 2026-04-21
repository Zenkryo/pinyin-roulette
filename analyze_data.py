import json
import re

# 拼音解析逻辑
shengmu_list = ['b', 'p', 'm', 'f', 'd', 't', 'n', 'l', 'g', 'k', 'h', 'j', 'q', 'x', 'zh', 'ch', 'sh', 'r', 'z', 'c', 's', 'y', 'w']
# 按照长度从长到短排序，防止 zh 匹配成 z
shengmu_list.sort(key=len, reverse=True)

tone_chars = {
    'ā': ('a', 1), 'á': ('a', 2), 'ǎ': ('a', 3), 'à': ('a', 4),
    'ō': ('o', 1), 'ó': ('o', 2), 'ǒ': ('o', 3), 'ò': ('o', 4),
    'ē': ('e', 1), 'é': ('e', 2), 'ě': ('e', 3), 'è': ('e', 4),
    'ī': ('i', 1), 'í': ('i', 2), 'ǐ': ('i', 3), 'ì': ('i', 4),
    'ū': ('u', 1), 'ú': ('u', 2), 'ǔ': ('u', 3), 'ù': ('u', 4),
    'ǖ': ('ü', 1), 'ǘ': ('ü', 2), 'ǚ': ('ü', 3), 'ǜ': ('ü', 4),
    'a': ('a', 0), 'o': ('o', 0), 'e': ('e', 0), 'i': ('i', 0), 'u': ('u', 0), 'ü': ('ü', 0), 'v': ('ü', 0)
}

def remove_tone(p):
    tone = 0
    clean_p = ""
    for char in p:
        if char in tone_chars:
            base, t = tone_chars[char]
            clean_p += base
            if t > 0: tone = t
        else:
            clean_p += char
    return clean_p, tone

def split_pinyin(p_with_tone):
    base_p, tone = remove_tone(p_with_tone)
    
    # 提取声母
    shengmu = ""
    for s in shengmu_list:
        if base_p.startswith(s):
            shengmu = s
            break
    
    yunmu = base_p[len(shengmu):]
    
    # 特殊规则：j q x 后面的 u 实际上是 ü
    if shengmu in ['j', 'q', 'x'] and yunmu.startswith('u'):
        # 但我们通常在显示时保留 u，在逻辑处理时视作 ü
        # 用户可能希望 yunmu 列表里包含 'u' 和 'ü'
        pass

    return shengmu, yunmu, base_p, tone

def main():
    with open('pinyin_map.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    all_yunmu = set()
    valid_combinations = {} # shengmu -> set of yunmu
    
    # 格式: { "ba": { 1: ["八"], 2: ["拔"] }, ... }
    # 或者简单点: { "bà": ["爸", "罢"], ... }
    # 用户的 request 指出：key 是拼音，value 为汉字列表。
    # 我直接把 pinyin_map.json 的内容定义进去即可。
    
    for p in data.keys():
        s, y, base, t = split_pinyin(p)
        all_yunmu.add(y)
        if s not in valid_combinations:
            valid_combinations[s] = set()
        valid_combinations[s].add(y)

    print("ALL_YUNMU:", sorted(list(all_yunmu)))
    
    # 构建 validPinyinMap
    # shengmu_list_with_empty = ['', 'b', 'p', ...]
    
if __name__ == "__main__":
    main()
