#!/usr/bin/env node
// 统一审核页入口：复用稳定模板，并固定搜索、重置、架构/动作筛选、显示无需操作和完整分页。
import fs from 'node:fs';

const args = process.argv.slice(2);
const input = args[args.indexOf('--input') + 1];
const output = args[args.indexOf('--output') + 1];
const temp = `${input}.render-temp.json`;
const plan = JSON.parse(fs.readFileSync(input, 'utf8').replace(/^\uFEFF/, ''));
const labels = { raw:'原始表格行', logical:'去重后逻辑项', target:'目标表记录', officialMatched:'严格命中', officialPending:'官网待判定', officialMissing:'官网未命中', N:'新增', U:'更新', R:'追加备注', S:'无需操作', C:'待判定' };
plan.meta.counts = Object.fromEntries(Object.entries(plan.meta.counts ?? {}).map(([k, v]) => [labels[k] ?? k, v]));
fs.writeFileSync(temp, JSON.stringify(plan), 'utf8');
process.argv = [process.argv[0], process.argv[1], '--input', temp, '--output', output];
await import('./render_confirmation_html_v2.mjs');
let html = fs.readFileSync(output, 'utf8');
html = html.replace('<input id="q" placeholder="搜索名称、版本、编号、记录 ID 或 URL">', '<input id="q" placeholder="搜索名称、版本、编号、记录 ID 或 URL"><button id="reset" type="button">重置</button>');
html = html.replace('<label><input id="s" type="checkbox"> 显示无需操作</label>', '');
html = html.replace("s=$('#s').checked", 's=true');
html = html.replace("['q','a','x','s','n']", "['q','a','x','n']");
html = html.replace('<button id="p">上一页</button><span id="z"></span><button id="qnext">下一页</button>', '<button id="first">首页</button><button id="p">上一页</button><span id="z"></span><button id="qnext">下一页</button><button id="last">末页</button>');
html = html.replace('<option>10</option><option selected>20</option>', '<option selected>10</option><option>20</option>');
const hasExecutable = (plan.items ?? []).some(i => ['N','U','R'].includes(i.action));
html = html.replace("draw();</script>", `if(!${hasExecutable})$('#x').value='';draw();$('#reset').onclick=()=>{$('#q').value='';$('#a').value='';$('#x').value='${hasExecutable ? 'active' : ''}';$('#n').value='10';pg=1;draw()};$('#first').onclick=()=>{pg=1;draw()};$('#last').onclick=()=>{pg=Math.ceil(data().length/+$('#n').value);draw()};</script>`);
fs.writeFileSync(output, html, 'utf8');
