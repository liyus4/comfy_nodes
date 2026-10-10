"""
ComfyUI ノード: Random Character Designer

軽い指示文（例: "悪魔・女の子・高露出"）と seed から、人気キャラクターの設計手法に沿った
キャラクターを1体設計し、再現性の高いプロンプト（positive / negative）と
「キャラクターシート」を出力します。

出力は「キャラの特徴」だけです。品質タグ（masterpiece 等）・solo・1girl/1boy・画風・状況は含めないので、
別ノードで作ったテキストと連結して使ってください。

使い方:
  1. brief に雰囲気を書いて Queue。seed を変えるたびに別のキャラが出ます。
  2. 気に入ったら lock を ON。character_sheet 欄に残ったシートが
     そのまま positive / negative の出力元になり、同じキャラを再現できます。
     シートは手で編集しても OK（'#' 以降はコメント扱い）。
"""

import importlib
import os

from . import data, engine, outfit_tags

# --- 開発用ホットリロード -----------------------------------------------------
# data.py / engine.py が更新されていたら、実行時に再読み込みする（ComfyUI の再起動不要）。
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
            # data -> engine の順で reload（engine は data を参照しているため）
            importlib.reload(outfit_tags)
            importlib.reload(data)
            importlib.reload(engine)
            print("[CharacterDesigner] data.py / engine.py を再読み込みしました")
        except Exception as e:  # 編集途中の構文エラー等で落とさない
            print(f"[CharacterDesigner] 再読み込みに失敗しました（前回の内容で続行）: {e!r}")
            return
    _MTIMES = current


_reload_if_changed()


class CharacterDesignerNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "brief": ("STRING", {
                    "multiline": True,
                    "default": "悪魔・女の子・高露出",
                    "placeholder": "例: 悪魔・女の子・高露出 / 猫耳メイド・ツンデレ / 天使・清楚・黒髪",
                }),
                # 除外リスト: ランダム選択のプールから外す（例: "水着, バニー, 高露出, ヤンデレ"）
                "exclude": ("STRING", {"default": "", "multiline": False, "placeholder": "出したくない語（例: 水着, バニー, 高露出）"}),
                # ドロップダウン指定は brief より優先。auto なら brief かランダム
                "motif": (engine.motif_choices(), {"default": "auto"}),
                "role": (engine.role_choices(), {"default": "auto"}),
                "personality": (engine.personality_choices(), {"default": "auto"}),
                "seed": ("INT", {
                    "default": 0, "min": 0, "max": 0xffffffffffffffff,
                    "control_after_generate": True,
                }),
                # classic = 王道（悪魔→サキュバス） / surprise = 意外性（悪魔→シスター） / auto = 4割で surprise
                "twist": (list(engine.TWISTS), {"default": "auto"}),
                # auto = brief の指定 > ランダム（標準多め）
                "exposure": (["auto", *engine.EXPOSURES], {"default": "auto"}),
                # tags = SD/Pony/Illustrious 向けのカンマ区切り / natural = Flux/SD3 向けの文章
                "prompt_style": (["tags", "natural"], {"default": "tags"}),
                # strict = booru タグ骨格・2色・不安定要素なし（再現性重視） / full = 詳細説明文
                "consistency": (list(engine.CONSISTENCY), {"default": "strict"}),
                # strict で主役の服と記号に (tag:1.2) の重みを付ける
                "emphasis": ("BOOLEAN", {"default": True}),
                # 表情はキャラのデフォルト顔として含め、ポーズは状況側の責務なので既定では含めない
                "expression_pose": (["expression_only", "both", "none"], {"default": "expression_only"}),
                # 目の形を固定（auto なら brief の指定 > 性格プロファイル）
                "eye_shape": (["auto", *data.EYE_SHAPES], {"default": "auto"}),
                "lock": ("BOOLEAN", {"default": False, "label_on": "locked (use sheet)", "label_off": "generate"}),
                "character_sheet": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "生成するとここにキャラクターシートが残ります。lock を ON にするとこの内容がそのまま出力されます。",
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "INT")
    RETURN_NAMES = ("positive", "negative", "character_sheet", "seed")
    FUNCTION = "design"
    CATEGORY = "Test/Example Nodes"
    OUTPUT_NODE = True

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # data.py / engine.py を編集したら、同じ入力でもキャッシュを使わず再実行させる
        return str(sorted(_source_mtimes().items()))

    def design(self, brief, exclude, motif, role, personality, seed, twist, exposure, prompt_style, consistency, emphasis, expression_pose, eye_shape, lock, character_sheet):
        _reload_if_changed()

        if lock and character_sheet.strip():
            # ロック中: シートを正として positive / negative を取り出す（再生成しない）
            positive, negative = engine.parse_sheet(character_sheet)
            sheet = character_sheet
        else:
            character = engine.generate(
                brief=brief,
                seed=seed,
                twist=twist,
                exposure=exposure,
                personality=engine.choice_key(personality),
                motif=engine.choice_key(motif),
                role=engine.choice_key(role),
                exclude=exclude,
                prompt_style=prompt_style,
                expression_pose=expression_pose,
                consistency=consistency,
                emphasis=emphasis,
                eye_shape=eye_shape,
            )
            sheet = engine.build_sheet(character)
            positive = engine.build_positive(character)
            negative = engine.build_negative(character)

        # "ui" の text は js/character_designer.js が受け取り、character_sheet 欄に書き戻します
        return {"ui": {"text": [sheet]}, "result": (positive, negative, sheet, seed)}
