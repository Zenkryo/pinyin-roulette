import json
import re

def remove_tone(pinyin):
    # 声调映射表
    tone_map = {
        'ā': 'a', 'á': 'a', 'ǎ': 'a', 'à': 'a',
        'ō': 'o', 'ó': 'o', 'ǒ': 'o', 'ò': 'o',
        'ē': 'e', 'é': 'e', 'ě': 'e', 'è': 'e',
        'ī': 'i', 'í': 'i', 'ǐ': 'i', 'ì': 'i',
        'ū': 'u', 'ú': 'u', 'ǔ': 'u', 'ù': 'u',
        'ǖ': 'ü', 'ǘ': 'ü', 'ǚ': 'ü', 'ǜ': 'ü'
    }
    res = ""
    for char in pinyin:
        res += tone_map.get(char, char)
    return res

def check_coverage():
    # 1. 加载有效的拼音组合（基础音节，如 'ba', 'pa'）
    # 使用 pinyin_map.json 作为标准数据源
    try:
        with open('pinyin_map.json', 'r', encoding='utf-8') as f:
            pinyin_data = json.load(f)
            # pinyinData 的键是带调的（如 'ā'），或者是基础拼音？
            # 根据之前的 conversation，pinyin_map.json 结构通常是 { "pinyin": [chars] }
            # 但在 index.html 中，pinyinData 的键是基础拼音（如 "zǔ"）？不对，带声调。
            # 我们需要得到所有的基础拼音集合。
            valid_bases = set()
            for key in pinyin_data.keys():
                valid_bases.add(remove_tone(key))
    except Exception as e:
        print(f"加载 pinyin_map.json 失败: {e}")
        return

    # 2. 加载过滤后的成语集
    try:
        with open('idioms2.json', 'r', encoding='utf-8') as f:
            idioms_data = json.load(f)
    except Exception as e:
        print(f"加载 idioms2.json 失败: {e}")
        return

    # 3. 提取成语中出现过的所有音节
    appeared_pinyins = set()
    for entry in idioms_data:
        pinyin_str = entry.get('pinyin', '')
        # 成语拼音通常以空格分隔，如 "chōng róng dà yá"
        syllables = pinyin_str.split()
        for s in syllables:
            base = remove_tone(s.lower())
            appeared_pinyins.add(base)

    # 4. 对比
    missing = valid_bases - appeared_pinyins
    
    print(f"有效拼音库总数 (基础音节): {len(valid_bases)}")
    print(f"成语库覆盖的音节总数: {len(appeared_pinyins)}")
    print(f"未在成语中出现的音节数量: {len(missing)}")
    
    if missing:
        print("\n以下音节在 idiom2.json 的成语中不存在：")
        print(", ".join(sorted(list(missing))))
    else:
        print("\n完美！所有有效拼音都在成语库中找到了对应。")

if __name__ == "__main__":
    check_coverage()
