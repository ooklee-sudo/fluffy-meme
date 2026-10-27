const fs=require('fs');const d=require('docx');
const {title,abstract,keywords,body,tables,refs,appendix}=require(process.env.CONTENT||'./content.js');
const path=require('path');
const F="Times New Roman";
function runs(t,extra={}){const out=[];const re=/(\*\*[^*]+\*\*|\*[^*]+\*)/g;let last=0,m;
  while((m=re.exec(t))){if(m.index>last)out.push(new d.TextRun({text:t.slice(last,m.index),font:F,size:24,...extra}));const s=m[0];
    if(s.startsWith('**'))out.push(new d.TextRun({text:s.slice(2,-2),bold:true,font:F,size:24,...extra}));else out.push(new d.TextRun({text:s.slice(1,-1),italics:true,font:F,size:24,...extra}));last=m.index+s.length;}
  if(last<t.length)out.push(new d.TextRun({text:t.slice(last),font:F,size:24,...extra}));return out;}
const dbl={line:480};
const P=t=>new d.Paragraph({children:runs(t),spacing:dbl,indent:{firstLine:720}});
const H1=t=>new d.Paragraph({heading:d.HeadingLevel.HEADING_1,children:[new d.TextRun({text:t,bold:true,font:F,size:24})],spacing:{before:240,after:0,line:480},keepNext:true});
const H2=t=>new d.Paragraph({heading:d.HeadingLevel.HEADING_2,children:[new d.TextRun({text:t,bold:true,italics:true,font:F,size:24})],spacing:{before:120,after:0,line:480},keepNext:true});
const bd={style:d.BorderStyle.SINGLE,size:4,color:"000000"};const borders={top:bd,bottom:bd,left:bd,right:bd};
function cell(t,w,head){return new d.TableCell({width:{size:w,type:d.WidthType.DXA},borders,margins:{top:50,bottom:50,left:80,right:80},shading:head?{type:d.ShadingType.CLEAR,fill:"E7E7E7",color:"auto"}:undefined,children:[new d.Paragraph({children:[new d.TextRun({text:t,font:F,size:19,bold:!!head})]})]});}
function table(T){const w=T.widths;return new d.Table({width:{size:w.reduce((a,b)=>a+b),type:d.WidthType.DXA},columnWidths:w,rows:[new d.TableRow({tableHeader:true,children:T.head.map((h,i)=>cell(h,w[i],true))}),...T.rows.map(r=>new d.TableRow({cantSplit:true,children:r.map((c,i)=>cell(c,w[i]))}))]});}
const kids=[];let tn=0;
kids.push(new d.Paragraph({alignment:d.AlignmentType.CENTER,spacing:{after:240,line:360},children:[new d.TextRun({text:title,bold:true,font:F,size:28})]}));
kids.push(new d.Paragraph({alignment:d.AlignmentType.CENTER,spacing:{after:120},children:[new d.TextRun({text:"Abstract",bold:true,font:F,size:24})]}));
kids.push(new d.Paragraph({spacing:dbl,children:runs(abstract)}));
kids.push(new d.Paragraph({spacing:{...dbl,before:120},children:[new d.TextRun({text:"Keywords: ",bold:true,font:F,size:24}),new d.TextRun({text:keywords,font:F,size:24})]}));
kids.push(new d.Paragraph({children:[new d.PageBreak()]}));
for(const b of body){
  if(b.h1)kids.push(H1(b.h1));else if(b.h2)kids.push(H2(b.h2));else if(b.p)kids.push(P(b.p));
  else if(b.figure){const img=fs.readFileSync(path.join(__dirname,b.figure));const iw=img.readUInt32BE(16),ih=img.readUInt32BE(20);const w=Math.min(600,Math.round(740*iw/ih)),h=Math.round(w*ih/iw);
    kids.push(new d.Paragraph({alignment:d.AlignmentType.CENTER,spacing:{before:120,after:60},keepNext:true,children:[new d.ImageRun({type:"png",data:img,transformation:{width:w,height:h},altText:{title:"Forest plot",description:b.alt,name:"Figure1"}})]}));
    kids.push(new d.Paragraph({spacing:{after:200,line:276},children:[new d.TextRun({text:"Figure 1. ",bold:true,font:F,size:22}),new d.TextRun({text:b.caption,font:F,size:22})]}));}
  else if(b.table){tn++;const T=tables[b.table];
    kids.push(new d.Paragraph({spacing:{before:120,after:80},keepNext:true,children:[new d.TextRun({text:`Table ${tn}. `,bold:true,font:F,size:22}),new d.TextRun({text:T.caption,font:F,size:22})]}));
    kids.push(table(T));kids.push(new d.Paragraph({spacing:{after:200},children:[]}));}
}
kids.push(new d.Paragraph({children:[new d.PageBreak()]}));
kids.push(new d.Paragraph({alignment:d.AlignmentType.CENTER,spacing:{after:120},children:[new d.TextRun({text:"References",bold:true,font:F,size:24})]}));
for(const r of refs)kids.push(new d.Paragraph({spacing:{line:480},indent:{left:720,hanging:720},children:runs(r)}));
kids.push(new d.Paragraph({children:[new d.PageBreak()]}));
for(const b of appendix){if(b.h1)kids.push(H1(b.h1));else if(b.p)kids.push(P(b.p));}
const doc=new d.Document({creator:"Anonymous",lastModifiedBy:"Anonymous",title:"Manuscript",styles:{default:{document:{run:{font:F,size:24}}},paragraphStyles:[
 {id:"Heading1",name:"Heading 1",basedOn:"Normal",next:"Normal",quickFormat:true,run:{font:F,size:24,bold:true},paragraph:{outlineLevel:0}},
 {id:"Heading2",name:"Heading 2",basedOn:"Normal",next:"Normal",quickFormat:true,run:{font:F,size:24,bold:true,italics:true},paragraph:{outlineLevel:1}}]},
 sections:[{properties:{page:{size:{width:12240,height:15840},margin:{top:1440,right:1440,bottom:1440,left:1440}}},
 footers:{default:new d.Footer({children:[new d.Paragraph({alignment:d.AlignmentType.CENTER,children:[new d.TextRun({children:[d.PageNumber.CURRENT],font:F,size:22})]})]})},children:kids}]});
d.Packer.toBuffer(doc).then(b=>fs.writeFileSync(process.argv[2],b));
