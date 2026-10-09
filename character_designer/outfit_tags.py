"""
服装系統ごとの「正規タグ列」（consistency = strict 用）。

Danbooru 系タグで学習したモデル（Anima / Illustrious / Pony など）は、説明文よりも
既知のタグの方が安定して再現されるため、strict モードでは data.py の説明文テンプレートの
代わりにこのタグ列を使います。

ルール:
  - 各リストの先頭が「主役の服」。engine が重み付けし、別色の同じ服を negative に入れる
  - 色は {main} と {sub} だけを使う（strict では {sub} は {main} に置き換えられ2色構成になる。
    縁の色は engine が "{accent} trim" を1タグだけ追加する）
  - 模様・素材・縁取りの位置などの不安定要素は書かない（シートのメモには data.py の説明文が残る）
  - 固定色が定番のもの（white apron, white veil, black pantyhose 等）はそのまま書く
"""

OUTFIT_TAGS = {
    "succubus": {
        "female": {
            "modest": ["{main} dress", "long sleeves", "{main} elbow gloves", "{main} thighhighs", "{main} boots"],
            "standard": ["{main} leotard", "strapless leotard", "{main} detached sleeves", "{main} thighhighs", "high heels", "{sub} choker"],
            "high": ["{main} leotard", "highleg leotard", "cleavage", "{main} elbow gloves", "{main} thighhighs", "lace-trimmed thighhighs", "garter straps", "high heels", "{sub} collar"],
        },
        "male": {
            "modest": ["{main} jacket", "{sub} shirt", "{main} pants", "dress shoes"],
            "standard": ["{main} open jacket", "bare pectorals", "{main} pants", "boots"],
            "high": ["{main} open vest", "bare pectorals", "{main} shorts", "thigh boots"],
        },
    },
    "sister": {
        "female": {
            "modest": ["{main} habit", "nun", "white veil", "long sleeves", "long skirt", "{main} pantyhose", "{main} footwear", "rosary"],
            "standard": ["{main} habit", "nun", "white veil", "white collar", "{main} thighhighs", "high heels", "rosary"],
            "high": ["{main} habit", "nun", "white veil", "cleavage cutout", "side slit", "{main} thighhighs", "lace-trimmed thighhighs", "garter straps", "{main} elbow gloves", "high heels", "rosary"],
        },
        "male": {
            "modest": ["{main} cassock", "priest", "white collar", "{sub} stole", "dress shoes"],
            "standard": ["{main} cassock", "priest", "white collar", "{sub} stole", "dress shoes"],
            "high": ["{main} cassock", "open clothes", "bare pectorals", "{sub} stole", "boots"],
        },
    },
    "maid": {
        "female": {
            "modest": ["{main} maid dress", "maid", "long sleeves", "white apron", "frilled apron", "maid headdress", "long skirt", "{main} pantyhose", "mary janes"],
            "standard": ["{main} maid dress", "maid", "short sleeves", "white apron", "frilled apron", "maid headdress", "white thighhighs", "mary janes"],
            "high": ["{main} maid dress", "maid", "off-shoulder dress", "cleavage", "miniskirt", "white apron", "maid headdress", "white thighhighs", "lace-trimmed thighhighs", "garter belt", "mary janes", "{sub} choker", "bell"],
        },
        "male": {
            "modest": ["{main} tailcoat", "butler", "white shirt", "{sub} vest", "white gloves", "{main} pants", "dress shoes"],
            "standard": ["{main} tailcoat", "butler", "white shirt", "{sub} vest", "white gloves", "{main} pants", "dress shoes"],
            "high": ["{main} vest", "butler", "open shirt", "bare pectorals", "white gloves", "{main} pants", "dress shoes"],
        },
    },
    "school_uniform": {
        "female": {
            "modest": ["{main} serafuku", "sailor collar", "{sub} neckerchief", "long sleeves", "{main} pleated skirt", "long skirt", "black pantyhose", "loafers", "school bag"],
            "standard": ["{main} blazer", "school uniform", "white shirt", "{sub} ribbon", "{main} pleated skirt", "black kneehighs", "loafers"],
            "high": ["{main} serafuku", "crop top", "sailor collar", "{sub} neckerchief", "midriff", "cleavage", "{main} microskirt", "pleated skirt", "black thighhighs", "loafers", "{sub} choker"],
        },
        "male": {
            "modest": ["{main} gakuran", "school uniform", "{main} pants", "black footwear", "school bag"],
            "standard": ["{main} blazer", "school uniform", "white shirt", "{sub} necktie", "{main} pants", "loafers"],
            "high": ["{main} gakuran", "open clothes", "bare pectorals", "{main} pants", "black footwear"],
        },
    },
    "gothic_lolita": {
        "female": {
            "modest": ["{main} dress", "gothic lolita", "lolita fashion", "long sleeves", "puffy sleeves", "high collar", "lace trim", "bonnet", "{main} lace gloves", "{main} pantyhose", "platform footwear", "mary janes"],
            "standard": ["{main} dress", "gothic lolita", "lolita fashion", "puffy short sleeves", "lace trim", "mini top hat", "{main} fingerless gloves", "{main} over-kneehighs", "platform footwear", "mary janes", "{sub} choker"],
            "high": ["{main} dress", "gothic lolita", "corset", "sweetheart neckline", "cleavage", "bare shoulders", "lace trim", "miniskirt", "mini top hat", "{main} elbow gloves", "{main} thighhighs", "lace-trimmed thighhighs", "garter belt", "platform heels", "{sub} choker"],
        },
        "male": {
            "modest": ["{main} coat", "victorian", "{sub} vest", "jabot", "{main} pants", "{main} boots", "top hat"],
            "standard": ["{main} coat", "victorian", "{sub} vest", "jabot", "{main} pants", "{main} boots", "top hat"],
            "high": ["{main} vest", "victorian", "open shirt", "bare pectorals", "{main} pants", "{main} boots"],
        },
    },
    "shrine_miko": {
        "female": {
            "modest": ["white kimono", "miko", "{main} hakama", "long sleeves", "white tabi", "zori", "hair ornament"],
            "standard": ["white kimono", "miko", "detached sleeves", "{main} hakama", "hakama short skirt", "white thighhighs", "zori", "hair ornament"],
            "high": ["white kimono", "miko", "sideless outfit", "cleavage", "detached sleeves", "{main} hakama", "hakama short skirt", "white thighhighs", "zori", "hair ornament"],
        },
        "male": {
            "modest": ["white kariginu", "kannushi", "{main} hakama", "white tabi", "zori", "eboshi"],
            "standard": ["white kariginu", "kannushi", "{main} hakama", "white tabi", "zori", "eboshi"],
            "high": ["white kimono", "open clothes", "bare pectorals", "{main} hakama", "zori"],
        },
    },
    "kimono": {
        "female": {
            "modest": ["{main} furisode", "kimono", "{sub} obi", "long sleeves", "wide sleeves", "kanzashi", "white tabi", "zori"],
            "standard": ["{main} kimono", "short kimono", "{sub} obi", "kanzashi", "white thighhighs", "geta"],
            "high": ["{main} kimono", "off-shoulder kimono", "cleavage", "short kimono", "side slit", "{sub} obi", "kanzashi", "white thighhighs", "geta"],
        },
        "male": {
            "modest": ["{main} kimono", "{main} haori", "{sub} obi", "zori"],
            "standard": ["{main} kimono", "{main} haori", "{sub} obi", "zori"],
            "high": ["{main} kimono", "open kimono", "bare pectorals", "{sub} obi", "geta"],
        },
    },
    "knight": {
        "female": {
            "modest": ["{main} armor", "full armor", "plate armor", "{sub} cape", "{main} gauntlets", "armored boots", "{sub} surcoat"],
            "standard": ["{main} breastplate", "armor", "{sub} tunic", "{sub} cape", "single pauldron", "{main} gauntlets", "armored skirt", "{sub} shorts", "{main} thigh boots"],
            "high": ["{main} bikini armor", "armor", "midriff", "{sub} cape", "single pauldron", "{main} gauntlets", "{main} thigh boots", "{sub} garter belt"],
        },
        "male": {
            "modest": ["{main} armor", "full armor", "plate armor", "{sub} cape", "{main} gauntlets", "armored boots"],
            "standard": ["{main} breastplate", "armor", "{sub} tunic", "{sub} cape", "{main} gauntlets", "armored boots"],
            "high": ["single pauldron", "{main} gauntlets", "bare pectorals", "{sub} cape", "{main} greaves"],
        },
    },
    "witch_robe": {
        "female": {
            "modest": ["{main} robe", "witch", "long sleeves", "high collar", "{main} gloves", "{main} boots"],
            "standard": ["{main} dress", "witch", "layered skirt", "{sub} cape", "{main} thighhighs", "{main} ankle boots"],
            "high": ["{main} dress", "witch", "plunging neckline", "cleavage", "midriff", "miniskirt", "{sub} cape", "{main} thighhighs", "lace-trimmed thighhighs", "garter straps", "{main} boots", "high heels"],
        },
        "male": {
            "modest": ["{main} robe", "wizard", "{main} boots"],
            "standard": ["{main} coat", "wizard", "{sub} shirt", "{main} pants", "{main} boots"],
            "high": ["{main} coat", "wizard", "open clothes", "bare pectorals", "{main} pants", "{main} boots"],
        },
    },
    "nurse": {
        "female": {
            "modest": ["white dress", "nurse", "long sleeves", "white nurse cap", "white pantyhose", "white footwear"],
            "standard": ["{main} dress", "nurse", "short sleeves", "{main} nurse cap", "white thighhighs", "white footwear", "stethoscope"],
            "high": ["{main} dress", "nurse", "unbuttoned dress", "cleavage", "short dress", "{main} nurse cap", "white thighhighs", "lace-trimmed thighhighs", "garter belt", "white high heels", "stethoscope"],
        },
        "male": {
            "modest": ["white coat", "doctor", "{main} scrubs", "stethoscope", "white footwear"],
            "standard": ["white coat", "doctor", "{main} scrubs", "stethoscope", "white footwear"],
            "high": ["white coat", "doctor", "open coat", "bare pectorals", "{main} pants", "stethoscope"],
        },
    },
    "idol": {
        "female": {
            "modest": ["{main} dress", "idol", "frills", "long sleeves", "{sub} hair ribbon", "white thighhighs", "{main} ankle boots", "{sub} wrist cuffs"],
            "standard": ["{main} cropped jacket", "idol", "{sub} corset", "layered skirt", "miniskirt", "frills", "{sub} hair ribbon", "white thighhighs", "{main} ankle boots", "headset"],
            "high": ["{main} bikini top", "idol", "frills", "microskirt", "midriff", "{sub} hair ribbon", "white thighhighs", "lace-trimmed thighhighs", "{main} boots", "high heels", "headset", "{sub} choker"],
        },
        "male": {
            "modest": ["{main} jacket", "idol", "white shirt", "{main} pants", "{main} boots", "headset"],
            "standard": ["{main} jacket", "idol", "white shirt", "{main} pants", "{main} boots", "headset"],
            "high": ["{main} open jacket", "idol", "bare pectorals", "{main} pants", "{main} boots", "headset"],
        },
    },
    "magical_girl": {
        "female": {
            "modest": ["{main} dress", "magical girl", "puffy long sleeves", "{sub} brooch", "layered skirt", "{sub} hair ribbon", "white gloves", "white pantyhose", "{main} boots"],
            "standard": ["{main} dress", "magical girl", "puffy short sleeves", "{sub} brooch", "layered skirt", "miniskirt", "{sub} hair ribbon", "white gloves", "white thighhighs", "{main} boots", "{sub} choker"],
            "high": ["{main} leotard", "magical girl", "highleg leotard", "{sub} brooch", "showgirl skirt", "{sub} hair ribbon", "white elbow gloves", "white thighhighs", "{main} boots", "high heels", "{sub} choker"],
        },
        "male": {
            "modest": ["{main} jacket", "magical boy", "{sub} brooch", "{sub} cape", "white gloves", "{main} pants", "{main} boots"],
            "standard": ["{main} jacket", "magical boy", "{sub} brooch", "{sub} cape", "white gloves", "{main} pants", "{main} boots"],
            "high": ["{main} open jacket", "magical boy", "bare pectorals", "{sub} brooch", "{main} shorts", "white gloves", "{main} boots"],
        },
    },
    "office_lady": {
        "female": {
            "modest": ["{main} pantsuit", "office lady", "white blouse", "{sub} brooch", "{main} pumps", "watch"],
            "standard": ["{main} blazer", "office lady", "white blouse", "{sub} brooch", "{main} pencil skirt", "black pantyhose", "{main} pumps"],
            "high": ["{main} blazer", "office lady", "open clothes", "{sub} bra", "lace bra", "cleavage", "{main} pencil skirt", "microskirt", "black pantyhose", "garter straps", "{main} pumps", "high heels"],
        },
        "male": {
            "modest": ["{main} suit", "white shirt", "{sub} necktie", "dress shoes"],
            "standard": ["{main} suit", "white shirt", "{sub} necktie", "dress shoes"],
            "high": ["{main} suit jacket", "open clothes", "bare pectorals", "loose necktie", "{main} pants", "dress shoes"],
        },
    },
    "casual_street": {
        "female": {
            "modest": ["{main} hoodie", "oversized clothes", "{sub} pleated skirt", "long skirt", "white sneakers", "{main} baseball cap"],
            "standard": ["{main} hoodie", "cropped hoodie", "{sub} denim shorts", "{main} thighhighs", "striped thighhighs", "white sneakers", "{sub} bag"],
            "high": ["{main} crop top", "cleavage", "midriff", "{sub} short shorts", "micro shorts", "{main} thighhighs", "striped thighhighs", "white sneakers", "platform footwear", "{main} open jacket"],
        },
        "male": {
            "modest": ["{main} hoodie", "oversized clothes", "{sub} cargo pants", "white sneakers", "{main} baseball cap"],
            "standard": ["{main} hoodie", "oversized clothes", "{sub} cargo pants", "white sneakers", "{main} baseball cap"],
            "high": ["{main} open jacket", "bare pectorals", "{sub} shorts", "white sneakers"],
        },
    },
    "swimsuit": {
        "female": {
            "modest": ["{main} one-piece swimsuit", "school swimsuit", "white rash guard", "{sub} sandals"],
            "standard": ["{main} bikini", "halterneck bikini", "{sub} sarong", "{sub} sandals", "anklet"],
            "high": ["{main} bikini", "micro bikini", "string bikini", "see-through", "anklet", "{sub} sandals"],
        },
        "male": {
            "modest": ["{main} swim trunks", "white rash guard", "sandals"],
            "standard": ["{main} swim trunks", "open shirt", "sandals"],
            "high": ["{main} swim briefs", "anklet", "sandals"],
        },
    },
    "bunny_girl": {
        "female": {
            "modest": ["{main} leotard", "playboy bunny", "long sleeves", "{sub} bowtie", "{main} rabbit ears", "fake animal ears", "black pantyhose", "{main} high heels", "wrist cuffs"],
            "standard": ["{main} leotard", "playboy bunny", "strapless leotard", "{sub} bowtie", "detached collar", "{main} rabbit ears", "fake animal ears", "black pantyhose", "{main} high heels", "wrist cuffs", "fake tail"],
            "high": ["{main} leotard", "playboy bunny", "highleg leotard", "cleavage", "{sub} bowtie", "detached collar", "{main} rabbit ears", "fake animal ears", "fishnet pantyhose", "{main} high heels", "wrist cuffs", "fake tail"],
        },
        "male": {
            "modest": ["{main} vest", "white shirt", "{sub} bowtie", "{main} rabbit ears", "fake animal ears", "{main} pants", "dress shoes"],
            "standard": ["{main} vest", "white shirt", "{sub} bowtie", "{main} rabbit ears", "fake animal ears", "{main} pants", "dress shoes"],
            "high": ["{main} open vest", "bare pectorals", "{sub} bowtie", "detached collar", "{main} rabbit ears", "fake animal ears", "{main} shorts", "wrist cuffs"],
        },
    },
    "military": {
        "female": {
            "modest": ["{main} military uniform", "military jacket", "double-breasted", "{main} pants", "{main} peaked cap", "black boots", "white gloves"],
            "standard": ["{main} military uniform", "military jacket", "double-breasted", "{main} pencil skirt", "{main} peaked cap", "black boots", "knee boots", "white gloves", "{sub} armband"],
            "high": ["{main} military jacket", "cropped jacket", "open jacket", "{sub} bikini top", "midriff", "{main} microskirt", "{main} peaked cap", "black thigh boots", "garter straps", "white gloves", "{sub} armband"],
        },
        "male": {
            "modest": ["{main} military uniform", "military jacket", "double-breasted", "{main} pants", "{main} peaked cap", "black boots", "white gloves"],
            "standard": ["{main} military uniform", "military jacket", "double-breasted", "{main} pants", "{main} peaked cap", "black boots", "white gloves"],
            "high": ["{main} military jacket", "open jacket", "bare pectorals", "{main} pants", "{main} peaked cap", "black boots"],
        },
    },
    "princess_dress": {
        "female": {
            "modest": ["{main} gown", "ball gown", "princess", "long sleeves", "{sub} tiara", "white elbow gloves", "{main} high heels", "pearl necklace"],
            "standard": ["{main} dress", "princess", "off-shoulder dress", "short sleeves", "layered skirt", "{sub} tiara", "white gloves", "{main} high heels", "pearl necklace"],
            "high": ["{main} dress", "princess", "corset", "sweetheart neckline", "cleavage", "side slit", "{sub} tiara", "white elbow gloves", "{main} high heels", "pearl necklace", "white thighhighs", "lace-trimmed thighhighs"],
        },
        "male": {
            "modest": ["{main} uniform", "prince", "epaulettes", "{sub} sash", "{main} pants", "{main} boots", "{sub} cape"],
            "standard": ["{main} uniform", "prince", "epaulettes", "{sub} sash", "{main} pants", "{main} boots", "{sub} cape"],
            "high": ["{main} open jacket", "prince", "bare pectorals", "{sub} sash", "{main} pants", "{main} boots"],
        },
    },
    "cheongsam": {
        "female": {
            "modest": ["{main} china dress", "long dress", "long sleeves", "{sub} double bun", "{main} flats"],
            "standard": ["{main} china dress", "short sleeves", "side slit", "double bun", "white thighhighs", "{main} high heels"],
            "high": ["{main} china dress", "sleeveless", "short dress", "side slit", "cleavage cutout", "double bun", "black thighhighs", "lace-trimmed thighhighs", "{main} high heels"],
        },
        "male": {
            "modest": ["{main} changshan", "chinese clothes", "{main} pants", "kung fu shoes"],
            "standard": ["{main} changshan", "chinese clothes", "{main} pants", "kung fu shoes"],
            "high": ["{main} chinese clothes", "open clothes", "bare pectorals", "{main} pants"],
        },
    },
    "bodysuit": {
        "female": {
            "modest": ["{main} bodysuit", "plugsuit", "high collar", "{main} gloves", "{main} boots"],
            "standard": ["{main} bodysuit", "skin tight", "{main} gloves", "{main} thigh boots", "{sub} utility belt"],
            "high": ["{main} bodysuit", "skin tight", "cleavage cutout", "cutout", "{main} gloves", "{main} thigh boots", "{sub} utility belt"],
        },
        "male": {
            "modest": ["{main} bodysuit", "plugsuit", "{main} gloves", "{main} boots"],
            "standard": ["{main} bodysuit", "plugsuit", "{main} gloves", "{main} boots"],
            "high": ["{main} bodysuit", "unzipped bodysuit", "bare pectorals", "{main} gloves", "{main} boots"],
        },
    },
    "sportswear": {
        "female": {
            "modest": ["{main} track jacket", "track suit", "{main} track pants", "white sneakers", "towel around neck"],
            "standard": ["{main} cropped jacket", "sportswear", "{main} gym shorts", "white thighhighs", "striped thighhighs", "white sneakers", "{sub} wristband"],
            "high": ["{main} sports bra", "{main} buruma", "midriff", "white thighhighs", "white sneakers", "{sub} wristband", "{main} open jacket"],
        },
        "male": {
            "modest": ["{main} track jacket", "track suit", "{main} track pants", "white sneakers"],
            "standard": ["{main} tank top", "{main} gym shorts", "white sneakers", "{sub} wristband"],
            "high": ["topless male", "{main} open track jacket", "{main} gym shorts", "white sneakers"],
        },
    },
    "pirate": {
        "female": {
            "modest": ["{main} coat", "pirate", "white shirt", "frilled shirt", "{sub} corset", "{main} tricorne", "{main} pants", "{main} boots", "{sub} sash"],
            "standard": ["{main} coat", "pirate", "white off-shoulder shirt", "{sub} corset", "{main} tricorne", "{main} shorts", "{sub} sash", "{main} thigh boots"],
            "high": ["{main} open coat", "pirate", "{sub} bikini top", "midriff", "{main} tricorne", "{main} micro shorts", "{sub} sash", "{main} thigh boots"],
        },
        "male": {
            "modest": ["{main} coat", "pirate", "white shirt", "{main} tricorne", "{main} pants", "{main} boots"],
            "standard": ["{main} coat", "pirate", "open shirt", "{main} tricorne", "{main} pants", "{main} boots"],
            "high": ["{main} open coat", "pirate", "bare pectorals", "{main} tricorne", "{main} pants", "{sub} sash", "{main} boots"],
        },
    },
    "ninja": {
        "female": {
            "modest": ["{main} ninja outfit", "ninja", "{main} arm guards", "{sub} scarf", "{main} boots", "{sub} sash"],
            "standard": ["{main} ninja outfit", "ninja", "sleeveless", "fishnets", "{main} shorts", "{sub} sash", "{main} arm guards", "{sub} scarf", "{main} thigh boots"],
            "high": ["{main} ninja outfit", "ninja", "sideless outfit", "cleavage", "fishnets", "{main} micro shorts", "{sub} sash", "{main} arm guards", "{sub} scarf", "{main} thigh boots"],
        },
        "male": {
            "modest": ["{main} ninja outfit", "ninja", "{main} arm guards", "{sub} scarf", "{main} boots"],
            "standard": ["{main} ninja outfit", "ninja", "sleeveless", "fishnets", "{main} pants", "{sub} sash", "{main} arm guards", "{sub} scarf"],
            "high": ["{main} open vest", "ninja", "fishnets", "bare pectorals", "{main} pants", "{sub} sash", "{main} arm guards", "{sub} scarf"],
        },
    },
    "jester_outfit": {
        "female": {
            "modest": ["{main} jester costume", "jester", "two-tone", "long sleeves", "jester cap", "bells", "{main} pantyhose", "pointy footwear"],
            "standard": ["{main} dress", "jester", "two-tone dress", "puffy short sleeves", "miniskirt", "jester cap", "bells", "mismatched legwear", "thighhighs", "ruffled collar", "pointy footwear"],
            "high": ["{main} leotard", "jester", "two-tone leotard", "highleg leotard", "cleavage", "jester cap", "bells", "mismatched legwear", "thighhighs", "ruffled collar", "high heels"],
        },
        "male": {
            "modest": ["{main} jester costume", "jester", "two-tone", "jester cap", "bells", "pointy footwear"],
            "standard": ["{main} jester costume", "jester", "two-tone", "jester cap", "bells", "pointy footwear"],
            "high": ["{main} open vest", "jester", "bare pectorals", "jester cap", "bells", "{main} pantyhose", "pointy footwear"],
        },
    },
    "loungewear": {
        "female": {
            "modest": [
                ["{main} pajamas", "{main} nightgown", "{main} hoodie, {sub} sweatpants", "{main} yukata, sleepwear"],
                "sleepwear",
                "?sleep mask on head",
                ["{sub} slippers", "barefoot", "{sub} socks"],
                "?hugging pillow",
            ],
            "standard": [
                ["{main} shirt, oversized shirt", "{main} camisole, {sub} shorts, pajama shorts", "{main} nightgown, short nightgown", "{main} sweater, sweater dress"],
                "sleepwear",
                "?sleep mask on head",
                ["{main} thighhighs", "bare legs", "{sub} socks"],
                ["{sub} slippers", "barefoot"],
            ],
            "high": [
                ["{main} negligee, see-through", "{main} babydoll, lace", "{main} dress shirt, open shirt, {sub} lingerie", "{main} camisole, micro shorts"],
                "lingerie",
                "cleavage",
                "?sleep mask on head",
                ["{main} thighhighs, lace-trimmed thighhighs", "bare legs"],
                ["{sub} slippers", "barefoot"],
            ],
        },
        "male": {
            "modest": [["{main} pajamas", "{main} t-shirt, {sub} sweatpants", "{main} yukata, sleepwear"], "?sleep mask on head", ["{sub} slippers", "barefoot"]],
            "standard": [["{main} pajamas", "{main} t-shirt, {sub} sweatpants", "{main} yukata, sleepwear"], "?sleep mask on head", ["{sub} slippers", "barefoot"]],
            "high": [["topless male, {main} pajama pants", "topless male, {main} boxers"], "?sleep mask on head", ["{sub} slippers", "barefoot"]],
        },
    },
    "teacher": {
        "female": {
            "modest": ["{main} cardigan", "teacher", "white blouse", "{sub} brooch", "{main} long skirt", "pleated skirt", "black pantyhose", "{main} flats", "glasses"],
            "standard": ["{main} blouse", "teacher", "{sub} brooch", "{sub} pencil skirt", "black pantyhose", "{main} pumps", "{main} cardigan"],
            "high": ["{main} blouse", "teacher", "unbuttoned shirt", "cleavage", "{sub} brooch", "{sub} pencil skirt", "microskirt", "black pantyhose", "garter straps", "{main} pumps", "{main} cardigan"],
        },
        "male": {
            "modest": ["{main} cardigan", "teacher", "white shirt", "{sub} necktie", "{main} pants", "dress shoes"],
            "standard": ["{main} cardigan", "teacher", "white shirt", "{sub} necktie", "{main} pants", "dress shoes"],
            "high": ["white shirt", "unbuttoned shirt", "bare pectorals", "loose necktie", "{main} cardigan", "{main} pants", "dress shoes"],
        },
    },
    "dancer": {
        "female": {
            "modest": ["{main} dress", "dancer", "long sleeves", "coins", "{sub} veil", "bangle", "{main} flats"],
            "standard": ["{main} harem outfit", "dancer", "{main} harem pants", "midriff", "{sub} veil", "bangle", "barefoot", "anklet"],
            "high": ["{main} bikini top", "harem outfit", "dancer", "{main} harem pants", "see-through", "side slit", "midriff", "{sub} veil", "bangle", "barefoot", "anklet"],
        },
        "male": {
            "modest": ["{main} tunic", "dancer", "{main} harem pants", "bangle"],
            "standard": ["{main} open vest", "dancer", "{main} harem pants", "bangle"],
            "high": ["topless male", "coin necklace", "{main} harem pants", "see-through", "bangle"],
        },
    },
    "delinquent": {
        "female": {
            "modest": ["{main} serafuku", "sukeban", "delinquent", "long skirt", "sailor collar", "{sub} neckerchief", "surgical mask", "mask around neck", "loafers", "chain"],
            "standard": ["{main} serafuku", "delinquent", "open clothes", "{sub} tank top", "sailor collar", "{main} pleated skirt", "black kneehighs", "loafers", "bandaid on cheek", "chain"],
            "high": ["{main} serafuku", "delinquent", "crop top", "open clothes", "{sub} bikini top", "sailor collar", "{main} microskirt", "pleated skirt", "black thighhighs", "loafers", "bandaid on cheek", "chain"],
        },
        "male": {
            "modest": ["{main} gakuran", "delinquent", "open clothes", "{sub} shirt", "{main} baggy pants", "black boots", "bandaid on cheek"],
            "standard": ["{main} gakuran", "delinquent", "open clothes", "{sub} shirt", "{main} baggy pants", "black boots", "bandaid on cheek"],
            "high": ["{main} gakuran", "delinquent", "open clothes", "bare pectorals", "{main} baggy pants", "black boots", "bandaid on cheek"],
        },
    },
    "saint": {
        "female": {
            "modest": ["white robe", "saint", "long sleeves", "wide sleeves", "high collar", "{sub} stole", "white gloves", "circlet", "white footwear"],
            "standard": ["white dress", "saint", "bare shoulders", "layered skirt", "{sub} cape", "white gloves", "circlet", "white thighhighs", "white high heels"],
            "high": ["white dress", "saint", "plunging neckline", "cleavage", "side slit", "{sub} veil", "white elbow gloves", "circlet", "white thighhighs", "lace-trimmed thighhighs", "garter straps", "white high heels"],
        },
        "male": {
            "modest": ["white robe", "priest", "{sub} stole", "white gloves", "white footwear"],
            "standard": ["white robe", "priest", "{sub} stole", "white gloves", "white footwear"],
            "high": ["white robe", "open clothes", "bare pectorals", "{sub} stole", "white footwear"],
        },
    },
    "goddess_dress": {
        "female": {
            "modest": ["{main} toga", "greek clothes", "long dress", "{sub} shawl", "laurel crown", "armlet", "{main} gladiator sandals"],
            "standard": ["{main} toga", "greek clothes", "bare shoulders", "laurel crown", "armlet", "bracelet", "{main} gladiator sandals"],
            "high": ["{main} toga", "greek clothes", "plunging neckline", "cleavage", "side slit", "laurel crown", "armlet", "{main} gladiator sandals", "{sub} shawl"],
        },
        "male": {
            "modest": ["{main} toga", "greek clothes", "laurel crown", "{main} sandals"],
            "standard": ["{main} toga", "greek clothes", "laurel crown", "{main} sandals"],
            "high": ["{main} toga", "bare pectorals", "greek clothes", "laurel crown", "armlet", "{main} sandals"],
        },
    },
    "cow_suit": {
        "female": {
            "modest": ["cow print bodysuit", "cow print", "long sleeves", "cowbell", "cow print thighhighs", "{main} boots"],
            "standard": ["cow print bikini", "cow print", "miniskirt", "cowbell", "cow print thighhighs", "arm warmers", "{main} boots"],
            "high": ["cow print bikini", "micro bikini", "cow print", "cowbell", "cow print thighhighs", "garter straps", "arm warmers", "{main} high heels"],
        },
        "male": {
            "modest": ["cow print vest", "cow print", "white shirt", "cowbell", "{main} pants", "{main} boots"],
            "standard": ["cow print vest", "cow print", "white shirt", "cowbell", "{main} pants", "{main} boots"],
            "high": ["topless male", "cow print shorts", "cow print", "cowbell", "arm warmers"],
        },
    },
    "hero": {
        "female": {
            "modest": ["{main} tunic", "hero", "white shirt", "{sub} cape", "{main} bracer", "{main} pants", "belt", "{main} boots"],
            "standard": ["{main} tunic", "hero", "sleeveless", "{sub} cape", "{main} bracer", "{main} shorts", "belt", "{main} thigh boots", "single pauldron"],
            "high": ["{main} crop top", "hero", "midriff", "cleavage", "{sub} cape", "{main} bracer", "{main} micro shorts", "belt", "{main} thigh boots", "single pauldron"],
        },
        "male": {
            "modest": ["{main} tunic", "hero", "white shirt", "{sub} cape", "{main} bracer", "{main} pants", "belt", "{main} boots"],
            "standard": ["{main} tunic", "hero", "sleeveless", "{sub} cape", "{main} bracer", "{main} pants", "belt", "{main} boots"],
            "high": ["{main} tunic", "open clothes", "bare pectorals", "{sub} cape", "{main} bracer", "{main} pants", "{main} boots"],
        },
    },
    "steampunk": {
        "female": {
            "modest": ["{main} jacket", "steampunk", "victorian", "{sub} corset", "{main} long skirt", "goggles on head", "{main} boots", "lace-up boots", "{sub} gloves"],
            "standard": ["{sub} corset", "steampunk", "white blouse", "{main} skirt", "goggles on head", "{main} thigh boots", "lace-up boots", "{sub} fingerless gloves", "gear hair ornament"],
            "high": ["{sub} corset", "underbust corset", "steampunk", "{sub} lace bra", "cleavage", "{main} microskirt", "goggles on head", "{main} thigh boots", "garter straps", "{sub} fingerless gloves", "gear hair ornament"],
        },
        "male": {
            "modest": ["{main} waistcoat", "steampunk", "white shirt", "goggles on head", "{main} pants", "{main} boots"],
            "standard": ["{main} waistcoat", "steampunk", "white shirt", "goggles on head", "{main} pants", "{main} boots"],
            "high": ["{main} waistcoat", "open clothes", "bare pectorals", "goggles on head", "{main} pants", "{main} boots"],
        },
    },
    "merchant": {
        "female": {
            "modest": ["{main} vest", "merchant", "white shirt", "{sub} apron", "{main} long skirt", "{sub} head scarf", "{main} ankle boots", "coin purse"],
            "standard": ["{main} vest", "merchant", "white off-shoulder shirt", "{sub} apron", "{main} skirt", "{sub} head scarf", "{main} ankle boots", "coin purse", "{sub} satchel"],
            "high": ["{main} vest", "merchant", "{sub} bikini top", "cleavage", "{sub} apron", "{main} microskirt", "{sub} head scarf", "{main} thigh boots", "coin purse"],
        },
        "male": {
            "modest": ["{main} vest", "merchant", "white shirt", "{sub} apron", "{main} pants", "{main} boots", "coin purse"],
            "standard": ["{main} vest", "merchant", "white shirt", "{sub} apron", "{main} pants", "{main} boots", "coin purse"],
            "high": ["{main} open vest", "merchant", "bare pectorals", "{main} pants", "{main} boots", "coin purse"],
        },
    },
    "pontiff": {
        "female": {
            "modest": ["{main} robe", "pope", "mitre", "{sub} stole", "white gloves", "{main} footwear"],
            "standard": ["{main} robe", "pope", "open robe", "{sub} dress", "mitre", "{sub} stole", "white gloves", "{main} thighhighs", "{main} high heels"],
            "high": ["{main} robe", "pope", "open robe", "{sub} bikini top", "cleavage", "mitre", "{sub} stole", "white elbow gloves", "{main} thighhighs", "lace-trimmed thighhighs", "garter straps", "{main} high heels"],
        },
        "male": {
            "modest": ["{main} robe", "pope", "mitre", "{sub} stole", "white gloves", "{main} footwear"],
            "standard": ["{main} robe", "pope", "mitre", "{sub} stole", "white gloves", "{main} footwear"],
            "high": ["{main} robe", "open robe", "bare pectorals", "mitre", "{sub} stole", "{main} pants"],
        },
    },
    "demon_lord": {
        "female": {
            "modest": ["{main} coat", "high collar", "long coat", "{sub} cape", "spiked pauldrons", "{main} gauntlets", "crown", "{main} armored boots"],
            "standard": ["{main} coat", "high collar", "{sub} cape", "spiked pauldrons", "{main} gauntlets", "crown", "{main} thigh boots"],
            "high": ["{main} open coat", "high collar", "{sub} bikini top", "midriff", "cleavage", "{sub} cape", "spiked pauldrons", "{main} gauntlets", "crown", "{main} thigh boots", "garter straps"],
        },
        "male": {
            "modest": ["{main} coat", "high collar", "long coat", "{sub} cape", "spiked pauldrons", "{main} gauntlets", "crown", "{main} armored boots"],
            "standard": ["{main} coat", "high collar", "{sub} cape", "spiked pauldrons", "{main} gauntlets", "crown", "{main} pants", "{main} armored boots"],
            "high": ["{main} open coat", "bare pectorals", "{sub} cape", "spiked pauldrons", "{main} gauntlets", "crown", "{main} pants", "{main} boots"],
        },
    },
    "thief": {
        "female": {
            "modest": ["{main} cloak", "hooded cloak", "hood down", "{main} vest", "{main} pants", "{main} bracer", "{main} boots", "belt pouch"],
            "standard": ["{main} cloak", "hooded cloak", "hood down", "{main} vest", "{sub} shirt", "{main} shorts", "{main} bracer", "{main} thigh boots", "belt pouch", "mask around neck"],
            "high": ["{main} cloak", "hooded cloak", "hood down", "{main} corset", "cleavage", "{main} micro shorts", "{main} bracer", "{main} thigh boots", "belt pouch", "mask around neck"],
        },
        "male": {
            "modest": ["{main} cloak", "hooded cloak", "{main} vest", "{main} pants", "{main} bracer", "{main} boots", "belt pouch"],
            "standard": ["{main} cloak", "hooded cloak", "{main} vest", "{main} pants", "{main} bracer", "{main} boots", "belt pouch"],
            "high": ["{main} cloak", "hooded cloak", "{main} open vest", "bare pectorals", "{main} pants", "{main} bracer", "{main} boots"],
        },
    },
    "archer": {
        "female": {
            "modest": ["{main} tunic", "archer", "long sleeves", "{sub} hooded cloak", "{main} bracer", "{main} pants", "{main} boots", "quiver"],
            "standard": ["{main} tunic", "archer", "sleeveless", "{sub} hooded cloak", "{main} bracer", "{main} shorts", "{main} thigh boots", "quiver"],
            "high": ["{main} crop top", "archer", "midriff", "{sub} hooded cloak", "{main} bracer", "{main} micro shorts", "{main} thigh boots", "quiver"],
        },
        "male": {
            "modest": ["{main} tunic", "archer", "{sub} hooded cloak", "{main} bracer", "{main} pants", "{main} boots", "quiver"],
            "standard": ["{main} tunic", "archer", "{sub} hooded cloak", "{main} bracer", "{main} pants", "{main} boots", "quiver"],
            "high": ["{main} tunic", "open clothes", "bare pectorals", "{sub} hooded cloak", "{main} bracer", "{main} pants", "{main} boots", "quiver"],
        },
    },
    "samurai": {
        "female": {
            "modest": ["{main} kimono", "samurai", "{main} hakama", "{sub} haori", "kote", "white tabi", "zori"],
            "standard": ["{main} kimono", "samurai", "hakama short skirt", "{sub} haori", "kote", "white thighhighs", "zori"],
            "high": ["{main} kimono", "samurai", "open kimono", "sarashi", "hakama short skirt", "{sub} haori", "off shoulder", "kote", "white thighhighs", "zori"],
        },
        "male": {
            "modest": ["{main} kimono", "samurai", "{main} hakama", "{sub} haori", "kote", "white tabi", "zori"],
            "standard": ["{main} kimono", "samurai", "{main} hakama", "{sub} haori", "kote", "white tabi", "zori"],
            "high": ["{main} kimono", "open kimono", "bare pectorals", "{main} hakama", "kote", "zori"],
        },
    },
    "police": {
        "female": {
            "modest": ["{main} police uniform", "police", "policewoman", "long sleeves", "{sub} necktie", "{main} pants", "police hat", "belt", "black footwear"],
            "standard": ["{main} police uniform", "police", "policewoman", "short sleeves", "{sub} necktie", "{main} pencil skirt", "police hat", "belt", "black boots", "white gloves"],
            "high": ["{main} police uniform", "police", "policewoman", "tied shirt", "cleavage", "{main} microskirt", "police hat", "belt", "handcuffs", "black thigh boots", "garter straps", "white gloves"],
        },
        "male": {
            "modest": ["{main} police uniform", "police", "{sub} necktie", "{main} pants", "police hat", "belt", "black footwear"],
            "standard": ["{main} police uniform", "police", "{sub} necktie", "{main} pants", "police hat", "belt", "black footwear"],
            "high": ["{main} police uniform", "open shirt", "bare pectorals", "{main} pants", "police hat", "belt", "black boots"],
        },
    },
    "chef": {
        "female": {
            "modest": ["white jacket", "chef", "double-breasted", "{main} apron", "chef hat", "{main} pants", "{main} footwear"],
            "standard": ["white jacket", "chef", "short sleeves", "{main} apron", "chef hat", "{main} shorts", "white thighhighs", "{main} footwear"],
            "high": ["white jacket", "chef", "open jacket", "{sub} bikini top", "cleavage", "{main} apron", "chef hat", "{main} micro shorts", "white thighhighs", "lace-trimmed thighhighs", "{main} high heels"],
        },
        "male": {
            "modest": ["white jacket", "chef", "double-breasted", "{main} apron", "chef hat", "{main} pants"],
            "standard": ["white jacket", "chef", "double-breasted", "{main} apron", "chef hat", "{main} pants"],
            "high": ["white jacket", "chef", "open jacket", "bare pectorals", "{main} apron", "chef hat", "{main} pants"],
        },
    },
    "cheerleader": {
        "female": {
            "modest": ["{main} shirt", "cheerleader", "long sleeves", "{main} pleated skirt", "white pantyhose", "white sneakers", "{sub} hair ribbon"],
            "standard": ["{main} crop top", "cheerleader", "sleeveless", "midriff", "{main} miniskirt", "pleated skirt", "white thighhighs", "striped thighhighs", "white sneakers", "{sub} hair ribbon", "pom pom (cheerleading)"],
            "high": ["{main} bikini top", "cheerleader", "{main} microskirt", "pleated skirt", "white thighhighs", "white sneakers", "{sub} hair ribbon", "pom pom (cheerleading)"],
        },
        "male": {
            "modest": ["{main} shirt", "cheerleader", "{main} track pants", "white sneakers"],
            "standard": ["{main} shirt", "cheerleader", "{main} track pants", "white sneakers", "{sub} headband"],
            "high": ["topless male", "{main} track pants", "white sneakers", "{sub} headband"],
        },
    },
    "race_queen": {
        "female": {
            "modest": ["{main} racing suit", "race queen", "{main} baseball cap", "white boots"],
            "standard": ["{main} cropped jacket", "race queen", "{main} miniskirt", "{main} baseball cap", "white thigh boots", "{sub} umbrella"],
            "high": ["{main} bikini top", "race queen", "{main} microskirt", "{main} baseball cap", "white thigh boots", "{sub} umbrella", "{sub} arm warmers"],
        },
        "male": {
            "modest": ["{main} racing suit", "{main} baseball cap", "white boots"],
            "standard": ["{main} racing suit", "{main} baseball cap", "white boots"],
            "high": ["{main} open jacket", "bare pectorals", "{main} pants", "{main} baseball cap", "white boots"],
        },
    },
    "western": {
        "female": {
            "modest": ["{main} shirt", "cowboy western", "long sleeves", "{sub} vest", "denim", "jeans", "{main} cowboy hat", "{main} cowboy boots", "{sub} bandana"],
            "standard": ["{main} shirt", "cowboy western", "tied shirt", "{sub} vest", "denim shorts", "{main} cowboy hat", "{main} cowboy boots", "{sub} bandana", "holster"],
            "high": ["{main} crop top", "cowboy western", "tied shirt", "cleavage", "{sub} open vest", "micro shorts", "denim", "{main} cowboy hat", "{main} thigh boots", "{sub} bandana", "thigh holster"],
        },
        "male": {
            "modest": ["{main} shirt", "cowboy western", "{sub} vest", "jeans", "{main} cowboy hat", "{main} cowboy boots", "{sub} bandana"],
            "standard": ["{main} shirt", "cowboy western", "{sub} vest", "jeans", "{main} cowboy hat", "{main} cowboy boots", "{sub} bandana", "holster"],
            "high": ["{sub} open vest", "cowboy western", "bare pectorals", "jeans", "{main} cowboy hat", "{main} cowboy boots", "{sub} bandana", "holster"],
        },
    },
    "waitress": {
        "female": {
            "modest": ["{main} dress", "waitress", "long sleeves", "white collar", "white apron", "frilled apron", "white headdress", "{main} pantyhose", "{main} flats", "{sub} bowtie"],
            "standard": ["{main} dress", "waitress", "short sleeves", "white collar", "white apron", "frilled apron", "white headdress", "white thighhighs", "mary janes", "{sub} bowtie"],
            "high": ["{main} dress", "waitress", "off-shoulder dress", "cleavage", "short dress", "white apron", "frilled apron", "white headdress", "white thighhighs", "lace-trimmed thighhighs", "garter belt", "mary janes", "high heels", "{sub} bowtie"],
        },
        "male": {
            "modest": ["{main} vest", "waiter", "white shirt", "{sub} bowtie", "{sub} apron", "{main} pants", "dress shoes"],
            "standard": ["{main} vest", "waiter", "white shirt", "{sub} bowtie", "{sub} apron", "{main} pants", "dress shoes"],
            "high": ["{main} open vest", "waiter", "bare pectorals", "{sub} bowtie", "{sub} apron", "{main} pants", "dress shoes"],
        },
    },
    "fortune_teller": {
        "female": {
            "modest": ["{main} robe", "fortune teller", "hooded robe", "hood up", "long sleeves", "wide sleeves", "{sub} shawl", "head scarf", "coins", "bangle", "{main} flats"],
            "standard": ["{main} dress", "fortune teller", "off-shoulder dress", "layered skirt", "{sub} shawl", "head scarf", "coins", "bangle", "hoop earrings", "{main} sandals"],
            "high": ["{main} crop top", "fortune teller", "plunging neckline", "cleavage", "{main} long skirt", "see-through skirt", "side slit", "{sub} shawl", "head scarf", "coins", "bangle", "hoop earrings", "{main} sandals"],
        },
        "male": {
            "modest": ["{main} robe", "fortune teller", "hooded robe", "{sub} sash", "rings", "{main} boots"],
            "standard": ["{main} vest", "fortune teller", "{sub} shirt", "head scarf", "rings", "{main} pants", "{main} boots"],
            "high": ["{main} open vest", "fortune teller", "bare pectorals", "head scarf", "rings", "{main} pants", "{main} sandals"],
        },
    },
    "flight_attendant": {
        "female": {
            "modest": ["{main} jacket", "flight attendant", "white blouse", "{sub} scarf", "{main} long skirt", "pencil skirt", "pillbox hat", "black pantyhose", "{main} pumps"],
            "standard": ["{main} jacket", "flight attendant", "white blouse", "{sub} scarf", "{main} pencil skirt", "pillbox hat", "black pantyhose", "{main} pumps", "{sub} gloves"],
            "high": ["{main} jacket", "flight attendant", "open jacket", "{sub} lace bra", "cleavage", "{sub} scarf", "{main} microskirt", "pencil skirt", "pillbox hat", "black pantyhose", "garter straps", "{main} pumps", "high heels", "{sub} gloves"],
        },
        "male": {
            "modest": ["{main} jacket", "pilot", "white shirt", "{sub} necktie", "{main} pants", "peaked cap", "dress shoes"],
            "standard": ["{main} jacket", "pilot", "white shirt", "{sub} necktie", "{main} pants", "peaked cap", "dress shoes"],
            "high": ["{main} open jacket", "pilot", "bare pectorals", "loose necktie", "{main} pants", "peaked cap", "dress shoes"],
        },
    },
}
