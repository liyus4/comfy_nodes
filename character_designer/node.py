"""
ComfyUI ノード: Random Character Designer

軽い指示文（例: "悪魔・女の子・高露出"）と seed から、人気キャラクターの設計手法に沿った
キャラクターを1体設計し、再現性の高いプロンプト（positive / negative）と
「キャラクターシート」を出力します。

使い方:
  1. brief に雰囲気を書いて Queue。seed を変えるたびに別のキャラが出ます。
  2. 気に入ったら lock を ON。character_sheet 欄に残ったシートが
     そのまま positive / negative の出力元になり、同じキャラを再現できます。
     シートは手で編集しても OK（'#' 以降はコメント扱い）。
"""

from . import engine


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
                "seed": ("INT", {
                    "default": 0, "min": 0, "max": 0xffffffffffffffff,
                    "control_after_generate": True,
                }),
                # classic = 王道（悪魔→サキュバス） / surprise = 意外性（悪魔→シスター） / auto = 4割で surprise
                "twist": (list(engine.TWISTS), {"default": "auto"}),
                # auto = brief の指定 > ランダム（標準多め）
                "exposure": (["auto", *engine.EXPOSURES], {"default": "auto"}),
                "personality": (engine.personality_choices(), {"default": "auto"}),
                # tags = SD/Pony/Illustrious 向けのカンマ区切り / natural = Flux/SD3 向けの文章
                "prompt_style": (["tags", "natural"], {"default": "tags"}),
                "prefix": ("STRING", {"default": "masterpiece, best quality, highly detailed", "multiline": False}),
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

    def design(self, brief, seed, twist, exposure, personality, prompt_style, prefix, lock, character_sheet):
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
                personality=engine.personality_key(personality),
                prompt_style=prompt_style,
                prefix=prefix,
            )
            sheet = engine.build_sheet(character)
            positive = engine.build_positive(character)
            negative = engine.build_negative(character)

        # "ui" の text は js/character_designer.js が受け取り、character_sheet 欄に書き戻します
        return {"ui": {"text": [sheet]}, "result": (positive, negative, sheet, seed)}
