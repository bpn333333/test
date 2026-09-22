const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE";               // 13.333 x 7.5
p.author = "AI映像制作事業";
p.title  = "投資家向け企画書";

const INK="16161A", PAPER="FFFFFF", SOFT="FCE5CD", VERM="B3121B",
      GOLD="C9962C", NAVY="2A3563", MUTED="6E6E76", LINE="DCD9D4",
      INKSOFT="3A3A42", ONDARK="EDEBE7", TEAL="1F6F63",
      ORANGE="D9601A", ONORG="FBE2D2",
      /* Ver1.0（松田さん配色）から取り込み */
      SOFT2="FFF2CC", BAR="D9D2E9", TITLEBG="FF9900";
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
function stat(s, x, y, w, h, big, label, note, col, bigSize, bg){
  s.addShape(p.ShapeType.rect, { x, y, w, h, fill:{color:bg||SOFT} });
  s.addText(big, { x:x+0.26, y:y+0.18, w:w-0.52, h:0.66, fontFace:F, fontSize:bigSize||27, bold:true,
    color:col||VERM, valign:"middle", margin:0, isTextBox:true });
  s.addText(label, { x:x+0.26, y:y+0.86, w:w-0.52, h:0.28, fontFace:F, fontSize:11, bold:true,
    color:INK, valign:"middle", margin:0, isTextBox:true });
  if(note) s.addText(note, { x:x+0.26, y:y+1.16, w:w-0.52, h:h-1.3, fontFace:F, fontSize:9,
    color:MUTED, valign:"top", lineSpacingMultiple:1.2, margin:0, isTextBox:true });
}
function card(s, x, y, w, h, title, lines, accent, fs, bg){
  s.addShape(p.ShapeType.rect, { x, y, w, h, fill:{color:bg||SOFT} });
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
  s.addShape(p.ShapeType.rect, { x:M, y:2.82, w:11.90, h:1.51, fill:{color:TITLEBG} });
  s.addText("次世代AI映像制作会社の設立投資案件", { x:M+0.28, y:2.82, w:11.62, h:1.51, fontFace:F, fontSize:40, bold:true,
    color:PAPER, valign:"middle", margin:0, isTextBox:true });
  s.addText("東アジアを21世紀のハリウッドにするためのAI映像制作ハブとするAI映像制作会社のシード投資のご案内",
    { x:M, y:4.61, w:11.90, h:0.50, fontFace:F, fontSize:15, color:ONDARK, valign:"middle", margin:0, isTextBox:true });
  s.addText("投資家向け企画書  ／  2026年9月", { x:M, y:6.48, w:7, h:0.36, fontFace:F, fontSize:12, color:ONORG, valign:"middle", margin:0, isTextBox:true });
  s.addText("新設法人（株式会社・仮称）", { x:M, y:6.84, w:7, h:0.36, fontFace:F, fontSize:12, color:ONORG, valign:"middle", margin:0, isTextBox:true });
}

/* ═══════════ 2. エグゼクティブサマリー ═══════════ */
{
  const s = base(false);
  head(s, 0, "エグゼクティブサマリー", "中華圏の最先端技術に日本のクオリティーコントロールとIPを融合させ、世界市場を取りに行く企業を設立");
  lede(s, 1.44, ["5年後・2031年、東証グロース市場への上場を目指す。",
    "日本企業から映像制作を受注し、中国を中心とする登録クリエイターで作る。制作データを特許とモデルに変える。"]);
  const y0=2.46, h=1.40, w=(W-0.6)/3;
  stat(s, M,           y0, w, h, "社員54名", "5期の体制で、年商82.5億", "売上/社員 1.53億。制作は業務委託と自動化で回す", VERM);
  stat(s, M+w+0.3,     y0, w, h, "3本立て",   "収益の柱", "① AI映像制作 ② 特許・制作用ツールの外販（2期〜）③ 越境C2C発注の手数料（6ヶ月目〜）", NAVY);
  stat(s, M+(w+0.3)*2, y0, w, h, "1.5億円",   "今回の調達目標", "追加はシリーズA 3億のみ。累計4.5億で上場まで届く設計", GOLD);

  s.addShape(p.ShapeType.rect, { x:M, y:4.00, w:W, h:0.92, fill:{color:SOFT2} });
  s.addText("投資の期待値", { x:M+0.26, y:4.06, w:2.2, h:0.28, fontFace:F, fontSize:11, bold:true, color:INK, margin:0, isTextBox:true });
  s.addText("シード1.42億 → 上場後持分14.5%（ESOP10%・シリーズA・IPO公募20%で希薄化後）。出資から約4.9年",
    { x:M+0.26, y:4.40, w:2.4, h:0.46, fontFace:F, fontSize:8, color:MUTED, valign:"top", lineSpacingMultiple:1.2, margin:0, isTextBox:true });
  const ex=[["18.7倍","183億（ライン別倍率・保守）"],["23.7倍","232億（ライン別倍率）"],["25.3倍","248億（全社PSR3倍）"]];
  ex.forEach(function(e,i){
    const x=M+2.9+i*3.05;
    s.addText(e[0], { x, y:4.06, w:1.3, h:0.42, fontFace:F, fontSize:19, bold:true, color:VERM, valign:"middle", margin:0, isTextBox:true });
    s.addText(e[1], { x, y:4.50, w:2.9, h:0.30, fontFace:F, fontSize:8.5, color:MUTED, valign:"middle", margin:0, isTextBox:true });
  });

  const y1=5.06, h2=1.18, w2=(W-0.6)/3;
  card(s, M,            y1, w2, h2, "何をするか",
    ["① 日本企業から映像制作を受注し、中国を中心とする登録クリエイターに配分する。",
     "② 溜まった制作データで特許を取得し、チェックポイント・LoRA・制作用ツールを外販する。",
     "③ 個人・中小の越境発注を、自動化したプラットフォームで受ける。"], VERM, 8.5, SOFT2);
  card(s, M+w2+0.3,     y1, w2, h2, "なぜ勝てるか",
    ["生成AIで制作原価は下がったが、日本企業の発注価格は下がっていない。この差が粗利。",
     "日本企業は中華圏に直接発注しない。言語・商習慣・品質保証・契約が壁。",
     "その壁を引き受けることが商品。"], NAVY, 8.5, SOFT2);
  card(s, M+(w2+0.3)*2, y1, w2, h2, "どこへ向かうか",
    ["3期に黒字化、5年目に年商82.5億・営業利益20.6億（24.9%）。",
     "売上の80%を「人手に比例しない収益」にする。社員を増やさずに伸びる形をつくる。"], GOLD, 8.5, SOFT2);
  foot(s, "収支は［仮置き］を含む計画値です。投資の期待値は計画達成時の試算であり、利回りの保証ではありません。倍率は市況で変動します");
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
  head(s, 2, "市場規模", "本丸は国内の映像制作市場です。ここは推計ではなく実測値があります");
  const y0=1.58, h=1.52, w=(W-0.6)/3;
  stat(s, M,           y0, w, h, "4,580億円", "① 国内 動画制作サービス市場（2025年度予測）", "2024年度 4,238億円 → 2027年度 5,400億円【実測・矢野経済研究所】", VERM);
  stat(s, M+w+0.3,     y0, w, h, "6,300億円", "② 動画コンテンツビジネス市場（2025年度予測）", "動画編集ソフト・配信PF・ライブ配信・アニメ制作。①とは別枠。ツール外販が面する市場【実測・矢野経済研究所】", NAVY);
  stat(s, M+(w+0.3)*2, y0, w, h, "6,800億円", "③ スキルシェア市場（2028年予測）", "個人の発注が集まる場。C2Cが面する市場【推計・動画の内訳は非開示】", GOLD);
  const rows=[
    hrow(["","当社が取りに行く帯","発注者","現状の制作費","AI導入後","なぜここか"]),
    [{text:"①",options:{bold:true,color:VERM}},{text:"企業VP・会社紹介",options:{bold:true}},"法人","50〜150万円","18〜52万円","フル生成AIが成立。撮影が消えて原価が半分以下になる"],
    [{text:"①",options:{bold:true,color:VERM}},{text:"展示会・イベント映像",options:{bold:true}},"法人","20〜100万円","6〜30万円","ループ素材は特に効く。閑散期を埋める"],
    [{text:"③",options:{bold:true,color:GOLD}},{text:"PR素材・SNS縦型",options:{bold:true}},"個人・中小","10〜50万円","2〜10万円","C2Cの主戦場。量産前提で件数が出る"],
    ["","映画・テレビCM","—","3〜5億／1,000万〜1億","▲20〜50%","桁は変わらない。当社は取りに行かない"],
  ];
  table(s, M, 3.30, W, rows, [0.6,2.5,1.4,2.1,1.6,3.83], 9.5, 0.36);
  warn(s, M, 5.22, (W-0.3)/2, 1.02, "動画広告市場は載せていません",
    ["広告の出稿額であって、映像制作の発注額ではありません。当社の対象市場ではないので外しました。"]);
  warn(s, M+(W-0.3)/2+0.3, 5.22, (W-0.3)/2, 1.02, "③のうち動画が何割かは、公表されていません",
    ["ココナラ・ランサーズとも、カテゴリ別の流通高を開示していません。6,800億円を当社の対象市場として使わないこと。",
     "個人案件は件数と単価を1期に実測して置き換えます。"]);
  foot(s, "出所: 矢野経済研究所（動画コンテンツビジネスに関する調査2025。①のBtoB動画制作サービスは②の6,300億円に含まれません）／ Business Insider Japan（スキルシェア市場2028年予測）／ Vidico（米国の1分単価）。AI後の単価は工程別削減率からの当社試算です");
}

/* ═══════════ 6. 企業案件と個人案件 — 発注市場の規模 ═══════════ */
{
  const s = base(false);
  head(s, 2, "企業案件と個人案件 — 発注市場の規模", "「誰がお金を払うのか」で見ると、法人と個人では市場の性質がまったく違います");
  const w3=(W-0.6)/3, y0=1.50, h0=1.50;
  stat(s,M,            y0,w3,h0,"4,580億円","① 企業案件｜法人が発注する市場",
    "国内動画制作サービス市場（2025年度予測）。2024年度 4,238億円 → 2027年度 5,400億円\n【実測値・矢野経済研究所】",VERM,26);
  stat(s,M+w3+0.3,     y0,w3,h0,"6,800億円","③ 個人案件｜個人が発注する市場",
    "スキルシェア市場全体の2028年予測。動画がこのうち何割かは公表されていません\n【推計・内訳は非開示】",GOLD,26);
  stat(s,M+(w3+0.3)*2, y0,w3,h0,"2兆894億円","参考｜個人が「受け取る」市場",
    "クリエイターエコノミー（2024年）。これは発注市場ではなく報酬市場です。\n【混同しないこと】",MUTED,26);
  sec(s,M,3.14,W,"同じ「1本の動画」でも、取引の形が違います");
  const rows=[
    hrow(["","① 企業案件（法人が発注）","③ 個人案件（個人が発注）"]),
    [{text:"1件あたり単価",options:{bold:true,color:INK}},{text:"20万〜200万円（制作会社）／代理店経由は100万〜1,000万円",options:{color:VERM,bold:true}},{text:"5,000円〜100万円。簡易編集は1,000円台も",options:{color:GOLD,bold:true}}],
    [{text:"発注者",options:{bold:true,color:INK}},"事業会社の広報・マーケ部門／広告代理店／制作会社","個人事業主・小規模店舗・YouTuber・配信者"],
    [{text:"取引の場",options:{bold:true,color:INK}},"相見積 → 稟議 → 発注書 → 検収 → 請求","ココナラ・ランサーズ・クラウドワークス（PFが仲介）"],
    [{text:"与信・請求",options:{bold:true,color:INK}},{text:"必要。ここが個人クリエイターには越えられない壁",options:{bold:true}},"原則プラットフォームが代行するため不要"],
    [{text:"当社の位置づけ",options:{bold:true,color:INK}},{text:"主軸。当社が受注して配分する",options:{bold:true,color:VERM}},{text:"第3の柱。自動化したPFで受ける",options:{color:GOLD}}],
  ];
  table(s,M,3.46,W,rows,[1.9,5.1,5.03],9.5,0.40);
  warn(s,M,5.96,W,0.88,"個人の発注市場は「小さい」のではなく「測られていない」",
    ["ココナラ・ランサーズとも、動画カテゴリの流通高を開示していません。6,800億円はスキルシェア全体の数字です。",
     "だから売上の主軸は法人（①）に置き、個人（③）は自動化したPFで薄く広く取ります。件数と単価は1期に実測します。"],9.5);
  foot(s,"出所: 矢野経済研究所（動画コンテンツビジネス調査2025）／ Business Insider Japan（スキルシェア市場2028年予測）／ クリエイターエコノミー協会（2025年版調査）／ ココナラ・ランサーズ公開単価。企業案件は実測値、個人案件は推計値です");
}

/* ═══════════ 7. どんな場面で発注が起きるのか ═══════════ */
{
  const s = base(false);
  head(s, 2, "どんな場面で発注が起きるのか — Where the demand comes from",
       "法人と個人で、依頼される映像はまったく違います。単価も尺も頻度も違います");
  sec(s, M, 1.50, 5.9, "① 企業案件｜法人が発注する — Corporate");
  const rowsA=[
    hrow(["場面 / Scene","単価","尺","頻度"]),
    [{text:"会社紹介  Company profile",options:{bold:true}},{text:"50〜150万",options:{bold:true,color:VERM}},"2〜5分","数年に1回"],
    [{text:"採用  Recruiting",options:{bold:true}},"40〜120万","2〜3分","毎年"],
    ["商品・サービス紹介  Product demo","30〜100万","1〜3分","製品ごと"],
    ["展示会ループ  Trade show loop","20〜60万","30秒〜2分","催事ごと"],
    ["社内研修・マニュアル  Training","20〜80万","3〜10分","随時"],
    ["IR・株主向け  Investor relations","50〜200万","3〜8分","年1回"],
  ];
  table(s, M, 1.82, 5.9, rowsA, [2.6,1.1,0.9,1.3], 9, 0.34);
  sec(s, M+6.2, 1.50, W-6.2, "③ 個人案件｜個人・中小が発注する — Individual & SMB");
  const rowsB=[
    hrow(["場面 / Scene","単価","尺","頻度"]),
    [{text:"SNS広告・縦型  Social ads",options:{bold:true}},{text:"1〜30万",options:{bold:true,color:GOLD}},"15〜60秒","毎月"],
    [{text:"店舗紹介  Shop introduction",options:{bold:true}},"3〜30万","1〜2分","開業時"],
    ["ウエディング  Wedding","5〜20万","3〜7分","一生に1回"],
    ["終活・記念  Memorial","5〜20万","3〜10分","一生に1回"],
    ["教材・オンライン講座  Course","3〜50万","5〜30分","講座ごと"],
    [{text:"クラウドファンディング  Crowdfunding",options:{bold:true}},{text:"10〜100万",options:{bold:true,color:GOLD}},"2〜4分","企画ごと"],
  ];
  table(s, M+6.2, 1.82, W-6.2, rowsB, [2.8,1.1,0.9,1.03], 9, 0.34);
  warn(s, M, 4.34, (W-0.3)/2, 1.06, "法人は「高く・少なく・止まらない」",
    ["単価が高く件数が少ない。稟議と検収があるぶん発注は途切れにくい。当社が受注して配分します。"]);
  warn(s, M+(W-0.3)/2+0.3, 4.34, (W-0.3)/2, 1.06, "個人は「安く・多く・波がある」",
    ["単価は低いが件数が出る。上限は100万円まで。人が介在すると採算が合わないので、自動化したPFで受けます。"]);
  const y2=5.60, w4=(W-0.9)/4;
  card(s, M,             y2, w4, 0.64, "共通するのは「尺が短い」", [], VERM, 8.5);
  card(s, M+w4+0.3,      y2, w4, 0.64, "実写が要らない場面が多い", [], NAVY, 8.5);
  card(s, M+(w4+0.3)*2,  y2, w4, 0.64, "だからフル生成AIが効く", [], GOLD, 8.5);
  card(s, M+(w4+0.3)*3,  y2, w4, 0.64, "修正のやり取りが資産になる", [], VERM, 8.5);
  foot(s, "単価・尺・頻度は業界相場と公開単価からの［仮置き］です。1期に実測して差し替えます。出所: 動画幹事・ムビサク（法人相場）／ ココナラ・ランサーズ公開単価（個人相場）");
}

/* ═══════════ 8. AI導入で、制作費はいくらになり、いくら浮くのか ═══════════ */
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
/* ═══════════ 9. ビジネスモデル ═══════════ */
{
  const s = base(false);
  head(s, 3, "ビジネスモデル", "主軸は映像制作。そこで溜まるデータをツールに変え、余力を越境C2Cで受けます");
  const rows=[
    hrow(["","入口","当社","出口","位置づけ"]),
    [{text:"①",options:{bold:true,color:VERM}},"日本の発注企業",{text:"当社が受注し、配分する",options:{bold:true}},"登録クリエイター",{text:"主軸",options:{bold:true,color:VERM}}],
    ["","事業会社・広告代理店・制作会社","要件定義・品質保証・契約・与信・請求","中国を中心に、案件で稼ぐ",""],
    [{text:"②",options:{bold:true,color:GOLD}},"①で溜まる制作データ",{text:"内製化してツール化",options:{bold:true}},"チェックポイント・LoRA・制作ツール",{text:"第2の柱",options:{bold:true,color:GOLD}}],
    ["","指示→初稿→修正→承認／検収通過率","工程の自動化・生成AI関連の特許取得","粗利率80%・人数に比例しない",""],
    [{text:"③",options:{bold:true,color:NAVY}},"日本・海外の個人と中小事業者",{text:"越境C2C発注プラットフォーム",options:{bold:true}},"中国の映像クリエイター",{text:"第3の柱",options:{color:NAVY}}],
    ["","中国に直接発注しない／できない","②のツールをそのまま発注導線に使う","制作パートナー経由で受注",""],
  ];
  table(s, M, 1.58, W, rows, [0.7,3.3,3.5,3.0,1.53], 9.5, 0.32);
  warn(s, M, 4.14, (W-0.3)/2, 1.24, "②と③は、同じシステムの内側と外側です",
    ["①の仲介で当社がやっている作業（要件定義・翻訳・自動チェック・決済）をツール化したものが②。",
     "そのツールを外部の発注者に開放したものが③。先に①があるから、②も③も成立します。"]);
  warn(s, M+(W-0.3)/2+0.3, 4.14, (W-0.3)/2, 1.24, "お金の流れ",
    ["③の回収は Stripe。当社で資金を預からない収納代行型を前提としています。",
     "中国のクリエイターへの支払いは、中国の映像制作パートナー企業を経由。第三者と同条件・証憑を残す運用です。",
     "資金決済法の該当性は弁護士に確認中です。［確認事項］"]);
  const y2=5.56, w3=(W-0.6)/3;
  card(s, M,             y2, w3, 0.96, "アダルトは対象外です",
    ["受注する案件にも、③に載せる作品にも含めません。決済・法規制・ストア審査が理由です。"], VERM, 9.5, SOFT2);
  card(s, M+w3+0.3,      y2, w3, 0.96, "差別化の核心は価格ではありません",
    ["海外に安く出せること自体は誰でも知っています。やらない理由は「管理しきれないから」です。"], NAVY, 9.5, SOFT2);
  card(s, M+(w3+0.3)*2,  y2, w3, 0.96, "発注側の管理コストがゼロになる",
    ["日本語の要件定義・品質保証・契約・与信・請求。この一式を当社が引き受けます。"], GOLD, 9.5, SOFT2);
  foot(s, "クリエイター調達の設計は CHINA_SOURCING を参照");
}

/* ═══════════ 10. AXで原価が変わる ═══════════ */
{
  const s = base(false);
  head(s, 3, "AXが、この事業の利益率を作ります",
       "同じ売上・同じ人数でも、1本あたりのディレクション時間が1/4になれば、原価が変わります");
  lede(s, 1.46, ["制作ディレクションは業務委託。成果物単位の支払です。",
    "だから作業時間が1/4になれば、1本あたりの支払も1/4になります。人を減らす話ではなく、原価の話です。"]);
  const rows=[
    hrow(["AX倍率","ディレクション費／本","1本あたり原価","粗利率","5期の営業利益","営業利益率"]),
    [{text:"1.0倍（AXなし）",options:{bold:true}},"20.0万（8時間相当）","35.5万","40.8%","+3.8億",{text:"4.6%",options:{bold:true,color:MUTED}}],
    ["2.0倍","10.0万","25.5万","57.5%","+15.0億","18.1%"],
    ["3.0倍","6.7万","22.2万","63.1%","+18.7億","22.6%"],
    [{text:"4.0倍（計画）",options:{bold:true,color:VERM}},{text:"5.0万（2時間相当）",options:{bold:true,color:VERM}},{text:"20.5万",options:{bold:true,color:VERM}},{text:"65.8%",options:{bold:true,color:VERM}},{text:"+20.6億",options:{bold:true,color:VERM}},{text:"24.9%",options:{bold:true,color:VERM}}],
  ];
  table(s, M, 2.62, W, rows, [2.2,2.6,1.9,1.5,1.9,1.93], 10, 0.44);
  sec(s, M, 4.66, 6.0, "1本あたりの原価（単価60万・AX4倍）");
  hbar(s, M, 5.02, 6.0, 0.32, 0.60, "中国クリエイターへの支払", "12.0万", BAR, 3.0);
  hbar(s, M, 5.38, 6.0, 0.32, 0.25, "制作ディレクション（業務委託）", "5.0万", VERM, 3.0);
  hbar(s, M, 5.74, 6.0, 0.32, 0.10, "ツール・素材・バッファ", "3.5万", BAR, 3.0);
  warn(s, M+6.3, 4.66, 5.73, 1.58, "浮いた分は、研究開発に戻します",
    ["AXなしとの差は5期で約17億。これを人件費の節約として持たず、研究開発（5期13億・売上の16%）へ入れます。",
     "モデルが強くなる → AX倍率が上がる → 原価が下がる → さらに研究開発に回せる。",
     "この循環が、他社が同じ年数をかけないと追いつけない理由です。"]);
  foot(s, "⚠ AX倍率4倍は未実証の［仮置き］です。3倍なら営業利益率22.6%、2倍なら18.1%。1期の最初の3案件で必ず実測します（マイルストーン参照）");
}

/* ═══════════ 11. ユニットエコノミクス ═══════════ */
{
  const s = base(false);
  head(s, 3, "ユニットエコノミクス", "売上82.5億が何の積み上げなのかを、1本・1契約・1取引あたりで示します");
  s.addText("① 映像制作 — 1本あたり（単価60万・AX4倍）", { x:M, y:1.52, w:6.0, h:0.3, fontFace:F, fontSize:11, bold:true, color:VERM, margin:0, isTextBox:true });
  const rowsA=[
    hrow(["","金額","誰が受け取るか"]),
    ["売上","60.0万","—"],
    ["中国クリエイターへの支払","▲12.0万","業務委託（中国・制作パートナー経由）"],
    ["制作ディレクション","▲5.0万","業務委託。AXで8時間→2時間"],
    ["AIツール・素材・レンダリング","▲2.0万","—"],
    ["品質バッファ（作り直し）","▲1.5万","業務委託"],
    [{text:"売上総利益",options:{bold:true,color:VERM}},{text:"39.5万（65.8%）",options:{bold:true,color:VERM}},{text:"社員は1人も原価に入らない",options:{bold:true}}],
  ];
  table(s, M, 1.88, 6.0, rowsA, [2.4,1.4,2.2], 9, 0.32);
  s.addText("② ツール外販 — 1契約あたり", { x:M+6.3, y:1.52, w:5.7, h:0.3, fontFace:F, fontSize:11, bold:true, color:GOLD, margin:0, isTextBox:true });
  const rowsB=[
    hrow(["","年間単価","5期の契約数","5期の売上"]),
    [{text:"制作会社（法人）",options:{bold:true,color:GOLD}},"320万","250社",{text:"8.0億",options:{bold:true,color:GOLD}}],
    ["個人クリエイター","12万","2,100人","2.5億"],
    [{text:"合計",options:{bold:true}},"","",{text:"10.5億",options:{bold:true,color:GOLD}}],
    [{text:"売るもの",options:{bold:true}},{text:"チェックポイント・LoRA",options:{color:GOLD}},{text:"要件定義テンプレート",options:{color:GOLD}},{text:"自動チェック",options:{color:GOLD}}],
  ];
  table(s, M+6.3, 1.88, 5.73, rowsB, [1.83,1.3,1.3,1.3], 9, 0.32);
  s.addText("③ 越境C2C発注 — 1取引あたり", { x:M, y:4.12, w:6.0, h:0.3, fontFace:F, fontSize:11, bold:true, color:NAVY, margin:0, isTextBox:true });
  const rowsC=[
    hrow(["","金額","備考"]),
    ["発注者が支払う額（GMV）","9.0万","単価帯は5,000円〜100万円。平均は中位に置く［仮置き］"],
    [{text:"当社の取引手数料 18%",options:{bold:true,color:NAVY}},{text:"1.62万",options:{bold:true,color:NAVY}},"国内C2Cの約22%より低く置く"],
    ["決済手数料・インフラ","▲0.24万","Stripe等"],
    [{text:"売上総利益",options:{bold:true,color:NAVY}},{text:"1.38万（85%）",options:{bold:true,color:NAVY}},{text:"人が介在しないので件数に比例しない",options:{bold:true}}],
  ];
  table(s, M, 4.48, 6.0, rowsC, [2.2,1.1,2.7], 9, 0.32);
  sec(s, M+6.3, 4.12, 5.73, "5期 売上82.5億の内訳");
  hbar(s, M+6.3, 4.50, 5.73, 0.34, 1.00, "① 映像制作 11,189本", "67.1億", VERM, 2.4);
  hbar(s, M+6.3, 4.88, 5.73, 0.34, 0.16, "② ツール外販", "10.5億", GOLD, 2.4);
  hbar(s, M+6.3, 5.26, 5.73, 0.34, 0.07, "③ C2C手数料", "4.9億", NAVY, 2.4);
  warn(s, M+6.3, 5.62, 5.73, 0.62, "原価に社員は1人も入りません",
    ["クリエイターもディレクションも業務委託。社員54名は、モデル開発と統括だけです。"]);
  foot(s, "制作の単価・原価は BUSINESS_PLAN 7-1 をAX前提で組み直したもの。ツール外販の単価と契約数、C2Cの手数料率・件数は、すべて未実測の［仮置き］です");
}

/* ═══════════ 12. 収益モデル ═══════════ */
{
  const s = base(false);
  head(s, 3, "収益モデル", "主軸は①の映像制作。②のツール外販が企業価値を作り、③のC2Cが裾野を広げます");
  const rows=[
    hrow(["","収益ライン","型","開始","5期の売上","備考"]),
    [{text:"①",options:{bold:true,color:VERM}},{text:"AI映像制作の受注 → クリエイターへ配分",options:{bold:true}},"フロー",{text:"初日から",options:{bold:true}},{text:"67.1億",options:{bold:true,color:VERM}},"粗利率66%。事業の主体。ここでデータが溜まる"],
    [{text:"②",options:{bold:true,color:GOLD}},{text:"特許・制作用ツールの外販",options:{bold:true}},"ストック",{text:"2期〜",options:{bold:true}},{text:"10.5億",options:{bold:true,color:GOLD}},"チェックポイント・LoRA・工程ツール。粗利率80%"],
    [{text:"③",options:{bold:true,color:NAVY}},"越境C2C発注の取引手数料","ストック","6ヶ月目〜",{text:"4.9億",options:{color:NAVY}},"手数料率18%［仮置き］。②のツールを外部に開放したもの"],
  ];
  table(s, M, 1.58, W, rows, [0.7,4.0,1.0,1.2,1.3,3.83], 9.5, 0.46);
  sec(s, M, 3.56, 6.0, "②で売るもの — ①の制作で溜まったデータから作る");
  const y=3.92, w=(6.0-0.3)/2, h=0.92;
  card(s, M,          y,       w, h, "チェックポイント", ["日本市場の要求で追い込んだ基盤モデル"], GOLD, 9);
  card(s, M+w+0.3,    y,       w, h, "LoRA", ["用途別・画風別の追加学習データ"], GOLD, 9);
  card(s, M,          y+h+0.2, w, h, "要件定義テンプレート", ["日本語で答えるだけで発注仕様になる"], GOLD, 9);
  card(s, M+w+0.3,    y+h+0.2, w, h, "成果物の自動チェック", ["尺・解像度・指示との整合"], GOLD, 9);
  warn(s, M+6.3, 3.56, 5.73, 1.42, "順番が大事です",
    ["①の制作を1万本こなさないと、②で売れるチェックポイントもLoRAも育ちません。",
     "制作が先、ツールが後。この順序だから、他社が同じものを作るには同じ年数がかかります。"]);
  warn(s, M+6.3, 5.06, 5.73, 1.18, "そして②が①の原価を下げます",
    ["自社で使えば原価が下がり、外に売れば売上になる。同じものが両方に効きます。"]);
  foot(s, "ツール外販の単価と契約数、C2Cの手数料率・発注件数・平均単価は、すべて未実測の［仮置き］です。1期に実測して差し替えます");
}

/* ═══════════ 13. 日本IPを使った作品制作 ═══════════ */
{
  const s = base(false);
  head(s, 3, "日本IPを使った作品制作 — アニメ化されないマンガを動かす",
       "中小出版社には「アニメ化したい作品」はあっても、1話3,000万円の制作費がありません");
  warn(s, M, 1.50, W, 1.16, "アニメ化の壁は、面白さではなく資金です",
    ["深夜アニメ1クール（12話）の制作費は一般に数億円規模とされ、製作委員会を組まないと着手できません。",
     "だから中小出版社の既刊マンガは、評価されていても映像化されないまま眠っています。AIで作れるなら、この在庫が動きます。"]);
  const rows=[
    hrow(["","対象IP","なぜ映像化されてこなかったか","版権コスト","当社の出口"]),
    [{text:"A",options:{bold:true,color:GOLD}},{text:"中小出版社の既刊マンガ（未映像化）",options:{bold:true}},{text:"製作委員会を組める規模ではない。制作費が出ない",options:{bold:true,color:VERM}},"数万〜数十万／作品","他社PFの看板作品・海外展開"],
    [{text:"C",options:{bold:true,color:NAVY}},"個人作家・Web小説（なろう系・pixiv）","権利者が1人。映像化の話が来ない","ほぼゼロ（成功報酬型）","他社PFの課金枠へ供給"],
    [{text:"B",options:{bold:true,color:NAVY}},"自治体・企業のキャラクター","予算が単発で、動かす発想がない","ゼロ（先方負担）","自治体PR・企業広報・ふるさと納税"],
    [{text:"D",options:{bold:true,color:VERM}},"パブリックドメイン（青空文庫・古典）","—（権利処理が不要）",{text:"ゼロ",options:{bold:true,color:VERM}},"他社PFに投入し、実績づくり"],
  ];
  table(s, M, 2.82, W, rows, [0.6,3.3,3.6,1.9,2.63], 9.5, 0.42);
  warn(s, M, 4.86, (W-0.3)/2, 1.38, "着手はDから。Aが本命です",
    ["D（版権ゼロ）で制作力を示し、他社PFでの再生数を実績にする。",
     "その実績を持って中小出版社へ行き、Aの未映像化マンガをレベニューシェアでアニメ化する。",
     "先方は制作費ゼロ、当社は版権コストほぼゼロ。噛み合います。"]);
  warn(s, M+(W-0.3)/2+0.3, 4.86, (W-0.3)/2, 1.38, "IPホルダーはAI生成を警戒します",
    ["原作ファンの反発が、原作そのものの価値を毀損しかねません。",
     "契約に「AI利用の可否と開示方法」を必ず明記します。JIAA調査でも受容条件1位は「AI利用が明記されている」37.6%。",
     "この作品群の収益は5年計画に計上していません。"]);
  foot(s, "出所: 日本動画協会 アニメ産業レポート（制作市場4,662億円・海外売上2兆1,700億円）／ JIAA「2026年インターネット広告に関するユーザー意識調査」。アニメ1話あたりの制作費は業界で広く言及される水準で、当社の実測ではありません");
}

/* ═══════════ 14. 政策も同じ方向を向いている ═══════════ */
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
/* ═══════════ 15. 競合 ═══════════ */
{
  const s = base(false);
  head(s, 4, "なぜショートムービー配信プラットフォームをやらないのか",
       "一度は検討しました。やらない理由を先に出します");
  const y0=1.50, w=(W-0.9)/4, h=1.46;
  card(s, M,             y0, w, h, "1  先行が8社いる",
    ["BUMP（DL400万・国内1位）／POPCORN（累計120億再生）／FANY:D／FOD SHORT ほか。","中国発アプリがアプリ市場シェア9割超。"], VERM, 9);
  card(s, M+w+0.3,       y0, w, h, "2  勝敗は広告費で決まる",
    ["視聴者獲得（流量投放）が総コストの約70%。","先に広告費を張れる側が勝つ消耗戦。"], VERM, 9);
  card(s, M+(w+0.3)*2,   y0, w, h, "3  当社の強みが効かない",
    ["要件定義・品質保証・契約・与信は、視聴者には関係がない。","制作力で差がつかない土俵。"], NAVY, 9);
  card(s, M+(w+0.3)*3,   y0, w, h, "4  資金が足りない",
    ["1.5億では広告費を1年も張れない。","中国のAI制作会社の約90%が赤字なのはこれが理由。"], GOLD, 9);
  warn(s, M, 3.18, W, 1.10, "やらないと決めた代わりに、作った作品は他社のPFに載せます",
    ["自社で配信面を持たないので、視聴者獲得費はゼロです。日本IP（前ページ）で作った作品は YouTube・TikTok・ショートドラマ各社へ供給します。",
     "配信は相手の土俵。当社は制作力とIPで取り分を得ます。"]);
  sec(s, M, 4.44, 6.0, "では当社の競合は誰か — 国内の映像制作市場です");
  hbar(s, M, 4.80, 6.0, 0.34, 0.20, "フリーランス", "3〜30万", BAR, 2.3);
  hbar(s, M, 5.16, 6.0, 0.34, 0.45, "当社", "40〜80万", VERM, 2.3);
  hbar(s, M, 5.52, 6.0, 0.34, 0.55, "中小の制作会社", "10〜80万", BAR, 2.3);
  hbar(s, M, 5.88, 6.0, 0.34, 1.00, "大手の制作会社", "50〜300万", BAR, 2.3);
  const rows=[
    hrow(["相手","相手の強み","当社が勝てる点"]),
    ["国内の映像制作会社","品質・信用・実績",{text:"価格。原価が半分以下",options:{bold:true}}],
    ["国内フリーランス","価格",{text:"品質保証と納期管理",options:{bold:true}}],
    ["中国へ直接発注","価格",{text:"契約・与信・請求。個人に直接出せる企業はほぼいない",options:{bold:true}}],
  ];
  table(s, M+6.3, 4.44, 5.73, rows, [1.6,1.5,2.63], 9, 0.40);
  foot(s, "出所: GOKKO ／ nowhere film ／ BUMP公式 ／ 36Kr Japan（中国発アプリの日本シェア）／ 第一財経・搜狐（中国AI短劇の淘汰）／ 動画幹事・ムビサク（制作費相場）。詳細は COMPETITORS.md");
}

/* ═══════════ 16. なぜクリエイターは当社に来るのか ═══════════ */
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

/* ═══════════ 17. 課題と解決 ═══════════ */
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
     "だから追うべき指標は売上ではなく、人手に比例しない収益（①②③）の比率です。5期で80%。"]);
  foot(s, "各課題の詳細と数値根拠は COMPETITORS ／ MOAT_TIMELINE ／ CHINA_SOURCING に記載");
}

/* ═══════════ 18. チーム ═══════════ */
{
  const s = base(false);
  head(s, 6, "チーム — 社員は極小に保ちます", "モデル開発と統括だけを社員に置き、制作は業務委託と自動化で回します");
  const y0=1.50, w=(W-0.6)/3, h=1.50;
  card(s, M,           y0, w, h, "代表取締役",
    ["会社経営・コンサルティング経験","日本・中国・台湾をまたぐ越境実務","（詳細は［記入予定］）"], VERM, 10);
  card(s, M+w+0.3,     y0, w, h, "CTO／モデル開発責任者", ["採用計画"], NAVY, 10);
  card(s, M+(w+0.3)*2, y0, w, h, "制作統括", ["採用計画"], GOLD, 10);
  const rows=[
    hrow(["","1期","2期","3期","4期","5期"]),
    [{text:"社員（日本側）",options:{bold:true,color:VERM}},{text:"6",options:{bold:true}},"12","24","40",{text:"54",options:{bold:true,color:VERM}}],
    ["　うちモデル開発エンジニア","2","5","12","22","34"],
    ["　うち経営・統括・管理","4","7","12","18","20"],
    [{text:"業務委託 ディレクション",options:{color:MUTED}},"1","5","16","32","54"],
    [{text:"業務委託 中国クリエイター（稼働）",options:{color:MUTED}},"2","7","23","46","78"],
    [{text:"★ 売上／社員",options:{bold:true}},"600万","2,450万","5,842万","9,570万",{text:"1.53億",options:{bold:true,color:VERM}}],
  ];
  table(s, M, 3.20, W, rows, [3.6,1.6,1.6,1.6,1.6,1.63], 9.5, 0.34);
  warn(s, M, 5.42, (W-0.3)/2, 0.82, "社員の平均単価は上がります",
    ["安い職種が社外に出るので、残るのはエンジニアと統括だけ。1期880万 → 5期904万。総額は4.9億に収まります。"]);
  warn(s, M+(W-0.3)/2+0.3, 5.42, (W-0.3)/2, 0.82, "中国の制作パートナー ［記入予定］",
    ["発注・支払はパートナー経由。制作データと成果物の権利は契約により日本側に帰属させます。"]);
  foot(s, "⚠ 業務委託が中心になるため、偽装請負にならない契約設計（指揮命令をしない／成果物単位で発注する）が必須です。契約書の雛形を1期に弁護士と作ります");
}

/* ═══════════ 19. 事業計画 ═══════════ */
{
  const s = base(false);
  head(s, 7, "事業計画", "2期まで赤字、3期に黒字化。上場申請は5期です");
  const labels=["1期 2027/9","2期 2028/9","3期 2029/9","4期 2030/9","5期 2031/9"];
  s.addChart(p.ChartType.bar, [
    { name:"売上高", labels, values:[36,294,1402,3828,8251] },
    { name:"営業利益", labels, values:[-76,-94,45,554,2055] },
  ], {
    x:M, y:1.6, w:6.6, h:3.3,
    barDir:"col", barGrouping:"clustered",
    chartColors:[NAVY, VERM],
    catAxisLabelFontFace:F, catAxisLabelFontSize:9, catAxisLabelColor:MUTED,
    valAxisLabelFontFace:F, valAxisLabelFontSize:9, valAxisLabelColor:MUTED,
    valAxisMinVal:-200, valAxisMaxVal:8600,
    showValue:true, dataLabelFontFace:F, dataLabelFontSize:8, dataLabelColor:INKSOFT,
    showLegend:true, legendPos:"b", legendFontFace:F, legendFontSize:9,
    valGridLine:{ color:LINE, style:"solid", size:0.5 }, catGridLine:{ style:"none" },
    title:"売上高と営業利益の推移（単位 百万円・計画値）", showTitle:true,
    titleFontFace:F, titleFontSize:11, titleColor:INK,
  });
  const cx=M+6.9, cw=W-6.9;
  card(s, cx, 1.6, cw, 1.02, "1〜2期 ― 仕組みを作る",
    ["制作54本→400本。AX倍率1.0→1.5。研究開発に1.2億を先に入れる。赤字は計画通りです。"], VERM, 9.5);
  card(s, cx, 2.74, cw, 0.9, "3期 ― 黒字化",
    ["AX2.2倍で原価が22.2万まで下がり、1,800本で黒字に転じます（+4,500万）。"], GOLD, 9.5);
  card(s, cx, 3.76, cw, 1.14, "4〜5期 ― 回収",
    ["AX4倍・11,189本。年商82.5億・営業利益20.6億（24.9%）。社員は54名にとどめます。"], NAVY, 9.5);
  const rows=[
    hrow(["","① 制作（本数）","② ツール ／ ③ C2C","AX倍率／粗利率"]),
    ["1期","27（54本）","— ／ 9","1.0倍 ／ 29%"],
    ["2期","220（400本）","20 ／ 54","1.5倍 ／ 51%"],
    ["3期（N-2期）","1,080（1,800本）","160 ／ 162","2.2倍 ／ 61%"],
    ["4期（N-1期）","3,000（5,000本）","504 ／ 324","3.0倍 ／ 66%"],
    [{text:"5期（N期）→ 2031年 上場",options:{bold:true,color:VERM}},{text:"6,713（11,189本）",options:{bold:true}},{text:"1,052 ／ 486",options:{bold:true}},{text:"4.0倍 ／ 69%",options:{bold:true}}],
  ];
  table(s, M, 5.06, W, rows, [3.0,3.2,3.0,2.83], 10, 0.3);
  foot(s, "計画値。AX倍率・本数カーブ・研究開発費・業務委託単価はすべて未実測の［仮置き］です。数字は plan_v13.py が計算しています");
}

/* ═══════════ 20. 上場までの流れ ═══════════ */
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
     "当社の想定時価総額は、保守的なライン別評価でも183億。維持基準100億に対して1.8倍のバッファがあります。"]);
  foot(s, "出所: 日本取引所グループ 上場維持基準。上場基準は改定が続くため、準備期に入る前に最新基準を再確認します");
}

/* ═══════════ 21. 出口とリターン ═══════════ */
{
  const s = base(false);
  head(s, 8, "出口とリターン", "5期の売上82.5億・営業利益20.6億を前提に試算しています");
  const y0=1.58, h=1.46, w=(W-0.6)/3;
  stat(s, M,           y0, w, h, "183〜232億", "ライン別に倍率を分けた場合（保守）", "ツール6〜7倍＋C2C4〜5倍＋制作1.5〜2倍。証券会社が実際にやる見方", VERM);
  stat(s, M+w+0.3,     y0, w, h, "248〜413億", "全社にPSR3〜5倍", "人手に比例しない収益が80%であることを根拠にする", NAVY);
  stat(s, M+(w+0.3)*2, y0, w, h, "1.53億", "売上／社員（5期）", "社員54名で年商82.5億。国内SaaSの平均2,000〜4,000万に対して桁が違う", GOLD);
  sec(s, M, 3.20, W, "シード投資家のリターン — 上場後持分 14.5%（ESOP10%・シリーズA・IPO公募20%で希薄化後）");
  const rows=[
    hrow(["時価総額","根拠","シードの取り分","倍率"]),
    ["183億","ツール6倍＋C2C4倍＋制作1.5倍（保守）","26.6億",{text:"18.7倍",options:{bold:true,color:VERM}}],
    ["232億","ツール7倍＋C2C5倍＋制作2.0倍","33.7億",{text:"23.7倍",options:{bold:true,color:VERM}}],
    ["248億","全社PSR3倍","35.9億",{text:"25.3倍",options:{bold:true,color:VERM}}],
    ["330億","全社PSR4倍","47.9億",{text:"33.7倍",options:{bold:true,color:VERM}}],
  ];
  table(s, M, 3.52, W, rows, [2.0,5.4,2.4,2.23], 10, 0.38);
  warn(s, M, 5.42, (W-0.3)/2, 0.82, "維持基準は余裕を持って超えます",
    ["グロースの「上場5年経過後に時価総額100億円」に対し、保守的な183億でも1.8倍のバッファがあります。"]);
  warn(s, M+(W-0.3)/2+0.3, 5.42, (W-0.3)/2, 0.82, "すべて「計画が達成された場合」の試算です",
    ["2025年のグロースIPOは18社（前年34社から半減）。倍率は市況で変動し、利回りの保証ではありません。"]);
  foot(s, "出所: M&A総研（業種別EV/EBITDA倍率）／ EY Japan（2026年以降のIPO市場）／ FiNX（グロース維持基準の制度化）。上場時の創業者持分は42%前後を想定");
}

/* ═══════════ 22. マイルストーン ═══════════ */
{
  const s = base(false);
  head(s, 9, "マイルストーン", "各フェーズは「ゲート条件」で区切ります。満たさない限り、次へは進みません");
  const rows=[
    hrow(["時期","やること","◆ 次へ進むゲート条件"]),
    ["〜2026/12","法人設立・中国パートナーとの契約・業務委託契約の雛形作成","パートナー契約の締結／弁護士の見解書（業務委託・資金決済法）"],
    ["2027/1-3","制作の受注開始／ツールの内部適用を開始",{text:"制作 累計5本／★ AX倍率の初回実測（1本あたりディレクション時間）",options:{bold:true,color:VERM}}],
    ["2027/4-9","C2C発注PFの公開（6ヶ月目）・D案IPの投入","制作 1期54本／登録100名／手数料率と平均単価の初回実測"],
    ["2期","制作400本・ツール外販の立ち上げ",{text:"AX倍率 1.5倍を達成",options:{bold:true}} ,"ツール外販 法人8社／シリーズA 3億／監査法人SR"],
    ["3期","制作1,800本・黒字化",{text:"AX倍率 2.2倍／通期黒字／監査開始",options:{bold:true}}],
    ["4期","制作5,000本・内部管理体制の構築","AX倍率 3.0倍／営業利益率15%以上／流通株式25%の設計合意"],
    [{text:"5期",options:{bold:true,color:VERM}},{text:"制作11,189本・上場申請",options:{bold:true}},{text:"AX倍率 4.0倍／年商82.5億・営業利益20.6億",options:{bold:true}}],
  ];
  const fixed = rows.map(function(r){ return r.length > 3 ? [r[0], r[1], r[2]] : r; });
  table(s, M, 1.58, W, fixed, [1.6,4.6,5.83], 9.5, 0.40);
  warn(s, M, 4.98, W, 1.26, "最優先で実測するのは AX倍率です",
    ["1本あたりのディレクション時間が8時間から何時間に落ちるか。これが計画の全部に乗っています。",
     "4倍なら営業利益率24.9%、3倍なら22.6%、2倍なら18.1%、AXなしなら4.6%。2027年1〜3月の最初の3案件で測ります。"]);
  foot(s, "ゲート条件を満たさない場合は次フェーズに進まず、前提を引き直します。詳細は ROADMAP.md");
}

/* ═══════════ 23. 資金計画 ═══════════ */
{
  const s = base(false);
  head(s, 10, "資金計画", "調達目標 1.5億円。融資を使わず、全額をエクイティで調達します");
  sec(s, M, 1.52, 6.3, "1年目の使途（単位 万円・合計 12,000万）");
  const items=[["人件費（社員6名）",5300,VERM],["研究開発（GPU・モデル・データ基盤）",3000,GOLD],
    ["C2C発注PF 開発（初期版）",800,NAVY],["獲得費（営業・マーケティング）",600,VERM],
    ["制作事業の運転資金",600,VERM],["法務（業務委託契約・資金決済法）",500,MUTED],
    ["設立・機材・その他初期",400,MUTED],["中国パートナー提携・渡航",300,MUTED],
    ["オフィス・SaaS・その他",300,MUTED],["特許出願（2件）",200,MUTED]];
  items.forEach(function(it,i){ hbar(s, M, 1.90+i*0.40, 6.3, 0.34, it[1]/5300, it[0], String(it[1]), it[2], 3.3); });
  const y1=1.90, w2=W-6.9;
  stat(s, M+6.9,                y1, (w2-0.3)/2, 1.44, "800万", "資本金（代表個人が直接出資）", "1,000万未満に抑え、初年度の消費税課税事業者化を回避", GOLD);
  stat(s, M+6.9+(w2-0.3)/2+0.3, y1, (w2-0.3)/2, 1.44, "1.42億", "シード（創業時）", "放出20〜27%を想定。J-KISSでの価格先送りも選択肢", NAVY);
  warn(s, M+6.9, 3.52, w2, 1.52, "使途の4分の1が研究開発です",
    ["1年目に使うのは 1億2,000万。残り約3,000万は2期への持ち越しです。",
     "最大の費目は人件費（社員6名・5,300万）、次が研究開発（3,000万）。",
     "社員を増やす代わりにモデルへ入れる、という配分を初年度から取ります。"]);
  warn(s, M+6.9, 5.14, w2, 1.10, "追加調達はシリーズA 3億のみ。累計4.5億です",
    ["社員を増やさずに伸びる設計なので、規模を追うための大型調達が要りません。シリーズB以降は想定していません。"]);
  s.addText("［仮置き］AX倍率と業務委託単価が未実測のため、2期以降の原価の精度が最も低い数字です。1期に実測して増減させます。",
    { x:M, y:5.96, w:6.3, h:0.34, fontFace:F, fontSize:9, color:MUTED, valign:"top", margin:0, isTextBox:true });
  foot(s, "※ 融資は使いません。補助金は後払いのため資金繰りに算入していません。全額をエクイティで調達します");
}

/* ═══════════ 24. リスクと対策 ═══════════ */
{
  const s = base(false);
  head(s, 11, "リスクと対策", "影響度と発生確率で並べています。上の2つが、この事業の生死を分けます");
  const rows=[
    hrow(["#","影響度","発生確率","リスク","対策"]),
    [{text:"1",options:{bold:true}},{text:"高",options:{bold:true,color:VERM}},{text:"高",options:{bold:true,color:VERM}},{text:"AX倍率が4倍に届かない",options:{bold:true}},"1期に実測。3倍なら22.6%、2倍なら18.1%まで落ちる。届かないぶんは本数計画を下げて利益率を守る"],
    [{text:"2",options:{bold:true}},{text:"高",options:{bold:true,color:VERM}},{text:"高",options:{bold:true,color:VERM}},{text:"単価60万を維持できない",options:{bold:true}},"SAM3%を取りにいけば価格競争になる。45万に落ちると売上50億。ツール外販の比率を上げて補う"],
    [{text:"3",options:{bold:true}},{text:"高",options:{bold:true,color:VERM}},{text:"中",options:{color:VERM}},{text:"業務委託が偽装請負と判定される",options:{bold:true}},"指揮命令をしない／成果物単位で発注する契約設計。1期に弁護士と雛形を作り、監査法人にも事前確認"],
    ["4","高","中","年11,189本の発注を取れない","代理店チャネル（2次受け）とC2Cのセルフサーブを主にする。営業社員で取りに行く設計にしない"],
    ["5","高","低","シリーズA 3億が入らない","ツール開発の投資を止めて制作に全振り。2期の赤字は▲9,400万→▲3,000万台まで縮む"],
    ["6","中","中","中国の制作パートナーへの依存","支払いと品質保証を1社に依存しない。2社目の提携を2期までに確保する"],
    ["7","中","中","クリエイター単価の上昇","中国側も同じAIを使えるようになれば12万が維持できない。ランク制と長期契約で固定する"],
    ["8","中","中","資金決済法の該当性","収納代行型（当社で預からない）を前提にPF設計の前に弁護士へ確認"],
  ];
  table(s, M, 1.58, W, rows, [0.5,0.9,1.0,3.4,6.23], 9, 0.42);
  warn(s, M, 5.42, W, 0.82, "1と2は、どちらも「原価と単価」の話です",
    ["この事業の利益は、AXで原価をどこまで下げられるかと、単価をどこまで守れるかの差に乗っています。だから両方を毎月測ります。"]);
  foot(s, "全リスクと対策は BUSINESS_PLAN ／ MOAT_TIMELINE ／ CHINA_SOURCING に記載しています");
}

/* ═══════════ 25. クロージング ═══════════ */
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

/* ═══════════ 26. 日本は一度、これをやっている ═══════════ */
{
  const s = base(false);
  head(s, 1, "日本は一度、これをやっている", "輸入した技術を4年で国産化し、その後20年以上の改善で世界一の品質に到達した");
  const y0=1.46, w=(W-0.9)/4, h=1.16;
  card(s, M,           y0, w, h, "1952", ["日産＝オースチン技術提携","日野＝ルノー、いすゞ＝ルーツ"], MUTED, 9);
  card(s, M+w+0.3,     y0, w, h, "1956-57", ["4社が相次いで完全国産化","ここまで4年"], VERM, 9);
  card(s, M+(w+0.3)*2, y0, w, h, "1960s-70s", ["QCサークル・トヨタ生産方式","改善を20年以上回し続ける"], NAVY, 9);
  card(s, M+(w+0.3)*3, y0, w, h, "1980s", ["品質と燃費で世界市場を取る","米国メーカーが学びに来る側へ"], GOLD, 9);

  /* 出発点と到達点。いずれも CC0 / パブリックドメインの写真 */
  const iw=2.44, ih=1.30, iy=2.80;
  img(s, "assets/austin1959.jpg",  M,        iy, iw, ih);
  arw(s, "r", M+iw+0.12, iy+0.47, 0.44, 0.36);
  img(s, "assets/corolla1986.jpg", M+iw+0.68, iy, iw, ih);
  s.addText("1959 日産オースチン A50", { x:M, y:iy+ih+0.04, w:iw, h:0.24, fontFace:F, fontSize:8.5,
    color:MUTED, align:"center", valign:"middle", margin:0, isTextBox:true });
  s.addText("1986 トヨタ カローラ", { x:M+iw+0.68, y:iy+ih+0.04, w:iw, h:0.24, fontFace:F, fontSize:8.5,
    color:MUTED, align:"center", valign:"middle", margin:0, isTextBox:true });

  warn(s, M+iw*2+0.98, iy, W-(iw*2+0.98), 1.58, "ポイントは国産化の速さではありません",
    ["日産・トヨタは国産化をゴールにせず、以後20年以上かけて生産方式と品質管理を磨き続けました。",
     "1980年代には米国メーカーが日本の生産方式を学びに来る側に回ります。",
     "内製化（3年）は出発点にすぎません。制作データで改善を回し続けることが、模倣されない資産になります。"], 9.5);

  const rows=[
    hrow(["","持っている側","","修得する側","期間","到達点"]),
    ["1952 → 1956","オースチン（英）","技術 →","日産・日野・いすゞ","4年","完全国産化。ただしこれは入口"],
    [{text:"2026 → 2029",options:{bold:true,color:VERM}},"世界のAIクリエイター","制作力 →",{text:"当社",options:{bold:true}},{text:"3年",options:{bold:true}},{text:"内製化。ここから改善を回す",options:{bold:true}}],
  ];
  table(s, M, 4.52, W, rows, [1.8,2.9,1.0,2.9,0.8,2.63], 9.5, 0.40);
  s.addText("⚠ 当時は政府の保護（輸入制限・関税）がありました。今のAI映像にはありません。だから改善のサイクルをより速く回す必要があります。",
    { x:M, y:5.86, w:W, h:0.34, fontFace:F, fontSize:10, bold:true, color:VERM, valign:"middle", margin:0, isTextBox:true });
  foot(s, "出所: 日産自動車 企業情報 ／ トヨタ博物館 ／ GAZOO「ノックダウン生産の時代」／ 日本科学技術連盟（QCサークル・デミング賞）。写真: 1959 Nissan Austin Cambridge Deluxe（CC0 / TTTNIS）、1986-1989 Toyota Corolla AE82（Public domain / OSX）いずれも Wikimedia Commons");
}
p.writeFile({ fileName: "deck.pptx" }).then(function(){ console.log("deck.pptx"); });

