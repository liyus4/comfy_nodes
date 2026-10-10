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

from . import data, engine, outfit_tags

# --- 開発用ホットリロード -----------------------------------------------------
# data.py / outfit_tags.py / engine.py が更新されていたら、実行時に再読み込みする（ComfyUI の再起動不要）。
# node.py 自体（入力欄の定義）と js/ の変更は従来どおり再起動 + ブラウザリロードが必要。
_WATCHED = (data, outfit_tags, engine)
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
EXPOSURE_JP = {"自動": "auto", "控えめ": "modest", "標準": "standard", "高露出": "high"}
STYLE_JP = {"タグ": "tags", "文章": "natural"}
CONSISTENCY_JP = {"厳密（タグ骨格・再現性重視）": "strict", "詳細（説明文）": "full"}
EXPRESSION_JP = {"表情のみ": "expression_only", "表情とポーズ": "both", "なし": "none"}
EYE_SHAPE_JP = {"自動": "auto", "ツリ目": "tsurime", "タレ目": "tareme", "ジト目": "jitome", "三白眼": "sanpaku"}

_KEY_RE = re.compile(r"\(([a-z_]+)\)\s*$")


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
                    "default": "悪魔・女の子・高露出",
                    "placeholder": "例: 悪魔・女の子・高露出 / 猫耳メイド・ツンデレ / 天使・清楚・黒髪・タレ目",
                    "tooltip": "雰囲気の指示。「・」「,」「空白」区切り。辞書に無い語はそのまま末尾に通します",
                }),
                "除外": ("STRING", {
                    "multiline": False, "default": "",
                    "placeholder": "出したくない語（例: 水着, バニー, 高露出, ヤンデレ）",
                    "tooltip": "ランダム選択のプールからモチーフ/服装/性格/露出を外します。明示した指定の方が優先",
                }),
                "モチーフ": (_jp_choices(data.MOTIFS), {"default": "自動", "tooltip": "自動以外は指示文より優先"}),
                "服装": (_jp_choices(data.ROLES), {"default": "自動", "tooltip": "自動以外は指示文より優先"}),
                "服装2": (["なし", "ランダム"] + _jp_choices(data.ROLES)[1:], {"default": "なし",
                          "tooltip": "2つ目の服装系統と融合（服装を土台に、頭・顔・手・首・羽織り・小物を取り込む）。指示文に系統を2つ書いても融合します"}),
                "性格": (_jp_choices(data.ARCHETYPES), {"default": "自動", "tooltip": "自動以外は指示文より優先"}),
                "シード": ("INT", {
                    "default": 0, "min": 0, "max": 0xffffffffffffffff,
                    "control_after_generate": True,
                    "tooltip": "同じ指示文とシードなら必ず同じキャラになります",
                }),
                "意外性": (list(TWIST_JP), {"default": "自動", "tooltip": "王道=悪魔→サキュバス / 意外性=悪魔→シスター / 自動=4割で意外性"}),
                "露出": (list(EXPOSURE_JP), {"default": "自動", "tooltip": "自動は指示文の指定 > ランダム"}),
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

    RETURN_TYPES = ("STRING", "STRING", "STRING", "INT")
    RETURN_NAMES = ("positive", "negative", "キャラシート", "シード")
    FUNCTION = "design"
    CATEGORY = "Test/Example Nodes"
    OUTPUT_NODE = True

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # data.py / engine.py を編集したら、同じ入力でもキャッシュを使わず再実行させる
        return str(sorted(_source_mtimes().items()))

    def design(self, 指示文, 除外, モチーフ, 服装, 服装2, 性格, シード, 意外性, 露出, 出力形式, 再現性, 強調, 表情ポーズ, 目の形, 固定, キャラシート):
        _reload_if_changed()

        if 固定 and キャラシート.strip():
            # ロック中: シートを正として positive / negative を取り出す（再生成しない）
            positive, negative = engine.parse_sheet(キャラシート)
            sheet = キャラシート
        else:
            character = engine.generate(
                brief=指示文,
                seed=シード,
                twist=TWIST_JP.get(意外性, "auto"),
                exposure=EXPOSURE_JP.get(露出, "auto"),
                personality=_jp_key(性格),
                motif=_jp_key(モチーフ),
                role=_jp_key(服装),
                role2="random" if 服装2 == "ランダム" else ("none" if 服装2 == "なし" else _jp_key(服装2)),
                exclude=除外,
                prompt_style=STYLE_JP.get(出力形式, "tags"),
                consistency=CONSISTENCY_JP.get(再現性, "strict"),
                emphasis=強調,
                expression_pose=EXPRESSION_JP.get(表情ポーズ, "expression_only"),
                eye_shape=EYE_SHAPE_JP.get(目の形, "auto"),
            )
            sheet = engine.build_sheet(character)
            positive = engine.build_positive(character)
            negative = engine.build_negative(character)

        # "ui" の text は js/character_designer.js が受け取り、キャラシート欄に書き戻します
        return {"ui": {"text": [sheet]}, "result": (positive, negative, sheet, シード)}
