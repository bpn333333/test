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
function img(s, path, x, y, w, h){
  s.addImage({ path, x, y, w, h });
}
function sec(s,x,y,w,t){
  s.addText(t,{x,y,w,h:0.3,fontFace:F,fontSize:11.5,bold:true,color:INK,valign:"middle",margin:0,isTextBox:true});
}
function warn(s, x, y, w, h, title, lines, fs){
  s.addShape(p.ShapeType.rect, { x, y, w, h, fill:{color:"FBF1F1"} });
  s.addShape(p.ShapeType.rect, { x, y, w:0.05, h, fill:{color:VERM} });
  s.addText("⚠ "+title, { x:x+0.28, y:y+0.16, w:w-0.5, h:0.3, fontFace:F, fontSize:12, bold:true,
    color:VERM, valign:"middle", margin:0, isTextBox:true });
  s.addText(lines.map((t,i)=>({text:t, options:{breakLine:i<lines.length-1}})),
    { x:x+0.28, y:y+0.52, w:w-0.5, h:h-0.68, fontFace:F, fontSize:fs||10, color:INKSOFT,
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
  img(s, "assets/image5.jpg", -0.04, 0, 13.44, 7.50);
  // 写真の上に白文字を置くため、可読性用のスクリム（半透明の黒）を敷く
  s.addShape(p.ShapeType.rect, { x:0, y:0, w:13.333, h:7.5, fill:{color:"000000", transparency:52} });
  s.addShape(p.ShapeType.rect, { x:M, y:2.05, w:0.62, h:0.62, fill:{color:PAPER} });
  s.addText("次世代AI映像制作会社の設立", { x:M, y:2.82, w:11.90, h:1.51, fontFace:F, fontSize:40, bold:true,
    color:PAPER, valign:"middle", margin:0, isTextBox:true });
  s.addText("東アジアを21世紀のハリウッドにするためのAI映像制作ハブとなるAI映像制作会社のシード投資のご案内",
    { x:M, y:4.61, w:11.90, h:0.50, fontFace:F, fontSize:15, color:ONDARK, valign:"middle", margin:0, isTextBox:true });
  s.addText("投資家向け企画書  ／  2026年9月", { x:M, y:6.48, w:7, h:0.36, fontFace:F, fontSize:12, color:ONORG, valign:"middle", margin:0, isTextBox:true });
  s.addText("新設法人（株式会社・仮称）", { x:M, y:6.84, w:7, h:0.36, fontFace:F, fontSize:12, color:ONORG, valign:"middle", margin:0, isTextBox:true });
}

/* ═══════════ 2. エグゼクティブサマリー ═══════════ */
{
  const s = base(false);
  head(s, 0, "エグゼクティブサマリー", "中華圏の最先端技術に日本のクオリティーコントロールとIPを融合させ、世界市場を取りに行く企業を設立");
  lede(s, 1.50, ["5年後・2031年、東証グロース市場への上場を目指す。",
    "中国を中心に世界のAIクリエイターを集め、企業案件と越境C2C発注で回すプラットフォームをつくる。"]);
  const y0=2.56, h=1.52, w=(W-0.6)/3;
  stat(s, M,           y0, w, h, "4,580億円", "国内の映像制作市場（実測）", "矢野経済研究所。2027年度は5,400億円の予測", VERM);
  stat(s, M+w+0.3,     y0, w, h, "3本立て",   "収益の柱", "企業案件の仲介（初日から）＋ 越境C2C発注の手数料（6ヶ月目〜）＋ ツール外販（2期〜）", NAVY);
  stat(s, M+(w+0.3)*2, y0, w, h, "1.5億円",   "今回の調達目標", "追加はシリーズA 3億のみ。累計4.5億で上場まで届く設計", GOLD);
  const y1=4.26, h2=2.28, w2=(W-0.6)/3;
  card(s, M,            y1, w2, h2, "何をするか",
    ["① 日本・海外の個人と中小事業者が、中国の映像クリエイターに直接発注できるプラットフォームを運営する。",
     "② 企業案件は当社が受注し、登録クリエイターに配分する。再生数がゼロでも稼げる。",
     "③ 溜まった制作データで生成AI関連の特許を取得し、チェックポイント・LoRA・モデル開発へ。①の自動化機能をそのままツールとして外販する。"]);
  card(s, M+w2+0.3,     y1, w2, h2, "なぜ勝てるか",
    ["2026年、中国の大手PFは純AIコンテンツの分成を圧縮し、最低保証を廃止した。AI専業のクリエイターは行き場を探している。",
     "企業案件があるので、トラフィックがゼロの初日からクリエイターに報酬を出せる。",
     "分成率で折り合わない課題を解決する唯一の設計。"], NAVY);
  card(s, M+(w2+0.3)*2, y1, w2, h2, "どこへ向かうか",
    ["1年目に基盤を作り、2〜3年目は投資期間。",
     "4年目に通期黒字化、5年目に年商20億・営業利益6.1億。",
     "売上の76%が人手に比例しない収益。自動車産業が輸入技術を4年で国産化したのと同じ道筋を、3年で。"], GOLD);
  foot(s, "収支は［仮置き］を含む計画値です。国内市場規模は矢野経済研究所の実測値。制作の単価・粗利率は業界相場からの設定で、1期に実測して差し替えます。");
}

/* ═══════════ 3. なぜ今なのか ═══════════ */
{
  const s = base(false);
  head(s, 1, "なぜ今なのか", "出遅れている日本、淘汰が始まった中国。そして優秀なAIクリエイターが行き場を失っている今がチャンス");
  const y0=1.46, w=(W-0.9)/4, h=1.52;
  card(s, M,             y0, w, h, "1  日本は出遅れている",
    ["政府がAI推進法を制定し、AI基本計画を閣議決定するほどの危機感。","映像制作の現場にAIはまだ入っていない。"], VERM, 9);
  card(s, M+w+0.3,       y0, w, h, "2  中国では淘汰が始まった",
    ["AI映像の制作会社は2026年Q1に 1,216社→698社（−42%）。","約90%が赤字。最大コストは広告出稿で約70%。"], VERM, 9);
  card(s, M+(w+0.3)*2,   y0, w, h, "3  制作力が余っている",
    ["中国PFは純AIコンテンツの分成を圧縮し、最低保証を廃止。","足りないのは「作る力」ではなく「売る力」。"], NAVY, 9);
  card(s, M+(w+0.3)*3,   y0, w, h, "4  当社が売る力になる",
    ["日本の発注を取り、要件定義・品質保証・契約・請求を引き受ける。","彼らは作るだけでよくなる。"], GOLD, 9);

  /* 松田さんが挿入した3枚。カード2・3・4の真下に置く（座標は編集版のまま） */
  img(s, "assets/image3.png",  4.11, 3.15, 2.03, 1.52);
  img(s, "assets/image2.png",  7.15, 3.18, 2.03, 1.46);
  img(s, "assets/image1.png", 10.19, 3.18, 2.20, 1.46);

  s.addShape(p.ShapeType.rect, { x:M, y:4.84, w:W, h:1.66, fill:{color:SOFT} });
  s.addText("中国のAI映像制作会社数", { x:1.05, y:4.91, w:6.00, h:0.30, fontFace:F, fontSize:11, bold:true, color:INK, margin:0, isTextBox:true });
  s.addText("2025年 Q4", { x:1.05, y:5.35, w:2.20, h:0.28, fontFace:F, fontSize:10, color:MUTED, margin:0, isTextBox:true });
  s.addText("1,216社", { x:1.05, y:5.63, w:2.40, h:0.60, fontFace:F, fontSize:22, bold:true, color:INK, valign:"middle", margin:0, isTextBox:true });
  s.addText("→", { x:3.65, y:5.63, w:0.70, h:0.60, fontFace:F, fontSize:18, color:MUTED, align:"center", valign:"middle", margin:0, isTextBox:true });
  s.addText("2026年 Q1", { x:4.45, y:5.35, w:2.20, h:0.28, fontFace:F, fontSize:10, color:MUTED, margin:0, isTextBox:true });
  s.addText("698社", { x:4.45, y:5.63, w:2.40, h:0.60, fontFace:F, fontSize:22, bold:true, color:VERM, valign:"middle", margin:0, isTextBox:true });
  s.addText([{text:"1四半期で −42%。制作力が市場に溢れ出しています。", options:{breakLine:true, bold:true, color:VERM}},
             {text:"ただし淘汰されているのは、広告出稿で視聴者を取りに行った会社です。作る力そのものは市場に残っています。", options:{breakLine:true}},
             {text:"当社が取るのは制作力であって、彼らが負けた土俵（視聴者獲得の消耗戦）には乗りません。", options:{}}],
    { x:7.65, y:4.97, w:4.53, h:1.40, fontFace:F, fontSize:9.5, color:INKSOFT, lineSpacingMultiple:1.26, valign:"top", margin:0, isTextBox:true });
  foot(s, "出所: 内閣府 AI戦略 ／ 第一財経・搜狐（中国AI短劇の淘汰）／ 网易「2026短劇分账新政」／ 経済産業省");
}

/* ═══════════ 4. 最終ゴール ═══════════ */
{
  const s = base(false);
  head(s, 1, "最終ゴール", "日本に制作ハブを置き、中華圏の技術を束ねて世界市場を取りに行く");
  lede(s, 1.52, ["AI映像制作ハブを日本に置く。",
    "中華圏の最先端技術に、日本のクオリティーコントロールとIPを載せて世界へ出す。"]);
  const y0=2.66, w=(W-0.6)/3, h=2.16;
  card(s, M,           y0, w, h, "① 日本の企業案件",
    ["4,580億円の実測市場。法人が発注し、与信と請求が必要な領域。",
     "個人クリエイターには越えられない壁を当社が引き受ける。",
     "初日から現金を生む主軸。"], VERM, 10);
  card(s, M+w+0.3,     y0, w, h, "② 越境C2C発注プラットフォーム",
    ["日本・海外の個人と中小事業者が、中国のクリエイターに直接発注できる場。",
     "言語・決済・品質保証・契約の壁を、システムで引き受ける。",
     "6ヶ月目から。取引手数料で回収する。"], NAVY, 10);
  card(s, M+(w+0.3)*2, y0, w, h, "③ 日本の個人案件",
    ["ウエディング・終活など、個人が発注する領域。単価5〜20万。",
     "法人案件の閑散期を埋める調整弁。",
     "要求が定型的で件数が出るため、最良の学習データ源になる。"], GOLD, 10);
  warn(s, M, 5.02, W, 1.22, "3つとも「制作」が土台です",
    ["②のプラットフォームは、①③で積んだクリエイターが無ければ受け手がいません。プラットフォームが先ではなく、制作が先です。",
     "そして①②③で溜まった制作データが、内製化・特許・モデル外販（P4）の原料になります。ここが企業価値の本体です。"]);
  foot(s, "市場規模の出所は次ページ以降。個人案件は「個人が発注する市場」であり、クリエイターエコノミー（個人が受け取る市場）とは別物です");
}

/* ═══════════ 5. 市場規模 ═══════════ */
{
  const s = base(false);
  head(s, 2, "市場規模", "市場は制約になりません。制約はクリエイター獲得と発注者獲得の資金です");
  const y0=1.58, h=1.52, w=(W-0.6)/3;
  stat(s, M,           y0, w, h, "4,580億円", "国内 動画制作サービス市場（2025年度予測）", "2024年度 4,238億円 → 2027年度 5,400億円【実測・矢野経済研究所】", VERM);
  stat(s, M+w+0.3,     y0, w, h, "1兆437億円", "国内 動画広告市場（2026年）", "2025年 8,855億円から拡大。縦型動画広告は前年比155.9%【実測】", NAVY);
  stat(s, M+(w+0.3)*2, y0, w, h, "6,800億円",  "スキルシェア市場（2028年予測）", "②が面する市場。動画編集はこのうちの一部【推計】", GOLD);
  const rows=[
    hrow(["","当社が取りに行く帯","現状の制作費","AI導入後","なぜここか"]),
    [{text:"★ 企業VP・会社紹介",options:{bold:true}},"法人が発注","50〜150万円","18〜52万円","フル生成AIが成立する。撮影が消えて原価が半分以下になる"],
    [{text:"★ 展示会・イベント映像",options:{bold:true}},"法人が発注","20〜100万円","6〜30万円","ループ素材は特に効く。閑散期を埋める"],
    [{text:"★ PR素材・SNS縦型",options:{bold:true}},"個人・中小が発注","10〜50万円","2〜10万円","②の主戦場。量産前提で件数が出る"],
    ["映画・テレビCM","—","3〜5億／1,000万〜1億","▲20〜50%","桁は変わらない。当社は取りに行かない"],
  ];
  table(s, M, 3.30, W, rows, [2.5,1.9,2.1,1.7,3.83], 9.5, 0.36);
  warn(s, M, 5.22, W, 1.02, "制作原価の下落は、当社にとって追い風でもあり時限でもあります",
    ["米国では企業動画の制作費中央値が 1分あたり約63万円 → 約38万円 に下落済み。日本も追随します。",
     "だから制作だけで終わらせず、①の自動化機能をツール外販（P4）へ移します。時限は3年と見ています。"]);
  foot(s, "出所: 矢野経済研究所（動画コンテンツビジネス調査2025）／ サイバーエージェント 国内動画広告の市場調査 ／ Business Insider Japan（スキルシェア市場2028年予測）／ Vidico（米国の1分単価）／ nowhere film。AI後の単価は工程別削減率からの当社試算です");
}

/* ═══════════ 6. 企業案件と個人案件 — 発注市場の規模 ═══════════ */
{
  const s = base(false);
  head(s, 2, "企業案件と個人案件 — 発注市場の規模", "「誰がお金を払うのか」で見ると、法人と個人では市場の性質がまったく違います");
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
  warn(s,M,5.96,W,0.88,"個人の発注市場は小さい。だから「国内で取る」のではなく「越境で開く」",
    ["個人が発注する市場は小さく、統計すら整備されていません。国内C2C（ココナラ等）で個人が中国のクリエイターに直接発注できないのは、言語・決済・品質保証・契約の壁があるからです。",
     "当社はこの壁をシステムで引き受け、越境の発注を成立させます。法人案件（①）は従来どおり当社が受注して配分します。"],9.5);
  foot(s,"出所: 矢野経済研究所（動画コンテンツビジネス調査2025）／ Business Insider Japan（スキルシェア市場2028年予測）／ クリエイターエコノミー協会（2025年版調査）／ ココナラ・ランサーズ公開単価。企業案件は実測値、個人案件は推計値です");
}

/* ═══════════ 7. AI導入で、制作費はいくらになり、いくら浮くのか ═══════════ */
{
  const s = base(false);
  head(s,2,"AI導入で、制作費はいくらになり、いくら浮くのか","削減が効くのは「人が動く工程」です。撮影・機材・出演で費用の55%。ここが1/5になると単価が根本から変わります");
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
  s.addText("★ 下3行がフル生成AIの成立帯です。当社が取りに行くのはこの帯です。映画・CMは部分適用にとどまり、桁は変わりません。",
    {x:M,y:4.62,w:W,h:0.28,fontFace:F,fontSize:10,bold:true,color:VERM,valign:"middle",margin:0,isTextBox:true});
  sec(s,M,4.98,5.9,"内訳はこう変わる｜企業VP 1本　100万円 → 35万円");
  const parts=[["企画",15,7.5,NAVY],["撮影",38,7.6,VERM],["機材",10,2.0,"8C1F26"],
               ["出演",7,0.7,ORANGE],["編集",20,10.0,TEAL],["諸経費",10,7.0,MUTED]];
  const bx=M+1.10, bw=4.15;
  [["現状",5.34,1],["AI後",5.76,2]].forEach(function(r){
    let cx=bx;
    s.addText(r[0],{x:M,y:r[1],w:1.02,h:0.30,fontFace:F,fontSize:9.5,bold:true,color:INK,valign:"middle",margin:0,isTextBox:true});
    parts.forEach(function(t){ const v=r[2]===1?t[1]:t[2], w=bw*v/100;
      s.addShape(p.ShapeType.rect,{x:cx,y:r[1],w,h:0.30,fill:{color:t[3]}});
      if(v>=12) s.addText(String(v),{x:cx,y:r[1],w,h:0.30,fontFace:F,fontSize:8.5,bold:true,color:PAPER,align:"center",valign:"middle",margin:0,isTextBox:true});
      cx+=w; });
    s.addText(r[2]===1?"100万円":"35万円",{x:cx+0.08,y:r[1],w:1.0,h:0.30,fontFace:F,fontSize:10,bold:true,
      color:r[2]===1?INK:TEAL,valign:"middle",margin:0,isTextBox:true});
  });
  parts.forEach(function(t,i){ const x=M+i*0.98;
    s.addShape(p.ShapeType.rect,{x,y:6.20,w:0.13,h:0.13,fill:{color:t[3]}});
    s.addText(t[0],{x:x+0.19,y:6.13,w:0.78,h:0.26,fontFace:F,fontSize:8,color:MUTED,valign:"middle",margin:0,isTextBox:true});
  });
  s.addText("撮影38＋機材10＋出演7＝55%が 10.3 まで落ちます。編集と諸経費は残ります。",
    {x:M,y:6.44,w:5.9,h:0.26,fontFace:F,fontSize:8.5,bold:true,color:VERM,valign:"middle",margin:0,isTextBox:true});
  card(s,M+6.2,4.98,W-6.2,1.72,"実際に出ている削減幅（実例）",
    ["大手保険のWeb広告動画　制作コスト ▲30〜50%／期間 ▲40%",
     "Amazon Nova活用の広告　費用 ▲70%・効果 8倍",
     "サイバーエージェント　1本 数千万円・3ヶ月 → 3本 300万円・1.5〜2週間",
     "映画の群衆シーン　9,000万円 → 150万円（▲98%）",
     "米国の企業動画　1分あたり 約63万円 → 約38万円（▲40%・実測）"],GOLD,9.5);
  foot(s,"出所: 動画幹事・ムビサク・デジタルドロップ（制作費相場／撮影費は制作費の35〜40%）／ ムービーインパクト・各社プレスリリース（AI導入の削減事例）／ Vidico（米国の1分単価）。用途別の削減率は、工程別の削減率（企画▲50%・撮影▲80%・機材▲80%・出演▲90%・編集▲50%・諸経費▲30%）を費用構成に当てた当社試算です");
}
/* ═══════════ 8. ビジネスモデル ═══════════ */
{
  const s = base(false);
  head(s, 3, "ビジネスモデル", "両面市場です。ただし②があるため、発注がゼロの初日からクリエイターに報酬を出せます");
  const rows=[
    hrow(["","入口","当社","出口","位置づけ"]),
    [{text:"①",options:{bold:true,color:NAVY}},"日本・海外の個人と中小事業者",{text:"当社プラットフォーム",options:{bold:true}},"中国の映像クリエイター",{text:"取引手数料",options:{bold:true,color:NAVY}}],
    ["","映像を作りたいが、中国に直接発注できない","要件定義テンプレート・AI翻訳・成果物の自動チェック・決済","制作パートナー経由で受注し、報酬を受け取る",""],
    [{text:"②",options:{bold:true,color:VERM}},"日本の発注企業",{text:"当社が受注し、配分",options:{bold:true}},"登録クリエイター",{text:"差益",options:{bold:true,color:VERM}}],
    ["","事業会社・広告代理店・制作会社","要件定義・品質保証・契約・与信・請求","再生数ゼロでも稼げる",""],
    [{text:"③",options:{bold:true,color:GOLD}},"①②で溜まる制作データ",{text:"内製化してモデル開発",options:{bold:true}},"プロダクト外販",{text:"ライセンス",options:{bold:true,color:GOLD}}],
    ["","指示→初稿→修正→承認／修正回数・検収通過率","工程のツール化・生成AI関連の特許取得","粗利率80%以上・人数に比例しない",""],
  ];
  table(s, M, 1.58, W, rows, [0.7,3.3,3.5,3.0,1.53], 9.5, 0.32);
  warn(s, M, 4.14, (W-0.3)/2, 1.24, "②が①のコールドスタートを解きます",
    ["両面市場の宿命は「クリエイターは発注がないと来ない、発注者はクリエイターがいないと来ない」。",
     "②は発注者を必要としません。案件を配ればクリエイターは集まり、その登録クリエイターが①の初期供給になります。"]);
  warn(s, M+(W-0.3)/2+0.3, 4.14, (W-0.3)/2, 1.24, "お金の流れ",
    ["発注者からの回収は Stripe。当社で資金を預からない収納代行型を前提としています。",
     "中国のクリエイターへの支払いは、中国の映像制作パートナー企業を経由。第三者と同条件・証憑を残す運用です。",
     "資金決済法の該当性は弁護士に確認中です。［確認事項］"]);
  const y2=5.56, w3=(W-0.6)/3;
  card(s, M,             y2, w3, 0.96, "アダルトは対象外です",
    ["受注する案件にも、①に載せる作品にも含めません。決済・法規制・ストア審査が理由です。"], VERM, 9.5);
  card(s, M+w3+0.3,      y2, w3, 0.96, "差別化の核心は価格ではありません",
    ["海外に安く出せること自体は誰でも知っています。やらない理由は「管理しきれないから」です。"], NAVY, 9.5);
  card(s, M+(w3+0.3)*2,  y2, w3, 0.96, "発注側の管理コストがゼロになる",
    ["日本語の要件定義・品質保証・契約・与信・請求。この一式を当社が引き受けます。"], GOLD, 9.5);
  foot(s, "クリエイター調達の設計は CHINA_SOURCING を参照");
}

/* ═══════════ 9. ユニットエコノミクス ═══════════ */
{
  const s = base(false);
  head(s, 3, "ユニットエコノミクス", "売上20億が何の積み上げなのかを、1本・1取引・1契約あたりで示します");
  s.addText("① 映像制作（②）— 1本あたり（平均単価50万円のとき）", { x:M, y:1.52, w:6.0, h:0.3, fontFace:F, fontSize:11, bold:true, color:INK, margin:0, isTextBox:true });
  const rowsA=[
    hrow(["","金額","備考"]),
    ["売上","50.0万","企業発注の中央値54万より保守的に設定"],
    ["個人クリエイターへの支払","▲12.0万","Bランク。有償テスト課題で確定させる"],
    ["一次レビュー報酬","▲3.0万","Aランクに委託"],
    ["AIツール・素材・レンダリング","▲2.0万",""],
    ["品質バッファ（作り直し）","▲1.5万","ここを原価から外さないこと"],
    [{text:"売上総利益",options:{bold:true,color:VERM}},{text:"31.5万（63%）",options:{bold:true,color:VERM}},{text:"計画は保守的に60%で置く",options:{bold:true}}],
  ];
  table(s, M, 1.88, 6.0, rowsA, [2.5,1.3,2.2], 9, 0.32);
  s.addText("② 越境C2C発注（①）— 1取引あたり", { x:M+6.3, y:1.52, w:5.7, h:0.3, fontFace:F, fontSize:11, bold:true, color:INK, margin:0, isTextBox:true });
  const rowsB=[
    hrow(["","金額","備考"]),
    ["発注者が支払う額（GMV）","9.0万","個人案件の相場レンジの中位［仮置き］"],
    [{text:"当社の取引手数料 18%",options:{bold:true,color:NAVY}},{text:"1.62万",options:{bold:true,color:NAVY}},"国内C2Cの約22%より低く置く"],
    ["決済手数料・インフラ","▲0.24万","Stripe等"],
    [{text:"売上総利益",options:{bold:true,color:NAVY}},{text:"1.38万（85%）",options:{bold:true,color:NAVY}},{text:"人が介在しないので件数に比例しない",options:{bold:true}}],
    [{text:"5期 年間3万件",options:{bold:true}},{text:"→ 4.86億",options:{bold:true,color:NAVY}},"GMV 27億 × 18%"],
  ];
  table(s, M+6.3, 1.88, 5.73, rowsB, [2.73,1.3,1.7], 9, 0.32);
  s.addText("③ ツール外販（③）— 1契約あたり", { x:M, y:4.12, w:6.0, h:0.3, fontFace:F, fontSize:11, bold:true, color:INK, margin:0, isTextBox:true });
  const rowsC=[
    hrow(["","年間単価","5期の契約数","5期の売上"]),
    [{text:"制作会社（法人）",options:{bold:true,color:GOLD}},"320万","250社",{text:"8.0億",options:{bold:true,color:GOLD}}],
    ["個人クリエイター","12万","2,100人","2.5億"],
    [{text:"合計",options:{bold:true}},"","",{text:"10.5億",options:{bold:true,color:GOLD}}],
  ];
  table(s, M, 4.48, 6.0, rowsC, [1.9,1.3,1.4,1.4], 9, 0.32);
  sec(s, M+6.3, 4.12, 5.73, "5期 売上20.2億の内訳");
  hbar(s, M+6.3, 4.50, 5.73, 0.34, 1.00, "ツール外販（③）", "10.5億", GOLD, 2.4);
  hbar(s, M+6.3, 4.88, 5.73, 0.34, 0.46, "C2C手数料（①）", "4.9億", NAVY, 2.4);
  hbar(s, M+6.3, 5.26, 5.73, 0.34, 0.46, "制作受託（②）", "4.8億", VERM, 2.4);
  warn(s, M, 5.62, W, 0.62, "76%が「人手に比例しない収益」です",
    ["①の手数料と③の外販は、件数や契約数が増えても人員が比例して増えません。だからSaaS寄りの評価（PSR 6〜8倍）で見ています。"]);
  foot(s, "制作の単価・原価は BUSINESS_PLAN 7-1。C2Cの手数料率・平均単価・件数、ツール外販の単価と契約数は、すべて未実測の［仮置き］です");
}

/* ═══════════ 10. 収益モデル ═══════════ */
{
  const s = base(false);
  head(s, 3, "収益モデル", "3本の柱。人手に比例しない収益（①③）を5期に76%まで上げます");
  const rows=[
    hrow(["","収益ライン","型","開始","5期の売上","備考"]),
    [{text:"P1",options:{bold:true,color:VERM}},{text:"映像制作の受注 → クリエイターへ配分",options:{bold:true}},"フロー","初日から",{text:"4.8億",options:{bold:true,color:VERM}},"粗利率60%。売上が人手に比例する"],
    [{text:"P2",options:{bold:true,color:NAVY}},{text:"越境C2C発注の取引手数料",options:{bold:true}},"ストック","6ヶ月目〜",{text:"4.9億",options:{bold:true,color:NAVY}},"手数料率18%［仮置き］。仲介業務を自動化したもの"],
    [{text:"P4",options:{bold:true,color:GOLD}},{text:"制作ツール・モデルの外販",options:{bold:true}},"ストック",{text:"2期〜",options:{bold:true}},{text:"10.5億",options:{bold:true,color:GOLD}},"粗利率80%以上。①の自動化機能をそのまま外販する"],
  ];
  table(s, M, 1.58, W, rows, [0.7,4.0,1.0,1.2,1.3,3.83], 9.5, 0.44);
  sec(s, M, 3.50, 6.0, "①で自動化する4つの機能");
  const y=3.86, w=(6.0-0.3)/2, h=0.92;
  card(s, M,          y,       w, h, "① 要件定義テンプレート", ["日本語で答えるだけで発注仕様になる"], NAVY, 9);
  card(s, M+w+0.3,    y,       w, h, "② AI翻訳", ["発注者とクリエイターのやり取りを双方向で"], NAVY, 9);
  card(s, M,          y+h+0.2, w, h, "③ 成果物の自動チェック", ["尺・解像度・指示との整合"], NAVY, 9);
  card(s, M+w+0.3,    y+h+0.2, w, h, "④ 決済・支払い", ["Stripeで回収、制作パートナー経由で支払う"], NAVY, 9);
  warn(s, M+6.3, 3.50, 5.73, 1.42, "この4機能が、そのままP4の商品になります",
    ["当社が仲介でやっている作業を、制作会社とクリエイターが自分で使える形にして売る。",
     "だから①とP4は別物ではなく、同じシステムの内側と外側です。2期から外販を始めるのはこのためです。"]);
  warn(s, M+6.3, 5.06, 5.73, 1.18, "手数料率18%は［仮置き］です",
    ["国内C2C（ココナラ等）の約22%より低く置いています。越境の壁を引き受ける対価としていくら取れるかは、PF公開後に実測します。"]);
  foot(s, "手数料率・発注件数・平均単価、ツール外販の契約数と単価は、すべて未実測の［仮置き］です。1期に実測して差し替えます");
}

/* ═══════════ 11. 日本IPを使った作品制作 ═══════════ */
{
  const s = base(false);
  head(s, 3, "日本IPを使った作品制作 — 4つの入口", "版権コストの安い順に着手します。D から始め、他社PFでの実績が出てから A へ");
  const rows=[
    hrow(["","対象IP","座組","版権コスト","出口"]),
    [{text:"D",options:{bold:true,color:VERM}},{text:"パブリックドメイン（青空文庫・古典）",options:{bold:true}},"権利処理が不要。単独で制作できる",{text:"ゼロ",options:{bold:true,color:VERM}},"他社PFに投入し、実績づくり"],
    [{text:"B",options:{bold:true,color:NAVY}},"自治体・企業のキャラクター","受託（②と同じ）。先方が権利者","ゼロ（先方負担）","自治体PR・企業広報・ふるさと納税"],
    [{text:"C",options:{bold:true,color:NAVY}},"個人作家・Web小説（なろう系・pixiv）","作家と直接レベニューシェア","ほぼゼロ（成功報酬型）","他社PFの課金枠へ供給"],
    [{text:"A",options:{bold:true,color:GOLD}},"中小出版社の既刊マンガ（未映像化作品）","原作使用許諾＋レベニューシェア","数万〜数十万／作品","他社PFの看板作品・海外展開"],
  ];
  table(s, M, 1.58, W, rows, [0.7,3.5,3.4,2.0,2.43], 9.5, 0.40);
  sec(s, M, 3.52, 6.0, "着手の順序 — 版権コストの安い順に積み上げる");
  const bw=1.32, by=3.90;
  box(s, M,             by+0.60, bw, 0.82, "D", "版権ゼロ", SOFT, VERM, MUTED, 13, 9);
  box(s, M+bw+0.18,     by+0.40, bw, 1.02, "B", "先方負担", SOFT, NAVY, MUTED, 13, 9);
  box(s, M+(bw+0.18)*2, by+0.20, bw, 1.22, "C", "成功報酬", SOFT, NAVY, MUTED, 13, 9);
  box(s, M+(bw+0.18)*3, by,      bw, 1.42, "A", "数万〜数十万", SOFT, GOLD, MUTED, 13, 9);
  warn(s, M+6.3, 3.52, 5.73, 1.40, "自社で配信面は持ちません",
    ["作った作品は他社のプラットフォーム（YouTube・TikTok・ショートドラマ各社）で稼ぎます。",
     "この作品群からの収益は5年計画に計上していません。①③の制作力とデータを作るための投資という位置づけです。"]);
  warn(s, M+6.3, 5.06, 5.73, 1.18, "IPホルダーはAI生成を警戒します",
    ["契約に「AI利用の可否と開示方法」を必ず明記します。JIAA調査でも受容条件1位は「AI利用が明記されている」37.6%。"]);
  foot(s, "出所: 日本動画協会 アニメ産業レポート（制作市場4,662億円・海外売上2兆1,700億円）／ JIAA「2026年インターネット広告に関するユーザー意識調査」");
}

/* ═══════════ 12. 政策も同じ方向を向いている ═══════════ */
{
  const s = base(false);
  head(s, 1, "政策も同じ方向を向いている", "国はコンテンツを輸出産業にすると決め、予算を3倍にした");
  img(s, "assets/image4.png", 10.48, 0.17, 2.41, 1.61);   // 松田さんが挿入（国会議事堂）
  const y0=1.78, h=1.44, w=(W-0.6)/3;
  stat(s, M,           y0, w, h, "20兆円", "コンテンツ海外売上 目標（2033年）", "経産省「エンタメ・クリエイティブ産業戦略2026」");
  stat(s, M+w+0.3,     y0, w, h, "3.5倍",  "経産省の財政支援規模", "令和6年度補正 101.1億円 → 令和7年度補正 350.2億円", NAVY);
  stat(s, M+(w+0.3)*2, y0, w, h, "+26%",   "アニメの海外売上（2024年）", "2兆1,700億円。市場全体は3兆8,400億円", GOLD);
  const y1=3.42, w2=(W-0.3)/2;
  card(s, M, y1, w2, 1.60, "AI政策",
    ["AI推進法（人工知能関連技術の研究開発及び活用の推進に関する法律）","2025年5月28日成立 ／ 6月4日公布。日本初のAI基本法。",
     "AI基本計画を2025年12月23日に閣議決定。内閣にAI戦略本部を設置。"], NAVY, 9.5);
  card(s, M+w2+0.3, y1, w2, 1.60, "当社が実際に狙える支援",
    ["東京都 創業助成事業 — 上限400万円・助成率2/3・最長2年","特許料等の減免 — 設立10年未満・資本金3億円以下なら1/3に軽減",
     "JLOX+ — 「制作の生産性向上に資するシステムの開発・実証」枠"], GOLD, 9.5);
  warn(s, M, 5.22, W, 1.02, "補助金は資金計画に算入していません",
    ["いずれも後払い（精算払い）で、入金が1年以上先になります。資金繰りの当てにはできません。",
     "取れた場合は上振れとして扱います。"]);
  foot(s, "出所: 経済産業省「エンタメ・クリエイティブ産業戦略2026」／ 内閣府 AI戦略 ／ 東京都中小企業振興公社 ／ 特許庁");
}
/* ═══════════ 13. 競合 ═══════════ */
{
  const s = base(false);
  head(s, 4, "競合 — 相手は2種類います", "クリエイター側は中国PF、発注者側は国内C2C。どちらとも正面からは戦いません");
  sec(s, M, 1.56, 6.0, "クリエイター側 — 各社が提示している分成率");
  hbar(s, M, 1.94, 6.0, 0.32, 0.90, "快手「灵感新纪元」", "最大90%", MUTED, 2.5);
  hbar(s, M, 2.30, 6.0, 0.32, 0.90, "抖音「漫画星河」", "純収益90%", MUTED, 2.5);
  hbar(s, M, 2.66, 6.0, 0.32, 0.80, "Bilibili「觉醒计划」", "最大80%", MUTED, 2.5);
  hbar(s, M, 3.02, 6.0, 0.32, 0.50, "抖音 AI実写短劇", "40〜60%", MUTED, 2.5);
  hbar(s, M, 3.38, 6.0, 0.32, 0.00, "当社", "―", VERM, 2.5);
  s.addText("当社の行が空欄であることが、このページの主張です。", { x:M, y:3.76, w:6.0, h:0.3, fontFace:F, fontSize:9.5, bold:true, color:VERM, margin:0, isTextBox:true });
  warn(s, M+6.3, 1.56, 5.73, 1.34, "分成率では勝てません",
    ["トラフィックがゼロの新規PFが「うちに投稿してください」と言っても、経済合理性がありません。",
     "快手1億／百度10億級のトラフィックプールとは桁が違います。"]);
  warn(s, M+6.3, 3.06, 5.73, 1.24, "ただし2026年、隙間が開きました",
    ["中国のPFは純AIコンテンツの分成を圧縮し、最低保証を廃止。リソースは実写短劇へ移りました。",
     "ここが唯一の入口です。ただし方針が戻れば消える時限付きです。"]);
  sec(s, M, 4.34, W, "発注者側 — 国内C2Cが開けていない側を取ります");
  const rows=[
    hrow(["","ココナラ・ランサーズ・クラウドワークス","当社"]),
    [{text:"発注先",options:{bold:true,color:INK}},"国内のフリーランス",{text:"中国の映像クリエイター",options:{bold:true,color:NAVY}}],
    [{text:"越境発注",options:{bold:true,color:INK}},{text:"導線が無い。言語・決済・品質保証・契約が壁",options:{color:MUTED}},{text:"その壁をシステムで引き受ける",options:{bold:true}}],
    [{text:"手数料",options:{bold:true,color:INK}},"約22%","18%［仮置き］"],
  ];
  table(s, M, 4.66, W, rows, [1.7,5.2,5.13], 9.5, 0.38);
  foot(s, "出所: Bilibili「2026熱門AI漫劇/短劇創作平台」／ 网易「2026短劇分账新政」／ ココナラ・ランサーズ公開単価。条件は頻繁に変わるため、提携前に公式条件の確認が必要です");
}

/* ═══════════ 14. なぜクリエイターは当社に来るのか ═══════════ */
{
  const s = base(false);
  head(s, 4, "では、なぜクリエイターは当社に来るのか", "分成率ではなく、3つの別の理由で選ばれる設計にします");
  const y0=1.62, w=(W-0.6)/3, h=1.96;
  card(s, M,           y0, w, h, "再生数に関係なく収入がある",
    ["大手PFには無い仕組みです。","当社が受注して配分するので、再生数に関係なく報酬が出ます。",
     "①の越境発注が立てば、個人からの発注も同じ導線で受けられます。"], VERM, 9.5);
  card(s, M+w+0.3,     y0, w, h, "AIを冷遇しない",
    ["2026年、中国PFは純AIコンテンツの分成を圧縮し、最低保証を廃止しました。","リソースは実写短劇へ移っています。",
     "AI専業のクリエイターは相対的に冷遇され始めています。"], NAVY, 9.5);
  card(s, M+(w+0.3)*2, y0, w, h, "日本市場への窓",
    ["日本語の要件定義・稟議・与信・請求。","個人では越えられない壁を当社が代行します。",
     "日本の発注は単価が高く、支払いが確実です。"], GOLD, 9.5);
  warn(s, M, 3.80, W, 1.30, "発注者側は、国内C2Cが開けていない市場です",
    ["ココナラ・ランサーズ・クラウドワークスに、中国のクリエイターへ発注する導線はありません。",
     "言語・決済・品質保証・契約の4つが壁で、個人同士の直接取引が成立しないからです。当社はその4つを機能として持ちます。"]);
  warn(s, M, 5.24, W, 1.00, "だから、発注者は「後から」取ります",
    ["初日はクリエイター側だけを取りに行きます。②の企業案件が、その口実と原資になります。",
     "発注者の獲得は6ヶ月目のPF公開以降です。①②で取引のある相手から載せるので、広告費を先に張る必要がありません。"]);
  foot(s, "出所: ココナラ・ランサーズ公開単価 ／ 36Kr Japan（中国発アプリの日本シェア）。詳細は COMPETITORS.md");
}

/* ═══════════ 15. 課題と解決 ═══════════ */
{
  const s = base(false);
  head(s, 5, "課題と、その解決方法", "最大の課題は両面市場のコールドスタート。②の企業案件が、この輪を回り始める前に断ちます");
  const bw=2.30, bh=0.78, cy=1.58;
  box(s, M,            cy,        bw, bh, "発注がない", "", SOFT, MUTED, MUTED, 11, 9);
  arw(s, "r", M+bw+0.10, cy+0.21, 0.42, 0.36);
  box(s, M+bw+0.62,    cy,        bw, bh, "分配の原資が出ない", "", SOFT, MUTED, MUTED, 11, 9);
  arw(s, "r", M+bw*2+0.72, cy+0.21, 0.42, 0.36);
  box(s, M+(bw+0.62)*2, cy,       bw, bh, "クリエイターが去る", "", SOFT, MUTED, MUTED, 11, 9);
  arw(s, "r", M+bw*3+1.34, cy+0.21, 0.42, 0.36);
  box(s, M+(bw+0.62)*3, cy,       bw, bh, "供給が減る", "", SOFT, VERM, MUTED, 11, 9);
  s.addText("この輪が回り続けるのが、両面市場のコールドスタートです。② は発注者を必要としません。案件を配ればクリエイターは集まり、その登録クリエイターが①の初期供給になります。",
    { x:M, y:2.48, w:W, h:0.34, fontFace:F, fontSize:10, color:INKSOFT, valign:"middle", margin:0, isTextBox:true });
  const rows=[
    hrow(["残りの課題","解決方法"]),
    ["分成率で大手に勝てない","分成率では戦わない。企業案件・AIを冷遇しない方針・日本市場への窓の3点で選ばれる設計にする"],
    ["発注者を集められない","PF公開（6ヶ月目）まで投下しない。①②で取引のある制作会社・クリエイターを先に載せ、供給がある状態で開く"],
    ["制作の市場単価が下がる","3年の時限と見ている。①の自動化機能をツール外販（P4）へ移して逃げ切る"],
    ["中国本土から当社PFに接続できない可能性","投稿・決済の経路を設計段階で検証。国内向けミラーまたは提携PF経由の導線を用意する"],
    ["成果物の品質が担保できない","審査基準に組み込み、品質判定の自動化を特許①として出願。検収通過率と修正回数のデータを学習側に回す"],
  ];
  table(s, M, 2.92, W, rows, [3.2,8.83], 9.5, 0.44);
  warn(s, M, 5.30, W, 0.94, "受託制作のままでは上場しません",
    ["労働集約型の受託は、売上が人手に比例するため「規模の割に伸びない事業」と読まれます。",
     "だから追うべき指標は売上ではなく、人手に比例しない収益（①③）の比率です。5期で76%。"]);
  foot(s, "各課題の詳細と数値根拠は COMPETITORS ／ MOAT_TIMELINE ／ CHINA_SOURCING に記載");
}

/* ═══════════ 16. チーム ═══════════ */
{
  const s = base(false);
  head(s, 6, "チーム", "（記入予定）");
  const y0=1.62, w=(W-0.6)/3, h=1.62;
  card(s, M,           y0, w, h, "代表取締役",
    ["会社経営・コンサルティング経験","日本・中国・台湾をまたぐ越境実務","（詳細は［記入予定］）"], VERM, 10);
  card(s, M+w+0.3,     y0, w, h, "CTO／開発責任者", ["採用計画"], NAVY, 10);
  card(s, M+(w+0.3)*2, y0, w, h, "プラットフォーム責任者", ["採用計画"], GOLD, 10);
  warn(s, M, 3.44, (W-0.3)/2, 1.30, "中国の制作パートナー",
    ["［記入予定］（実在の映像制作会社と提携）",
     "クリエイターへの発注・支払いはこのパートナーを経由します。",
     "制作データと成果物の権利は、契約により日本側（当社）に帰属させます。"]);
  warn(s, M+(W-0.3)/2+0.3, 3.44, (W-0.3)/2, 1.30, "この章は記入予定です",
    ["代表の経歴と実績 ／ これから採用する職種・時期・採用チャネル ／ アドバイザー・顧問",
     "越境C2C発注PFとツール外販を同じシステムで作るため、1年目からエンジニアが必要です。"]);
  const rows=[
    hrow(["","1期","2期","3期","4期","5期"]),
    ["日本側 人員","6名","16名","30名","44名","60名"],
    ["中国側 登録クリエイター","8〜10名","15〜18名","25〜30名","45〜55名","70名前後"],
    [{text:"1人あたり人件費",options:{bold:true}},"500万","700万","800万","900万",{text:"1,000万",options:{bold:true}}],
  ];
  table(s, M, 4.98, W, rows, [3.0,1.8,1.8,1.8,1.8,1.83], 9.5, 0.32);
  foot(s, "1年目は6名体制（代表・エンジニア2・運営2・営業1）を想定しています");
}

/* ═══════════ 17. 事業計画 ═══════════ */
{
  const s = base(false);
  head(s, 7, "事業計画", "3期まで赤字が前提。通期黒字化は4期、上場申請は5期です");
  const labels=["1期 2027/9","2期 2028/9","3期 2029/9","4期 2030/9","5期 2031/9"];
  s.addChart(p.ChartType.bar, [
    { name:"売上高", labels, values:[36,179,522,1148,2018] },
    { name:"営業利益", labels, values:[-32,-67,-4,235,613] },
  ], {
    x:M, y:1.6, w:6.6, h:3.3,
    barDir:"col", barGrouping:"clustered",
    chartColors:[NAVY, VERM],
    catAxisLabelFontFace:F, catAxisLabelFontSize:9, catAxisLabelColor:MUTED,
    valAxisLabelFontFace:F, valAxisLabelFontSize:9, valAxisLabelColor:MUTED,
    valAxisMinVal:-200, valAxisMaxVal:2100,
    showValue:true, dataLabelFontFace:F, dataLabelFontSize:8, dataLabelColor:INKSOFT,
    showLegend:true, legendPos:"b", legendFontFace:F, legendFontSize:9,
    valGridLine:{ color:LINE, style:"solid", size:0.5 }, catGridLine:{ style:"none" },
    title:"売上高と営業利益の推移（単位 百万円・計画値）", showTitle:true,
    titleFontFace:F, titleFontSize:11, titleColor:INK,
  });
  const cx=M+6.9, cw=W-6.9;
  card(s, cx, 1.6, cw, 1.02, "1期 ― 基盤をつくる",
    ["PF開発と公開（6ヶ月目）。企業案件で2,700万、C2C手数料で900万。営業利益 ▲3,200万は計画通りの投資です。"], VERM, 9.5);
  card(s, cx, 2.74, cw, 0.9, "2〜3期 ― 投資期間",
    ["制作体制とツール外販に投下。赤字は2期に最大化（▲6,700万）し、3期はほぼ均衡（▲400万）まで戻ります。"], NAVY, 9.5);
  card(s, cx, 3.76, cw, 1.14, "4〜5期 ― 回収",
    ["4期に通期黒字化。5期に年商20億・営業利益6.1億（30.4%）。時価総額121〜161億の水準へ。"], GOLD, 9.5);
  const rows=[
    hrow(["","売上の内訳（百万円）","この期の到達点"]),
    ["1期","制作27 ／ C2C 9","制作54本・PF公開・登録100名"],
    ["2期","制作105 ／ C2C 54 ／ 外販20","ツール外販の初期契約／シリーズA 3億"],
    ["3期（N-2期）","制作200 ／ C2C 162 ／ 外販160","監査開始。赤字がほぼ均衡まで戻る"],
    ["4期（N-1期）","制作320 ／ C2C 324 ／ 外販504","通期黒字化。内部管理体制の構築"],
    [{text:"5期（N期）→ 2031年 上場",options:{bold:true,color:VERM}},{text:"制作480 ／ C2C 486 ／ 外販1,052",options:{bold:true}},{text:"売上20億・営業利益6.1億",options:{bold:true}}],
  ];
  table(s, M, 5.06, W, rows, [3.0,4.5,4.53], 10, 0.3);
  foot(s, "計画値。C2Cの手数料率・発注件数、ツール外販の契約数はすべて未実測の［仮置き］です。1期に実測して差し替えます。数字は plan_c2c.py が計算しています");
}

/* ═══════════ 18. 上場までの流れ ═══════════ */
{
  const s = base(false);
  head(s, 8, "上場までの流れ", "5期（2031年）での上場を逆算。N-2期の監査開始は3期・2028年10月です");
  const y0=1.62, w=(W-1.2)/5, h=1.50;
  card(s, M,             y0, w, h, "1期  2026/10-2027/9", ["・制作の受注開始","・PF開発と公開","・C2Cの手数料率を実測"], VERM, 9);
  card(s, M+w+0.3,       y0, w, h, "2期  2027/10-2028/9", ["・制作体制の拡大","・ツール外販の初期契約","・シリーズA 3億／監査法人SR"], NAVY, 9);
  card(s, M+(w+0.3)*2,   y0, w, h, "3期 N-2  2028/10-2029/9", ["・監査開始","・ツール外販の本格展開","・主幹事証券の選定"], NAVY, 9);
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
  warn(s, M, 4.96, W, 1.28, "ゴールは上場ではありません",
    ["グロースは2030年3月以降「上場5年経過後に時価総額100億円」の維持基準が新設されました。2031年上場なら2036年に100億円。",
     "当社の想定時価総額は121〜161億（中心141億）で、維持基準に対して41%のバッファがあります。"]);
  foot(s, "出所: 日本取引所グループ 上場維持基準。上場基準は改定が続くため、準備期に入る前に最新基準を再確認します");
}

/* ═══════════ 19. 出口とリターン ═══════════ */
{
  const s = base(false);
  head(s, 8, "出口とリターン", "5期の売上20億・営業利益6.1億を前提に、3手法で試算しています");
  const y0=1.62, h=1.52, w=(W-0.6)/3;
  stat(s, M,           y0, w, h, "82〜164億", "PER法", "当期純利益 約4.1億（実効税率33%）× PER 20〜40倍");
  stat(s, M+w+0.3,     y0, w, h, "121〜161億",  "PSR法", "売上20億 × PSR 6〜8倍。売上の76%が人手に比例しない収益なのでSaaS寄りで見る", NAVY);
  stat(s, M+(w+0.3)*2, y0, w, h, "60〜101億",  "EV/EBITDA法", "EBITDA 約6.7億 × 8.9〜15倍（情報通信業の中央値8.9倍）", GOLD);
  s.addText("中心値は 時価総額 141億円 ─ グロースの上場維持基準（2036年に100億円以上）に対し 41% のバッファ",
    { x:M, y:3.32, w:W, h:0.36, fontFace:F, fontSize:12.5, bold:true, color:VERM, valign:"middle", margin:0, isTextBox:true });
  const y1=3.84, w2=(W-0.3)/2;
  card(s, M, y1, w2, 1.46, "M&A で売却する場合",
    ["3期（売上5.2億・ほぼ均衡）… 10〜25億。買い手が評価するのはクリエイター網と技術。",
     "4期（売上11.5億・営業利益2.4億）… 30〜60億 ／ 5期（売上20億）… 121〜161億。",
     "戦略的買い手（大手代理店・制作会社・テレビ局）ならシナジー価格が乗ります。"], NAVY, 9.5);
  card(s, M+w2+0.3, y1, w2, 1.46, "シード投資家のリターン",
    ["ESOP10%・シリーズA・IPO公募20%で希薄化後、上場後のシード持分は 14.5%。",
     "時価総額121億 → 12.4倍 ／ 141億 → 14.4倍 ／ 161億 → 16.5倍（出資から約4.9年）。",
     "上場時の創業者持分は 42%前後。時価総額141億なら評価額 約59億。"], GOLD, 9.5);
  warn(s, M, 5.46, W, 0.78, "すべて「成功した場合」の試算です",
    ["2025年のグロースIPOは18社（前年34社から半減）で、IPO市場そのものが縮んでいます。倍率は市況で変動します。"]);
  foot(s, "出所: M&A総研（業種別EV/EBITDA倍率）／ みつきコンサルティング（メディア・コンテンツ業界のM&A）／ EY Japan（2026年以降のIPO市場）／ FiNX（グロース維持基準の制度化）");
}

/* ═══════════ 20. マイルストーン ═══════════ */
{
  const s = base(false);
  head(s, 9, "マイルストーン", "各フェーズは「ゲート条件」で区切ります。満たさない限り、次へは進みません");
  const rows=[
    hrow(["時期","やること","◆ 次へ進むゲート条件"]),
    ["〜2026/12","法人設立・PF要件定義・中国パートナーとの契約","PF仕様の確定／法務の見解書（資金決済法）／パートナー契約の締結"],
    ["2027/1-3","制作の受注開始／PF開発",{text:"制作 累計5本・粗利率60%／ディレクター時間 8時間",options:{bold:true,color:VERM}}],
    ["2027/4-9","PF公開（6ヶ月目）・発注者の獲得開始・D案IPの投入","制作 1期54本／登録100名・成約100件／手数料率と平均単価の初回実測"],
    ["2期","制作体制の拡大・ツール外販の立ち上げ","ツール外販 法人8社／シリーズA 3億／監査法人ショートレビュー"],
    ["3期","赤字の縮小・ツール外販の本格展開","人手に比例しない収益62%以上／監査開始"],
    ["4期","通期黒字化・内部管理体制の構築","通期黒字化／人手に比例しない収益72%／流通株式25%の設計合意"],
    [{text:"5期",options:{bold:true,color:VERM}},{text:"上場申請",options:{bold:true}},{text:"年商20億・営業利益6.1億／時価総額141億",options:{bold:true}}],
  ];
  table(s, M, 1.58, W, rows, [1.6,4.6,5.83], 9.5, 0.38);
  warn(s, M, 4.90, W, 1.34, "最優先で実測するのは「手数料率と平均単価」です",
    ["［仮置き］手数料率18%・平均単価9万円で、5期のC2C売上4.9億を置いています。ここが半分なら2.5億です。",
     "PF公開直後（2027/4-9）に必ず測ってください。以降のすべての売上計画が、この2つの数字に乗っています。"]);
  foot(s, "ゲート条件を満たさない場合は次フェーズに進まず、前提を引き直します。詳細は ROADMAP.md");
}

/* ═══════════ 21. 資金計画 ═══════════ */
{
  const s = base(false);
  head(s, 10, "資金計画", "調達目標 1.5億円。融資を使わず、全額をエクイティで調達します");
  sec(s, M, 1.52, 6.3, "1年目の使途（単位 万円・合計 9,380万）");
  const items=[["人件費（6名）",3000,VERM],["PF開発（越境C2C発注 初期版）",1500,NAVY],["ツール外販の開発着手",1200,GOLD],
    ["制作事業の運転資金",800,VERM],["営業・マーケティング",600,VERM],["オフィス・SaaS・その他",480,MUTED],
    ["法務（資金決済法・越境契約）",400,MUTED],["設立・機材・その他初期",400,MUTED],
    ["中国パートナー提携・渡航",300,MUTED],["採用費",300,MUTED],["インフラ・決済（Stripe等）",200,MUTED],
    ["特許出願（2件）・データ基盤",200,MUTED]];
  items.forEach(function(it,i){ hbar(s, M, 1.88+i*0.33, 6.3, 0.30, it[1]/3000, it[0], String(it[1]), it[2], 3.2); });
  const y1=1.88, w2=W-6.9;
  stat(s, M+6.9,                y1, (w2-0.3)/2, 1.44, "800万", "資本金（代表個人が直接出資）", "1,000万未満に抑え、初年度の消費税課税事業者化を回避", GOLD);
  stat(s, M+6.9+(w2-0.3)/2+0.3, y1, (w2-0.3)/2, 1.44, "1.42億", "シード（創業時）", "放出20〜27%を想定。J-KISSでの価格先送りも選択肢", NAVY);
  warn(s, M+6.9, 3.50, w2, 1.48, "1.5億は「1年目の使途」ではありません",
    ["1年目に使うのは 9,380万。残り約5,600万は2期への持ち越しです。",
     "PF開発を初期版に絞り、広告費を先に張らない設計にしたぶん、2期へ厚く回せています。",
     "シリーズA 3億は2期の実績を見てから臨めます。"]);
  warn(s, M+6.9, 5.10, w2, 1.14, "追加調達はシリーズA 3億のみ。累計4.5億です",
    ["①③は人手に比例しないので、規模を追うための大型調達が要りません。シリーズB以降は想定していません。"]);
  s.addText("［仮置き］C2C発注の件数と手数料率が未実測のため、P2の売上の精度が最も低い数字です。PF公開後に実測して増減させます。",
    { x:M, y:5.90, w:6.3, h:0.34, fontFace:F, fontSize:9, color:MUTED, valign:"top", margin:0, isTextBox:true });
  foot(s, "※ 融資は使いません。補助金は後払いのため資金繰りに算入していません。全額をエクイティで調達します");
}

/* ═══════════ 22. リスクと対策 ═══════════ */
{
  const s = base(false);
  head(s, 11, "リスクと対策", "影響度と発生確率で並べています。上の3つが、この事業の生死を分けます");
  const rows=[
    hrow(["#","影響度","発生確率","リスク","対策"]),
    [{text:"1",options:{bold:true}},{text:"高",options:{bold:true,color:VERM}},{text:"高",options:{bold:true,color:VERM}},{text:"制作の市場単価が下がる",options:{bold:true}},"3年の時限と見ている。①の自動化機能をツール外販（P4）へ移して逃げ切る"],
    [{text:"2",options:{bold:true}},{text:"高",options:{bold:true,color:VERM}},{text:"中",options:{color:VERM}},{text:"発注者が集まらない",options:{bold:true}},"PF公開まで投下しない。①②で取引のある相手を先に載せ、供給がある状態で開く。伸びなければ企業案件に軸足を戻す"],
    [{text:"3",options:{bold:true}},{text:"高",options:{bold:true,color:VERM}},{text:"中",options:{color:VERM}},{text:"シリーズA 3億が入らない",options:{bold:true}},"ツール外販の開発を止めて制作に全振り。2期の赤字は▲6,700万→▲1,000万台まで縮む"],
    ["4",{text:"高",options:{bold:true,color:VERM}},"中",{text:"資金決済法の該当性",options:{bold:true}},"収納代行型（当社で預からない）を前提にPF設計の前に弁護士へ確認。法務費用400万を初年度に計上済み"],
    ["5","高","低","営業・エンジニアが採用できない","2次受け（代理店経由）を主軸に置けば律速がディレクターに移り、採用難易度が下がる"],
    ["6","中","中","中国の制作パートナーへの依存","支払いと品質保証を1社に依存しない。2社目の提携を2期までに確保する"],
    ["7","中","中","中国本土から当社PFに接続できない","設計段階で検証。国内向けミラーまたは提携PF経由の導線を用意"],
    ["8","中","低","クリエイターの離脱","登録は常に稼働数の1.5倍。春節（1〜2月）の稼働低下も計画に織り込み済み"],
  ];
  table(s, M, 1.58, W, rows, [0.5,0.9,1.0,3.6,6.03], 9, 0.42);
  warn(s, M, 5.42, W, 0.82, "1と2は「事業そのもの」のリスクです",
    ["3〜8が全部外れても、制作受託（②）は残ります。プラットフォームが伸びなくても事業が消えない構造にしてあります。"]);
  foot(s, "全リスクと対策は BUSINESS_PLAN ／ MOAT_TIMELINE ／ CHINA_SOURCING に記載しています");
}

/* ═══════════ 23. クロージング ═══════════ */
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
  s.addText("制作単価が下がり切るまでの時限", { x:M+w+0.3, y:y+0.62, w, h:0.3, fontFace:F, fontSize:11, color:ONORG, valign:"middle", margin:0, isTextBox:true });
  s.addText("2031年", { x:M+(w+0.3)*2, y, w, h:0.6, fontFace:F, fontSize:30, bold:true, color:PAPER, valign:"middle", margin:0, isTextBox:true });
  s.addText("東証グロース上場", { x:M+(w+0.3)*2, y:y+0.62, w, h:0.3, fontFace:F, fontSize:11, color:ONORG, valign:"middle", margin:0, isTextBox:true });
}

/* ═══════════ 24. 日本は一度、これをやっている ═══════════ */
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


p.writeFile({ fileName: "deck.pptx" }).then(function(){ console.log("deck.pptx"); });
