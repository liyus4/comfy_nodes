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

EXPOSURES = ("modest", "standard", "high")
EXPOSURE_JP = {"modest": "控えめ", "standard": "標準", "high": "高露出"}
TWISTS = ("auto", "classic", "surprise")


# ---------------------------------------------------------------------------
# 指示文のパース
# ---------------------------------------------------------------------------

@dataclass
class Spec:
    gender: Optional[str] = None       # "girl" / "boy"
    motif: Optional[str] = None
    role: Optional[str] = None
    archetype: Optional[str] = None
    exposure: Optional[str] = None
    hair_color: Optional[str] = None
    eye_color: Optional[str] = None
    theme_color: Optional[str] = None
    hair_styles: List[str] = field(default_factory=list)
    traits: List[str] = field(default_factory=list)
    extras: List[str] = field(default_factory=list)   # 認識できなかった語（そのまま通す）
    matched: List[str] = field(default_factory=list)  # ログ用


_SPLIT_RE = re.compile(r"[・,、，/／\s\n|｜;；]+")


def _syn_hits(token: str, syns: List[str]) -> bool:
    """同義語リストのいずれかが token に含まれるか。ASCII 語は単語境界で判定する。"""
    low = token.lower()
    for s in syns:
        s_low = s.lower()
        if s_low.isascii():
            if re.search(r"(?<![a-z0-9])" + re.escape(s_low) + r"(?![a-z0-9])", low):
                return True
        else:
            if s_low in low:
                return True
    return False


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
    ]


def _extract_multiword(brief: str) -> Tuple[str, List[str]]:
    """
    空白を含む同義語（"shrine maiden", "light blue hair" など）は空白分割で壊れるので、
    先に全文から探して1トークンに置き換えておく（空白をアンダースコアに変換して退避）。
    """
    text = brief or ""
    found = []
    phrases = set()
    for table in _all_tables():
        for syns in table.values():
            for s in syns:
                if " " in s:
                    phrases.add(s)
    for phrase in sorted(phrases, key=len, reverse=True):
        pat = re.compile(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])", re.IGNORECASE)
        if pat.search(text):
            text = pat.sub(phrase.replace(" ", "_"), text)
            found.append(phrase)
    return text, found


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
            if spec.motif is None:
                spec.motif = m
            matched = True
        for r in _lookup(tok, {k: v["syn"] for k, v in D.ROLES.items()}):
            if spec.role is None:
                spec.role = r
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
) -> Character:
    rng = random.Random(seed)
    spec = parse_brief(brief)
    excluded = parse_exclude(exclude)

    # ドロップダウン指定（auto 以外）は brief より優先
    if motif != "auto" and motif in D.MOTIFS:
        spec.motif = motif
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
    motif = D.MOTIFS[motif_key]

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
    palette_pool = list(motif["palettes"]) * 2 + list(arch["palettes"]) + list(role.get("palettes", []))
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

    base_pattern = _pick(rng, motif["patterns"]) or "ribbon motif"
    pattern = f"{_pick(rng, D.PATTERN_STYLES)} {base_pattern}"
    material = _pick(rng, role.get("materials", [])) or "cotton"
    slots = {"main": main, "sub": sub, "accent": accent, "pattern": pattern, "material": material}

    # --- 髪 ---------------------------------------------------------------
    if spec.hair_color:
        hair_color = spec.hair_color
    elif rng.random() < 0.5:
        # 「髪か瞳にテーマカラーを乗せる」ルール: main か sub を髪色にする
        hair_color = D.COLOR_TO_HAIR.get(_pick(rng, [main, sub]), _pick(rng, arch["hair_colors"]))
    else:
        hair_color = _pick(rng, list(arch["hair_colors"]) + list(motif["hair_colors"]))

    if spec.hair_styles:
        hair_style = ", ".join(spec.hair_styles)
    else:
        hair_style = _pick(rng, arch["hair_styles"])
    hair = [hair_color, hair_style]
    if "bangs" not in hair_style and "hiding the face" not in hair_style and "covering" not in hair_style:
        hair.append(_pick(rng, D.BANGS))

    # --- 瞳 ---------------------------------------------------------------
    if spec.eye_color:
        eye_color = spec.eye_color
    elif rng.random() < 0.55:
        # 「瞳はアクセントカラー」ルール
        eye_color = D.COLOR_TO_EYE.get(accent, _pick(rng, motif["eye_colors"]))
    else:
        eye_color = _pick(rng, motif["eye_colors"])
    eye_shape = _pick(rng, arch["eyes"])
    eyes = [eye_color, eye_shape]
    if "heterochromia" in spec.traits and "heterochromia" not in eye_color:
        eyes.insert(0, "heterochromia")

    # --- 肌・体型 ---------------------------------------------------------
    skin = motif.get("skin") or "fair skin"
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

    # --- モチーフの記号 ---------------------------------------------------
    features = []
    primary = _pick(rng, motif["features_primary"])
    if primary:
        features.append(primary)
    features += _sample(rng, [f for f in motif["features_optional"] if f != primary], rng.randint(1, 2))
    features = [_fill(f, slots) for f in features]

    # --- 服装 -------------------------------------------------------------
    if gender == "boy" and "male" in role:
        outfit_src = role["male"][exp]
    else:
        outfit_src = role["outfits"][exp]
    outfit = [_fill(o, slots) for o in outfit_src]
    if arch.get("footwear"):
        replacement = _fill(arch["footwear"], slots)
        outfit = [o for o in outfit if not any(k in o for k in D.FOOTWEAR_KEYWORDS)]
        outfit.append(replacement)

    # --- 性格を示す小物 ---------------------------------------------------
    feature_text = " ".join(features).lower()
    acc_pool = [a for a in arch["accessories"] if not (a == "fang" and "fang" in feature_text)]
    accessories = [_fill(a, slots) for a in _sample(rng, acc_pool, rng.randint(1, 2))]
    if "glasses" in spec.traits and not any("glasses" in o for o in outfit):
        accessories.append("glasses")
    if "fang" in spec.traits and not any("fang" in x for x in features + accessories):
        accessories.append("fang")

    # --- シグネチャ小物（1つだけ） -----------------------------------------
    prop = _fill(_pick(rng, list(motif["props"]) + list(role.get("props", []))) or "", slots)

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
    )


# ---------------------------------------------------------------------------
# プロンプト組み立て
# ---------------------------------------------------------------------------

def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for it in items:
        key = it.strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(it.strip())
    return out


def build_positive(c: Character) -> str:
    color_anchor = f"{c.main} and {c.sub} color scheme with {c.accent} accents"

    if c.prompt_style == "natural":
        pron, poss = ("She", "her") if c.gender == "girl" else ("He", "his")
        who = "girl" if c.gender == "girl" else "boy"
        parts = []
        # 服装1点の中にカンマが入るので、項目の区切りはセミコロンにする
        parts.append(f"A {who} ({', '.join(c.body)}) with {', '.join(c.hair)}; {', '.join(c.eyes)}; {c.skin}.")
        if c.features:
            parts.append(f"{pron} has {'; '.join(c.features)}.")
        parts.append(f"{pron} wears: {'; '.join(c.outfit)}.")
        if c.accessories:
            parts.append(f"{pron} also has {'; '.join(c.accessories)}.")
        if c.prop:
            parts.append(f"{poss.capitalize()} signature item is {c.prop}.")
        if c.expression_pose == "both":
            parts.append(f"Expression and pose: {c.expression}; {c.pose}.")
        elif c.expression_pose == "expression_only":
            parts.append(f"Default expression: {c.expression}.")
        parts.append(f"Color scheme: {c.main} and {c.sub} with {c.accent} accents; the pattern used is {c.pattern}.")
        if c.unrecognized:
            parts.append(" ".join(c.unrecognized))
        return " ".join(parts)

    tags = []
    # 人数・性別タグ(1girl/1boy)は状況側で指定する前提なので入れない
    tags += c.body
    tags += c.hair
    tags += c.eyes
    tags.append(c.skin)
    tags += c.features
    tags += c.outfit
    tags += c.accessories
    if c.prop:
        tags.append(c.prop)
    if c.expression_pose == "both":
        tags += [c.expression, c.pose]
    elif c.expression_pose == "expression_only":
        tags.append(c.expression)
    tags.append(color_anchor)
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
    if "hat" not in everything and "cap" not in everything and "bonnet" not in everything and "veil" not in everything:
        neg.append("hat")
    if "heterochromia" not in everything:
        neg.append("heterochromia")
    if c.exposure == "modest":
        neg += ["cleavage", "navel", "bare shoulders", "midriff", "nude"]
    elif c.exposure == "standard":
        neg += ["nude", "nipples"]
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
        f"# motif      : {motif['jp']} ({c.motif})   role: {role['jp']} ({c.role})   gender: {c.gender}",
        f"# personality: {arch['jp']} ({c.archetype})",
        f"#   -> {arch['design_jp']}",
        f"# palette    : main={c.main} / sub={c.sub} / accent={c.accent}   pattern={c.pattern}   material={c.material}",
        f"# signature  : {c.prop or '(なし)'}",
        f"# exposure   : {EXPOSURE_JP[c.exposure]} ({c.exposure})   twist: {twist_text}   style: {c.prompt_style}   expression_pose: {c.expression_pose}",
        f"# design     : {design_note}",
    ]
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
