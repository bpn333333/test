const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE";               // 13.333 x 7.5
p.author = "AI映像プラットフォーム事業";
p.title  = "投資家向け企画書";

const INK="16161A", PAPER="FFFFFF", SOFT="F4F2EF", VERM="B3121B",
      GOLD="C9962C", NAVY="2A3563", MUTED="6E6E76", LINE="DCD9D4",
      INKSOFT="3A3A42", ONDARK="EDEBE7", TEAL="1F6F63",
      ORANGE="D9601A", ONORG="FBE2D2";
const F="Yu Gothic";
const M=0.65, W=12.03;

let pageNo = 0;
function base(dark){
  const s = p.addSlide();
  s.background = { color: dark ? ORANGE : PAPER };
  return s;
}
function head(s, num, title, sub){
  if(num!==null && num!==undefined){
    s.addShape(p.ShapeType.rect, { x:M, y:0.44, w:0.52, h:0.52, fill:{color:VERM} });
    s.addText(String(num), { x:M, y:0.44, w:0.52, h:0.52, fontFace:F, fontSize:17, bold:true,
      color:PAPER, align:"center", valign:"middle", margin:0, isTextBox:true });
  }
  s.addText(title, { x:1.32, y:0.40, w:W-0.67, h:0.6, fontFace:F, fontSize:25, bold:true,
    color:INK, valign:"middle", margin:0, isTextBox:true });
  if(sub) s.addText(sub, { x:1.32, y:1.02, w:W-0.67, h:0.34, fontFace:F, fontSize:12,
    color:MUTED, valign:"middle", margin:0, isTextBox:true });
}
function foot(s, note){
  pageNo++;
  if(note) s.addText(note, { x:M, y:6.93, w:W-1.2, h:0.34, fontFace:F, fontSize:8.5,
    color:MUTED, valign:"middle", margin:0, isTextBox:true });
  s.addText(String(pageNo), { x:12.28, y:6.93, w:0.4, h:0.3, fontFace:F, fontSize:9,
    color:MUTED, align:"right", valign:"middle", margin:0, isTextBox:true });
}
function lede(s, y, lines, h){
  s.addShape(p.ShapeType.rect, { x:M, y, w:0.055, h:h||0.86, fill:{color:VERM} });
  s.addText(lines.map((t,i)=>({text:t, options:{breakLine:i<lines.length-1, color:i===0?VERM:INK}})),
    { x:M+0.25, y, w:W-0.25, h:h||0.86, fontFace:F, fontSize:15.5, bold:true, color:INK,
      lineSpacingMultiple:1.3, valign:"middle", margin:0, isTextBox:true });
}
function stat(s, x, y, w, h, big, label, note, col, bigSize){
  s.addShape(p.ShapeType.rect, { x, y, w, h, fill:{color:SOFT} });
  s.addText(big, { x:x+0.26, y:y+0.18, w:w-0.52, h:0.66, fontFace:F, fontSize:bigSize||27, bold:true,
    color:col||VERM, valign:"middle", margin:0, isTextBox:true });
  s.addText(label, { x:x+0.26, y:y+0.86, w:w-0.52, h:0.28, fontFace:F, fontSize:11, bold:true,
    color:INK, valign:"middle", margin:0, isTextBox:true });
  if(note) s.addText(note, { x:x+0.26, y:y+1.16, w:w-0.52, h:h-1.3, fontFace:F, fontSize:9,
    color:MUTED, valign:"top", lineSpacingMultiple:1.2, margin:0, isTextBox:true });
}
function card(s, x, y, w, h, title, lines, accent, fs){
  s.addShape(p.ShapeType.rect, { x, y, w, h, fill:{color:SOFT} });
  s.addShape(p.ShapeType.rect, { x:x+0.24, y:y+0.28, w:0.12, h:0.12, fill:{color:accent||VERM} });
  s.addText(title, { x:x+0.48, y:y+0.18, w:w-0.72, h:0.32, fontFace:F, fontSize:12.5, bold:true,
    color:INK, valign:"middle", margin:0, isTextBox:true });
  s.addText(lines.map((t,i)=>({ text:t, options:{ breakLine:i<lines.length-1 } })),
    { x:x+0.48, y:y+0.56, w:w-0.72, h:h-0.76, fontFace:F, fontSize:fs||10,
      color:INKSOFT, lineSpacingMultiple:1.26, valign:"top", margin:0, isTextBox:true });
}
function table(s, x, y, w, rows, colW, fs, rowH){
  const f=fs||10;
  s.addTable(rows, {
    x, y, w, colW,
    fontFace:F, fontSize:f, color:INKSOFT, valign:"middle",
    border:{type:"solid", color:LINE, pt:0.6},
    rowH: rowH||0.34,
    margin:[4,7,4,7],
  });
}
function hrow(cells){ return cells.map(t=>({ text:t, options:{ bold:true, color:PAPER, fill:{color:ORANGE}, fontSize:9.5 } })); }
function warn(s, x, y, w, h, title, lines){
  s.addShape(p.ShapeType.rect, { x, y, w, h, fill:{color:"FBF1F1"} });
  s.addShape(p.ShapeType.rect, { x, y, w:0.05, h, fill:{color:VERM} });
  s.addText("⚠ "+title, { x:x+0.28, y:y+0.16, w:w-0.5, h:0.3, fontFace:F, fontSize:12, bold:true,
    color:VERM, valign:"middle", margin:0, isTextBox:true });
  s.addText(lines.map((t,i)=>({text:t, options:{breakLine:i<lines.length-1}})),
    { x:x+0.28, y:y+0.52, w:w-0.5, h:h-0.68, fontFace:F, fontSize:10, color:INKSOFT,
      lineSpacingMultiple:1.26, valign:"top", margin:0, isTextBox:true });
}


/* ── 図形ヘルパー ────────────────────────────────────────── */
function box(s,x,y,w,h,title,body,fill,tc,bc,ts,bs){
  s.addShape(p.ShapeType.rect,{x,y,w,h,fill:{color:fill||SOFT}});
  s.addText(title,{x:x+0.16,y:y+0.10,w:w-0.32,h:0.34,fontFace:F,fontSize:ts||11.5,bold:true,
    color:tc||INK,align:"center",valign:"middle",margin:0,isTextBox:true});
  if(body) s.addText(body,{x:x+0.16,y:y+0.44,w:w-0.32,h:h-0.56,fontFace:F,fontSize:bs||9,
    color:bc||MUTED,align:"center",valign:"top",lineSpacingMultiple:1.2,margin:0,isTextBox:true});
}
function arw(s,dir,x,y,w,h,col){
  const m={r:"rightArrow",l:"leftArrow",u:"upArrow",d:"downArrow"};
  s.addShape(p.ShapeType[m[dir]],{x,y,w,h,fill:{color:col||LINE}});
}
function dot(s,x,y,d,label,col){
  s.addShape(p.ShapeType.ellipse,{x,y,w:d,h:d,fill:{color:col||VERM}});
  s.addText(label,{x,y,w:d,h:d,fontFace:F,fontSize:10,bold:true,color:PAPER,
    align:"center",valign:"middle",margin:0,isTextBox:true});
}
function hbar(s,x,y,w,h,frac,label,val,col,lw){
  s.addText(label,{x,y,w:lw,h,fontFace:F,fontSize:9.5,color:INKSOFT,valign:"middle",margin:0,isTextBox:true});
  const bx=x+lw+0.12, bw=w-lw-1.0;
  s.addShape(p.ShapeType.rect,{x:bx,y:y+h/2-0.11,w:Math.max(bw*frac,0.05),h:0.22,fill:{color:col||NAVY}});
  s.addText(val,{x:x+w-0.95,y,w:0.95,h,fontFace:F,fontSize:9.5,bold:true,color:INK,
    align:"right",valign:"middle",margin:0,isTextBox:true});
}

/* ═══════════ 1. 表紙 ═══════════ */
{
  const s = base(true);
  s.addShape(p.ShapeType.rect, { x:M, y:2.05, w:0.62, h:0.62, fill:{color:PAPER} });
  s.addText("AI映像プラットフォーム", { x:M, y:2.95, w:11.9, h:0.95, fontFace:F, fontSize:42, bold:true,
    color:PAPER, valign:"middle", margin:0, isTextBox:true });
  s.addText("世界のクリエイターが作り、稼ぐ場所をつくる。企業案件は、私たちが取ってくる。",
    { x:M, y:3.98, w:11.9, h:0.5, fontFace:F, fontSize:16, color:ONDARK, valign:"middle", margin:0, isTextBox:true });
  s.addText("投資家向け企画書  ／  2026年9月", { x:M, y:5.6, w:7, h:0.36, fontFace:F, fontSize:12, color:ONORG, valign:"middle", margin:0, isTextBox:true });
  s.addText("新設法人（株式会社・仮称）", { x:M, y:5.96, w:7, h:0.36, fontFace:F, fontSize:12, color:ONORG, valign:"middle", margin:0, isTextBox:true });
}

/* ═══════════ 2. エグゼクティブサマリー ═══════════ */
{
  const s = base(false);
  head(s, 0, "エグゼクティブサマリー", "クリエイターに「再生数ゼロでも稼げる理由」を先に渡し、そこからプラットフォームを立ち上げます");
  lede(s, 1.50, ["5年後・2031年、東証グロース市場への上場を目指す。",
    "中国を中心に世界のAIクリエイターを集め、課金とマッチングの両輪で回すプラットフォームをつくる。"]);
  const y0=2.56, h=1.38, w=(W-0.6)/3;
  stat(s, M,           y0, w, h, "約340億ドル〜", "AI短劇の市場規模（中国・推計）", "海外市場は500億ドル超との推計。ユーザー28億人");
  stat(s, M+w+0.3,     y0, w, h, "2本立て",     "収益の柱", "企業案件の仲介（初日から）＋ 視聴課金の分配（6ヶ月目〜）", NAVY);
  stat(s, M+(w+0.3)*2, y0, w, h, "1.5億円",     "今回の調達目標", "", GOLD);
  const y1=4.12, h2=2.42, w2=(W-0.6)/3;
  card(s, M,            y1, w2, h2, "何をするか",
    ["① クリエイターが自由に投稿し、課金と視聴で稼げるプラットフォームを運営する。",
     "② 企業案件は当社が受注し、登録クリエイターに配分する。再生数がゼロでも稼げる。",
     "③ 溜まった制作データで生成AI関連の特許を取得し、モデル開発へ。"]);
  card(s, M+w2+0.3,     y1, w2, h2, "なぜ勝てるか",
    ["2026年、中国の大手PFは純AIコンテンツの分成を圧縮し、最低保証を廃止した。",
     "AI専業のクリエイターは行き場を探している。",
     "②があるので、トラフィックがゼロの初日からクリエイターに報酬を出せる。",
     "分成率で殴り合わずに済む唯一の設計。"], NAVY);
  card(s, M+(w2+0.3)*2, y1, w2, h2, "どこへ向かうか",
    ["1年目に基盤を作り、2〜3年目は投資期間。",
     "4年目に単月黒字化、5年目に年商37億・営業利益9億。",
     "自動車産業が輸入技術を4年で国産化したのと同じ道筋を、3年で。"], GOLD);
  foot(s, "数値の出所は各章に記載。市場規模・収支は［仮置き］を含む計画値です。中国の推計値は1ドル=7.1元で換算しています。");
}

/* ═══════════ 3. なぜ今なのか ═══════════ */
{
  const s = base(false);
  head(s, 1, "なぜ今なのか", "出遅れた日本、淘汰が始まった中国。そしてAIクリエイターが行き場を失った瞬間");
  const w=(W-0.9)/4, y=1.62, h=2.28;
  const items=[
    ["1","日本は出遅れている","政府がAI推進法を制定し、AI基本計画を閣議決定するほどの危機感。映像制作の現場にAIはまだ入っていない。",VERM],
    ["2","中国では淘汰が始まった","AI漫劇の制作会社は2026年Q1に1,216社→698社（−42%）。約90%が赤字。最大コストは制作費ではなく広告出稿で全体の約70%。",NAVY],
    ["3","AIクリエイターが行き場を失った","2026年、中国の大手PFは純AIコンテンツの分成を圧縮し、最低保証を廃止。リソースは実写へ移った。",GOLD],
    ["4","受け皿をつくる","彼らに「AIを冷遇しない場所」と「再生数ゼロでも稼げる企業案件」を渡す。そこから日本の技術資産へ。",TEAL],
  ];
  items.forEach((it,i)=>{
    const x=M+(w+0.3)*i;
    s.addShape(p.ShapeType.rect, { x, y, w, h, fill:{color:SOFT} });
    s.addText(it[0], { x:x+0.26, y:y+0.2, w:0.6, h:0.44, fontFace:F, fontSize:20, bold:true, color:it[3], valign:"middle", margin:0, isTextBox:true });
    s.addText(it[1], { x:x+0.26, y:y+0.72, w:w-0.52, h:0.6, fontFace:F, fontSize:12.5, bold:true, color:INK, valign:"top", lineSpacingMultiple:1.2, margin:0, isTextBox:true });
    s.addText(it[2], { x:x+0.26, y:y+1.4, w:w-0.52, h:h-1.58, fontFace:F, fontSize:9.5, color:INKSOFT, valign:"top", lineSpacingMultiple:1.24, margin:0, isTextBox:true });
  });
  s.addShape(p.ShapeType.rect, { x:M, y:4.22, w:W, h:2.28, fill:{color:ORANGE} });
  s.addText("中国のAI漫劇 制作会社数（活躍承制方）", { x:M+0.4, y:4.42, w:6, h:0.3, fontFace:F, fontSize:11, color:ONORG, valign:"middle", margin:0, isTextBox:true });
  s.addText("2025年 Q4", { x:M+0.4, y:4.86, w:2.2, h:0.28, fontFace:F, fontSize:10.5, color:ONORG, valign:"middle", margin:0, isTextBox:true });
  s.addText("1,216社", { x:M+0.4, y:5.14, w:2.4, h:0.6, fontFace:F, fontSize:30, bold:true, color:ONORG, valign:"middle", margin:0, isTextBox:true });
  s.addText("→", { x:M+3.0, y:5.14, w:0.7, h:0.6, fontFace:F, fontSize:24, color:ONORG, align:"center", valign:"middle", margin:0, isTextBox:true });
  s.addText("2026年 Q1", { x:M+3.8, y:4.86, w:2.2, h:0.28, fontFace:F, fontSize:10.5, color:ONORG, valign:"middle", margin:0, isTextBox:true });
  s.addText("698社", { x:M+3.8, y:5.14, w:2.4, h:0.6, fontFace:F, fontSize:30, bold:true, color:PAPER, valign:"middle", margin:0, isTextBox:true });
  s.addText([{text:"1四半期で −42%。", options:{bold:true, color:PAPER, breakLine:true}},
             {text:"制作力が市場に溢れ出しています。約90%が赤字。最大コストは制作費ではなく広告出稿で全体の約70%。", options:{color:ONORG, breakLine:true}},
             {text:"彼らに足りないのは「作る力」ではなく「売る力」です。", options:{bold:true, color:PAPER}}],
    { x:M+7.0, y:4.7, w:W-7.5, h:1.4, fontFace:F, fontSize:11.5, lineSpacingMultiple:1.3, valign:"middle", margin:0, isTextBox:true });
  foot(s, "出所: 内閣府 AI戦略 ／ 第一財経・搜狐（中国AI短劇の淘汰）／ 网易「2026短劇分账新政」／ 経済産業省");
}

/* ═══════════ 4. 日本は一度、これをやっている ═══════════ */
{
  const s = base(false);
  head(s, 1, "日本は一度、これをやっている", "輸入した技術を4年で国産化し、その後20年以上の改善で世界一の品質に到達した");
  const yrs=[["1952","日産＝オースチン技術提携\n日野＝ルノー、いすゞ＝ルーツ"],
             ["1956-57","4社が相次いで完全国産化\nここまで4年"],
             ["1960s-70s","QCサークル・トヨタ生産方式\n改善を20年以上回し続ける"],
             ["1980s","品質と燃費で世界市場を取る\n米国メーカーが学びに来る側へ"],
             ["示唆","国産化は入口にすぎない。\n本当の資産はその後の改善"]];
  const w=(W-1.2)/5;
  yrs.forEach((it,i)=>{
    const x=M+(w+0.3)*i;
    s.addShape(p.ShapeType.rect, { x, y:1.62, w, h:1.16, fill:{color:SOFT} });
    s.addText(it[0], { x:x+0.2, y:1.72, w:w-0.4, h:0.34, fontFace:F, fontSize:13, bold:true, color:(i===4?ORANGE:VERM), valign:"middle", margin:0, isTextBox:true });
    s.addText(it[1], { x:x+0.2, y:2.06, w:w-0.4, h:0.64, fontFace:F, fontSize:9.5, color:INKSOFT, valign:"top", lineSpacingMultiple:1.2, margin:0, isTextBox:true });
  });
  const rows=[
    hrow(["","持っている側","","修得する側","期間","到達点"]),
    [{text:"1952 → 1956", options:{bold:true,color:INK}},"オースチン（英）\n完成した技術を持つ側","技術 →","日産・日野・いすゞ\nノックダウン生産で修得",{text:"4年",options:{bold:true,color:VERM,align:"center"}},"完全国産化。ただしこれは入口で、\n以後の改善で世界一の品質に到達した"],
    [{text:"2026 → 2029", options:{bold:true,color:INK}},"世界のAIクリエイター\n行き場を失っている側","制作力 →","当社プラットフォーム\n案件・課金・データで抱える",{text:"3年",options:{bold:true,color:VERM,align:"center"}},"内製化。ここからデータで改善を回し、\n品質で差をつける"],
  ];
  table(s, M, 3.0, W, rows, [1.5,2.5,1.0,2.7,0.8,3.53], 9.5, 0.7);
  warn(s, M, 5.18, W, 1.54, "ポイントは国産化の速さではありません。その後の改善で、世界一の品質を築いたことです。",
    ["日産・トヨタは国産化をゴールにせず、以後20年以上かけて生産方式と品質管理を磨き続けました。1980年代には米国メーカーが日本の生産方式を学びに来る側に回ります。",
     "当社も同じです。内製化（3年）は出発点にすぎません。①②で溜まった制作データで改善を回し続けることが、模倣されない資産になります。",
     "⚠ 当時は政府の保護（輸入制限・関税）がありました。今のAI映像にはありません。だから改善のサイクルをより速く回す必要があります。"]);
  foot(s, "出所: 日産自動車 企業情報 ／ トヨタ博物館 ／ GAZOO「ノックダウン生産の時代」／ 日本科学技術連盟（QCサークル・デミング賞）");
}

/* ═══════════ 5. 政策も同じ方向を向いている ═══════════ */
{
  const s = base(false);
  head(s, 1, "政策も同じ方向を向いている", "国はコンテンツを輸出産業にすると決め、予算を3倍にした");
  const w=(W-0.6)/3, y=1.6, h=1.5;
  stat(s, M,           y, w, h, "20兆円", "コンテンツ海外売上 目標（2033年）", "経産省「エンタメ・クリエイティブ産業戦略2026」");
  stat(s, M+w+0.3,     y, w, h, "3.5倍",  "経産省の財政支援規模", "令和6年度補正 101.1億円 → 令和7年度補正 350.2億円", NAVY);
  stat(s, M+(w+0.3)*2, y, w, h, "+26%",   "アニメの海外売上（2024年）", "2兆1,700億円。市場全体は3兆8,400億円", GOLD);
  const y1=3.42, h2=2.2, w2=(W-0.3)/2;
  card(s, M, y1, w2, h2, "AI政策",
    ["AI推進法（人工知能関連技術の研究開発及び活用の推進に関する法律）",
     "2025年5月28日成立 ／ 6月4日公布。日本初のAI基本法。",
     "AI基本計画を2025年12月23日に閣議決定。内閣にAI戦略本部を設置。"], NAVY, 10.5);
  card(s, M+w2+0.3, y1, w2, h2, "当社が実際に狙える支援",
    ["東京都 創業助成事業 — 上限400万円・助成率2/3・最長2年",
     "特許料等の減免 — 設立10年未満・資本金3億円以下なら1/3に軽減",
     "JLOX+ — 「制作の生産性向上に資するシステムの開発・実証」枠"], GOLD, 10.5);
  foot(s, "出所: 経済産業省「エンタメ・クリエイティブ産業戦略2026」／ 内閣府 AI戦略 ／ 東京都中小企業振興公社 ／ 特許庁");
}

/* ═══════════ 6. 市場規模 ═══════════ */
{
  const s = base(false);
  head(s, 2, "市場規模", "市場は制約になりません。制約はクリエイター獲得と視聴者獲得の資金です");
  const rows=[
    hrow(["","規模","性質"]),
    ["AI短劇 市場規模（中国・推計）",{text:"約5.0兆〜10.9兆円",options:{bold:true,color:VERM}},"推計。出所により幅が大きい"],
    ["同 海外市場（推計）",{text:"約7.5兆円超",options:{bold:true,color:VERM}},"ユーザー28億人との推計"],
    ["日本のショートドラマ市場",{text:"1,530億円（2026年予測）",options:{bold:true,color:NAVY}},"中国発アプリがシェア9割超"],
    ["日本の映像制作市場（企業案件）",{text:"4,580億円",options:{bold:true,color:NAVY}},"実測値。②の対象市場"],
  ];
  table(s, M, 1.58, W, rows, [4.2,3.5,4.33], 10.5, 0.42);
  const y1=3.72, h2=1.5, w2=(W-0.3)/2;
  card(s, M, y1, w2, h2, "追い風は実測できている",
    ["動画広告市場 2025年 8,855億円 → 2026年 1兆437億円",
     "縦型動画広告は前年比 155.9%"], NAVY, 11);
  card(s, M+w2+0.3, y1, w2, h2, "当社が取りに行く順序",
    ["初日は 企業案件（4,580億円の市場）。ここは実測値があります。",
     "6ヶ月目から 視聴課金。ここは推計値の世界です。"], GOLD, 11);
  warn(s, M, 5.4, W, 1.36, "制作原価の下落は、プラットフォーム側にとっては追い風です",
    ["米国では企業動画の制作費中央値がAI導入で 1分あたり約63万円 → 約38万円 に下落済み。受託事業にとっては単価下落の脅威です。",
     "しかし投稿されるコンテンツの量が増えるという意味では、プラットフォームにとっては供給が厚くなるということです。だから受託ではなくプラットフォームを主軸に据えます。"]);
  foot(s, "出所: サイバーエージェント 国内動画広告の市場調査 ／ TVtalk「AI短劇深度調研報告」／ nowhere film ／ Vidico（米国相場）。推計値は幅が大きく参考値です。為替は1ドル=150円・1元=21円で換算");
}

/* ═══════════ 7. ビジネスモデル ═══════════ */
{
  const s = base(false);
  head(s, 3, "ビジネスモデル", "両面市場です。ただし②があるため、視聴者がゼロの初日からクリエイターに報酬を出せます");
  const rows=[
    hrow(["","入口","当社","出口"]),
    [{text:"①",options:{bold:true,color:VERM,align:"center"}},"世界のクリエイター\n中国を中心に、自由に投稿","当社プラットフォーム\n配信・課金・分配・審査・権利処理","視聴者\n課金・視聴 → 収益をクリエイターへ分配"],
    [{text:"②",options:{bold:true,color:NAVY,align:"center"}},"日本の発注企業\n事業会社・広告代理店・制作会社","当社が受注し、配分\n要件定義・品質保証・契約・与信・請求","登録クリエイター\n再生数ゼロでも稼げる"],
    [{text:"③",options:{bold:true,color:GOLD,align:"center"}},"①②で溜まる制作データ\n指示→初稿→修正→承認／視聴維持率","内製化してモデル開発\n工程のツール化・生成AI関連の特許取得","プロダクト外販\n粗利率80%以上・人数に比例しない"],
  ];
  table(s, M, 1.6, W, rows, [0.7,3.65,3.9,3.78], 10, 0.86);
  warn(s, M, 5.16, W, 1.5, "②が①のコールドスタートを解きます",
    ["両面市場の宿命は「クリエイターは視聴者がいないと来ない、視聴者はコンテンツがないと来ない」。",
     "②は視聴者を必要としません。案件を配ればクリエイターは集まり、その作品が①の初期コンテンツになります。",
     "だから②を先に、①と並走させます。"]);
  foot(s, "クリエイター調達の設計は CHINA_SOURCING ／ プラットフォームの設計判断は PLATFORM_PIVOT を参照");
}

/* ═══════════ 8. 収益モデルと、最初の設計判断 ═══════════ */
{
  const s = base(false);
  head(s, 3, "収益モデルと、最初の設計判断", "1話の解放を「待つ／広告／課金」の3択にします。国内1位の BUMP と同じ形です");
  const rows=[
    hrow(["","収益ライン","型","開始","備考"]),
    [{text:"P1",options:{bold:true,color:VERM}},"企業案件の受注 → クリエイターへ配分","フロー・差益",{text:"初日から",options:{bold:true}},"単価48万・粗利率54%。実測前提が使える唯一のライン"],
    [{text:"P2",options:{bold:true,color:VERM}},"視聴課金の当社取り分","ストック",{text:"6ヶ月目〜",options:{bold:true}},"数話無料＋以降は都度課金。ReelShort・DramaBox と同型"],
    [{text:"P3",options:{bold:true,color:TEAL}},"広告収益（リワードで1話アンロック）","非連動",{text:"6ヶ月目〜",options:{bold:true}},"非課金層の収益化。実効eCPM ¥1,200。BUMPと同型"],
    [{text:"P4",options:{bold:true,color:GOLD}},"制作ツール・モデルの外販","ストック","3年目〜","粗利率80%以上。上場に必要な「読める収益」"],
  ];
  table(s, M, 1.58, W, rows, [0.7,3.9,1.5,1.3,4.63], 10, 0.44);
  card(s, M, 3.98, (W-0.3)/2, 2.4, "1話の解放は3択にします（BUMP型）",
    ["① 待つ　　　24時間で1話無料。収益はゼロだが、離脱を止める",
     "② 広告を見る　リワード広告1本で1話。1日3回まで。実効eCPM ¥1,200",
     "③ 課金する　　1話97円／コイン。ARPPU ¥3,000/月。ここが主力",
     "",
     "国内1位の BUMP（累計400万DL）が、すでにこの形で成立しています。"], TEAL, 10.5);
  card(s, M+(W-0.3)/2+0.3, 3.98, (W-0.3)/2, 2.4, "1MAUあたりの当社収益が +43%",
    ["課金のみの設計 ¥324/年 → BUMP型 ¥464/年。この上振れは計画に計上済みです（5期 売上33億→37億）。",
     "損益分岐となる「流量投放 ÷ 課金GMV」が 40% → 50% に上がります。",
     "リワード広告は、既にアプリにいる非課金層から取るため追加の獲得費用がゼロです。",
     "",
     "⚠ フィード型広告（RPM ¥20〜80＝1話 0.02〜0.08円）なら配信原価 0.225円/話 に負けます。",
     "　 リワード型（1話 0.60円＝原価の2.7倍）だから成立します。"], GOLD, 9.5);
  foot(s, "出所: BUMP公式（emole）／ Playio・Tenjin 2026年eCPMベンチマーク（日本のリワードeCPMは $17.35）。実効eCPM・課金率・カニバリ率は未実測です");
}

/* ═══════════ 9. 日本IPを使った作品制作 ═══════════ */
{
  const s = base(false);
  head(s, 3, "日本IPを使った作品制作 — 4つの入口", "版権コストの安い順に着手します。D から始め、課金収益が立ってから A へ");
  const rows=[
    hrow(["","対象IP","座組","版権コスト","出口"]),
    [{text:"D",options:{bold:true,color:TEAL}},"パブリックドメイン（青空文庫・古典）","権利処理が不要。単独で制作できる",{text:"ゼロ",options:{bold:true,color:TEAL}},"自社PFの初期コンテンツ・実績づくり"],
    [{text:"B",options:{bold:true,color:NAVY}},"自治体・企業のキャラクター","受託（②と同じ）。先方が権利者",{text:"ゼロ（先方負担）",options:{bold:true,color:NAVY}},"自治体PR・企業広報・ふるさと納税"],
    [{text:"C",options:{bold:true,color:GOLD}},"個人作家・Web小説（なろう系・pixiv）","作家と直接レベニューシェア。権利者が1人で交渉が速い",{text:"ほぼゼロ（成功報酬型）",options:{bold:true,color:GOLD}},"自社PFの課金コンテンツ"],
    [{text:"A",options:{bold:true,color:VERM}},"中小出版社の既刊マンガ（未映像化作品）","原作使用許諾＋レベニューシェア。制作費は当社負担",{text:"数万〜数十万／作品",options:{bold:true,color:VERM}},"自社PFの看板作品・海外展開"],
  ];
  table(s, M, 1.54, W, rows, [0.62,2.9,3.75,2.0,2.76], 9.5, 0.5);

  /* ▼ 図: 着手の階段 */
  const gx=M, gw=6.62, base_=6.38;
  s.addText("着手の順序 — 版権コストの安い順に積み上げる", { x:gx, y:4.16, w:gw, h:0.3,
    fontFace:F, fontSize:11, bold:true, color:INK, valign:"middle", margin:0, isTextBox:true });
  const steps=[["D","パブリックドメイン","版権ゼロ",0.72,TEAL],
               ["B","自治体・企業キャラ","先方負担",0.98,NAVY],
               ["C","個人作家・Web小説","成功報酬",1.34,GOLD],
               ["A","中小出版社マンガ","数万〜数十万",1.78,VERM]];
  steps.forEach((t,i)=>{
    const x=gx+i*1.68, w=1.58, h=t[3], y=base_-h;
    s.addShape(p.ShapeType.rect, { x, y, w, h, fill:{color:t[4]} });
    s.addText(t[0], { x, y:y+0.06, w, h:0.34, fontFace:F, fontSize:15, bold:true, color:PAPER,
      align:"center", valign:"middle", margin:0, isTextBox:true });
    s.addText(t[2], { x, y:base_-0.34, w, h:0.3, fontFace:F, fontSize:9, bold:true, color:PAPER,
      align:"center", valign:"middle", margin:0, isTextBox:true });
    s.addText(t[1], { x, y:base_+0.04, w, h:0.28, fontFace:F, fontSize:8.5, color:INKSOFT,
      align:"center", valign:"middle", margin:0, isTextBox:true });
    if(i<3) arw(s, "r", x+1.60, base_-h-0.24, 0.10, 0.20, MUTED);
  });
  s.addShape(p.ShapeType.line, { x:gx, y:base_, w:gw, h:0, line:{color:LINE, width:1} });

  warn(s, M+6.9, 4.16, W-6.9, 2.28, "IPホルダーはAI生成を警戒します",
    ["原作ファンの反発が、原作そのものの価値を毀損しかねません。",
     "契約に「AI利用の可否と開示方法」を必ず明記します。",
     "JIAA調査でも受容条件1位は「AI利用が明記されている」37.6%。開示を前提に設計します。",
     "",
     "⚠ D は版権コストがゼロなので、PF公開前から積み上げられます。ローンチ時に「見るものがある」状態をつくる唯一の方法です。"]);
  foot(s, "出所: 日本動画協会 アニメ産業レポート（制作市場4,662億円・海外売上2兆1,700億円）／ JIAA「2026年インターネット広告に関するユーザー意識調査」");
}

/* ═══════════ 10. 競合 ═══════════ */
{
  const s = base(false);
  head(s, 4, "競合 — クリエイター側の相手は TikTok ではありません", "快手・抖音・Bilibili・百度が、いまAIクリエイター獲得競争をしています");

  /* ▼ 図: 各社の分成率 */
  const bx=M, bw=6.6;
  s.addText("各社が提示している分成率", { x:bx, y:1.56, w:bw, h:0.3, fontFace:F, fontSize:11,
    bold:true, color:INK, valign:"middle", margin:0, isTextBox:true });
  const bars=[["快手「灵感新纪元」",0.90,"最大 90%",VERM],
              ["抖音「漫画星河」",0.90,"純収益の 90%",VERM],
              ["Bilibili「觉醒计划」",0.80,"最大 80%",VERM],
              ["抖音 AI実写短劇",0.60,"40〜60%",NAVY],
              ["抖音 AI漫劇",0.50,"30〜50%",NAVY]];
  bars.forEach((t,i)=>hbar(s, bx, 1.95+i*0.5, bw, 0.44, t[1], t[0], t[2], t[3], 2.35));
  s.addShape(p.ShapeType.line, { x:bx, y:4.52, w:bw, h:0, line:{color:LINE, width:1, dashType:"dash"} });
  s.addShape(p.ShapeType.rect, { x:bx, y:4.66, w:bw, h:0.52, fill:{color:SOFT} });
  s.addText("当社", { x:bx+0.16, y:4.66, w:2.2, h:0.52, fontFace:F, fontSize:10, bold:true,
    color:INK, valign:"middle", margin:0, isTextBox:true });
  s.addText("分成率では戦いません（右）", { x:bx+2.5, y:4.66, w:bw-2.66, h:0.52, fontFace:F,
    fontSize:10, bold:true, color:VERM, valign:"middle", margin:0, isTextBox:true });
  s.addText("トラフィック支援も桁が違います — 快手 1億／Bilibili 数百万／百度 10億級のトラフィックプール。\n抖音の上位作品は月10万〜50万元。",
    { x:bx, y:5.34, w:bw, h:0.7, fontFace:F, fontSize:9.5, color:MUTED,
      lineSpacingMultiple:1.3, valign:"top", margin:0, isTextBox:true });

  warn(s, M+6.9, 1.9, W-6.9, 1.94, "分成率では勝てません",
    ["トラフィックがゼロの新規PFが「うちに投稿してください」と言っても、経済合理性がありません。",
     "正面から分成率で殴り合う設計にはしません。"]);
  card(s, M+6.9, 4.02, W-6.9, 2.44, "ただし2026年、隙間が開きました",
    ["中国のPFは純AIコンテンツの分成を圧縮し、最低保証を廃止。",
     "リソースは実写短劇へ（有料実写は70%→80%に引き上げ）。",
     "AI専業のクリエイターは相対的に冷遇され始めています。",
     "",
     "ここが唯一の入口です。ただし方針が戻れば消える時限付きです。"], GOLD, 10.5);
  foot(s, "出所: Bilibili「2026熱門AI漫劇/短劇創作平台」／ 中伝英才「AI短劇制作平台 2026主流平台全解析」／ 网易「2026短劇分账新政」。条件は頻繁に変わるため、提携前に公式条件の確認が必要です");
}

/* ═══════════ 11. なぜクリエイターは当社に来るのか ═══════════ */
{
  const s = base(false);
  head(s, 4, "では、なぜクリエイターは当社に来るのか", "分成率ではなく、3つの別の理由で選ばれる設計にします");
  const w=(W-0.6)/3, y=1.6, h=1.9;
  const it=[["再生数ゼロでも","企業案件という別の収入","大手PFには無い。当社が受注して配分するので、視聴者がいなくても報酬が出ます",VERM],
            ["AIを冷遇しない","2026年の分成圧縮への受け皿","中国PFが下げた分成と廃止した最低保証。そこを埋めます",NAVY],
            ["日本市場への窓","個人では越えられない壁","日本語の要件定義・稟議・与信・請求。当社が代行します",GOLD]];
  it.forEach((t,i)=>{
    const x=M+(w+0.3)*i;
    s.addShape(p.ShapeType.rect, { x, y, w, h, fill:{color:SOFT} });
    s.addShape(p.ShapeType.rect, { x, y, w:0.05, h, fill:{color:t[3]} });
    s.addText(t[0], { x:x+0.3, y:y+0.2, w:w-0.56, h:0.32, fontFace:F, fontSize:11, bold:true, color:t[3], valign:"middle", margin:0, isTextBox:true });
    s.addText(t[1], { x:x+0.3, y:y+0.54, w:w-0.56, h:0.6, fontFace:F, fontSize:14, bold:true, color:INK, valign:"top", lineSpacingMultiple:1.16, margin:0, isTextBox:true });
    s.addText(t[2], { x:x+0.3, y:y+1.2, w:w-0.56, h:h-1.38, fontFace:F, fontSize:9.5, color:INKSOFT, valign:"top", lineSpacingMultiple:1.24, margin:0, isTextBox:true });
  });
  warn(s, M, 3.76, (W-0.3)/2, 2.4, "視聴者側の競合は、さらに厳しい",
    ["BUMP（DL400万・国内1位）／POPCORN（累計120億再生）／FANY:D／FOD SHORT／SWIPEDRAMA／UniReel など最低8サービス。",
     "中国発アプリが日本のアプリ市場シェア9割超。市場は1,530億円規模（2026年予測）で、民放キー局も参入を模索。"]);
  card(s, M+(W-0.3)/2+0.3, 3.76, (W-0.3)/2, 2.4, "だから、視聴者は「後から」取ります",
    ["初日はクリエイター側だけを取りに行きます。②の企業案件が、その口実と原資になります。",
     "視聴者獲得（流量投放）は6ヶ月目のPF公開以降に集中投下します。ここが最大の支出項目です（第10章）。"], NAVY, 10);
  foot(s, "出所: GOKKO ／ nowhere film ／ BUMP公式 ／ 36Kr Japan（中国発アプリの日本シェア）。詳細は COMPETITORS.md");
}

/* ═══════════ 12. 課題と解決 ═══════════ */
{
  const s = base(false);
  head(s, 5, "課題と、その解決方法", "最大の課題は両面市場のコールドスタート。②の企業案件が、この輪を回り始める前に断ちます");

  /* ▼ 図: コールドスタートの輪と、②による遮断 */
  s.addShape(p.ShapeType.rect, { x:M+3.15, y:1.52, w:2.55, h:0.6, fill:{color:VERM} });
  s.addText("② 企業案件で原資を入れる", { x:M+3.15, y:1.52, w:2.55, h:0.6, fontFace:F, fontSize:10.5,
    bold:true, color:PAPER, align:"center", valign:"middle", margin:0, isTextBox:true });
  arw(s, "d", M+4.31, 2.16, 0.24, 0.26, VERM);

  const loop=["視聴者がいない","分配の原資が出ない","クリエイターが去る","コンテンツが減る"];
  loop.forEach((t,i)=>{
    const x=M+i*3.15;
    s.addShape(p.ShapeType.rect, { x, y:2.48, w:2.55, h:0.78, fill:{color:i===1?"FBF1F1":SOFT} });
    if(i===1) s.addShape(p.ShapeType.rect, { x, y:2.48, w:0.05, h:0.78, fill:{color:VERM} });
    s.addText(t, { x:x+0.14, y:2.48, w:2.27, h:0.78, fontFace:F, fontSize:11.5, bold:true,
      color:i===1?VERM:INK, align:"center", valign:"middle", margin:0, isTextBox:true });
    if(i<3) arw(s, "r", x+2.67, 2.75, 0.36, 0.24, MUTED);
  });
  arw(s, "l", M+0.35, 3.42, 11.3, 0.3, LINE);
  s.addText("この輪が回り続けるのが、両面市場のコールドスタートです", { x:M+0.9, y:3.42, w:10.2, h:0.3,
    fontFace:F, fontSize:9.5, bold:true, color:INKSOFT, align:"center", valign:"middle", margin:0, isTextBox:true });
  s.addText("② は視聴者を必要としません。案件を配ればクリエイターは集まり、その作品が①の初期コンテンツになります。だから②を先に、①と並走させます。",
    { x:M, y:3.82, w:W, h:0.28, fontFace:F, fontSize:10, bold:true, color:VERM,
      align:"center", valign:"middle", margin:0, isTextBox:true });

  const rows=[
    hrow(["残りの課題","解決方法"]),
    [{text:"分成率で大手に勝てない",options:{bold:true,color:INK}},"分成率では戦わない。企業案件・AIを冷遇しない方針・日本市場への窓の3点で選ばれる設計にする"],
    [{text:"視聴者獲得が最大の支出",options:{bold:true,color:INK}},"PF公開（6ヶ月目）まで投下しない。公開後に集中投下し、CPIを実測してから増減させる"],
    [{text:"中国本土から当社PFに接続できない可能性",options:{bold:true,color:INK}},"投稿・決済の経路を設計段階で検証。国内向けミラーまたは提携PF経由の投稿導線を用意する"],
    [{text:"「AIっぽさ」が視聴維持率を下げる",options:{bold:true,color:INK}},"審査基準に組み込み、品質判定の自動化を特許①として出願。視聴維持率データを学習側に回す"],
  ];
  table(s, M, 4.28, W, rows, [4.3,7.73], 10.5, 0.5);
  foot(s, "各課題の詳細と数値根拠は PLATFORM_PIVOT ／ COMPETITORS ／ MOAT_TIMELINE ／ CHINA_SOURCING に記載");
}

/* ═══════════ 13. チーム ═══════════ */
{
  const s = base(false);
  head(s, 6, "チーム", "（記入予定）");
  const w=(W-0.6)/3, y=1.7, h=2.3;
  [["代表取締役","経歴 ／ 実績"],["CTO／開発責任者","採用計画"],["クリエイター獲得責任者","採用計画"]].forEach((t,i)=>{
    const x=M+(w+0.3)*i;
    s.addShape(p.ShapeType.rect, { x, y, w, h, fill:{color:PAPER}, line:{color:LINE, width:1, dashType:"dash"} });
    s.addText(t[0], { x:x+0.3, y:y+0.32, w:w-0.6, h:0.4, fontFace:F, fontSize:14, bold:true, color:INK, valign:"middle", margin:0, isTextBox:true });
    s.addText(t[1], { x:x+0.3, y:y+0.78, w:w-0.6, h:0.4, fontFace:F, fontSize:10.5, color:MUTED, valign:"middle", margin:0, isTextBox:true });
  });
  card(s, M, 4.3, W, 2.1, "この章は記入予定です",
    ["代表の経歴と実績 ／ これから採用する職種・時期・採用チャネル ／ アドバイザー・顧問",
     "",
     "プラットフォーム事業への転換により、1年目からエンジニアが必要になりました。",
     "1年目は6名体制（代表・エンジニア2・運営2・営業1）を想定しています。"], MUTED, 11);
  foot(s);
}

/* ═══════════ 14. 事業計画（チャート） ═══════════ */
{
  const s = base(false);
  head(s, 7, "事業計画", "プラットフォーム型のため3年目まで赤字が前提。単月黒字化は4年目、上場申請は5期です");
  const labels=["1期 2027/9","2期 2028/9","3期 2029/9","4期 2030/9","5期 2031/9"];
  s.addChart(p.ChartType.bar, [
    { name:"売上高", labels, values:[30,190,530,1670,3700] },
    { name:"営業利益", labels, values:[-113,-134,-54,250,900] },
  ], {
    x:M, y:1.6, w:6.6, h:3.3,
    barDir:"col", barGrouping:"clustered",
    chartColors:[NAVY, VERM],
    catAxisLabelFontFace:F, catAxisLabelFontSize:9, catAxisLabelColor:MUTED,
    valAxisLabelFontFace:F, valAxisLabelFontSize:9, valAxisLabelColor:MUTED,
    valAxisMinVal:-200, valAxisMaxVal:3800,
    showValue:true, dataLabelFontFace:F, dataLabelFontSize:8, dataLabelColor:INKSOFT,
    showLegend:true, legendPos:"b", legendFontFace:F, legendFontSize:9,
    valGridLine:{ color:LINE, style:"solid", size:0.5 }, catGridLine:{ style:"none" },
    title:"売上高と営業利益の推移（単位 百万円・計画値）", showTitle:true,
    titleFontFace:F, titleFontSize:11, titleColor:INK,
  });
  const cx=M+6.9, cw=W-6.9;
  card(s, cx, 1.6, cw, 1.02, "1期 ― 基盤をつくる",
    ["PF開発と公開（6ヶ月目）。企業案件で2,700万、課金で300万。営業利益 ▲1.1億は計画通りの投資です。"], VERM, 9.5);
  card(s, cx, 2.74, cw, 0.9, "2〜3期 ― 投資期間",
    ["視聴者獲得に集中投下。赤字は2期に最大化し、3期から縮小に転じます。"], NAVY, 9.5);
  card(s, cx, 3.76, cw, 1.14, "4〜5期 ― 回収",
    ["4期に単月黒字化、5期に年商37億・営業利益9億。時価総額140億の水準へ。"], GOLD, 9.5);
  const rows=[
    hrow(["","この期にやること","この期の到達点"]),
    ["1期","PF公開・登録100名","企業案件 月300万"],
    ["2期","MAU・課金率の実測","監査法人ショートレビュー"],
    ["3期（N-2期）","監査開始","赤字が縮小に転じる"],
    ["4期（N-1期）","単月黒字化","内部管理体制の構築"],
    [{text:"5期（N期）→ 2031年 上場",options:{bold:true,color:VERM}},{text:"年商37億・営業利益9億",options:{bold:true}},{text:"想定時価総額140億円",options:{bold:true}}],
  ];
  table(s, M, 5.06, W, rows, [3.0,4.5,4.53], 10, 0.3);
  foot(s, "計画値。P2（課金）の課金率・ARPPU は未実測です。1期に実測して差し替えます。プラットフォーム型のため赤字期間が長く、追加調達を前提としています（第10章）");
}

/* ═══════════ 15. 上場までの流れ ═══════════ */
{
  const s = base(false);
  head(s, 8, "上場までの流れ", "5期（2031年）での上場を逆算。N-2期の監査開始は3期・2028年10月です");
  const w=(W-1.2)/5, y=1.62, h=1.9;
  const ph=[["1期","2026/10-2027/9",["PF開発・公開","クリエイター100名","企業案件の立ち上げ"],VERM],
            ["2期","2027/10-2028/9",["視聴者獲得に集中","課金率の実測","監査法人SR"],VERM],
            ["3期 N-2","2028/10-2029/9",["監査開始","赤字が縮小へ","主幹事証券の選定"],NAVY],
            ["4期 N-1","2029/10-2030/9",["単月黒字化","内部管理体制の構築","資本政策の確定"],NAVY],
            ["5期 N期","2030/10-2031/9",["上場申請","2031年・東証グロース",""],GOLD]];
  ph.forEach((t,i)=>{
    const x=M+(w+0.3)*i;
    s.addShape(p.ShapeType.rect, { x, y, w, h, fill:{color:SOFT} });
    s.addShape(p.ShapeType.rect, { x, y, w, h:0.06, fill:{color:t[3]} });
    s.addText(t[0], { x:x+0.24, y:y+0.2, w:w-0.48, h:0.32, fontFace:F, fontSize:14, bold:true, color:t[3], valign:"middle", margin:0, isTextBox:true });
    s.addText(t[1], { x:x+0.24, y:y+0.54, w:w-0.48, h:0.28, fontFace:F, fontSize:9, color:MUTED, valign:"middle", margin:0, isTextBox:true });
    s.addText(t[2].filter(Boolean).map((l,k,a)=>({text:"・"+l, options:{breakLine:k<a.length-1}})),
      { x:x+0.24, y:y+0.9, w:w-0.48, h:h-1.06, fontFace:F, fontSize:9.5, color:INKSOFT, lineSpacingMultiple:1.26, valign:"top", margin:0, isTextBox:true });
  });
  card(s, M, 3.76, (W-0.3)/2, 1.62, "資本政策の想定",
    ["シード1.5億（今回）→ ESOP枠10% → シリーズA 3億（2期）→ シリーズB 8億（4期）",
     "IPO公募20%を経て、上場時の創業者持分は 35%前後 を想定。",
     "1ラウンドで33%超は放出しません（特別決議の拒否権を渡さないため）。"], NAVY, 10);
  warn(s, M+(W-0.3)/2+0.3, 3.76, (W-0.3)/2, 1.62, "5年で上場するための条件",
    ["2期目（2028年）に監査法人のショートレビューを受ける必要があります。",
     "赤字が最大化する期に監査法人を確保できるかが最初の関門です。"]);
  s.addShape(p.ShapeType.rect, { x:M, y:5.56, w:W, h:0.92, fill:{color:ORANGE} });
  s.addText([{text:"⚠ ゴールは上場ではありません。", options:{bold:true, color:PAPER, breakLine:true}},
             {text:"グロースは2030年3月以降「上場5年経過後に時価総額100億円」の維持基準が新設。2031年上場なら2036年に100億円。", options:{color:ONORG}}],
    { x:M+0.34, y:5.62, w:W-0.68, h:0.8, fontFace:F, fontSize:11, lineSpacingMultiple:1.28, valign:"middle", margin:0, isTextBox:true });
  foot(s, "出所: 日本取引所グループ 上場維持基準。上場基準は改定が続くため、準備期に入る前に最新基準を再確認します");
}

/* ═══════════ 16. 出口とリターン ═══════════ */
{
  const s = base(false);
  head(s, 8, "出口とリターン", "5期の売上37億・営業利益9億を前提に、3手法で試算しています");
  const w=(W-0.6)/3, y=1.6, h=1.46;
  stat(s, M,           y, w, h, "121〜241億", "PER法", "当期純利益 約6.0億（実効税率33%）× PER 20〜40倍", VERM, 24);
  stat(s, M+w+0.3,     y, w, h, "74〜185億", "PSR法", "売上37億 × PSR 2〜5倍。プラットフォーム型はこちらで見られやすい", NAVY, 24);
  stat(s, M+(w+0.3)*2, y, w, h, "93〜158億", "EV/EBITDA法", "EBITDA 約10.5億 × 8.9〜15倍（情報通信業の中央値8.9倍）", GOLD, 24);
  s.addShape(p.ShapeType.rect, { x:M, y:3.24, w:W, h:0.58, fill:{color:ORANGE} });
  s.addText("中心値は 時価総額 140億円 ─ グロースの上場維持基準（上場5年経過後に100億円以上）に対し 40% のバッファ",
    { x:M+0.34, y:3.24, w:W-0.68, h:0.58, fontFace:F, fontSize:12.5, bold:true, color:PAPER, valign:"middle", margin:0, isTextBox:true });
  card(s, M, 3.98, (W-0.3)/2, 1.62, "M&A で売却する場合",
    ["3期（売上5.3億・赤字）… 10〜30億。買い手が評価するのはクリエイターネットワークと技術。",
     "4期（売上16.7億・営業利益2.5億）… 35〜70億 ／ 5期（売上37億）… 93〜158億。",
     "戦略的買い手（中国PF・テレビ局・大手代理店）ならシナジー価格が乗ります。"], NAVY, 10);
  card(s, M+(W-0.3)/2+0.3, 3.98, (W-0.3)/2, 1.62, "創業者・投資家のリターン",
    ["上場時の創業者持分は 35%前後 を想定（CAP_TABLE.md）。時価総額140億なら評価額 約51億。",
     "⚠ IPOは上場直後に全株を売れません。ロックアップ（通常90〜180日）があり、現金化は数年かけて段階的になります。M&Aは一括で現金化できる点が違います。"], GOLD, 10);
  warn(s, M, 5.74, W, 0.92, "すべて「成功した場合」の試算です",
    ["プラットフォーム型は勝者総取りになりやすく、2位以下の評価は急落します。2025年のグロースIPOは18社（前年34社から半減）で、IPO市場そのものが縮んでいます。"]);
  foot(s, "出所: M&A総研（業種別EV/EBITDA倍率）／ みつきコンサルティング（メディア・コンテンツ業界のM&A）／ EY Japan（2026年以降のIPO市場）／ FiNX（グロース維持基準の制度化）。倍率は市況で変動します");
}

/* ═══════════ 17. マイルストーン ═══════════ */
{
  const s = base(false);
  head(s, 9, "マイルストーン", "各フェーズは「ゲート条件」で区切ります。満たさない限り、次へは進みません");

  /* ▼ 図: ゲート付きフェーズ帯 */
  const ph=["〜2026/12","2027/1-3","2027/4-9","2期","3期","4期","5期"];
  ph.forEach((t,i)=>{
    const on = i===2 || i===6;
    s.addShape(p.ShapeType.chevron, { x:M+i*1.70, y:1.54, w:1.82, h:0.66,
      fill:{color: i===6 ? VERM : (on ? "F0DCC9" : SOFT)} });
    s.addText(t, { x:M+i*1.70+0.18, y:1.54, w:1.5, h:0.66, fontFace:F, fontSize:10,
      bold:true, color: i===6 ? PAPER : INK, align:"center", valign:"middle", margin:0, isTextBox:true });
  });
  s.addText("◆ 各フェーズの間にゲートがあります", { x:M, y:2.26, w:W, h:0.26, fontFace:F,
    fontSize:9, color:MUTED, valign:"middle", margin:0, isTextBox:true });

  const rows=[
    hrow(["時期","やること","◆ 次へ進むゲート条件"]),
    ["〜2026/12","法人設立・PF要件定義・クリエイター20名と先行契約","クリエイター20名の登録／PF仕様の確定"],
    ["2027/1-3","PF開発（アプリ・Web・課金・分配）／企業案件の受注開始",{text:"企業案件 累計5本／粗利率55%以上",options:{bold:true}}],
    [{text:"2027/4-9",options:{bold:true,color:VERM}},{text:"PF公開（6ヶ月目）・視聴者獲得の開始・D案IPの投入",options:{bold:true}},{text:"登録100名／公開作品500本／課金率の初回実測",options:{bold:true,color:VERM}}],
    ["2期","視聴者獲得に集中投下・課金モデルの最適化","MAUとCPIの実測／監査法人ショートレビュー"],
    ["3期","赤字の縮小・プロダクト（P4）の開発着手","監査開始／赤字が縮小に転じる"],
    ["4期","単月黒字化・内部管理体制の構築","単月黒字化／プロダクト比率10%以上"],
    [{text:"5期",options:{bold:true,color:VERM}},{text:"上場申請",options:{bold:true}},{text:"年商37億・営業利益9億／時価総額140億",options:{bold:true}}],
  ];
  table(s, M, 2.62, W, rows, [1.6,5.4,5.03], 10.5, 0.5);
  foot(s, "ゲート条件を満たさない場合は次フェーズに進まず、前提を引き直します。とくに「課金率の初回実測」（2027/4-9）は、以降のすべての売上計画が乗る数字です");
}

/* ═══════════ 18. 資金計画 ═══════════ */
{
  const s = base(false);
  head(s, 10, "資金計画", "調達目標 1.5億円。融資を使わず、全額をエクイティで調達します");
  s.addText("1年目の使途（単位 万円・合計 14,280万）", { x:M, y:1.54, w:6.4, h:0.3, fontFace:F, fontSize:11, bold:true, color:INK, valign:"middle", margin:0, isTextBox:true });
  const uses=[["視聴者獲得（流量投放）",4800,VERM],["PF開発（アプリ・Web・課金）",3500,NAVY],["人件費（6名）",3000,NAVY],
              ["分配原資の補填",1500,VERM],["オフィス・SaaS・その他",480,MUTED],["設立・機材・その他初期",400,MUTED],
              ["法務（資金決済法・規約・UGC対応）",300,MUTED],["インフラ（配信・ストレージ）",300,MUTED]];
  const maxv=4800, bx=M, bw=6.4;
  uses.forEach((u,i)=>{
    const y=1.94+i*0.55;
    s.addText(u[0], { x:bx, y, w:3.1, h:0.3, fontFace:F, fontSize:10, color:INKSOFT, valign:"middle", margin:0, isTextBox:true });
    const bl=(u[1]/maxv)*2.5;
    s.addShape(p.ShapeType.rect, { x:bx+3.15, y:y+0.06, w:bl, h:0.19, fill:{color:u[2]} });
    s.addText(String(u[1]), { x:bx+5.72, y, w:0.68, h:0.3, fontFace:F, fontSize:10, bold:true, color:INK, align:"right", valign:"middle", margin:0, isTextBox:true });
  });
  const cx=M+6.9, cw=W-6.9;
  stat(s, cx, 1.9, (cw-0.3)/2, 1.56, "800万", "資本金（創業者出資）", "1,000万未満に抑え、初年度の消費税課税事業者化を回避", NAVY, 24);
  stat(s, cx+(cw-0.3)/2+0.3, 1.9, (cw-0.3)/2, 1.56, "1.42億", "シード（創業時）", "放出20〜27%を想定。J-KISSでの価格先送りも選択肢", GOLD, 24);
  warn(s, cx, 3.66, cw, 1.86, "追加調達を前提にしています",
    ["1.5億は1年目を賄う額です。2期は視聴者獲得が通年になるため、支出は1年目を上回ります。",
     "2期にシリーズA 3億、4期にシリーズB 8億。累計調達は12.5億規模です。",
     "プラットフォーム型は数年の赤字が構造的な前提であり、それを織り込んだ資本政策にしています。"]);
  card(s, cx, 5.66, cw, 1.0, "補助金は資金繰りに算入していません",
    ["後払い（精算払い）で入金が1年以上先のためです。"], MUTED, 10);
  s.addText("※ 融資は使いません。全額をエクイティで調達します。", { x:M, y:6.2, w:6.4, h:0.3,
    fontFace:F, fontSize:10, bold:true, color:VERM, valign:"middle", margin:0, isTextBox:true });
  foot(s, "［仮置き］視聴者獲得のCPIが未実測のため、最大費目である流量投放4,800万の精度が最も低い数字です。PF公開後に実測して増減させます。");
}

/* ═══════════ 19. リスクと対策 ═══════════ */
{
  const s = base(false);
  head(s, 11, "リスクと対策", "影響度と発生確率で並べています。右上の2つが、この事業の生死を分けます");

  /* ▼ 図: リスクマップ */
  s.addText("リスクマップ（影響度 × 発生確率）", { x:M, y:1.54, w:5.4, h:0.3, fontFace:F,
    fontSize:11, bold:true, color:INK, valign:"middle", margin:0, isTextBox:true });
  const px=1.45, py=1.98, qw=2.25, qh=1.75;
  [[0,0,SOFT],[1,0,"F8E6E6"],[0,1,SOFT],[1,1,SOFT]].forEach(q=>{
    s.addShape(p.ShapeType.rect, { x:px+q[0]*qw, y:py+q[1]*qh, w:qw, h:qh, fill:{color:q[2]},
      line:{color:PAPER, width:1.5} });
  });
  s.addText("最優先", { x:px+qw+1.32, y:py+0.06, w:0.85, h:0.26, fontFace:F, fontSize:9,
    bold:true, color:VERM, align:"right", valign:"middle", margin:0, isTextBox:true });
  s.addText("↑ 影響度", { x:M, y:2.02, w:0.76, h:0.3, fontFace:F, fontSize:8.5, color:MUTED,
    valign:"middle", margin:0, isTextBox:true });
  s.addText("発生確率 →", { x:px, y:5.54, w:2.0, h:0.28, fontFace:F, fontSize:8.5, color:MUTED,
    valign:"middle", margin:0, isTextBox:true });
  [[1,4.85,2.30,VERM],[2,5.30,2.72,VERM],[3,4.05,2.44,VERM],
   [4,3.92,3.08,VERM],[5,5.10,4.02,MUTED],[6,3.02,4.24,MUTED]].forEach(d=>{
    dot(s, d[1], d[2], 0.36, String(d[0]), d[3]);
  });

  const H={text:"高",options:{bold:true,color:PAPER,fill:{color:VERM},align:"center"}};
  const Mm={text:"中",options:{bold:true,color:PAPER,fill:{color:MUTED},align:"center"}};
  const rows=[
    hrow(["#","","リスク","対策"]),
    [{text:"1",options:{bold:true,color:VERM,align:"center"}},H,{text:"視聴者が集まらない",options:{bold:true}},"PF公開まで流量投放を投下しない。公開後にCPIを実測し、閾値を超えたら企業案件（②）に軸足を戻す"],
    [{text:"2",options:{bold:true,color:VERM,align:"center"}},H,{text:"クリエイターが集まらない",options:{bold:true}},"分成率で戦わない。企業案件・AIを冷遇しない方針・日本市場への窓の3点で選ばれる設計にする"],
    [{text:"3",options:{bold:true,color:VERM,align:"center"}},H,{text:"中国PFが分成圧縮を撤回する",options:{bold:true}},"四半期ごとに各PFの分成条件を追跡。撤回の兆候が出たら獲得を前倒しする"],
    [{text:"4",options:{bold:true,color:VERM,align:"center"}},H,{text:"追加調達が続かない",options:{bold:true}},"企業案件（②）を単独で黒字化できる水準まで育て、最悪ケースでも事業が止まらない構造にする"],
    [{text:"5",options:{bold:true,color:MUTED,align:"center"}},Mm,{text:"資金決済法・UGC対応の義務",options:{bold:true}},"PF設計の前に弁護士へ確認。法務費用300万を初年度に計上済み"],
    [{text:"6",options:{bold:true,color:MUTED,align:"center"}},Mm,{text:"中国本土から当社PFに接続できない",options:{bold:true}},"設計段階で検証。国内向けミラーまたは提携PF経由の投稿導線を用意"],
  ];
  table(s, M+5.95, 1.9, W-5.95, rows, [0.38,0.44,2.15,3.11], 9, 0.66);
  foot(s, "全リスクと対策は PLATFORM_PIVOT ／ COMPETITORS ／ MOAT_TIMELINE ／ CHINA_SOURCING に記載しています");
}

/* ═══════════ 20. クロージング ═══════════ */
{
  const s = base(true);
  s.addShape(p.ShapeType.rect, { x:M, y:1.9, w:0.62, h:0.62, fill:{color:PAPER} });
  s.addText("行き場を失ったクリエイターに、稼ぐ場所を。", { x:M, y:2.8, w:11.9, h:1.0, fontFace:F, fontSize:38, bold:true, color:PAPER, valign:"middle", margin:0, isTextBox:true });
  s.addText("中国の大手がAIを冷遇し始めた今が、受け皿をつくる唯一の窓です。",
    { x:M, y:3.86, w:11.9, h:0.5, fontFace:F, fontSize:15, color:ONORG, valign:"middle", margin:0, isTextBox:true });
  const w=(W-0.6)/3, y=4.9;
  [["1.5億円","今回の調達目標",PAPER],["3年","この窓が開いている期間",PAPER],["2031年","東証グロース上場",PAPER]].forEach((t,i)=>{
    const x=M+(w+0.3)*i;
    s.addShape(p.ShapeType.rect, { x, y, w:0.05, h:1.0, fill:{color:t[2]} });
    s.addText(t[0], { x:x+0.26, y:y+0.02, w:w-0.4, h:0.58, fontFace:F, fontSize:26, bold:true, color:t[2], valign:"middle", margin:0, isTextBox:true });
    s.addText(t[1], { x:x+0.26, y:y+0.6, w:w-0.4, h:0.34, fontFace:F, fontSize:11, color:ONORG, valign:"middle", margin:0, isTextBox:true });
  });
}

p.writeFile({ fileName: "deck.pptx" }).then(()=>console.log("written: deck.pptx"));
