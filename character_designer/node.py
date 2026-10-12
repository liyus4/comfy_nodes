"""
ComfyUI ノード: Random Character Designer

軽い指示文（例: "悪魔・女の子・高露出"）と seed から、人気キャラクターの設計手法に沿った
キャラクターを1体設計し、再現性の高いプロンプト（positive / negative）と
「キャラクターシート」を出力します。

出力は「キャラの特徴」だけです。品質タグ（masterpiece 等）・solo・1girl/1boy・画風・状況は含めないので、
別ノードで作ったテキストと連結して使ってください。

使い方:
  1. 指示文に雰囲気を書いて Queue。シードを変えるたびに別のキャラが出ます。
  2. 気に入ったら「固定」を ON。キャラシート欄に残ったシートが
     そのまま positive / negative の出力元になり、同じキャラを再現できます。
     シートは手で編集しても OK（'#' 以降はコメント扱い）。

入力名は UI での分かりやすさのため日本語にしています（Python の識別子として有効で、
ComfyUI の API / ワークフロー JSON も UTF-8 なので動作に支障はありません）。
engine 側は英語のキーで動くので、このファイルで日本語 <-> 内部値を変換しています。
"""

import importlib
import os
import re

from . import data, engine, outfit_tags, monster

# --- 開発用ホットリロード -----------------------------------------------------
# data.py / outfit_tags.py / engine.py が更新されていたら、実行時に再読み込みする（ComfyUI の再起動不要）。
# node.py 自体（入力欄の定義）と js/ の変更は従来どおり再起動 + ブラウザリロードが必要。
_WATCHED = (data, outfit_tags, engine, monster)
_MTIMES = {}


def _source_mtimes():
    out = {}
    for m in _WATCHED:
        try:
            out[m.__name__] = os.path.getmtime(m.__file__)
        except OSError:
            pass
    return out


def _reload_if_changed():
    global _MTIMES
    current = _source_mtimes()
    if current == _MTIMES:
        return
    if _MTIMES:  # 初回は記録だけ
        try:
            # outfit_tags -> data -> engine の順で reload（依存の順）
            importlib.reload(outfit_tags)
            importlib.reload(data)
            importlib.reload(engine)
            print("[CharacterDesigner] data.py / outfit_tags.py / engine.py を再読み込みしました")
        except Exception as e:  # 編集途中の構文エラー等で落とさない
            print(f"[CharacterDesigner] 再読み込みに失敗しました（前回の内容で続行）: {e!r}")
            return
    _MTIMES = current


_reload_if_changed()

# --- 日本語ラベル <-> 内部値 ---------------------------------------------------
TWIST_JP = {"自動": "auto", "王道": "classic", "意外性": "surprise"}
EXPOSURE_JP = {"自動": "auto", "控えめ": "modest", "標準": "standard", "高露出": "high", "準裸": "near_nude", "全裸": "nude"}
STYLE_JP = {"タグ": "tags", "文章": "natural"}
CONSISTENCY_JP = {"厳密（タグ骨格・再現性重視）": "strict", "詳細（説明文）": "full"}
EXPRESSION_JP = {"表情のみ": "expression_only", "表情とポーズ": "both", "なし": "none"}
EYE_SHAPE_JP = {"自動": "auto", "ツリ目": "tsurime", "タレ目": "tareme", "ジト目": "jitome", "三白眼": "sanpaku"}

_KEY_RE = re.compile(r"\(([a-z_ ]+)\)\s*$")


def _jp_choices(table) -> list:
    """コンボ用: '自動' + '日本語名 (key)' の一覧"""
    return ["自動"] + [f"{v['jp']} ({k})" for k, v in table.items()]


def _jp_key(choice: str) -> str:
    """'悪魔 (demon)' -> 'demon'。'自動' や不明な値は 'auto'"""
    m = _KEY_RE.search(choice or "")
    return m.group(1) if m else "auto"


class CharacterDesignerNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "指示文": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "placeholder": "例: 悪魔・女の子・高露出 / 猫耳メイド・ツンデレ / 天使・清楚・黒髪・タレ目（空ならすべてランダム）",
                    "tooltip": "雰囲気の指示。「・」「,」「空白」区切り。辞書に無い語はそのまま末尾に通します",
                }),
                "除外": ("STRING", {
                    "multiline": False, "default": "",
                    "placeholder": "出したくない語（例: 水着, バニー, 高露出, ヤンデレ）",
                    "tooltip": "ランダム選択のプールからモチーフ/服装/性格/露出を外します。明示した指定の方が優先",
                }),
                "種族": (_jp_choices(data.RACES), {"default": "自動", "tooltip": "体の記号（耳・角・肌）と配色の軸。自動以外は指示文より優先"}),
                "モチーフ": (["自動", "なし", "ランダム"] + _jp_choices(data.THEMES)[1:], {"default": "自動",
                             "tooltip": "模様・小物・差し色の軸。自動=指示文の指定 > 35%で付く / なし=付けない / ランダム=必ず付く / 指定"}),
                "服装": (_jp_choices(data.ROLES), {"default": "自動", "tooltip": "自動以外は指示文より優先"}),
                "服装2": (["なし", "ランダム"] + _jp_choices(data.ROLES)[1:], {"default": "なし",
                          "tooltip": "2つ目の服装系統と融合（服装を土台に、頭・顔・手・首・羽織り・小物を取り込む）。指示文に系統を2つ書いても融合します"}),
                "性格": (_jp_choices(data.ARCHETYPES), {"default": "自動", "tooltip": "自動以外は指示文より優先"}),
                "一貫性": (["なし", "弱", "標準", "強"], {"default": "標準",
                           "tooltip": "選ばれた種族・モチーフ・服装からコンセプト（例: 夜の女王）を導出し、性格・配色・シルエット・装飾・手持ち・マスコットをそれに寄せる強さ。なし=従来どおり独立抽選"}),
                "装飾量": (["0 なし", "1 控えめ", "2 標準", "3 盛る"], {"default": "2 標準",
                           "tooltip": "服装の上に重ねる独自性（非対称化・ベルト/ストラップ・モチーフ形状の装備・レイヤリング・切り抜き・象徴的な一点・テック）。2以上で象徴的な一点が付く"}),
                "シルエット": (["自動"] + [f"{v['jp']} ({k})" for k, v in data.SILHOUETTES.items()], {"default": "自動",
                             "tooltip": "ボリュームの偏り（上重心/下重心/縦長/横広）。髪・装飾の選択と情報量ゾーンがこれに寄る"}),
                "シェイプ": (["自動"] + [f"{v['jp']} ({k})" for k, v in data.SHAPES.items()], {"default": "自動",
                           "tooltip": "シェイプ言語（丸=親しみ/四角=安定/鋭角=攻撃性）。自動は性格から。反対の形は negative に入る"}),
                "世界観": (["自動"] + [f"{v['jp']} ({k})" for k, v in data.ERAS.items()], {"default": "自動",
                           "tooltip": "時代設定。服装候補をその範囲に絞り、雰囲気タグ（fantasy / futuristic / japanese clothes）を足す。指定した服装は優先"}),
                "マスコット": (["自動", "なし", "ランダム"] + [f"{m['jp']} ({m['key']})" for m in data.MASCOTS], {"default": "自動",
                             "tooltip": "同伴する小さな相棒（肩の小動物・精霊・小型ロボ・ぬいぐるみ・小鳥）。色と形は種族・モチーフに連動"}),
                "顔の印": (["なし", "ランダム"] + [f"{m['jp']} ({m['key']})" for m in data.FACE_MARKS], {"default": "なし",
                           "tooltip": "頬や目元の記号（ハート・星・涙・十字・泣きぼくろ・鼻の絆創膏・ヒゲ模様・縫い目）。不安定要素なので既定はなし"}),
                "手持ち": (["自動", "なし", "ランダム", "巨大武器", "服装の小道具"] + [f"{v['jp']} ({k})" for k, v in data.HANDHELDS.items()], {"default": "自動",
                           "tooltip": "武装・小道具は positive ではなく「装備」出力に入る。自動=職業の好みの武器を75%＋職業ギア / 巨大武器=本人より大きい武器 / 服装の小道具=職業ギアのみ"}),
                "年齢感": (["自動", "若い (young)", "大人 (adult)", "年上 (older)"], {"default": "自動",
                           "tooltip": "顔立ち・体つきの年齢感。自動は性格（お姉さん・ドS・暴君など＝大人、メスガキ・ドジっ娘など＝若い）とコンセプトから"}),
                "胸": (["自動"] + [lv[0] for lv in data.BUST_LEVELS], {"default": "自動", "tooltip": "0=flat chest … 5=gigantic、6以降は重みと文章でさらに大きく。自動は種族・性格の推奨"}),
                "身長": (["自動"] + list(data.HEIGHT_LEVELS), {"default": "自動"}),
                "体型": (["自動"] + list(data.BUILD_LEVELS), {"default": "自動", "tooltip": "華奢/細身/普通/むっちり/ぽっちゃり/筋肉質。自動は種族・性格の推奨"}),
                "服の色": (["自動"] + [f"{jp} ({k})" for k, jp in data.COLOR_JP.items()], {"default": "自動",
                           "tooltip": "服のメインカラー。自動は種族・性格・服装の推奨パレットから。指定時も縁色などは推奨から補完"}),
                "髪の色": (["自動"] + [f"{jp} ({k})" for k, jp in data.HAIR_COLOR_JP.items()], {"default": "自動",
                           "tooltip": "髪色。自動はテーマカラーか性格・種族の似合う色から"}),
                "シード": ("INT", {
                    "default": 0, "min": 0, "max": 0xffffffffffffffff,
                    "control_after_generate": True,
                    "tooltip": "同じ指示文とシードなら必ず同じキャラになります",
                }),
                "意外性": (list(TWIST_JP), {"default": "自動", "tooltip": "王道=悪魔→サキュバス / 意外性=悪魔→シスター / 自動=4割で意外性"}),
                "露出": (list(EXPOSURE_JP), {"default": "自動", "tooltip": "自動は指示文の指定 > ランダム（準裸・全裸はランダムでは出ない）。準裸=下着未満の面積＋装身具のみ / 全裸=装身具のみ"}),
                "出力形式": (list(STYLE_JP), {"default": "タグ", "tooltip": "タグ=カンマ区切り / 文章=自然文"}),
                "再現性": (list(CONSISTENCY_JP), {"default": "厳密（タグ骨格・再現性重視）",
                                                  "tooltip": "厳密=booruタグ骨格・2色・不安定要素なし（Anima/Illustrious 向け） / 詳細=服1点ごとの説明文"}),
                "強調": ("FLOAT", {"default": 1.6, "min": 0.0, "max": 3.0, "step": 0.1,
                                  "tooltip": "厳密モードの重み (tag:1.6)。Anima は SDXL より強めが必要。1.0 以下で無効"}),
                "表情ポーズ": (list(EXPRESSION_JP), {"default": "表情のみ", "tooltip": "ポーズは状況側で指定する前提なので既定は表情のみ"}),
                "目の形": (list(EYE_SHAPE_JP), {"default": "自動", "tooltip": "自動は指示文の指定 > 性格プロファイル"}),
                "固定": ("BOOLEAN", {"default": False, "label_on": "固定中（シートを使用）", "label_off": "生成する",
                                    "tooltip": "ON にするとキャラシート欄の内容をそのまま出力します"}),
                "キャラシート": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "生成するとここにキャラクターシートが残ります。「固定」を ON にするとこの内容がそのまま出力されます。",
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "INT", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("positive", "negative", "キャラシート", "シード", "三面図", "表情シート", "装備", "装備なし負")
    FUNCTION = "design"
    CATEGORY = "Test/Example Nodes"
    OUTPUT_NODE = True

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # data.py / engine.py を編集したら、同じ入力でもキャッシュを使わず再実行させる
        return str(sorted(_source_mtimes().items()))

    GENDER = "auto"  # 男性ノードは "boy"

    def design(self, **kw):
        _reload_if_changed()
        指示文 = kw.get("指示文", ""); 除外 = kw.get("除外", ""); 種族 = kw.get("種族", "自動"); モチーフ = kw.get("モチーフ", "自動"); 服装 = kw.get("服装", "自動")
        服装2 = kw.get("服装2", "なし"); 性格 = kw.get("性格", "自動"); 一貫性 = kw.get("一貫性", "標準"); 装飾量 = kw.get("装飾量", "2 標準"); シルエット = kw.get("シルエット", "自動")
        シェイプ = kw.get("シェイプ", "自動"); 世界観 = kw.get("世界観", "自動"); マスコット = kw.get("マスコット", "自動"); 顔の印 = kw.get("顔の印", "なし"); 手持ち = kw.get("手持ち", "自動")
        年齢感 = kw.get("年齢感", "自動"); 胸 = kw.get("胸", "自動"); 身長 = kw.get("身長", "自動"); 体型 = kw.get("体型", "自動"); 服の色 = kw.get("服の色", "自動"); 髪の色 = kw.get("髪の色", "自動")
        シード = kw.get("シード", 0); 意外性 = kw.get("意外性", "自動"); 露出 = kw.get("露出", "自動"); 出力形式 = kw.get("出力形式", "タグ"); 再現性 = kw.get("再現性", "厳密（タグ骨格・再現性重視）")
        強調 = kw.get("強調", 1.6); 表情ポーズ = kw.get("表情ポーズ", "表情のみ"); 目の形 = kw.get("目の形", "自動"); 固定 = kw.get("固定", False); キャラシート = kw.get("キャラシート", "")

        if 固定 and キャラシート.strip():
            # ロック中: シートを正として positive / negative を取り出す（再生成しない）
            parts = engine.parse_sheet_all(キャラシート)
            positive, negative = parts["positive"], parts["negative"]
            equipment, equipment_neg = parts["equipment"], parts["equipment-negative"]
            sheet = キャラシート
            # 三面図・表情シートは positive から組み立てる（表情のタグは残るが実用上は問題ない）
            turnaround = positive + (". " + equipment if equipment else "") + ", character sheet, multiple views, turnaround, front view, side view, back view, full body, standing, arms at sides, white background, simple background"
            expressions = positive + ", expression chart, multiple views, portrait, same character, (smile, angry, sad, surprised, embarrassed blush, smug), white background, simple background"
        else:
            character = engine.generate(
                brief=指示文,
                seed=シード,
                twist=TWIST_JP.get(意外性, "auto"),
                exposure=EXPOSURE_JP.get(露出, "auto"),
                personality=_jp_key(性格),
                motif=_jp_key(種族),
                theme={"なし": "none", "ランダム": "random"}.get(モチーフ) or _jp_key(モチーフ),
                role=_jp_key(服装),
                role2="random" if 服装2 == "ランダム" else ("none" if 服装2 == "なし" else _jp_key(服装2)),
                exclude=除外,
                handheld={"自動": "auto", "なし": "none", "ランダム": "random", "巨大武器": "giant", "服装の小道具": "role"}.get(手持ち) or _jp_key(手持ち),
                coherence={"なし": "none", "弱": "weak", "標準": "normal", "強": "strong"}.get(一貫性, "normal"),
                detail_level=int(str(装飾量).split(" ")[0]),
                silhouette=_jp_key(シルエット),
                era=_jp_key(世界観),
                mascot={"自動": "auto", "なし": "none", "ランダム": "random"}.get(マスコット) or _jp_key(マスコット),
                face_mark={"なし": "none", "ランダム": "random"}.get(顔の印) or _jp_key(顔の印),
                shape_lang=_jp_key(シェイプ),
                age=_jp_key(年齢感),
                bust=胸 if 胸 != "自動" else "auto",
                height=身長 if 身長 != "自動" else "auto",
                build=体型 if 体型 != "自動" else "auto",
                main_color=_jp_key(服の色),
                hair_color=_jp_key(髪の色),
                prompt_style=STYLE_JP.get(出力形式, "tags"),
                consistency=CONSISTENCY_JP.get(再現性, "strict"),
                emphasis=強調,
                expression_pose=EXPRESSION_JP.get(表情ポーズ, "expression_only"),
                eye_shape=EYE_SHAPE_JP.get(目の形, "auto"),
                gender=self.GENDER,
            )
            sheet = engine.build_sheet(character)
            positive = engine.build_positive(character)
            negative = engine.build_negative(character)
            turnaround = engine.build_turnaround(character)
            expressions = engine.build_expression_sheet(character)
            equipment = engine.build_equipment(character)
            equipment_neg = engine.build_equipment_negative(character)

        # "ui" の text は js/character_designer.js が受け取り、キャラシート欄に書き戻します
        return {"ui": {"text": [sheet]}, "result": (positive, negative, sheet, シード, turnaround, expressions, equipment, equipment_neg)}


class MaleCharacterDesignerNode(CharacterDesignerNode):
    """男性キャラクター版。性別を男性に固定し、女性限定の性格と胸の指定を外す"""
    GENDER = "boy"

    @classmethod
    def INPUT_TYPES(cls):
        t = CharacterDesignerNode.INPUT_TYPES()
        req = dict(t["required"])
        req["指示文"] = ("STRING", {"multiline": False, "default": "",
                                   "placeholder": "例: 騎士・俺様 / 狼・執事・無口 / 王子様・金髪（空ならすべてランダム。性別は男性固定）",
                                   "tooltip": "雰囲気の指示。「・」「,」「空白」区切り。辞書に無い英単語は自由モチーフとして小物・模様に混ざります"})
        req["性格"] = (["自動"] + [f"{v['jp']} ({k})" for k, v in data.ARCHETYPES.items() if k not in data.FEMALE_ONLY_ARCHS], {"default": "自動", "tooltip": "自動以外は指示文より優先"})
        req["服装"] = (["自動"] + [f"{v['jp']} ({k})" for k, v in data.ROLES.items() if "male" in v], {"default": "自動", "tooltip": "男性用の服装がある系統のみ"})
        req["服装2"] = (["なし", "ランダム"] + [f"{v['jp']} ({k})" for k, v in data.ROLES.items() if "male" in v], {"default": "なし", "tooltip": "2つ目の服装系統と融合"})
        del req["胸"]
        return {"required": req}


MONSTER_COHERENCE_JP = {"なし": "none", "弱": "weak", "標準": "normal", "強": "strong"}


class MonsterDesignerNode:
    """人型ではない完全なモンスター（竜・獣・スライム・ゴーレム・植物・虫・機械・霊体…）を設計する"""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "指示文": ("STRING", {"multiline": False, "default": "",
                                     "placeholder": "例: ドラゴン・炎・巨大 / スライム・毒・愛嬌 / 大狼・氷・威厳・白（空ならすべてランダム）",
                                     "tooltip": "種別・属性・大きさ・気質・色を「・」「,」「空白」区切りで。辞書に無い英単語は模様・角・体の形に混ざります"}),
                "除外": ("STRING", {"multiline": False, "default": "", "placeholder": "出したくない語（例: スライム, 毒, 不気味）",
                                   "tooltip": "ランダム選択のプールから種別/属性/気質を外します"}),
                "種別": (["自動"] + [f"{v['jp']} ({k})" for k, v in monster.TYPES.items()], {"default": "自動", "tooltip": "体の設計図。自動以外は指示文より優先"}),
                "属性": (["自動", "なし"] + [f"{v['jp']} ({k})" for k, v in monster.ELEMENTS.items()], {"default": "自動", "tooltip": "体表のエフェクト・配色・模様。自動は種別に合う属性を80%で"}),
                "大きさ": (["自動"] + [f"{v['jp']} ({k})" for k, v in monster.SIZES.items()], {"default": "自動", "tooltip": "自動は種別の既定±1段"}),
                "気質": (["自動"] + [f"{v['jp']} ({k})" for k, v in monster.TEMPERS.items()], {"default": "自動", "tooltip": "目・姿勢・表情（人型の性格に相当）。シェイプ言語の既定もここから"}),
                "一貫性": (["なし", "弱", "標準", "強"], {"default": "標準", "tooltip": "種別・属性・気質からコンセプト（例: 炎の古竜）を導出し、装飾や配色をそれに寄せる強さ"}),
                "装飾量": (["0 なし", "1 控えめ", "2 標準", "3 盛る"], {"default": "2 標準", "tooltip": "体の装飾（骨甲冑・結晶・棘・ルーン・鎖・苔・追加の目・機械部品…）の数"}),
                "シェイプ": (["自動"] + [f"{v['jp']} ({k})" for k, v in data.SHAPES.items()], {"default": "自動", "tooltip": "丸=親しみ/四角=安定/鋭角=攻撃性。自動は気質から"}),
                "世界観": (["自動"] + [f"{v['jp']} ({k})" for k, v in data.ERAS.items()], {"default": "自動", "tooltip": "SF 以外では機械部品の装飾が出ません"}),
                "体の色": (["自動"] + [f"{jp} ({k})" for k, jp in data.COLOR_JP.items()], {"default": "自動", "tooltip": "体のメインカラー。副色・差し色は属性のパレットから"}),
                "シード": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "control_after_generate": True}),
                "出力形式": (list(STYLE_JP), {"default": "タグ"}),
                "再現性": (list(CONSISTENCY_JP), {"default": "厳密（タグ骨格・再現性重視）", "tooltip": "厳密=主要タグに重み / 詳細=重みなし"}),
                "強調": ("FLOAT", {"default": 1.6, "min": 0.0, "max": 3.0, "step": 0.1}),
                "固定": ("BOOLEAN", {"default": False, "label_on": "固定中（シートを使用）", "label_off": "生成する"}),
                "キャラシート": ("STRING", {"multiline": True, "default": "", "placeholder": "生成するとここにモンスターシートが残ります。「固定」を ON にするとこの内容がそのまま出力されます。"}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "INT", "STRING")
    RETURN_NAMES = ("positive", "negative", "キャラシート", "シード", "三面図")
    FUNCTION = "design"
    CATEGORY = "Test/Example Nodes"
    OUTPUT_NODE = True

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return str(sorted(_source_mtimes().items()))

    def design(self, **kw):
        _reload_if_changed()
        固定 = kw.get("固定", False); キャラシート = kw.get("キャラシート", ""); シード = kw.get("シード", 0)
        if 固定 and キャラシート.strip():
            positive, negative = engine.parse_sheet(キャラシート)
            sheet = キャラシート
            turnaround = positive + ", creature sheet, multiple views, turnaround, front view, side view, back view, full body, white background, simple background"
        else:
            m = monster.generate(
                brief=kw.get("指示文", ""), seed=シード, exclude=kw.get("除外", ""),
                mtype=_jp_key(kw.get("種別", "自動")), element={"なし": "none"}.get(kw.get("属性", "自動")) or _jp_key(kw.get("属性", "自動")),
                size=_jp_key(kw.get("大きさ", "自動")), temper=_jp_key(kw.get("気質", "自動")),
                coherence=MONSTER_COHERENCE_JP.get(kw.get("一貫性", "標準"), "normal"), detail_level=int(str(kw.get("装飾量", "2 標準")).split(" ")[0]),
                shape_lang=_jp_key(kw.get("シェイプ", "自動")), era=_jp_key(kw.get("世界観", "自動")), main_color=_jp_key(kw.get("体の色", "自動")),
                emphasis=kw.get("強調", 1.6), consistency=CONSISTENCY_JP.get(kw.get("再現性", ""), "strict"), prompt_style=STYLE_JP.get(kw.get("出力形式", "タグ"), "tags"),
            )
            sheet = monster.build_sheet(m); positive = monster.build_positive(m); negative = monster.build_negative(m); turnaround = monster.build_turnaround(m)
        return {"ui": {"text": [sheet]}, "result": (positive, negative, sheet, シード, turnaround)}
