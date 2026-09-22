const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE";               // 13.333 x 7.5
p.author = "AI映像制作事業";
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
  s.addText("AI映像制作", { x:M, y:2.95, w:11.9, h:0.95, fontFace:F, fontSize:42, bold:true,
    color:PAPER, valign:"middle", margin:0, isTextBox:true });
  s.addText("日本で受注し、中国のAIクリエイターで作る。溜まった制作データを、模倣されない資産に変える。",
    { x:M, y:3.98, w:11.9, h:0.5, fontFace:F, fontSize:16, color:ONDARK, valign:"middle", margin:0, isTextBox:true });
  s.addText("投資家向け企画書  ／  2026年9月", { x:M, y:5.6, w:7, h:0.36, fontFace:F, fontSize:12, color:ONORG, valign:"middle", margin:0, isTextBox:true });
  s.addText("新設法人（株式会社・仮称）", { x:M, y:5.96, w:7, h:0.36, fontFace:F, fontSize:12, color:ONORG, valign:"middle", margin:0, isTextBox:true });
}

/* ═══════════ 2. エグゼクティブサマリー ═══════════ */
{
  const s = base(false);
  head(s, 0, "エグゼクティブサマリー", "映像制作でキャッシュと顧客とデータを作り、人手に比例しない収益へ移します");
  lede(s, 1.50, ["5年後・2031年、東証グロース市場への上場を目指す。",
    "日本企業から映像制作を受注し、中国を中心とする登録クリエイターで作る。制作データを特許とモデルに変える。"]);
  const y0=2.56, h=1.52, w=(W-0.6)/3;
  stat(s, M,           y0, w, h, "4,580億円", "国内の映像制作市場（実測）", "矢野経済研究所。2027年度は5,400億円の予測", VERM);
  stat(s, M+w+0.3,     y0, w, h, "3本立て",   "収益の柱", "① 映像制作（初日から）② 自社PFの課金・広告（6ヶ月目〜）③ ツール外販（3期〜）", NAVY);
  stat(s, M+(w+0.3)*2, y0, w, h, "1.5億円",   "今回の調達目標", "追加はシリーズA 3億のみ。累計4.5億で上場まで届く設計", GOLD);
  const y1=4.26, h2=2.28, w2=(W-0.6)/3;
  card(s, M,            y1, w2, h2, "何をするか",
    ["① 日本企業から映像制作を受注し、中国を中心とする登録クリエイターに配分する。",
     "② 制作した作品と日本IPを、自社プラットフォームに載せて課金・広告で回収する。",
     "③ 溜まった制作データで生成AI関連の特許を取得し、ツール・モデルを外販する。"]);
  card(s, M+w2+0.3,     y1, w2, h2, "なぜ勝てるか",
    ["生成AIで制作原価は下がったが、日本企業の発注価格は下がっていない。この差が粗利。",
     "日本企業は中華圏に直接発注できない。言語・商習慣・品質保証・契約が壁。",
     "その壁を引き受けることが商品。差別化は価格ではなく「発注側の管理コストをゼロにする」こと。"], NAVY);
  card(s, M+(w2+0.3)*2, y1, w2, h2, "どこへ向かうか",
    ["1〜3年目は投資期間。4年目に通期黒字化、5年目に年商18億・営業利益3.8億。",
     "売上の44%を「人手に比例しない収益」にする。ここが上場審査で効く。",
     "自動車産業が輸入技術を4年で国産化したのと同じ道筋を、3年で。"], GOLD);
  foot(s, "収支は［仮置き］を含む計画値です。国内市場規模は矢野経済研究所の実測値。制作の単価・粗利率は業界相場からの設定で、1期に実測して差し替えます。");
}

/* ═══════════ 3. なぜ今なのか ═══════════ */
{
  const s = base(false);
  head(s, 1, "なぜ今なのか", "中国で制作力が余り、日本ではまだAIが現場に入っていない。この差が開いているのは数年です");
  const y0=1.58, w=(W-0.9)/4, h=1.62;
  card(s, M,             y0, w, h, "1  日本は出遅れている",
    ["政府がAI推進法を制定し、AI基本計画を閣議決定するほどの危機感。","映像制作の現場にAIはまだ入っていない。"], VERM, 9.5);
  card(s, M+w+0.3,       y0, w, h, "2  中国では淘汰が始まった",
    ["AI映像の制作会社は2026年Q1に 1,216社→698社（−42%）。","約90%が赤字。最大コストは制作費ではなく広告出稿で約70%。"], VERM, 9.5);
  card(s, M+(w+0.3)*2,   y0, w, h, "3  制作力が余っている",
    ["中国PFは純AIコンテンツの分成を圧縮し、最低保証を廃止。","足りないのは「作る力」ではなく「売る力」。"], NAVY, 9.5);
  card(s, M+(w+0.3)*3,   y0, w, h, "4  当社が売る力になる",
    ["日本の発注を取り、要件定義・品質保証・契約・請求を引き受ける。","彼らは作るだけでよくなる。"], GOLD, 9.5);
  s.addText("中国のAI映像制作会社数", { x:M, y:3.44, w:5.6, h:0.3, fontFace:F, fontSize:11, bold:true, color:INK, margin:0, isTextBox:true });
  box(s, M,      3.80, 1.9, 1.0, "2025年 Q4", "1,216社", SOFT, MUTED, INK, 10, 17);
  arw(s, "r", M+2.02, 4.12, 0.5, 0.36);
  box(s, M+2.66, 3.80, 1.9, 1.0, "2026年 Q1", "698社", SOFT, MUTED, VERM, 10, 17);
  s.addText("1四半期で −42%", { x:M+4.72, y:4.06, w:1.6, h:0.48, fontFace:F, fontSize:13, bold:true, color:VERM, valign:"middle", margin:0, isTextBox:true });
  warn(s, M+6.5, 3.44, W-6.5, 1.36, "ただし、これは「安く買い叩ける」という話ではありません",
    ["淘汰されているのは、広告出稿で視聴者を取りに行った会社です。作る力そのものは市場に残っています。",
     "当社が取るのは制作力であって、彼らが負けた土俵（視聴者獲得の消耗戦）には乗りません。"]);
  const rows=[
    hrow(["","中国のAI制作会社","当社"]),
    ["収益の取り方","自社作品を投稿し、再生数で分成を取る","日本企業から受注して納品する"],
    ["最大コスト","広告出稿（全体の約70%）","制作原価（売上の40%）"],
    ["負ける理由","広告費を先に張れる側が勝つ消耗戦","―（この土俵に乗らない）"],
  ];
  table(s, M, 4.96, W, rows, [2.4,4.8,4.83], 10, 0.34);
  foot(s, "出所: 内閣府 AI戦略 ／ 第一財経・搜狐（中国AI短劇の淘汰）／ 网易「2026短劇分账新政」／ 経済産業省");
}

/* ═══════════ 4. 日本は一度、これをやっている ═══════════ */
{
  const s = base(false);
  head(s, 1, "日本は一度、これをやっている", "輸入した技術を4年で国産化し、その後20年以上の改善で世界一の品質に到達した");
  const y0=1.62, w=(W-0.9)/4, h=1.30;
  card(s, M,           y0, w, h, "1952", ["日産＝オースチン技術提携","日野＝ルノー、いすゞ＝ルーツ"], MUTED, 9.5);
  card(s, M+w+0.3,     y0, w, h, "1956-57", ["4社が相次いで完全国産化","ここまで4年"], VERM, 9.5);
  card(s, M+(w+0.3)*2, y0, w, h, "1960s-70s", ["QCサークル・トヨタ生産方式","改善を20年以上回し続ける"], NAVY, 9.5);
  card(s, M+(w+0.3)*3, y0, w, h, "1980s", ["品質と燃費で世界市場を取る","米国メーカーが学びに来る側へ"], GOLD, 9.5);
  const rows=[
    hrow(["","持っている側","","修得する側","期間","到達点"]),
    ["1952 → 1956","オースチン（英）","技術 →","日産・日野・いすゞ","4年","完全国産化。ただしこれは入口"],
    [{text:"2026 → 2029",options:{bold:true,color:VERM}},"世界のAIクリエイター","制作力 →",{text:"当社",options:{bold:true}},{text:"3年",options:{bold:true}},{text:"内製化。ここから改善を回す",options:{bold:true}}],
  ];
  table(s, M, 3.22, W, rows, [1.8,2.9,1.0,2.9,0.8,2.63], 9.5, 0.40);
  warn(s, M, 4.62, W, 1.16, "ポイントは国産化の速さではありません。その後の改善で世界一の品質を築いたことです",
    ["日産・トヨタは国産化をゴールにせず、以後20年以上かけて生産方式と品質管理を磨き続けました。",
     "当社も同じです。内製化（3年）は出発点で、制作データで改善を回し続けることが模倣されない資産になります。"]);
  s.addText("⚠ 当時は政府の保護（輸入制限・関税）がありました。今のAI映像にはありません。だから改善のサイクルをより速く回す必要があります。",
    { x:M, y:5.94, w:W, h:0.34, fontFace:F, fontSize:10, bold:true, color:VERM, valign:"middle", margin:0, isTextBox:true });
  foot(s, "出所: 日産自動車 企業情報 ／ トヨタ博物館 ／ GAZOO「ノックダウン生産の時代」／ 日本科学技術連盟（QCサークル・デミング賞）");
}

/* ═══════════ 5. 政策も同じ方向を向いている ═══════════ */
{
  const s = base(false);
  head(s, 1, "政策も同じ方向を向いている", "国はコンテンツを輸出産業にすると決め、予算を3倍にした");
  const y0=1.62, h=1.52, w=(W-0.6)/3;
  stat(s, M,           y0, w, h, "20兆円", "コンテンツ海外売上 目標（2033年）", "経産省「エンタメ・クリエイティブ産業戦略2026」");
  stat(s, M+w+0.3,     y0, w, h, "3.5倍",  "経産省の財政支援規模", "令和6年度補正 101.1億円 → 令和7年度補正 350.2億円", NAVY);
  stat(s, M+(w+0.3)*2, y0, w, h, "+26%",   "アニメの海外売上（2024年）", "2兆1,700億円。市場全体は3兆8,400億円", GOLD);
  const y1=3.32, w2=(W-0.3)/2;
  card(s, M, y1, w2, 1.62, "AI政策",
    ["AI推進法（人工知能関連技術の研究開発及び活用の推進に関する法律）","2025年5月28日成立 ／ 6月4日公布。日本初のAI基本法。",
     "AI基本計画を2025年12月23日に閣議決定。内閣にAI戦略本部を設置。"], NAVY, 9.5);
  card(s, M+w2+0.3, y1, w2, 1.62, "当社が実際に狙える支援",
    ["東京都 創業助成事業 — 上限400万円・助成率2/3・最長2年","特許料等の減免 — 設立10年未満・資本金3億円以下なら1/3に軽減",
     "JLOX+ — 「制作の生産性向上に資するシステムの開発・実証」枠"], GOLD, 9.5);
  warn(s, M, 5.14, W, 1.10, "補助金は資金計画に算入していません",
    ["いずれも後払い（精算払い）で、入金が1年以上先になります。資金繰りの当てにはできません。",
     "取れた場合は上振れとして扱います。"]);
  foot(s, "出所: 経済産業省「エンタメ・クリエイティブ産業戦略2026」／ 内閣府 AI戦略 ／ 東京都中小企業振興公社 ／ 特許庁");
}

/* ═══════════ 6. 市場規模 ═══════════ */
{
  const s = base(false);
  head(s, 2, "市場規模", "本丸は国内の映像制作市場です。ここは推計ではなく実測値があります");
  const y0=1.58, h=1.52, w=(W-0.6)/3;
  stat(s, M,           y0, w, h, "4,580億円", "国内 動画制作サービス市場（2025年度予測）", "2024年度 4,238億円 → 2027年度 5,400億円【実測・矢野経済研究所】", VERM);
  stat(s, M+w+0.3,     y0, w, h, "1兆437億円", "国内 動画広告市場（2026年）", "2025年 8,855億円から拡大。縦型動画広告は前年比155.9%【実測】", NAVY);
  stat(s, M+(w+0.3)*2, y0, w, h, "1,530億円",  "日本のショートドラマ市場（2026年予測）", "自社PFが面する市場。中国発アプリがシェア9割超", GOLD);
  const rows=[
    hrow(["","当社が取りに行く帯","AI導入後の制作費","当社の受注単価","なぜここか"]),
    [{text:"★ 企業VP・会社紹介",options:{bold:true}},"現状 50〜150万円","18〜52万円","40〜80万","フル生成AIが成立する。撮影が消えて原価が半分以下になる"],
    [{text:"★ 展示会・イベント映像",options:{bold:true}},"現状 20〜100万円","6〜30万円","30〜60万","ループ素材は特に効く。閑散期を埋める"],
    [{text:"★ PR素材・SNS縦型",options:{bold:true}},"現状 10〜50万円","2〜10万円","10〜30万","量産前提。件数が出るのでデータが溜まる"],
    ["映画・テレビCM","部分適用のみ","▲20〜50%","―","桁は変わらない。当社は取りに行かない"],
  ];
  table(s, M, 3.30, W, rows, [2.5,2.2,1.8,1.7,3.83], 9.5, 0.36);
  warn(s, M, 5.22, W, 1.02, "制作原価の下落は、当社にとって追い風でもあり時限でもあります",
    ["米国では企業動画の制作費中央値が 1分あたり約63万円 → 約38万円 に下落済み。日本も追随します。",
     "だから制作だけで終わらせず、3期からツール外販（P4）へ移します。時限は3年と見ています。"]);
  foot(s, "出所: 矢野経済研究所（動画コンテンツビジネス調査2025）／ サイバーエージェント 国内動画広告の市場調査 ／ Vidico（米国の1分単価）／ nowhere film。AI後の単価は工程別削減率からの当社試算です");
}

/* ═══════════ 7. ビジネスモデル ═══════════ */
{
  const s = base(false);
  head(s, 3, "ビジネスモデル", "主軸は映像制作。自社プラットフォームは、作った作品の出口として副次的に置きます");
  const rows=[
    hrow(["","入口","当社","出口","位置づけ"]),
    [{text:"①",options:{bold:true,color:VERM}},"日本の発注企業",{text:"受注し、配分する",options:{bold:true}},"登録クリエイター",{text:"主軸",options:{bold:true,color:VERM}}],
    ["","事業会社・広告代理店・制作会社","要件定義・品質保証・契約・与信・請求","中国を中心に、案件で稼ぐ",""],
    [{text:"②",options:{bold:true,color:NAVY}},"①で作った作品＋日本IP","自社プラットフォーム","視聴者",{text:"副次",options:{color:NAVY}}],
    ["","パブリックドメインから着手","配信・課金・広告・分配","課金と広告で回収",""],
    [{text:"③",options:{bold:true,color:GOLD}},"①②で溜まる制作データ","内製化してツール化","プロダクト外販",{text:"企業価値",options:{bold:true,color:GOLD}}],
    ["","指示→初稿→修正→承認","工程の自動化・特許取得","粗利率80%・人数に比例しない",""],
  ];
  table(s, M, 1.58, W, rows, [0.7,3.3,3.5,3.0,1.53], 9.5, 0.32);
  warn(s, M, 4.14, (W-0.3)/2, 1.24, "①が②のコールドスタートを解きます",
    ["両面市場の宿命は「クリエイターは視聴者がいないと来ない、視聴者はコンテンツがないと来ない」。",
     "①は視聴者を必要としません。案件を配ればクリエイターは集まり、その作品が②の初期コンテンツになります。"]);
  warn(s, M+(W-0.3)/2+0.3, 4.14, (W-0.3)/2, 1.24, "アダルトは対象外です",
    ["受注する案件にも、自社PFに載せる作品にも含めません。理由は技術ではありません。",
     "決済代行とアプリ内課金が通らず、年齢確認の義務が重くなります。単価は高い領域ですが、取りません。"]);
  const y2=5.56, w3=(W-0.6)/3;
  card(s, M,             y2, w3, 0.96, "差別化の核心は価格ではありません",
    ["海外に安く出せること自体は誰でも知っています。やらない理由は「管理しきれないから」です。"], VERM, 9.5);
  card(s, M+w3+0.3,      y2, w3, 0.96, "そこを引き受けるのが商品です",
    ["日本語の要件定義・品質保証・契約・与信・請求。個人クリエイターには越えられない壁。"], NAVY, 9.5);
  card(s, M+(w3+0.3)*2,  y2, w3, 0.96, "発注側の管理コストがゼロになる",
    ["相見積 → 稟議 → 発注書 → 検収 → 請求。この一式を当社が引き受けます。"], GOLD, 9.5);
  foot(s, "クリエイター調達の設計は CHINA_SOURCING ／ プラットフォームの収益設計は PLATFORM_PIVOT 第11章を参照");
}

/* ═══════════ 8. ユニットエコノミクス ═══════════ */
{
  const s = base(false);
  head(s, 3, "ユニットエコノミクス", "売上18億が何の積み上げなのかを、1本あたりと1人あたりで示します");
  s.addText("① 映像制作 — 1本あたり（平均単価50万円のとき）", { x:M, y:1.52, w:6.0, h:0.3, fontFace:F, fontSize:11.5, bold:true, color:INK, margin:0, isTextBox:true });
  const rowsA=[
    hrow(["","金額","備考"]),
    ["売上","50.0万","企業発注の中央値54万より保守的に設定"],
    ["個人クリエイターへの支払","▲12.0万","Bランク。有償テスト課題で確定させる"],
    ["一次レビュー報酬","▲3.0万","Aランクに委託"],
    ["AIツール・素材・レンダリング","▲2.0万",""],
    ["品質バッファ（作り直し）","▲1.5万","ここを原価から外さないこと"],
    [{text:"売上総利益",options:{bold:true,color:VERM}},{text:"31.5万（63%）",options:{bold:true,color:VERM}},{text:"計画は保守的に60%で置く",options:{bold:true}}],
  ];
  table(s, M, 1.88, 6.0, rowsA, [2.5,1.3,2.2], 9, 0.33);
  s.addText("② 自社プラットフォーム — 1MAUあたり年間", { x:M+6.3, y:1.52, w:5.7, h:0.3, fontFace:F, fontSize:11.5, bold:true, color:INK, margin:0, isTextBox:true });
  const rowsB=[
    hrow(["","流通額","当社取り分"]),
    ["課金（課金率3%×ARPPU¥3,000）","¥1,080","¥324（30%）"],
    ["リワード広告（eCPM¥1,200）","¥216","¥108（50%）"],
    ["インタースティシャル（¥600）","¥65","¥32（50%）"],
    [{text:"合計",options:{bold:true,color:NAVY}},{text:"¥1,361",options:{bold:true}},{text:"¥464",options:{bold:true,color:NAVY}}],
    [{text:"5期 期中平均MAU 107.5万人",options:{bold:true}},"",{text:"→ 4.99億円",options:{bold:true,color:NAVY}}],
  ];
  table(s, M+6.3, 1.88, 5.73, rowsB, [2.93,1.4,1.4], 9, 0.33);
  s.addText("③ 5期 売上18億の内訳", { x:M, y:4.42, w:6.0, h:0.3, fontFace:F, fontSize:11.5, bold:true, color:INK, margin:0, isTextBox:true });
  hbar(s, M, 4.80, 6.0, 0.36, 1.00, "映像制作 1,667本 × 60万", "10.0億", VERM, 2.9);
  hbar(s, M, 5.20, 6.0, 0.36, 0.50, "PF課金・広告 MAU107.5万", "5.0億", NAVY, 2.9);
  hbar(s, M, 5.60, 6.0, 0.36, 0.30, "プロダクト外販", "3.0億", GOLD, 2.9);
  warn(s, M+6.3, 4.42, 5.73, 1.82, "最も弱い数字はMAUです",
    ["期末125万人は「PFを副次に留める」設計からの逆算で、実測でも他社比較でもありません。",
     "MAUが計画の1/3（40万人）でも売上14.9億・営業利益1.2億で、事業は黒字を保ちます。",
     "PFを畳んでも制作事業が残る構造にしてあります。"]);
  foot(s, "制作の単価・原価は BUSINESS_PLAN 7-1、PFの1MAU¥464は PLATFORM_PIVOT 11-3。課金率・ARPPU・eCPM・MAUはすべて未実測の［仮置き］です");
}

/* ═══════════ 9. 収益モデル ═══════════ */
{
  const s = base(false);
  head(s, 3, "収益モデル", "3本の柱。人手に比例しない収益（P2〜P4）を5期に44%まで上げます");
  const rows=[
    hrow(["","収益ライン","型","開始","5期の売上","備考"]),
    [{text:"P1",options:{bold:true,color:VERM}},{text:"映像制作の受注 → クリエイターへ配分",options:{bold:true}},"フロー",{text:"初日から",options:{bold:true}},{text:"10.0億",options:{bold:true,color:VERM}},"粗利率60%。売上が人手に比例する"],
    [{text:"P2",options:{bold:true,color:NAVY}},"自社PFの視聴課金（当社取り分30%）","ストック","6ヶ月目〜","3.5億","待つ／広告／課金の3択。BUMPと同型"],
    [{text:"P3",options:{bold:true,color:NAVY}},"自社PFの広告（当社取り分50%）","非連動","6ヶ月目〜","1.5億","非課金層の収益化。追加の獲得費用がゼロ"],
    [{text:"P4",options:{bold:true,color:GOLD}},{text:"制作ツール・モデルの外販",options:{bold:true}},"ストック","3期〜",{text:"3.0億",options:{bold:true,color:GOLD}},"粗利率80%。上場に必要な「読める収益」"],
  ];
  table(s, M, 1.58, W, rows, [0.7,4.0,1.0,1.2,1.3,3.83], 9.5, 0.40);
  s.addText("1話の解放は3択にします（BUMP型）", { x:M, y:3.56, w:6.0, h:0.3, fontFace:F, fontSize:11.5, bold:true, color:INK, margin:0, isTextBox:true });
  const y=3.92, w=(6.0-0.4)/3;
  card(s, M,           y, w, 1.36, "① 待つ", ["24時間で1話無料。","収益はゼロだが、離脱を止める"], MUTED, 9);
  card(s, M+w+0.2,     y, w, 1.36, "② 広告を見る", ["リワード広告1本で1話。","1日3回まで"], NAVY, 9);
  card(s, M+(w+0.2)*2, y, w, 1.36, "③ 課金する", ["1話97円／コイン。","ここが主力"], VERM, 9);
  s.addText("国内1位の BUMP（累計400万DL）が、すでにこの形で成立しています。",
    { x:M, y:5.36, w:6.0, h:0.3, fontFace:F, fontSize:9.5, color:MUTED, margin:0, isTextBox:true });
  warn(s, M+6.3, 3.56, 5.73, 1.32, "広告は「形式」を間違えると逆ざやになります",
    ["フィード型（RPM¥20〜80＝1話0.02〜0.08円）なら配信原価0.225円に負けます。",
     "リワード型（1話0.60円＝原価の2.7倍）だから成立します。"]);
  warn(s, M+6.3, 5.02, 5.73, 1.22, "摩擦を入れないと課金を食います",
    ["リワードは1日3回まで。課金者には広告を出さない。この2つを仕様に必ず入れます。"]);
  foot(s, "出所: BUMP公式（emole）／ Playio・Tenjin 2026年eCPMベンチマーク（日本のリワードeCPMは $17.35）。実効eCPM・課金率・カニバリ率は未実測です");
}

/* ═══════════ 10. 日本IPを使った作品制作 ═══════════ */
{
  const s = base(false);
  head(s, 3, "日本IPを使った作品制作 — 4つの入口", "版権コストの安い順に着手します。D から始め、課金収益が立ってから A へ");
  const rows=[
    hrow(["","対象IP","座組","版権コスト","出口"]),
    [{text:"D",options:{bold:true,color:VERM}},{text:"パブリックドメイン（青空文庫・古典）",options:{bold:true}},"権利処理が不要。単独で制作できる",{text:"ゼロ",options:{bold:true,color:VERM}},"自社PFの初期コンテンツ・実績づくり"],
    [{text:"B",options:{bold:true,color:NAVY}},"自治体・企業のキャラクター","受託（①と同じ）。先方が権利者","ゼロ（先方負担）","自治体PR・企業広報・ふるさと納税"],
    [{text:"C",options:{bold:true,color:NAVY}},"個人作家・Web小説（なろう系・pixiv）","作家と直接レベニューシェア","ほぼゼロ（成功報酬型）","自社PFの課金コンテンツ"],
    [{text:"A",options:{bold:true,color:GOLD}},"中小出版社の既刊マンガ（未映像化作品）","原作使用許諾＋レベニューシェア","数万〜数十万／作品","自社PFの看板作品・海外展開"],
  ];
  table(s, M, 1.58, W, rows, [0.7,3.5,3.4,2.0,2.43], 9.5, 0.40);
  s.addText("着手の順序 — 版権コストの安い順に積み上げる", { x:M, y:3.52, w:6.0, h:0.3, fontFace:F, fontSize:11.5, bold:true, color:INK, margin:0, isTextBox:true });
  const bw=1.32, by=3.90;
  box(s, M,             by+0.60, bw, 0.82, "D", "版権ゼロ", SOFT, VERM, MUTED, 13, 9);
  box(s, M+bw+0.18,     by+0.40, bw, 1.02, "B", "先方負担", SOFT, NAVY, MUTED, 13, 9);
  box(s, M+(bw+0.18)*2, by+0.20, bw, 1.22, "C", "成功報酬", SOFT, NAVY, MUTED, 13, 9);
  box(s, M+(bw+0.18)*3, by,      bw, 1.42, "A", "数万〜数十万", SOFT, GOLD, MUTED, 13, 9);
  warn(s, M+6.3, 3.52, 5.73, 1.40, "IPホルダーはAI生成を警戒します",
    ["原作ファンの反発が、原作そのものの価値を毀損しかねません。",
     "契約に「AI利用の可否と開示方法」を必ず明記します。JIAA調査でも受容条件1位は「AI利用が明記されている」37.6%。"]);
  warn(s, M+6.3, 5.06, 5.73, 1.18, "D はPF公開前から積み上げられます",
    ["版権コストがゼロなので、開発期間中に作れます。公開日に「見るものがある」状態をつくる唯一の方法です。"]);
  foot(s, "出所: 日本動画協会 アニメ産業レポート（制作市場4,662億円・海外売上2兆1,700億円）／ JIAA「2026年インターネット広告に関するユーザー意識調査」");
}

/* ═══════════ 11. 競合 ═══════════ */
{
  const s = base(false);
  head(s, 4, "競合 — 主戦場は国内の映像制作市場です", "相手は国内の制作会社とフリーランス。中国PFはクリエイター獲得での競合です");
  const rows=[
    hrow(["","相手","相手の強み","当社が勝てる点"]),
    [{text:"主戦場",options:{bold:true,color:VERM}},"国内の映像制作会社（中小10〜80万／大手50〜300万）","品質・信用・実績",{text:"価格。原価が半分以下",options:{bold:true}}],
    ["","国内フリーランス（3〜30万）","価格",{text:"品質保証と納期管理。個人では受けきれない規模",options:{bold:true}}],
    ["","クラウドソーシング経由の海外発注","価格","日本語での要件定義と品質保証"],
    ["","中国の個人クリエイターへの直接発注","価格",{text:"契約・与信・請求。個人に直接出せる企業はほぼいない",options:{bold:true}}],
    [{text:"副戦場",options:{bold:true,color:NAVY}},"クリエイター獲得（快手・抖音・Bilibili）","分成率 最大80〜90%＋巨大トラフィック",{text:"分成率では戦わない（次ページ）",options:{color:NAVY}}],
  ];
  table(s, M, 1.58, W, rows, [1.2,3.6,3.2,4.03], 9.5, 0.42);
  s.addText("空白は「制作会社の品質を、フリーランスに近い価格で」", { x:M, y:4.28, w:6.0, h:0.3, fontFace:F, fontSize:11.5, bold:true, color:INK, margin:0, isTextBox:true });
  hbar(s, M, 4.64, 6.0, 0.34, 0.20, "フリーランス", "3〜30万", MUTED, 2.3);
  hbar(s, M, 5.00, 6.0, 0.34, 0.45, "当社", "40〜80万", VERM, 2.3);
  hbar(s, M, 5.36, 6.0, 0.34, 0.55, "中小の制作会社", "10〜80万", MUTED, 2.3);
  hbar(s, M, 5.72, 6.0, 0.34, 1.00, "大手の制作会社", "50〜300万", MUTED, 2.3);
  warn(s, M+6.3, 4.28, 5.73, 1.96, "視聴者側の競合には、正面から行きません",
    ["BUMP（DL400万・国内1位）／POPCORN（累計120億再生）／FANY:D／FOD SHORT ほか最低8サービス。",
     "中国発アプリが日本のアプリ市場シェア9割超。ここへ広告費で挑むのは消耗戦です。",
     "当社のPFは、制作した作品と日本IPの出口として小さく回します。5期でもMAU125万・売上5億の規模です。"]);
  foot(s, "出所: 動画幹事・ムビサク（制作費相場）／ GOKKO ／ nowhere film ／ BUMP公式 ／ 36Kr Japan（中国発アプリの日本シェア）。詳細は COMPETITORS.md");
}

/* ═══════════ 12. なぜクリエイターは当社に来るのか ═══════════ */
{
  const s = base(false);
  head(s, 4, "では、なぜクリエイターは当社に来るのか", "分成率ではなく、3つの別の理由で選ばれる設計にします");
  const y0=1.62, w=(W-0.6)/3, h=1.84;
  card(s, M,           y0, w, h, "再生数ゼロでも収入がある",
    ["大手PFには無い仕組みです。","当社が日本企業から受注して配分するので、視聴者がいなくても報酬が出ます。",
     "これが最大の差別化です。"], VERM, 9.5);
  card(s, M+w+0.3,     y0, w, h, "AIを冷遇しない",
    ["2026年、中国PFは純AIコンテンツの分成を圧縮し、最低保証を廃止しました。","リソースは実写短劇へ移っています。",
     "AI専業のクリエイターは相対的に冷遇され始めています。"], NAVY, 9.5);
  card(s, M+(w+0.3)*2, y0, w, h, "日本市場への窓",
    ["日本語の要件定義・稟議・与信・請求。","個人では越えられない壁を当社が代行します。",
     "日本の発注は単価が高く、支払いが確実です。"], GOLD, 9.5);
  s.addText("各社が提示している分成率 — ここでは戦いません", { x:M, y:3.66, w:6.0, h:0.3, fontFace:F, fontSize:11.5, bold:true, color:INK, margin:0, isTextBox:true });
  hbar(s, M, 4.02, 6.0, 0.34, 0.90, "快手「灵感新纪元」", "最大90%", MUTED, 2.5);
  hbar(s, M, 4.38, 6.0, 0.34, 0.90, "抖音「漫画星河」", "純収益90%", MUTED, 2.5);
  hbar(s, M, 4.74, 6.0, 0.34, 0.80, "Bilibili「觉醒计划」", "最大80%", MUTED, 2.5);
  hbar(s, M, 5.10, 6.0, 0.34, 0.50, "抖音 AI実写短劇", "40〜60%", MUTED, 2.5);
  hbar(s, M, 5.46, 6.0, 0.34, 0.00, "当社", "―", VERM, 2.5);
  s.addText("当社の行が空欄であることが、このページの主張です。", { x:M, y:5.84, w:6.0, h:0.3, fontFace:F, fontSize:9.5, bold:true, color:VERM, margin:0, isTextBox:true });
  warn(s, M+6.3, 3.66, 5.73, 1.34, "分成率では勝てません",
    ["トラフィックがゼロの新規PFが「うちに投稿してください」と言っても、経済合理性がありません。",
     "快手1億／百度10億級のトラフィックプールとは桁が違います。"]);
  warn(s, M+6.3, 5.16, 5.73, 1.08, "ただし2026年、隙間が開きました",
    ["ここが唯一の入口です。ただし中国PFの方針が戻れば消える、時限付きの窓です。"]);
  foot(s, "出所: Bilibili「2026熱門AI漫劇/短劇創作平台」／ 中伝英才「AI短劇制作平台 2026主流平台全解析」／ 网易「2026短劇分账新政」。条件は頻繁に変わるため、提携前に公式条件の確認が必要です");
}

/* ═══════════ 13. 課題と解決 ═══════════ */
{
  const s = base(false);
  head(s, 5, "課題と、その解決方法", "最大の課題は、受託のままでは上場しないことです。そこにP4を置いています");
  warn(s, M, 1.56, W, 1.16, "受託制作のままでは上場しません",
    ["労働集約型の受託は、売上が人手に比例するため成長性が評価されにくく、上場審査でも投資家評価でも「規模の割に伸びない事業」と読まれます。",
     "だから追うべき指標は売上ではなく、人手に比例しない収益（P2〜P4）の比率です。5期で44%、6期で50%超を目指します。"]);
  s.addText("人手に比例しない収益の比率", { x:M, y:2.92, w:6.0, h:0.3, fontFace:F, fontSize:11.5, bold:true, color:INK, margin:0, isTextBox:true });
  hbar(s, M, 3.28, 6.0, 0.32, 0.23, "1期", "23%", MUTED, 1.0);
  hbar(s, M, 3.60, 6.0, 0.32, 0.41, "2期", "41%", NAVY, 1.0);
  hbar(s, M, 3.92, 6.0, 0.32, 0.46, "3期", "46%", NAVY, 1.0);
  hbar(s, M, 4.24, 6.0, 0.32, 0.48, "4期", "48%", NAVY, 1.0);
  hbar(s, M, 4.56, 6.0, 0.32, 0.44, "5期", "44%", VERM, 1.0);
  s.addText("5期に横ばうのは、制作（P1）が10億まで伸びるためです。50%超は6期の見込み。",
    { x:M, y:4.94, w:6.0, h:0.34, fontFace:F, fontSize:9, color:MUTED, margin:0, isTextBox:true });
  const rows=[
    hrow(["残りの課題","解決方法"]),
    ["制作の市場単価が下がる","3年の時限と見ている。P4（ツール外販）を3期から立ち上げて逃げ切る"],
    ["ディレクターが先に詰まる","Aランクのクリエイターに一次レビューを移管し、1人あたり月8本→10本へ"],
    ["クリエイターの離脱","登録は常に稼働数の1.5倍。春節（1〜2月）は稼働が2〜3週間落ちる前提で計画"],
    ["PFの視聴者が集まらない","制作と日本IPで初期コンテンツを賄う。集まらなければPFを縮小し、制作とP4に集中する"],
    ["中国本土から接続できない","設計段階で検証。国内向けミラーまたは提携PF経由の投稿導線を用意"],
  ];
  table(s, M+6.3, 2.92, 5.73, rows, [2.2,3.53], 9, 0.44);
  foot(s, "各課題の詳細と数値根拠は BUSINESS_PLAN ／ MARKET_SIZING ／ MOAT_TIMELINE ／ CHINA_SOURCING に記載");
}

/* ═══════════ 14. チーム ═══════════ */
{
  const s = base(false);
  head(s, 6, "チーム", "（記入予定）");
  const y0=1.70, w=(W-0.6)/3, h=1.70;
  card(s, M,           y0, w, h, "代表取締役", ["経歴 ／ 実績"], VERM, 10);
  card(s, M+w+0.3,     y0, w, h, "CTO／開発責任者", ["採用計画"], NAVY, 10);
  card(s, M+(w+0.3)*2, y0, w, h, "制作ディレクター責任者", ["採用計画"], GOLD, 10);
  warn(s, M, 3.72, W, 1.30, "この章は記入予定です",
    ["代表の経歴と実績 ／ これから採用する職種・時期・採用チャネル ／ アドバイザー・顧問"]);
  const rows=[
    hrow(["","1期","2期","3期","4期","5期"]),
    ["日本側 人員","6名","14名","25名","36名","50名"],
    ["中国側 登録クリエイター","8〜10名","15〜18名","25〜30名","45〜55名","70名前後"],
    [{text:"1人あたり人件費",options:{bold:true}},"500万","700万","800万","900万",{text:"1,000万",options:{bold:true}}],
  ];
  table(s, M, 5.20, W, rows, [3.0,1.8,1.8,1.8,1.8,1.83], 9.5, 0.32);
  foot(s, "1期は6名（代表・エンジニア2・制作ディレクター1・クリエイター管理1・営業1）。制作事業のため、売上の伸びと人員の伸びが連動します");
}

/* ═══════════ 15. 事業計画 ═══════════ */
{
  const s = base(false);
  head(s, 7, "事業計画", "3期まで赤字が前提。通期黒字化は4期、上場申請は5期です");
  const labels=["1期 2027/9","2期 2028/9","3期 2029/9","4期 2030/9","5期 2031/9"];
  s.addChart(p.ChartType.bar, [
    { name:"売上高", labels, values:[35,177,468,958,1799] },
    { name:"営業利益", labels, values:[-42,-79,-67,59,384] },
  ], {
    x:M, y:1.6, w:6.6, h:3.3,
    barDir:"col", barGrouping:"clustered",
    chartColors:[NAVY, VERM],
    catAxisLabelFontFace:F, catAxisLabelFontSize:9, catAxisLabelColor:MUTED,
    valAxisLabelFontFace:F, valAxisLabelFontSize:9, valAxisLabelColor:MUTED,
    valAxisMinVal:-200, valAxisMaxVal:1900,
    showValue:true, dataLabelFontFace:F, dataLabelFontSize:8, dataLabelColor:INKSOFT,
    showLegend:true, legendPos:"b", legendFontFace:F, legendFontSize:9,
    valGridLine:{ color:LINE, style:"solid", size:0.5 }, catGridLine:{ style:"none" },
    title:"売上高と営業利益の推移（単位 百万円・計画値）", showTitle:true,
    titleFontFace:F, titleFontSize:11, titleColor:INK,
  });
  const cx=M+6.9, cw=W-6.9;
  card(s, cx, 1.6, cw, 1.02, "1期 ― 基盤をつくる",
    ["制作54本で2,700万。PF公開は6ヶ月目。営業利益 ▲4,200万は計画通りの投資です。"], VERM, 9.5);
  card(s, cx, 2.74, cw, 0.9, "2〜3期 ― 投資期間",
    ["制作体制の拡大に投下。赤字は2期に最大化（▲7,900万）し、3期から縮小に転じます。"], NAVY, 9.5);
  card(s, cx, 3.76, cw, 1.14, "4〜5期 ― 回収",
    ["4期に通期黒字化。5期に年商18億・営業利益3.8億（21.3%）。時価総額64億の水準へ。"], GOLD, 9.5);
  const rows=[
    hrow(["","売上の内訳（百万円）","この期の到達点"]),
    ["1期","制作27 ／ PF 8","制作54本・PF公開・登録100名"],
    ["2期","制作105 ／ PF 72","監査法人ショートレビュー／シリーズA 3億"],
    ["3期（N-2期）","制作252 ／ PF 186 ／ P4 30","監査開始。赤字が縮小に転じる"],
    ["4期（N-1期）","制作502 ／ PF 336 ／ P4 120","通期黒字化。内部管理体制の構築"],
    [{text:"5期（N期）→ 2031年 上場",options:{bold:true,color:VERM}},{text:"制作1,000 ／ PF 499 ／ P4 300",options:{bold:true}},{text:"売上18億・営業利益3.8億",options:{bold:true}}],
  ];
  table(s, M, 5.06, W, rows, [3.0,4.5,4.53], 10, 0.3);
  foot(s, "計画値。制作の単価・粗利率、PFの課金率・ARPPU・eCPM、MAUはすべて未実測です。1期に実測して差し替えます。数字は financial_model.py が計算しています");
}

/* ═══════════ 16. 上場までの流れ ═══════════ */
{
  const s = base(false);
  head(s, 8, "上場までの流れ", "5期（2031年）での上場を逆算。N-2期の監査開始は3期・2028年10月です");
  const y0=1.62, w=(W-1.2)/5, h=1.50;
  card(s, M,             y0, w, h, "1期  2026/10-2027/9", ["・制作の受注開始","・PF開発と公開","・ディレクター時間の実測"], VERM, 9);
  card(s, M+w+0.3,       y0, w, h, "2期  2027/10-2028/9", ["・制作体制の拡大","・シリーズA 3億","・監査法人SR"], NAVY, 9);
  card(s, M+(w+0.3)*2,   y0, w, h, "3期 N-2  2028/10-2029/9", ["・監査開始","・P4の立ち上げ","・主幹事証券の選定"], NAVY, 9);
  card(s, M+(w+0.3)*3,   y0, w, h, "4期 N-1  2029/10-2030/9", ["・通期黒字化","・内部管理体制の構築","・資本政策の確定"], GOLD, 9);
  card(s, M+(w+0.3)*4,   y0, w, h, "5期 N期  2030/10-2031/9", ["・上場申請","・2031年・東証グロース"], GOLD, 9);
  const y1=3.34, w2=(W-0.3)/2;
  card(s, M, y1, w2, 1.42, "資本政策の想定",
    ["シード1.5億（今回）→ ESOP枠10% → シリーズA 3億（2期）。累計4.5億。",
     "IPO公募20%を経て、上場時の創業者持分は 42%前後 を想定。",
     "1ラウンドで33%超は放出しません（特別決議の拒否権を渡さないため）。"], NAVY, 9.5);
  warn(s, M+w2+0.3, y1, w2, 1.42, "5年で上場するための最初の関門",
    ["2期（2028年）に監査法人のショートレビューを受ける必要があります。",
     "赤字が最大化する期に監査法人を確保できるかが関門です。シリーズAの契約書を持って臨みます。"]);
  warn(s, M, 4.96, W, 1.28, "ゴールは上場ではありません。そして上場時点では維持基準に届きません",
    ["グロースは2030年3月以降「上場5年経過後に時価総額100億円」の維持基準が新設されました。2031年上場なら2036年に100億円。",
     "当社の上場時の想定時価総額は64億で、届いていません。期限は2036年なので、上場後5年で1.55倍にする計画を示す必要があります。"]);
  foot(s, "出所: 日本取引所グループ 上場維持基準。上場基準は改定が続くため、準備期に入る前に最新基準を再確認します");
}

/* ═══════════ 17. 出口とリターン ═══════════ */
{
  const s = base(false);
  head(s, 8, "出口とリターン", "5期の売上18億・営業利益3.8億を前提に、3手法で試算しています");
  const y0=1.62, h=1.52, w=(W-0.6)/3;
  stat(s, M,           y0, w, h, "51〜103億", "PER法", "当期純利益 約2.6億（実効税率33%）× PER 20〜40倍");
  stat(s, M+w+0.3,     y0, w, h, "36〜90億",  "PSR法", "売上18億 × PSR 2〜5倍", NAVY);
  stat(s, M+(w+0.3)*2, y0, w, h, "38〜64億",  "EV/EBITDA法", "EBITDA 約4.2億 × 8.9〜15倍（情報通信業の中央値8.9倍）", GOLD);
  s.addText("中心値は 時価総額 64億円 ─ グロースの上場維持基準（2036年に100億円以上）に対し 36億円の不足",
    { x:M, y:3.32, w:W, h:0.36, fontFace:F, fontSize:12.5, bold:true, color:VERM, valign:"middle", margin:0, isTextBox:true });
  const y1=3.84, w2=(W-0.3)/2;
  card(s, M, y1, w2, 1.46, "M&A で売却する場合",
    ["3期（売上4.7億・赤字）… 10〜25億。買い手が評価するのはクリエイター網と技術。",
     "4期（売上9.6億・営業利益0.6億）… 20〜45億 ／ 5期（売上18億）… 38〜64億。",
     "戦略的買い手（大手代理店・制作会社・テレビ局）ならシナジー価格が乗ります。"], NAVY, 9.5);
  card(s, M+w2+0.3, y1, w2, 1.46, "創業者・投資家のリターン",
    ["上場時の創業者持分は 42%前後 を想定。時価総額64億なら評価額 約27億。",
     "シリーズBが不要になったため、経営権（50%超）は上場直前まで維持できます。",
     "IPOはロックアップ（通常90〜180日）があり、現金化は数年かけて段階的になります。"], GOLD, 9.5);
  warn(s, M, 5.46, W, 0.78, "すべて「成功した場合」の試算です",
    ["2025年のグロースIPOは18社（前年34社から半減）で、IPO市場そのものが縮んでいます。倍率は市況で変動します。"]);
  foot(s, "出所: M&A総研（業種別EV/EBITDA倍率）／ みつきコンサルティング（メディア・コンテンツ業界のM&A）／ EY Japan（2026年以降のIPO市場）／ FiNX（グロース維持基準の制度化）");
}

/* ═══════════ 18. マイルストーン ═══════════ */
{
  const s = base(false);
  head(s, 9, "マイルストーン", "各フェーズは「ゲート条件」で区切ります。満たさない限り、次へは進みません");
  const rows=[
    hrow(["時期","やること","◆ 次へ進むゲート条件"]),
    ["〜2026/12","法人設立・PF要件定義・クリエイターに有償テスト課題","クリエイターのランク判定／PF仕様の確定／法務の見解書"],
    ["2027/1-3","制作の受注開始／PF開発",{text:"制作 累計5本・粗利率60%／ディレクター時間 8時間",options:{bold:true,color:VERM}}],
    ["2027/4-9","PF公開（6ヶ月目）・視聴者獲得の開始・D案IPの投入","制作 1期54本／登録100名・公開作品500本／課金率とCPIの初回実測"],
    ["2期","制作体制の拡大・課金モデルの最適化","シリーズA 3億／監査法人ショートレビュー"],
    ["3期","赤字の縮小・P4（ツール外販）の立ち上げ","P4の売上が立つ／人手に比例しない収益45%以上／監査開始"],
    ["4期","通期黒字化・内部管理体制の構築","通期黒字化／プロダクト比率12%／流通株式25%の設計合意"],
    [{text:"5期",options:{bold:true,color:VERM}},{text:"上場申請",options:{bold:true}},{text:"売上18億・営業利益3.8億／時価総額64億",options:{bold:true}}],
  ];
  table(s, M, 1.58, W, rows, [1.6,4.6,5.83], 9.5, 0.38);
  warn(s, M, 4.90, W, 1.34, "最優先で実測するのは「1本あたりディレクター投下時間」です",
    ["［仮置き］8時間で人員計画の全部を置いています。実測が16時間なら必要人数が倍になり、5期の営業利益は3.8億→2.4億に落ちます。",
     "最初の3案件で必ず測ってください。後で気づくより、2027年3月時点で直すほうが遥かに安く済みます。"]);
  foot(s, "ゲート条件を満たさない場合は次フェーズに進まず、前提を引き直します。詳細は ROADMAP.md");
}

/* ═══════════ 19. 資金計画 ═══════════ */
{
  const s = base(false);
  head(s, 10, "資金計画", "調達目標 1.5億円。融資を使わず、全額をエクイティで調達します");
  s.addText("1年目の使途（単位 万円・合計 11,680万）", { x:M, y:1.52, w:6.3, h:0.3, fontFace:F, fontSize:11.5, bold:true, color:INK, margin:0, isTextBox:true });
  const items=[["人件費（6名）",3000,VERM],["PF開発（アプリ・Web・課金）",2500,NAVY],["制作事業の運転資金",1500,VERM],
    ["視聴者獲得（流量投放）",1500,NAVY],["営業・マーケティング",800,VERM],["オフィス・SaaS・その他",480,MUTED],
    ["設立・機材・その他初期",400,MUTED],["法務（資金決済法・UGC対応）",300,MUTED],["分配原資の補填",300,MUTED],
    ["採用費・渡航費・特許・データ基盤",700,MUTED]];
  items.forEach(function(it,i){ hbar(s, M, 1.88+i*0.36, 6.3, 0.32, it[1]/3000, it[0], String(it[1]), it[2], 3.0); });
  const y1=1.88, w2=W-6.9;
  stat(s, M+6.9,                y1, (w2-0.3)/2, 1.44, "800万", "資本金（創業者出資）", "1,000万未満に抑え、初年度の消費税課税事業者化を回避", GOLD);
  stat(s, M+6.9+(w2-0.3)/2+0.3, y1, (w2-0.3)/2, 1.44, "1.42億", "シード（創業時）", "放出20〜27%を想定。J-KISSでの価格先送りも選択肢", NAVY);
  warn(s, M+6.9, 3.50, w2, 1.48, "1.5億は「1年目の使途」ではありません",
    ["1年目に使うのは 1億1,680万。残り約3,320万は2期への持ち越しです。",
     "1期末の手元は約1億300万で、2期の月次赤字660万に対して15ヶ月分のランウェイがあります。",
     "シリーズA 3億は2期の実績を見てから臨めます。"]);
  warn(s, M+6.9, 5.10, w2, 1.14, "追加調達はシリーズA 3億のみ。累計4.5億です",
    ["旧計画はシリーズB 8億を含む累計12.5億でした。8億ぶん不要になり、創業者持分が42%まで厚く残ります。"]);
  s.addText("［仮置き］視聴者獲得のCPIが未実測のため、流量投放1,500万の精度が最も低い数字です。PF公開後に実測して増減させます。",
    { x:M, y:5.56, w:6.3, h:0.5, fontFace:F, fontSize:9, color:MUTED, valign:"top", lineSpacingMultiple:1.2, margin:0, isTextBox:true });
  foot(s, "※ 融資は使いません。補助金は後払いのため資金繰りに算入していません。全額をエクイティで調達します");
}

/* ═══════════ 20. リスクと対策 ═══════════ */
{
  const s = base(false);
  head(s, 11, "リスクと対策", "影響度と発生確率で並べています。上の3つが、この事業の生死を分けます");
  const rows=[
    hrow(["#","影響度","発生確率","リスク","対策"]),
    [{text:"1",options:{bold:true}},{text:"高",options:{bold:true,color:VERM}},{text:"中",options:{color:VERM}},{text:"ディレクター時間が想定の倍",options:{bold:true}},"最初の3案件で実測。超えるなら一次レビューをAランクへ移管し、人員計画を引き直す"],
    [{text:"2",options:{bold:true}},{text:"高",options:{bold:true,color:VERM}},{text:"高",options:{bold:true,color:VERM}},{text:"制作の市場単価が下がる",options:{bold:true}},"3年の時限と見ている。P4（ツール外販）を3期から立ち上げて逃げ切る"],
    [{text:"3",options:{bold:true}},{text:"高",options:{bold:true,color:VERM}},{text:"中",options:{color:VERM}},{text:"シリーズA 3億が入らない",options:{bold:true}},"PFを止めて制作に全振り。2期の営業利益は▲7,900万→▲1,000万。単独で生き残れる"],
    ["4","高","低","営業・ディレクターが採用できない","2次受け（代理店経由）を主軸に置けば律速がディレクターに移り、採用難易度が下がる"],
    ["5","中","高","PFの視聴者が集まらない","MAUが計画の1/3でも営業利益率7.9%を維持。PFを縮小し制作とP4に集中する"],
    ["6","中","中","資金決済法・UGC対応の義務","PF設計の前に弁護士へ確認。法務費用300万を初年度に計上済み"],
    ["7","中","中","中国本土から当社PFに接続できない","設計段階で検証。国内向けミラーまたは提携PF経由の投稿導線を用意"],
    ["8","中","低","クリエイターの離脱","登録は常に稼働数の1.5倍。春節（1〜2月）の稼働低下も計画に織り込み済み"],
  ];
  table(s, M, 1.58, W, rows, [0.5,0.9,1.0,3.6,6.03], 9, 0.42);
  warn(s, M, 5.42, W, 0.82, "1と2は「制作事業そのもの」のリスクです",
    ["3〜7のプラットフォーム側が全部外れても、制作事業は残ります。ここが旧計画との決定的な違いです。"]);
  foot(s, "全リスクと対策は BUSINESS_PLAN ／ MOAT_TIMELINE ／ CHINA_SOURCING ／ PLATFORM_PIVOT に記載しています");
}

/* ═══════════ 21. クロージング ═══════════ */
{
  const s = base(true);
  s.addText("制作力が余っている場所と、発注が余っている場所をつなぐ。", { x:M, y:2.30, w:11.9, h:0.8, fontFace:F, fontSize:32, bold:true,
    color:PAPER, valign:"middle", margin:0, isTextBox:true });
  s.addText("中国では制作会社の42%が1四半期で消え、日本の映像制作市場は4,580億円で伸び続けています。",
    { x:M, y:3.20, w:11.9, h:0.5, fontFace:F, fontSize:15, color:ONDARK, valign:"middle", margin:0, isTextBox:true });
  const y=4.30, w=(W-0.6)/3;
  s.addText("1.5億円", { x:M, y, w, h:0.6, fontFace:F, fontSize:30, bold:true, color:PAPER, valign:"middle", margin:0, isTextBox:true });
  s.addText("今回の調達目標", { x:M, y:y+0.62, w, h:0.3, fontFace:F, fontSize:11, color:ONORG, valign:"middle", margin:0, isTextBox:true });
  s.addText("3年", { x:M+w+0.3, y, w, h:0.6, fontFace:F, fontSize:30, bold:true, color:PAPER, valign:"middle", margin:0, isTextBox:true });
  s.addText("この窓が開いている期間", { x:M+w+0.3, y:y+0.62, w, h:0.3, fontFace:F, fontSize:11, color:ONORG, valign:"middle", margin:0, isTextBox:true });
  s.addText("2031年", { x:M+(w+0.3)*2, y, w, h:0.6, fontFace:F, fontSize:30, bold:true, color:PAPER, valign:"middle", margin:0, isTextBox:true });
  s.addText("東証グロース上場", { x:M+(w+0.3)*2, y:y+0.62, w, h:0.3, fontFace:F, fontSize:11, color:ONORG, valign:"middle", margin:0, isTextBox:true });
}

p.writeFile({ fileName: "deck.pptx" }).then(function(){ console.log("deck.pptx"); });
