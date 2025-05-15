import PyPDF2
import re
import os
import json
import nltk
from nltk.stem import WordNetLemmatizer

# ——————————————————————————————————————————————————————————————————————————————
# 0. 停用词列表，可按需扩充
STOPWORDS = {
    "a","an","the","and","or","of","in","on","to","for","with","by","is","are","as","at",
    "this","that","it","its","be","from","which","we","can","will","also"
}

# 初始化 Lemmatizer
lemmatizer = WordNetLemmatizer()

# ——————————————————————————————————————————————————————————————————————————————
# 1. 打开 PDF —— 请改成你本地的路径
pdf_path = r"D:\ebook\Y5B7M4_Introduction_to_Linear_Algebra-_Fourth_Edition.pdf"
reader = PyPDF2.PdfReader(pdf_path)

# ——————————————————————————————————————————————————————————————————————————————
# 2. 扫描每页前几行，记录真正的“Chapter X”起始页
chapter_starts = []
for i, page in enumerate(reader.pages):
    text = page.extract_text() or ""
    lines = text.splitlines()
    # 只检查前 5 行，看有没有独立成行的“Chapter N”
    for line in lines[:5]:
        m = re.match(r'^\s*Chapter\s+(\d+)\b', line, re.IGNORECASE)
        if m:
            chap = int(m.group(1))
            chapter_starts.append((chap, i))
            break

if not chapter_starts:
    raise RuntimeError("❌ 没有检测到任何章节起始，请检查 PDF 中章节标题格式。")

# 去重并排序
unique_starts = {}
for chap, pg in chapter_starts:
    if chap not in unique_starts or pg < unique_starts[chap]:
        unique_starts[chap] = pg
chapter_starts = sorted(unique_starts.items(), key=lambda x: x[0])

# ——————————————————————————————————————————————————————————————————————————————
# 3. 为每章提取并清洗单词列表
output_dir = "chapter_cleaned_keywords"
os.makedirs(output_dir, exist_ok=True)
all_chapters = {}

for idx, (chap_num, start_page) in enumerate(chapter_starts):
    end_page = chapter_starts[idx+1][1] if idx+1 < len(chapter_starts) else len(reader.pages)
    tokens = []
    for p in range(start_page, end_page):
        page_text = reader.pages[p].extract_text() or ""
        lines = page_text.splitlines()
        # 跳过前后各 2 行（页眉／页脚）
        body_lines = lines[2:-2] if len(lines) > 4 else lines
        tokens += re.findall(r"\b\w+\b", " ".join(body_lines).lower())

    # 初步去重
    unique_tokens = set(tokens)

    cleaned = []
    for w in unique_tokens:
        # 1) 保留至少含一字母，且长度>=3
        if len(w) < 3 or not re.search(r"[a-z]", w):
            continue
        # 2) 去除含数字或下划线
        if re.search(r"[\d_]", w):
            continue
        # 3) 去除停用词
        if w in STOPWORDS:
            continue
        # 4) 词形还原
        lemma = lemmatizer.lemmatize(w)
        # 5) 再次排重
        cleaned.append(lemma)

    final_words = sorted(set(cleaned))

    # 写入单章文件
    fname = os.path.join(output_dir, f"Chapter_{chap_num:02d}_keywords.txt")
    with open(fname, "w", encoding="utf-8") as f:
        for term in final_words:
            f.write(term + "\n")

    all_chapters[f"Chapter_{chap_num}"] = final_words
    print(f"✔ Chapter {chap_num}: {len(final_words)} terms → {fname}")

# ——————————————————————————————————————————————————————————————————————————————
# 4. 导出总 JSON
with open("all_chapters_cleaned_keywords.json", "w", encoding="utf-8") as jf:
    json.dump(all_chapters, jf, ensure_ascii=False, indent=2)

print("\n✅ 完成！请检查目录“chapter_cleaned_keywords/”下的 .txt 文件，以及根目录的 all_chapters_cleaned_keywords.json。")
