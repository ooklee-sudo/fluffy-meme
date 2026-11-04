const fs=require('fs');
const C=[];const F='';const AlignmentType={CENTER:'c'};
const P=(s,o)=>({t:'P',s});const H1=s=>({t:'H1',s});const H2=s=>({t:'H2',s});const B=s=>({t:'B',s});
const cap=s=>({t:'cap',s});const note=s=>({t:'note',s});const table=(w,r)=>({t:'table',w,r});const sidebar=(h,p)=>({t:'sidebar',h,p});
function Paragraph(o){return {t:'para',o:o}} ; function TextRun(o){return o} ; function ImageRun(o){return {img:1}}
const body=fs.readFileSync('body2.js','utf8').replace(/new Paragraph\(/g,'Paragraph(').replace(/new TextRun\(/g,'TextRun(').replace(/new ImageRun\(\{[^]*?\}\)\]/,'ImageRun({})]').replace(/refs\.forEach[^\n]*\n/,'C.push({t:"refs",refs});\n').replace(/C\.push\(new Paragraph\(\{spacing:\{before:360[^\n]*\n/,'').replace(/fs\.readFileSync\(process\.argv\[3\]\)/,'0');
eval(body.replace(/C\.push\(Paragraph\(\{spacing:\{before:360[^\n]*\n/,''));
const runs=(s)=>s;
fs.writeFileSync('content.json',JSON.stringify(C,null,1));
