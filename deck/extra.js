const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE";
p.author = "AI映像プラットフォーム事業";
p.title  = "市場規模と制作費の構造";

const INK="16161A", PAPER="FFFFFF", SOFT="F4F2EF", VERM="B3121B",
      GOLD="C9962C", NAVY="2A3563", MUTED="6E6E76", LINE="DCD9D4",
      INKSOFT="3A3A42", TEAL="1F6F63", ORANGE="D9601A", ONORG="FBE2D2";
const F="Yu Gothic";
const M=0.65, W=12.03;
let pageNo=0;

function base(){ const s=p.addSlide(); s.background={color:PAPER}; return s; }
function head(s,num,title,sub){
  s.addShape(p.ShapeType.rect,{x:M,y:0.44,w:0.52,h:0.52,fill:{color:VERM}});
  s.addText(String(num),{x:M,y:0.44,w:0.52,h:0.52,fontFace:F,fontSize:17,bold:true,color:PAPER,align:"center",valign:"middle",margin:0,isTextBox:true});
  s.addText(title,{x:1.32,y:0.40,w:W-0.67,h:0.6,fontFace:F,fontSize:25,bold:true,color:INK,valign:"middle",margin:0,isTextBox:true});
  s.addText(sub,{x:1.32,y:1.02,w:W-0.67,h:0.34,fontFace:F,fontSize:12,color:MUTED,valign:"middle",margin:0,isTextBox:true});
}
function foot(s,note){
  pageNo++;
  s.addText(note,{x:M,y:6.90,w:W-1.2,h:0.36,fontFace:F,fontSize:8,color:MUTED,valign:"middle",margin:0,isTextBox:true});
  s.addText(String(pageNo),{x:12.28,y:6.93,w:0.4,h:0.3,fontFace:F,fontSize:9,color:MUTED,align:"right",valign:"middle",margin:0,isTextBox:true});
}
function sec(s,x,y,w,t){
  s.addText(t,{x,y,w,h:0.3,fontFace:F,fontSize:11.5,bold:true,color:INK,valign:"middle",margin:0,isTextBox:true});
}
function card(s,x,y,w,h,title,lines,accent,fs){
  s.addShape(p.ShapeType.rect,{x,y,w,h,fill:{color:SOFT}});
  s.addShape(p.ShapeType.rect,{x:x+0.24,y:y+0.28,w:0.12,h:0.12,fill:{color:accent||VERM}});
  s.addText(title,{x:x+0.48,y:y+0.18,w:w-0.72,h:0.32,fontFace:F,fontSize:12.5,bold:true,color:INK,valign:"middle",margin:0,isTextBox:true});
  s.addText(lines.map((t,i)=>({text:t,options:{breakLine:i<lines.length-1}})),
    {x:x+0.48,y:y+0.56,w:w-0.72,h:h-0.76,fontFace:F,fontSize:fs||10,color:INKSOFT,lineSpacingMultiple:1.26,valign:"top",margin:0,isTextBox:true});
}
function warn(s,x,y,w,h,title,lines,fs){
  s.addShape(p.ShapeType.rect,{x,y,w,h,fill:{color:"FBF1F1"}});
  s.addShape(p.ShapeType.rect,{x,y,w:0.05,h,fill:{color:VERM}});
  s.addText("⚠ "+title,{x:x+0.28,y:y+0.14,w:w-0.5,h:0.3,fontFace:F,fontSize:12,bold:true,color:VERM,valign:"middle",margin:0,isTextBox:true});
  s.addText(lines.map((t,i)=>({text:t,options:{breakLine:i<lines.length-1}})),
    {x:x+0.28,y:y+0.50,w:w-0.5,h:h-0.64,fontFace:F,fontSize:fs||10,color:INKSOFT,lineSpacingMultiple:1.26,valign:"top",margin:0,isTextBox:true});
}
function table(s,x,y,w,rows,colW,fs,rowH){
  s.addTable(rows,{x,y,w,colW,fontFace:F,fontSize:fs||10,color:INKSOFT,valign:"middle",
    border:{type:"solid",color:LINE,pt:0.6},rowH:rowH||0.34,margin:[4,7,4,7]});
}
function hrow(c){ return c.map(t=>({text:t,options:{bold:true,color:PAPER,fill:{color:ORANGE},fontSize:9.5}})); }
function stat(s,x,y,w,h,big,label,note,col,bs){
  s.addShape(p.ShapeType.rect,{x,y,w,h,fill:{color:SOFT}});
  s.addText(big,{x:x+0.26,y:y+0.16,w:w-0.52,h:0.62,fontFace:F,fontSize:bs||26,bold:true,color:col||VERM,valign:"middle",margin:0,isTextBox:true});
  s.addText(label,{x:x+0.26,y:y+0.80,w:w-0.52,h:0.3,fontFace:F,fontSize:11,bold:true,color:INK,valign:"middle",margin:0,isTextBox:true});
  s.addText(note,{x:x+0.26,y:y+1.10,w:w-0.52,h:h-1.24,fontFace:F,fontSize:9,color:MUTED,valign:"top",lineSpacingMultiple:1.2,margin:0,isTextBox:true});
}

/* ═════════════ A. 企業案件と個人案件の市場規模 ═════════════ */
{
  const s=base();
  head(s,1,"企業案件と個人案件 — 発注市場の規模","「誰がお金を払うのか」で見ると、法人と個人では市場の性質がまったく違います");

  const w3=(W-0.6)/3, y0=1.50, h0=1.50;
  stat(s,M,            y0,w3,h0,"4,580億円","企業案件｜法人が発注する市場",
    "国内動画制作サービス市場（2025年度予測）。2024年度 4,238億円 → 2027年度 5,400億円\n【実測値・矢野経済研究所】",VERM,26);
  stat(s,M+w3+0.3,     y0,w3,h0,"6,800億円","個人案件｜個人が発注する市場",
    "スキルシェア市場全体の2028年予測。動画編集はこのうちの一部にすぎず、\n【直接の統計は存在しません】",NAVY,26);
  stat(s,M+(w3+0.3)*2, y0,w3,h0,"2兆894億円","参考｜個人が「受け取る」市場",
    "クリエイターエコノミー（2024年）。これは発注市場ではなく報酬市場です。\n【混同しないこと】",MUTED,26);

  sec(s,M,3.14,W,"同じ「1本の動画」でも、取引の形が違います");
  const rows=[
    hrow(["","企業案件（法人が発注）","個人案件（個人が発注）"]),
    [{text:"1件あたり単価",options:{bold:true,color:INK}},{text:"20万〜200万円（制作会社）／代理店経由は100万〜1,000万円",options:{color:VERM,bold:true}},{text:"5,000円〜30万円。簡易編集は1,000円台も",options:{color:NAVY,bold:true}}],
    [{text:"発注者",options:{bold:true,color:INK}},"事業会社の広報・マーケ部門／広告代理店／制作会社","YouTuber・配信者・インフルエンサー・個人事業主"],
    [{text:"取引の場",options:{bold:true,color:INK}},"相見積 → 稟議 → 発注書 → 検収 → 請求","ココナラ・ランサーズ・クラウドワークス（PFが仲介）"],
    [{text:"与信・請求",options:{bold:true,color:INK}},{text:"必要。ここが個人クリエイターには越えられない壁",options:{bold:true}},"原則プラットフォームが代行するため不要"],
    [{text:"市場の性質",options:{bold:true,color:INK}},"単価が高く件数が少ない。参入障壁が高い","単価が低く件数が多い。初級案件は完全な買い手市場"],
  ];
  table(s,M,3.46,W,rows,[1.9,5.1,5.03],9.5,0.40);

  warn(s,M,5.96,W,0.86,"個人は「発注者」ではなく「稼ぎ手」です",
    ["個人が発注する市場は小さく、統計すら整備されていません。一方、個人が受け取る市場は2兆円規模です。",
     "だから当社は、法人を発注側（P1）、個人を供給側（登録クリエイター）として扱います。"],9.5);
  foot(s,"出所: 矢野経済研究所（動画コンテンツビジネス調査2025）／ Business Insider Japan（スキルシェア市場2028年予測）／ クリエイターエコノミー協会（2025年版調査）／ ココナラ・ランサーズ公開単価。企業案件は実測値、個人案件は推計値です");
}

/* ═════════════ B. 制作費の相場・内訳とAIの効果 ═════════════ */
{
  const s=base();
  head(s,2,"AI導入で、制作費はいくらになり、いくら浮くのか","削減が効くのは「人が動く工程」です。撮影・機材・出演で費用の55%。ここが消えると単価の桁が変わります");

  sec(s,M,1.48,W,"用途別｜現状の制作費 → AI導入後の制作費 → コストメリット");
  const rows=[
    hrow(["用途","現状の制作費","AI導入後","コストメリット（削減額）","削減率","AIの効き方"]),
    ["映画（実写）","3〜5億円","2.4〜4億円",{text:"▲6,000万〜1億円",options:{bold:true,color:VERM}},{text:"▲20%",options:{bold:true,align:"center"}},"部分適用のみ。VFX・群衆・背景"],
    ["アニメ映画","1〜20億円","7,000万〜14億円",{text:"▲3,000万〜6億円",options:{bold:true,color:VERM}},{text:"▲30%",options:{bold:true,align:"center"}},"中割・背景・彩色の自動化"],
    ["テレビCM（制作費）","1,000万〜1億円","500万〜5,000万円",{text:"▲500万〜5,000万円",options:{bold:true,color:VERM}},{text:"▲50%",options:{bold:true,align:"center"}},"実写×生成AIのハイブリッド"],
    [{text:"★ 企業VP・会社紹介",options:{bold:true,color:INK}},{text:"50〜150万円",options:{bold:true}},{text:"18〜52万円",options:{bold:true,color:TEAL}},{text:"▲32〜98万円",options:{bold:true,color:VERM}},{text:"▲65%",options:{bold:true,color:VERM,align:"center"}},{text:"フル生成AIが成立。撮影が消える",options:{bold:true}}],
    [{text:"★ 展示会・社内イベント映像",options:{bold:true,color:INK}},{text:"20〜100万円",options:{bold:true}},{text:"6〜30万円",options:{bold:true,color:TEAL}},{text:"▲14〜70万円",options:{bold:true,color:VERM}},{text:"▲70%",options:{bold:true,color:VERM,align:"center"}},{text:"同上。ループ素材は特に効く",options:{bold:true}}],
    [{text:"★ PR素材・SNS縦型",options:{bold:true,color:INK}},{text:"10〜50万円",options:{bold:true}},{text:"2〜10万円",options:{bold:true,color:TEAL}},{text:"▲8〜40万円",options:{bold:true,color:VERM}},{text:"▲80%",options:{bold:true,color:VERM,align:"center"}},{text:"量産前提。1本あたりが最も下がる",options:{bold:true}}],
  ];
  table(s,M,1.78,W,rows,[2.30,1.95,1.95,2.25,0.95,2.63],9.5,0.40);
  s.addText("★ 下3行がフル生成AIの成立帯です。当社の企業案件（P1）は、この帯を取りに行きます。映画・CMは部分適用にとどまり、桁は変わりません。",
    {x:M,y:4.62,w:W,h:0.28,fontFace:F,fontSize:10,bold:true,color:VERM,valign:"middle",margin:0,isTextBox:true});

  /* ── 下段左: 内訳の before / after ── */
  sec(s,M,4.98,5.9,"内訳はこう変わる｜企業VP 1本　100万円 → 35万円");
  const parts=[["企画",15,7.5,NAVY],["撮影",38,7.6,VERM],["機材",10,2.0,"8C1F26"],
               ["出演",7,0.7,ORANGE],["編集",20,10.0,TEAL],["諸経費",10,7.0,MUTED]];
  const bx=M+1.10, bw=4.15;
  [["現状",5.34,1],["AI後",5.76,2]].forEach(r=>{
    let cx=bx;
    s.addText(r[0],{x:M,y:r[1],w:1.02,h:0.30,fontFace:F,fontSize:9.5,bold:true,color:INK,valign:"middle",margin:0,isTextBox:true});
    parts.forEach(t=>{ const v=r[2]===1?t[1]:t[2], w=bw*v/100;
      s.addShape(p.ShapeType.rect,{x:cx,y:r[1],w,h:0.30,fill:{color:t[3]}});
      if(v>=12) s.addText(String(v),{x:cx,y:r[1],w,h:0.30,fontFace:F,fontSize:8.5,bold:true,color:PAPER,align:"center",valign:"middle",margin:0,isTextBox:true});
      cx+=w; });
    s.addText(r[2]===1?"100万円":"35万円",{x:cx+0.08,y:r[1],w:1.0,h:0.30,fontFace:F,fontSize:10,bold:true,
      color:r[2]===1?INK:TEAL,valign:"middle",margin:0,isTextBox:true});
  });
  parts.forEach((t,i)=>{ const x=M+i*0.98;
    s.addShape(p.ShapeType.rect,{x,y:6.20,w:0.13,h:0.13,fill:{color:t[3]}});
    s.addText(t[0],{x:x+0.19,y:6.13,w:0.78,h:0.26,fontFace:F,fontSize:8,color:MUTED,valign:"middle",margin:0,isTextBox:true});
  });
  s.addText("消えるのは 撮影38＋機材10＋出演7＝55%。編集と諸経費は残ります。",
    {x:M,y:6.44,w:5.9,h:0.26,fontFace:F,fontSize:8.5,bold:true,color:VERM,valign:"middle",margin:0,isTextBox:true});

  /* ── 下段右: 実例 ── */
  card(s,M+6.2,4.98,W-6.2,1.72,"実際に出ている削減幅（実例）",
    ["大手保険のWeb広告動画　制作コスト ▲30〜50%／期間 ▲40%",
     "Amazon Nova活用の広告　費用 ▲70%・効果 8倍",
     "サイバーエージェント　1本 数千万円・3ヶ月 → 3本 300万円・1.5〜2週間",
     "映画の群衆シーン　9,000万円 → 150万円（▲98%）",
     "米国の企業動画　1分あたり 約63万円 → 約38万円（▲40%・実測）"],GOLD,9.5);
  foot(s,"出所: 動画幹事・ムビサク・デジタルドロップ（制作費相場／撮影費は制作費の35〜40%）／ ムービーインパクト・各社プレスリリース（AI導入の削減事例）／ Vidico（米国の1分単価）。用途別の削減率は、工程別の削減率（企画▲50%・撮影▲80%・機材▲80%・出演▲90%・編集▲50%・諸経費▲30%）を費用構成に当てた当社試算です");
}

p.writeFile({fileName:"extra.pptx"}).then(()=>console.log("written: extra.pptx"));
