"""
Random Character Designer の生成エンジン。

  parse_brief(brief)              : 軽い指示文（例: "悪魔・女の子・高露出"）を解釈して Spec にする
  generate(brief, seed, ...)      : Spec と seed から Character（設計結果）を組み立てる
  build_sheet(character)          : 設計結果を「キャラクターシート」テキストにする
  parse_sheet(text)               : シートから positive / negative を取り出す（ロック再現用）

seed が同じなら必ず同じキャラクターが出ます（random.Random(seed) のみを使用）。
"""

import random
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from . import data as D
from . import outfit_tags as OT

EXPOSURES = ("modest", "standard", "high")
EXPOSURE_JP = {"modest": "控えめ", "standard": "標準", "high": "高露出"}
CONSISTENCY = ("strict", "full")
TWISTS = ("auto", "classic", "surprise")


# ---------------------------------------------------------------------------
# 指示文のパース
# ---------------------------------------------------------------------------

@dataclass
class Spec:
    gender: Optional[str] = None       # "girl" / "boy"
    motif: Optional[str] = None        # 種族（race）
    theme: Optional[str] = None        # モチーフ（theme）
    role: Optional[str] = None
    role2: Optional[str] = None       # 指示文に服装系統が2つあれば2つ目（融合用）
    handheld: Optional[str] = None    # 指示文の手持ち（剣・杖・本…）
    archetype: Optional[str] = None
    exposure: Optional[str] = None
    hair_color: Optional[str] = None
    eye_color: Optional[str] = None
    theme_color: Optional[str] = None
    hair_styles: List[str] = field(default_factory=list)
    traits: List[str] = field(default_factory=list)
    eye_tags: Dict[str, str] = field(default_factory=dict)  # カテゴリ -> タグ（指示文で指定された目の特徴）
    extras: List[str] = field(default_factory=list)   # 認識できなかった語（そのまま通す）
    matched: List[str] = field(default_factory=list)  # ログ用


_SPLIT_RE = re.compile(r"[・,、，/／\s\n|｜;；]+")


def _syn_hits(token: str, syns: List[str]) -> bool:
    """同義語リストのいずれかが token に含まれるか。ASCII 語は単語境界で判定する。"""
    low = token.lower()
    for s in syns:
        s_low = s.lower()
        if s_low.isascii():
            if _ascii_syn_re(s_low).search(low):
                return True
        else:
            if s_low in low:
                return True
    return False


_SYN_RE_CACHE: Dict[str, "re.Pattern"] = {}


def _ascii_syn_re(s_low: str) -> "re.Pattern":
    """ASCII 同義語の単語境界つき正規表現をキャッシュする（同義語が多く re の内部キャッシュ(512)を溢れるため）"""
    pat = _SYN_RE_CACHE.get(s_low)
    if pat is None:
        pat = re.compile(r"(?<![a-z0-9])" + re.escape(s_low) + r"(?![a-z0-9])")
        _SYN_RE_CACHE[s_low] = pat
    return pat


def _lookup(token: str, table: Dict[str, List[str]]) -> List[str]:
    """同義語テーブルから token に一致するキーを（長い同義語優先で）列挙する。"""
    hits = []
    # 長い同義語を持つ項目を先に（"黒髪" を "黒" より優先する等）
    order = sorted(table.items(), key=lambda kv: -max(len(s) for s in kv[1]))
    for key, syns in order:
        if _syn_hits(token, syns):
            hits.append(key)
    return hits


def _all_tables() -> List[Dict[str, List[str]]]:
    return [
        D.GENDER_WORDS,
        {k: v["syn"] for k, v in D.MOTIFS.items()},
        {k: v["syn"] for k, v in D.ROLES.items()},
        {k: v["syn"] for k, v in D.ARCHETYPES.items()},
        D.EXPOSURE_WORDS,
        D.HAIR_COLOR_WORDS,
        D.EYE_COLOR_WORDS,
        D.HAIR_STYLE_WORDS,
        {k: v["syn"] for k, v in D.TRAIT_WORDS.items()},
        {str(k): v for k, v in D.EYE_WORDS.items()},
        {k: v["syn"] for k, v in D.HANDHELDS.items()},
    ]


def _extract_multiword(brief: str) -> Tuple[str, List[str]]:
    """
    空白を含む同義語（"shrine maiden", "light blue hair" など）は空白分割で壊れるので、
    先に全文から探して1トークンに置き換えておく（空白をアンダースコアに変換して退避）。
    """
    text = brief or ""
    found = []
    if " " not in text:
        return text, found
    for phrase, pat in _multiword_patterns():
        if pat.search(text):
            text = pat.sub(phrase.replace(" ", "_"), text)
            found.append(phrase)
    return text, found


_MULTIWORD = None


def _multiword_patterns():
    """空白を含む同義語の正規表現を一度だけコンパイルして使い回す（辞書が大きいので毎回コンパイルすると非常に遅い）"""
    global _MULTIWORD
    if _MULTIWORD is None:
        phrases = set()
        for table in _all_tables():
            for syns in table.values():
                for s in syns:
                    if " " in s:
                        phrases.add(s)
        _MULTIWORD = [(ph, re.compile(r"(?<![a-z0-9])" + re.escape(ph) + r"(?![a-z0-9])", re.IGNORECASE))
                      for ph in sorted(phrases, key=len, reverse=True)]
    return _MULTIWORD


def parse_brief(brief: str) -> Spec:
    spec = Spec()
    text, _ = _extract_multiword(brief)
    tokens = [t.strip() for t in _SPLIT_RE.split(text) if t.strip()]

    for tok in tokens:
        tok = tok.replace("_", " ")
        matched = False

        for g in _lookup(tok, D.GENDER_WORDS):
            spec.gender = g
            matched = True
        for m in _lookup(tok, {k: v["syn"] for k, v in D.MOTIFS.items()}):
            if D.MOTIFS[m].get("kind") == "theme":
                if spec.theme is None:
                    spec.theme = m
            elif spec.motif is None:
                spec.motif = m
            matched = True
        for r in _lookup(tok, {k: v["syn"] for k, v in D.ROLES.items()}):
            if spec.role is None:
                spec.role = r
            elif spec.role2 is None and r != spec.role:
                spec.role2 = r
            matched = True
        for a in _lookup(tok, {k: v["syn"] for k, v in D.ARCHETYPES.items()}):
            if spec.archetype is None:
                spec.archetype = a
            matched = True
        for e in _lookup(tok, D.EXPOSURE_WORDS):
            spec.exposure = e
            matched = True
        for h in _lookup(tok, D.HAIR_COLOR_WORDS):
            spec.hair_color = h
            matched = True
        for e in _lookup(tok, D.EYE_COLOR_WORDS):
            spec.eye_color = e
            matched = True
        for s in _lookup(tok, D.HAIR_STYLE_WORDS):
            if s not in spec.hair_styles:
                spec.hair_styles.append(s)
            matched = True
        for t in _lookup(tok, {k: v["syn"] for k, v in D.TRAIT_WORDS.items()}):
            if t not in spec.traits:
                spec.traits.append(t)
            matched = True
        for cat_tag in _lookup(tok, {k: v for k, v in D.EYE_WORDS.items()}):
            spec.eye_tags[cat_tag[0]] = cat_tag[1]
            matched = True
        for h in _lookup(tok, {k: v["syn"] for k, v in D.HANDHELDS.items()}):
            if spec.handheld is None:
                spec.handheld = h
            matched = True

        # 単色ワード（赤・青…）は、他に何も一致しなかった時だけテーマカラーとして扱う
        if not matched:
            colors = _lookup(tok, D.COLOR_WORDS)
            if colors:
                spec.theme_color = colors[0]
                matched = True

        if matched:
            spec.matched.append(tok)
        else:
            spec.extras.append(tok)

    return spec


def parse_exclude(text: str) -> Dict[str, set]:
    """
    除外欄（例: "水着, バニー, 高露出, ヤンデレ"）を解釈して、
    ランダム選択のプールから外す motif / role / archetype / exposure のキー集合にする。
    """
    out = {"motif": set(), "role": set(), "archetype": set(), "exposure": set()}
    tables = [
        ("motif", {k: v["syn"] for k, v in D.MOTIFS.items()}),
        ("role", {k: v["syn"] for k, v in D.ROLES.items()}),
        ("archetype", {k: v["syn"] for k, v in D.ARCHETYPES.items()}),
        ("exposure", D.EXPOSURE_WORDS),
    ]
    text2, _ = _extract_multiword(text)
    for tok in _SPLIT_RE.split(text2):
        tok = tok.strip().replace("_", " ")
        if not tok:
            continue
        # 「サキュバス衣装」がモチーフ「悪魔」(同義語"サキュバス")まで巻き込まないよう、
        # 最も長い同義語で一致した辞書だけに適用する
        best_len, best = 0, None
        for name, table in tables:
            for key in _lookup(tok, table):
                length = max(len(syn) for syn in table[key] if _syn_hits(tok, [syn]))
                if length > best_len:
                    best_len, best = length, (name, key)
        if best:
            out[best[0]].add(best[1])
    return out


def _without(pool, excluded) -> list:
    """プールから除外分を引く。全部消えてしまう場合は除外を無視して元のプールを返す。"""
    pool = list(pool)
    kept = [x for x in pool if x not in excluded]
    return kept or pool


# ---------------------------------------------------------------------------
# 生成結果
# ---------------------------------------------------------------------------

@dataclass
class Character:
    seed: int
    brief: str
    gender: str
    motif: str
    role: str
    archetype: str
    exposure: str
    twist: str                      # "classic" / "surprise" / "fixed"
    twist_role: bool
    twist_arch: bool
    palette: Tuple[str, str, str]   # main, sub, accent
    pattern: str
    material: str
    hair: List[str]
    eyes: List[str]
    skin: str
    body: List[str]
    features: List[str]
    outfit: List[str]
    accessories: List[str]
    prop: str
    expression: str
    pose: str
    extras: List[str]
    unrecognized: List[str]
    excluded: Dict[str, set]
    prompt_style: str
    expression_pose: str        # "expression_only" / "both" / "none"
    consistency: str = "full"   # "strict" = booru タグ骨格・2色・不安定要素なし / "full" = 詳細説明文
    emphasis: float = 1.6       # strict での重み（主役の服・記号・目の形）。1.0 以下で無効。Anima は SDXL より強めが必要
    eye_intensity: str = "normal"   # 目の形の強弱 slight / normal / strong
    role2: str = ""                 # 融合した2つ目の服装系統（無ければ空）
    exposure_tags: List[str] = field(default_factory=list)  # 高露出のときの露出部位タグ
    theme: str = ""                 # モチーフ（テーマ）のキー（無ければ空）
    handheld_tags: List[str] = field(default_factory=list)  # 手持ちの booru タグ（先頭に重み）
    body_sentences: List[str] = field(default_factory=list)  # 体型指定の文章
    embellish_tags: List[str] = field(default_factory=list)  # 装飾レイヤーのタグ
    embellish_nl: List[str] = field(default_factory=list)    # 装飾レイヤーの文章断片
    iconic_tag: str = ""                                     # 象徴的な一点（重み付き）
    detail_level: int = 0
    hair_special_nl: List[str] = field(default_factory=list)  # 髪の個性の文章断片
    silhouette: str = ""
    shape_lang: str = ""
    zones: List[str] = field(default_factory=list)
    silhouette_tags: List[str] = field(default_factory=list)
    pattern_base: str = ""      # スタイル修飾なしの模様名
    print_tag: str = ""         # strict で出す booru の print タグ（無ければ空）
    outfit_detail: List[str] = field(default_factory=list)  # 説明文テンプレート版の服装（strict ではシートのメモ用）
    eye_choice: Dict[str, str] = field(default_factory=dict)  # 目の各カテゴリの選択（negative 用）
    omitted: List[str] = field(default_factory=list)        # strict で省いた不安定要素

    @property
    def main(self):
        return self.palette[0]

    @property
    def sub(self):
        return self.palette[1]

    @property
    def accent(self):
        return self.palette[2]


class _SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def _fill(template: str, slots: Dict[str, str]) -> str:
    return template.format_map(_SafeDict(slots))


def _pick(rng: random.Random, seq, default=None):
    seq = list(seq)
    if not seq:
        return default
    return rng.choice(seq)


def _sample(rng: random.Random, seq, k: int) -> List[str]:
    seq = list(seq)
    if k <= 0 or not seq:
        return []
    return rng.sample(seq, min(k, len(seq)))


def _weighted_pick(rng: random.Random, weights: Dict[str, int]) -> str:
    keys = list(weights.keys())
    return rng.choices(keys, weights=[weights[k] for k in keys], k=1)[0]


_OPTIONAL_RE = None


def _optional_patterns():
    """OPTIONAL_ITEM_KEYWORDS を事前コンパイル（data の再読み込み時は engine も再読み込みされるので作り直される）"""
    global _OPTIONAL_RE
    if _OPTIONAL_RE is None:
        _OPTIONAL_RE = [(kw, prob, re.compile(r"(?<![a-z])" + re.escape(kw) + r"(?![a-z])")) for kw, prob in D.OPTIONAL_ITEM_KEYWORDS.items()]
    return _OPTIONAL_RE


def _expand_items(items, variant: float, keep: Dict[str, bool], rng: random.Random) -> List[str]:
    """
    服装リストの記法を展開する。
      - list       : どれか1つ（variant で位置を決めるので、説明文版とタグ版で選択肢の数が同じなら同じ選択になる）
      - "?item"    : 任意。OPTIONAL_ITEM_KEYWORDS に該当すればその確率、無ければ 50%。
                     採否は「何番目の ? アイテムか」で説明文版とタグ版が共有する（順番を揃えて書く）
      - OPTIONAL_ITEM_KEYWORDS に該当 : 指定確率（採否はキーワードで共有）
    先頭（主役の服）は必ず残す。
    """
    out: List[str] = []
    q_index = 0
    for i, it in enumerate(items):
        if isinstance(it, list):
            it = it[min(int(variant * len(it)), len(it) - 1)]
        if not it:
            continue
        if i == 0:
            out.append(it.lstrip("?"))
            continue
        low = it.lower().lstrip("?")
        matched = next(((kw, prob) for kw, prob, pat in _optional_patterns() if pat.search(low)), None)
        if it.startswith("?"):
            key = f"?{q_index}"
            q_index += 1
            if key not in keep:
                keep[key] = rng.random() < (matched[1] if matched else 0.5)
            if keep[key]:
                out.append(it[1:])
            continue
        if matched:
            kw, prob = matched
            if kw not in keep:
                keep[kw] = rng.random() < prob
            if not keep[kw]:
                continue
        out.append(it)
    return out


_SLOT_RE = None


def _slot_patterns():
    global _SLOT_RE
    if _SLOT_RE is None:
        _SLOT_RE = [(slot, [re.compile(r"(?<![a-z])" + re.escape(k) + r"(?![a-z])") for k in kws]) for slot, kws in D.OUTFIT_SLOTS]
    return _SLOT_RE


def classify_slot(item: str) -> str:
    """服装アイテムを部位スロットに分類する（最初に一致したもの。どれにも当たらなければ accessory）"""
    low = item.lower()
    for slot, pats in _slot_patterns():
        if any(p.search(low) for p in pats):
            return slot
    return "accessory"


def fuse_outfits(base: List[str], flavor: List[str], rng: random.Random) -> List[str]:
    """
    2系統の服装を矛盾なく融合する。
      - base（土台）はそのまま。主役の服・丈・袖・露出の切り方は土台が決める
      - flavor（風味）からは頭・顔・手・首・羽織り・腰・識別タグ・小物だけを、スロットが空いていれば取り込む
      - 頭・羽織り・足・脚は一定確率で flavor 側が土台側を置き換える（どちらが主か seed で揺らぐ）
      - 上半身・下半身・全身・袖・説明タグは flavor から取らない（ここが矛盾の元）
    """
    out = list(base)
    taken: Dict[str, List[int]] = {}
    for i, it in enumerate(base):
        taken.setdefault(classify_slot(it), []).append(i)
    if "full" in taken:
        taken.setdefault("top", []); taken.setdefault("bottom", [])
    counts: Dict[str, int] = {}
    replaced = set()
    for it in flavor:
        slot = classify_slot(it)
        limit = D.FUSION_TAKE.get(slot)
        if not limit or counts.get(slot, 0) >= limit:
            continue
        if it in out:
            continue
        if taken.get(slot):
            prob = D.FUSION_OVERRIDE.get(slot, 0.0)
            if 0 in taken[slot]:
                prob = 0.0  # 先頭＝主役の服は置き換えない
            if slot not in replaced and prob and rng.random() < prob:
                # 土台側の同スロットを flavor 側で置き換える
                for idx in taken[slot]:
                    out[idx] = ""
                replaced.add(slot)
            elif slot in ("identity", "accessory", "neck"):
                pass  # 複数可
            else:
                continue
        out.append(it)
        counts[slot] = counts.get(slot, 0) + 1
    return [x for x in out if x]


def merge_race_theme(race: dict, theme: Optional[dict]) -> dict:
    """種族（体の記号・肌・配色の軸）にテーマ（模様・小物・差し色の軸）を重ねた「合成モチーフ」を作る"""
    m = dict(race)
    m["theme_features"] = []
    if not theme:
        return m
    m["theme_features"] = list(theme.get("features_primary", [])) + list(theme.get("features_optional", []))
    if not race.get("palette_only"):
        m["palettes"] = list(race["palettes"]) * 2 + list(theme["palettes"]) * 2
    m["patterns"] = list(theme["patterns"]) or list(race["patterns"])
    m["props"] = list(race["props"]) + list(theme["props"])
    for key in ("classic_roles", "gap_roles", "classic_arch", "gap_arch", "hair_colors", "eye_colors"):
        merged = list(race.get(key, []))
        merged += [x for x in theme.get(key, []) if x not in merged]
        m[key] = merged
    if not race.get("signature_print") and theme.get("signature_print"):
        m["signature_print"] = theme["signature_print"]
    if not race.get("pupils") and theme.get("pupils"):
        m["pupils"] = theme["pupils"]
    return m


def build_handheld(key: str, rng: random.Random, slots: Dict[str, str]) -> Tuple[List[str], str]:
    """手持ち（武器・小道具）を seed で決めて、booru タグ列と形状を固定する文章を返す"""
    spec = D.HANDHELDS[key]
    type_desc, type_tag = _pick(rng, spec["types"])
    parts = [_fill(_pick(rng, opts), slots) for opts in spec["slots"].values()]
    hold_desc, hold_tag = _pick(rng, spec["holds"])
    hold_desc = _fill(hold_desc, slots)
    tags = []
    for t in list(spec["tags"]) + type_tag.split(", ") + hold_tag.split(", "):
        if t not in tags:
            tags.append(t)
    desc = f"{type_desc} with {', '.join(parts)}, {hold_desc}"
    return tags, desc


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for it in items:
        key = it.strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(it.strip())
    return out


def build_embellishments(level: int, outfit: List[str], gender: str, exposure: str, shape: str, tech_affinity: bool,
                         features_text: str, rng: random.Random, slots: Dict[str, str],
                         zones: Optional[List[str]] = None) -> Tuple[List[str], List[str], str]:
    """
    装飾レイヤー。服装の部位スロットと衝突しないようにアドオンを選ぶ。
    返り値: (タグ列, 文章の断片, 象徴的な一点のタグ)
    """
    n_small, want_iconic = D.EMBELLISH_LEVELS.get(level, (0, False))
    if n_small == 0 and not want_iconic:
        return [], [], ""
    taken = {classify_slot(t) for t in outfit}
    used: set = set()
    out_tags: List[str] = []
    nl_parts: List[str] = []
    iconic_tag = ""
    outfit_text = " ".join(outfit).lower()

    def usable(entry) -> bool:
        if entry.get("male") is False and gender == "boy":
            return False
        if entry.get("exposure") and exposure not in entry["exposure"]:
            return False
        if entry.get("shape") and not shape:
            return False
        if entry.get("requires") and entry["requires"] not in outfit_text:
            return False
        slot = entry["slot"]
        if slot in used:
            return False
        if slot in taken and not entry.get("replace"):
            return False
        if slot == "tail" and "tail" in features_text:
            return False
        if slot == "head" and ("hood" in outfit_text or "hat" in outfit_text or "veil" in outfit_text):
            return False
        return True

    def apply(entry):
        nonlocal outfit
        slot = entry["slot"]
        if entry.get("replace") and slot in taken:
            # 服の同部位を置き換える（先頭＝主役の服は残す）
            outfit[:] = [t for i, t in enumerate(outfit) if i == 0 or classify_slot(t) != slot]
        used.add(slot)
        fill = dict(slots, shape=shape or "ornate")
        out_tags.extend(_fill(t, fill) for t in entry["tags"])
        nl_parts.append(_fill(entry["nl"], fill))  # {poss} は _SafeDict により残る

    if want_iconic:
        cands = [x for x in D.EMBELLISHMENTS["iconic"] if usable(x)]
        if cands:
            entry = _pick(rng, cands)
            apply(entry)
            iconic_tag = _fill(entry["tags"][-1], dict(slots, shape=shape or "ornate"))
    weights = dict(D.EMBELLISH_WEIGHTS)
    if tech_affinity:
        weights["tech"] = 4
    # 非対称化を1つは優先的に入れる（VTuber 的な「読める」シルエット）
    order = ["asymmetry"] + rng.choices(list(weights), weights=list(weights.values()), k=n_small * 3)

    def in_zone(entry) -> bool:
        return not zones or D.SLOT_ZONE.get(entry["slot"], "torso") in zones

    for cat in order:
        if len(nl_parts) - (1 if iconic_tag else 0) >= n_small:
            break
        cands = [x for x in D.EMBELLISHMENTS[cat] if usable(x)]
        # 情報量ゾーン: 集めるゾーンのアドオンを優先（無ければ他から）
        zoned = [x for x in cands if in_zone(x)]
        if zoned:
            apply(_pick(rng, zoned))
        elif cands and rng.random() < 0.3:
            apply(_pick(rng, cands))
    return out_tags, nl_parts, iconic_tag


def build_hair_special(level: int, hair: List[str], hair_color: str, palette: Tuple[str, str, str], shape: str,
                       rng: random.Random, prefer: Optional[List[str]] = None) -> Tuple[List[str], List[str]]:
    """髪の個性（装飾量に連動）。土台の髪型と結び方が衝突しないよう判定する"""
    n_sil, n_col, n_tie = D.HAIR_SPECIAL_LEVELS.get(level, (0, 0, 0))
    if not (n_sil or n_col or n_tie):
        return [], []
    base = " ".join(hair).lower()
    main, sub, accent = palette
    def hair_of(color):
        return D.COLOR_TO_HAIR.get(color, color + " hair").replace(" hair", "")
    fill = {"main": main, "sub": sub, "accent": accent, "shape": shape or "star",
            "hair_base": hair_color.replace(" hair", ""), "sub_hair": hair_of(sub), "accent_hair": hair_of(accent)}
    if fill["sub_hair"] == fill["hair_base"]:
        fill["sub_hair"] = hair_of(accent)
    if fill["accent_hair"] == fill["hair_base"]:
        fill["accent_hair"] = hair_of(sub)
    tags: List[str] = []
    nl: List[str] = []
    def take(cat, n, allow):
        cands = [x for x in D.HAIR_SPECIAL[cat] if allow(x)]
        # シルエットに合う語を含む候補を優先（半分の確率）
        if prefer and rng.random() < 0.5:
            pref = [x for x in cands if any(p in " ".join(x["tags"]).lower() for p in prefer)]
            if pref:
                cands = pref
        for x in _sample(rng, cands, n):
            tags.extend(_fill(t, fill) for t in x["tags"])
            nl.append(_fill(x["nl"], fill))
    has_tie = any(k in base for k in D.HAIR_TIE_KEYWORDS)
    is_short = "short" in base or "bob" in base
    take("silhouette", n_sil, lambda x: not (x.get("shape") and not shape) and not (x.get("length") and is_short))
    if n_col and rng.random() < D.HAIR_SPECIAL_PROB.get(level, 0):
        take("color", n_col, lambda x: True)
    if n_tie and not has_tie and not is_short:
        take("tie", n_tie, lambda x: True)
    return tags, nl


def _role_available(role: str, gender: str) -> bool:
    role = D.ROLE_ALIASES.get(role, role)
    if role not in D.ROLES:
        return False
    if gender == "boy" and "male" not in D.ROLES[role]:
        return False
    return True


def _all_roles(gender: str) -> List[str]:
    return [r for r in D.ROLES if _role_available(r, gender)]


# ---------------------------------------------------------------------------
# 生成本体
# ---------------------------------------------------------------------------

def generate(
    brief: str,
    seed: int,
    twist: str = "auto",
    exposure: str = "auto",
    personality: str = "auto",
    prompt_style: str = "tags",
    expression_pose: str = "expression_only",
    motif: str = "auto",
    role: str = "auto",
    exclude: str = "",
    consistency: str = "strict",
    emphasis: float = 1.6,
    eye_shape: str = "auto",
    role2: str = "none",
    theme: str = "auto",
    main_color: str = "auto",
    hair_color: str = "auto",
    handheld: str = "none",
    bust: str = "auto",
    height: str = "auto",
    build: str = "auto",
    detail_level: int = 2,
    silhouette: str = "auto",
    shape_lang: str = "auto",
) -> Character:
    strict = consistency == "strict"
    rng = random.Random(seed)
    spec = parse_brief(brief)
    excluded = parse_exclude(exclude)

    # ドロップダウン指定（auto 以外）は brief より優先
    if motif != "auto" and motif in D.MOTIFS:
        if D.MOTIFS[motif].get("kind") == "theme":
            spec.theme = motif
        else:
            spec.motif = motif
    if theme in D.THEMES:
        spec.theme = theme
    # 服の色 / 髪の色のドロップダウン（auto 以外は指示文より優先）
    if main_color != "auto" and main_color in D.COLOR_JP:
        spec.theme_color = main_color
    if hair_color != "auto" and hair_color in D.HAIR_COLOR_JP:
        spec.hair_color = hair_color
    if role != "auto" and role in D.ROLES:
        spec.role = role

    # --- 性別 -------------------------------------------------------------
    gender = spec.gender or "girl"

    # --- モチーフ ---------------------------------------------------------
    if spec.motif:
        motif_key = spec.motif
    else:
        weights = {k: w for k, w in D.MOTIF_WEIGHTS.items() if k not in excluded["motif"]} or dict(D.MOTIF_WEIGHTS)
        motif_key = _weighted_pick(rng, weights)
    # --- テーマ（モチーフ）: 指定 > "none" > 確率で付与 -----------------------
    if spec.theme:
        theme_key = spec.theme
    elif theme == "none":
        theme_key = None
    elif theme == "random" or rng.random() < D.THEME_PROB:
        pool_t = [k for k in D.THEMES if k not in excluded["motif"]] or list(D.THEMES)
        theme_key = _pick(rng, pool_t)
    else:
        theme_key = None
    motif = merge_race_theme(D.MOTIFS[motif_key], D.MOTIFS[theme_key] if theme_key else None)

    # --- ギャップ（意外性）判定 ------------------------------------------
    role_fixed = spec.role is not None
    arch_fixed = personality != "auto" or spec.archetype is not None

    if twist == "auto":
        surprise = rng.random() < 0.4
    else:
        surprise = twist == "surprise"

    # surprise の時、役割と性格のどちらを外すか（両方 / 役割だけ / 性格だけ）
    twist_role = twist_arch = False
    if surprise:
        mode = rng.choices(["both", "role", "arch"], weights=[4, 4, 2], k=1)[0]
        twist_role = mode in ("both", "role") and not role_fixed
        twist_arch = mode in ("both", "arch") and not arch_fixed
        # どちらも固定されていて外せない時は、固定されていない方があればそちらを外す
        if not twist_role and not twist_arch:
            if not role_fixed:
                twist_role = True
            elif not arch_fixed:
                twist_arch = True

    # --- 服装系統（役割） -------------------------------------------------
    if role_fixed:
        role_key = spec.role
    else:
        if twist_role:
            pool = [D.ROLE_ALIASES.get(r, r) for r in motif["gap_roles"]]
        else:
            pool = [D.ROLE_ALIASES.get(r, r) for r in motif["classic_roles"]]
        pool = [r for r in pool if _role_available(r, gender) and r not in excluded["role"]]
        if not pool:
            # human モチーフなど候補が無い場合は全系統から（surprise なら王道を除く）
            pool = _all_roles(gender)
            if twist_role:
                classic = set(D.ROLE_ALIASES.get(r, r) for r in motif["classic_roles"])
                pool = [r for r in pool if r not in classic] or pool
            pool = _without(pool, excluded["role"])
        role_key = _pick(rng, pool)
    role = D.ROLES[role_key]

    # --- 融合する2つ目の服装系統 -----------------------------------------
    if role2 in D.ROLES:
        role2_key = role2
    elif role2 == "random":
        pool2 = [r for r in _all_roles(gender) if r != role_key and r not in excluded["role"]] or [r for r in _all_roles(gender) if r != role_key]
        role2_key = _pick(rng, pool2)
    elif role2 == "none" and spec.role2 and spec.role2 != role_key and _role_available(spec.role2, gender):
        role2_key = spec.role2
    else:
        role2_key = None
    if role2_key == role_key:
        role2_key = None
    role_b = D.ROLES[role2_key] if role2_key else None

    # --- 性格アーキタイプ -------------------------------------------------
    if personality != "auto":
        arch_key = personality
    elif spec.archetype is not None:
        arch_key = spec.archetype
    else:
        pool = [a for a in (motif["gap_arch"] if twist_arch else motif["classic_arch"]) if a not in excluded["archetype"]]
        if not pool:
            pool = list(D.ARCHETYPES.keys())
            if twist_arch:
                pool = [a for a in pool if a not in motif["classic_arch"]] or pool
            pool = _without(pool, excluded["archetype"])
        arch_key = _pick(rng, pool)
    arch = D.ARCHETYPES[arch_key]

    if role_fixed and arch_fixed:
        twist_label = "fixed"
    elif twist_role or twist_arch:
        twist_label = "surprise"
    else:
        twist_label = "classic"

    # --- 露出 -------------------------------------------------------------
    if exposure in EXPOSURES:
        exp = exposure
    elif spec.exposure in EXPOSURES:
        exp = spec.exposure
    else:
        cands = [(e, w) for e, w in zip(EXPOSURES, [2, 5, 3]) if e not in excluded["exposure"]] or list(zip(EXPOSURES, [2, 5, 3]))
        exp = rng.choices([e for e, _ in cands], weights=[w for _, w in cands], k=1)[0]

    # --- テーマカラー（3色ルール） ---------------------------------------
    if motif.get("palette_only"):
        palette_pool = list(motif["palettes"])
    else:
        palette_pool = list(motif["palettes"]) * 2 + list(arch["palettes"]) + list(role.get("palettes", []))
        if role_b:
            palette_pool += list(role_b.get("palettes", []))
    main, sub, accent = _pick(rng, palette_pool)
    if spec.theme_color:
        main = spec.theme_color
    if sub == main:
        sub = accent
    if sub == main:
        sub = next(c for c in D.CONTRAST_FALLBACK if c != main)
    if accent in (main, sub):
        accent = next(c for c in D.CONTRAST_FALLBACK if c not in (main, sub))
    palette = (main, sub, accent)

    if motif.get("signature_print"):
        base_pattern = motif["signature_print"]
        pattern = base_pattern
    else:
        base_pattern = _pick(rng, motif["patterns"]) or "ribbon motif"
        pattern = f"{_pick(rng, D.PATTERN_STYLES)} {base_pattern}"
    material = _pick(rng, role.get("materials", [])) or "cotton"
    girl_or_boy = "girl" if gender == "girl" else "boy"
    slots = {"main": main, "sub": sub, "accent": accent, "pattern": pattern, "material": material, "girl_or_boy": girl_or_boy}
    # strict: 色を main + accent の2色に圧縮（{sub} は main に寄せる）
    slots_strict = {"main": main, "sub": main, "accent": accent, "pattern": pattern, "material": "", "girl_or_boy": girl_or_boy}
    fill_slots = slots  # 記号・小物は3色のまま（2色圧縮は服タグにだけ適用）
    omitted: List[str] = []

    def _unstable(text: str) -> bool:
        low = text.lower()
        return any(k in low for k in D.UNSTABLE_KEYWORDS)

    # --- 髪 ---------------------------------------------------------------
    if spec.hair_color:
        hair_color = spec.hair_color
    elif motif.get("hair_from_main"):
        hair_color = D.COLOR_TO_HAIR.get(main, "blue hair")
    elif rng.random() < 0.5:
        # 「髪か瞳にテーマカラーを乗せる」ルール: main か sub を髪色にする
        hair_color = D.COLOR_TO_HAIR.get(_pick(rng, [main, sub]), _pick(rng, arch["hair_colors"]))
    else:
        hair_color = _pick(rng, list(arch["hair_colors"]) + list(motif["hair_colors"]))

    if spec.hair_styles:
        hair_style = ", ".join(spec.hair_styles)
    else:
        hair_style = _pick(rng, arch["hair_styles"])
    style_low = hair_style.lower()
    hair = [hair_color]
    # 長さ（型から推定。推定できなければランダム）
    length = next((tag for kw, tag in D.HAIR_LENGTH_KEYWORDS if kw in style_low), None)
    if not length and not spec.hair_styles:
        length = rng.choices(["very long hair", "long hair", "medium hair", "short hair"], weights=[2, 4, 3, 2], k=1)[0]
    if length:
        hair.append(length)
    # 質感（型に含まれていなければ追加）
    if not any(k in style_low for k in D.HAIR_TEXTURE_KEYWORDS):
        hair.append(_pick(rng, D.HAIR_TEXTURES))
    hair.append(hair_style)
    if motif.get("hair_extra"):
        hair.append(motif["hair_extra"])
    # 前髪・横髪
    if "bangs" not in style_low and "hiding the face" not in style_low and "covering" not in style_low:
        hair.append(_pick(rng, D.BANGS))
    if "sidelocks" not in style_low and rng.random() < 0.7:
        hair.append(_pick(rng, D.SIDELOCKS))
    # 差し色・アホ毛など（40%で1つ。型に ahoge があれば重複させない）
    if rng.random() < 0.4:
        extra = _fill(_pick(rng, D.HAIR_EXTRAS), slots)
        if not ("ahoge" in extra and "ahoge" in style_low):
            hair.append(extra)

    # --- 瞳 ---------------------------------------------------------------
    if spec.eye_color:
        eye_color = spec.eye_color
    elif rng.random() < 0.55:
        # 「瞳はアクセントカラー」ルール
        eye_color = D.COLOR_TO_EYE.get(accent, _pick(rng, motif["eye_colors"]))
    else:
        eye_color = _pick(rng, motif["eye_colors"])
    eyes = [eye_color]
    if "heterochromia" in spec.traits and "heterochromia" not in eye_color:
        eyes.insert(0, "heterochromia")
    # 目の構造: 形 / 開き具合 / 瞳孔 / ハイライト / まつ毛 / 眉 / メイク / その他
    profile = D.EYE_PROFILES.get(arch_key, {"shape": ["tsurime", "tareme"]})
    chosen: Dict[str, str] = {}
    if eye_shape != "auto" and eye_shape in D.EYE_SHAPES:
        chosen["shape"] = eye_shape
    elif "shape" in spec.eye_tags:
        chosen["shape"] = spec.eye_tags["shape"]
    else:
        chosen["shape"] = _pick(rng, profile.get("shape") or ["tsurime", "tareme"])
    for cat in ("lid", "pupils", "highlights", "lashes", "brows", "makeup", "details"):
        if cat in spec.eye_tags:
            chosen[cat] = spec.eye_tags[cat]
            continue
        if cat == "pupils" and motif.get("pupils") and "heterochromia" not in eye_color:
            chosen[cat] = _pick(rng, motif["pupils"])   # モチーフ由来の瞳孔は必ず出す
            continue
        cands = profile.get(cat)
        if cands and rng.random() < D.EYE_PROBS[cat]:
            chosen[cat] = _pick(rng, cands)
    if "size" not in spec.eye_tags and rng.random() < 0.5:
        chosen["size"] = _pick(rng, D.EYE_SIZES)
    elif "size" in spec.eye_tags:
        chosen["size"] = spec.eye_tags["size"]
    eye_intensity = rng.choices([k for k, _, _ in D.EYE_INTENSITY], weights=D.EYE_INTENSITY_WEIGHTS, k=1)[0]
    eye_order = ("shape", "size", "lid", "pupils", "highlights", "lashes", "brows", "makeup", "details")
    eyes += [_fill(chosen[cat], slots) for cat in eye_order if cat in chosen]

    # --- 肌・体型 ---------------------------------------------------------
    skin = _fill(motif.get("skin") or "fair skin", slots)
    if "dark skin" in spec.traits:
        skin = "dark skin"
    elif arch_key == "gal" and rng.random() < 0.5 and not spec.traits:
        skin = "tan skin"

    body: List[str] = []
    for t in spec.traits:
        if t in ("dark skin", "heterochromia"):
            continue
        if gender == "boy" and D.TRAIT_WORDS[t]["female_only"]:
            continue
        body.append(t)
    arch_body = [b for b in arch["body"] if not (gender == "boy" and b in ("mature female", "small breasts", "curvy"))]
    if not body:
        body.extend(arch_body or [_pick(rng, D.BODY_DEFAULT_FEMALE if gender == "girl" else D.BODY_DEFAULT_MALE)])
    if gender == "girl" and not any("breasts" in b or "chest" in b for b in body):
        if "petite" in body:
            chest = rng.choices(D.CHEST_SIZES, weights=[6, 3, 1], k=1)[0]
        elif "curvy" in body or "mature female" in body:
            chest = rng.choices(D.CHEST_SIZES, weights=[1, 3, 6], k=1)[0]
        else:
            chest = rng.choices(D.CHEST_SIZES, weights=[3, 4, 3], k=1)[0]
        body.append(chest)
    motif_body = [b for b in motif.get("body", []) if gender == "girl"]
    if motif_body and not spec.traits and not arch["body"]:
        body = [b for b in body if "breasts" not in b] + motif_body
    if arch_key == "mesugaki" and "petite" not in body:
        body.insert(0, "petite")
    # --- 体型の指定（指定が無ければ従来どおり推奨のまま） ---------------------
    body_sentences: List[str] = []
    if height in D.HEIGHT_LEVELS:
        tags_h, nl_h = D.HEIGHT_LEVELS[height]
        body = [b for b in body if b not in D.BODY_HEIGHT_TAGS] + tags_h
        if nl_h:
            body_sentences.append(f"{'She' if gender == 'girl' else 'He'} is {nl_h}.")
    if build in D.BUILD_LEVELS:
        tags_b, nl_b = D.BUILD_LEVELS[build]
        body = [b for b in body if b not in D.BODY_BUILD_TAGS] + tags_b
        if nl_b:
            body_sentences.append(f"{'Her' if gender == 'girl' else 'His'} build is {nl_b}.")
    if gender == "girl" and bust != "auto":
        level = next((lv for lv in D.BUST_LEVELS if lv[0] == bust or lv[0].split(" ")[0] == str(bust)), None)
        if level:
            body = [b for b in body if b not in D.BODY_BUST_TAGS] + list(level[1])
            body_sentences.append(f"Her breasts are {level[2]}.")
    body = _dedupe(body)

    # --- モチーフの記号 ---------------------------------------------------
    features = []
    primary_pool = list(motif["features_primary"])
    optional_pool = list(motif["features_optional"])
    if strict:
        omitted += [_fill(f, slots) for f in primary_pool + optional_pool if _unstable(f)]
        primary_pool = [f for f in primary_pool if not _unstable(f)]
        optional_pool = [f for f in optional_pool if not _unstable(f)]
    primary = _pick(rng, primary_pool) or (_pick(rng, optional_pool) if strict else None)
    if primary:
        features.append(primary)
    n_opt = 1 if strict else rng.randint(1, 2)
    features += _sample(rng, [f for f in optional_pool if f != primary], n_opt)
    theme_pool = list(motif.get("theme_features", []))
    if strict:
        omitted += [_fill(f, slots) for f in theme_pool if _unstable(f)]
        theme_pool = [f for f in theme_pool if not _unstable(f)]
    features += _sample(rng, theme_pool, 1 if strict else rng.randint(1, 2))
    features = [_fill(f, fill_slots) for f in features]

    # --- 服装 -------------------------------------------------------------
    if gender == "boy" and "male" in role:
        outfit_src = role["male"][exp]
    else:
        outfit_src = role["outfits"][exp]
    variant = rng.random()          # 選択肢の位置（説明文版・タグ版で共有）
    keep: Dict[str, bool] = {}      # 任意小物の採用判断（同上）
    outfit_detail = [_fill(o, slots).replace("print print", "print") for o in _expand_items(outfit_src, variant, keep, rng)]
    fuse_seed = rng.random()        # 融合の置き換え判断（説明文版・タグ版で共有）
    if role_b:
        src_b = role_b["male"][exp] if (gender == "boy" and "male" in role_b) else role_b["outfits"][exp]
        detail_b = [_fill(o, slots).replace("print print", "print") for o in _expand_items(src_b, variant, dict(keep), random.Random(int(fuse_seed * 1e9)))]
        outfit_detail = fuse_outfits(outfit_detail, detail_b, random.Random(int(fuse_seed * 1e9) + 1))
    if arch.get("footwear"):
        outfit_detail = [o for o in outfit_detail if not any(k in o for k in D.FOOTWEAR_KEYWORDS)]
        outfit_detail.append(_fill(arch["footwear"], slots))
    if strict:
        # booru の正規タグ列（先頭が主役の服）
        tag_src = OT.OUTFIT_TAGS[role_key]["male" if gender == "boy" else "female"][exp]
        outfit = [_fill(t, slots_strict) for t in _expand_items(tag_src, variant, keep, rng)]
        if role_b:
            tag_b = OT.OUTFIT_TAGS[role2_key]["male" if gender == "boy" else "female"][exp]
            tags_b = [_fill(t, slots_strict) for t in _expand_items(tag_b, variant, dict(keep), random.Random(int(fuse_seed * 1e9)))]
            outfit = fuse_outfits(outfit, tags_b, random.Random(int(fuse_seed * 1e9) + 1))
        if arch.get("footwear_tags"):
            outfit = [t for t in outfit if not any(k in t for k in D.FOOTWEAR_KEYWORDS)]
            outfit += [_fill(t, slots_strict) for t in arch["footwear_tags"]]
    else:
        outfit = list(outfit_detail)

    # --- 性格を示す小物 ---------------------------------------------------
    feature_text = " ".join(features).lower()
    acc_pool = [a for a in arch["accessories"] if not (a == "fang" and "fang" in feature_text)]
    if strict:
        omitted += [_fill(a, slots) for a in acc_pool if _unstable(a)]
        acc_pool = [a for a in acc_pool if not _unstable(a)]
    accessories = [_fill(a, fill_slots) for a in _sample(rng, acc_pool, 1 if strict else rng.randint(1, 2))]
    if "glasses" in spec.traits and not any("glasses" in o for o in outfit):
        accessories.append("glasses")
    if "fang" in spec.traits and not any("fang" in x for x in features + accessories):
        accessories.append("fang")

    # --- シグネチャ小物（1つだけ） -----------------------------------------
    # --- シルエット設計・シェイプ言語・情報量ゾーン ---------------------------
    sil_rng = random.Random(seed * 31337 + 5)
    sil_key = silhouette if silhouette in D.SILHOUETTES else _pick(sil_rng, list(D.SILHOUETTES))
    sil = D.SILHOUETTES[sil_key]
    zones = list(sil["zones"])
    shape_key = shape_lang if shape_lang in D.SHAPES else D.ARCH_SHAPE.get(arch_key, "round")
    shape_spec = D.SHAPES[shape_key]
    silhouette_tags = list(sil["tags"]) + (list(shape_spec["tags"]) if detail_level >= 1 else [])

    # --- 装飾レイヤー（独自性） -------------------------------------------------
    shape = D.SHAPE_WORDS.get(theme_key or "", "") or D.SHAPE_WORDS.get(motif_key, "")
    tech_aff = (motif_key in D.TECH_AFFINITY) or (theme_key in D.TECH_AFFINITY)
    emb_rng = random.Random(seed * 7919 + 17)
    embellish_tags, embellish_nl, iconic_tag = build_embellishments(
        detail_level, outfit, gender, exp, shape, tech_aff, " ".join(features).lower(), emb_rng, fill_slots,
        zones if detail_level >= 1 else None)
    if strict:
        # 説明文版（シートのメモ）にも同じ内容を足しておく
        outfit_detail = outfit_detail + embellish_tags
    hair_special_tags, hair_special_nl = build_hair_special(detail_level, hair, hair_color, palette, shape, random.Random(seed * 104729 + 3),
                                                            prefer=sil.get("hair", []))
    hair = hair + hair_special_tags

    # --- 手持ち（武器・小道具）。既定では何も持たない --------------------------
    prop = ""
    handheld_tags: List[str] = []
    handheld_key = None
    if handheld == "random":
        handheld_key = _pick(rng, list(D.HANDHELDS))
    elif handheld in D.HANDHELDS:
        handheld_key = handheld
    elif handheld == "none" and spec.handheld:
        handheld_key = spec.handheld
    if handheld_key:
        handheld_tags, prop = build_handheld(handheld_key, rng, slots)
    elif handheld == "role":
        # 服装の小道具（巫女の御幣、ナースの注射器など）
        prop_pool = list(role.get("props", [])) + (list(role_b.get("props", [])) if role_b else [])
        prop = _fill(_pick(rng, prop_pool) or "", fill_slots)
        if prop and not any(w in prop.lower() for w in D.PROP_ANCHORED_WORDS):
            prop = "holding " + prop
        handheld_tags = [prop] if prop else []

    # 高露出: 露出アンカー（モデルが穏当に描きがちなので明示する）
    exposure_tags: List[str] = []
    if exp == "high":
        pool_x = D.EXPOSURE_HIGH_EXTRAS_MALE if gender == "boy" else D.EXPOSURE_HIGH_EXTRAS
        outfit_text = " ".join(outfit + outfit_detail).lower()
        pool_x = [t for t in pool_x if t not in outfit_text]
        exposure_tags = _sample(rng, pool_x, D.EXPOSURE_HIGH_COUNT)

    # strict: 模様は booru に print タグがあるものだけ出す
    print_tag = (motif.get("signature_print") or D.BOORU_PRINT.get(base_pattern, "")) if strict else ""
    if strict and not print_tag:
        omitted.append(f"pattern: {pattern}")

    # --- 表情・ポーズ -----------------------------------------------------
    expression = _pick(rng, arch["expression"])
    pose = _pick(rng, arch["pose"])

    return Character(
        seed=seed, brief=brief, gender=gender, motif=motif_key, role=role_key, archetype=arch_key,
        exposure=exp, twist=twist_label, twist_role=twist_role, twist_arch=twist_arch,
        palette=palette, pattern=pattern, material=material,
        hair=hair, eyes=eyes, skin=skin, body=body, features=features, outfit=outfit,
        accessories=accessories, prop=prop, expression=expression, pose=pose,
        extras=[], unrecognized=spec.extras, excluded=excluded, prompt_style=prompt_style, expression_pose=expression_pose,
        consistency=consistency, emphasis=emphasis, pattern_base=base_pattern, print_tag=print_tag,
        outfit_detail=outfit_detail, omitted=omitted, eye_choice=chosen, eye_intensity=eye_intensity,
        role2=role2_key or "", exposure_tags=exposure_tags, theme=theme_key or "", handheld_tags=handheld_tags,
        body_sentences=body_sentences, embellish_tags=embellish_tags, embellish_nl=embellish_nl, iconic_tag=iconic_tag,
        detail_level=detail_level, hair_special_nl=hair_special_nl,
        silhouette=sil_key, shape_lang=shape_key, zones=zones, silhouette_tags=silhouette_tags,
    )


# ---------------------------------------------------------------------------
# プロンプト組み立て
# ---------------------------------------------------------------------------

def _w(tag: str, weight: float) -> str:
    """ComfyUI 形式の重み付け (tag:1.6)。weight が 1.0 以下なら素のタグ"""
    if not tag or weight <= 1.0:
        return tag
    return f"({tag}:{round(weight, 2)})"


def _eye_weight(c: Character) -> float:
    factor = next((f for k, f, _ in D.EYE_INTENSITY if k == c.eye_intensity), 1.0)
    return round(c.emphasis * factor, 2)


def _eye_sentence(c: Character, pron: str, poss: str) -> str:
    """目の形を自然文で補強する（画風に固定されがちな目の形を言葉で押す）"""
    shape = c.eye_choice.get("shape")
    if not shape:
        return ""
    adverb = next((a for k, _, a in D.EYE_INTENSITY if k == c.eye_intensity), "")
    desc = D.EYE_SHAPE_NL.get(shape, shape)
    parts = [f"{poss.capitalize()} eyes are {adverb + ' ' if adverb else ''}{desc}"]
    extras = [c.eye_choice[k] for k in ("size", "lid", "highlights") if k in c.eye_choice]
    if extras:
        parts.append(", ".join(extras))
    return ", ".join(parts) + "."


def _exposure_sentence(c: Character, pron: str, poss: str) -> str:
    if c.exposure != "high" or not c.exposure_tags:
        return ""
    parts = ", ".join(c.exposure_tags)
    return f"{poss.capitalize()} outfit shows a lot of skin: {parts}."


def _theme_sentence(c: Character, pron: str, poss: str) -> str:
    """モチーフは衣装の装飾として表現し、別の物体として置かせない"""
    if not c.theme:
        return ""
    name = D.MOTIFS[c.theme]["jp"] if False else c.theme.replace("_", " ")
    pat = c.print_tag or c.pattern_base
    return f"The {name} motif is worked into {poss} outfit as {pat} and matching accessories, not as separate objects."


def _silhouette_sentence(c: Character, pron: str, poss: str) -> str:
    if not c.silhouette:
        return ""
    parts = [D.SILHOUETTES[c.silhouette]["nl"].capitalize() + "."]
    if c.detail_level >= 1 and c.shape_lang:
        parts.append(D.SHAPES[c.shape_lang]["nl"].capitalize() + ".")
    if c.detail_level >= 1 and c.zones:
        rest = [z for z in D.ZONE_JP if z not in c.zones]
        parts.append(f"Design density is concentrated at the {' and '.join(D.ZONE_JP[z] for z in c.zones)}; the {', '.join(D.ZONE_JP[z] for z in rest)} are kept plain as visual rest areas.")
    return " ".join(parts)


def _hair_sentence(c: Character, pron: str, poss: str) -> str:
    if not c.hair_special_nl:
        return ""
    return f"{poss.capitalize()} hair has {'; '.join(c.hair_special_nl)}."


def _embellish_sentence(c: Character, pron: str, poss: str) -> str:
    """装飾レイヤーの文章: 象徴的な一点を先に、残りを列挙"""
    if not c.embellish_nl:
        return ""
    parts = [p.replace("{poss}", poss) for p in c.embellish_nl]
    out = []
    if c.iconic_tag:
        out.append(f"{poss.capitalize()} iconic design element is {parts[0]}.")
        parts = parts[1:]
    if parts:
        out.append(f"Design details: {'; '.join(parts)}.")
    return " ".join(out)


def _article(phrase: str) -> str:
    return "an" if phrase[:1].lower() in "aeiou" else "a"


def _handheld_sentence(c: Character, pron: str, poss: str) -> str:
    if not c.prop:
        return ""
    if c.handheld_tags and c.handheld_tags[0] == c.prop:
        return ""  # 服装の小道具はタグそのもの
    return f"{pron} holds {_article(c.prop)} {c.prop}."


def _persona_sentence(c: Character, pron: str, poss: str) -> str:
    sig = D.ARCH_SIGNATURE.get(c.archetype)
    if not sig or not sig.get("persona"):
        return ""
    return sig["persona"].replace("{pron}", pron).replace("{poss}", poss)


def _signature_tags(c: Character) -> List[str]:
    sig = D.ARCH_SIGNATURE.get(c.archetype)
    return list(sig["tags"]) if sig else []


def _primary_noun(tag: str) -> str:
    """主役の服タグから名詞を取り出す（"black pleated skirt" -> "skirt"）"""
    words = re.sub(r"[()]|:\d+(\.\d+)?", "", tag.split(",")[0]).split()
    return words[-1] if words else ""


def _alt_color_negatives(c: Character) -> List[str]:
    """主役の服について、別色の同じ服を negative に入れる（ポーズ違いでの色ブレ対策）"""
    if not c.outfit:
        return []
    noun = _primary_noun(c.outfit[0])
    if not noun or noun in ("clothes", "outfit", "male", "pectorals"):
        return []
    # 主役タグが固定色（white kimono 等）ならその色を基準にする
    first = c.outfit[0].lower()
    color = c.main
    for name in sorted(list(D.COLOR_BASE) + D.ALT_COLORS, key=len, reverse=True):
        if first.startswith(name + " "):
            color = name
            break
    base = D.COLOR_BASE.get(color, color)
    return [f"{col} {noun}" for col in D.ALT_COLORS if col != base][:5]


def build_positive(c: Character) -> str:
    strict = c.consistency == "strict"
    pron, poss = ("She", "her") if c.gender == "girl" else ("He", "his")
    who = "girl" if c.gender == "girl" else "boy"

    if c.prompt_style == "natural":
        parts = []
        parts.append(f"A {who} ({', '.join(c.body)}) with {', '.join(c.hair)}; {', '.join(c.eyes)}; {c.skin}.")
        if c.features:
            parts.append(f"{pron} has {'; '.join(c.features)}.")
        if strict:
            parts.append(f"{pron} wears {', '.join(c.outfit)}.")
        else:
            parts.append(f"{pron} wears: {'; '.join(c.outfit)}.")
        if c.accessories:
            parts.append(f"{pron} also has {'; '.join(c.accessories)}.")
        if c.prop:
            parts.append(f"{pron} holds {_article(c.prop)} {c.prop}.")
        if c.expression_pose == "both":
            parts.append(f"Expression and pose: {c.expression}; {c.pose}.")
        elif c.expression_pose == "expression_only":
            parts.append(f"Default expression: {c.expression}.")
        if strict:
            pat = f" and {c.print_tag}" if c.print_tag else ""
            parts.append(f"{poss.capitalize()} outfit is {c.main} with {c.accent} trim{pat}.")
        else:
            parts.append(f"Color scheme: {c.main} and {c.sub} with {c.accent} accents; the pattern used is {c.pattern}.")
        parts.append(_embellish_sentence(c, pron, poss))
        parts.append(_silhouette_sentence(c, pron, poss))
        parts.append(_hair_sentence(c, pron, poss))
        parts += c.body_sentences
        parts.append(_theme_sentence(c, pron, poss))
        parts.append(_exposure_sentence(c, pron, poss))
        parts.append(_eye_sentence(c, pron, poss))
        parts.append(_persona_sentence(c, pron, poss))
        parts = [p for p in parts if p]
        if c.unrecognized:
            parts.append(" ".join(c.unrecognized))
        return " ".join(parts)

    tags: List[str] = []
    tags += c.body
    tags += c.hair
    if strict:
        # 目の形には強弱に応じた重み（Anima は SDXL より強い重みが必要）
        shape = c.eye_choice.get("shape")
        tags += [_w(t, _eye_weight(c)) if t == shape else t for t in c.eyes]
    else:
        tags += c.eyes
    tags.append(c.skin)
    if strict:
        # 記号 -> 主役の服（重み付き）-> 残りの服 -> 小物 -> 署名タグ -> 持ち物 -> 表情 -> 模様 -> 縁色 -> 自然文（服・目・性格）
        if c.features:
            tags.append(_w(c.features[0], round(c.emphasis * 0.9, 2)))
            tags += c.features[1:]
        if c.outfit:
            tags.append(_w(c.outfit[0], c.emphasis))
            tags += c.outfit[1:]
        for t in c.embellish_tags:
            tags.append(_w(t, c.emphasis) if t == c.iconic_tag else t)
        tags += c.silhouette_tags
        if c.exposure_tags:
            tags.append(_w(c.exposure_tags[0], round(c.emphasis * 0.9, 2)))
            tags += c.exposure_tags[1:]
        tags += c.accessories
        signature = _signature_tags(c)
        present = {t.lower() for t in tags}
        tags += [_w(t, round(c.emphasis * 0.9, 2)) for t in signature if t.lower() not in present]
        if c.handheld_tags:
            tags.append(_w(c.handheld_tags[0], round(c.emphasis * 0.9, 2)))
            tags += c.handheld_tags[1:]
        # 表情に署名タグと同じ語が含まれていれば重複を除く（"sadistic smirk, looking down at viewer" など）
        expression = ", ".join(x for x in c.expression.split(", ") if x not in signature) or c.expression
        if c.expression_pose == "both":
            tags += [expression, c.pose]
        elif c.expression_pose == "expression_only":
            tags.append(expression)
        if c.print_tag:
            tags.append(c.print_tag)
        tags.append(f"{c.accent} trim")
        tags += c.unrecognized
        # タグ列のあとに自然文（服・目・性格）を続ける: "tags, tags. Sentence. Sentence."
        sentences = [f"{poss.capitalize()} outfit is {c.main} with {c.accent} trim.", _embellish_sentence(c, pron, poss), _silhouette_sentence(c, pron, poss), _hair_sentence(c, pron, poss), *c.body_sentences, _theme_sentence(c, pron, poss), _handheld_sentence(c, pron, poss), _exposure_sentence(c, pron, poss), _eye_sentence(c, pron, poss), _persona_sentence(c, pron, poss)]
        return ", ".join(_dedupe(tags)) + ". " + " ".join(s for s in sentences if s)

    tags += c.features
    tags += c.outfit
    tags += c.embellish_tags
    tags += c.silhouette_tags
    tags += c.exposure_tags
    tags += c.accessories
    tags += _signature_tags(c)
    if c.handheld_tags:
        tags += c.handheld_tags
    if c.prop and c.prop not in c.handheld_tags:
        tags.append(c.prop)
    if c.expression_pose == "both":
        tags += [c.expression, c.pose]
    elif c.expression_pose == "expression_only":
        tags.append(c.expression)
    tags.append(f"{c.main} and {c.sub} color scheme with {c.accent} accents")
    tags += c.unrecognized
    return ", ".join(_dedupe(tags))


def build_negative(c: Character) -> str:
    neg = list(D.NEGATIVE_BASE)

    everything = " ".join(c.features + c.outfit + c.accessories + [c.prop] + c.hair + c.eyes + c.body).lower()
    # 設計に含まれていない記号は負方向に入れて「勝手に生える」のを防ぐ
    if "horn" not in everything:
        neg.append("horns")
    if "wing" not in everything:
        neg.append("wings")
    if "tail" not in everything:
        neg.append("tail")
    if "ears" not in everything:
        neg.append("animal ears")
    if "halo" not in everything:
        neg.append("halo")
    if "glasses" not in everything:
        neg.append("glasses")
    if not any(k in everything for k in ("hat", "cap", "bonnet", "veil", "mitre", "tricorne", "crown", "headdress", "hood")):
        neg.append("hat")
    if "heterochromia" not in everything:
        neg.append("heterochromia")
    if "colored skin" in c.skin:
        neg += ["fair skin", "pale skin"]
    if c.consistency == "strict":
        # 目: 反対の形を（重み付きで）抑える
        shape = c.eye_choice.get("shape")
        if shape and shape in D.EYE_OPPOSITE:
            neg.append(_w(D.EYE_OPPOSITE[shape], round(max(c.emphasis * 0.8, 1.0), 2)))
        # 目: 選ばなかった特殊瞳孔・反対のハイライトを抑える
        if "pupils" not in c.eye_choice:
            neg += ["slit pupils", "heart-shaped pupils"]
        hl = c.eye_choice.get("highlights")
        if hl == "empty eyes":
            neg.append("sparkling eyes")
        elif hl:
            neg.append("empty eyes")
        # 不安定要素は negative でも抑える
        neg += ["facial mark", "face paint", "body markings"]
        # モチーフの小物が背景に単独で置かれるのを抑える
        neg += ["floating objects", "scattered objects", "objects in background"]
        # シェイプ言語の反対の形を抑える
        if c.detail_level >= 1 and c.shape_lang:
            neg += list(D.SHAPES[c.shape_lang]["neg"])
        # 手持ちが無いときは、装飾が手持ち化しないよう抑える（署名に手持ちがある性格は除く）
        sig = _signature_tags(c)
        if not c.handheld_tags and not any(s in D.SIGNATURE_HANDHELDS for s in sig) and "holding own head" not in " ".join(c.features):
            neg += list(D.HANDHELD_NEGATIVE)
        neg += _alt_color_negatives(c)
    if c.exposure == "modest":
        neg += ["cleavage", "navel", "bare shoulders", "midriff", "nude"]
    elif c.exposure == "high":
        neg += list(D.EXPOSURE_HIGH_NEGATIVE) + ["nude", "nipples"]
    else:
        neg += ["nude", "nipples"]
    return ", ".join(_dedupe(neg))


# ---------------------------------------------------------------------------
# キャラクターシート
# ---------------------------------------------------------------------------

_SECTION_RE = re.compile(r"^\s*#[\s\-─━=]*(positive|negative)\b", re.IGNORECASE)


def build_sheet(c: Character) -> str:
    motif = D.MOTIFS[c.motif]
    role = D.ROLES[c.role]
    arch = D.ARCHETYPES[c.archetype]

    if c.twist == "surprise":
        concept = f"{motif['jp']} × {role['jp']}（ギャップ型）"
        design_note = motif["gap_jp"].format(role=role["jp"])
    elif c.twist == "fixed":
        concept = f"{motif['jp']} × {role['jp']}（指定どおり）"
        design_note = motif["classic_jp"]
    else:
        concept = f"{motif['jp']} × {role['jp']}（王道型）"
        design_note = motif["classic_jp"]

    twist_detail = []
    if c.twist_role:
        twist_detail.append("服装を外した")
    if c.twist_arch:
        twist_detail.append("性格を外した")
    twist_text = {"surprise": "surprise（" + "・".join(twist_detail) + "）", "classic": "classic", "fixed": "fixed"}[c.twist]

    lines = [
        "# ━━━━━━━━━━━━━━━━ CHARACTER SHEET ━━━━━━━━━━━━━━━━",
        f"# seed       : {c.seed}",
        f"# brief      : {c.brief.strip().replace(chr(10), ' / ') if c.brief.strip() else '(なし)'}",
        f"# concept    : {concept}",
        f"# race       : {motif['jp']} ({c.motif})   motif: " + (f"{D.MOTIFS[c.theme]['jp']} ({c.theme})" if c.theme else "(なし)") + f"   role: {role['jp']} ({c.role})" + (f" × {D.ROLES[c.role2]['jp']} ({c.role2}) [融合]" if c.role2 else "") + f"   gender: {c.gender}",
        f"# personality: {arch['jp']} ({c.archetype})",
        f"#   -> {arch['design_jp']}",
        f"# palette    : main={c.main} / sub={c.sub} / accent={c.accent}   pattern={c.pattern}   material={c.material}",
        f"# handheld   : {c.prop or '(なし)'}",
        f"# embellish  : level={c.detail_level}  " + (" / ".join(c.embellish_tags) if c.embellish_tags else "(なし)"),
        f"# silhouette : {D.SILHOUETTES[c.silhouette]['jp'] if c.silhouette else '-'} ({c.silhouette})   shape: {D.SHAPES[c.shape_lang]['jp'] if c.shape_lang else '-'} ({c.shape_lang})   density zones: {', '.join(c.zones) or '-'}",
        f"# exposure   : {EXPOSURE_JP[c.exposure]} ({c.exposure})   twist: {twist_text}   style: {c.prompt_style}   expression_pose: {c.expression_pose}",
        f"# eyes       : {' / '.join(c.eyes)}   intensity={c.eye_intensity}   emphasis={c.emphasis}",
        f"# consistency: {c.consistency}" + ("（booru タグ骨格 / 色は main+accent の2色 / 不安定要素は省略）" if c.consistency == "strict" else "（詳細説明文）"),
        f"# design     : {design_note}",
    ]
    if c.consistency == "strict":
        lines.append("# detail(memo): " + " / ".join(c.outfit_detail))
        if c.omitted:
            lines.append("# omitted    : " + " / ".join(c.omitted) + "  (strict では出力しない不安定要素)")
    ex = [f"{k}={','.join(sorted(v))}" for k, v in c.excluded.items() if v]
    if ex:
        lines.append(f"# exclude    : {'  '.join(ex)}")
    if c.unrecognized:
        lines.append(f"# passthrough: {', '.join(c.unrecognized)}  (辞書に無い語はそのままプロンプト末尾に追加)")
    lines += [
        "# ──────── positive ────────",
        build_positive(c),
        "# ──────── negative ────────",
        build_negative(c),
        "# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]
    return "\n".join(lines)


def parse_sheet(text: str) -> Tuple[str, str]:
    """
    シートから positive / negative を取り出す。
      - "# ... positive ..." / "# ... negative ..." の行でセクションを切り替える
      - それ以外の '#' 以降はコメントとして除去（ユーザーのメモ書きを許容）
      - セクション指定が無い行は positive 扱い
    """
    section = "positive"
    buf = {"positive": [], "negative": []}
    for raw in (text or "").splitlines():
        m = _SECTION_RE.match(raw)
        if m:
            section = m.group(1).lower()
            continue
        line = re.sub(r"#.*", "", raw).strip()
        if line:
            buf[section].append(line)
    return "\n".join(buf["positive"]), "\n".join(buf["negative"])


def _choices(table) -> List[str]:
    """ノードのコンボ用: 'auto' + 'key 日本語名' の一覧"""
    return ["auto"] + [f"{k} {v['jp']}" for k, v in table.items()]


def personality_choices() -> List[str]:
    return _choices(D.ARCHETYPES)


def motif_choices() -> List[str]:
    return _choices(D.MOTIFS)


def role_choices() -> List[str]:
    return _choices(D.ROLES)


def choice_key(choice: str) -> str:
    """'demon 悪魔' -> 'demon'"""
    return (choice or "auto").split(" ", 1)[0]


personality_key = choice_key
