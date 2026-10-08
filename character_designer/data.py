"""
Random Character Designer の知識ベース。

人気キャラクターの設計手法を「データ」として持ち、engine.py が組み合わせて
再現性の高いキャラクタープロンプトを組み立てます。

設計原則（engine.py が実際に適用するルール）
  1. 記号化         : モチーフごとの「一目で分かる記号」（角・翼・耳・輪など）を必ず1つ以上入れる
  2. テーマカラー   : main / sub / accent の3色に制限し、縁・裏地・小物の色まで accent で固定する
  3. 性格の外見化   : 目の形（ツリ目/タレ目/伏し目）、髪型、表情、ポーズ、小物で性格を伝える
  4. ギャップ設計   : モチーフ × 意外な職業/性格 を組み合わせて印象に残す（twist=surprise）
  5. シグネチャ小物 : その子だけの持ち物を1つ決めて固定する
  6. 模様は1種類    : 服の模様は1種類（{pattern}）だけを使い、配置場所も明記してブレを抑える
  7. 細部の固定     : 素材・縁取り色・留め具・丈・レッグウェア・靴まで文章で指定する

テンプレート文字列の置換キー:
  {main} {sub} {accent}  … テーマカラー3色
  {pattern}              … モチーフ由来の模様（1種類のみ）
  {material}             … 服装系統由来の素材
"""

# ---------------------------------------------------------------------------
# 色まわり
# ---------------------------------------------------------------------------

# 指示文の色ワード -> プロンプト用の色名（テーマカラー main を上書きする）
COLOR_WORDS = {
    "black": ["黒", "ブラック", "black"],
    "white": ["白", "ホワイト", "white"],
    "crimson": ["赤", "紅", "レッド", "red", "crimson"],
    "royal blue": ["青", "ブルー", "blue"],
    "navy": ["紺", "ネイビー", "navy"],
    "sky blue": ["水色", "空色", "ライトブルー", "sky blue", "light blue"],
    "teal": ["青緑", "ティール", "teal", "turquoise"],
    "emerald green": ["緑", "グリーン", "翠", "green"],
    "mint": ["ミント", "mint"],
    "gold": ["金", "ゴールド", "gold"],
    "silver": ["銀", "シルバー", "silver"],
    "pastel pink": ["ピンク", "桃", "pink"],
    "hot pink": ["ショッキングピンク", "ホットピンク", "hot pink", "magenta"],
    "purple": ["紫", "パープル", "purple", "violet"],
    "lavender": ["ラベンダー", "薄紫", "lavender"],
    "orange": ["オレンジ", "橙", "orange"],
    "yellow": ["黄", "イエロー", "yellow"],
    "brown": ["茶", "ブラウン", "brown"],
    "cream": ["クリーム", "アイボリー", "cream", "ivory"],
    "wine red": ["ワインレッド", "ボルドー", "wine red", "bordeaux", "burgundy"],
    "gray": ["灰", "グレー", "gray", "grey"],
}

# テーマカラー -> 髪色タグ（「髪か瞳にテーマカラーを乗せる」ルール用）
COLOR_TO_HAIR = {
    "black": "black hair", "white": "white hair", "crimson": "red hair",
    "royal blue": "blue hair", "navy": "dark blue hair", "sky blue": "light blue hair",
    "teal": "teal hair", "emerald green": "green hair", "mint": "mint green hair",
    "gold": "blonde hair", "silver": "silver hair", "pastel pink": "pink hair",
    "hot pink": "hot pink hair", "purple": "purple hair", "lavender": "lavender hair",
    "orange": "orange hair", "yellow": "blonde hair", "brown": "brown hair",
    "cream": "platinum blonde hair", "wine red": "dark red hair", "gray": "gray hair",
    "dark purple": "dark purple hair", "scarlet": "red hair", "olive green": "dark green hair",
}

# テーマカラー -> 瞳色タグ（「瞳はアクセントカラー」ルール用）
COLOR_TO_EYE = {
    "black": "black eyes", "white": "silver eyes", "crimson": "red eyes",
    "royal blue": "blue eyes", "navy": "dark blue eyes", "sky blue": "light blue eyes",
    "teal": "teal eyes", "emerald green": "green eyes", "mint": "mint green eyes",
    "gold": "golden eyes", "silver": "silver eyes", "pastel pink": "pink eyes",
    "hot pink": "magenta eyes", "purple": "purple eyes", "lavender": "lavender eyes",
    "orange": "orange eyes", "yellow": "yellow eyes", "brown": "brown eyes",
    "cream": "amber eyes", "wine red": "dark red eyes", "gray": "gray eyes",
    "dark purple": "violet eyes", "scarlet": "red eyes", "olive green": "green eyes",
}

# main と sub が同色になった時に差し替える「コントラスト色」
CONTRAST_FALLBACK = ["white", "black", "gold", "silver", "crimson", "navy"]

# ---------------------------------------------------------------------------
# 指示文の「特徴ワード」（髪・瞳・体型など、そのままタグになるもの）
# ---------------------------------------------------------------------------

HAIR_COLOR_WORDS = {
    "black hair": ["黒髪", "black hair"],
    "white hair": ["白髪", "白い髪", "white hair"],
    "silver hair": ["銀髪", "silver hair"],
    "blonde hair": ["金髪", "ブロンド", "blonde", "blond hair"],
    "platinum blonde hair": ["プラチナブロンド", "platinum blonde"],
    "red hair": ["赤髪", "赤毛", "red hair"],
    "pink hair": ["ピンク髪", "桃髪", "pink hair"],
    "blue hair": ["青髪", "blue hair"],
    "light blue hair": ["水色髪", "light blue hair"],
    "purple hair": ["紫髪", "purple hair"],
    "green hair": ["緑髪", "green hair"],
    "brown hair": ["茶髪", "brown hair"],
    "orange hair": ["オレンジ髪", "orange hair"],
    "gradient hair": ["グラデ髪", "グラデーション", "gradient hair"],
}

EYE_COLOR_WORDS = {
    "red eyes": ["赤目", "赤い目", "赤瞳", "red eyes"],
    "blue eyes": ["青目", "青い目", "碧眼", "blue eyes"],
    "golden eyes": ["金目", "金眼", "golden eyes", "yellow eyes"],
    "green eyes": ["緑目", "翠眼", "green eyes"],
    "purple eyes": ["紫目", "紫眼", "purple eyes"],
    "pink eyes": ["ピンク目", "pink eyes"],
    "black eyes": ["黒目", "black eyes"],
    "heterochromia": ["オッドアイ", "heterochromia", "odd eyes"],
}

HAIR_STYLE_WORDS = {
    "long hair": ["ロング", "長髪", "long hair"],
    "short hair": ["ショート", "短髪", "short hair"],
    "bob cut": ["ボブ", "bob"],
    "twintails": ["ツインテール", "ツインテ", "twintails"],
    "ponytail": ["ポニーテール", "ポニテ", "ponytail"],
    "side ponytail": ["サイドテール", "side ponytail"],
    "braid": ["三つ編み", "編み込み", "braid"],
    "hair bun": ["お団子", "団子", "hair bun"],
    "drill hair": ["ドリル", "縦ロール", "drill hair"],
    "hime cut": ["姫カット", "hime cut"],
    "wavy hair": ["ウェーブ", "wavy"],
    "ahoge": ["アホ毛", "ahoge"],
}

# 体型・年齢感・その他（タグをそのまま追加。female_only は男性キャラでは無視）
TRAIT_WORDS = {
    "petite": {"syn": ["ロリ", "幼女", "小柄", "ちび", "petite", "loli"], "female_only": False},
    "tall": {"syn": ["長身", "高身長", "tall"], "female_only": False},
    "mature female": {"syn": ["熟女", "人妻", "mature"], "female_only": True},
    "large breasts": {"syn": ["巨乳", "爆乳", "大きい胸", "large breasts", "busty"], "female_only": True},
    "small breasts": {"syn": ["貧乳", "ちっぱい", "小さい胸", "small breasts", "flat chest"], "female_only": True},
    "muscular": {"syn": ["筋肉", "マッチョ", "muscular"], "female_only": False},
    "slender": {"syn": ["スレンダー", "細身", "slender", "slim"], "female_only": False},
    "dark skin": {"syn": ["褐色", "黒肌", "dark skin", "tan"], "female_only": False},
    "glasses": {"syn": ["眼鏡", "メガネ", "めがね", "glasses"], "female_only": False},
    "fang": {"syn": ["八重歯", "fang"], "female_only": False},
    "mole under eye": {"syn": ["泣きぼくろ", "ほくろ", "mole"], "female_only": False},
    "freckles": {"syn": ["そばかす", "freckles"], "female_only": False},
    "elf ears": {"syn": ["エルフ", "elf"], "female_only": False},
}

GENDER_WORDS = {
    "girl": ["女の子", "女子", "少女", "女性", "娘", "ガール", "girl", "female", "woman", "1girl"],
    "boy": ["男の子", "男子", "少年", "男性", "ボーイ", "boy", "male", "man", "1boy"],
}

EXPOSURE_WORDS = {
    "high": ["高露出", "露出高", "露出多", "露出度高", "セクシー", "エロ", "sexy", "revealing", "skimpy"],
    "modest": ["低露出", "露出少", "露出控えめ", "控えめ", "露出なし", "modest", "conservative"],
    "standard": ["普通の露出", "standard exposure"],
}

# ---------------------------------------------------------------------------
# 性格アーキタイプ（性格 → 外見への翻訳表）
# ---------------------------------------------------------------------------
# eyes            : 目の形（性格を最も直接的に伝える要素）
# hair_styles     : 髪型（長さを含む完全な表現）
# hair_colors     : 似合う髪色の候補
# palettes        : (main, sub, accent) の候補
# expression/pose : デフォルト表情・ポーズ
# body            : 体型タグ（空ならランダム）
# accessories     : 性格を示す小物（1〜2個選ばれる）
# footwear        : 指定時は服装系統の靴をこれで置き換える（地雷系の厚底など）
# design_jp       : シートに書き出す「性格→外見」の設計メモ

ARCHETYPES = {
    "tsundere": {
        "jp": "ツンデレ",
        "syn": ["ツンデレ", "つんでれ", "tsundere"],
        "design_jp": "ツリ目＋腕組み＋赤面で「強がり」を一目で伝える。動きのあるツインテ系、暖色の勝ち気カラー",
        "eyes": ["tsurime", "sharp upturned eyes"],
        "hair_styles": ["long twintails", "drill twintails", "high side ponytail", "long hair with twin ribbons"],
        "hair_colors": ["blonde hair", "red hair", "orange hair", "pink hair"],
        "palettes": [("crimson", "white", "gold"), ("scarlet", "black", "gold"), ("orange", "white", "navy")],
        "expression": ["pouting with light blush", "annoyed blush, looking away", "smug smirk with faint blush"],
        "pose": ["arms crossed", "hands on hips", "pointing at viewer"],
        "body": [],
        "accessories": ["twin {accent} hair ribbons", "{accent} ribbon choker"],
        "footwear": None,
    },
    "amaama": {
        "jp": "甘々",
        "syn": ["甘々", "あまあま", "甘えん坊", "デレデレ", "甘やかし", "sweet", "clingy", "deredere"],
        "design_jp": "タレ目＋ふわふわ髪＋パステルで「やさしさ」を表現。ハートとリボンで甘さを記号化",
        "eyes": ["tareme", "soft droopy eyes", "gentle half-closed eyes"],
        "hair_styles": ["long fluffy wavy hair", "low twintails with ribbons", "medium wavy hair with a side braid"],
        "hair_colors": ["pink hair", "platinum blonde hair", "light brown hair", "lavender hair"],
        "palettes": [("pastel pink", "white", "gold"), ("cream", "pastel pink", "crimson"), ("lavender", "white", "pastel pink")],
        "expression": ["gentle loving smile", "blushing smile, half-closed eyes", "happy smile with closed eyes"],
        "pose": ["leaning toward viewer", "hands clasped in front of chest", "hugging own arm"],
        "body": [],
        "accessories": ["{accent} heart-shaped hair clip", "{sub} ribbon choker with {accent} heart charm"],
        "footwear": None,
    },
    "mesugaki": {
        "jp": "メスガキ",
        "syn": ["メスガキ", "めすがき", "生意気", "小悪魔", "mesugaki", "bratty", "brat"],
        "design_jp": "小柄＋八重歯＋ニヤニヤ顔＋見下ろし視線。派手色の組み合わせで「生意気」を記号化",
        "eyes": ["smug half-closed eyes", "jitome with a smug look", "sharp eyes"],
        "hair_styles": ["short twintails", "side ponytail", "twin hair buns with loose strands", "short bob with a side tail"],
        "hair_colors": ["pink hair", "blonde hair", "light blue hair", "white hair"],
        "palettes": [("hot pink", "black", "white"), ("black", "hot pink", "yellow"), ("white", "hot pink", "sky blue")],
        "expression": ["smug grin showing a fang", "smug smile, looking down on viewer", "tongue out, teasing grin"],
        "pose": ["peace sign near the eye", "hands behind back, leaning forward", "pointing and laughing"],
        "body": ["petite", "small build"],
        "accessories": ["{accent} heart-shaped hair clip", "{accent} star-shaped earring", "fang"],
        "footwear": None,
    },
    "seiso": {
        "jp": "清楚系",
        "syn": ["清楚", "せいそ", "お淑やか", "大和撫子", "seiso", "pure", "modest girl"],
        "design_jp": "黒髪ロング＋白基調＋小物は最小限で清潔感。伏し目がちな穏やかな表情",
        "eyes": ["gentle eyes", "soft downcast eyes", "calm tareme"],
        "hair_styles": ["long straight hair with hime cut", "long straight hair", "low ponytail with a ribbon", "half-up long hair"],
        "hair_colors": ["black hair", "dark blue hair", "dark brown hair"],
        "palettes": [("white", "navy", "gold"), ("white", "sky blue", "silver"), ("navy", "white", "crimson")],
        "expression": ["serene closed-mouth smile", "gentle smile", "shy soft smile"],
        "pose": ["hands clasped in front", "slight bow", "hand on chest"],
        "body": [],
        "accessories": ["simple {accent} hair ribbon", "small {accent} pendant necklace"],
        "footwear": None,
    },
    "jirai": {
        "jp": "地雷系",
        "syn": ["地雷", "じらい", "ぴえん", "量産型", "病み", "jirai", "menhera"],
        "design_jp": "黒×ピンク＋泣き腫らし風メイク（赤いアイシャドウ・目の下の赤み）＋包帯・ハートで「病み可愛い」を可視化。厚底靴",
        "eyes": ["hollow eyes with heavy red eyeshadow", "tired eyes with under-eye blush", "teary half-closed eyes"],
        "hair_styles": ["low twintails with blunt bangs", "black bob with pink inner color", "long twintails with blunt bangs"],
        "hair_colors": ["black hair", "pink hair", "dark brown hair"],
        "palettes": [("black", "pastel pink", "white"), ("black", "white", "hot pink"), ("dark purple", "pastel pink", "white")],
        "expression": ["empty eyes, slight pout", "tearful eyes, faint smile", "blank stare"],
        "pose": ["hugging own arm", "sitting with knees up", "finger on lips"],
        "body": [],
        "accessories": ["bandaged wrist", "{accent} heart-shaped choker", "{sub} cross earring", "twin {sub} ribbon hair bows"],
        "footwear": "black platform shoes with {accent} ribbons",
    },
    "uchiki": {
        "jp": "内気",
        "syn": ["内気", "うちき", "人見知り", "引っ込み思案", "オドオド", "ダンデレ", "dandere", "shy", "timid"],
        "design_jp": "前髪で目を隠す＋くすみ色＋萌え袖＋うつむき姿勢で内気さを表現",
        "eyes": ["downcast eyes", "eyes partially hidden by long bangs", "nervous eyes"],
        "hair_styles": ["long hair with bangs covering one eye", "twin braids", "messy low ponytail", "long hair hiding the face"],
        "hair_colors": ["dark brown hair", "black hair", "dark blue hair", "lavender hair"],
        "palettes": [("gray", "lavender", "white"), ("navy", "cream", "brown"), ("dark green", "cream", "gold")],
        "expression": ["nervous, slight blush, looking away", "timid smile", "startled expression"],
        "pose": ["hands clasped in front, hunched posture", "holding a book to chest", "peeking from behind the hair"],
        "body": [],
        "accessories": ["oversized sleeves covering the hands", "{accent} hair pin"],
        "footwear": None,
    },
    "kuudere": {
        "jp": "クーデレ",
        "syn": ["クーデレ", "クール", "無表情", "kuudere", "cool", "stoic"],
        "design_jp": "寒色＋直線的な髪＋無表情で冷静さ。装飾は最小限で銀を差し色に",
        "eyes": ["calm half-closed eyes", "sharp calm eyes", "expressionless eyes"],
        "hair_styles": ["long straight hair", "short bob with straight bangs", "long straight hair with a single side braid"],
        "hair_colors": ["silver hair", "white hair", "light blue hair", "black hair"],
        "palettes": [("navy", "white", "silver"), ("black", "sky blue", "silver"), ("white", "royal blue", "silver")],
        "expression": ["expressionless", "slight sideways glance", "cold stare"],
        "pose": ["standing straight, hands at sides", "arms folded loosely", "hand on own cheek"],
        "body": [],
        "accessories": ["minimal {accent} stud earring", "thin {accent} hair clip"],
        "footwear": None,
    },
    "yandere": {
        "jp": "ヤンデレ",
        "syn": ["ヤンデレ", "やんでれ", "yandere"],
        "design_jp": "可憐で整った外見に「光のない目」を乗せるギャップ設計。白×血の赤",
        "eyes": ["wide eyes with shrunken pupils", "empty eyes with a sweet gaze", "shadowed eyes with glowing pupils"],
        "hair_styles": ["long straight hair with hime cut", "long hair with a single large ribbon", "low twin braids"],
        "hair_colors": ["black hair", "dark purple hair", "pink hair", "white hair"],
        "palettes": [("white", "crimson", "black"), ("black", "wine red", "white"), ("pastel pink", "crimson", "black")],
        "expression": ["sweet smile with empty eyes", "yandere trance, head tilted", "unsettling gentle smile"],
        "pose": ["hands held to chest", "head tilt", "hands behind back"],
        "body": [],
        "accessories": ["{accent} ribbon choker", "{sub} ribbon in hair"],
        "footwear": None,
    },
    "genki": {
        "jp": "元気っ娘",
        "syn": ["元気", "げんき", "活発", "明るい", "ハイテンション", "genki", "energetic", "cheerful"],
        "design_jp": "アホ毛＋暖色＋動きのあるポーズと大きな口の笑顔で活発さを表現",
        "eyes": ["bright round eyes", "sparkling eyes"],
        "hair_styles": ["short hair with ahoge", "high ponytail", "side ponytail with a scrunchie", "short messy hair"],
        "hair_colors": ["orange hair", "brown hair", "blonde hair", "red hair"],
        "palettes": [("orange", "white", "sky blue"), ("yellow", "navy", "white"), ("crimson", "white", "yellow")],
        "expression": ["big open-mouth smile", "wide grin", "laughing"],
        "pose": ["fist pump", "running pose", "double peace sign"],
        "body": ["slender", "athletic"],
        "accessories": ["{accent} star hair clip", "{sub} sports wristband"],
        "footwear": None,
    },
    "ojousama": {
        "jp": "お嬢様",
        "syn": ["お嬢様", "令嬢", "高飛車", "ヒメデレ", "himedere", "ojousama", "lady", "noble"],
        "design_jp": "縦ロール＋ゴールド＋顎を上げた見下ろし視線で気品と高慢さ。真珠や薔薇の小物",
        "eyes": ["elegant upturned eyes", "confident eyes"],
        "hair_styles": ["vertical drill twintails", "long wavy hair with drill curls", "long wavy hair with a headdress"],
        "hair_colors": ["blonde hair", "platinum blonde hair", "silver hair", "light brown hair"],
        "palettes": [("white", "gold", "royal blue"), ("lavender", "white", "gold"), ("wine red", "gold", "white")],
        "expression": ["confident smile, chin raised", "haughty laugh, hand over mouth", "proud smile"],
        "pose": ["holding a folding fan", "hand on cheek", "one hand on hip, elegant posture"],
        "body": [],
        "accessories": ["{accent} pearl earrings", "{sub} rose hair ornament", "{accent} headdress"],
        "footwear": None,
    },
    "oneesan": {
        "jp": "お姉さん",
        "syn": ["お姉さん", "おねえさん", "年上", "大人の女性", "oneesan", "onee-san", "big sister"],
        "design_jp": "長身＋深い色＋余裕のある微笑みで大人っぽさ。泣きぼくろとイヤリング",
        "eyes": ["relaxed tareme", "relaxed half-closed eyes", "gentle teasing eyes"],
        "hair_styles": ["long wavy hair", "side-swept long hair", "loose low bun with loose strands"],
        "hair_colors": ["black hair", "dark purple hair", "dark red hair", "brown hair"],
        "palettes": [("black", "wine red", "gold"), ("dark purple", "black", "gold"), ("white", "navy", "gold")],
        "expression": ["gentle teasing smile", "seductive smile", "warm smile"],
        "pose": ["hand on hip", "leaning forward slightly", "finger on chin"],
        "body": ["tall", "mature female", "curvy"],
        "accessories": ["mole under eye", "{accent} drop earrings"],
        "footwear": None,
    },
    "gal": {
        "jp": "ギャル",
        "syn": ["ギャル", "ぎゃる", "黒ギャル", "gal", "gyaru"],
        "design_jp": "派手髪＋濃いまつ毛メイク＋小物の量で快活さ。ネイルとブレスレット",
        "eyes": ["sharp eyes with long lashes and makeup", "bright eyes with heavy makeup"],
        "hair_styles": ["long wavy hair", "bleached hair with dark roots, long", "side ponytail with a scrunchie", "long hair with loose curls"],
        "hair_colors": ["blonde hair", "platinum blonde hair", "pink hair", "light brown hair"],
        "palettes": [("hot pink", "black", "gold"), ("white", "pastel pink", "gold"), ("black", "gold", "white")],
        "expression": ["wide grin", "wink", "playful smile"],
        "pose": ["peace sign", "hand on hip", "taking a selfie pose"],
        "body": [],
        "accessories": ["lots of {accent} bracelets", "{accent} nail art", "{sub} scrunchie"],
        "footwear": None,
    },
    "chuuni": {
        "jp": "中二病",
        "syn": ["中二病", "厨二", "中二", "chuunibyou", "chuuni"],
        "design_jp": "眼帯＋黒×赤＋片目を隠す髪と大げさなポーズで中二感。包帯と指なし手袋",
        "eyes": ["one eye hidden by hair", "sharp eyes"],
        "hair_styles": ["long hair covering one eye", "long twintails with one side covering the eye", "short hair with long side bangs"],
        "hair_colors": ["black hair", "dark blue hair", "dark red hair", "white hair"],
        "palettes": [("black", "purple", "crimson"), ("black", "gold", "crimson"), ("navy", "black", "gold")],
        "expression": ["smirk, hand over one eye", "serious dramatic look", "smug smile"],
        "pose": ["dramatic hand pose", "hand over one eye", "outstretched hand toward viewer"],
        "body": [],
        "accessories": ["medical eyepatch", "bandaged arm", "{main} fingerless gloves with {accent} trim"],
        "footwear": None,
    },
    "bokukko": {
        "jp": "ボクっ娘",
        "syn": ["ボクっ娘", "ぼくっこ", "男勝り", "ボーイッシュ", "bokukko", "boyish", "tomboy"],
        "design_jp": "ショートヘア＋スポーティな色＋ポケットに手。中性的で快活なシルエット",
        "eyes": ["slightly sharp eyes", "bright eyes"],
        "hair_styles": ["short hair", "boyish short cut with ahoge", "short messy hair with a cap"],
        "hair_colors": ["brown hair", "black hair", "blonde hair", "orange hair"],
        "palettes": [("navy", "white", "orange"), ("emerald green", "white", "yellow"), ("black", "white", "crimson")],
        "expression": ["grin", "confident smile", "cheeky smile"],
        "pose": ["hands in pockets", "thumbs up", "hand behind head"],
        "body": ["slender", "athletic", "small breasts"],
        "accessories": ["{sub} sports wristband", "{accent} baseball cap"],
        "footwear": None,
    },
    "dojikko": {
        "jp": "ドジっ娘",
        "syn": ["ドジっ娘", "ドジ", "天然", "おっちょこちょい", "dojikko", "clumsy", "airhead"],
        "design_jp": "大きな丸い目＋ハネ毛＋絆創膏。慌てた表情と汗で「ドジ」を可視化",
        "eyes": ["wide round eyes", "tareme"],
        "hair_styles": ["messy medium hair with ahoge", "twin braids with loose strands", "short hair with a cowlick"],
        "hair_colors": ["light brown hair", "pink hair", "blonde hair", "orange hair"],
        "palettes": [("pastel pink", "white", "yellow"), ("cream", "sky blue", "crimson"), ("orange", "white", "gold")],
        "expression": ["flustered, teary eyes", "nervous smile with a sweat drop", "surprised open mouth"],
        "pose": ["tripping forward", "hands up in surprise", "scratching the back of head"],
        "body": [],
        "accessories": ["band-aid on the knee", "{accent} round hair clip", "ahoge"],
        "footwear": None,
    },
    "sadistic": {
        "jp": "ドS・女王様",
        "syn": ["ドS", "どえす", "女王様", "サディスト", "sadistic", "queen", "dominatrix"],
        "design_jp": "冷たい笑み＋見下ろし視線＋黒×赤＋チョーカーと鞭で支配者の記号",
        "eyes": ["sharp eyes with a cold smirk", "narrow eyes looking down on viewer"],
        "hair_styles": ["long straight hair", "high ponytail", "long wavy hair"],
        "hair_colors": ["black hair", "silver hair", "dark red hair", "blonde hair"],
        "palettes": [("black", "crimson", "gold"), ("black", "purple", "silver"), ("wine red", "black", "gold")],
        "expression": ["sadistic smirk, looking down on viewer", "cold smile", "amused smirk"],
        "pose": ["hand on hip, one foot forward", "arms crossed, chin raised", "holding a riding crop"],
        "body": ["tall"],
        "accessories": ["{main} choker with a {accent} ring", "{accent} earrings"],
        "footwear": None,
    },
}

# ---------------------------------------------------------------------------
# モチーフ（テーマ）
# ---------------------------------------------------------------------------
# features_primary  : 必ず入る「一目で分かる記号」の候補（1つ選ぶ）
# features_optional : 追加の記号（0〜2個選ぶ）
# palettes          : (main, sub, accent)
# patterns          : 服に使う模様（1種類だけ選ぶ）
# props             : シグネチャ小物候補
# classic_roles     : 王道の職業/服装系統   gap_roles : 意外性のある組み合わせ
# classic_arch      : 王道の性格            gap_arch  : 意外性のある性格
# hair_colors / eye_colors : モチーフらしい髪・瞳（瞳は特殊な瞳孔表現を含む）
# skin              : 肌の指定（省略時は fair skin）
# classic_jp / gap_jp : シートに書く設計意図

MOTIFS = {
    "demon": {
        "jp": "悪魔",
        "syn": ["悪魔", "デーモン", "デビル", "魔族", "魔物", "サキュバス", "淫魔", "demon", "devil", "succubus", "imp"],
        "features_primary": ["{sub} curved demon horns", "small {main} demon horns with {accent} tips", "{accent} twisted demon horns"],
        "features_optional": ["small bat wings on the back, {main} membrane with {accent} edges", "{main} spade-tipped demon tail with {accent} tip", "slit pupils", "small fangs"],
        "palettes": [("black", "crimson", "gold"), ("dark purple", "black", "hot pink"), ("black", "hot pink", "white"), ("wine red", "black", "silver")],
        "patterns": ["bat-wing motif", "pentagram motif", "heart motif", "flame pattern"],
        "props": ["small trident", "heart-shaped lollipop", "chained pendant with a {accent} gem"],
        "classic_roles": ["succubus", "gothic_lolita", "dancer", "bunny_girl"],
        "gap_roles": ["sister", "shrine_miko", "school_uniform", "nurse", "idol", "maid", "teacher", "magical_girl", "office_lady"],
        "classic_arch": ["mesugaki", "oneesan", "sadistic", "tsundere"],
        "gap_arch": ["seiso", "uchiki", "amaama", "dojikko"],
        "hair_colors": ["black hair", "dark purple hair", "red hair", "pink hair", "white hair"],
        "eye_colors": ["red eyes with slit pupils", "golden eyes with slit pupils", "magenta eyes"],
        "skin": None,
        "classic_jp": "悪魔といえば妖艶な小悪魔——王道の記号（角・翼・尻尾）を外さない",
        "gap_jp": "悪魔なのに{role}——相反する記号で印象に残すギャップ設計",
    },
    "angel": {
        "jp": "天使",
        "syn": ["天使", "エンジェル", "堕天使", "angel", "seraph"],
        "features_primary": ["small white feathered wings", "{accent} glowing halo floating above the head", "large white feathered wings with {accent}-tipped feathers"],
        "features_optional": ["{accent} glowing halo floating above the head", "feathers floating around", "glowing {accent} markings"],
        "palettes": [("white", "gold", "sky blue"), ("white", "cream", "gold"), ("sky blue", "white", "silver"), ("black", "white", "gold")],
        "patterns": ["feather motif", "filigree motif", "cross pattern", "cloud motif"],
        "props": ["small golden harp", "holy book with a {accent} clasp", "glowing {accent} orb"],
        "classic_roles": ["sister", "princess_dress", "magical_girl", "idol"],
        "gap_roles": ["delinquent", "succubus", "military", "pirate", "casual_street", "gothic_lolita", "ninja"],
        "classic_arch": ["seiso", "amaama", "dojikko", "uchiki"],
        "gap_arch": ["mesugaki", "sadistic", "gal", "chuuni"],
        "hair_colors": ["blonde hair", "white hair", "platinum blonde hair", "light blue hair"],
        "eye_colors": ["blue eyes", "golden eyes", "light blue eyes"],
        "skin": None,
        "classic_jp": "天使といえば白×金の清らかさ——翼と光輪の記号を素直に使う",
        "gap_jp": "天使なのに{role}——清らかな記号を崩して印象に残すギャップ設計",
    },
    "vampire": {
        "jp": "吸血鬼",
        "syn": ["吸血鬼", "ヴァンパイア", "バンパイア", "vampire"],
        "features_primary": ["small fangs", "sharp fangs"],
        "features_optional": ["small bat wings on the back", "red eyes with slit pupils", "bat-shaped {accent} hair ornament"],
        "palettes": [("black", "crimson", "gold"), ("wine red", "black", "white"), ("white", "crimson", "black"), ("dark purple", "crimson", "silver")],
        "patterns": ["rose motif", "bat-wing motif", "lace rose pattern", "cross pattern"],
        "props": ["wine glass filled with red liquid", "black lace parasol with {accent} trim", "coffin-shaped bag"],
        "classic_roles": ["gothic_lolita", "princess_dress", "succubus", "dancer"],
        "gap_roles": ["school_uniform", "nurse", "idol", "sportswear", "swimsuit", "teacher"],
        "classic_arch": ["ojousama", "oneesan", "sadistic", "kuudere"],
        "gap_arch": ["dojikko", "genki", "uchiki", "amaama"],
        "hair_colors": ["silver hair", "black hair", "platinum blonde hair", "dark red hair"],
        "eye_colors": ["red eyes", "red eyes with slit pupils", "golden eyes"],
        "skin": "pale skin",
        "classic_jp": "吸血鬼といえば黒×深紅の貴族——牙と青白い肌を記号にする",
        "gap_jp": "吸血鬼なのに{role}——夜の貴族を日常に放り込むギャップ設計",
    },
    "witch": {
        "jp": "魔女",
        "syn": ["魔女", "魔法使い", "魔術師", "ウィッチ", "witch", "wizard", "mage", "sorceress"],
        "features_primary": ["large pointed {main} witch hat with {accent} band and {sub} buckle", "wide-brimmed {main} witch hat with {accent} ribbon"],
        "features_optional": ["glowing {accent} magic circle floating beside", "small familiar (black cat) on the shoulder", "{accent} star-shaped earrings"],
        "palettes": [("black", "purple", "gold"), ("dark purple", "black", "orange"), ("navy", "gold", "white"), ("brown", "cream", "emerald green")],
        "patterns": ["star and moon motif", "rune pattern", "constellation motif", "spiral motif"],
        "props": ["broomstick with {accent} bindings", "staff with a glowing {accent} crystal", "thick grimoire with a {accent} lock", "potion vial on a {accent} chain"],
        "classic_roles": ["witch_robe", "gothic_lolita", "princess_dress"],
        "gap_roles": ["office_lady", "nurse", "sportswear", "idol", "school_uniform", "swimsuit", "military"],
        "classic_arch": ["kuudere", "ojousama", "chuuni", "uchiki"],
        "gap_arch": ["genki", "gal", "mesugaki", "dojikko"],
        "hair_colors": ["purple hair", "black hair", "silver hair", "dark blue hair"],
        "eye_colors": ["purple eyes", "golden eyes", "green eyes"],
        "skin": None,
        "classic_jp": "魔女といえばとんがり帽子と黒×紫——帽子のシルエットを最大の記号にする",
        "gap_jp": "魔女なのに{role}——帽子だけ残して日常に落とし込むギャップ設計",
    },
    "cat": {
        "jp": "猫",
        "syn": ["猫", "ネコ", "ねこ", "猫耳", "キャット", "cat", "neko", "catgirl", "kitten"],
        "features_primary": ["cat ears matching the hair color with {accent} inner fur", "cat ears matching the hair color"],
        "features_optional": ["cat tail matching the hair color with a {accent} ribbon", "slit pupils", "small fang", "{accent} bell collar"],
        "palettes": [("black", "white", "pastel pink"), ("white", "pastel pink", "gold"), ("brown", "cream", "crimson"), ("gray", "white", "royal blue")],
        "patterns": ["paw print motif", "fish motif", "cat silhouette motif", "ribbon motif"],
        "props": ["{accent} bell collar", "fish-shaped plush", "ball of {accent} yarn"],
        "classic_roles": ["maid", "casual_street", "school_uniform", "loungewear", "bunny_girl"],
        "gap_roles": ["knight", "military", "office_lady", "sister", "ninja", "pirate"],
        "classic_arch": ["mesugaki", "amaama", "genki", "kuudere"],
        "gap_arch": ["seiso", "ojousama", "sadistic", "chuuni"],
        "hair_colors": ["black hair", "white hair", "brown hair", "gray hair", "orange hair"],
        "eye_colors": ["golden eyes with slit pupils", "green eyes with slit pupils", "blue eyes with slit pupils", "heterochromia, golden and blue eyes"],
        "skin": None,
        "classic_jp": "猫といえば気まぐれで可愛い——耳と尻尾を髪色と揃えて一体感を出す",
        "gap_jp": "猫なのに{role}——気まぐれな記号と規律的な服装のギャップ設計",
    },
    "fox": {
        "jp": "狐",
        "syn": ["狐", "キツネ", "きつね", "妖狐", "狐耳", "fox", "kitsune"],
        "features_primary": ["fox ears matching the hair color with {accent} inner fur"],
        "features_optional": ["fluffy fox tail matching the hair color with a white tip", "multiple fox tails", "slit pupils", "red whisker markings on the cheeks"],
        "palettes": [("white", "crimson", "gold"), ("orange", "white", "black"), ("black", "gold", "crimson"), ("cream", "crimson", "gold")],
        "patterns": ["flame pattern", "wave pattern", "sakura pattern", "fox silhouette motif"],
        "props": ["fox mask worn on the side of the head", "paper talisman", "paper umbrella in {main} with {accent} rim"],
        "classic_roles": ["shrine_miko", "kimono", "witch_robe"],
        "gap_roles": ["office_lady", "idol", "school_uniform", "nurse", "military", "sportswear"],
        "classic_arch": ["oneesan", "kuudere", "ojousama", "sadistic"],
        "gap_arch": ["dojikko", "uchiki", "genki", "mesugaki"],
        "hair_colors": ["white hair", "blonde hair", "orange hair", "silver hair", "black hair"],
        "eye_colors": ["golden eyes with slit pupils", "red eyes", "amber eyes"],
        "skin": None,
        "classic_jp": "狐といえば和装の妖艶さ——白×紅×金と尻尾で神秘性を出す",
        "gap_jp": "狐なのに{role}——和の妖しさと現代的な服装のギャップ設計",
    },
    "wolf": {
        "jp": "狼",
        "syn": ["狼", "オオカミ", "おおかみ", "人狼", "狼耳", "wolf", "werewolf"],
        "features_primary": ["wolf ears matching the hair color"],
        "features_optional": ["bushy wolf tail matching the hair color", "sharp fangs", "sharp claws", "fur trim on the collar"],
        "palettes": [("gray", "white", "crimson"), ("black", "silver", "sky blue"), ("brown", "cream", "orange"), ("white", "gray", "gold")],
        "patterns": ["claw-mark pattern", "moon motif", "tribal pattern", "fur trim"],
        "props": ["fur-lined cloak", "dog tag necklace", "bone-shaped hair clip"],
        "classic_roles": ["casual_street", "military", "knight", "ninja", "pirate"],
        "gap_roles": ["maid", "sister", "idol", "princess_dress", "loungewear", "nurse"],
        "classic_arch": ["bokukko", "genki", "tsundere", "kuudere"],
        "gap_arch": ["amaama", "uchiki", "seiso", "dojikko"],
        "hair_colors": ["gray hair", "silver hair", "black hair", "brown hair"],
        "eye_colors": ["golden eyes", "amber eyes", "ice blue eyes"],
        "skin": None,
        "classic_jp": "狼といえば野性味——牙と尖った耳、動きやすい服装で活発さを出す",
        "gap_jp": "狼なのに{role}——野性の記号と上品な服装のギャップ設計",
    },
    "rabbit": {
        "jp": "兎",
        "syn": ["兎", "うさぎ", "ウサギ", "兎耳", "ラビット", "rabbit", "bunny", "usagi"],
        "features_primary": ["long rabbit ears matching the hair color with {accent} inner fur", "floppy rabbit ears matching the hair color"],
        "features_optional": ["small fluffy cotton tail", "{accent} ribbon tied on one ear", "slightly buck teeth"],
        "palettes": [("white", "pastel pink", "crimson"), ("black", "white", "hot pink"), ("lavender", "white", "gold"), ("cream", "brown", "crimson")],
        "patterns": ["carrot motif", "moon motif", "polka-dot pattern", "clover motif"],
        "props": ["carrot plush", "pocket watch on a {accent} chain", "mochi-shaped plush"],
        "classic_roles": ["bunny_girl", "idol", "casual_street", "loungewear", "magical_girl"],
        "gap_roles": ["military", "knight", "office_lady", "ninja", "delinquent", "pirate"],
        "classic_arch": ["amaama", "genki", "dojikko", "uchiki"],
        "gap_arch": ["sadistic", "kuudere", "chuuni", "yandere"],
        "hair_colors": ["white hair", "pink hair", "platinum blonde hair", "light brown hair"],
        "eye_colors": ["red eyes", "pink eyes", "blue eyes"],
        "skin": None,
        "classic_jp": "兎といえば小さく可愛らしい——長い耳のシルエットと丸いポーズ",
        "gap_jp": "兎なのに{role}——臆病な記号と強い服装のギャップ設計",
    },
    "dragon": {
        "jp": "竜",
        "syn": ["竜", "龍", "ドラゴン", "竜娘", "竜人", "dragon", "drake", "wyvern"],
        "features_primary": ["{sub} dragon horns with {accent} tips", "large curved {accent} dragon horns"],
        "features_optional": ["long dragon tail with {accent} scales", "small dragon wings with {main} membrane and {accent} claws", "{accent} scale markings on the cheeks", "slit pupils"],
        "palettes": [("black", "gold", "crimson"), ("white", "gold", "sky blue"), ("emerald green", "gold", "black"), ("navy", "silver", "sky blue")],
        "patterns": ["scale pattern", "dragon crest motif", "flame pattern", "eastern cloud pattern"],
        "props": ["glowing {accent} crystal orb", "oversized dragon-claw gauntlet", "pile of gold coins"],
        "classic_roles": ["knight", "cheongsam", "princess_dress", "kimono"],
        "gap_roles": ["office_lady", "school_uniform", "maid", "nurse", "loungewear", "idol"],
        "classic_arch": ["ojousama", "kuudere", "sadistic", "tsundere"],
        "gap_arch": ["dojikko", "amaama", "uchiki", "genki"],
        "hair_colors": ["white hair", "black hair", "silver hair", "blonde hair", "green hair"],
        "eye_colors": ["golden eyes with slit pupils", "red eyes with slit pupils", "green eyes with slit pupils"],
        "skin": None,
        "classic_jp": "竜といえば威厳——大きな角とうろこ模様、金の差し色で格の高さを出す",
        "gap_jp": "竜なのに{role}——最強の記号と日常的な服装のギャップ設計",
    },
    "mermaid": {
        "jp": "人魚",
        "syn": ["人魚", "マーメイド", "mermaid"],
        "features_primary": ["fin-shaped ears with {accent} edges", "{sub} scale markings on the cheeks and shoulders"],
        "features_optional": ["pearl hair ornaments", "small fins on the forearms", "water droplets floating around"],
        "palettes": [("teal", "white", "pastel pink"), ("sky blue", "white", "gold"), ("navy", "teal", "silver"), ("mint", "white", "gold")],
        "patterns": ["scale pattern", "wave pattern", "seashell motif", "bubble motif"],
        "props": ["trident with a {accent} gem", "seashell purse", "pearl necklace"],
        "classic_roles": ["swimsuit", "idol", "princess_dress", "dancer"],
        "gap_roles": ["school_uniform", "office_lady", "knight", "military", "ninja", "teacher"],
        "classic_arch": ["seiso", "amaama", "dojikko", "oneesan"],
        "gap_arch": ["sadistic", "mesugaki", "chuuni", "bokukko"],
        "hair_colors": ["teal hair", "light blue hair", "blonde hair", "pink hair"],
        "eye_colors": ["teal eyes", "light blue eyes", "green eyes"],
        "skin": None,
        "classic_jp": "人魚といえば水の透明感——青緑×白と真珠で清涼感を出す",
        "gap_jp": "人魚なのに{role}——水の記号と陸の服装のギャップ設計",
    },
    "fairy": {
        "jp": "妖精",
        "syn": ["妖精", "フェアリー", "ピクシー", "fairy", "pixie", "sprite"],
        "features_primary": ["translucent insect-like wings with {accent} glow", "small butterfly wings with {sub} and {accent} pattern"],
        "features_optional": ["pointy ears", "{accent} flower hair ornament", "glowing {accent} particles floating around"],
        "palettes": [("mint", "white", "gold"), ("pastel pink", "white", "lavender"), ("emerald green", "cream", "gold"), ("sky blue", "white", "yellow")],
        "patterns": ["leaf motif", "flower pattern", "butterfly motif", "vine motif"],
        "props": ["wand with a {accent} star tip", "flower basket", "acorn-shaped bag"],
        "classic_roles": ["magical_girl", "princess_dress", "idol", "loungewear"],
        "gap_roles": ["military", "office_lady", "gothic_lolita", "knight", "delinquent", "ninja"],
        "classic_arch": ["amaama", "genki", "dojikko", "uchiki"],
        "gap_arch": ["sadistic", "kuudere", "mesugaki", "chuuni"],
        "hair_colors": ["green hair", "pink hair", "blonde hair", "light blue hair", "lavender hair"],
        "eye_colors": ["green eyes", "pink eyes", "golden eyes"],
        "skin": None,
        "classic_jp": "妖精といえば自然と光——葉や花のモチーフと透ける羽で軽やかさを出す",
        "gap_jp": "妖精なのに{role}——軽やかな記号と重い服装のギャップ設計",
    },
    "ghost": {
        "jp": "幽霊",
        "syn": ["幽霊", "ゴースト", "お化け", "亡霊", "ghost", "spirit", "phantom"],
        "features_primary": ["white triangular hitaikakushi headband", "will-o'-the-wisps floating nearby with {accent} glow"],
        "features_optional": ["slightly transparent body", "floating slightly above the ground", "{accent} glowing eyes"],
        "palettes": [("white", "sky blue", "lavender"), ("black", "white", "sky blue"), ("lavender", "white", "silver")],
        "patterns": ["spiral motif", "faded hem pattern", "wisp motif", "moon motif"],
        "props": ["candle with a {accent} flame", "paper lantern", "old pocket mirror"],
        "classic_roles": ["kimono", "gothic_lolita", "school_uniform", "sister"],
        "gap_roles": ["idol", "gal_street", "sportswear", "swimsuit", "office_lady", "nurse"],
        "classic_arch": ["uchiki", "yandere", "kuudere", "seiso"],
        "gap_arch": ["genki", "mesugaki", "gal", "dojikko"],
        "hair_colors": ["white hair", "black hair", "light blue hair", "lavender hair"],
        "eye_colors": ["light blue eyes", "empty gray eyes", "red eyes"],
        "skin": "pale skin",
        "classic_jp": "幽霊といえば白と青白さ——三角頭巾と人魂で一目で分かる記号に",
        "gap_jp": "幽霊なのに{role}——儚い記号と明るい服装のギャップ設計",
    },
    "android": {
        "jp": "アンドロイド",
        "syn": ["ロボ", "ロボット", "アンドロイド", "機械", "サイボーグ", "メカ", "robot", "android", "cyborg", "mecha"],
        "features_primary": ["visible mechanical joints at the elbows and knees", "glowing {accent} circuit lines on the skin", "mechanical headgear with {accent} antenna"],
        "features_optional": ["mechanical ear covers with {accent} lights", "glowing {accent} eyes", "small floating drone companion", "{sub} metal plating on the shoulders"],
        "palettes": [("white", "black", "sky blue"), ("black", "silver", "crimson"), ("gray", "white", "orange"), ("navy", "white", "mint")],
        "patterns": ["circuit pattern", "hexagon pattern", "glowing line pattern", "barcode motif"],
        "props": ["holographic display panel", "cable connector hanging from the neck", "energy core in the chest with {accent} glow"],
        "classic_roles": ["bodysuit", "military", "office_lady", "nurse"],
        "gap_roles": ["maid", "shrine_miko", "kimono", "sister", "idol", "loungewear", "school_uniform"],
        "classic_arch": ["kuudere", "dojikko", "uchiki", "seiso"],
        "gap_arch": ["genki", "gal", "tsundere", "mesugaki"],
        "hair_colors": ["white hair", "silver hair", "light blue hair", "black hair"],
        "eye_colors": ["glowing blue eyes", "glowing red eyes", "glowing green eyes"],
        "skin": None,
        "classic_jp": "アンドロイドといえば無機質——関節や発光ラインで人外感を出し、白×黒に差し色1色",
        "gap_jp": "アンドロイドなのに{role}——無機質な記号と温かい服装のギャップ設計",
    },
    "oni": {
        "jp": "鬼",
        "syn": ["鬼", "おに", "鬼娘", "oni", "ogre"],
        "features_primary": ["single {accent} oni horn on the forehead", "twin {sub} oni horns with {accent} tips"],
        "features_optional": ["small fangs", "oni mask worn on the side of the head", "{sub} tiger-stripe cloth accents"],
        "palettes": [("crimson", "black", "gold"), ("royal blue", "white", "gold"), ("black", "gold", "crimson"), ("white", "crimson", "gold")],
        "patterns": ["tiger-stripe pattern", "eastern cloud pattern", "hemp-leaf pattern", "flame pattern"],
        "props": ["oversized kanabo club", "sake gourd on a {accent} cord", "oni mask"],
        "classic_roles": ["kimono", "shrine_miko", "delinquent", "ninja"],
        "gap_roles": ["school_uniform", "office_lady", "idol", "nurse", "maid", "sister"],
        "classic_arch": ["genki", "bokukko", "tsundere", "oneesan"],
        "gap_arch": ["uchiki", "seiso", "amaama", "dojikko"],
        "hair_colors": ["black hair", "white hair", "red hair", "blue hair"],
        "eye_colors": ["red eyes", "golden eyes", "amber eyes"],
        "skin": None,
        "classic_jp": "鬼といえば力強さ——角と虎柄、紅×黒×金で和の迫力を出す",
        "gap_jp": "鬼なのに{role}——荒々しい記号とおとなしい服装のギャップ設計",
    },
    "reaper": {
        "jp": "死神",
        "syn": ["死神", "しにがみ", "reaper", "grim reaper", "shinigami"],
        "features_primary": ["skull-shaped {accent} hair ornament", "shadowy dark aura around the body"],
        "features_optional": ["{accent} glowing eyes", "small black feathered wings", "chain wrapped around one arm"],
        "palettes": [("black", "white", "crimson"), ("black", "purple", "silver"), ("gray", "black", "sky blue")],
        "patterns": ["skull motif", "bone pattern", "hourglass motif", "chain pattern"],
        "props": ["oversized scythe with a {accent} blade edge", "hourglass with {accent} sand", "black lantern"],
        "classic_roles": ["gothic_lolita", "witch_robe", "school_uniform", "sister"],
        "gap_roles": ["idol", "nurse", "sportswear", "maid", "swimsuit", "loungewear"],
        "classic_arch": ["kuudere", "uchiki", "yandere", "sadistic"],
        "gap_arch": ["genki", "amaama", "dojikko", "gal"],
        "hair_colors": ["black hair", "white hair", "silver hair", "dark purple hair"],
        "eye_colors": ["red eyes", "golden eyes", "glowing purple eyes"],
        "skin": "pale skin",
        "classic_jp": "死神といえば黒と鎌——骸骨モチーフと影のオーラで不吉さを記号化",
        "gap_jp": "死神なのに{role}——不吉な記号と明るい服装のギャップ設計",
    },
    "sheep": {
        "jp": "羊",
        "syn": ["羊", "ひつじ", "ヒツジ", "sheep", "lamb"],
        "features_primary": ["curly {accent} sheep horns", "fluffy wool-like hair with sheep ears"],
        "features_optional": ["sheep ears matching the hair color", "fluffy wool collar", "sleepy expression"],
        "palettes": [("cream", "white", "pastel pink"), ("white", "sky blue", "gold"), ("lavender", "cream", "gold")],
        "patterns": ["cloud motif", "polka-dot pattern", "star pattern", "ribbon motif"],
        "props": ["small pillow", "sleep mask pushed up on the head", "oversized mug"],
        "classic_roles": ["loungewear", "casual_street", "gothic_lolita", "idol"],
        "gap_roles": ["military", "knight", "delinquent", "ninja", "office_lady", "pirate"],
        "classic_arch": ["amaama", "uchiki", "dojikko", "seiso"],
        "gap_arch": ["sadistic", "mesugaki", "chuuni", "bokukko"],
        "hair_colors": ["platinum blonde hair", "white hair", "cream hair", "light brown hair"],
        "eye_colors": ["golden eyes", "brown eyes", "pink eyes"],
        "skin": None,
        "classic_jp": "羊といえばもこもこ——丸いシルエットと柔らかい色で安心感を出す",
        "gap_jp": "羊なのに{role}——のんびりした記号と鋭い服装のギャップ設計",
    },
    "star": {
        "jp": "星",
        "syn": ["星", "宇宙", "スター", "ギャラクシー", "星座", "star", "space", "galaxy", "cosmic"],
        "features_primary": ["star-shaped pupils", "hair with a galaxy gradient and {accent} sparkles"],
        "features_optional": ["small floating stars with {accent} glow", "{accent} star-shaped hair ornament", "constellation markings on the skin"],
        "palettes": [("navy", "gold", "white"), ("dark purple", "sky blue", "gold"), ("black", "silver", "pastel pink")],
        "patterns": ["star pattern", "constellation motif", "crescent moon motif", "planet motif"],
        "props": ["star-tipped wand", "small telescope", "glowing {accent} star charm"],
        "classic_roles": ["magical_girl", "idol", "witch_robe", "princess_dress"],
        "gap_roles": ["school_uniform", "sportswear", "office_lady", "casual_street", "nurse", "knight"],
        "classic_arch": ["genki", "ojousama", "kuudere", "chuuni"],
        "gap_arch": ["uchiki", "jirai", "sadistic", "dojikko"],
        "hair_colors": ["dark blue hair", "purple hair", "silver hair", "blonde hair"],
        "eye_colors": ["golden eyes", "purple eyes", "blue eyes"],
        "skin": None,
        "classic_jp": "星といえばきらめき——紺×金と星の瞳で神秘的な華やかさを出す",
        "gap_jp": "星なのに{role}——夜空の記号と日常の服装のギャップ設計",
    },
    "flower": {
        "jp": "花",
        "syn": ["花", "フラワー", "植物", "薔薇", "桜", "flower", "floral", "rose", "sakura"],
        "features_primary": ["large {accent} flower hair ornament", "crown of {sub} flowers"],
        "features_optional": ["petals floating around", "vine accents wrapped around the arms", "{accent} petal-shaped earrings"],
        "palettes": [("white", "emerald green", "pastel pink"), ("crimson", "emerald green", "gold"), ("pastel pink", "white", "crimson"), ("lavender", "white", "gold")],
        "patterns": ["floral pattern", "leaf motif", "rose motif", "sakura pattern"],
        "props": ["lace parasol with {accent} trim", "flower basket", "single {accent} rose"],
        "classic_roles": ["princess_dress", "kimono", "gothic_lolita", "idol"],
        "gap_roles": ["military", "knight", "delinquent", "bodysuit", "sportswear", "pirate"],
        "classic_arch": ["seiso", "amaama", "ojousama", "oneesan"],
        "gap_arch": ["sadistic", "bokukko", "mesugaki", "chuuni"],
        "hair_colors": ["pink hair", "blonde hair", "green hair", "black hair"],
        "eye_colors": ["green eyes", "pink eyes", "golden eyes"],
        "skin": None,
        "classic_jp": "花といえば華やかさ——1種類の花に絞って髪飾りと模様を統一する",
        "gap_jp": "花なのに{role}——可憐な記号と硬派な服装のギャップ設計",
    },
    "jester": {
        "jp": "道化",
        "syn": ["ピエロ", "道化", "クラウン", "ジョーカー", "clown", "jester", "joker", "harlequin"],
        "features_primary": ["small {accent} teardrop face paint under one eye", "{main} and {sub} jester hat with {accent} bells"],
        "features_optional": ["heterochromia, {main} and {sub} eyes", "painted smile mark on the cheek", "small {accent} bells on the outfit"],
        "palettes": [("purple", "gold", "black"), ("crimson", "white", "black"), ("black", "white", "crimson")],
        "patterns": ["diamond harlequin pattern", "checkered pattern", "playing-card suit motif", "star pattern"],
        "props": ["juggling balls", "fan of playing cards", "mask on a stick"],
        "classic_roles": ["jester_outfit", "gothic_lolita", "idol", "dancer"],
        "gap_roles": ["office_lady", "nurse", "sister", "school_uniform", "military", "teacher"],
        "classic_arch": ["mesugaki", "chuuni", "genki", "sadistic"],
        "gap_arch": ["kuudere", "seiso", "uchiki", "amaama"],
        "hair_colors": ["purple hair", "red hair", "white hair", "black hair"],
        "eye_colors": ["heterochromia, golden and purple eyes", "golden eyes", "red eyes"],
        "skin": None,
        "classic_jp": "道化といえばひし形模様と鈴——左右非対称の配色で不気味な楽しさを出す",
        "gap_jp": "道化なのに{role}——ふざけた記号と真面目な服装のギャップ設計",
    },
    "human": {
        "jp": "人間（モチーフなし）",
        "syn": ["人間", "普通", "ノーマル", "モチーフなし", "human", "normal", "plain"],
        "features_primary": [],
        "features_optional": [],
        "palettes": [("white", "navy", "crimson"), ("black", "white", "gold"), ("pastel pink", "white", "gold"), ("navy", "white", "gold"), ("gray", "black", "sky blue")],
        "patterns": ["ribbon motif", "star accents", "stripe accents", "small floral motif", "checkered pattern"],
        "props": ["tote bag in {main} with {accent} handles", "folding umbrella", "paperback book"],
        "classic_roles": [],  # 空 = 全ての服装系統
        "gap_roles": [],
        "classic_arch": [],
        "gap_arch": [],
        "hair_colors": ["black hair", "brown hair", "blonde hair", "light brown hair"],
        "eye_colors": ["brown eyes", "blue eyes", "green eyes", "golden eyes"],
        "skin": None,
        "classic_jp": "モチーフなし——服装と性格の記号だけでキャラを立てる",
        "gap_jp": "モチーフなし——服装と性格の意外な組み合わせで印象に残す",
    },
}

# 指示文にモチーフ指定が無い時の重み（human をやや高めにして「普通の子」も出す）
MOTIF_WEIGHTS = {k: (3 if k == "human" else 1) for k in MOTIFS}

# ---------------------------------------------------------------------------
# 服装系統（職業・衣装）: 露出3段階 × 女性/男性
# ---------------------------------------------------------------------------
# outfits  : {"modest": [...], "standard": [...], "high": [...]}  女性用
# male     : 同上（無い場合は engine が男性キャラではこの系統を自動選択しない）
# props    : シグネチャ小物候補（モチーフの props と合わせて1つ選ぶ）
# materials: {material} 候補
# palettes : この服装らしい (main, sub, accent)

ROLES = {
    "succubus": {
        "jp": "サキュバス衣装",
        "syn": ["サキュバス衣装", "レオタード", "leotard"],
        "outfits": {
            "modest": [
                "{material} {main} long-sleeved dress with {accent} trim along the collar and cuffs, {sub} {pattern} on the hem",
                "{main} opera gloves with {accent} edge",
                "{main} thigh-high stockings with {accent} top band",
                "{main} heeled boots with {accent} buckles",
            ],
            "standard": [
                "{material} {main} strapless leotard with {accent} piping along every edge and a {sub} {pattern} on the chest",
                "{main} detached sleeves with {accent} trim",
                "{main} thigh-high stockings with {accent} top band",
                "{main} high heels with {accent} ankle strap",
                "{sub} choker with {accent} heart charm",
            ],
            "high": [
                "{material} {main} high-cut bikini-style leotard with {accent} piping and a {sub} heart cutout at the chest",
                "{main} long opera gloves with {accent} edge",
                "{main} thigh-high stockings with {accent} lace tops and garter straps",
                "{main} stiletto heels with {accent} ankle strap",
                "{sub} collar with {accent} chain",
            ],
        },
        "male": {
            "modest": ["{material} {main} tailored jacket with {accent} piping and {sub} {pattern} on the lapels, {sub} shirt", "{main} fitted trousers with {accent} side stripe", "{main} dress shoes"],
            "standard": ["{material} {main} open tailored jacket with {accent} piping and {sub} {pattern} on the lapels, bare chest", "{main} fitted trousers with {accent} side stripe", "{main} boots"],
            "high": ["{material} {main} open vest with {accent} piping, bare chest, {sub} {pattern} on the collar", "{main} fitted shorts with {accent} belt", "{main} thigh-high boots with {accent} buckles"],
        },
        "props": ["heart-shaped lollipop", "small pitchfork"],
        "materials": ["latex", "satin", "velvet"],
        "palettes": [("black", "crimson", "gold"), ("dark purple", "black", "hot pink")],
    },
    "sister": {
        "jp": "シスター",
        "syn": ["シスター", "修道女", "修道服", "聖職者", "nun", "sister", "priestess", "cleric"],
        "outfits": {
            "modest": [
                "{material} {main} full-length nun habit with {accent} edge trim on the hem and cuffs, {sub} {pattern} embroidered on the chest, white collar",
                "{main} veil with {accent} lining",
                "{sub} rosary with {accent} cross",
                "{main} opaque tights",
                "{main} low-heeled shoes",
            ],
            "standard": [
                "{material} {main} knee-length nun habit with {accent} edge trim on the hem and cuffs, {sub} {pattern} embroidered on the chest, white collar",
                "{main} veil with {accent} lining",
                "{sub} rosary with {accent} cross",
                "{main} thigh-high stockings with {accent} top band",
                "{main} heeled shoes",
            ],
            "high": [
                "{material} {main} nun habit with a deep cleavage cutout framed in {accent} trim, high side slits to the hip, {sub} {pattern} embroidered on the chest",
                "{main} veil with {accent} lining",
                "{sub} rosary with {accent} cross",
                "{main} thigh-high stockings with {accent} lace tops and garter straps",
                "{main} heeled pumps",
                "{main} opera gloves with {accent} edge",
            ],
        },
        "male": {
            "modest": ["{material} {main} priest cassock with {accent} piping, {sub} {pattern} embroidered on the chest, white collar", "{sub} stole with {accent} cross", "{main} dress shoes"],
            "standard": ["{material} {main} priest cassock with {accent} piping, {sub} {pattern} embroidered on the chest, white collar", "{sub} stole with {accent} cross", "{main} dress shoes"],
            "high": ["{material} {main} priest cassock open at the chest with {accent} piping, {sub} {pattern} embroidered on the chest", "{sub} stole with {accent} cross", "{main} boots"],
        },
        "props": ["rosary", "holy book", "candle"],
        "materials": ["cotton", "wool", "satin"],
        "palettes": [("black", "white", "gold"), ("white", "navy", "gold"), ("navy", "white", "silver")],
    },
    "maid": {
        "jp": "メイド",
        "syn": ["メイド", "maid", "メイド服"],
        "outfits": {
            "modest": [
                "{material} {main} long-sleeved maid dress with {accent} piping along the collar and cuffs, floor-length skirt, {sub} {pattern} on the hem",
                "white frilled apron with {accent} ribbon at the back",
                "white frilled maid headdress with {accent} ribbon",
                "{main} opaque tights",
                "{main} mary janes with {accent} strap",
            ],
            "standard": [
                "{material} {main} short-sleeved maid dress with {accent} piping along the collar and cuffs, knee-length skirt, {sub} {pattern} on the hem",
                "white frilled apron with {accent} ribbon at the back",
                "white frilled maid headdress with {accent} ribbon",
                "white thigh-high stockings with {accent} top band",
                "{main} mary janes with {accent} strap",
            ],
            "high": [
                "{material} {main} off-shoulder mini maid dress with {accent} piping along the neckline, deep cleavage, {sub} {pattern} on the hem",
                "white frilled apron with {accent} ribbon at the back, barely covering the skirt",
                "white frilled maid headdress with {accent} ribbon",
                "white thigh-high stockings with {accent} lace tops and garter belt",
                "{main} heeled mary janes with {accent} strap",
                "{sub} choker with {accent} bell",
            ],
        },
        "male": {
            "modest": ["{material} {main} butler tailcoat with {accent} piping and {sub} {pattern} on the lapels, white dress shirt, {sub} vest", "white gloves", "{main} trousers with {accent} side stripe", "{main} dress shoes"],
            "standard": ["{material} {main} butler tailcoat with {accent} piping and {sub} {pattern} on the lapels, white dress shirt, {sub} vest", "white gloves", "{main} trousers with {accent} side stripe", "{main} dress shoes"],
            "high": ["{material} {main} butler vest with {accent} piping over an open white shirt, {sub} {pattern} on the collar", "white gloves", "{main} trousers with {accent} side stripe", "{main} dress shoes"],
        },
        "props": ["silver tea tray", "feather duster"],
        "materials": ["cotton", "satin"],
        "palettes": [("black", "white", "crimson"), ("navy", "white", "gold"), ("wine red", "white", "gold"), ("pastel pink", "white", "gold")],
    },
    "school_uniform": {
        "jp": "学生服",
        "syn": ["制服", "学生", "JK", "女子高生", "セーラー服", "セーラー", "ブレザー", "生徒", "school uniform", "schoolgirl", "student", "sailor uniform", "blazer"],
        "outfits": {
            "modest": [
                "{main} long-sleeved sailor uniform with {accent} lines on the collar and cuffs, {sub} neckerchief with {pattern}",
                "{main} pleated skirt below the knee with {accent} hem line",
                "black opaque tights",
                "brown loafers",
                "{sub} school bag",
            ],
            "standard": [
                "{main} blazer with {accent} piping and {sub} {pattern} badge on the breast pocket, white dress shirt, {sub} ribbon tie",
                "{main} pleated skirt above the knee with {accent} hem line",
                "black knee-high socks with {accent} top line",
                "brown loafers",
            ],
            "high": [
                "{main} cropped sailor top with {accent} lines on the collar, {sub} neckerchief with {pattern}, bare midriff, deep neckline",
                "{main} micro pleated skirt with {accent} hem line",
                "black thigh-high stockings with {accent} top band",
                "brown loafers",
                "{sub} ribbon choker",
            ],
        },
        "male": {
            "modest": ["{main} gakuran with {accent} piping, {sub} {pattern} badge on the collar", "{main} slacks", "black leather shoes", "{sub} school bag"],
            "standard": ["{main} blazer with {accent} piping and {sub} {pattern} badge on the breast pocket, white shirt, {sub} necktie", "{main} slacks", "brown loafers"],
            "high": ["{main} gakuran worn open over a bare chest, {accent} piping, {sub} {pattern} badge on the collar", "{main} slacks", "black leather shoes"],
        },
        "props": ["school bag", "bento box", "textbook"],
        "materials": ["wool", "cotton"],
        "palettes": [("navy", "white", "crimson"), ("black", "white", "crimson"), ("gray", "white", "royal blue")],
    },
    "gothic_lolita": {
        "jp": "ゴスロリ",
        "syn": ["ゴスロリ", "ゴシック", "ロリータ", "ゴシックロリータ", "gothic", "lolita", "gothic lolita"],
        "outfits": {
            "modest": [
                "{material} {main} gothic lolita dress with {accent} lace trim on every hem, high collar, long puffed sleeves, {sub} {pattern} on the bodice, floor-length tiered skirt",
                "{main} bonnet with {accent} ribbons",
                "{main} lace gloves",
                "{main} opaque tights with {accent} {pattern}",
                "{main} platform mary janes with {accent} buckles",
            ],
            "standard": [
                "{material} {main} gothic lolita dress with {accent} lace trim on every hem, short puffed sleeves, knee-length tiered skirt, {sub} {pattern} on the bodice",
                "{main} mini top hat with {accent} ribbon",
                "{main} lace fingerless gloves",
                "{main} over-knee socks with {accent} {pattern}",
                "{main} platform mary janes with {accent} buckles",
                "{sub} ribbon choker with {accent} cameo",
            ],
            "high": [
                "{material} {main} gothic lolita corset dress with {accent} lace trim, deep sweetheart neckline, exposed shoulders, {sub} {pattern} on the bodice, mini tiered skirt",
                "{main} mini top hat with {accent} ribbon",
                "{main} lace opera gloves",
                "{main} thigh-high stockings with {accent} lace tops and garter belt",
                "{main} platform heels with {accent} buckles",
                "{sub} ribbon choker with {accent} cameo",
            ],
        },
        "male": {
            "modest": ["{material} {main} victorian frock coat with {accent} embroidery, {sub} vest with {pattern}, white jabot", "{main} trousers", "{main} boots with {accent} buckles", "{main} top hat with {accent} ribbon"],
            "standard": ["{material} {main} victorian frock coat with {accent} embroidery, {sub} vest with {pattern}, white jabot", "{main} trousers", "{main} boots with {accent} buckles", "{main} top hat with {accent} ribbon"],
            "high": ["{material} {main} victorian vest with {accent} embroidery over an open white shirt, {sub} {pattern} on the collar", "{main} trousers", "{main} boots with {accent} buckles"],
        },
        "props": ["black lace parasol with {accent} trim", "antique doll"],
        "materials": ["velvet", "satin", "lace"],
        "palettes": [("black", "white", "crimson"), ("black", "wine red", "gold"), ("dark purple", "black", "silver")],
    },
    "shrine_miko": {
        "jp": "巫女",
        "syn": ["巫女", "神社", "巫女服", "miko", "shrine maiden"],
        "outfits": {
            "modest": [
                "white kimono top with {accent} piping on the collar, long sleeves with {sub} {pattern}",
                "{main} hakama with {accent} cord",
                "white tabi socks",
                "zori sandals",
                "{sub} {pattern} hair ornament",
            ],
            "standard": [
                "white kimono top with detached sleeves tied with {accent} cords, {sub} {pattern} on the sleeves",
                "{main} knee-length hakama with {accent} cord",
                "white thigh-high tabi socks",
                "zori sandals",
                "{sub} {pattern} hair ornament",
            ],
            "high": [
                "white sleeveless kimono top open at the chest with {accent} piping, sideless, detached sleeves with {sub} {pattern}",
                "{main} micro hakama with {accent} cord and side slits",
                "white thigh-high stockings with {accent} top band",
                "zori sandals",
                "{sub} {pattern} hair ornament",
            ],
        },
        "male": {
            "modest": ["white kariginu robe with {accent} collar, {sub} {pattern} on the sleeves", "{main} hakama", "white tabi socks", "zori sandals"],
            "standard": ["white kariginu robe with {accent} collar, {sub} {pattern} on the sleeves", "{main} hakama", "white tabi socks", "zori sandals"],
            "high": ["white kimono top worn open at the chest with {accent} collar, {sub} {pattern} on the sleeves", "{main} hakama", "zori sandals"],
        },
        "props": ["gohei wand", "paper talisman", "bow and arrow"],
        "materials": ["silk"],
        "palettes": [("crimson", "white", "gold"), ("navy", "white", "gold"), ("black", "white", "crimson")],
    },
    "kimono": {
        "jp": "着物",
        "syn": ["着物", "和服", "浴衣", "和風", "振袖", "kimono", "yukata", "japanese clothes"],
        "outfits": {
            "modest": [
                "{material} {main} furisode kimono with {sub} {pattern} across the sleeves and hem, {accent} obi sash with a decorative knot",
                "{sub} {pattern} kanzashi hair ornament",
                "white tabi socks",
                "zori sandals",
                "{accent} obijime cord",
            ],
            "standard": [
                "{material} {main} kimono with {sub} {pattern} on the sleeves and hem, {accent} obi sash, short hem above the knee",
                "{sub} {pattern} kanzashi hair ornament",
                "white thigh-high tabi socks",
                "geta sandals",
                "{accent} obijime cord",
            ],
            "high": [
                "{material} {main} kimono worn off the shoulders exposing the chest, {sub} {pattern} on the sleeves, {accent} obi sash, mini length with high side slits",
                "{sub} {pattern} kanzashi hair ornament",
                "white thigh-high stockings with {accent} top band",
                "geta sandals",
                "{accent} obijime cord",
            ],
        },
        "male": {
            "modest": ["{material} {main} kimono with {sub} {pattern} on the back, {accent} obi sash", "{main} haori jacket", "zori sandals"],
            "standard": ["{material} {main} kimono with {sub} {pattern} on the back, {accent} obi sash", "{main} haori jacket", "zori sandals"],
            "high": ["{material} {main} kimono worn open at the chest with {sub} {pattern} on the back, {accent} obi sash", "geta sandals"],
        },
        "props": ["paper umbrella in {main} with {accent} rim", "folding fan with {pattern}"],
        "materials": ["silk"],
        "palettes": [("crimson", "black", "gold"), ("navy", "white", "gold"), ("white", "pastel pink", "crimson"), ("black", "gold", "crimson")],
    },
    "knight": {
        "jp": "騎士",
        "syn": ["騎士", "ナイト", "聖騎士", "パラディン", "鎧", "甲冑", "knight", "paladin", "armor", "armour"],
        "outfits": {
            "modest": [
                "{main} full plate armor with {accent} engraved edges and {sub} {pattern} emblem on the chestplate",
                "{sub} cape with {accent} lining",
                "{main} armored gauntlets",
                "{main} armored boots",
                "{sub} surcoat with {accent} trim",
            ],
            "standard": [
                "{main} breastplate with {accent} engraved edges and {sub} {pattern} emblem, over a {sub} tunic",
                "{sub} half-cape with {accent} lining",
                "{main} pauldron on one shoulder",
                "{main} gauntlets",
                "{main} armored skirt over {sub} shorts",
                "{main} armored thigh-high boots",
            ],
            "high": [
                "{main} bikini armor with {accent} engraved edges and {sub} {pattern} emblem on the chest, exposed midriff",
                "{sub} half-cape with {accent} lining",
                "{main} pauldron on one shoulder",
                "{main} gauntlets",
                "{main} armored thigh-high boots",
                "{sub} garter belt with {accent} buckle",
            ],
        },
        "male": {
            "modest": ["{main} full plate armor with {accent} engraved edges and {sub} {pattern} emblem on the chestplate", "{sub} cape with {accent} lining", "{main} armored gauntlets", "{main} armored boots"],
            "standard": ["{main} breastplate with {accent} engraved edges and {sub} {pattern} emblem over a {sub} tunic", "{sub} half-cape with {accent} lining", "{main} gauntlets", "{main} armored boots"],
            "high": ["{main} pauldron and {main} gauntlets with {accent} engraved edges, bare chest with a {sub} {pattern} tattoo", "{sub} half-cape with {accent} lining", "{main} armored greaves"],
        },
        "props": ["longsword with {accent} hilt", "kite shield with {pattern}", "lance"],
        "materials": ["steel"],
        "palettes": [("silver", "white", "gold"), ("black", "crimson", "gold"), ("white", "royal blue", "gold"), ("gold", "white", "crimson")],
    },
    "witch_robe": {
        "jp": "魔女服",
        "syn": ["魔女服", "ローブ", "robe", "witch outfit"],
        "outfits": {
            "modest": [
                "{material} {main} full-length witch robe with {accent} trim on the hem and cuffs, {sub} {pattern} embroidered on the chest, high collar",
                "{main} gloves with {accent} trim",
                "{main} boots with {accent} buckles",
            ],
            "standard": [
                "{material} {main} witch dress with {accent} trim, knee-length layered skirt, {sub} {pattern} on the hem",
                "{sub} short cape with {accent} clasp",
                "{main} thigh-high socks with {accent} top band",
                "{main} ankle boots with {accent} buckles",
            ],
            "high": [
                "{material} {main} witch outfit with a deep plunging neckline framed in {accent} trim, mini skirt with {sub} {pattern}, exposed midriff",
                "{sub} short cape with {accent} clasp",
                "{main} thigh-high stockings with {accent} lace tops and garter straps",
                "{main} heeled boots with {accent} buckles",
            ],
        },
        "male": {
            "modest": ["{material} {main} wizard robe with {accent} trim, {sub} {pattern} embroidered on the chest", "{main} boots"],
            "standard": ["{material} {main} wizard coat with {accent} trim, {sub} {pattern} embroidered on the chest, {sub} shirt", "{main} trousers", "{main} boots"],
            "high": ["{material} {main} open wizard coat with {accent} trim over a bare chest, {sub} {pattern} on the collar", "{main} trousers", "{main} boots"],
        },
        "props": ["broomstick", "crystal-tipped staff", "grimoire"],
        "materials": ["velvet", "wool"],
        "palettes": [("black", "purple", "gold"), ("navy", "gold", "white"), ("dark purple", "black", "orange")],
    },
    "nurse": {
        "jp": "ナース",
        "syn": ["ナース", "看護師", "看護婦", "nurse"],
        "outfits": {
            "modest": [
                "white long-sleeved nurse uniform with {accent} piping on the collar and cuffs, {sub} {pattern} badge on the chest, knee-length",
                "white nurse cap with {accent} line",
                "white tights",
                "white nurse shoes",
            ],
            "standard": [
                "{main} short-sleeved nurse dress with {accent} piping on the collar and pocket, {sub} {pattern} badge on the chest, above-knee",
                "{main} nurse cap with {accent} line",
                "white thigh-high stockings with {accent} top band",
                "white nurse shoes",
                "stethoscope around the neck",
            ],
            "high": [
                "{material} {main} mini nurse dress unbuttoned to the chest with {accent} piping, {sub} {pattern} badge, high-cut hem",
                "{main} nurse cap with {accent} line",
                "white thigh-high stockings with {accent} lace tops and garter belt",
                "white heeled pumps",
                "stethoscope around the neck",
            ],
        },
        "male": {
            "modest": ["white doctor's coat with {accent} piping, {sub} {pattern} badge, {main} scrubs underneath", "stethoscope around the neck", "white shoes"],
            "standard": ["white doctor's coat with {accent} piping, {sub} {pattern} badge, {main} scrubs underneath", "stethoscope around the neck", "white shoes"],
            "high": ["white doctor's coat open over a bare chest with {accent} piping, {sub} {pattern} badge", "{main} scrub pants", "stethoscope around the neck", "white shoes"],
        },
        "props": ["oversized syringe", "clipboard", "pill bottle"],
        "materials": ["cotton", "latex"],
        "palettes": [("white", "pastel pink", "crimson"), ("white", "sky blue", "navy"), ("black", "white", "crimson")],
    },
    "idol": {
        "jp": "アイドル",
        "syn": ["アイドル", "ステージ衣装", "idol", "stage outfit"],
        "outfits": {
            "modest": [
                "{material} {main} idol stage dress with {accent} frills on every hem, long sleeves, {sub} {pattern} on the bodice",
                "{sub} ribbon hair accessory with {pattern}",
                "white thigh-high socks with {accent} top band",
                "{main} ankle boots with {accent} ribbons",
                "{sub} wrist cuffs with {accent} trim",
            ],
            "standard": [
                "{material} {main} idol stage outfit: cropped jacket with {accent} frills, {sub} corset top with {pattern}, layered mini skirt with {accent} hem",
                "{sub} ribbon hair accessory with {pattern}",
                "white thigh-high socks with {accent} top band",
                "{main} ankle boots with {accent} ribbons",
                "headset microphone",
            ],
            "high": [
                "{material} {main} idol stage outfit: bikini-style top with {accent} frills, {sub} {pattern} on the chest, micro skirt with {accent} hem, exposed midriff",
                "{sub} ribbon hair accessory with {pattern}",
                "white thigh-high stockings with {accent} lace tops",
                "{main} heeled boots with {accent} ribbons",
                "headset microphone",
                "{sub} choker with {accent} star",
            ],
        },
        "male": {
            "modest": ["{material} {main} idol stage jacket with {accent} piping and {sub} {pattern} on the chest, white shirt", "{main} slacks with {accent} side stripe", "{main} boots", "headset microphone"],
            "standard": ["{material} {main} idol stage jacket with {accent} piping and {sub} {pattern} on the chest, white shirt", "{main} slacks with {accent} side stripe", "{main} boots", "headset microphone"],
            "high": ["{material} {main} open idol stage jacket with {accent} piping over a bare chest, {sub} {pattern} on the collar", "{main} slacks with {accent} side stripe", "{main} boots", "headset microphone"],
        },
        "props": ["glowing microphone in {accent}", "glow stick"],
        "materials": ["satin", "sequined"],
        "palettes": [("pastel pink", "white", "gold"), ("sky blue", "white", "silver"), ("white", "royal blue", "gold"), ("black", "hot pink", "silver")],
    },
    "magical_girl": {
        "jp": "魔法少女",
        "syn": ["魔法少女", "マジカル", "magical girl", "mahou shoujo"],
        "outfits": {
            "modest": [
                "{main} magical girl dress with {accent} trim on every hem, long puffed sleeves, {sub} {pattern} brooch on the chest, knee-length layered skirt",
                "{sub} ribbon on the head with {accent} {pattern}",
                "white gloves with {accent} cuffs",
                "white tights",
                "{main} boots with {accent} trim",
            ],
            "standard": [
                "{main} magical girl outfit with {accent} trim, puffed short sleeves, {sub} {pattern} brooch on the chest, layered mini skirt",
                "{sub} oversized ribbon on the head with {accent} {pattern}",
                "white gloves with {accent} cuffs",
                "white thigh-high socks with {accent} top band",
                "{main} boots with {accent} trim",
                "{sub} choker with {accent} gem",
            ],
            "high": [
                "{main} magical girl leotard with {accent} trim, {sub} {pattern} brooch on the chest, high-cut hips, detached micro skirt",
                "{sub} oversized ribbon on the head with {accent} {pattern}",
                "white opera gloves with {accent} cuffs",
                "white thigh-high stockings with {accent} top band",
                "{main} heeled boots with {accent} trim",
                "{sub} choker with {accent} gem",
            ],
        },
        "male": {
            "modest": ["{main} magical boy uniform with {accent} trim, {sub} {pattern} brooch on the chest", "{sub} half-cape", "white gloves", "{main} boots"],
            "standard": ["{main} magical boy uniform with {accent} trim, {sub} {pattern} brooch on the chest", "{sub} half-cape", "white gloves", "{main} boots"],
            "high": ["{main} magical boy jacket open over a bare chest with {accent} trim, {sub} {pattern} brooch", "{main} shorts", "white gloves", "{main} boots"],
        },
        "props": ["magical wand with a {accent} {pattern} tip", "transformation compact"],
        "materials": ["satin"],
        "palettes": [("pastel pink", "white", "gold"), ("white", "sky blue", "gold"), ("lavender", "white", "silver"), ("black", "crimson", "gold")],
    },
    "office_lady": {
        "jp": "オフィス（スーツ）",
        "syn": ["OL", "オフィス", "スーツ", "秘書", "会社員", "office", "suit", "secretary", "office lady"],
        "outfits": {
            "modest": [
                "{material} {main} tailored pantsuit with {accent} piping on the lapels, white blouse, {sub} {pattern} brooch",
                "{main} pumps",
                "{sub} wristwatch",
            ],
            "standard": [
                "{material} {main} fitted blazer with {accent} piping on the lapels, white blouse, {sub} {pattern} brooch",
                "{main} knee-length pencil skirt",
                "sheer black pantyhose",
                "{main} pumps with {accent} heel",
            ],
            "high": [
                "{material} {main} fitted blazer with {accent} piping, open to show a {sub} lace bra, {sub} {pattern} brooch",
                "{main} micro pencil skirt",
                "sheer black pantyhose with {accent} garter straps visible",
                "{main} stiletto pumps",
            ],
        },
        "male": {
            "modest": ["{material} {main} business suit with {accent} piping, white shirt, {sub} necktie with {pattern}", "{main} dress shoes"],
            "standard": ["{material} {main} business suit with {accent} piping, white shirt, {sub} necktie with {pattern}", "{main} dress shoes"],
            "high": ["{material} {main} suit jacket worn open over a bare chest with {accent} piping, loosened {sub} necktie with {pattern}", "{main} slacks", "{main} dress shoes"],
        },
        "props": ["tablet", "leather briefcase"],
        "materials": ["wool"],
        "palettes": [("black", "white", "gold"), ("navy", "white", "silver"), ("gray", "white", "wine red")],
    },
    "casual_street": {
        "jp": "カジュアル・ストリート",
        "syn": ["私服", "カジュアル", "ストリート", "パーカー", "casual", "street", "hoodie", "streetwear"],
        "outfits": {
            "modest": [
                "{material} {main} oversized hoodie with {sub} {pattern} print on the chest and {accent} drawstrings",
                "{sub} long pleated skirt with {accent} hem",
                "white sneakers with {accent} laces",
                "{main} baseball cap with {accent} logo",
            ],
            "standard": [
                "{material} {main} cropped hoodie with {sub} {pattern} print and {accent} drawstrings",
                "{sub} denim shorts with {accent} belt",
                "{main} thigh-high socks with {accent} stripes",
                "white sneakers with {accent} laces",
                "{sub} crossbody bag",
            ],
            "high": [
                "{material} {main} crop top with {sub} {pattern} print, deep neckline, exposed midriff",
                "{sub} micro shorts with {accent} belt",
                "{main} thigh-high socks with {accent} stripes",
                "white platform sneakers with {accent} laces",
                "{main} oversized open jacket with {accent} lining",
            ],
        },
        "male": {
            "modest": ["{material} {main} oversized hoodie with {sub} {pattern} print and {accent} drawstrings", "{sub} cargo pants", "white sneakers with {accent} laces", "{main} baseball cap"],
            "standard": ["{material} {main} oversized hoodie with {sub} {pattern} print and {accent} drawstrings", "{sub} cargo pants", "white sneakers with {accent} laces", "{main} baseball cap"],
            "high": ["{material} {main} open jacket with {sub} {pattern} print over a bare chest, {accent} lining", "{sub} shorts with {accent} belt", "white sneakers with {accent} laces"],
        },
        "props": ["smartphone with {accent} case", "headphones around the neck", "skateboard"],
        "materials": ["cotton", "nylon"],
        "palettes": [("black", "white", "hot pink"), ("navy", "white", "orange"), ("gray", "black", "sky blue"), ("white", "pastel pink", "lavender")],
    },
    "swimsuit": {
        "jp": "水着",
        "syn": ["水着", "ビキニ", "スクール水着", "スク水", "swimsuit", "bikini", "swimwear"],
        "outfits": {
            "modest": [
                "{main} one-piece school swimsuit with {accent} piping and a {sub} {pattern} name tag",
                "white rash guard with {accent} zipper",
                "{sub} sandals",
            ],
            "standard": [
                "{main} halter bikini with {accent} piping and {sub} {pattern} on the top",
                "{sub} sheer sarong with {accent} hem",
                "{sub} sandals",
                "{accent} ankle bracelet",
            ],
            "high": [
                "{main} micro string bikini with {accent} piping and a {sub} {pattern} charm at the center",
                "{sub} sheer cover-up open at the front",
                "{accent} ankle bracelet",
                "{sub} sandals",
            ],
        },
        "male": {
            "modest": ["{main} swim trunks with {accent} side stripe and {sub} {pattern}", "white rash guard with {accent} zipper", "sandals"],
            "standard": ["{main} swim trunks with {accent} side stripe and {sub} {pattern}", "open white shirt", "sandals"],
            "high": ["{main} brief-style swimsuit with {accent} piping and {sub} {pattern}", "{accent} ankle bracelet", "sandals"],
        },
        "props": ["beach ball", "parasol", "water gun"],
        "materials": ["nylon"],
        "palettes": [("white", "sky blue", "gold"), ("black", "hot pink", "white"), ("navy", "white", "crimson"), ("pastel pink", "white", "mint")],
    },
    "bunny_girl": {
        "jp": "バニーガール",
        "syn": ["バニー", "バニーガール", "バニースーツ", "bunny girl", "bunny suit", "bunnysuit"],
        "outfits": {
            "modest": [
                "{material} {main} bunny suit with long sleeves and {accent} piping, high neckline, {sub} {pattern} bowtie",
                "{main} bunny ears headband with {accent} inner lining",
                "black sheer pantyhose",
                "{main} heeled pumps",
                "white wrist cuffs",
            ],
            "standard": [
                "{material} {main} strapless bunny leotard with {accent} piping along every edge, {sub} {pattern} bowtie, white collar",
                "{main} bunny ears headband with {accent} inner lining",
                "black sheer pantyhose",
                "{main} heeled pumps",
                "white wrist cuffs",
                "fluffy white cotton tail",
            ],
            "high": [
                "{material} {main} high-cut strapless bunny leotard with {accent} piping, deep cleavage, {sub} {pattern} bowtie, white collar",
                "{main} bunny ears headband with {accent} inner lining",
                "black fishnet pantyhose",
                "{main} stiletto pumps",
                "white wrist cuffs",
                "fluffy white cotton tail",
            ],
        },
        "male": {
            "modest": ["{material} {main} vest with {accent} piping, white shirt, {sub} {pattern} bowtie", "{main} bunny ears headband with {accent} inner lining", "{main} slacks", "{main} dress shoes"],
            "standard": ["{material} {main} vest with {accent} piping, white shirt, {sub} {pattern} bowtie", "{main} bunny ears headband with {accent} inner lining", "{main} slacks", "{main} dress shoes"],
            "high": ["{sub} {pattern} bowtie and white collar on a bare chest, {main} vest with {accent} piping worn open", "{main} bunny ears headband with {accent} inner lining", "{main} fitted shorts", "white wrist cuffs"],
        },
        "props": ["serving tray with champagne", "casino chips"],
        "materials": ["satin", "latex"],
        "palettes": [("black", "white", "crimson"), ("white", "pastel pink", "gold"), ("navy", "white", "gold"), ("wine red", "black", "gold")],
    },
    "military": {
        "jp": "軍服",
        "syn": ["軍服", "軍人", "将校", "ミリタリー", "military", "soldier", "officer", "army"],
        "outfits": {
            "modest": [
                "{main} military officer uniform jacket with {accent} piping and {sub} {pattern} insignia on the collar, double-breasted gold buttons",
                "{main} trousers with {accent} side stripe",
                "{main} peaked cap with {accent} badge",
                "black leather boots",
                "white gloves",
            ],
            "standard": [
                "{main} military uniform jacket with {accent} piping and {sub} {pattern} insignia, double-breasted gold buttons",
                "{main} pencil skirt with {accent} hem line",
                "{main} peaked cap with {accent} badge",
                "black knee-high leather boots",
                "white gloves",
                "{sub} armband",
            ],
            "high": [
                "{main} cropped military jacket with {accent} piping and {sub} {pattern} insignia, open to show a {sub} bikini top, exposed midriff",
                "{main} micro skirt with {accent} hem line",
                "{main} peaked cap with {accent} badge",
                "black thigh-high leather boots with {accent} garter straps",
                "white gloves",
                "{sub} armband",
            ],
        },
        "male": {
            "modest": ["{main} military officer uniform with {accent} piping and {sub} {pattern} insignia, double-breasted gold buttons", "{main} trousers with {accent} side stripe", "{main} peaked cap with {accent} badge", "black leather boots", "white gloves"],
            "standard": ["{main} military officer uniform with {accent} piping and {sub} {pattern} insignia, double-breasted gold buttons", "{main} trousers with {accent} side stripe", "{main} peaked cap with {accent} badge", "black leather boots", "white gloves"],
            "high": ["{main} military jacket worn open over a bare chest with {accent} piping and {sub} {pattern} insignia", "{main} trousers with {accent} side stripe", "{main} peaked cap with {accent} badge", "black leather boots"],
        },
        "props": ["saber with {accent} hilt", "riding crop", "handgun in a holster"],
        "materials": ["wool"],
        "palettes": [("black", "crimson", "gold"), ("navy", "white", "gold"), ("olive green", "black", "gold"), ("white", "navy", "gold")],
    },
    "princess_dress": {
        "jp": "お姫様ドレス",
        "syn": ["お姫様", "姫", "プリンセス", "ドレス", "王女", "princess", "dress", "ball gown", "gown"],
        "outfits": {
            "modest": [
                "{material} {main} ball gown with {accent} embroidery on the bodice and hem, long sleeves, {sub} {pattern} on the skirt panels, floor-length",
                "{sub} tiara with {accent} gems",
                "white opera gloves",
                "{main} heeled shoes with {accent} buckles",
                "{accent} pearl necklace",
            ],
            "standard": [
                "{material} {main} princess dress with {accent} embroidery on the bodice, off-shoulder short sleeves, {sub} {pattern} on the skirt panels, knee-length layered skirt",
                "{sub} tiara with {accent} gems",
                "white gloves",
                "{main} heeled shoes with {accent} buckles",
                "{accent} pearl necklace",
            ],
            "high": [
                "{material} {main} princess corset dress with {accent} embroidery, deep sweetheart neckline, high thigh slit, {sub} {pattern} on the skirt",
                "{sub} tiara with {accent} gems",
                "white opera gloves",
                "{main} heeled shoes with {accent} buckles",
                "{accent} pearl necklace",
                "white thigh-high stockings with {accent} lace tops",
            ],
        },
        "male": {
            "modest": ["{material} {main} prince uniform with {accent} embroidery, {sub} sash with {pattern}, epaulettes", "{main} trousers", "{main} boots", "{sub} half-cape with {accent} lining"],
            "standard": ["{material} {main} prince uniform with {accent} embroidery, {sub} sash with {pattern}, epaulettes", "{main} trousers", "{main} boots", "{sub} half-cape with {accent} lining"],
            "high": ["{material} {main} prince jacket worn open over a bare chest with {accent} embroidery, {sub} sash with {pattern}", "{main} trousers", "{main} boots"],
        },
        "props": ["single rose", "lace fan", "scepter with a {accent} gem"],
        "materials": ["silk", "satin"],
        "palettes": [("white", "gold", "royal blue"), ("pastel pink", "white", "gold"), ("lavender", "white", "silver"), ("crimson", "gold", "black")],
    },
    "cheongsam": {
        "jp": "チャイナドレス",
        "syn": ["チャイナ", "チャイナドレス", "チャイナ服", "cheongsam", "china dress", "qipao"],
        "outfits": {
            "modest": [
                "{material} {main} long cheongsam with {accent} piping on the collar and hem, {sub} {pattern} embroidery, long sleeves, modest slits",
                "{sub} hair buns with {accent} ribbons",
                "{main} flat shoes",
            ],
            "standard": [
                "{material} {main} cheongsam with {accent} piping on the collar and hem, {sub} {pattern} embroidery, short sleeves, side slit to the thigh",
                "{sub} double hair buns with {accent} ribbons",
                "white thigh-high socks with {accent} top band",
                "{main} heeled shoes",
            ],
            "high": [
                "{material} {main} micro cheongsam with {accent} piping, sleeveless, {sub} {pattern} embroidery, side slits to the waist, keyhole cleavage cutout",
                "{sub} double hair buns with {accent} ribbons",
                "black thigh-high stockings with {accent} lace tops",
                "{main} heeled shoes",
            ],
        },
        "male": {
            "modest": ["{material} {main} changshan with {accent} piping, {sub} {pattern} embroidery", "{main} trousers", "{main} kung fu shoes"],
            "standard": ["{material} {main} changshan with {accent} piping, {sub} {pattern} embroidery", "{main} trousers", "{main} kung fu shoes"],
            "high": ["{material} {main} sleeveless chinese vest worn open with {accent} piping, {sub} {pattern} embroidery", "{main} trousers", "{main} kung fu shoes"],
        },
        "props": ["paper fan with {pattern}", "steamed bun"],
        "materials": ["silk", "satin"],
        "palettes": [("crimson", "gold", "black"), ("royal blue", "gold", "white"), ("black", "gold", "crimson"), ("emerald green", "gold", "white")],
    },
    "bodysuit": {
        "jp": "ボディスーツ",
        "syn": ["ボディスーツ", "プラグスーツ", "ライダースーツ", "bodysuit", "plugsuit", "catsuit"],
        "outfits": {
            "modest": [
                "{main} full-body plugsuit with {accent} glowing lines along the seams and {sub} {pattern} on the chest, high collar",
                "{main} armored gloves",
                "{main} boots with {accent} lights",
            ],
            "standard": [
                "{main} skin-tight bodysuit with {accent} glowing lines along the seams and {sub} {pattern} on the chest, {sub} panels on the sides",
                "{main} gloves with {accent} trim",
                "{main} thigh-high boots with {accent} lights",
                "{sub} utility belt",
            ],
            "high": [
                "{main} skin-tight bodysuit with {accent} glowing lines, cutouts at the chest and hips, {sub} {pattern} on the chest",
                "{main} gloves with {accent} trim",
                "{main} thigh-high boots with {accent} lights",
                "{sub} utility belt",
            ],
        },
        "male": {
            "modest": ["{main} full-body plugsuit with {accent} glowing lines along the seams and {sub} {pattern} on the chest", "{main} gloves", "{main} boots"],
            "standard": ["{main} full-body plugsuit with {accent} glowing lines along the seams and {sub} {pattern} on the chest", "{main} gloves", "{main} boots"],
            "high": ["{main} bodysuit with {accent} glowing lines, open at the chest, {sub} {pattern} on the shoulder", "{main} gloves", "{main} boots"],
        },
        "props": ["sci-fi helmet under the arm", "energy pistol"],
        "materials": ["latex", "synthetic"],
        "palettes": [("white", "black", "sky blue"), ("black", "crimson", "silver"), ("navy", "white", "orange")],
    },
    "sportswear": {
        "jp": "スポーツウェア",
        "syn": ["体操服", "スポーツ", "ジャージ", "陸上", "ブルマ", "運動", "sports", "athletic", "gym", "track"],
        "outfits": {
            "modest": [
                "{main} track jacket with {accent} stripes on the sleeves and {sub} {pattern} on the chest, zipped up",
                "{main} track pants with {accent} stripes",
                "white sneakers",
                "{sub} sports towel around the neck",
            ],
            "standard": [
                "{main} athletic crop jacket with {accent} stripes and {sub} {pattern} on the chest",
                "{main} gym shorts with {accent} trim",
                "white thigh-high socks with {accent} stripes",
                "white sneakers",
                "{sub} wristbands",
            ],
            "high": [
                "{main} sports bra with {accent} trim and {sub} {pattern} on the chest",
                "{main} buruma with {accent} trim",
                "white thigh-high socks with {accent} stripes",
                "white sneakers",
                "{sub} wristbands",
                "{main} open track jacket",
            ],
        },
        "male": {
            "modest": ["{main} track jacket with {accent} stripes and {sub} {pattern} on the chest", "{main} track pants", "white sneakers"],
            "standard": ["{main} tank top with {accent} trim and {sub} {pattern} on the chest", "{main} gym shorts", "white sneakers", "{sub} wristbands"],
            "high": ["shirtless, {main} open track jacket with {accent} stripes", "{main} gym shorts", "white sneakers", "{sub} wristbands"],
        },
        "props": ["basketball", "sports drink bottle", "tennis racket"],
        "materials": ["nylon"],
        "palettes": [("navy", "white", "orange"), ("crimson", "white", "gold"), ("black", "sky blue", "white")],
    },
    "pirate": {
        "jp": "海賊",
        "syn": ["海賊", "パイレーツ", "pirate"],
        "outfits": {
            "modest": [
                "{material} {main} pirate captain coat with {accent} trim and {sub} {pattern} embroidery, white ruffled shirt, {sub} corset",
                "{main} tricorn hat with {accent} feather",
                "{main} trousers",
                "{main} knee-high leather boots with {accent} buckles",
                "{sub} sash",
            ],
            "standard": [
                "{material} {main} pirate coat with {accent} trim and {sub} {pattern} embroidery, white off-shoulder ruffled blouse, {sub} corset",
                "{main} tricorn hat with {accent} feather",
                "{main} shorts with {sub} sash",
                "{main} thigh-high leather boots with {accent} buckles",
            ],
            "high": [
                "{material} {main} open pirate coat with {accent} trim and {sub} {pattern} embroidery, {sub} bikini top with {accent} lacing, exposed midriff",
                "{main} tricorn hat with {accent} feather",
                "{main} micro shorts with {sub} sash",
                "{main} thigh-high leather boots with {accent} buckles",
            ],
        },
        "male": {
            "modest": ["{material} {main} pirate captain coat with {accent} trim and {sub} {pattern} embroidery, white shirt", "{main} tricorn hat with {accent} feather", "{main} trousers", "{main} boots"],
            "standard": ["{material} {main} pirate captain coat with {accent} trim and {sub} {pattern} embroidery, white shirt open at the chest", "{main} tricorn hat with {accent} feather", "{main} trousers", "{main} boots"],
            "high": ["{material} {main} open pirate coat with {accent} trim over a bare chest, {sub} {pattern} embroidery", "{main} tricorn hat with {accent} feather", "{main} trousers with {sub} sash", "{main} boots"],
        },
        "props": ["cutlass", "flintlock pistol", "treasure map"],
        "materials": ["leather"],
        "palettes": [("black", "crimson", "gold"), ("navy", "white", "gold"), ("brown", "cream", "gold")],
    },
    "ninja": {
        "jp": "忍者",
        "syn": ["忍者", "くノ一", "くのいち", "忍び", "ninja", "kunoichi", "shinobi"],
        "outfits": {
            "modest": [
                "{main} ninja outfit with {accent} trim on the collar and cuffs, {sub} {pattern} on the chest guard",
                "{main} arm guards",
                "{sub} scarf",
                "{main} tabi boots",
                "{sub} sash",
            ],
            "standard": [
                "{main} sleeveless ninja top with {accent} trim, fishnet undershirt, {sub} {pattern} on the chest guard",
                "{main} shorts with {sub} sash",
                "{main} arm guards",
                "{sub} scarf",
                "{main} thigh-high tabi boots",
            ],
            "high": [
                "{main} ninja outfit with a deep V neckline framed in {accent} trim, fishnet underlayer, {sub} {pattern} on the chest guard, sideless",
                "{main} micro shorts with {sub} sash",
                "{main} arm guards",
                "{sub} scarf",
                "{main} thigh-high tabi boots with {accent} straps",
            ],
        },
        "male": {
            "modest": ["{main} ninja outfit with {accent} trim, {sub} {pattern} on the chest guard", "{main} arm guards", "{sub} scarf", "{main} tabi boots"],
            "standard": ["{main} sleeveless ninja top with {accent} trim, fishnet undershirt, {sub} {pattern} on the chest guard", "{main} pants with {sub} sash", "{main} arm guards", "{sub} scarf", "{main} tabi boots"],
            "high": ["{main} ninja vest worn open over fishnet with {accent} trim, {sub} {pattern} on the chest guard", "{main} pants with {sub} sash", "{main} arm guards", "{sub} scarf", "{main} tabi boots"],
        },
        "props": ["kunai", "giant shuriken", "katana on the back"],
        "materials": ["cloth"],
        "palettes": [("black", "crimson", "gold"), ("navy", "white", "silver"), ("dark purple", "black", "pastel pink")],
    },
    "jester_outfit": {
        "jp": "道化師衣装",
        "syn": ["道化師", "ジェスター", "サーカス", "circus"],
        "outfits": {
            "modest": [
                "{main} and {sub} harlequin jester outfit with {accent} bells on every point, {pattern} on the sleeves, long sleeves",
                "{main} and {sub} jester hat with {accent} bells",
                "{main} tights with {pattern}",
                "{main} pointed shoes with {accent} bells",
            ],
            "standard": [
                "{main} and {sub} harlequin jester dress with {accent} bells on every hem, {pattern} on the bodice, short puffed sleeves, mini skirt",
                "{main} and {sub} jester hat with {accent} bells",
                "{main} and {sub} mismatched thigh-high socks",
                "{main} pointed shoes with {accent} bells",
                "{sub} ruffled collar",
            ],
            "high": [
                "{main} and {sub} harlequin jester leotard with {accent} bells, {pattern} on the bodice, high-cut hips, deep neckline",
                "{main} and {sub} jester hat with {accent} bells",
                "{main} and {sub} mismatched thigh-high stockings",
                "{main} pointed heels with {accent} bells",
                "{sub} ruffled collar",
            ],
        },
        "male": {
            "modest": ["{main} and {sub} harlequin jester outfit with {accent} bells, {pattern} on the sleeves", "{main} and {sub} jester hat with {accent} bells", "{main} pointed shoes"],
            "standard": ["{main} and {sub} harlequin jester outfit with {accent} bells, {pattern} on the sleeves", "{main} and {sub} jester hat with {accent} bells", "{main} pointed shoes"],
            "high": ["{main} and {sub} harlequin vest worn open with {accent} bells, {pattern} on the collar", "{main} and {sub} jester hat with {accent} bells", "{main} and {sub} harlequin tights", "{main} pointed shoes"],
        },
        "props": ["juggling balls", "fan of playing cards", "mask on a stick"],
        "materials": ["satin"],
        "palettes": [("purple", "gold", "black"), ("crimson", "white", "black"), ("black", "white", "crimson")],
    },
    "loungewear": {
        "jp": "部屋着・パジャマ",
        "syn": ["パジャマ", "部屋着", "ネグリジェ", "寝間着", "pajamas", "loungewear", "nightgown", "sleepwear"],
        "outfits": {
            "modest": [
                "{material} {main} long pajama set with {sub} {pattern} print and {accent} piping on the collar",
                "{sub} fluffy slippers",
                "{main} sleep mask pushed up on the head with {accent} trim",
            ],
            "standard": [
                "{material} {main} oversized sleep shirt with {sub} {pattern} print and {accent} buttons, reaching the thighs",
                "{sub} fluffy slippers",
                "{main} thigh-high socks with {accent} top band",
                "{main} sleep mask pushed up on the head with {accent} trim",
            ],
            "high": [
                "{material} {main} sheer negligee with {accent} lace trim and {sub} {pattern} ribbons, deep neckline",
                "{sub} fluffy slippers",
                "{main} thigh-high stockings with {accent} lace tops",
                "{main} sleep mask pushed up on the head with {accent} trim",
            ],
        },
        "male": {
            "modest": ["{material} {main} pajama set with {sub} {pattern} print and {accent} piping", "{sub} slippers"],
            "standard": ["{material} {main} pajama set with {sub} {pattern} print and {accent} piping", "{sub} slippers"],
            "high": ["shirtless, {material} {main} pajama pants with {sub} {pattern} print and {accent} drawstring", "{sub} slippers"],
        },
        "props": ["oversized plush toy", "pillow", "mug of cocoa"],
        "materials": ["silk", "flannel"],
        "palettes": [("pastel pink", "white", "lavender"), ("sky blue", "white", "gold"), ("black", "white", "hot pink")],
    },
    "teacher": {
        "jp": "先生",
        "syn": ["先生", "教師", "教員", "teacher", "sensei"],
        "outfits": {
            "modest": [
                "{material} {main} cardigan over a white blouse with {accent} buttons, {sub} {pattern} brooch",
                "{main} long pleated skirt",
                "black tights",
                "{main} flats",
                "rimless glasses",
            ],
            "standard": [
                "{material} {main} fitted blouse with {accent} buttons, {sub} {pattern} brooch, {sub} knee-length pencil skirt",
                "sheer black pantyhose",
                "{main} pumps",
                "{main} cardigan draped over the shoulders",
            ],
            "high": [
                "{material} {main} blouse unbuttoned to the chest with {accent} buttons, {sub} {pattern} brooch, {sub} micro pencil skirt",
                "sheer black pantyhose with {accent} garter straps",
                "{main} pumps",
                "{main} cardigan draped over the shoulders",
            ],
        },
        "male": {
            "modest": ["{material} {main} cardigan over a white shirt, {sub} necktie with {pattern}", "{main} slacks", "{main} shoes"],
            "standard": ["{material} {main} cardigan over a white shirt, {sub} necktie with {pattern}", "{main} slacks", "{main} shoes"],
            "high": ["{material} white shirt unbuttoned to the chest with a loosened {sub} necktie with {pattern}, {main} cardigan draped over the shoulders", "{main} slacks", "{main} shoes"],
        },
        "props": ["pointer stick", "attendance book", "piece of chalk"],
        "materials": ["wool", "cotton"],
        "palettes": [("navy", "white", "gold"), ("brown", "cream", "wine red"), ("black", "white", "crimson")],
    },
    "dancer": {
        "jp": "踊り子",
        "syn": ["踊り子", "ダンサー", "ベリーダンス", "dancer", "belly dancer"],
        "outfits": {
            "modest": [
                "{material} {main} long-sleeved dance dress with {accent} coin trim on the hem, {sub} {pattern} embroidery, flowing skirt",
                "{sub} veil with {accent} coins",
                "{accent} bangles",
                "{main} flat shoes",
            ],
            "standard": [
                "{material} {main} dancer top with {accent} coin trim, {sub} {pattern} embroidery, flowing {main} harem pants with {accent} waistband",
                "{sub} veil with {accent} coins",
                "{accent} bangles on both wrists",
                "barefoot with {accent} anklets",
            ],
            "high": [
                "{material} {main} bikini-style dancer top with {accent} coin trim, {sub} {pattern} embroidery, sheer {main} harem pants slit to the hip with {accent} waistband, exposed midriff",
                "{sub} face veil with {accent} coins",
                "{accent} bangles on both wrists",
                "barefoot with {accent} anklets",
                "{sub} navel jewel",
            ],
        },
        "male": {
            "modest": ["{material} {main} dancer tunic with {accent} coin trim, {sub} {pattern} embroidery", "{main} harem pants with {accent} waistband", "{accent} bangles"],
            "standard": ["{material} {main} open vest with {accent} coin trim, {sub} {pattern} embroidery", "{main} harem pants with {accent} waistband", "{accent} bangles"],
            "high": ["shirtless with {accent} coin necklace, {sub} {pattern} body paint", "sheer {main} harem pants with {accent} waistband", "{accent} bangles on both wrists"],
        },
        "props": ["sheer veil", "tambourine", "finger cymbals"],
        "materials": ["silk", "sheer chiffon"],
        "palettes": [("crimson", "gold", "black"), ("teal", "gold", "white"), ("purple", "gold", "black")],
    },
    "delinquent": {
        "jp": "不良・スケバン",
        "syn": ["不良", "ヤンキー", "スケバン", "ヤンキー", "delinquent", "sukeban", "yankee"],
        "outfits": {
            "modest": [
                "{main} ankle-length sukeban sailor uniform with {accent} lines on the collar, {sub} neckerchief with {pattern}",
                "{main} surgical mask pulled down to the chin",
                "black loafers",
                "{sub} chain accessory",
            ],
            "standard": [
                "{main} sailor uniform worn open over a {sub} tank top, {accent} lines on the collar, {pattern} on the neckerchief",
                "{main} short pleated skirt with {accent} hem",
                "black knee-high socks",
                "black loafers",
                "bandage on the cheek",
                "{sub} chain accessory",
            ],
            "high": [
                "{main} cropped sukeban top worn open over a {sub} bikini top, {accent} lines on the collar, {pattern} neckerchief",
                "{main} micro pleated skirt with {accent} hem",
                "black thigh-high socks",
                "black loafers",
                "bandage on the cheek",
                "{sub} chain accessory",
            ],
        },
        "male": {
            "modest": ["{main} long gakuran worn open over a {sub} shirt, {accent} piping, {pattern} embroidery on the back", "{main} baggy trousers", "black boots", "bandage on the cheek"],
            "standard": ["{main} long gakuran worn open over a {sub} shirt, {accent} piping, {pattern} embroidery on the back", "{main} baggy trousers", "black boots", "bandage on the cheek"],
            "high": ["{main} long gakuran worn open over a bare chest, {accent} piping, {pattern} embroidery on the back", "{main} baggy trousers", "black boots", "bandage on the cheek"],
        },
        "props": ["wooden sword", "bike chain", "lollipop in the mouth"],
        "materials": ["cotton"],
        "palettes": [("black", "white", "crimson"), ("navy", "white", "gold"), ("dark purple", "black", "pastel pink")],
    },
}

# モチーフの gap_roles で参照している別名（存在しないキーを吸収する）
ROLE_ALIASES = {
    "gal_street": "casual_street",
}

# ---------------------------------------------------------------------------
# 共通パーツ
# ---------------------------------------------------------------------------

BANGS = ["blunt bangs", "side-swept bangs", "parted bangs", "hair between eyes", "swept bangs"]

# 性格に体型指定が無い時の候補（女性）
BODY_DEFAULT_FEMALE = ["slender", "medium build", "petite", "curvy"]
BODY_DEFAULT_MALE = ["slender", "medium build", "athletic", "lean"]
CHEST_SIZES = ["small breasts", "medium breasts", "large breasts"]

# 靴の判定キーワード（性格の footwear 置換に使う）
FOOTWEAR_KEYWORDS = ["shoes", "loafers", "boots", "sneakers", "heels", "sandals", "pumps", "mary janes", "slippers", "barefoot", "geta", "zori", "flats"]

# 品質系（lowres 等）はこのノードの責務外なので入れない。キャラ特徴の整合性に関わるものだけ
NEGATIVE_BASE = [
    "extra accessories", "mismatched colors",
]

# ---------------------------------------------------------------------------
# 自己検証（モジュール読み込み時に参照の整合性だけ確認する）
# ---------------------------------------------------------------------------

def _validate():
    for mk, m in MOTIFS.items():
        for key in ("classic_roles", "gap_roles"):
            for r in m[key]:
                r = ROLE_ALIASES.get(r, r)
                assert r in ROLES, f"MOTIFS[{mk}].{key} に未定義の role: {r}"
        for key in ("classic_arch", "gap_arch"):
            for a in m[key]:
                assert a in ARCHETYPES, f"MOTIFS[{mk}].{key} に未定義の archetype: {a}"
    for rk, r in ROLES.items():
        for ex in ("modest", "standard", "high"):
            assert ex in r["outfits"], f"ROLES[{rk}] に露出 {ex} の服装が無い"
            if "male" in r:
                assert ex in r["male"], f"ROLES[{rk}].male に露出 {ex} の服装が無い"


_validate()
