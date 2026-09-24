/* 補足ビジュアル 2枚 — 生産体制の地図／3本の柱
 *   node visual.js  →  visual.pptx  →  slim.py で仕上げる
 * 地図は make_map.py が assets/map_eastasia.png と .json（拠点・矢印ラベルの座標）を出力する。
 * 章番号は本編に差し込んだときの位置に合わせてある（地図＝6 チーム、柱＝3 ビジネスモデル）。
 */
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE";               // 13.333 x 7.5
p.author = "AI映像制作事業";
p.title  = "生産体制と3本の柱";

const INK="16161A", PAPER="FFFFFF", VERM="B3121B",
      GOLD="C9962C", NAVY="2A3563", MUTED="6E6E76", LINE="DCD9D4",
      INKSOFT="3A3A42", ONDARK="EDEBE7", TEAL="1F6F63", ORANGE="D9601A",
      CARD="F7F5F2", STEP="55555E";
const TINT = { [VERM]:"FBEDED", [GOLD]:"FBF4E3", [NAVY]:"E9EBF3" };
const F="Yu Gothic";
const M=0.65, W=12.03;

let pageNo = 0;
function base(){ const s=p.addSlide(); s.background={color:PAPER}; return s; }
function head(s, num, title, sub){
  s.addShape(p.ShapeType.rect, { x:M, y:0.44, w:0.52, h:0.52, fill:{color:VERM} });
  s.addText(String(num), { x:M, y:0.44, w:0.52, h:0.52, fontFace:F, fontSize:17, bold:true,
    color:PAPER, align:"center", valign:"middle", margin:0, isTextBox:true });
  s.addText(title, { x:1.32, y:0.40, w:W-0.67, h:0.6, fontFace:F, fontSize:25, bold:true,
    color:INK, valign:"middle", margin:0, isTextBox:true });
  s.addText(sub, { x:1.32, y:1.02, w:W-0.67, h:0.34, fontFace:F, fontSize:12,
    color:MUTED, valign:"middle", margin:0, isTextBox:true });
}
function foot(s, note){
  pageNo++;
  s.addText(note, { x:M, y:6.93, w:W-1.2, h:0.34, fontFace:F, fontSize:8.5,
    color:MUTED, valign:"middle", margin:0, isTextBox:true });
  s.addText(String(pageNo), { x:12.28, y:6.93, w:0.4, h:0.3, fontFace:F, fontSize:9,
    color:MUTED, align:"right", valign:"middle", margin:0, isTextBox:true });
}
function txt(s, t, o){
  s.addText(t, Object.assign({ fontFace:F, margin:0, isTextBox:true, valign:"middle" }, o));
}

/* ═══════════ 1. 生産体制 — 東アジアの3拠点 ═══════════ */
const MAP_PNG  = __dirname + "/assets/map_eastasia.png";
const MAP_JSON = __dirname + "/assets/map_eastasia.json";
if (fs.existsSync(MAP_PNG) && fs.existsSync(MAP_JSON)) {
  const G = JSON.parse(fs.readFileSync(MAP_JSON, "utf8"));
  const s = base();
  head(s, 6, "日本・中国・ベトナムの3拠点で、制作と開発を回す",
       "受注と品質保証は日本、制作は中国、開発はベトナム。国境をまたいだ分業を、日本の社員22名で束ねます（5期計画）");

  s.addImage({ path: MAP_PNG, x: G.box.x, y: G.box.y, w: G.box.w, h: G.box.h });

  // 矢印のラベル（白い縁取りで地図から浮かせる。背景の箱は置かない）
  const HALO = { size:7, opacity:0.95, color:PAPER };
  G.flows.forEach(f => {
    txt(s, f.label, { x:f.x-f.w/2, y:f.y-0.16, w:f.w, h:0.32, fontSize:10, bold:true,
      color:f.color, align:"center", glow:HALO });
  });
  // 拠点のピンと国名
  G.pins.forEach(pn => {
    s.addShape(p.ShapeType.ellipse, { x:pn.x-0.11, y:pn.y-0.11, w:0.22, h:0.22,
      fill:{color:pn.color}, line:{color:PAPER, width:2} });
    txt(s, [{ text:pn.name, options:{ fontSize:15, bold:true, color:INK, glow:HALO, breakLine:true } },
            { text:pn.role, options:{ fontSize:10, bold:true, color:pn.color, glow:HALO } }],
      { x:pn.lx, y:pn.ly, w:pn.lw, h:0.58, align:pn.align, valign:"top" });
  });

  // 地図の右下（海の上）に、3拠点の組み合わせを一言で
  txt(s, [{ text:"日本の品質保証 × 中国の制作力 × ベトナムの開発力", options:{ fontSize:11.5, bold:true, color:INK, glow:HALO, breakLine:true } },
          { text:"3拠点とも時差1〜2時間。受注・制作・修正が同じ営業日で回る", options:{ fontSize:9.5, color:INKSOFT, glow:HALO } }],
    { x:4.55, y:5.92, w:3.45, h:0.66, align:"right", valign:"top", lineSpacingMultiple:1.25 });

  // 右：拠点ごとの役割
  const cx = 8.35, cw = M+W-8.35;
  const cards = [
    { name:"日本", role:"本社・受注・品質保証", col:VERM, lines:[
      "日本企業と個人・中小から受注し、品質を保証して納品",
      "知財・IPの管理と、②③の開発を統括",
      "社員22名はすべて日本側（5期）" ] },
    { name:"中国", role:"制作", col:ORANGE, lines:[
      "制作パートナー経由で、登録クリエイターが制作",
      "登録2,000名・稼働681名（5期）",
      "稼働681名は、中国の微短劇就業者69万人の0.3%" ] },
    { name:"ベトナム", role:"開発", col:TEAL, lines:[
      "オフショア委託で、②のツールと③のPFを開発",
      "エンジニア19名（5期・業務委託）",
      "AXで1人あたりの生産性を上げ、人数を抑える" ] },
  ];
  cards.forEach((c, i) => {
    const y = 1.52 + i*1.53, h = 1.40;
    s.addShape(p.ShapeType.rect, { x:cx, y, w:cw, h, fill:{color:CARD} });
    s.addShape(p.ShapeType.rect, { x:cx, y, w:0.08, h, fill:{color:c.col} });
    txt(s, [{ text:c.name, options:{ fontSize:16, bold:true, color:INK } },
            { text:"　"+c.role, options:{ fontSize:10.5, bold:true, color:c.col } }],
      { x:cx+0.28, y:y+0.12, w:cw-0.44, h:0.40 });
    txt(s, c.lines.map((t,k)=>({ text:t, options:{ breakLine:k<c.lines.length-1 } })),
      { x:cx+0.28, y:y+0.56, w:cw-0.44, h:h-0.68, fontSize:9.5, color:INKSOFT,
        lineSpacingMultiple:1.28, valign:"top" });
  });
  s.addShape(p.ShapeType.rect, { x:cx, y:6.11, w:cw, h:0.69, fill:{color:INKSOFT} });
  txt(s, [{ text:"② ツール外販は国内と海外へ", options:{ fontSize:11.5, bold:true, color:PAPER, breakLine:true } },
          { text:"5期39.4億の約半分が海外向けの計画", options:{ fontSize:9.5, color:ONDARK } }],
    { x:cx+0.28, y:6.11, w:cw-0.44, h:0.69, lineSpacingMultiple:1.2 });

  foot(s, "5期（2031年）の計画値。出所: 事業計画_Ver0.8.xlsx／中国網絡視聴協会（微短劇就業者）。地図: Natural Earth。"
        + "拠点は国単位の表示で都市を特定しない。中国の制作パートナーは契約前［記入予定］");
} else {
  console.warn("地図の素材がないので1枚目を飛ばします（make_map.py を先に実行）");
}

/* ═══════════ 2. 3本の柱 ═══════════ */
{
  const s = base();
  head(s, 3, "3本の柱 — 作る・売る・開く",
       "①の制作で溜めたデータが②のツールになり、②を外に開いたものが③。3本が互いの入口になっています");

  const RX = M+0.35, RW = W-0.7;
  // 屋根（ペディメント）と梁
  s.addShape(p.ShapeType.triangle, { x:RX, y:1.46, w:RW, h:0.74, fill:{color:INKSOFT} });
  txt(s, "5期 売上 117.4億", { x:RX+RW/2-2.2, y:1.84, w:4.4, h:0.34, fontSize:17, bold:true,
    color:PAPER, align:"center" });
  s.addShape(p.ShapeType.rect, { x:RX, y:2.22, w:RW, h:0.32, fill:{color:INKSOFT} });
  txt(s, "営業利益 41.9億（35.7%） ｜ 2031年 東証グロース上場を目指す",
    { x:RX, y:2.22, w:RW, h:0.32, fontSize:11, bold:true, color:ONDARK, align:"center" });

  const PW = 3.0, X0 = RX+0.3, G = (RW-0.6-3*PW)/2;
  const pillars = [
    { no:"①", name:"AI映像制作", col:VERM, icon:"play",
      desc:["日本企業の映像を受注し、","中国のクリエイターで制作する"],
      meta:"案件ごと ｜ 初日から", big:"35.2億", sub:"5期・3,727本" },
    { no:"②", name:"ツール外販", col:GOLD, icon:"gear",
      desc:["制作で溜まったデータを","特許・モデル・ツールにして売る"],
      meta:"年額契約（ARR） ｜ 2期〜", big:"39.4億", sub:"5期・法人578社" },
    { no:"③", name:"越境C2C", col:NAVY, icon:"globe",
      desc:["②の仕組みを外に開き、","個人・中小の発注を中国へつなぐ"],
      meta:"取引手数料30% ｜ 6ヶ月目〜", big:"42.7億", sub:"5期・年95,200件" },
  ];
  pillars.forEach((c, i) => {
    const px = X0 + i*(PW+G), cxm = px+PW/2;
    // 柱頭・柱身・柱礎
    s.addShape(p.ShapeType.rect, { x:px-0.1, y:2.60, w:PW+0.2, h:0.16, fill:{color:c.col} });
    s.addShape(p.ShapeType.rect, { x:px, y:2.76, w:PW, h:2.74, fill:{color:TINT[c.col]} });
    s.addShape(p.ShapeType.rect, { x:px, y:2.76, w:0.07, h:2.74, fill:{color:c.col, transparency:55} });
    s.addShape(p.ShapeType.rect, { x:px+PW-0.07, y:2.76, w:0.07, h:2.74, fill:{color:c.col, transparency:55} });
    s.addShape(p.ShapeType.rect, { x:px-0.1, y:5.50, w:PW+0.2, h:0.16, fill:{color:c.col} });

    // アイコン（色丸に白抜き）
    const d = 0.84, bx = cxm-d/2, by = 2.90;
    s.addShape(p.ShapeType.ellipse, { x:bx, y:by, w:d, h:d, fill:{color:c.col} });
    if (c.icon === "play") {
      s.addShape(p.ShapeType.triangle, { x:cxm-0.15, y:by+d/2-0.17, w:0.34, h:0.34,
        fill:{color:PAPER}, rotate:90 });
    } else if (c.icon === "gear") {
      s.addShape(p.ShapeType.gear6, { x:cxm-0.27, y:by+d/2-0.27, w:0.54, h:0.54, fill:{color:PAPER} });
      s.addShape(p.ShapeType.ellipse, { x:cxm-0.09, y:by+d/2-0.09, w:0.18, h:0.18, fill:{color:c.col} });
    } else {
      const g = 0.52, gy = by+d/2-g/2;
      s.addShape(p.ShapeType.ellipse, { x:cxm-g/2, y:gy, w:g, h:g, fill:{color:c.col}, line:{color:PAPER, width:2} });
      s.addShape(p.ShapeType.ellipse, { x:cxm-0.11, y:gy, w:0.22, h:g, fill:{color:c.col}, line:{color:PAPER, width:1.75} });
      s.addShape(p.ShapeType.line, { x:cxm-g/2, y:gy+g/2, w:g, h:0, line:{color:PAPER, width:1.75} });
    }

    txt(s, c.no+" "+c.name, { x:px, y:3.84, w:PW, h:0.34, fontSize:16, bold:true, color:c.col, align:"center" });
    txt(s, c.desc.map((t,k)=>({ text:t, options:{ breakLine:k<c.desc.length-1 } })),
      { x:px+0.15, y:4.20, w:PW-0.3, h:0.54, fontSize:10, color:INKSOFT, align:"center",
        lineSpacingMultiple:1.25, valign:"top" });
    s.addShape(p.ShapeType.line, { x:px+0.4, y:4.80, w:PW-0.8, h:0, line:{color:c.col, width:0.75, transparency:40} });
    txt(s, c.meta, { x:px, y:4.86, w:PW, h:0.24, fontSize:9, color:MUTED, align:"center" });
    txt(s, [{ text:c.big, options:{ fontSize:18, bold:true, color:c.col } },
            { text:"　"+c.sub, options:{ fontSize:9, color:MUTED } }],
      { x:px, y:5.10, w:PW, h:0.34, align:"center" });
  });

  // 柱と柱のあいだ：何が次の柱へ渡るか
  [["制作","データ"],["外部に","開放"]].forEach((lab, i) => {
    const gx = X0 + PW + G/2 + i*(PW+G);
    txt(s, lab.map((t,k)=>({ text:t, options:{ breakLine:k<lab.length-1 } })),
      { x:gx-0.33, y:2.84, w:0.66, h:0.40, fontSize:9, bold:true, color:INKSOFT, align:"center",
        lineSpacingMultiple:1.1 });
    s.addShape(p.ShapeType.rightArrow, { x:gx-0.26, y:3.24, w:0.52, h:0.30, fill:{color:INKSOFT} });
  });

  // 土台（基壇）
  s.addShape(p.ShapeType.rect, { x:RX+0.15, y:5.72, w:RW-0.3, h:0.24, fill:{color:STEP} });
  s.addShape(p.ShapeType.rect, { x:RX, y:5.98, w:RW, h:0.52, fill:{color:INKSOFT} });
  txt(s, "土台 ｜ 中国の制作力 × 日本の品質保証 × AX（AIで制作工数を圧縮する）",
    { x:RX, y:5.98, w:RW, h:0.52, fontSize:12, bold:true, color:ONDARK, align:"center" });

  foot(s, "5期（2031年）の計画値。出所: 事業計画_Ver0.8.xlsx。②は年額契約で継続収益（ARR）になるが、①は案件ごと、③は取引ごとの売上");
}

p.writeFile({ fileName: __dirname + "/visual.pptx" }).then(f => console.log(f));
