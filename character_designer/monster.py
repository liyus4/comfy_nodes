# -*- coding: utf-8 -*-
"""
Random Monster Designer のデータとエンジン。
人型ではない「完全なモンスター」（竜・獣・スライム・ゴーレム・植物・虫・機械・霊体…）を
seed 固定で設計し、Anima 向けの positive / negative / シートを作る。
キャラクター版（engine.py / data.py）の配色・ムード・形状・自由モチーフの仕組みを流用する。
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from . import data as D
from . import engine as E

# ---------------------------------------------------------------------------
# 種別（体の設計図）。parts: 部位 -> テンプレート（{main}/{sub}/{accent}/{shape} を穴埋め）
#   surface: 体表の語（配色タグ "{main} scales" に使う）  loco: 移動様式  size: 既定の大きさ
# ---------------------------------------------------------------------------
TYPES: Dict[str, dict] = {
    "dragon": {"jp": "ドラゴン", "syn": ["ドラゴン", "竜", "龍", "古竜", "dragon", "wyrm"], "tags": ["dragon", "western dragon"], "surface": "scales", "loco": "quadruped", "size": "huge",
               "kind": "a massive four-legged dragon with vast wings", "moods": ["fire", "royal", "military"], "elements": ["fire", "ice", "dark", "thunder", "holy"],
               "parts": {"head": ["a long horned head with {sub} horns curving back", "a crowned head with a {shape}-shaped frill of {sub} spines", "a blunt heavy skull with four {sub} horns"],
                         "wings": ["huge {sub} membrane wings with {accent} veins", "wings edged with {accent} light", "tattered {sub} wings"],
                         "tail": ["a long tail ending in a {shape}-shaped {sub} blade", "a spiked tail with {accent} glowing tip", "a thick club tail"],
                         "chest": ["{sub} armored belly plates", "a chest crisscrossed with old scars", "{accent} glowing chest core"]}},
    "wyvern": {"jp": "ワイバーン", "syn": ["ワイバーン", "飛竜", "wyvern"], "tags": ["wyvern", "dragon"], "surface": "scales", "loco": "flying", "size": "large",
               "kind": "a two-legged winged wyvern built for flight", "moods": ["sky", "wild", "military"], "elements": ["wind", "poison", "thunder", "fire"],
               "parts": {"head": ["a narrow beaked head with {sub} crest", "a hooked snout with a {shape}-shaped crest"], "wings": ["bat-like {sub} wings with clawed thumbs", "wide {sub} wings with {accent} tips"],
                         "tail": ["a whip tail with a venomous {accent} stinger", "a long rudder tail with {sub} fin"]}},
    "drake": {"jp": "地竜", "syn": ["地竜", "ドレイク", "drake", "land dragon"], "tags": ["dragon", "drake"], "surface": "scales", "loco": "quadruped", "size": "large",
              "kind": "a heavy wingless land dragon", "moods": ["fire", "wild", "ruin"], "elements": ["fire", "earth", "poison", "metal"],
              "parts": {"head": ["a broad armored head with a {shape}-shaped nose horn", "a crocodile-like jaw lined with {accent} teeth"], "back": ["a ridge of {sub} dorsal plates", "{sub} bony armor covering the back"],
                        "tail": ["a heavy mace tail with {sub} knobs", "a tail with {accent} spines"]}},
    "hydra": {"jp": "ヒュドラ", "syn": ["ヒュドラ", "ハイドラ", "多頭竜", "hydra"], "tags": ["hydra", "multiple heads", "dragon"], "surface": "scales", "loco": "quadruped", "size": "huge",
              "kind": "a many-headed serpentine dragon", "moods": ["sick", "dark", "water"], "elements": ["poison", "water", "dark"],
              "parts": {"heads": ["five snake-like heads on long necks", "three heads, each with a different {accent} glowing eye color", "seven writhing heads with {sub} frills"], "body": ["a bloated {sub} underbelly", "a body coiled on short legs"],
                        "tail": ["a tail that splits into two tips", "a tail dragging {accent} slime"]}},
    "slime": {"jp": "スライム", "syn": ["スライム", "粘体", "slime", "ooze", "gel"], "tags": ["slime (creature)", "goo"], "surface": "gel", "loco": "amorphous", "size": "small",
              "kind": "a translucent amorphous slime", "moods": ["water", "cute", "play"], "elements": ["water", "poison", "crystal", "holy"],
              "parts": {"body": ["a {main} translucent blob with a {accent} glowing core", "a wobbling dome of {main} gel with bubbles inside", "a {main} slime shaped like a {shape}"],
                        "face": ["two simple dot eyes and a wide mouth", "a single {accent} eye floating inside", "no face at all, only a glowing core"],
                        "extra": ["small {sub} objects suspended inside the body", "dripping {main} droplets", "tiny pseudopods reaching out"]}},
    "golem": {"jp": "ゴーレム", "syn": ["ゴーレム", "岩巨人", "石像", "golem", "stone golem"], "tags": ["golem", "stone", "rock"], "surface": "stone", "loco": "biped", "size": "huge",
              "kind": "a towering golem of rough stone", "moods": ["ruin", "military", "nature"], "elements": ["earth", "crystal", "holy", "metal"],
              "parts": {"body": ["blocky {main} stone slabs held together by {accent} glowing seams", "a body of weathered {main} boulders", "{main} stone with moss in every crack"],
                        "head": ["a faceless head with a single {accent} glowing rune", "a crude carved face with hollow {accent} eyes", "no head, a {accent} core set in the chest"],
                        "arms": ["enormous slab arms dragging on the ground", "one arm larger than the other", "arms ending in {sub} crystal fists"]}},
    "treant": {"jp": "トレント", "syn": ["トレント", "樹木", "木の魔物", "treant", "ent", "tree monster"], "tags": ["treant", "tree", "plant monster"], "surface": "bark", "loco": "rooted", "size": "huge",
               "kind": "a walking tree with a gnarled face in its trunk", "moods": ["nature", "ruin", "night"], "elements": ["plant", "earth", "holy", "dark"],
               "parts": {"trunk": ["a thick {main} trunk with a split face", "a hollow trunk glowing {accent} inside", "a trunk wrapped in {sub} vines"],
                         "crown": ["a crown of {sub} leaves", "bare dead branches", "{accent} blossoms among the branches"], "roots": ["root legs that creep forward", "roots bursting from the ground", "roots clutching stones"]}},
    "mandragora": {"jp": "マンドラゴラ", "syn": ["マンドラゴラ", "マンドレイク", "人参の魔物", "mandragora", "mandrake"], "tags": ["mandragora", "plant monster"], "surface": "skin", "loco": "rooted", "size": "tiny",
                   "kind": "a small screaming root creature", "moods": ["nature", "cute", "sick"], "elements": ["plant", "poison", "earth"],
                   "parts": {"body": ["a {main} root body with stubby limbs", "a wrinkled {main} tuber with a {accent} glowing mouth"], "head": ["a tuft of {sub} leaves on the head", "a {shape}-shaped flower on the head"]}},
    "carnivorous_plant": {"jp": "食人植物", "syn": ["食人植物", "食虫植物", "ラフレシア", "man-eating plant", "carnivorous plant", "flytrap"], "tags": ["plant monster", "carnivorous plant"], "surface": "petals", "loco": "rooted", "size": "large",
                          "kind": "a giant carnivorous plant", "moods": ["nature", "sick", "sexy"], "elements": ["poison", "plant", "water"],
                          "parts": {"mouth": ["a huge {main} maw lined with {accent} thorn teeth", "a flytrap head dripping {accent} nectar"], "vines": ["{sub} vines lashing in every direction", "vines tipped with {shape}-shaped buds"],
                                    "roots": ["a bulbous {main} bulb at the base", "roots spread like legs"]}},
    "mushroom": {"jp": "キノコの魔物", "syn": ["キノコ", "茸", "マイコニド", "mushroom", "myconid", "fungus"], "tags": ["mushroom", "plant monster"], "surface": "cap", "loco": "biped", "size": "small",
                 "kind": "a walking mushroom creature", "moods": ["nature", "night", "sick"], "elements": ["poison", "plant", "dark", "light"],
                 "parts": {"cap": ["a wide {main} cap with {accent} spots", "a {main} cap glowing faintly {accent}", "a cap shaped like a {shape}"], "body": ["a pale {sub} stalk with stubby legs", "a stalk covered in tiny {accent} eyes"],
                           "extra": ["spores drifting around it", "smaller mushrooms growing from its back"]}},
    "giant_wolf": {"jp": "大狼", "syn": ["大狼", "狼の魔物", "魔狼", "フェンリル", "giant wolf", "dire wolf", "fenrir"], "tags": ["wolf", "oversized animal"], "surface": "fur", "loco": "quadruped", "size": "large",
                   "kind": "a giant wolf", "moods": ["wild", "night", "ice"], "elements": ["ice", "dark", "thunder", "holy"],
                   "parts": {"head": ["a long muzzle with {accent} glowing eyes", "a scarred face with one {accent} eye", "a head with {sub} bone armor"], "fur": ["a thick {sub} mane around the neck", "fur bristling into {shape}-shaped tufts"],
                             "tail": ["a bushy {main} tail with {sub} tip", "three tails"]}},
    "cerberus": {"jp": "ケルベロス", "syn": ["ケルベロス", "三つ首", "地獄の番犬", "cerberus", "hellhound"], "tags": ["cerberus", "multiple heads", "dog"], "surface": "fur", "loco": "quadruped", "size": "large",
                 "kind": "a three-headed hound", "moods": ["fire", "dark", "military"], "elements": ["fire", "dark", "poison"],
                 "parts": {"heads": ["three snarling heads with {accent} eyes", "three heads, the middle one larger with a {sub} mane"], "body": ["{main} fur with {accent} embers glowing underneath", "a chest wrapped in {sub} chains"],
                           "tail": ["a serpent for a tail", "a tail of {accent} flame"]}},
    "griffin": {"jp": "グリフォン", "syn": ["グリフォン", "グリフィン", "鷲獅子", "griffin", "gryphon"], "tags": ["griffin", "wings"], "surface": "feathers", "loco": "flying", "size": "large",
                "kind": "a griffin with an eagle's head and a lion's body", "moods": ["sky", "royal", "light"], "elements": ["wind", "holy", "thunder", "light"],
                "parts": {"head": ["an eagle head with {accent} eyes and a {sub} beak", "a head crested with {sub} feathers"], "wings": ["broad {main} feathered wings with {sub} tips", "wings trailing {accent} light"],
                          "body": ["a lion body with {sub} fur", "a body with {accent} markings on the flanks"]}},
    "phoenix": {"jp": "不死鳥", "syn": ["不死鳥", "フェニックス", "火の鳥", "phoenix", "firebird"], "tags": ["phoenix", "bird"], "surface": "feathers", "loco": "flying", "size": "large",
                "kind": "a bird of living flame", "moods": ["fire", "holy", "light"], "elements": ["fire", "holy", "light"],
                "parts": {"plumage": ["{main} feathers that burn at the edges", "{main} plumage with {accent} flame tips"], "tail": ["a long trailing tail of {accent} fire", "tail feathers shaped like {shape}s"],
                          "crest": ["a {sub} crest of flame", "a crest shaped like a crown"]}},
    "chimera": {"jp": "キマイラ", "syn": ["キマイラ", "キメラ", "合成獣", "chimera"], "tags": ["chimera", "multiple heads"], "surface": "fur", "loco": "quadruped", "size": "large",
                "kind": "a chimera fused from several beasts", "moods": ["wild", "dark", "fire"], "elements": ["fire", "poison", "dark"],
                "parts": {"heads": ["a lion head and a {sub} goat head side by side", "a lion head, a goat head and a snake-headed tail"], "body": ["a {main} lion body with {sub} goat legs", "a body stitched together with {accent} glowing seams"],
                          "wings": ["small {sub} dragon wings", "no wings"]}},
    "behemoth": {"jp": "ベヒモス", "syn": ["ベヒモス", "ベヒーモス", "巨獣", "behemoth"], "tags": ["behemoth", "oversized animal"], "surface": "hide", "loco": "quadruped", "size": "colossal",
                 "kind": "a mountain-sized beast", "moods": ["ruin", "military"], "elements": ["earth", "fire", "dark"],
                 "parts": {"head": ["a bull-like head with {sub} horns as big as trees", "a head with a {shape}-shaped horn"], "back": ["a back covered in {sub} bony plates", "a back where moss and trees grow"],
                           "legs": ["pillar legs cracking the ground", "legs with {accent} glowing joints"]}},
    "basilisk": {"jp": "バジリスク", "syn": ["バジリスク", "コカトリス", "石化竜", "basilisk", "cockatrice"], "tags": ["basilisk", "lizard"], "surface": "scales", "loco": "multi_legged", "size": "medium",
                 "kind": "an eight-legged lizard whose gaze turns things to stone", "moods": ["sick", "ruin", "dark"], "elements": ["poison", "earth", "dark"],
                 "parts": {"eyes": ["{accent} glowing eyes with petrifying light", "eyes wrapped in {sub} membrane"], "body": ["a long {main} body with eight legs", "a body with {sub} stone-like patches"],
                           "crest": ["a rooster-like {sub} comb", "a crest of {shape}-shaped spines"]}},
    "kraken": {"jp": "クラーケン", "syn": ["クラーケン", "大ダコ", "大イカ", "海の魔物", "kraken", "giant octopus", "giant squid"], "tags": ["kraken", "tentacles", "octopus"], "surface": "skin", "loco": "aquatic", "size": "colossal",
               "kind": "a colossal tentacled sea monster", "moods": ["water", "night", "dark"], "elements": ["water", "dark", "thunder", "poison"],
               "parts": {"tentacles": ["eight {main} tentacles with {accent} suckers", "tentacles tipped with {sub} hooks", "tentacles glowing {accent} at the tips"], "head": ["a bulbous {main} mantle with a single {accent} eye", "a beaked maw ringed by eyes"],
                         "extra": ["bioluminescent {accent} spots", "barnacles and coral on the skin"]}},
    "giant_shark": {"jp": "鮫の魔物", "syn": ["鮫", "サメ", "鮫の魔物", "giant shark", "shark monster"], "tags": ["shark", "oversized animal"], "surface": "skin", "loco": "aquatic", "size": "large",
                    "kind": "a monstrous shark", "moods": ["water", "wild", "military"], "elements": ["water", "ice", "metal"],
                    "parts": {"jaws": ["rows of {accent} teeth in a gaping jaw", "a jaw that unhinges wide"], "fins": ["{sub} fins edged like blades", "a dorsal fin shaped like a {shape}"], "extra": ["old harpoon scars", "{accent} glowing gill slits"]}},
    "jellyfish": {"jp": "クラゲの魔物", "syn": ["クラゲ", "海月", "jellyfish"], "tags": ["jellyfish"], "surface": "membrane", "loco": "floating", "size": "medium",
                  "kind": "a drifting giant jellyfish", "moods": ["water", "night", "magic"], "elements": ["water", "thunder", "light", "poison"],
                  "parts": {"bell": ["a translucent {main} bell with {accent} glowing veins", "a bell shaped like a {shape}"], "tentacles": ["long {sub} tentacles trailing {accent} light", "frilled {sub} oral arms"]}},
    "giant_spider": {"jp": "大蜘蛛", "syn": ["大蜘蛛", "蜘蛛の魔物", "giant spider", "spider monster"], "tags": ["spider", "oversized animal"], "surface": "carapace", "loco": "multi_legged", "size": "large",
                     "kind": "a giant spider", "moods": ["dark", "night", "sick"], "elements": ["poison", "dark", "crystal"],
                     "parts": {"legs": ["eight {main} jointed legs with {sub} bands", "legs tipped with {accent} blades"], "eyes": ["eight {accent} glowing eyes", "a cluster of eyes shaped like a {shape}"], "abdomen": ["a bloated {main} abdomen with a {accent} {shape} marking", "an abdomen trailing {sub} silk"]}},
    "scorpion": {"jp": "大サソリ", "syn": ["サソリ", "蠍", "大サソリ", "scorpion"], "tags": ["scorpion", "oversized animal"], "surface": "carapace", "loco": "multi_legged", "size": "medium",
                 "kind": "a giant armored scorpion", "moods": ["ruin", "sick", "military"], "elements": ["poison", "earth", "fire"],
                 "parts": {"claws": ["huge {sub} pincers", "pincers edged with {accent} glow"], "tail": ["a segmented tail with a {accent} glowing stinger", "a tail ending in a {shape}-shaped stinger"], "shell": ["{main} plated carapace with {sub} seams", "a carapace with {accent} cracks"]}},
    "giant_insect": {"jp": "巨大甲虫", "syn": ["甲虫", "カブトムシ", "巨大昆虫", "虫の魔物", "giant beetle", "giant insect", "mantis"], "tags": ["insect", "beetle", "oversized animal"], "surface": "carapace", "loco": "multi_legged", "size": "medium",
                     "kind": "a giant armored insect", "moods": ["nature", "military", "tech"], "elements": ["earth", "thunder", "metal", "plant"],
                     "parts": {"horn": ["a {shape}-shaped {sub} horn", "twin {sub} horns"], "shell": ["a glossy {main} carapace with {accent} edges", "a carapace with {sub} stripes"], "wings": ["{accent} translucent wings folded under the shell", "wings that hum with {accent} light"]}},
    "bone_dragon": {"jp": "骨竜", "syn": ["骨竜", "スケルトンドラゴン", "ボーンドラゴン", "bone dragon", "skeletal dragon", "undead dragon"], "tags": ["bone dragon", "skeleton", "dragon", "undead"], "surface": "bones", "loco": "quadruped", "size": "huge",
                    "kind": "a dragon skeleton animated by dark magic", "moods": ["dark", "ruin", "night"], "elements": ["dark", "poison", "ice", "holy"],
                    "parts": {"skull": ["a horned skull with {accent} fire in the eye sockets", "a cracked skull held together by {accent} light"], "wings": ["bare wing bones with tattered {sub} membrane", "wings of {accent} spectral light"],
                              "body": ["exposed {main} ribs with a {accent} glowing core inside", "bones wrapped in {sub} chains"]}},
    "zombie_beast": {"jp": "腐獣", "syn": ["腐獣", "ゾンビ獣", "アンデッド獣", "zombie beast", "undead beast", "rotting beast"], "tags": ["zombie", "undead", "oversized animal"], "surface": "hide", "loco": "quadruped", "size": "medium",
                     "kind": "a rotting undead beast", "moods": ["sick", "ruin", "dark"], "elements": ["poison", "dark", "plant"],
                     "parts": {"body": ["{main} rotting hide with exposed {sub} bone", "a body held together by {accent} glowing stitches"], "head": ["a jaw hanging loose", "a skull half exposed with one {accent} eye"], "extra": ["fungus growing from the back", "{accent} ooze dripping from wounds"]}},
    "gargoyle": {"jp": "ガーゴイル", "syn": ["ガーゴイル", "石像の魔物", "gargoyle"], "tags": ["gargoyle", "stone", "wings"], "surface": "stone", "loco": "flying", "size": "medium",
                 "kind": "a winged stone gargoyle", "moods": ["ruin", "night", "holy"], "elements": ["earth", "dark", "holy", "thunder"],
                 "parts": {"face": ["a grotesque {main} stone face with {accent} eyes", "a face carved like a {shape}"], "wings": ["cracked {main} stone wings", "wings with {accent} glowing cracks"], "body": ["a crouching body with {sub} lichen", "a body with moss in the carvings"]}},
    "floating_eye": {"jp": "浮遊眼球", "syn": ["浮遊眼球", "目玉の魔物", "ビホルダー", "floating eye", "eye monster", "beholder"], "tags": ["floating", "eyeball", "monster"], "surface": "skin", "loco": "floating", "size": "medium",
                     "kind": "a floating sphere dominated by one huge eye", "moods": ["magic", "dark", "tech"], "elements": ["dark", "thunder", "light", "void"],
                     "parts": {"eye": ["one huge {accent} eye with a {shape}-shaped pupil", "a central eye ringed by smaller eyes"], "body": ["a {main} fleshy sphere", "a {main} sphere with {sub} armored plates"], "stalks": ["eye stalks waving around it", "tentacles hanging below", "no limbs at all"]}},
    "tentacle_horror": {"jp": "触手の怪物", "syn": ["触手", "触手の怪物", "邪神", "不定形", "tentacle monster", "eldritch horror", "shoggoth"], "tags": ["tentacles", "eldritch abomination", "monster"], "surface": "flesh", "loco": "amorphous", "size": "huge",
                        "kind": "a shapeless mass of eyes and tentacles", "moods": ["dark", "night", "sick"], "elements": ["void", "dark", "poison", "water"],
                        "parts": {"mass": ["a {main} writhing mass with {accent} eyes opening everywhere", "a mass that folds in on itself"], "tentacles": ["countless {sub} tentacles", "tentacles ending in mouths"], "extra": ["a {shape}-shaped {accent} sigil floating above it", "reality bending around it"]}},
    "wisp": {"jp": "ウィスプ", "syn": ["ウィスプ", "鬼火", "人魂", "精霊の火", "wisp", "will-o-wisp", "hitodama"], "tags": ["hitodama", "floating", "fire"], "surface": "light", "loco": "floating", "size": "tiny",
             "kind": "a floating ball of spirit flame", "moods": ["night", "magic", "light"], "elements": ["light", "dark", "ice", "fire"],
             "parts": {"core": ["a {accent} flame core", "a core shaped like a {shape}"], "trail": ["a long {main} trailing tail of light", "smaller wisps orbiting it"], "face": ["a faint ghostly face", "no face"]}},
    "ghost_beast": {"jp": "霊獣", "syn": ["霊獣", "幽霊獣", "亡霊の獣", "ghost beast", "spectral beast", "spirit beast"], "tags": ["ghost", "spirit", "translucent"], "surface": "mist", "loco": "floating", "size": "medium",
                    "kind": "a translucent spectral beast", "moods": ["night", "holy", "ice"], "elements": ["light", "ice", "dark", "holy"],
                    "parts": {"body": ["a translucent {main} wolf-like form", "a deer-like form of {main} mist", "a serpent-like form of {main} light"], "eyes": ["{accent} glowing eyes", "no eyes, only a {accent} glow"], "extra": ["{sub} mist trailing behind", "{accent} floating lights around it"]}},
    "sacred_beast": {"jp": "神獣", "syn": ["神獣", "麒麟", "白狐", "九尾の獣", "sacred beast", "kirin", "divine beast", "nine-tailed fox"], "tags": ["kirin", "fox", "multiple tails"], "surface": "fur", "loco": "quadruped", "size": "large",
                     "kind": "a divine beast wreathed in light", "moods": ["holy", "wafu", "light"], "elements": ["holy", "light", "fire", "thunder"],
                     "parts": {"head": ["a deer-like head with a {sub} antler", "a fox head with {accent} markings"], "tails": ["nine {main} tails tipped with {accent} fire", "a single tail of {accent} light"], "extra": ["{accent} flames at the hooves", "a {shape}-shaped {sub} halo"]}},
    "elemental": {"jp": "精霊体", "syn": ["精霊体", "エレメンタル", "元素の魔物", "elemental"], "tags": ["elemental", "monster"], "surface": "element", "loco": "floating", "size": "large",
                  "kind": "a creature made entirely of its element", "moods": ["magic", "fire", "water"], "elements": ["fire", "ice", "thunder", "water", "wind", "earth"],
                  "parts": {"body": ["a vaguely beast-shaped body of raw {main} element", "a swirling {main} vortex with a {accent} core"], "limbs": ["limbs that dissolve and reform", "no limbs, only the swirling mass"], "extra": ["a {shape}-shaped {accent} core", "fragments orbiting it"]}},
    "crystal_beast": {"jp": "結晶獣", "syn": ["結晶獣", "クリスタルビースト", "宝石の魔物", "crystal beast", "gem monster"], "tags": ["crystal", "monster"], "surface": "crystal", "loco": "quadruped", "size": "medium",
                      "kind": "a beast made of living crystal", "moods": ["ice", "magic", "royal"], "elements": ["crystal", "ice", "light", "thunder"],
                      "parts": {"body": ["a {main} crystal body with {accent} light inside", "clustered {main} crystal shards forming a body"], "head": ["a head of {sub} crystal spikes", "a {shape}-shaped crystal head"], "extra": ["{accent} light refracting through the body", "crystal shards floating around it"]}},
    "machine_beast": {"jp": "機械獣", "syn": ["機械獣", "メカ獣", "機械の魔物", "ロボ獣", "machine beast", "mech beast", "robot beast"], "tags": ["mecha", "robot", "monster"], "surface": "armor", "loco": "quadruped", "size": "large",
                      "kind": "a beast-shaped war machine", "moods": ["tech", "military", "ruin"], "elements": ["thunder", "metal", "fire", "void"],
                      "parts": {"body": ["{main} armor plates with {accent} glowing lines", "a rusted {main} frame with exposed {sub} cables"], "head": ["a {accent} single-lens sensor head", "a head shaped like a {shape}"], "extra": ["thrusters on the back", "a cannon mounted on the back", "cables trailing like a tail"]}},
    "living_armor": {"jp": "生きた鎧", "syn": ["生きた鎧", "リビングアーマー", "空の鎧", "living armor", "animated armor"], "tags": ["living armor", "empty armor", "monster"], "surface": "armor", "loco": "biped", "size": "medium",
                     "kind": "a hollow suit of armor moving on its own", "moods": ["military", "ruin", "dark"], "elements": ["dark", "holy", "metal", "ice"],
                     "parts": {"body": ["hollow {main} plate armor with {accent} light leaking from the gaps", "{main} armor fused with {sub} rust"], "head": ["an empty helm with a {accent} glow inside", "a helm shaped like a {shape}"], "extra": ["a greatsword fused to its arm", "chains hanging from the armor"]}},
    "sandworm": {"jp": "砂虫", "syn": ["砂虫", "サンドワーム", "大ミミズ", "ワーム", "sandworm", "giant worm"], "tags": ["worm", "oversized animal"], "surface": "hide", "loco": "serpentine", "size": "colossal",
                 "kind": "a colossal burrowing worm", "moods": ["ruin", "wild"], "elements": ["earth", "poison", "fire"],
                 "parts": {"mouth": ["a round maw ringed with {accent} teeth", "a maw that opens in four petals"], "body": ["segmented {main} body with {sub} bands", "a body with {accent} glowing segments"], "extra": ["sand pouring off its back", "{sub} bristles along the body"]}},
    "mimic": {"jp": "ミミック", "syn": ["ミミック", "宝箱の魔物", "mimic"], "tags": ["mimic", "treasure chest", "monster"], "surface": "wood", "loco": "biped", "size": "small",
              "kind": "a treasure chest with teeth and a tongue", "moods": ["play", "dark", "royal"], "elements": ["dark", "poison", "crystal"],
              "parts": {"body": ["a {main} wooden chest with {sub} metal bands", "a chest shaped like a {shape}"], "mouth": ["rows of {accent} teeth and a long tongue", "a tongue dripping {accent} slime"], "extra": ["gold coins spilling out", "small legs under the chest", "eyes on the lid"]}},
    "giant_frog": {"jp": "大蛙", "syn": ["大蛙", "蛙の魔物", "ガマ", "giant frog", "toad monster"], "tags": ["frog", "oversized animal"], "surface": "skin", "loco": "quadruped", "size": "medium",
                   "kind": "a giant warty toad", "moods": ["water", "nature", "sick"], "elements": ["poison", "water", "plant"],
                   "parts": {"skin": ["{main} warty skin with {accent} spots", "slimy {main} skin"], "mouth": ["a wide mouth with a long tongue", "a mouth hiding {accent} teeth"], "extra": ["a {shape}-shaped {sub} marking on the back", "lily pads growing on its back"]}},
    "dragon_turtle": {"jp": "竜亀", "syn": ["竜亀", "玄武", "大亀", "dragon turtle", "giant turtle"], "tags": ["turtle", "dragon"], "surface": "shell", "loco": "quadruped", "size": "colossal",
                      "kind": "a mountain-like turtle with a dragon's head", "moods": ["water", "ruin", "holy"], "elements": ["water", "earth", "holy", "ice"],
                      "parts": {"shell": ["a {main} shell with a forest growing on top", "a shell carved with {accent} runes"], "head": ["a dragon head with {sub} whiskers", "a head crowned with {shape}-shaped horns"], "extra": ["water pouring from the shell", "{accent} glowing seams between the plates"]}},
}

# 属性（体表のエフェクト・配色・模様）
ELEMENTS: Dict[str, dict] = {
    "fire": {"jp": "炎", "syn": ["炎", "火", "火炎", "fire", "flame"], "tags": ["fire", "burning"], "moods": ["fire"], "palettes": [("black", "crimson", "orange"), ("crimson", "black", "gold"), ("brown", "orange", "yellow")],
             "effects": ["flames leaking from the joints", "{accent} embers glowing between the {surface}", "a mane of {accent} fire", "smoke rising from the mouth"], "pattern": "ember-like cracks"},
    "ice": {"jp": "氷", "syn": ["氷", "凍", "吹雪", "ice", "frost", "snow"], "tags": ["ice", "frost"], "moods": ["ice"], "palettes": [("white", "sky blue", "silver"), ("sky blue", "navy", "white"), ("lavender", "white", "sky blue")],
            "effects": ["{accent} ice crystals growing along the back", "frost breath", "icicles hanging from the body", "a body half encased in ice"], "pattern": "frost patterns"},
    "thunder": {"jp": "雷", "syn": ["雷", "電撃", "稲妻", "thunder", "lightning", "electric"], "tags": ["electricity", "lightning"], "moods": ["sky", "tech"], "palettes": [("navy", "yellow", "white"), ("black", "yellow", "sky blue"), ("purple", "yellow", "white")],
                "effects": ["{accent} lightning crackling along the body", "static sparks between the {surface}", "a {accent} glowing lightning-shaped marking"], "pattern": "lightning-bolt markings"},
    "water": {"jp": "水", "syn": ["水", "海", "潮", "water", "sea", "ocean"], "tags": ["water"], "moods": ["water"], "palettes": [("navy", "sky blue", "white"), ("teal", "white", "gold"), ("sky blue", "navy", "silver")],
              "effects": ["water flowing over the body", "{accent} glowing wave markings", "bubbles rising from the skin"], "pattern": "wave pattern"},
    "wind": {"jp": "風", "syn": ["風", "嵐", "疾風", "wind", "storm", "gale"], "tags": ["wind"], "moods": ["sky", "wild"], "palettes": [("white", "mint", "silver"), ("emerald green", "white", "gold"), ("sky blue", "white", "mint")],
             "effects": ["swirls of wind around the body", "{accent} glowing swirl markings", "feathers drifting around it"], "pattern": "swirl markings"},
    "earth": {"jp": "土", "syn": ["土", "岩", "大地", "earth", "rock", "stone"], "tags": ["rock", "stone"], "moods": ["nature", "ruin"], "palettes": [("brown", "gray", "gold"), ("gray", "emerald green", "brown"), ("brown", "black", "orange")],
              "effects": ["stone plates grown into the {surface}", "moss and grass growing on the back", "{accent} glowing rune carvings"], "pattern": "rune carvings"},
    "poison": {"jp": "毒", "syn": ["毒", "猛毒", "瘴気", "poison", "venom", "toxic"], "tags": ["poison"], "moods": ["sick", "dark"], "palettes": [("purple", "black", "emerald green"), ("dark purple", "mint", "black"), ("black", "purple", "yellow")],
               "effects": ["{accent} venom dripping from the fangs", "a purple miasma around the body", "{accent} glowing warning spots"], "pattern": "warning spots"},
    "holy": {"jp": "聖", "syn": ["聖", "神聖", "光の加護", "holy", "sacred", "divine"], "tags": ["halo", "glowing"], "moods": ["holy", "light"], "palettes": [("white", "gold", "sky blue"), ("cream", "gold", "white"), ("white", "silver", "lavender")],
             "effects": ["a {accent} halo floating above", "{accent} glowing sacred markings", "feathers of light drifting around it"], "pattern": "sacred markings"},
    "dark": {"jp": "闇", "syn": ["闇", "暗黒", "呪い", "dark", "shadow", "cursed"], "tags": ["darkness", "glowing eyes"], "moods": ["dark", "night"], "palettes": [("black", "dark purple", "crimson"), ("black", "gray", "purple"), ("dark purple", "black", "silver")],
             "effects": ["black mist bleeding from the body", "{accent} glowing cursed markings", "shadows writhing at its feet"], "pattern": "cursed markings"},
    "crystal": {"jp": "結晶", "syn": ["結晶", "水晶", "宝石", "crystal", "gem"], "tags": ["crystal"], "moods": ["magic", "ice"], "palettes": [("white", "sky blue", "lavender"), ("purple", "pastel pink", "white"), ("black", "teal", "silver")],
                "effects": ["{accent} crystals growing from the back", "a body veined with {accent} crystal", "crystal shards orbiting it"], "pattern": "crystal veins"},
    "metal": {"jp": "金属", "syn": ["金属", "鋼", "鉄", "metal", "steel", "iron"], "tags": ["metal", "armor"], "moods": ["military", "tech"], "palettes": [("silver", "black", "crimson"), ("gray", "gold", "black"), ("black", "silver", "sky blue")],
              "effects": ["{main} metal plates grown over the body", "rivets and seams across the {surface}", "{accent} glowing joints"], "pattern": "riveted plates"},
    "plant": {"jp": "植物", "syn": ["植物", "草", "花", "蔦", "plant", "flower", "vine"], "tags": ["plant", "flower"], "moods": ["nature"], "palettes": [("emerald green", "brown", "pastel pink"), ("mint", "white", "yellow"), ("dark green", "crimson", "gold")],
              "effects": ["{accent} flowers blooming on the body", "vines wrapped around the limbs", "leaves growing from the back"], "pattern": "leaf markings"},
    "light": {"jp": "光", "syn": ["光", "輝き", "星", "light", "radiant", "star"], "tags": ["glowing", "light particles"], "moods": ["light", "magic"], "palettes": [("white", "gold", "sky blue"), ("navy", "gold", "white"), ("lavender", "white", "gold")],
              "effects": ["{accent} light particles drifting from the body", "glowing {shape}-shaped markings", "a body that glows from within"], "pattern": "star markings"},
    "void": {"jp": "虚無", "syn": ["虚無", "宇宙", "次元", "void", "cosmic", "abyss"], "tags": ["space", "glowing"], "moods": ["night", "magic", "tech"], "palettes": [("black", "purple", "sky blue"), ("navy", "black", "pastel pink"), ("black", "teal", "white")],
             "effects": ["a starry void visible through gaps in the body", "{accent} glowing cosmic markings", "fragments floating weightlessly around it"], "pattern": "cosmic markings"},
}

# 大きさ: (jp, タグ, 説明文, 比較対象)
SIZES: Dict[str, dict] = {
    "tiny": {"jp": "極小", "syn": ["極小", "小さい", "手のひら", "tiny", "palm-sized"], "tags": ["tiny"], "nl": "tiny, small enough to sit in a palm"},
    "small": {"jp": "小型", "syn": ["小型", "小さめ", "small"], "tags": ["small"], "nl": "small, about the size of a dog"},
    "medium": {"jp": "中型", "syn": ["中型", "人間大", "medium", "human-sized"], "tags": [], "nl": "about the size of a human"},
    "large": {"jp": "大型", "syn": ["大型", "大きい", "馬大", "large", "big"], "tags": ["large"], "nl": "large, bigger than a horse"},
    "huge": {"jp": "巨大", "syn": ["巨大", "超大型", "huge", "giant"], "tags": ["giant monster", "huge"], "nl": "huge, towering over a house"},
    "colossal": {"jp": "超巨大", "syn": ["超巨大", "山のような", "colossal", "kaiju", "mountain-sized"], "tags": ["kaiju", "giant monster", "colossal"], "nl": "colossal, as large as a mountain"},
}
SIZE_ORDER = ["tiny", "small", "medium", "large", "huge", "colossal"]

# 気質: 目・姿勢・表情（人型の「性格」に相当）
TEMPERS: Dict[str, dict] = {
    "feral": {"jp": "獰猛", "syn": ["獰猛", "凶暴", "野生", "feral", "savage", "ferocious"], "tags": ["fangs", "snarling", "glowing eyes"], "nl": "feral and savage, fangs bared, muscles tensed to lunge", "moods": ["wild", "fire"]},
    "majestic": {"jp": "威厳", "syn": ["威厳", "王者", "気高い", "majestic", "noble", "regal"], "tags": ["majestic", "looking down"], "nl": "majestic and calm, standing tall as if ruling its domain", "moods": ["royal", "holy"]},
    "ancient": {"jp": "太古", "syn": ["太古", "古代", "眠れる", "ancient", "sleeping", "elder"], "tags": ["moss", "cracked"], "nl": "ancient and slow, half asleep, with moss and cracks of age across its body", "moods": ["ruin", "nature"]},
    "berserk": {"jp": "狂乱", "syn": ["狂乱", "暴走", "狂気", "berserk", "rampaging", "frenzied"], "tags": ["open mouth", "roaring", "veins"], "nl": "berserk and rampaging, roaring with glowing eyes and bulging veins", "moods": ["fire", "dark"]},
    "sacred": {"jp": "神聖", "syn": ["神聖", "神々しい", "sacred", "serene"], "tags": ["serene", "glowing"], "nl": "serene and sacred, moving without a sound, light clinging to its body", "moods": ["holy", "light"]},
    "eerie": {"jp": "不気味", "syn": ["不気味", "怪奇", "おぞましい", "eerie", "creepy", "unsettling"], "tags": ["glowing eyes", "unsettling"], "nl": "eerie and unsettling, moving in ways that look wrong", "moods": ["night", "sick"]},
    "cunning": {"jp": "狡猾", "syn": ["狡猾", "ずる賢い", "cunning", "sly"], "tags": ["narrowed eyes", "grin"], "nl": "cunning and patient, watching with narrowed eyes and a faint grin", "moods": ["dark", "play"]},
    "playful": {"jp": "愛嬌", "syn": ["愛嬌", "のんき", "かわいい", "playful", "goofy", "cute"], "tags": ["round eyes", "happy"], "nl": "playful and goofy, with round eyes and a clumsy posture", "moods": ["cute", "play"]},
}

# 体の装飾（装飾量）。slot が同じものは1つまで。cat: ムード
MODIFIERS: List[dict] = [
    {"tags": ["bone armor", "{sub} bone plates over the shoulders"], "nl": "plates of {sub} bone armor over the shoulders", "slot": "armor", "moods": ["military", "ruin"]},
    {"tags": ["metal armor", "{sub} metal plates bolted onto the body"], "nl": "{sub} metal plates bolted onto the body", "slot": "armor", "moods": ["tech", "military"]},
    {"tags": ["crystal growths", "{accent} crystals growing from the back"], "nl": "{accent} crystals growing from the back", "slot": "back", "moods": ["magic", "ice"]},
    {"tags": ["spikes", "rows of {sub} spikes along the spine"], "nl": "rows of {sub} spikes along the spine", "slot": "back", "moods": ["wild", "dark"]},
    {"tags": ["glowing runes", "{accent} glowing runes carved into the body"], "nl": "{accent} glowing runes carved into the body", "slot": "markings", "moods": ["magic", "holy"]},
    {"tags": ["stripes", "{sub} stripes across the body"], "nl": "{sub} stripes across the body", "slot": "markings", "moods": ["wild", "nature"]},
    {"tags": ["spots", "{accent} spots along the flanks"], "nl": "{accent} spots along the flanks", "slot": "markings", "moods": ["cute", "nature"]},
    {"tags": ["glowing cracks", "{accent} glowing cracks across the body"], "nl": "{accent} glowing cracks running across the body", "slot": "markings", "moods": ["fire", "ruin"]},
    {"tags": ["extra eyes", "a second pair of {accent} eyes"], "nl": "a second pair of {accent} eyes", "slot": "eyes", "moods": ["dark", "sick"]},
    {"tags": ["multiple heads", "a second smaller head"], "nl": "a second, smaller head growing from the shoulder", "slot": "heads", "moods": ["dark", "wild"]},
    {"tags": ["exposed bone", "exposed {sub} ribs"], "nl": "exposed {sub} ribs on one side", "slot": "wound", "moods": ["ruin", "sick"]},
    {"tags": ["chains", "broken {sub} chains and shackles on the limbs"], "nl": "broken {sub} chains and shackles still on its limbs", "slot": "bindings", "moods": ["dark", "military"]},
    {"tags": ["moss", "moss and small plants growing on the back"], "nl": "moss and small plants growing on its back", "slot": "back", "moods": ["nature", "ruin"]},
    {"tags": ["floating parts", "{sub} armor pieces floating detached around the body"], "nl": "{sub} armor pieces floating detached around the body", "slot": "float", "moods": ["magic", "tech"]},
    {"tags": ["mechanical parts", "one limb replaced by a {sub} mechanical prosthetic"], "nl": "one limb replaced by a {sub} mechanical prosthetic", "slot": "limb", "moods": ["tech"]},
    {"tags": ["mane", "a thick {sub} mane"], "nl": "a thick {sub} mane around the neck", "slot": "neck", "moods": ["wild", "royal"]},
    {"tags": ["collar", "a huge {sub} collar with a {accent} bell"], "nl": "a huge {sub} collar with a {accent} bell", "slot": "neck", "moods": ["cute", "play"]},
    {"tags": ["tail blade", "a tail ending in a {shape}-shaped {sub} blade"], "nl": "a tail ending in a {shape}-shaped {sub} blade", "slot": "tail", "moods": ["military"]},
    {"tags": ["lantern", "a {accent} glowing lantern-like lure hanging from the head"], "nl": "a {accent} glowing lantern-like lure hanging from the head", "slot": "head", "moods": ["night", "water"]},
    {"tags": ["horns", "huge {sub} horns shaped like {shape}s"], "nl": "huge {sub} horns shaped like {shape}s", "slot": "head", "moods": ["wild", "royal"]},
    {"tags": ["crown", "a natural crown of {accent} crystal on the head"], "nl": "a natural crown of {accent} crystal on the head", "slot": "head", "moods": ["royal", "magic"]},
    {"tags": ["scars", "deep old scars across the face"], "nl": "deep old scars across the face", "slot": "face", "moods": ["military", "wild"]},
    {"tags": ["mask", "a {sub} bone mask fused to the face"], "nl": "a {sub} bone mask fused to the face", "slot": "face", "moods": ["dark", "wafu"]},
    {"tags": ["sigil", "a {shape}-shaped {accent} sigil floating above the head"], "nl": "a {shape}-shaped {accent} sigil floating above the head", "slot": "float", "moods": ["magic", "holy"]},
    {"tags": ["ornaments", "{accent} ornaments and bells hung on the horns"], "nl": "{accent} ornaments and bells hung on the horns", "slot": "head", "moods": ["wafu", "royal"]},
    {"tags": ["fur trim", "{sub} fur along the spine and tail"], "nl": "{sub} fur along the spine and tail", "slot": "back", "moods": ["wild", "ice"]},
    {"tags": ["bioluminescent", "{accent} bioluminescent spots that pulse slowly"], "nl": "{accent} bioluminescent spots that pulse slowly", "slot": "markings", "moods": ["water", "night"]},
    {"tags": ["treasure", "gold coins and gems embedded in the {surface}"], "nl": "gold coins and gems embedded in the {surface}", "slot": "markings", "moods": ["royal", "play"]},
]
DETAIL_LEVELS = {0: 0, 1: 1, 2: 2, 3: 4}

LOCO_TAGS = {"quadruped": ["quadruped", "on all fours"], "biped": ["bipedal"], "flying": ["flying", "wings"], "floating": ["floating"], "amorphous": ["amorphous"],
             "serpentine": ["serpentine body", "no legs"], "multi_legged": ["multiple legs"], "rooted": ["rooted"], "aquatic": ["underwater", "swimming"]}
LOCO_NEG = {"quadruped": ["standing on two legs", "bipedal"], "biped": [], "flying": [], "floating": ["legs"], "amorphous": ["limbs", "legs"],
            "serpentine": ["legs", "arms"], "multi_legged": ["two legs"], "rooted": ["walking"], "aquatic": []}
BASE_NEGATIVE = ["humanoid", "human", "1girl", "1boy", "anthro", "furry", "humanoid form", "human face", "human hands", "clothes", "armor on a person"]
SURFACE_JP = {"scales": "鱗", "fur": "毛皮", "stone": "石", "bark": "樹皮", "skin": "皮膚", "gel": "ゲル", "carapace": "甲殻", "feathers": "羽毛", "bones": "骨", "hide": "皮", "petals": "花弁",
              "cap": "傘", "membrane": "膜", "flesh": "肉", "light": "光", "mist": "霧", "element": "元素", "crystal": "結晶", "armor": "装甲", "wood": "木", "shell": "甲羅"}
TYPE_WEIGHTS = {k: (3 if k in ("dragon", "giant_wolf", "slime", "golem", "wyvern", "griffin", "machine_beast", "kraken") else 1) for k in TYPES}

# ---------------------------------------------------------------------------
# 指示文のパース
# ---------------------------------------------------------------------------
@dataclass
class MSpec:
    mtype: Optional[str] = None
    element: Optional[str] = None
    size: Optional[str] = None
    temper: Optional[str] = None
    color: Optional[str] = None
    free_words: List[str] = field(default_factory=list)
    passthrough: List[str] = field(default_factory=list)


def _lookup(tok: str, table: Dict[str, List[str]], shadow) -> List[str]:
    return E._lookup(tok, table, shadow)


def parse_brief(brief: str) -> MSpec:
    spec = MSpec()
    tokens = [t.strip() for t in E._SPLIT_RE.split(brief or "") if t.strip()]
    syn_tables = {"type": {k: v["syn"] for k, v in TYPES.items()}, "element": {k: v["syn"] for k, v in ELEMENTS.items()},
                  "size": {k: v["syn"] for k, v in SIZES.items()}, "temper": {k: v["syn"] for k, v in TEMPERS.items()}}
    all_syns = [s for t in syn_tables.values() for v in t.values() for s in v]
    for tok in tokens:
        shadow = [s for s in all_syns if s in tok]  # 長い同義語が短い同義語を隠す（engine と同じ考え方）
        shadow = [s for s in shadow if not any(s != o and s in o for o in shadow)]
        matched = False
        for key, table in syn_tables.items():
            hits = _lookup(tok, table, shadow)
            if hits:
                if getattr(spec, {"type": "mtype"}.get(key, key)) is None:
                    setattr(spec, {"type": "mtype"}.get(key, key), hits[0])
                matched = True
        if not matched:
            colors = E._lookup(tok, D.COLOR_WORDS)
            if colors:
                spec.color = colors[0]
                matched = True
        if not matched:
            if tok.isascii() and re.fullmatch(r"[A-Za-z][A-Za-z\- ]{1,30}", tok):
                spec.free_words.append(tok.lower())
            else:
                spec.passthrough.append(tok)
    spec.free_words = spec.free_words[:2]
    return spec


def parse_exclude(text: str) -> Dict[str, set]:
    out = {"type": set(), "element": set(), "temper": set()}
    tokens = [t.strip() for t in E._SPLIT_RE.split(text or "") if t.strip()]
    for tok in tokens:
        for key, table in (("type", {k: v["syn"] for k, v in TYPES.items()}), ("element", {k: v["syn"] for k, v in ELEMENTS.items()}), ("temper", {k: v["syn"] for k, v in TEMPERS.items()})):
            for k in E._lookup(tok, table):
                out[key].add(k)
    return out


# ---------------------------------------------------------------------------
# 生成
# ---------------------------------------------------------------------------
@dataclass
class Monster:
    seed: int
    brief: str
    mtype: str
    element: str
    size: str
    temper: str
    palette: Tuple[str, str, str]
    parts: List[str]
    effects: List[str]
    modifiers: List[dict]          # 穴埋め済み {"tags": [...], "nl": ...}
    shape_lang: str
    era: str
    free_words: List[str]
    free_nl: List[str]
    passthrough: List[str]
    concept_jp: str
    concept_en: str
    moods: List[str]
    coherence: str
    detail_level: int
    emphasis: float
    consistency: str
    prompt_style: str
    brief_hits: List[str]

    @property
    def main(self): return self.palette[0]
    @property
    def sub(self): return self.palette[1]
    @property
    def accent(self): return self.palette[2]


def generate(brief: str = "", seed: int = 0, mtype: str = "auto", element: str = "auto", size: str = "auto", temper: str = "auto",
             main_color: str = "auto", exclude: str = "", coherence: str = "normal", detail_level: int = 2, shape_lang: str = "auto",
             era: str = "auto", emphasis: float = 1.6, consistency: str = "strict", prompt_style: str = "tags") -> Monster:
    rng = random.Random(seed)
    spec = parse_brief(brief)
    excluded = parse_exclude(exclude)
    strength = D.COHERENCE_LEVELS.get(coherence, 1.2)
    concept: Dict[str, float] = {}
    brief_hits: List[str] = []

    # 種別
    if mtype in TYPES:
        t_key = mtype
    elif spec.mtype:
        t_key = spec.mtype; brief_hits.append("type")
    else:
        pool = [k for k in TYPES if k not in excluded["type"]] or list(TYPES)
        t_key = rng.choices(pool, weights=[TYPE_WEIGHTS[k] for k in pool], k=1)[0]
    t = TYPES[t_key]
    E._add_moods(concept, t["moods"], 1.5)

    # 属性（種別に合うものを優先）
    if element in ELEMENTS:
        e_key = element
    elif element == "none":
        e_key = ""
    elif spec.element:
        e_key = spec.element; brief_hits.append("element")
    else:
        pref = [e for e in t["elements"] if e not in excluded["element"]]
        others = [e for e in ELEMENTS if e not in excluded["element"] and e not in pref]
        if rng.random() < 0.8 and pref:
            e_key = E._coherent_pick(rng, pref, lambda e: ELEMENTS[e]["moods"], concept, strength)
        else:
            e_key = E._coherent_pick(rng, others or pref, lambda e: ELEMENTS[e]["moods"], concept, strength)
    el = ELEMENTS.get(e_key)
    if el:
        E._add_moods(concept, el["moods"], 1.5)

    # 大きさ（既定の±1段）
    if size in SIZES:
        s_key = size
    elif spec.size:
        s_key = spec.size; brief_hits.append("size")
    else:
        i = SIZE_ORDER.index(t["size"])
        s_key = SIZE_ORDER[max(0, min(len(SIZE_ORDER) - 1, i + rng.choice([-1, 0, 0, 0, 1])))]

    # 気質
    if temper in TEMPERS:
        tp_key = temper
    elif spec.temper:
        tp_key = spec.temper; brief_hits.append("temper")
    else:
        pool = [k for k in TEMPERS if k not in excluded["temper"]] or list(TEMPERS)
        tp_key = E._coherent_pick(rng, pool, lambda k: TEMPERS[k]["moods"], concept, strength)
    E._add_moods(concept, TEMPERS[tp_key]["moods"], 1.0)

    # 配色（3色）: 属性のパレットから。色指定は main を差し替え
    pal_pool = list(el["palettes"]) if el else [("gray", "black", "crimson"), ("brown", "cream", "gold"), ("black", "silver", "sky blue")]
    palette = list(E._pick(rng, pal_pool))
    color_key = main_color if main_color in D.COLOR_JP else (spec.color if spec.color else None)
    if color_key:
        if color_key in palette:
            palette.remove(color_key)
            palette.insert(0, color_key)
        else:
            palette[0] = color_key
        brief_hits.append("color") if spec.color and main_color not in D.COLOR_JP else None
    E._add_moods(concept, D.COLOR_MOOD.get(palette[0]), 0.8)
    palette = tuple(palette)

    # 形状語（自由モチーフ > 属性の模様語 > 種別）
    free_words = spec.free_words
    shape_word = free_words[0] if free_words else {"fire": "flame", "ice": "icicle", "thunder": "lightning-bolt", "water": "wave", "wind": "swirl", "earth": "rune", "poison": "skull",
                                                   "holy": "cross", "dark": "eye", "crystal": "crystal", "metal": "gear", "plant": "leaf", "light": "star", "void": "hexagon"}.get(e_key, "crescent")
    slots = {"main": palette[0], "sub": palette[1], "accent": palette[2], "shape": shape_word, "surface": t["surface"]}

    # 部位（各部位1つ）
    parts = [E._fill(E._pick(rng, opts), slots) for opts in t["parts"].values()]
    # 属性エフェクト（1〜2）
    effects = [E._fill(x, slots) for x in E._sample(rng, el["effects"], 2 if detail_level >= 2 else 1)] if el else []

    # シェイプ言語
    shape_key = shape_lang if shape_lang in D.SHAPES else {"feral": "sharp", "berserk": "sharp", "cunning": "sharp", "majestic": "square", "ancient": "square", "sacred": "round", "playful": "round", "eerie": "sharp"}[tp_key]

    # 世界観
    era_key = era if era in D.ERAS else ("scifi" if t_key in ("machine_beast",) else "fantasy")

    # 体の装飾（装飾量）: コンセプトとの相性で選び、slot は1つまで
    n_mod = DETAIL_LEVELS.get(detail_level, 2)
    used_slots = set(); mods: List[dict] = []
    cands = [m for m in MODIFIERS if not (era_key != "scifi" and "mechanical" in m["tags"][0]) and not (t["surface"] in ("gel", "light", "mist", "element") and m["slot"] in ("armor", "wound", "neck"))]
    mrng = random.Random(seed * 7919 + 31)
    for _ in range(n_mod * 3):
        if len(mods) >= n_mod or not cands:
            break
        m = E._coherent_pick(mrng, [c for c in cands if c["slot"] not in used_slots] or cands, lambda c: c["moods"], concept, strength)
        if m is None or m["slot"] in used_slots:
            continue
        used_slots.add(m["slot"])
        mods.append({"tags": [E._fill(x, slots) for x in m["tags"]], "nl": E._fill(m["nl"], slots)})

    # 自由モチーフ: 模様・角・体の形に混ぜる
    free_nl: List[str] = []
    if free_words:
        frng = random.Random(seed * 104729 + 7)
        tmpl = [("{word}-shaped {accent} markings", "{word}-shaped {accent} markings across the body"), ("{word}-shaped {sub} horns", "{word}-shaped {sub} horns"),
                ("{word}-shaped {accent} core", "a {word}-shaped {accent} glowing core"), ("{word} pattern on the {surface}", "a {word} pattern on the {surface}"),
                ("{word}-shaped tail tip", "a tail tipped with a {word} shape"), ("{word}-shaped {accent} sigil floating above", "a {word}-shaped {accent} sigil floating above it")]
        for w in free_words:
            for tag_t, nl_t in E._sample(frng, tmpl, 2):
                fw = dict(slots, word=w)
                mods.append({"tags": [E._fill(tag_t, fw)], "nl": E._fill(nl_t, fw)})
                free_nl.append(E._fill(nl_t, fw))
        brief_hits.append("free")

    top = sorted(concept.items(), key=lambda kv: -kv[1])
    top_moods = [k for k, _ in top[:2]] if strength > 0 else []
    concept_jp = (D.MOOD_JP[top_moods[0]] + t["jp"]) if top_moods else t["jp"]
    concept_en = f"the {t['jp']} of {D.MOOD_EN[top_moods[0]]}" if top_moods else t["jp"]
    concept_en = concept_en.replace(t["jp"], t["tags"][0])

    return Monster(seed=seed, brief=brief, mtype=t_key, element=e_key, size=s_key, temper=tp_key, palette=palette, parts=parts, effects=effects,
                   modifiers=mods, shape_lang=shape_key, era=era_key, free_words=free_words, free_nl=free_nl, passthrough=spec.passthrough,
                   concept_jp=concept_jp, concept_en=concept_en, moods=top_moods, coherence=coherence, detail_level=detail_level, emphasis=emphasis,
                   consistency=consistency, prompt_style=prompt_style, brief_hits=brief_hits)


# ---------------------------------------------------------------------------
# 出力
# ---------------------------------------------------------------------------
def _w(tag: str, m: Monster, scale: float = 1.0) -> str:
    return E._w(tag, round(m.emphasis * scale, 2)) if m.consistency == "strict" else tag


def _sentences(m: Monster) -> List[str]:
    t = TYPES[m.mtype]; el = ELEMENTS.get(m.element)
    out = []
    if m.moods and m.coherence != "none":
        out.append(f"Concept: {m.concept_en}. Every part of the creature, from its colors to its markings, follows the theme of {' and '.join(D.MOOD_EN[x] for x in m.moods)}.")
    out.append(f"It is {t['kind']}, {SIZES[m.size]['nl']}, with {', '.join(m.parts)}.")
    out.append(f"Its body is {m.main} {t['surface']} with {m.sub} secondary areas and {m.accent} accents; {m.accent} is the glowing color of its eyes and markings. Color ratio: {m.main} about 70%, {m.sub} about 25%, {m.accent} about 5%.")
    if el:
        out.append(f"Its element is {el['jp'] if False else m.element}: {'; '.join(m.effects)}.")
    if m.modifiers:
        out.append("Distinctive details: " + "; ".join(x["nl"] for x in m.modifiers) + ".")
    out.append(D.SHAPES[m.shape_lang]["nl"].capitalize() + ".")
    out.append(f"It is {TEMPERS[m.temper]['nl']}.")
    if m.free_words:
        out.append(f"The whole creature is themed around {' and '.join(m.free_words)}: its horns, markings and body shapes all reference it.")
    return [s for s in out if s]


def build_positive(m: Monster) -> str:
    t = TYPES[m.mtype]; el = ELEMENTS.get(m.element)
    tags: List[str] = ["no humans", "monster"]
    tags.append(_w(t["tags"][0], m))
    tags += t["tags"][1:]
    tags += SIZES[m.size]["tags"]
    tags += LOCO_TAGS[t["loco"]]
    tags.append(_w(f"{m.main} {t['surface']}", m))
    tags.append(f"{m.sub} underside")
    tags.append(_w(f"{m.accent} glowing eyes", m, 0.9))
    if el:
        tags.append(_w(el["tags"][0], m, 0.9))
        tags += el["tags"][1:]
        tags += m.effects
    tags += m.parts
    for x in m.modifiers:
        tags += x["tags"]
    tags += TEMPERS[m.temper]["tags"]
    tags += D.SHAPES[m.shape_lang]["tags"]
    tags += D.ERAS[m.era].get("tags", [])
    tags += m.passthrough
    tags = E._dedupe(tags)
    if m.prompt_style == "natural":
        return " ".join(_sentences(m)) + " Tags: " + ", ".join(tags) + "."
    return ", ".join(tags) + ". " + " ".join(_sentences(m))


def build_negative(m: Monster) -> str:
    t = TYPES[m.mtype]
    neg = list(BASE_NEGATIVE) + list(LOCO_NEG[t["loco"]])
    used = {D.COLOR_BASE.get(c, c) for c in m.palette}
    neg += [f"{c} {t['surface']}" for c in D.ALT_COLORS if c not in used]
    neg += list(D.SHAPES[m.shape_lang]["neg"])
    if "multiple heads" not in t["tags"] and not any("second" in x["nl"] for x in m.modifiers):
        neg.append("multiple heads")
    if t["loco"] != "flying" and "wings" not in " ".join(t["parts"].keys()):
        neg.append("wings")
    neg += ["text", "watermark", "multiple monsters"]
    return ", ".join(E._dedupe(neg))


def build_sheet(m: Monster) -> str:
    t = TYPES[m.mtype]; el = ELEMENTS.get(m.element)
    lines = [
        f"# ====== Random Monster Designer  seed={m.seed} ======",
        f"# brief      : {m.brief or '(なし)'}",
        f"# concept    : 『{m.concept_jp}』 ({m.concept_en})   moods: {', '.join(m.moods) or '-'}   一貫性: {m.coherence}",
        f"# type       : {t['jp']} ({m.mtype})   element: {el['jp'] + ' (' + m.element + ')' if el else '(なし)'}   size: {SIZES[m.size]['jp']} ({m.size})   temper: {TEMPERS[m.temper]['jp']} ({m.temper})",
        f"# palette    : main={m.main}  sub={m.sub}  accent={m.accent}   surface: {SURFACE_JP.get(t['surface'], t['surface'])}",
        f"# parts      : " + " / ".join(m.parts),
        f"# effects    : " + (" / ".join(m.effects) if m.effects else "(なし)"),
        f"# details    : level={m.detail_level}  " + (" / ".join(x['tags'][0] for x in m.modifiers) if m.modifiers else "(なし)"),
        f"# shape      : {D.SHAPES[m.shape_lang]['jp']} ({m.shape_lang})   era: {m.era}   free motif: {', '.join(m.free_words) or '(なし)'}",
        f"# from brief : {', '.join(m.brief_hits) or '(なし)'}   style: {m.prompt_style}   emphasis={m.emphasis}",
        "# ──────── positive ────────",
        build_positive(m),
        "# ──────── negative ────────",
        build_negative(m),
    ]
    return "\n".join(lines)


def build_turnaround(m: Monster) -> str:
    return build_positive(m) + ", creature sheet, multiple views, turnaround, front view, side view, back view, full body, white background, simple background"
