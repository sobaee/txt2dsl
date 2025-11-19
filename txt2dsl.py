import io
import os
import re
from html.parser import HTMLParser

# ========== Interactive prompt ==========
input_file = input("Enter input TXT file path: ").strip()
while not os.path.isfile(input_file):
    print("File not found, try again.")
    input_file = input("Enter input TXT file path: ").strip()

output_file = os.path.splitext(input_file)[0] + ".dsl"
print(f"Output DSL will be: {output_file}")

# ========== Read header ==========
dict_name = None
source_lang = "GermanNewSpelling"
target_lang = "GermanNewSpelling"
content_lines = []

with io.open(input_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

for line in lines:
    stripped = line.strip()
    if stripped.startswith("##name"):
        dict_name = stripped.split("\t", 1)[1].strip()
    elif stripped.startswith("##sourceLang"):
        source_lang = stripped.split("\t", 1)[1].strip()
    elif stripped.startswith("##targetLang"):
        target_lang = stripped.split("\t", 1)[1].strip()
    elif stripped.startswith("##"):
        continue
    else:
        # ========= إزالة \n المكتوبة حرفياً =========
        clean_line = line.replace("\\n", "")
        content_lines.append(clean_line.rstrip("\n"))
        # ============================================

if not dict_name:
    dict_name = os.path.splitext(os.path.basename(input_file))[0]

# ========== Fix only phonetic brackets ==========
def fix_phonetic_brackets(text):
    phonetic_pattern = r"\[['ˈˌ].*?\]"
    def replace_brackets(match):
        phonetic_text = match.group(0)
        phonetic_text = phonetic_text.replace('[', '(').replace(']', ')')
        return phonetic_text
    text = re.sub(phonetic_pattern, replace_brackets, text)
    return text

# ========== Parser ==========
class LingvoHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.output = ""
        self.stack = []
    
    def emit(self, text):
        self.output += text
    
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        self.stack.append((tag, attrs_dict))

        if tag in ["object", "img"]:
            file_attr = attrs_dict.get("data") or attrs_dict.get("src")
            if file_attr:
                self.emit(f"[s]{file_attr}[/s]")

        elif tag == "br":
            self.emit("\n\t")

        elif tag == "font":
            color = attrs_dict.get("color")
            if color:
                clean = color.lstrip("#")
                self.emit(f"[c {clean}]")

        elif tag == "strong":
            self.emit("[/m]\n\t[m1]")

        elif tag == "b":
            self.emit("[b]")
        
        elif tag == "i":
            self.emit("[i]")

        elif tag == "u":
            self.emit("[u]")

        elif tag == "s":
            self.emit("[s]")
    
    def handle_endtag(self, tag):
        if tag == "font":
            for i in range(len(self.stack)-1, -1, -1):
                stack_tag, attrs_dict = self.stack[i]
                if stack_tag == "font":
                    color = attrs_dict.get("color")
                    if color:
                        self.emit("[/c]")
                    break
        
        elif tag == "b":
            self.emit("[/b]")

        elif tag == "i":
            self.emit("[/i]")

        elif tag == "u":
            self.emit("[/u]")

        elif tag == "s":
            self.emit("[/s]")

        elif tag == "strong":
            self.emit("")
    
    def handle_data(self, data):
        self.emit(data)
    
    def close(self):
        super().close()
        return self.output

# ========== Write DSL ==========

with io.open(output_file, "w", encoding="utf-16") as outf:
    outf.write(f'#NAME "{dict_name}"\n')
    outf.write(f'#INDEX_LANGUAGE "{source_lang}"\n')
    outf.write(f'#CONTENTS_LANGUAGE "{target_lang}"\n\n')

    for line in content_lines:
        if not line.strip():
            continue

        parts = line.split("\t", 1)
        head = parts[0].strip()

        # ========== إذا كان head يحتوي | ==========
        if "|" in head:
            head = "\n".join(h.strip() for h in head.split("|") if h.strip())
        # ===========================================

        html = parts[1] if len(parts) > 1 else ""

        outf.write(head + "\n")
        outf.write("\t[m1]")

        parser = LingvoHTMLParser()
        parser.feed(html)
        parser.close()

        text = parser.output
        
        text = fix_phonetic_brackets(text)

        # استبدال سطرين متتاليين ناتجين عن <br><br>
        text = re.sub(r"(?:\n\t\s*){2,}", "[m1]\\ [/m]", text)

        outf.write(text)
        outf.write("[/m]\n")

print("Completed successfully.")