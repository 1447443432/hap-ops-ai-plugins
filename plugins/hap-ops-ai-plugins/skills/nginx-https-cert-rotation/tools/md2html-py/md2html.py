#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
md2html.py — 跨平台 Markdown -> HTML 转换器（HAP 升级指南专用）

与 Go 版 tools/md2html/md2html(.exe) 共用同一份 template.html 与 CSS/JS 规范，
在 Windows / Linux / macOS / codex 云端 等任何带 python3 的环境里产出一致的 HTML。

设计目标：
  1. 零第三方依赖，仅用 Python 标准库（不联网、不 pip install）。
  2. 与 Go 版产物"同源"：同一份 template.html 保证 CSS/JS/侧边栏/TOC 交互完全一致；
     后处理逻辑（heading id、静态 TOC、日期高亮、代码块复制按钮）逐条等价复刻 Go 版。
  3. 用法兼容 Go 版：md2html.py -input xxx.md -output xxx.html [-title 标题]

作者：HAP 升级指南 Skill 维护
"""

import sys
import os
import re
import argparse
import unicodedata

# ----------------------------------------------------------------------------
# 语言白名单（与 Go 版 languageHintRE 完全一致，全部小写）
# 仅当围栏代码块声明的语言在该集合内时，才显示语言标签并写入 data-lang
# ----------------------------------------------------------------------------
_LANG_HINTS = {
    "bash", "sh", "shell", "yaml", "yml", "javascript", "js", "typescript", "ts",
    "json", "sql", "python", "py", "java", "go", "rust", "dockerfile", "docker",
    "text", "plaintext", "toml", "ini", "conf", "xml", "html", "css", "scss",
    "markdown", "md", "powershell", "ps1", "cmd", "bat", "makefile", "nginx",
    "properties", "groovy", "kotlin", "scala", "swift", "c", "cpp", "csharp", "cs",
    "ruby", "rb", "php", "perl", "lua", "r", "dart", "elixir", "erlang",
    "haskell", "clojure", "lisp", "fortran", "matlab", "zig", "v", "svelte",
}

_NUMBER_PREFIX_RE = re.compile(r'^\d+[\.\s]+')
_DATE_RE = re.compile(r'\d{4}-\d{2}-\d{2}')
# 正文内联日期：排除已经被 inline-date 包裹的日期（避免对
# <p> 和 <blockquote> 双重处理时出现嵌套 span，与 Go 版逐层等价）
_INLINE_DATE_RE = re.compile(r'(?<!inline-date">)\d{4}-\d{2}-\d{2}')
_TARGET_DATE_LABEL_RE = re.compile(r'目标版本发布日期')
_CODE_BLOCK_RE = re.compile(r'(?s)(<pre><code(?:\s+class="language-([^"]*)")?>)(.+?)(</code></pre>)')


def escape_html(s):
    """等价复刻 Go 版（goldmark + goquery 序列化）对文本内容的转义：
    & < > " ' 全部转义（goquery 用 x/net/html 序列化文本节点时会转义这五个字符）。"""
    return (s.replace('&', '&amp;')
             .replace('<', '&lt;')
             .replace('>', '&gt;')
             .replace('"', '&#34;')
             .replace("'", '&#39;'))


def _is_cjk(ch):
    """等价复刻 unicode.Is(unicode.Han, r)：判断是否为 CJK 统一表意文字。"""
    return '一' <= ch <= '鿿'


def generate_heading_id(text):
    """等价复刻 Go 版 generateHeadingID。

    规则：去除开头的数字前缀（如 '1. '）；空格/全角空格 -> '-'（首空格不加点）；
    仅保留汉字/字母/数字；去除首尾 '-'；空结果回退为 'heading'。
    """
    # goldmark 对标题文本取的是"原始文本"（实体尚未转义），故先还原实体，
    # 使 &amp; 回到 & 并被后续规则跳过（生成 -- 而非 amp），与 Go 版一致。
    text = (text.replace('&amp;', '&').replace('&lt;', '<')
                .replace('&gt;', '>').replace('&#34;', '"').replace('&#39;', "'"))
    stripped = _NUMBER_PREFIX_RE.sub('', text)
    out = []
    first = True
    for ch in stripped:
        if ch == ' ' or ch == '\u3000':
            if not first:
                out.append('-')
        elif _is_cjk(ch) or ch.isalpha() or ch.isdigit():
            out.append(ch)
            first = False
    id_ = ''.join(out).strip('-')
    return id_ if id_ else 'heading'


# ----------------------------------------------------------------------------
# 行内解析：code / link / strong / em / del（与 goldmark GFM 行内渲染对齐）
# 注意：goquery 重新序列化文本节点时会把 & < > " ' 全部实体化，因此普通文本
# 必须先转义，再套用 ** / * / _ / ~~ / 链接 等行内标记（标记本身不是这五个字符）。
# ----------------------------------------------------------------------------
def _escape_text(s):
    return escape_html(s)


# ----------------------------------------------------------------------------
# CommonMark 行内强调（emphasis）的 flanking 规则（goldmark 严格遵循）
# 一个 * / ** 定界符只有同时满足左/右 flanking 才分别作为开/闭强调符。
# 这能正确解释 "**来自 v7.1.0 的要求：**" 在 goldmark 中不被加粗
# （闭符 ** 前后均为全角冒号这一 Unicode 标点，不构成 right-flanking）。
# ----------------------------------------------------------------------------
_PUNCT_EXTRA = set('$+<=>^`|~')


def _is_punct(ch):
    if not ch:
        return False
    if ch in _PUNCT_EXTRA:
        return True
    return unicodedata.category(ch).startswith('P')


def _is_ws(ch):
    return ch == '' or ch == ' ' or ch == '\t' or ch == '\n' or ch == '\r' \
        or ch == '\u3000' or ch == '\f' or ch == '\v'


def _left_flanking(text, pos, dlen):
    before = text[pos - 1] if pos > 0 else ''
    after = text[pos + dlen] if pos + dlen < len(text) else ''
    if _is_ws(after):
        return False
    if (not _is_punct(after)) or _is_ws(before) or _is_punct(before):
        return True
    return False


def _right_flanking(text, pos, dlen):
    before = text[pos - 1] if pos > 0 else ''
    after = text[pos + dlen] if pos + dlen < len(text) else ''
    if _is_ws(before):
        return False
    if (not _is_punct(before)) or (_is_punct(before) and (_is_ws(after) or _is_punct(after))):
        return True
    return False


def _can_open(delim, text, pos):
    """开符判定：星号定界符用基础 flanking；下划线定界符需额外 intraword 约束
    （CommonMark：_ 仅当"左 flanking 且非右 flanking"，或"前后均为标点且后随空白/标点"
    时才可作为开符，从而不强调词内下划线如 a_b_c）。"""
    dlen = len(delim)
    if delim[0] != '_':
        return _left_flanking(text, pos, dlen)
    before = text[pos - 1] if pos > 0 else ''
    after = text[pos + dlen] if pos + dlen < len(text) else ''
    lf = _left_flanking(text, pos, dlen)
    rf = _right_flanking(text, pos, dlen)
    if (not rf) or (rf and _is_punct(before) and (_is_ws(after) or _is_punct(after))):
        return lf
    return False


def _can_close(delim, text, pos):
    """闭符判定：同上，下划线定界符需额外 intraword 约束。"""
    dlen = len(delim)
    if delim[0] != '_':
        return _right_flanking(text, pos, dlen)
    before = text[pos - 1] if pos > 0 else ''
    after = text[pos + dlen] if pos + dlen < len(text) else ''
    lf = _left_flanking(text, pos, dlen)
    rf = _right_flanking(text, pos, dlen)
    if (not lf) or (lf and _is_punct(after) and (_is_ws(before) or _is_punct(before))):
        return rf
    return False


def _emph_pass(text, delim, tag):
    """对单个定界符（delim 可为 '*' 或 '**'，长度 1 或 2）按 flanking 规则配对。
    未成功配对的定界符保留原样（与 goldmark 一致）。"""
    dlen = len(delim)
    n = len(text)
    # 收集"恰好 dlen 个连续定界符"的候选位置（避开更长定界符串）
    cands = []
    i = 0
    while i < n:
        if text.startswith(delim, i):
            j = i
            while j < n and text[j] == delim[0]:
                j += 1
            if j - i == dlen:
                cands.append(i)
            i = j
        else:
            i += 1
    result = []
    text_ptr = 0
    stack = []  # 尚未闭合的开符位置
    for pos in cands:
        can_open = _can_open(delim, text, pos)
        can_close = _can_close(delim, text, pos)
        if stack and can_close:
            open_pos = stack.pop()
            result.append(text[text_ptr:open_pos])
            result.append('<' + tag + '>')
            result.append(text[open_pos + dlen:pos])
            result.append('</' + tag + '>')
            text_ptr = pos + dlen
        elif can_open and not stack:
            stack.append(pos)
        # 其余情况：定界符保留原样，留待末尾随剩余文本输出
    result.append(text[text_ptr:])
    return ''.join(result)


def _apply_markup(text):
    """在已经转义过的文本上套用行内标记（链接/加粗/斜体/删除线/还原代码占位符）。
    输入文本应当已经过 _escape_text 转义，避免二次转义。
    强调只在"非标签文本段"上应用，避免误伤 <a href>、已生成的 <strong> 等内容。"""
    def _link(m):
        # URL 已在转义后的文本里（如 & -> &amp;），直接放入 href，不再二次转义；
        # 链接文本递归套用标记（含强调）
        url = m.group(2).strip()
        return '<a href="' + url + '">' + _apply_markup(m.group(1)) + '</a>'

    text = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', _link, text)
    # 按 HTML 标签切分，仅在标签之间的纯文本段上做强调，保护标签内部（如 href）
    parts = re.split(r'(<[^>]+>)', text)
    out = []
    for seg in parts:
        if seg.startswith('<') and seg.endswith('>'):
            out.append(seg)
            continue
        seg = _emph_pass(seg, '**', 'strong')
        seg = _emph_pass(seg, '*', 'em')
        seg = _emph_pass(seg, '__', 'strong')
        seg = _emph_pass(seg, '_', 'em')
        seg = re.sub(r'~~(.+?)~~', r'<del>\1</del>', seg)
        out.append(seg)
    return ''.join(out)


def inline(text):
    # 1) 先用占位符保护行内代码，避免内部内容被二次解析
    codes = []

    def _stash(m):
        codes.append(m.group(1))  # 仅存反引号内的内容（不含反引号本身）
        return "\x00CODE" + str(len(codes) - 1) + "\x00"

    text = re.sub(r'`([^`]+)`', _stash, text)

    # 2) 转义普通文本（标记字符 * _ ~ [ ] ( ) 不在转义集合内，正则仍可命中）
    text = _escape_text(text)

    # 3) 套用行内标记（输入已转义，内部递归不再转义）
    text = _apply_markup(text)

    # 4) 还原行内代码（内容需单独转义）
    def _restore(m):
        return '<code>' + escape_html(codes[int(m.group(1))]) + '</code>'

    text = re.sub(r'\x00CODE(\d+)\x00', _restore, text)
    return text


# ----------------------------------------------------------------------------
# 块级解析：针对 HAP 升级文档用到的 Markdown 语法子集
# 目标：生成与 goldmark 风格一致的标签结构（h1-h6 / p / ul / ol / li /
#       table(thead>tr>th, tbody>tr>td) / pre>code.language-x / blockquote / hr）
# 空白差异不影响渲染，因此不必逐字节对齐。
# ----------------------------------------------------------------------------
def _is_block_start(line):
    s = line.strip()
    if s == '':
        return True
    if s.startswith('```') or s.startswith('~~~'):
        return True
    if re.match(r'^#{1,6}\s+', line):
        return True
    if re.match(r'^\s*>\s?', line):
        return True
    if re.match(r'^\s*([-*+]|\d+\.)\s+', line):
        return True
    if re.match(r'^\s*([-*_])(\s*\1){2,}\s*$', line):
        return True
    if '|' in s:
        return True
    return False


def _parse_list(lines, start, base_indent=None):
    """缩进敏感的列表解析，返回 (items, next_index, loose)。

    items: [{'content', 'ordered', 'start', 'task', 'blocks', 'children'}, ...]
      - start: 有序列表首个标记的数字（goldmark 对非 1 起始会输出 <ol start="N">）
      - task: TaskList 复选框 HTML（'' 表示非复选框项）
      - blocks: 列表项续行里的块级子内容（如缩进的代码块），已渲染为 HTML
      - children: 嵌套列表
    loose: 是否为松散列表（任意项被空行分隔或含块级子内容，则整体松散，
           所有项文本包 <p>）
    """
    items = []
    i = start
    n = len(lines)
    if base_indent is None:
        m0 = re.match(r'^(\s*)([-*+]|\d+\.)\s+', lines[i])
        base_indent = len(m0.group(1)) if m0 else 0
    loose = False
    list_ordered = None  # 当前列表种类（有序/无序），由首个项决定；
                         # 用于区分"同级列表项"是否属于同一列表（ul 与 ol 即使同级也属两个独立列表）
    prev_was_item = False
    while i < n:
        line = lines[i]
        if line.strip() == '':
            # 空行处理：根据下一行决定是合并为同一松散列表，还是结束当前列表
            if i + 1 < n:
                nxt = lines[i + 1]
                nxt_m = re.match(r'^(\s*)([-*+]|\d+\.)\s+', nxt)
                if nxt_m:
                    nind = len(nxt_m.group(1))
                    nxt_ordered = bool(re.match(r'^\s*\d+\.', nxt))
                    if nind > base_indent:
                        # 更深缩进的列表项 => 当前项的子列表（类型可不同），合并
                        if prev_was_item:
                            loose = True
                        i += 1
                        continue
                    if nind == base_indent:
                        # 同级列表项：仅当类型一致（同为 ul 或同为 ol）才合并为同一松散列表；
                        # 类型不一致（如 ul 之后接 ol）视为两个独立列表，结束当前列表
                        same_type = (list_ordered is None) or (nxt_ordered == list_ordered)
                        if same_type:
                            if prev_was_item:
                                loose = True
                            i += 1
                            continue
                        else:
                            break
                elif (len(nxt) - len(nxt.lstrip())) > base_indent:
                    # 空行后跟缩进的非列表内容（如代码块）=> 当前项的续行（项级松散），合并
                    i += 1
                    continue
            break
        m = re.match(r'^(\s*)([-*+]|\d+\.)\s+(.*)$', line)
        if not m:
            break
        indent = len(m.group(1))
        if indent < base_indent:
            break
        if indent > base_indent:
            sub, i, sub_loose = _parse_list(lines, i, indent)
            if items:
                items[-1]['children'] = sub
                items[-1]['child_loose'] = sub_loose
            prev_was_item = True
            continue
        # 同级列表项
        marker = m.group(2)
        if list_ordered is None:
            list_ordered = bool(re.match(r'\d+\.', marker))
        content = m.group(3).rstrip()
        # TaskList 复选框：- [ ] / - [x] / - [X]
        # 属性顺序必须与 goldmark tasklist 扩展完全一致：checked（若存在）置于
        # disabled / type 之前，即 `<input checked="" disabled="" type="checkbox"/>`。
        task_html = ''
        tm = re.match(r'^\[([ xX])\]\s+(.*)$', content)
        if tm:
            checked = tm.group(1).lower() == 'x'
            task_html = '<input' + (' checked=""' if checked else '') + ' disabled="" type="checkbox"/> '
            content = tm.group(2)
        ordered = bool(re.match(r'\d+\.', marker))
        start_val = 0
        if ordered:
            try:
                start_val = int(re.match(r'\d+', marker).group(0))
            except ValueError:
                start_val = 0
        i += 1
        # 收集续行块（缩进大于 base_indent 的围栏代码块/嵌套列表/段落）
        cont = []
        while i < n:
            l = lines[i]
            if l.strip() == '':
                if i + 1 < n and (len(lines[i + 1]) - len(lines[i + 1].lstrip())) > base_indent:
                    cont.append(l)
                    i += 1
                    continue
                break
            ind2 = len(l) - len(l.lstrip())
            if ind2 > base_indent:
                cont.append(l)
                i += 1
                continue
            break
        blocks = []
        if cont:
            # goldmark 仅在"项文本与续行块之间用空行分隔"时才将该项判为松散，
            # 进而使整列松散；无空行分隔的缩进块子项（如直接跟缩进代码）
            # 应保持紧凑（项文本不包 <p>）。
            item_loose = any(c.strip() == '' for c in cont)
            lead, rest = _split_cont(cont)
            if lead:
                # 首段惰性续行并入 item 段落（goldmark 软换行渲染为 \n），
                # 不单独成块，与 goldmark 列表项段落语义一致。
                lead_text = '\n'.join(l.strip() for l in lead)
                content = (content + '\n' + lead_text) if content else lead_text
            if rest:
                blocks.append(md_to_html('\n'.join(rest)))
            if item_loose:
                loose = True
        items.append({'content': content, 'ordered': ordered, 'start': start_val,
                      'task': task_html, 'blocks': blocks, 'children': None})
        prev_was_item = True
    return items, i, loose


def _split_cont(cont):
    """将列表项续行 cont 拆分为：
    - lead：首段惰性续行（应并入 item 段落，与 goldmark 一致不单独成块）
    - rest：其余块级子内容（经 md_to_html 渲染为独立块）
    空行或块级起始行会终结 lead 段落（与 CommonMark 列表项续行语义一致）。
    """
    lead = []
    rest = []
    in_lead = True
    for line in cont:
        if in_lead:
            if line.strip() == '':
                in_lead = False
                continue
            if _is_block_start(line):
                in_lead = False
                rest.append(line)
                continue
            lead.append(line)
        else:
            rest.append(line)
    return lead, rest


def _render_list(items, loose=False):
    if not items:
        return ''
    tag = 'ol' if items[0]['ordered'] else 'ul'
    start_attr = ''
    if items[0]['ordered'] and items[0].get('start', 0) > 1:
        start_attr = ' start="' + str(items[0]['start']) + '"'
    out = ['<' + tag + start_attr + '>']
    for it in items:
        inner = it.get('task', '') + inline(it['content'])
        if loose and it['content'].strip():
            li = '<li>\n<p>' + inner + '</p>'
        elif it['content'].strip():
            li = '<li>' + inner
        else:
            li = '<li>' + inner
        for b in it.get('blocks', []):
            li += '\n' + b
        if it.get('children'):
            li += '\n' + _render_list(it['children'], it.get('child_loose', False))
        if loose or it.get('blocks') or it.get('children'):
            li += '\n'
        li += '</li>'
        out.append(li)
    out.append('</' + tag + '>')
    return '\n'.join(out)


def _render_table(rows):
    def _split(r):
        r = r.strip()
        if r.startswith('|'):
            r = r[1:]
        if r.endswith('|'):
            r = r[:-1]
        return [c.strip() for c in r.split('|')]

    header = _split(rows[0])
    data = [_split(r) for r in rows[2:]]  # 跳过表头行与分隔行
    out = ['<table>', '<thead>', '<tr>']
    for c in header:
        out.append('<th>' + inline(c) + '</th>')
    out.append('</tr>')
    out.append('</thead>')
    out.append('<tbody>')
    for row in data:
        out.append('<tr>')
        for c in row:
            out.append('<td>' + inline(c) + '</td>')
        out.append('</tr>')
    out.append('</tbody>')
    out.append('</table>')
    return '\n'.join(out)


def md_to_html(md):
    lines = md.split('\n')
    n = len(lines)
    out = []
    i = 0
    while i < n:
        line = lines[i]
        stripped = line.strip()

        # 1) 围栏代码块 ``` 或 ~~~
        if stripped.startswith('```') or stripped.startswith('~~~'):
            fence = stripped[:3]
            lang = stripped[3:].strip()
            fence_indent = len(line) - len(line.lstrip())  # 围栏缩进（CommonMark：内容行去除同等缩进）
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith(fence):
                cl = lines[i]
                # 去除内容行中不超过围栏缩进的前导空格（与 goldmark 行为一致）
                ls = len(cl) - len(cl.lstrip())
                if ls >= fence_indent:
                    cl = cl[fence_indent:]
                buf.append(cl)
                i += 1
            i += 1  # 跳过闭合围栏
            code = '\n'.join(buf)
            if buf:
                code += '\n'  # goldmark 代码块内容末尾带一个换行
            if lang:
                out.append('<pre><code class="language-' + escape_html(lang) + '">' + escape_html(code) + '</code></pre>')
            else:
                out.append('<pre><code>' + escape_html(code) + '</code></pre>')
            continue

        # 2) 标题 # ~ ######
        m = re.match(r'^(#{1,6})\s+(.*?)\s*#*\s*$', line)
        if m:
            lvl = len(m.group(1))
            txt = m.group(2).strip()
            out.append('<h' + str(lvl) + '>' + inline(txt) + '</h' + str(lvl) + '>')
            i += 1
            continue

        # 3) 水平线
        if re.match(r'^\s*([-*_])(\s*\1){2,}\s*$', line):
            out.append('<hr/>')
            i += 1
            continue

        # 4) 引用块
        if re.match(r'^\s*>\s?', line):
            buf = []
            while i < n and re.match(r'^\s*>\s?', lines[i]):
                buf.append(re.sub(r'^\s*>\s?', '', lines[i]))
                i += 1
            out.append('<blockquote>\n' + md_to_html('\n'.join(buf)) + '\n</blockquote>')
            continue

        # 5) 表格（GFM pipe table）
        if '|' in stripped and i + 1 < n and '-' in lines[i + 1] and re.match(r'^\s*\|?[\s:|-]+\|', lines[i + 1]):
            rows = []
            while i < n and lines[i].strip() != '' and '|' in lines[i].strip():
                rows.append(lines[i].strip())
                i += 1
            if len(rows) >= 2:
                out.append(_render_table(rows))
                continue

        # 6) 列表
        if re.match(r'^\s*([-*+]|\d+\.)\s+', line):
            items, i, loose = _parse_list(lines, i)
            out.append(_render_list(items, loose))
            continue

        # 7) 空行
        if stripped == '':
            i += 1
            continue

        # 8) 段落：收集连续非块起始行
        buf = []
        while i < n and not _is_block_start(lines[i]):
            buf.append(lines[i].strip())
            i += 1
        para = '\n'.join(buf).strip()  # 保留软换行，与 goldmark 输出对齐
        if para:
            out.append('<p>' + inline(para) + '</p>')
    return '\n'.join(out)


# ----------------------------------------------------------------------------
# 后处理（逐条等价复刻 Go 版 postProcess + processCodeBlocks）
# ----------------------------------------------------------------------------
def process_code_blocks(body):
    def _repl(m):
        opening = m.group(1)
        lang = (m.group(2) or '').lower()
        code = m.group(3)
        valid = lang if lang in _LANG_HINTS else ''
        label = '<span class="code-lang-label">' + valid + '</span>' if valid else ''
        attrs = opening[len('<pre><code'):]  # ' class="language-x">' 或 '>'
        return ('<div class="code-block" data-lang="' + valid + '">' + label +
                '<button class="copy-btn">复制</button><pre><code' + attrs + code + '</code></pre></div>')

    return _CODE_BLOCK_RE.sub(_repl, body)


def _highlight_meta_dates(body):
    def _repl_table(tm):
        tbl = tm.group(0)

        def _repl_tr(trm):
            tr = trm.group(0)
            cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', tr, flags=re.S)
            if len(cells) < 2:
                return tr
            label = re.sub(r'<[^>]+>', '', cells[0]).strip()
            value_html = cells[1]
            if ('发布日期' in label) or ('日期' in label):
                is_target = bool(_TARGET_DATE_LABEL_RE.search(label))

                def _repl_date(dm):
                    d = dm.group(0)
                    if is_target:
                        return '<span class="date-val date-val-primary">' + d + '</span>'
                    return '<span class="date-val">' + d + '</span>'

                new_val = _DATE_RE.sub(_repl_date, value_html)
                if is_target and '⚠️' in new_val:
                    new_val = new_val.replace('⚠️', '<span style="color:#cf222e;">⚠️</span>')
                # 仅替换第二个单元格（保持首个单元格不变）
                return tr.replace(cells[1], new_val, 1)
            return tr

        return re.sub(r'<tr>(.*?)</tr>', _repl_tr, tbl, flags=re.S)

    return re.sub(r'<table class="meta-block">.*?</table>', _repl_table, body, flags=re.S)


def _highlight_inline_dates(body):
    def _repl_tag(m):
        tag_open = m.group(1)
        inner = m.group(2)
        tag_close = m.group(3)
        new_inner = _INLINE_DATE_RE.sub(lambda dm: '<span class="inline-date">' + dm.group(0) + '</span>', inner)
        return tag_open + new_inner + tag_close

    body = re.sub(r'(<p>)(.*?)(</p>)', _repl_tag, body, flags=re.S)
    body = re.sub(r'(<li>)(.*?)(</li>)', _repl_tag, body, flags=re.S)
    body = re.sub(r'(<blockquote[^>]*>)(.*?)(</blockquote>)', _repl_tag, body, flags=re.S)
    return body


def generate_toc(entries):
    """等价复刻 Go 版 generateTOC。
    entries: [(level, original_text, id), ...]（original_text 含数字前缀，与 Go 版一致）
    """
    if not entries:
        return '<ul class="toc" id="toc"></ul>'

    out = ['<ul class="toc" id="toc">']
    cur_section = None
    cur_children = None

    for lvl, text, hid in entries:
        if lvl == 2:
            if cur_section is not None:
                if cur_children is not None:
                    cur_section.append(''.join(cur_children))
                    cur_section.append('</ul></li>')
                else:
                    cur_section.append('</li>')
                out.append(''.join(cur_section))
            cur_section = ['<li class="toc-section">',
                           '<div class="toc-header">',
                           '<span class="toc-toggle">▾</span>',
                           '<a href="#' + hid + '">' + text + '</a>',
                           '</div>']
            cur_children = ['<ul class="toc-children">']
        else:
            if cur_children is None:
                cur_children = ['<ul class="toc-children">']
            cur_children.append('<li class="toc-item h' + str(lvl) +
                                '"><a href="#' + hid + '">' + text + '</a></li>')

    if cur_section is not None:
        if cur_children is not None:
            cur_section.append(''.join(cur_children))
            cur_section.append('</ul></li>')
        else:
            cur_section.append('</li>')
        out.append(''.join(cur_section))

    out.append('</ul>')
    return ''.join(out)


def post_process(body):
    # 0) 代码块包装（先于其它，保证后续不破坏代码块）
    body = process_code_blocks(body)

    toc_entries = []

    # 1) heading id + 收集 TOC（h2-h5；h1 为文档标题不加 id）
    def _repl_heading(m):
        lvl = int(m.group(1))
        inner = m.group(2)
        text = re.sub(r'<[^>]+>', '', inner).strip()  # 等价 goquery s.Text()
        hid = generate_heading_id(text)
        toc_entries.append((lvl, text, hid))
        return '<h' + str(lvl) + ' id="' + hid + '">' + inner + '</h' + str(lvl) + '>'

    body = re.sub(r'<h([2-5])[^>]*>(.*?)</h\1>', _repl_heading, body, flags=re.S)

    # 2) 第一个表格加 meta-block（版本信息表）
    body = re.sub(r'<table>', '<table class="meta-block">', body, count=1)

    # 3) 含 ⚠️ 的 blockquote 加 attention
    def _repl_quote(m):
        inner = m.group(1)
        if '⚠️' in inner:
            return '<blockquote class="attention">' + inner + '</blockquote>'
        return m.group(0)

    body = re.sub(r'<blockquote>(.*?)</blockquote>', _repl_quote, body, flags=re.S)

    # 4) meta-block 表格日期高亮
    body = _highlight_meta_dates(body)

    # 5) 正文内联日期（p/li/blockquote，不在 td 内）
    body = _highlight_inline_dates(body)

    # 6) 静态 TOC
    toc_html = generate_toc(toc_entries)

    return body, toc_html


def extract_title(body):
    m = re.search(r'<h1[^>]*>(.*?)</h1>', body, flags=re.S)
    if m:
        return re.sub(r'<[^>]+>', '', m.group(1)).strip()
    return 'HAP 升级指南'


def find_template():
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, '..', 'md2html', 'template.html'),
        os.path.join(here, 'template.html'),
        os.path.join(here, '..', 'template.html'),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    raise FileNotFoundError('template.html not found (looked in: ' + ', '.join(candidates) + ')')


def main():
    ap = argparse.ArgumentParser(
        description='Convert HAP Upgrade Guide Markdown to a single-file HTML document '
                    '(sidebar TOC, code copy buttons, responsive layout).')
    ap.add_argument('-input', required=True, help='Input Markdown file path')
    ap.add_argument('-output', required=True, help='Output HTML file path')
    ap.add_argument('-title', default='', help='Document title (auto from first h1 if empty)')
    args = ap.parse_args()

    # 读取时按通用换行符规范化（CRLF/LF/CR -> LF），与 goldmark 解析行为一致；
    # 输出用 newline='' 关闭行尾翻译，保证与 Go 版（直接写原始字节）行尾完全一致。
    with open(args.input, 'r', encoding='utf-8') as f:
        md = f.read()
    md = md.replace('\r\n', '\n').replace('\r', '\n')

    body = md_to_html(md)
    body, toc_html = post_process(body)
    body = body.lstrip()  # 去除前导空白（等价 goquery 的 TrimLeft）
    body += '\n'  # goldmark 产物末尾带一个换行，template 再接 </div> 形成空行，保持逐字节一致

    title = args.title if args.title else extract_title(body)

    tpl_path = find_template()
    with open(tpl_path, 'r', encoding='utf-8', newline='') as f:
        tpl = f.read()

    result = tpl.replace('{{TITLE}}', title).replace('{{BODY}}', body).replace('{{TOC}}', toc_html)

    with open(args.output, 'w', encoding='utf-8', newline='') as f:
        f.write(result)

    print('Generated: ' + args.output)


if __name__ == '__main__':
    main()
