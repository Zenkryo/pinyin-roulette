import json
import re
import os

def process():
    # 路径
    dict_path = 'dict1.txt'
    common_path = '3500.txt'
    output_path = 'pinyin_map.json'

    # 1. 加载 3500 常用字
    common_chars = set()
    if not os.path.exists(common_path):
        print(f"错误: 找不到 {common_path}")
        return

    with open(common_path, 'r', encoding='utf-8') as f:
        for line in f:
            # 提取行中所有非空白字符，确保加载所有汉字
            chars = line.strip()
            if chars:
                # 如果一行有多个字，也能正确处理
                for char in chars:
                    if not char.isspace():
                        common_chars.add(char)

    print(f"成功加载 {len(common_chars)} 个常用汉字。")

    # 2. 解析 dict1.txt
    pinyin_to_chars = {}
    
    # 匹配键值的正则表达式
    # 格式可能如: 'bǎng páng pāng': ['膀'], 或 'líng': [
    key_re = re.compile(r"^\s*['\"]?(.*?)['\"]?\s*:\s*\[(.*)$")
    # 匹配单引号或双引号内的单个字 (即汉字)
    char_re = re.compile(r"['\"](.)['\"]")

    current_pinyins = []
    
    if not os.path.exists(dict_path):
        print(f"错误: 找不到 {dict_path}")
        return

    with open(dict_path, 'r', encoding='utf-8') as f:
        for line in f:
            line_content = line.strip()
            if not line_content or line_content in ['{', '}', '};']:
                continue
            
            match = key_re.match(line_content)
            if match:
                # 发现新的拼音键
                pinyins_str = match.group(1)
                remaining = match.group(2)
                
                # 按照空格或逗号分割拼音 (多音字通常空格分隔)
                current_pinyins = re.split(r'[,\s]+', pinyins_str)
                current_pinyins = [p.strip() for p in current_pinyins if p.strip()]
                
                # 检查同一行是否直接包含了汉字列表
                chars_found = char_re.findall(remaining)
                for char in chars_found:
                    if char in common_chars:
                        for p in current_pinyins:
                            if p not in pinyin_to_chars:
                                pinyin_to_chars[p] = set()
                            pinyin_to_chars[p].add(char)
                
                # 如果这一行包含了闭括号 ]，说明列表结束
                if ']' in remaining:
                    current_pinyins = []
            else:
                # 正在处理列表中的汉字行
                if current_pinyins:
                    chars_found = char_re.findall(line_content)
                    for char in chars_found:
                        if char in common_chars:
                            for p in current_pinyins:
                                if p not in pinyin_to_chars:
                                    pinyin_to_chars[p] = set()
                                pinyin_to_chars[p].add(char)
                    
                    if ']' in line_content:
                        current_pinyins = []

    # 3. 转换为最终 JSON 格式 (将 set 转为 sorted list)
    final_data = {p: sorted(list(chars)) for p, chars in pinyin_to_chars.items()}
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print(f"分析完成。输出文件: {output_path}")
    print(f"总计找到 {len(final_data)} 个不同的拼音。")

if __name__ == "__main__":
    process()
