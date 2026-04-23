import json
import os

def filter_idioms(input_json, char_file, output_json):
    """
    读取 input_json 中的成语，如果成语中包含不在 char_file 中的汉字，则过滤掉。
    结果保存到 output_json。
    """
    # 加载允许的汉字
    if not os.path.exists(char_file):
        print(f"Error: {char_file} not found.")
        return

    print(f"正在从 {char_file} 加载常用字...")
    allowed_chars = set()
    with open(char_file, 'r', encoding='utf-8') as f:
        for line in f:
            # 过滤掉空白字符，保留所有非空白字符
            chars = line.strip()
            for char in chars:
                allowed_chars.add(char)
    
    print(f"已加载 {len(allowed_chars)} 个唯一字符。")

    # 加载成语 JSON
    if not os.path.exists(input_json):
        print(f"Error: {input_json} not found.")
        return

    print(f"正在读取 {input_json}...")
    with open(input_json, 'r', encoding='utf-8') as f:
        try:
            idioms_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return

    print(f"开始过滤成语 (总数: {len(idioms_data)})...")
    filtered_idioms = []
    
    for entry in idioms_data:
        idiom_str = entry.get('idiom', '')
        if not idiom_str:
            continue
            
        # 检查是否成语中的所有字符都在允许的集合中
        is_valid = True
        for char in idiom_str:
            if char not in allowed_chars:
                is_valid = False
                break
        
        if is_valid:
            filtered_idioms.append(entry)

    # 写入结果
    print(f"过滤完成。保留成语数量: {len(filtered_idioms)}")
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(filtered_idioms, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存到 {output_json}")

if __name__ == "__main__":
    # 根据用户描述，虽然提到 350.txt，但目录下实际为 3500.txt
    INPUT_FILE = 'idioms.json'
    CHAR_FILE = '3500.txt'
    OUTPUT_FILE = 'idioms2.json'
    
    filter_idioms(INPUT_FILE, CHAR_FILE, OUTPUT_FILE)
