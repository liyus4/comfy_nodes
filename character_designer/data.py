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
  6. 模様の固定     : 服の模様は「スタイル＋モチーフ由来の模様」（{pattern}）として具体的に決め、配置場所も明記してブレを抑える
  7. 細部の固定     : 素材・縁取り色・留め具・丈・レッグウェア・靴まで文章で指定する

服装リストの記法（data.ROLES / outfit_tags.OUTFIT_TAGS 共通）:
  "item"                 … 必ず入る
  ["item A", "item B"]   … どれか1つ（seed で決まる。説明文版とタグ版で選択肢の数を揃えると同じ選択になる）
  "?item"                … 50% で入る
  OPTIONAL_ITEM_KEYWORDS に該当する小物 … 指定した確率で入る（先頭＝主役の服は必ず残す）

テンプレート文字列の置換キー:
  {main} {sub} {accent}  … テーマカラー3色
  {pattern}              … スタイル修飾＋モチーフ由来の模様（例: small repeating bat-wing motif）
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

# ノードのドロップダウン用: 服の色 / 髪の色 の日本語ラベル
COLOR_JP = {
    "black": "黒", "white": "白", "crimson": "赤", "wine red": "ワインレッド", "royal blue": "青", "navy": "紺", "sky blue": "水色",
    "teal": "青緑", "emerald green": "緑", "mint": "ミント", "gold": "金", "silver": "銀", "pastel pink": "ピンク", "hot pink": "ショッキングピンク",
    "purple": "紫", "dark purple": "濃紫", "lavender": "ラベンダー", "orange": "オレンジ", "yellow": "黄", "brown": "茶", "cream": "クリーム", "gray": "灰",
}
HAIR_COLOR_JP = {
    "black hair": "黒髪", "white hair": "白髪", "silver hair": "銀髪", "gray hair": "灰色髪", "platinum blonde hair": "プラチナブロンド", "blonde hair": "金髪",
    "light brown hair": "明るい茶髪", "brown hair": "茶髪", "dark brown hair": "暗い茶髪", "red hair": "赤髪", "dark red hair": "暗い赤髪", "orange hair": "オレンジ髪",
    "pink hair": "ピンク髪", "hot pink hair": "ショッキングピンク髪", "purple hair": "紫髪", "dark purple hair": "濃紫髪", "lavender hair": "ラベンダー髪",
    "blue hair": "青髪", "dark blue hair": "紺髪", "light blue hair": "水色髪", "teal hair": "青緑髪", "green hair": "緑髪", "dark green hair": "深緑髪", "mint green hair": "ミント髪",
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
}

GENDER_WORDS = {
    "girl": ["女の子", "女子", "少女", "女性", "娘", "ガール", "girl", "female", "woman", "1girl"],
    "boy": ["男の子", "男子", "少年", "男性", "ボーイ", "boy", "male", "man", "1boy"],
}

EXPOSURE_WORDS = {
    "high": ["高露出", "露出高", "露出多", "露出度高", "セクシー", "エロ", "sexy", "revealing", "skimpy"],
    "modest": ["低露出", "露出少", "露出控えめ", "控えめ", "露出なし", "modest", "conservative"],
    "standard": ["標準露出", "標準", "普通の露出", "普通", "standard exposure", "normal exposure"],
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
        "footwear_tags": ["black platform footwear"],
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
        "expression": ["evil smile, looking down at viewer", "sadistic smirk, looking down at viewer", "condescending smile, narrowed eyes"],
        "pose": ["hand on hip, one foot forward", "arms crossed, chin raised", "holding a riding crop"],
        "body": ["tall"],
        "accessories": ["{main} choker with a {accent} ring", "{accent} earrings"],
        "footwear": None,
    },
    "juujun": {
        "jp": "従順",
        "syn": ["従順", "じゅうじゅん", "忠実", "服従", "献身", "素直", "obedient", "submissive", "devoted", "loyal"],
        "design_jp": "伏し目＋手を前で揃える＋首輪やリボンの「所有の記号」。淡い色と控えめな装飾で素直さを表現",
        "eyes": ["soft downcast eyes", "gentle half-closed eyes"],
        "hair_styles": ["long straight hair", "low twin braids", "long hair with a single ribbon", "neat bob with straight bangs"],
        "hair_colors": ["black hair", "light brown hair", "white hair", "platinum blonde hair"],
        "palettes": [("white", "pastel pink", "crimson"), ("cream", "brown", "gold"), ("black", "white", "crimson")],
        "expression": ["gentle smile, looking at viewer", "shy smile, head tilt", "calm devoted gaze"],
        "pose": ["hands folded in front", "kneeling", "head bowed slightly", "hands behind back"],
        "body": [],
        "accessories": ["{sub} collar with {accent} ring", "{accent} ribbon choker", "{sub} ribbon in hair"],
        "footwear": None,
    },
    "okubyou": {
        "jp": "臆病",
        "syn": ["臆病", "おくびょう", "怖がり", "ビビり", "弱気", "cowardly", "scared", "fearful", "coward"],
        "design_jp": "涙目＋震え＋自分を抱える・物陰から覗く。縮こまったシルエットと淡い寒色で怖がりを表現",
        "eyes": ["wide teary eyes", "nervous wide eyes"],
        "hair_styles": ["messy medium hair", "low twintails", "long hair with long bangs", "short hair with a cowlick"],
        "hair_colors": ["light brown hair", "lavender hair", "light blue hair", "white hair"],
        "palettes": [("lavender", "white", "sky blue"), ("cream", "sky blue", "pastel pink"), ("gray", "white", "lavender")],
        "expression": ["scared, teary eyes", "nervous, trembling", "wide eyes, tears welling up"],
        "pose": ["hugging own body", "peeking from behind a wall", "cowering", "hands up defensively"],
        "body": [],
        "accessories": ["small {sub} plush held tightly", "{accent} hair pin", "bandaid on the knee"],
        "footwear": None,
    },
    "jishinka": {
        "jp": "自信家",
        "syn": ["自信家", "自信満々", "堂々", "自信", "confident", "self-assured", "bold"],
        "design_jp": "胸を張る＋腰に手＋顎を上げた笑み。はっきりした原色と金で強さを表現",
        "eyes": ["confident sharp eyes", "bright determined eyes"],
        "hair_styles": ["long wavy hair swept back", "high ponytail", "short hair slicked back", "long straight hair"],
        "hair_colors": ["blonde hair", "red hair", "black hair", "white hair"],
        "palettes": [("crimson", "white", "gold"), ("royal blue", "white", "gold"), ("white", "gold", "crimson")],
        "expression": ["confident smile", "smug confident grin", "proud smile, chin up"],
        "pose": ["hand on hip, chest out", "arms crossed", "pointing at self with thumb"],
        "body": [],
        "accessories": ["{accent} earrings", "{accent} brooch"],
        "footwear": None,
    },
    "haraguro": {
        "jp": "腹黒",
        "syn": ["腹黒", "はらぐろ", "黒幕", "haraguro", "two-faced", "scheming"],
        "design_jp": "完璧な笑顔の裏に影——細めた目と口元の笑みのズレ、白×黒×紫で裏のある雰囲気",
        "eyes": ["narrowed smiling eyes", "closed-eye smile", "sharp eyes behind a gentle smile"],
        "hair_styles": ["long straight hair", "neat low ponytail", "half-up long hair"],
        "hair_colors": ["black hair", "dark purple hair", "white hair", "platinum blonde hair"],
        "palettes": [("white", "black", "purple"), ("black", "white", "gold"), ("lavender", "black", "gold")],
        "expression": ["polite smile with shadowed eyes", "closed-eye smile", "faint knowing smirk"],
        "pose": ["hands folded in front", "finger on lips", "head tilt with hands behind back"],
        "body": [],
        "accessories": ["{accent} brooch", "thin {accent} chain necklace"],
        "footwear": None,
    },
    "fushigi": {
        "jp": "不思議ちゃん",
        "syn": ["不思議ちゃん", "不思議", "電波", "ふわふわ", "fushigi", "eccentric", "spacey"],
        "design_jp": "焦点の合わない目とちぐはぐな小物。パステル＋ミスマッチで浮世離れ感",
        "eyes": ["unfocused dreamy eyes", "wide eyes with star-shaped highlights"],
        "hair_styles": ["long messy wavy hair", "uneven twintails", "long hair with random small braids"],
        "hair_colors": ["lavender hair", "light blue hair", "pink hair", "white hair"],
        "palettes": [("lavender", "white", "mint"), ("sky blue", "pastel pink", "yellow"), ("white", "lavender", "gold")],
        "expression": ["blank dreamy smile", "staring into space", "head tilted, mouth slightly open"],
        "pose": ["floating hand gestures", "hugging a strange plush", "looking up at the sky"],
        "body": [],
        "accessories": ["mismatched {accent} earrings", "odd {sub} hair clips", "small plush hanging from the bag"],
        "footwear": None,
    },
    "iinchou": {
        "jp": "委員長",
        "syn": ["委員長", "真面目", "優等生", "生徒会", "iinchou", "class rep", "serious", "honor student"],
        "design_jp": "眼鏡＋きっちり三つ編み＋腕章。紺×白で規律を記号化",
        "eyes": ["sharp eyes behind glasses", "serious eyes"],
        "hair_styles": ["twin braids", "neat bob with straight bangs", "low braided ponytail"],
        "hair_colors": ["black hair", "dark brown hair", "dark blue hair"],
        "palettes": [("navy", "white", "crimson"), ("white", "navy", "gold"), ("black", "white", "royal blue")],
        "expression": ["stern look", "pushing up glasses", "slight disapproving frown"],
        "pose": ["holding a clipboard", "arms crossed, pushing up glasses", "pointing with a finger"],
        "body": [],
        "accessories": ["glasses", "{sub} armband with {accent} lettering"],
        "footwear": None,
    },
    "ottori": {
        "jp": "おっとり",
        "syn": ["おっとり", "のんびり", "マイペース", "おだやか", "ottori", "laid-back", "easygoing"],
        "design_jp": "タレ目＋ゆるいウェーブ＋暖かい色。動きの少ないやわらかいポーズ",
        "eyes": ["soft tareme", "sleepy half-closed eyes"],
        "hair_styles": ["long loose wavy hair", "low side braid", "loose bun with loose strands"],
        "hair_colors": ["light brown hair", "platinum blonde hair", "pink hair", "blonde hair"],
        "palettes": [("cream", "brown", "pastel pink"), ("pastel pink", "white", "gold"), ("mint", "cream", "gold")],
        "expression": ["soft relaxed smile", "gentle smile with closed eyes", "yawning softly"],
        "pose": ["hand on cheek", "holding a teacup", "hands folded in lap"],
        "body": [],
        "accessories": ["{accent} flower hair clip", "soft {sub} scarf"],
        "footwear": None,
    },
    "nekketsu": {
        "jp": "熱血",
        "syn": ["熱血", "熱い", "根性", "nekketsu", "hot-blooded", "passionate"],
        "design_jp": "燃えるような目＋逆立つ髪＋赤×オレンジ。拳を握る力強いポーズ",
        "eyes": ["burning determined eyes", "sharp eyes with flame-like highlights"],
        "hair_styles": ["spiky short hair", "high ponytail with spiky bangs", "short messy hair with a headband"],
        "hair_colors": ["red hair", "orange hair", "black hair", "blonde hair"],
        "palettes": [("crimson", "orange", "gold"), ("black", "crimson", "yellow"), ("orange", "white", "black")],
        "expression": ["determined grin", "shouting with a fist raised", "fired-up expression"],
        "pose": ["clenched fist raised", "fighting stance", "pointing forward"],
        "body": ["athletic"],
        "accessories": ["{sub} headband", "{accent} wristbands", "bandage on the nose"],
        "footwear": None,
    },
    "dokuzetsu": {
        "jp": "毒舌",
        "syn": ["毒舌", "辛口", "皮肉", "dokuzetsu", "sharp-tongued", "sarcastic", "snarky"],
        "design_jp": "細めたジト目＋片眉を上げた顔＋寒色×黒。腕組みで距離感",
        "eyes": ["jitome", "half-closed eyes with a raised eyebrow"],
        "hair_styles": ["short bob", "long hair with a single side tail", "straight medium hair"],
        "hair_colors": ["black hair", "dark blue hair", "silver hair", "dark purple hair"],
        "palettes": [("black", "white", "sky blue"), ("navy", "gray", "crimson"), ("dark purple", "white", "silver")],
        "expression": ["deadpan stare", "smirk with a raised eyebrow", "sighing, unimpressed"],
        "pose": ["arms crossed", "hand on hip, leaning back", "shrug"],
        "body": [],
        "accessories": ["thin {accent} earring", "{sub} choker"],
        "footwear": None,
    },
    "aneki": {
        "jp": "姉御",
        "syn": ["姉御", "アネゴ", "姐さん", "姉貴", "番長", "aneki", "anego"],
        "design_jp": "長身＋鋭い目＋大きな笑い顔。黒×赤×金で貫禄",
        "eyes": ["sharp confident eyes", "narrowed eyes with a bold grin"],
        "hair_styles": ["long hair with pompadour bangs", "high ponytail", "long wavy hair swept back"],
        "hair_colors": ["black hair", "red hair", "blonde hair", "brown hair"],
        "palettes": [("black", "crimson", "gold"), ("crimson", "black", "white"), ("navy", "gold", "crimson")],
        "expression": ["bold confident grin", "laughing loudly", "cocky smirk"],
        "pose": ["hands on hips, chest out", "fist on hip, thumb pointing at self", "arms crossed, chin up"],
        "body": ["tall"],
        "accessories": ["{accent} earrings", "{main} jacket draped over the shoulders"],
        "footwear": None,
    },
}

# ---------------------------------------------------------------------------
# モチーフ（テーマ）
# ---------------------------------------------------------------------------
# features_primary  : 必ず入る「一目で分かる記号」の候補（1つ選ぶ）
# features_optional : 追加の記号（0〜2個選ぶ）
# palettes          : (main, sub, accent)
# patterns          : 服に使う模様の候補（多いほど良い。1体ごとに1つ選んでスタイル修飾を付ける）
# props             : シグネチャ小物候補
# classic_roles     : 王道の職業/服装系統   gap_roles : 意外性のある組み合わせ
# classic_arch      : 王道の性格            gap_arch  : 意外性のある性格
# hair_colors / eye_colors : モチーフらしい髪・瞳（瞳は特殊な瞳孔表現を含む）
# skin              : 肌の指定（省略時は fair skin）
# classic_jp / gap_jp : シートに書く設計意図

MOTIFS = {
    "demon": {
        "jp": "悪魔",
        "syn": ["悪魔", "デーモン", "デビル", "魔族", "魔物", "サキュバス", "淫魔", "魔王", "demon", "devil", "succubus", "imp", "demon lord"],
        "features_primary": ["{sub} curved demon horns", "small {main} demon horns with {accent} tips", "{accent} twisted demon horns"],
        "features_optional": ["small bat wings on the back, {main} membrane with {accent} edges", "{main} spade-tipped demon tail with {accent} tip", "slit pupils", "small fangs"],
        "palettes": [("black", "crimson", "gold"), ("dark purple", "black", "hot pink"), ("black", "hot pink", "white"), ("wine red", "black", "silver")],
        "patterns": ["bat-wing motif", "pentagram motif", "heart motif", "flame pattern", "chain motif", "devil-tail swirl pattern", "gothic cross pattern", "thorn vine pattern", "spade motif"],
        "props": ["small trident", "heart-shaped lollipop", "chained pendant with a {accent} gem"],
        "classic_roles": ["succubus", "gothic_lolita", "dancer", "bunny_girl", "demon_lord", "thief"],
        "gap_roles": ["sister", "shrine_miko", "school_uniform", "nurse", "idol", "maid", "teacher", "magical_girl", "office_lady", "saint", "pontiff", "hero", "waitress", "police"],
        "classic_arch": ["mesugaki", "oneesan", "sadistic", "tsundere", "jishinka"],
        "gap_arch": ["seiso", "uchiki", "amaama", "dojikko", "juujun", "okubyou"],
        "hair_colors": ["black hair", "dark purple hair", "red hair", "pink hair", "white hair"],
        "eye_colors": ["red eyes", "golden eyes", "magenta eyes"],
        "pupils": ["slit pupils"],
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
        "patterns": ["feather motif", "filigree motif", "cross pattern", "cloud motif", "halo ring motif", "lily motif", "dove motif", "stained-glass pattern", "star pattern"],
        "props": ["small golden harp", "holy book with a {accent} clasp", "glowing {accent} orb"],
        "classic_roles": ["sister", "princess_dress", "magical_girl", "idol", "saint", "goddess_dress", "pontiff"],
        "gap_roles": ["delinquent", "succubus", "military", "pirate", "casual_street", "gothic_lolita", "ninja", "thief", "demon_lord", "race_queen"],
        "classic_arch": ["seiso", "amaama", "dojikko", "uchiki", "juujun"],
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
        "patterns": ["rose motif", "bat-wing motif", "lace rose pattern", "cross pattern", "blood-drop motif", "thorn vine pattern", "gothic cross pattern", "damask pattern", "coffin motif"],
        "props": ["wine glass filled with red liquid", "black lace parasol with {accent} trim", "coffin-shaped bag"],
        "classic_roles": ["gothic_lolita", "princess_dress", "succubus", "dancer"],
        "gap_roles": ["school_uniform", "nurse", "idol", "sportswear", "swimsuit", "teacher", "chef", "police", "cheerleader"],
        "classic_arch": ["ojousama", "oneesan", "sadistic", "kuudere"],
        "gap_arch": ["dojikko", "genki", "uchiki", "amaama", "juujun"],
        "hair_colors": ["silver hair", "black hair", "platinum blonde hair", "dark red hair"],
        "eye_colors": ["red eyes", "red eyes", "golden eyes"],
        "pupils": ["slit pupils"],
        "skin": "pale skin",
        "classic_jp": "吸血鬼といえば黒×深紅の貴族——牙と青白い肌を記号にする",
        "gap_jp": "吸血鬼なのに{role}——夜の貴族を日常に放り込むギャップ設計",
    },
    "witch": {
        "kind": "theme",
        "jp": "魔女",
        "syn": ["魔女", "魔法使い", "魔術師", "ウィッチ", "witch", "wizard", "mage", "sorceress"],
        "features_primary": ["large pointed {main} witch hat with {accent} band and {sub} buckle", "wide-brimmed {main} witch hat with {accent} ribbon"],
        "features_optional": ["star and moon embroidery on the hem", "small black cat familiar sitting on the shoulder", "{accent} star-shaped earrings", "crescent moon brooch on the chest"],
        "palettes": [("black", "purple", "gold"), ("dark purple", "black", "orange"), ("navy", "gold", "white"), ("brown", "cream", "emerald green")],
        "patterns": ["star and moon motif", "rune pattern", "constellation motif", "spiral motif", "crescent moon motif", "cat silhouette motif", "potion bottle motif", "tarot card motif", "pentagram motif"],
        "props": [],
        "classic_roles": ["witch_robe", "gothic_lolita", "princess_dress", "steampunk", "merchant", "fortune_teller"],
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
        "patterns": ["paw print motif", "fish motif", "cat silhouette motif", "ribbon motif", "bell motif", "cat-ear silhouette motif", "yarn ball motif", "stripe pattern", "heart motif"],
        "props": ["{accent} bell collar", "fish-shaped plush", "ball of {accent} yarn"],
        "classic_roles": ["maid", "casual_street", "school_uniform", "loungewear", "bunny_girl", "waitress", "thief"],
        "gap_roles": ["knight", "military", "office_lady", "sister", "ninja", "pirate"],
        "classic_arch": ["mesugaki", "amaama", "genki", "kuudere"],
        "gap_arch": ["seiso", "ojousama", "sadistic", "chuuni"],
        "hair_colors": ["black hair", "white hair", "brown hair", "gray hair", "orange hair"],
        "eye_colors": ["golden eyes", "green eyes", "blue eyes", "heterochromia, golden and blue eyes"],
        "pupils": ["slit pupils"],
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
        "patterns": ["flame pattern", "wave pattern", "sakura pattern", "fox silhouette motif", "torii gate motif", "hemp-leaf pattern", "fox-fire motif", "paper talisman motif", "autumn leaf motif"],
        "props": ["fox mask worn on the side of the head", "paper talisman", "paper umbrella in {main} with {accent} rim"],
        "classic_roles": ["shrine_miko", "kimono", "witch_robe"],
        "gap_roles": ["office_lady", "idol", "school_uniform", "nurse", "military", "sportswear"],
        "classic_arch": ["oneesan", "kuudere", "ojousama", "sadistic"],
        "gap_arch": ["dojikko", "uchiki", "genki", "mesugaki"],
        "hair_colors": ["white hair", "blonde hair", "orange hair", "silver hair", "black hair"],
        "eye_colors": ["golden eyes", "red eyes", "amber eyes"],
        "pupils": ["slit pupils"],
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
        "patterns": ["claw-mark pattern", "moon motif", "tribal pattern", "fur trim", "paw print motif", "crescent moon motif", "fang motif", "plaid pattern", "pine tree motif"],
        "props": ["fur-lined cloak", "dog tag necklace", "bone-shaped hair clip"],
        "classic_roles": ["casual_street", "military", "knight", "ninja", "pirate", "archer", "hero", "thief"],
        "gap_roles": ["maid", "sister", "idol", "princess_dress", "loungewear", "nurse"],
        "classic_arch": ["bokukko", "genki", "tsundere", "kuudere"],
        "gap_arch": ["amaama", "uchiki", "seiso", "dojikko", "juujun"],
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
        "patterns": ["carrot motif", "moon motif", "polka-dot pattern", "clover motif", "star pattern", "heart motif", "ribbon motif", "radish motif", "egg motif"],
        "props": ["carrot plush", "pocket watch on a {accent} chain", "mochi-shaped plush"],
        "classic_roles": ["bunny_girl", "idol", "casual_street", "loungewear", "magical_girl"],
        "gap_roles": ["military", "knight", "office_lady", "ninja", "delinquent", "pirate"],
        "classic_arch": ["amaama", "genki", "dojikko", "uchiki", "okubyou"],
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
        "patterns": ["scale pattern", "dragon crest motif", "flame pattern", "eastern cloud pattern", "pearl orb motif", "lightning pattern", "claw-mark pattern", "wave pattern", "sun motif"],
        "props": ["glowing {accent} crystal orb", "oversized dragon-claw gauntlet", "pile of gold coins"],
        "classic_roles": ["knight", "cheongsam", "princess_dress", "kimono", "demon_lord", "samurai", "hero"],
        "gap_roles": ["office_lady", "school_uniform", "maid", "nurse", "loungewear", "idol"],
        "classic_arch": ["ojousama", "kuudere", "sadistic", "tsundere", "jishinka"],
        "gap_arch": ["dojikko", "amaama", "uchiki", "genki", "okubyou"],
        "hair_colors": ["white hair", "black hair", "silver hair", "blonde hair", "green hair"],
        "eye_colors": ["golden eyes", "red eyes", "green eyes"],
        "pupils": ["slit pupils"],
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
        "patterns": ["scale pattern", "wave pattern", "seashell motif", "bubble motif", "starfish motif", "coral motif", "pearl motif", "fish motif", "anchor motif"],
        "props": ["trident with a {accent} gem", "seashell purse", "pearl necklace"],
        "classic_roles": ["swimsuit", "idol", "princess_dress", "dancer"],
        "gap_roles": ["school_uniform", "office_lady", "knight", "military", "ninja", "teacher"],
        "classic_arch": ["seiso", "amaama", "dojikko", "oneesan"],
        "gap_arch": ["sadistic", "mesugaki", "chuuni", "bokukko", "jishinka"],
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
        "patterns": ["leaf motif", "flower pattern", "butterfly motif", "vine motif", "mushroom motif", "dewdrop motif", "star pattern", "four-leaf clover motif", "acorn motif"],
        "props": ["wand with a {accent} star tip", "flower basket", "acorn-shaped bag"],
        "classic_roles": ["magical_girl", "princess_dress", "idol", "loungewear"],
        "gap_roles": ["military", "office_lady", "gothic_lolita", "knight", "delinquent", "ninja"],
        "classic_arch": ["amaama", "genki", "dojikko", "uchiki", "okubyou"],
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
        "patterns": ["spiral motif", "faded hem pattern", "wisp motif", "moon motif", "candle flame motif", "lantern motif", "skull motif", "fog gradient pattern", "crescent moon motif"],
        "props": ["candle with a {accent} flame", "paper lantern", "old pocket mirror"],
        "classic_roles": ["kimono", "gothic_lolita", "school_uniform", "sister", "fortune_teller"],
        "gap_roles": ["idol", "gal_street", "sportswear", "swimsuit", "office_lady", "nurse"],
        "classic_arch": ["uchiki", "yandere", "kuudere", "seiso", "okubyou"],
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
        "patterns": ["circuit pattern", "hexagon pattern", "glowing line pattern", "barcode motif", "qr-code motif", "gear motif", "warning stripe pattern", "pixel pattern", "wireframe grid pattern"],
        "props": ["holographic display panel", "cable connector hanging from the neck", "energy core in the chest with {accent} glow"],
        "classic_roles": ["bodysuit", "military", "office_lady", "nurse", "police", "steampunk", "race_queen"],
        "gap_roles": ["maid", "shrine_miko", "kimono", "sister", "idol", "loungewear", "school_uniform"],
        "classic_arch": ["kuudere", "dojikko", "uchiki", "seiso", "juujun"],
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
        "patterns": ["tiger-stripe pattern", "eastern cloud pattern", "hemp-leaf pattern", "flame pattern", "kanabo club motif", "wave pattern", "checkered pattern", "sakura pattern", "thunder drum motif"],
        "props": ["oversized kanabo club", "sake gourd on a {accent} cord", "oni mask"],
        "classic_roles": ["kimono", "shrine_miko", "delinquent", "ninja", "samurai"],
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
        "patterns": ["skull motif", "bone pattern", "hourglass motif", "chain pattern", "scythe motif", "crow feather motif", "cross pattern", "spiderweb pattern", "candle motif"],
        "props": ["oversized scythe with a {accent} blade edge", "hourglass with {accent} sand", "black lantern"],
        "classic_roles": ["gothic_lolita", "witch_robe", "school_uniform", "sister", "thief", "pontiff"],
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
        "patterns": ["cloud motif", "polka-dot pattern", "star pattern", "ribbon motif", "sheep silhouette motif", "heart motif", "stripe pattern", "moon motif", "clover motif"],
        "props": ["small pillow", "sleep mask pushed up on the head", "oversized mug"],
        "classic_roles": ["loungewear", "casual_street", "gothic_lolita", "idol"],
        "gap_roles": ["military", "knight", "delinquent", "ninja", "office_lady", "pirate"],
        "classic_arch": ["amaama", "uchiki", "dojikko", "seiso", "juujun", "okubyou"],
        "gap_arch": ["sadistic", "mesugaki", "chuuni", "bokukko", "jishinka"],
        "hair_colors": ["platinum blonde hair", "white hair", "cream hair", "light brown hair"],
        "eye_colors": ["golden eyes", "brown eyes", "pink eyes"],
        "skin": None,
        "classic_jp": "羊といえばもこもこ——丸いシルエットと柔らかい色で安心感を出す",
        "gap_jp": "羊なのに{role}——のんびりした記号と鋭い服装のギャップ設計",
    },
    "star": {
        "kind": "theme",
        "jp": "星",
        "syn": ["星", "宇宙", "スター", "ギャラクシー", "星座", "star", "space", "galaxy", "cosmic"],
        "features_primary": ["star-shaped pupils", "hair with a galaxy gradient and {accent} sparkles"],
        "features_optional": ["{accent} star-shaped hair ornament", "star-shaped {accent} earrings", "star-shaped brooch on the chest", "star-print ribbons on the outfit"],
        "palettes": [("navy", "gold", "white"), ("dark purple", "sky blue", "gold"), ("black", "silver", "pastel pink")],
        "patterns": ["star pattern", "constellation motif", "crescent moon motif", "planet motif", "comet motif", "zodiac sign motif", "galaxy gradient pattern", "sparkle motif", "rocket motif"],
        "props": [],
        "classic_roles": ["magical_girl", "idol", "witch_robe", "princess_dress", "goddess_dress", "flight_attendant", "fortune_teller"],
        "gap_roles": ["school_uniform", "sportswear", "office_lady", "casual_street", "nurse", "knight"],
        "classic_arch": ["genki", "ojousama", "kuudere", "chuuni", "jishinka"],
        "gap_arch": ["uchiki", "jirai", "sadistic", "dojikko"],
        "hair_colors": ["dark blue hair", "purple hair", "silver hair", "blonde hair"],
        "eye_colors": ["golden eyes", "purple eyes", "blue eyes"],
        "skin": None,
        "classic_jp": "星といえばきらめき——紺×金と星の瞳で神秘的な華やかさを出す",
        "gap_jp": "星なのに{role}——夜空の記号と日常の服装のギャップ設計",
    },
    "flower": {
        "kind": "theme",
        "jp": "花",
        "syn": ["花", "フラワー", "植物", "薔薇", "桜", "flower", "floral", "rose", "sakura"],
        "features_primary": ["large {accent} flower hair ornament", "crown of {sub} flowers"],
        "features_optional": ["petal-shaped {accent} earrings", "flower corsage on the chest", "floral lace trim on the hem", "vine embroidery on the sleeves"],
        "palettes": [("white", "emerald green", "pastel pink"), ("crimson", "emerald green", "gold"), ("pastel pink", "white", "crimson"), ("lavender", "white", "gold")],
        "patterns": ["floral pattern", "leaf motif", "rose motif", "sakura pattern", "lily motif", "sunflower motif", "hydrangea pattern", "ivy pattern", "lavender motif", "tulip motif"],
        "props": [],
        "classic_roles": ["princess_dress", "kimono", "gothic_lolita", "idol", "goddess_dress", "waitress", "saint"],
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
        "kind": "theme",
        "jp": "道化",
        "syn": ["ピエロ", "道化", "クラウン", "ジョーカー", "clown", "jester", "joker", "harlequin"],
        "features_primary": ["{accent} teardrop facial mark under the left eye", "{main} and {sub} jester hat with {accent} bells"],
        "features_optional": ["{accent} bell earrings", "harlequin diamond pattern on the sleeves", "small {accent} bells sewn on the hem", "ruffled jester collar"],
        "palettes": [("purple", "gold", "black"), ("crimson", "white", "black"), ("black", "white", "crimson")],
        "patterns": ["diamond harlequin pattern", "checkered pattern", "playing-card suit motif", "star pattern", "mask motif", "spiral motif", "stripe pattern", "bell motif", "dice motif"],
        "props": [],
        "classic_roles": ["jester_outfit", "gothic_lolita", "idol", "dancer", "thief", "merchant", "fortune_teller"],
        "gap_roles": ["office_lady", "nurse", "sister", "school_uniform", "military", "teacher"],
        "classic_arch": ["mesugaki", "chuuni", "genki", "sadistic"],
        "gap_arch": ["kuudere", "seiso", "uchiki", "amaama"],
        "hair_colors": ["purple hair", "red hair", "white hair", "black hair"],
        "eye_colors": ["heterochromia, golden and purple eyes", "golden eyes", "red eyes"],
        "skin": None,
        "classic_jp": "道化といえばひし形模様と鈴——左右非対称の配色で不気味な楽しさを出す",
        "gap_jp": "道化なのに{role}——ふざけた記号と真面目な服装のギャップ設計",
    },
    "goddess": {
        "jp": "女神",
        "syn": ["女神", "神様", "goddess", "deity", "divine"],
        "features_primary": ["large {accent} glowing halo ring behind the head", "golden laurel crown with {accent} glow"],
        "features_optional": ["divine glowing aura", "feathers of light floating around", "glowing {accent} markings on the forehead", "floating slightly above the ground"],
        "palettes": [("white", "gold", "sky blue"), ("cream", "gold", "crimson"), ("white", "lavender", "gold"), ("gold", "white", "royal blue")],
        "patterns": ["laurel motif", "sun motif", "filigree motif", "feather motif", "olive branch motif", "greek key pattern", "dove motif", "star pattern", "wheat motif"],
        "props": ["golden staff with a {accent} orb", "overflowing golden chalice", "glowing scales of judgment"],
        "classic_roles": ["goddess_dress", "saint", "princess_dress", "pontiff"],
        "gap_roles": ["office_lady", "school_uniform", "sportswear", "casual_street", "delinquent", "merchant", "swimsuit", "waitress"],
        "classic_arch": ["seiso", "oneesan", "ojousama", "amaama", "ottori"],
        "gap_arch": ["mesugaki", "dojikko", "gal", "sadistic", "dokuzetsu"],
        "hair_colors": ["blonde hair", "white hair", "platinum blonde hair", "light blue hair"],
        "eye_colors": ["golden eyes", "blue eyes", "glowing white eyes"],
        "skin": None,
        "classic_jp": "女神といえば白×金の神々しさ——光輪と月桂冠で神格を記号化",
        "gap_jp": "女神なのに{role}——神格の記号と俗世の服装のギャップ設計",
    },
    "cow": {
        "jp": "乳牛",
        "syn": ["乳牛", "牛", "ホルスタイン", "牛娘", "cow", "holstein"],
        "features_primary": ["cow ears with {accent} ear tag, cow horns", "cow horns, cow ears"],
        "features_optional": ["cow tail", "{accent} cowbell collar", "cow print accents on the outfit"],
        "signature_print": "cow print",  # strict/full どちらでも必ず出す模様
        "palettes": [("white", "black", "pastel pink"), ("white", "black", "gold"), ("cream", "brown", "crimson")],
        "patterns": ["cow print", "cowbell motif", "milk bottle motif", "daisy motif", "clover motif", "polka-dot pattern", "gingham pattern", "grass motif"],
        "props": ["{accent} cowbell", "milk bottle", "bucket of milk"],
        "classic_roles": ["cow_suit", "swimsuit", "loungewear", "maid", "waitress"],
        "gap_roles": ["knight", "military", "office_lady", "sister", "ninja", "pontiff", "police"],
        "classic_arch": ["amaama", "oneesan", "dojikko", "ottori", "juujun"],
        "gap_arch": ["sadistic", "kuudere", "tsundere", "chuuni", "dokuzetsu"],
        "hair_colors": ["white hair", "black hair", "brown hair", "platinum blonde hair"],
        "eye_colors": ["brown eyes", "golden eyes", "blue eyes"],
        "skin": None,
        "body": ["large breasts"],
        "classic_jp": "乳牛といえば牛柄と鈴——白×黒の牛柄を1点に絞って記号化",
        "gap_jp": "乳牛なのに{role}——のどかな記号と硬い服装のギャップ設計",
    },
    "dog": {
        "jp": "犬",
        "syn": ["犬", "イヌ", "いぬ", "犬耳", "ワンコ", "dog", "inu", "puppy"],
        "features_primary": ["dog ears matching the hair color", "floppy dog ears matching the hair color"],
        "features_optional": ["fluffy dog tail matching the hair color, wagging", "{accent} dog collar with a tag", "small fang", "paw-print markings on the cheek"],
        "palettes": [("brown", "cream", "crimson"), ("white", "gold", "royal blue"), ("black", "white", "orange"), ("cream", "brown", "sky blue")],
        "patterns": ["paw print motif", "bone motif", "collar motif", "star pattern", "heart motif", "plaid pattern", "dog silhouette motif", "ball motif", "bone-and-collar pattern"],
        "props": ["bone-shaped plush", "frisbee", "{accent} leash held in the mouth"],
        "classic_roles": ["casual_street", "sportswear", "maid", "school_uniform", "police", "cheerleader"],
        "gap_roles": ["princess_dress", "gothic_lolita", "kimono", "succubus", "pontiff", "office_lady"],
        "classic_arch": ["genki", "amaama", "dojikko", "bokukko", "nekketsu", "juujun"],
        "gap_arch": ["kuudere", "sadistic", "ojousama", "jirai", "haraguro"],
        "hair_colors": ["brown hair", "blonde hair", "black hair", "white hair"],
        "eye_colors": ["brown eyes", "golden eyes", "blue eyes"],
        "skin": None,
        "classic_jp": "犬といえば忠実で元気——垂れ耳と振る尻尾、首輪で親しみやすさを記号化",
        "gap_jp": "犬なのに{role}——人懐っこい記号と気取った服装のギャップ設計",
    },
    "tiger": {
        "jp": "虎",
        "syn": ["虎", "トラ", "タイガー", "tiger"],
        "features_primary": ["tiger ears matching the hair color", "striped tiger ears with {accent} inner fur"],
        "features_optional": ["striped tiger tail", "small fangs", "tiger-stripe markings on the cheeks", "sharp claws"],
        "palettes": [("orange", "black", "white"), ("white", "black", "sky blue"), ("gold", "black", "crimson")],
        "patterns": ["tiger-stripe pattern", "claw-mark pattern", "flame pattern", "bamboo motif", "paw print motif", "sun motif", "wave pattern", "fang motif"],
        "props": ["oversized claw gauntlets", "{accent} paw-shaped bag", "meat on the bone"],
        "classic_roles": ["sportswear", "delinquent", "cheongsam", "samurai", "casual_street"],
        "gap_roles": ["maid", "sister", "loungewear", "office_lady", "waitress", "saint"],
        "classic_arch": ["genki", "nekketsu", "bokukko", "aneki", "tsundere", "jishinka"],
        "gap_arch": ["uchiki", "amaama", "seiso", "ottori", "fushigi", "okubyou"],
        "hair_colors": ["orange hair", "white hair", "blonde hair", "black hair"],
        "eye_colors": ["golden eyes", "amber eyes", "ice blue eyes"],
        "pupils": ["slit pupils"],
        "skin": None,
        "classic_jp": "虎といえば力強さ——縞模様と牙、オレンジ×黒で迫力を記号化",
        "gap_jp": "虎なのに{role}——猛獣の記号とおとなしい服装のギャップ設計",
    },
    "snake": {
        "jp": "蛇",
        "syn": ["蛇", "ヘビ", "へび", "ラミア", "蛇娘", "snake", "lamia", "serpent", "naga"],
        "features_primary": ["slit pupils with {accent} scale markings around the eyes", "snake scale markings on the cheeks and neck"],
        "features_optional": ["small snake fangs", "a small snake coiled around the arm", "{accent} scale pattern on the arms", "forked tongue"],
        "palettes": [("emerald green", "black", "gold"), ("dark purple", "black", "gold"), ("white", "gold", "emerald green")],
        "patterns": ["scale pattern", "serpent motif", "diamond pattern", "apple motif", "spiral motif", "moon motif", "hourglass motif", "thorn vine pattern"],
        "props": ["snake-shaped staff", "{accent} snake armlet", "glass vial of venom"],
        "classic_roles": ["dancer", "witch_robe", "cheongsam", "succubus", "goddess_dress", "fortune_teller"],
        "gap_roles": ["nurse", "school_uniform", "idol", "office_lady", "sister", "cheerleader"],
        "classic_arch": ["sadistic", "oneesan", "yandere", "kuudere", "haraguro"],
        "gap_arch": ["dojikko", "genki", "uchiki", "amaama", "ottori"],
        "hair_colors": ["green hair", "black hair", "purple hair", "white hair"],
        "eye_colors": ["golden eyes", "green eyes", "red eyes"],
        "pupils": ["slit pupils"],
        "skin": None,
        "classic_jp": "蛇といえば妖艶さ——縦長の瞳とうろこ、緑×黒×金で危うさを記号化",
        "gap_jp": "蛇なのに{role}——妖しい記号と健全な服装のギャップ設計",
    },
    "shark": {
        "jp": "鮫",
        "syn": ["鮫", "サメ", "さめ", "シャーク", "shark"],
        "features_primary": ["shark fin on the back", "shark tail with {accent} tip"],
        "features_optional": ["rows of sharp teeth grin", "gill markings on the neck", "small fins on the forearms", "shark-tooth necklace"],
        "palettes": [("sky blue", "white", "navy"), ("gray", "white", "crimson"), ("navy", "white", "hot pink")],
        "patterns": ["wave pattern", "shark-tooth pattern", "fish motif", "anchor motif", "stripe pattern", "bubble motif", "sun motif", "fin silhouette motif"],
        "props": ["shark-shaped plush", "surfboard", "{accent} water bottle"],
        "classic_roles": ["swimsuit", "sportswear", "casual_street", "bodysuit", "race_queen"],
        "gap_roles": ["sister", "princess_dress", "office_lady", "gothic_lolita", "kimono", "saint"],
        "classic_arch": ["genki", "mesugaki", "bokukko", "dojikko", "nekketsu"],
        "gap_arch": ["seiso", "ojousama", "uchiki", "kuudere", "ottori"],
        "hair_colors": ["light blue hair", "gray hair", "white hair", "dark blue hair"],
        "eye_colors": ["sharp blue eyes", "golden eyes", "dark eyes"],
        "skin": None,
        "classic_jp": "鮫といえば背びれとギザ歯——水色×白×紺で海の活発さを記号化",
        "gap_jp": "鮫なのに{role}——獰猛な記号と上品な服装のギャップ設計",
    },
    "harpy": {
        "jp": "鳥",
        "syn": ["鳥", "ハーピー", "ハーピィ", "鳥娘", "フクロウ", "鷹", "bird", "harpy", "owl", "hawk"],
        "features_primary": ["feathered wings on the back in {main} with {accent} tips", "feather-tipped ears"],
        "features_optional": ["bird tail feathers", "feathers floating around", "small feather tufts in the hair", "bird talon-shaped {accent} hair ornament"],
        "palettes": [("brown", "cream", "gold"), ("white", "sky blue", "gold"), ("black", "crimson", "gold"), ("orange", "white", "black")],
        "patterns": ["feather motif", "wing motif", "egg motif", "cloud motif", "star pattern", "nest motif", "arrow motif", "wind swirl pattern"],
        "props": ["egg-shaped bag", "feather quill", "small bird perched on the finger"],
        "classic_roles": ["dancer", "casual_street", "magical_girl", "archer", "goddess_dress"],
        "gap_roles": ["office_lady", "military", "nurse", "school_uniform", "chef", "police"],
        "classic_arch": ["genki", "dojikko", "kuudere", "uchiki", "fushigi"],
        "gap_arch": ["sadistic", "ojousama", "gal", "aneki"],
        "hair_colors": ["brown hair", "white hair", "black hair", "blonde hair"],
        "eye_colors": ["sharp golden eyes", "amber eyes", "blue eyes"],
        "skin": None,
        "classic_jp": "鳥といえば羽根——翼と羽飾りで軽やかさと自由さを記号化",
        "gap_jp": "鳥なのに{role}——自由な記号と拘束的な服装のギャップ設計",
    },
    "slime": {
        "jp": "スライム",
        "syn": ["スライム", "ゼリー", "ぷにぷに", "slime", "jelly", "goo"],
        "features_primary": [
            "slime {girl_or_boy}, monster {girl_or_boy}, translucent body, glowing {accent} core in the chest",
            "slime {girl_or_boy}, monster {girl_or_boy}, translucent gelatinous body, see-through body",
        ],
        "features_optional": ["dripping slime hair", "slime drops floating around", "bubbles inside the body", "glowing {accent} core visible in the chest"],
        "palettes": [("sky blue", "white", "royal blue"), ("mint", "white", "emerald green"), ("pastel pink", "white", "hot pink"), ("purple", "lavender", "gold")],
        "patterns": ["bubble motif", "droplet motif", "star pattern", "polka-dot pattern", "heart motif", "wave pattern", "jelly cube motif", "sparkle motif"],
        "props": ["slime-shaped plush", "{accent} crystal core", "jar of jelly"],
        "classic_roles": ["swimsuit", "loungewear", "casual_street", "bodysuit", "magical_girl"],
        "gap_roles": ["knight", "military", "office_lady", "sister", "teacher", "samurai"],
        "classic_arch": ["amaama", "dojikko", "ottori", "genki", "fushigi"],
        "gap_arch": ["sadistic", "kuudere", "chuuni", "mesugaki", "dokuzetsu"],
        "hair_colors": [],
        "hair_from_main": True,          # 髪色は必ずテーマカラー main（体と同色）
        "palette_only": True,            # 体色がテーマなので、性格・服装のパレットに引っ張られない
        "hair_extra": "translucent hair",
        "eye_colors": ["blue eyes", "green eyes", "hollow glowing eyes"],
        "skin": "{main} skin, colored skin, translucent skin",
        "classic_jp": "スライムといえば半透明——体・髪・肌を同じ色にして核で人外感、1色＋白で清涼感",
        "gap_jp": "スライムなのに{role}——ぷにぷにの記号と硬い服装のギャップ設計",
    },
    "yukionna": {
        "kind": "theme",
        "jp": "氷雪・雪女",
        "syn": ["雪女", "雪", "氷", "ゆきおんな", "氷雪", "snow", "ice", "yuki-onna", "frost"],
        "features_primary": ["ice crystal hair ornament with {accent} glow", "snowflake-shaped {accent} hair ornament"],
        "features_optional": ["icicle-shaped {accent} earrings", "snowflake embroidery on the hem", "white fur-trimmed collar", "crystal-like {accent} brooch"],
        "palettes": [("white", "sky blue", "silver"), ("navy", "white", "sky blue"), ("lavender", "white", "silver")],
        "patterns": ["snowflake pattern", "ice crystal motif", "frost pattern", "crescent moon motif", "plum blossom motif", "wave pattern", "crystal motif", "camellia motif"],
        "props": [],
        "classic_roles": ["kimono", "princess_dress", "gothic_lolita", "shrine_miko", "goddess_dress"],
        "gap_roles": ["swimsuit", "sportswear", "idol", "casual_street", "cheerleader", "race_queen"],
        "classic_arch": ["kuudere", "seiso", "yandere", "oneesan", "dokuzetsu"],
        "gap_arch": ["genki", "dojikko", "gal", "amaama", "nekketsu"],
        "hair_colors": ["white hair", "light blue hair", "silver hair"],
        "eye_colors": ["ice blue eyes", "silver eyes", "light blue eyes"],
        "skin": "pale skin",
        "classic_jp": "雪女といえば白と青白さ——雪の結晶と冷たい色で静けさを記号化",
        "gap_jp": "雪女なのに{role}——冷たい記号と熱い服装のギャップ設計",
    },
    "fire": {
        "kind": "theme",
        "jp": "炎",
        "syn": ["炎", "火", "ファイア", "炎属性", "fire", "flame", "blaze"],
        "features_primary": ["hair tips glowing like {accent} flames", "flame-shaped {accent} hair ornament"],
        "features_optional": ["flame embroidery along the hem", "ember-colored {accent} earrings", "flame-shaped brooch on the chest", "scorched hem with {accent} ember glow"],
        "palettes": [("crimson", "black", "gold"), ("orange", "black", "yellow"), ("black", "orange", "gold")],
        "patterns": ["flame pattern", "ember motif", "sun motif", "phoenix motif", "lightning pattern", "lava crack pattern", "sparkle motif", "smoke swirl pattern"],
        "props": [],
        "classic_roles": ["knight", "dancer", "shrine_miko", "ninja", "military", "hero"],
        "gap_roles": ["nurse", "office_lady", "maid", "loungewear", "sister", "flight_attendant"],
        "classic_arch": ["nekketsu", "genki", "tsundere", "aneki", "jishinka"],
        "gap_arch": ["kuudere", "uchiki", "seiso", "ottori", "fushigi"],
        "hair_colors": ["red hair", "orange hair", "black hair with red tips", "blonde hair"],
        "eye_colors": ["red eyes", "orange eyes", "golden eyes"],
        "skin": None,
        "classic_jp": "炎といえば赤×黒×金——燃える髪先と火の粉で熱さを記号化",
        "gap_jp": "炎なのに{role}——熱い記号と冷静な服装のギャップ設計",
    },
    "butterfly": {
        "kind": "theme",
        "jp": "蝶",
        "syn": ["蝶", "ちょうちょ", "バタフライ", "蛾", "butterfly", "moth"],
        "features_primary": ["large butterfly wings with {sub} and {accent} pattern", "small butterfly antennae"],
        "features_optional": ["{accent} butterfly hair ornament", "butterfly-wing-shaped earrings", "butterfly brooch on the chest", "butterfly embroidery on the hem"],
        "palettes": [("dark purple", "black", "gold"), ("sky blue", "white", "gold"), ("pastel pink", "white", "lavender"), ("black", "crimson", "gold")],
        "patterns": ["butterfly motif", "wing pattern", "scale pattern", "flower pattern", "lace pattern", "spiral motif", "star pattern", "leaf motif"],
        "props": [],
        "classic_roles": ["gothic_lolita", "dancer", "kimono", "princess_dress", "cheongsam"],
        "gap_roles": ["military", "office_lady", "sportswear", "school_uniform", "delinquent", "police"],
        "classic_arch": ["oneesan", "ojousama", "yandere", "seiso", "haraguro"],
        "gap_arch": ["genki", "bokukko", "mesugaki", "dojikko", "nekketsu"],
        "hair_colors": ["purple hair", "black hair", "blonde hair", "light blue hair"],
        "eye_colors": ["purple eyes", "golden eyes", "blue eyes"],
        "skin": None,
        "classic_jp": "蝶といえば華やかな羽——羽の模様を服の模様と揃えて統一感を出す",
        "gap_jp": "蝶なのに{role}——華やかな記号と無骨な服装のギャップ設計",
    },
    "zombie": {
        "jp": "ゾンビ",
        "syn": ["ゾンビ", "アンデッド", "屍", "zombie", "undead"],
        "features_primary": ["stitches across the cheek and arm", "bandages wrapped around one arm and one leg"],
        "features_optional": ["stitched seams on the limbs", "one eye glowing {accent}", "cracked skin markings", "name tag on the wrist"],
        "palettes": [("gray", "black", "crimson"), ("dark green", "black", "purple"), ("white", "gray", "crimson")],
        "patterns": ["stitch pattern", "skull motif", "bandage wrap pattern", "cross pattern", "bone pattern", "biohazard motif", "patchwork pattern", "tombstone motif"],
        "props": ["oversized bone", "stuffed bear with stitches", "shovel"],
        "classic_roles": ["school_uniform", "nurse", "loungewear", "gothic_lolita", "sister"],
        "gap_roles": ["idol", "office_lady", "cheerleader", "bunny_girl", "princess_dress", "race_queen"],
        "classic_arch": ["uchiki", "kuudere", "dojikko", "jirai", "fushigi", "okubyou"],
        "gap_arch": ["genki", "gal", "ojousama", "seiso", "nekketsu"],
        "hair_colors": ["gray hair", "pale green hair", "black hair", "white hair"],
        "eye_colors": ["hollow gray eyes", "glowing red eyes", "heterochromia, red and gray eyes"],
        "skin": "pale gray skin",
        "classic_jp": "ゾンビといえば縫い目と包帯——灰色の肌と光る片目で不死を記号化",
        "gap_jp": "ゾンビなのに{role}——朽ちた記号と華やかな服装のギャップ設計",
    },
    "elf": {
        "kind": "race",
        "jp": "エルフ",
        "syn": ["エルフ", "森人", "elf", "elven", "elvish"],
        "features_primary": ["long pointy ears", "pointy ears"],
        "features_optional": ["leaf-shaped {accent} earrings", "small flower hair ornament", "slender elegant build", "{accent} circlet"],
        "palettes": [("emerald green", "cream", "gold"), ("white", "emerald green", "gold"), ("sky blue", "white", "silver"), ("cream", "brown", "emerald green")],
        "patterns": ["leaf motif", "vine motif", "moon motif", "flower pattern", "star pattern", "filigree motif", "feather motif", "acorn motif"],
        "props": ["elegant longbow", "ancient spell book", "glowing crystal pendant"],
        "classic_roles": ["archer", "witch_robe", "princess_dress", "goddess_dress", "hero", "fortune_teller"],
        "gap_roles": ["office_lady", "school_uniform", "police", "race_queen", "nurse", "delinquent", "casual_street"],
        "classic_arch": ["seiso", "kuudere", "ojousama", "ottori", "iinchou"],
        "gap_arch": ["gal", "mesugaki", "genki", "nekketsu", "dojikko"],
        "hair_colors": ["blonde hair", "platinum blonde hair", "silver hair", "green hair"],
        "eye_colors": ["green eyes", "blue eyes", "golden eyes"],
        "skin": None,
        "classic_jp": "エルフといえば長い耳と気品——緑×金と森の意匠で高貴さを記号化",
        "gap_jp": "エルフなのに{role}——高貴な記号と俗な服装のギャップ設計",
    },
    "dark_elf": {
        "kind": "race",
        "jp": "ダークエルフ",
        "syn": ["ダークエルフ", "褐色エルフ", "dark elf", "drow"],
        "features_primary": ["long pointy ears", "pointy ears"],
        "features_optional": ["{accent} tribal armlet", "silver circlet", "{accent} ear cuffs", "white eyelashes"],
        "palettes": [("dark purple", "black", "silver"), ("black", "crimson", "gold"), ("navy", "white", "silver"), ("white", "dark purple", "gold")],
        "patterns": ["spider web pattern", "moon motif", "thorn vine pattern", "tribal pattern", "star pattern", "scale pattern", "crescent moon motif", "diamond pattern"],
        "props": ["curved dagger", "poison vial", "dark crystal staff"],
        "classic_roles": ["dancer", "thief", "archer", "succubus", "witch_robe", "demon_lord"],
        "gap_roles": ["sister", "school_uniform", "maid", "nurse", "office_lady", "waitress", "saint"],
        "classic_arch": ["sadistic", "oneesan", "kuudere", "dokuzetsu", "jishinka"],
        "gap_arch": ["dojikko", "amaama", "uchiki", "okubyou", "juujun"],
        "hair_colors": ["white hair", "silver hair", "lavender hair", "platinum blonde hair"],
        "eye_colors": ["red eyes", "purple eyes", "golden eyes"],
        "skin": "dark skin",
        "classic_jp": "ダークエルフといえば褐色の肌と白髪——黒×紫×銀で妖艶さを記号化",
        "gap_jp": "ダークエルフなのに{role}——妖艶な記号と清潔な服装のギャップ設計",
    },
    "dwarf": {
        "kind": "race",
        "jp": "ドワーフ",
        "syn": ["ドワーフ", "dwarf", "dwarven"],
        "features_primary": ["short sturdy build", "round rosy cheeks"],
        "features_optional": ["braided hair with {accent} beads", "leather tool belt", "soot smudge on the cheek", "{accent} goggles on the head"],
        "palettes": [("brown", "crimson", "gold"), ("orange", "brown", "gold"), ("gray", "crimson", "silver"), ("olive green", "brown", "gold")],
        "patterns": ["gear motif", "rune pattern", "anvil motif", "plaid pattern", "hammer motif", "chain pattern", "checkered pattern", "flame pattern"],
        "props": ["oversized war hammer", "tankard of ale", "pouch of gemstones"],
        "classic_roles": ["steampunk", "merchant", "knight", "casual_street", "chef"],
        "gap_roles": ["idol", "princess_dress", "flight_attendant", "race_queen", "goddess_dress", "bunny_girl"],
        "classic_arch": ["nekketsu", "aneki", "genki", "bokukko", "jishinka"],
        "gap_arch": ["seiso", "ojousama", "uchiki", "fushigi"],
        "hair_colors": ["red hair", "brown hair", "blonde hair", "orange hair"],
        "eye_colors": ["brown eyes", "green eyes", "golden eyes"],
        "skin": None,
        "body": ["petite"],
        "classic_jp": "ドワーフといえば小柄で頑丈——茶×紅×金と工具で職人気質を記号化",
        "gap_jp": "ドワーフなのに{role}——無骨な記号と華やかな服装のギャップ設計",
    },
    "goblin": {
        "kind": "race",
        "jp": "ゴブリン",
        "syn": ["ゴブリン", "小鬼", "goblin"],
        "features_primary": ["long pointy ears", "small fangs, long pointy ears"],
        "features_optional": ["small fangs", "{accent} bone hair ornament", "mischievous grin"],
        "palettes": [("emerald green", "brown", "gold"), ("olive green", "black", "crimson"), ("brown", "emerald green", "gold")],
        "patterns": ["skull motif", "bone pattern", "coin motif", "patchwork pattern", "claw-mark pattern", "tribal pattern", "star pattern", "stripe pattern"],
        "props": ["sack of loot", "rusty dagger", "stolen golden goblet"],
        "classic_roles": ["thief", "merchant", "casual_street", "pirate", "archer"],
        "gap_roles": ["idol", "sister", "princess_dress", "office_lady", "flight_attendant", "saint"],
        "classic_arch": ["mesugaki", "genki", "dokuzetsu", "haraguro"],
        "gap_arch": ["seiso", "ojousama", "juujun", "okubyou"],
        "hair_colors": ["green hair", "black hair", "red hair", "brown hair"],
        "eye_colors": ["yellow eyes", "red eyes", "golden eyes"],
        "skin": "green skin, colored skin",
        "body": ["petite"],
        "classic_jp": "ゴブリンといえば小柄で悪戯好き——緑の肌と尖った耳、戦利品で記号化",
        "gap_jp": "ゴブリンなのに{role}——悪戯な記号と上品な服装のギャップ設計",
    },
    "doll": {
        "kind": "race",
        "jp": "人形",
        "syn": ["人形", "ドール", "球体関節", "doll", "puppet", "marionette"],
        "features_primary": ["ball-jointed doll, visible doll joints", "doll joints"],
        "features_optional": ["glass-like eyes", "keyhole on the back", "marionette strings", "{accent} ribbon tied at the neck joint"],
        "palettes": [("white", "pastel pink", "gold"), ("black", "white", "crimson"), ("lavender", "white", "silver"), ("cream", "wine red", "gold")],
        "patterns": ["lace pattern", "ribbon motif", "rose motif", "checkered pattern", "heart motif", "key motif", "filigree motif", "polka-dot pattern"],
        "props": ["wind-up key", "tiny teacup", "music box"],
        "classic_roles": ["gothic_lolita", "princess_dress", "maid", "loungewear", "waitress"],
        "gap_roles": ["military", "sportswear", "police", "bodysuit", "delinquent", "race_queen"],
        "classic_arch": ["kuudere", "fushigi", "seiso", "juujun", "yandere"],
        "gap_arch": ["genki", "gal", "nekketsu", "aneki"],
        "hair_colors": ["platinum blonde hair", "black hair", "pink hair", "silver hair"],
        "eye_colors": ["glass-like blue eyes", "glass-like red eyes", "glass-like golden eyes"],
        "skin": "pale skin, porcelain skin",
        "classic_jp": "人形といえば球体関節と硝子の瞳——陶器の肌とレースで作り物の美を記号化",
        "gap_jp": "人形なのに{role}——静的な記号と活動的な服装のギャップ設計",
    },
    "alien": {
        "kind": "race",
        "jp": "宇宙人",
        "syn": ["宇宙人", "エイリアン", "異星人", "alien", "extraterrestrial"],
        "features_primary": ["small antennae on the head", "antennae"],
        "features_optional": ["pointy ears", "{accent} glowing eyes", "small floating ufo companion", "third eye"],
        "palettes": [("mint", "white", "hot pink"), ("lavender", "white", "sky blue"), ("sky blue", "white", "yellow"), ("emerald green", "black", "hot pink")],
        "patterns": ["star pattern", "planet motif", "ufo motif", "hexagon pattern", "galaxy gradient pattern", "circuit pattern", "polka-dot pattern", "wave pattern"],
        "props": ["ray gun", "small floating ufo", "glowing orb"],
        "classic_roles": ["bodysuit", "casual_street", "idol", "swimsuit", "magical_girl"],
        "gap_roles": ["kimono", "shrine_miko", "sister", "samurai", "merchant", "teacher"],
        "classic_arch": ["fushigi", "kuudere", "genki", "dojikko"],
        "gap_arch": ["aneki", "nekketsu", "seiso", "ojousama"],
        "hair_colors": [],
        "hair_from_main": True,
        "palette_only": True,
        "eye_colors": ["glowing eyes", "black eyes", "large black eyes"],
        "skin": "{main} skin, colored skin",
        "classic_jp": "宇宙人といえば触角と異色の肌——髪・肌を1色に揃えて人外感を記号化",
        "gap_jp": "宇宙人なのに{role}——異星の記号と和の服装のギャップ設計",
    },
    "mouse": {
        "kind": "race",
        "jp": "ネズミ",
        "syn": ["ネズミ", "鼠", "ねずみ", "ハムスター", "mouse", "rat", "hamster"],
        "features_primary": ["round mouse ears matching the hair color"],
        "features_optional": ["thin mouse tail", "buck teeth", "small fang", "{accent} ear ribbon"],
        "palettes": [("gray", "white", "pastel pink"), ("brown", "cream", "crimson"), ("white", "pastel pink", "gold")],
        "patterns": ["cheese motif", "polka-dot pattern", "heart motif", "sunflower motif", "star pattern", "ribbon motif", "gingham pattern", "paw print motif"],
        "props": ["wedge of cheese", "handful of sunflower seeds", "acorn"],
        "classic_roles": ["casual_street", "loungewear", "maid", "school_uniform", "waitress"],
        "gap_roles": ["military", "knight", "office_lady", "police", "demon_lord", "pontiff"],
        "classic_arch": ["uchiki", "dojikko", "okubyou", "amaama"],
        "gap_arch": ["sadistic", "aneki", "jishinka", "nekketsu"],
        "hair_colors": ["gray hair", "brown hair", "white hair"],
        "eye_colors": ["red eyes", "black eyes", "brown eyes"],
        "skin": None,
        "body": ["petite"],
        "classic_jp": "ネズミといえば小さくて臆病——丸い耳と細い尻尾で可愛らしさを記号化",
        "gap_jp": "ネズミなのに{role}——小動物の記号と強い服装のギャップ設計",
    },
    "bear": {
        "kind": "race",
        "jp": "クマ",
        "syn": ["クマ", "熊", "くま", "bear"],
        "features_primary": ["round bear ears matching the hair color"],
        "features_optional": ["small bear tail", "sharp claws", "thick fur collar", "bear paw gloves"],
        "palettes": [("brown", "cream", "crimson"), ("white", "sky blue", "gold"), ("black", "white", "orange")],
        "patterns": ["paw print motif", "honey motif", "forest motif", "plaid pattern", "star pattern", "fish motif", "heart motif", "polka-dot pattern"],
        "props": ["jar of honey", "oversized salmon", "bear plush"],
        "classic_roles": ["casual_street", "loungewear", "hero", "merchant", "chef"],
        "gap_roles": ["idol", "bunny_girl", "flight_attendant", "office_lady", "race_queen", "goddess_dress"],
        "classic_arch": ["ottori", "amaama", "aneki", "nekketsu"],
        "gap_arch": ["kuudere", "mesugaki", "haraguro", "dokuzetsu"],
        "hair_colors": ["brown hair", "black hair", "white hair"],
        "eye_colors": ["brown eyes", "black eyes", "golden eyes"],
        "skin": None,
        "classic_jp": "クマといえば大らかさ——丸い耳と蜂蜜、暖かい茶色で安心感を記号化",
        "gap_jp": "クマなのに{role}——のんびりした記号と華やかな服装のギャップ設計",
    },
    "deer": {
        "kind": "race",
        "jp": "鹿",
        "syn": ["鹿", "シカ", "しか", "トナカイ", "deer", "reindeer"],
        "features_primary": ["deer antlers", "small deer antlers with {accent} ornaments"],
        "features_optional": ["deer ears", "short deer tail", "{accent} bell on the antlers"],
        "palettes": [("brown", "cream", "gold"), ("white", "emerald green", "gold"), ("crimson", "cream", "gold")],
        "patterns": ["leaf motif", "snowflake pattern", "holly motif", "star pattern", "plaid pattern", "pine tree motif", "acorn motif", "flower pattern"],
        "props": ["lantern", "basket of berries", "sprig of holly"],
        "classic_roles": ["shrine_miko", "kimono", "goddess_dress", "archer", "saint"],
        "gap_roles": ["military", "police", "race_queen", "delinquent", "bodysuit"],
        "classic_arch": ["seiso", "ottori", "uchiki", "okubyou"],
        "gap_arch": ["sadistic", "gal", "mesugaki", "aneki"],
        "hair_colors": ["brown hair", "platinum blonde hair", "white hair"],
        "eye_colors": ["brown eyes", "golden eyes", "green eyes"],
        "skin": None,
        "classic_jp": "鹿といえば角と静けさ——枝角と森の色で神聖さを記号化",
        "gap_jp": "鹿なのに{role}——静かな記号と騒がしい服装のギャップ設計",
    },
    "horse": {
        "kind": "race",
        "jp": "馬",
        "syn": ["馬", "ウマ", "うま", "馬娘", "horse"],
        "features_primary": ["horse ears matching the hair color"],
        "features_optional": ["long horse tail matching the hair color", "{accent} ear ribbon", "{accent} horseshoe hair ornament"],
        "palettes": [("navy", "white", "gold"), ("brown", "white", "crimson"), ("black", "white", "gold"), ("crimson", "white", "gold")],
        "patterns": ["horseshoe motif", "star pattern", "stripe pattern", "clover motif", "checkered pattern", "carrot motif", "diamond pattern", "laurel motif"],
        "props": ["trophy", "carrot", "horseshoe charm"],
        "classic_roles": ["sportswear", "race_queen", "cheerleader", "idol", "school_uniform", "knight"],
        "gap_roles": ["sister", "gothic_lolita", "pontiff", "loungewear", "fortune_teller"],
        "classic_arch": ["genki", "nekketsu", "jishinka", "kuudere", "iinchou"],
        "gap_arch": ["uchiki", "okubyou", "jirai", "fushigi"],
        "hair_colors": ["brown hair", "black hair", "white hair", "blonde hair"],
        "eye_colors": ["brown eyes", "blue eyes", "golden eyes"],
        "skin": None,
        "body": ["tall", "athletic"],
        "classic_jp": "馬といえば駿足と気高さ——耳と長い尻尾、紺×白×金で競技者感を記号化",
        "gap_jp": "馬なのに{role}——躍動の記号と静かな服装のギャップ設計",
    },
    "bee": {
        "kind": "race",
        "jp": "蜂",
        "syn": ["蜂", "ハチ", "はち", "ミツバチ", "bee", "hornet", "wasp"],
        "features_primary": ["small translucent insect wings", "bee antennae, insect wings"],
        "features_optional": ["bee stinger", "black and yellow striped accents", "fluffy fur collar"],
        "palettes": [("yellow", "black", "gold"), ("black", "yellow", "white"), ("cream", "yellow", "brown")],
        "patterns": ["honeycomb pattern", "stripe pattern", "flower pattern", "honey motif", "hexagon pattern", "sunflower motif", "polka-dot pattern", "heart motif"],
        "props": ["jar of honey", "large flower", "honey dipper"],
        "classic_roles": ["idol", "cheerleader", "swimsuit", "magical_girl", "waitress"],
        "gap_roles": ["sister", "military", "samurai", "office_lady", "knight"],
        "classic_arch": ["genki", "mesugaki", "nekketsu", "amaama"],
        "gap_arch": ["uchiki", "ottori", "kuudere", "okubyou"],
        "hair_colors": ["blonde hair", "black hair", "black hair with yellow streaks"],
        "eye_colors": ["golden eyes", "black eyes", "amber eyes"],
        "skin": None,
        "classic_jp": "蜂といえば黄×黒の縞——触角と羽で働き者の元気さを記号化",
        "gap_jp": "蜂なのに{role}——せわしない記号と静かな服装のギャップ設計",
    },
    "spider": {
        "kind": "race",
        "jp": "蜘蛛",
        "syn": ["蜘蛛", "クモ", "くも", "アラクネ", "spider", "arachne"],
        "features_primary": ["small spider legs extending from the back", "spider-leg-shaped hair ornaments"],
        "features_optional": ["spiderweb accents", "{accent} spider pendant", "sharp fangs", "silk thread trailing from the fingers"],
        "palettes": [("black", "purple", "silver"), ("black", "crimson", "white"), ("dark purple", "black", "gold")],
        "patterns": ["spiderweb pattern", "skull motif", "lace pattern", "diamond pattern", "thorn vine pattern", "moon motif", "chain pattern", "star pattern"],
        "props": ["spider plush", "spool of silk thread", "lantern"],
        "classic_roles": ["gothic_lolita", "witch_robe", "succubus", "dancer", "fortune_teller"],
        "gap_roles": ["nurse", "school_uniform", "idol", "cheerleader", "waitress", "flight_attendant"],
        "classic_arch": ["sadistic", "haraguro", "yandere", "kuudere"],
        "gap_arch": ["dojikko", "amaama", "okubyou", "genki"],
        "hair_colors": ["black hair", "purple hair", "white hair"],
        "eye_colors": ["red eyes", "purple eyes", "glowing red eyes"],
        "skin": "pale skin",
        "classic_jp": "蜘蛛といえば糸と巣——黒×紫と蜘蛛の脚で妖しさを記号化",
        "gap_jp": "蜘蛛なのに{role}——妖しい記号と健全な服装のギャップ設計",
    },
    "bat": {
        "kind": "race",
        "jp": "コウモリ",
        "syn": ["コウモリ", "蝙蝠", "こうもり", "bat"],
        "features_primary": ["bat-wing-shaped ears", "bat ears"],
        "features_optional": ["small bat wings on the back", "small fangs", "bat-shaped {accent} hair ornament"],
        "palettes": [("black", "purple", "crimson"), ("dark purple", "black", "hot pink"), ("navy", "black", "gold")],
        "patterns": ["bat-wing motif", "moon motif", "star pattern", "crescent moon motif", "polka-dot pattern", "heart motif", "spiderweb pattern", "stripe pattern"],
        "props": ["lollipop", "sleep mask", "tiny lantern"],
        "classic_roles": ["gothic_lolita", "loungewear", "casual_street", "succubus", "jester_outfit"],
        "gap_roles": ["nurse", "idol", "police", "cheerleader", "flight_attendant"],
        "classic_arch": ["jirai", "mesugaki", "uchiki", "fushigi"],
        "gap_arch": ["seiso", "genki", "jishinka", "iinchou"],
        "hair_colors": ["black hair", "purple hair", "dark purple hair"],
        "eye_colors": ["red eyes", "golden eyes", "purple eyes"],
        "skin": None,
        "classic_jp": "コウモリといえば夜行性——大きな耳と小さな翼、黒×紫で夜の雰囲気を記号化",
        "gap_jp": "コウモリなのに{role}——夜の記号と昼の服装のギャップ設計",
    },
    "tanuki": {
        "kind": "race",
        "jp": "狸",
        "syn": ["狸", "たぬき", "タヌキ", "アライグマ", "tanuki", "raccoon"],
        "features_primary": ["tanuki ears matching the hair color", "raccoon ears matching the hair color"],
        "features_optional": ["striped bushy tanuki tail", "leaf on the head", "{accent} ear ribbon"],
        "palettes": [("brown", "cream", "gold"), ("olive green", "brown", "gold"), ("gray", "cream", "crimson")],
        "patterns": ["leaf motif", "polka-dot pattern", "hemp-leaf pattern", "wave pattern", "sakura pattern", "stripe pattern", "acorn motif", "coin motif"],
        "props": ["leaf", "sake gourd", "straw hat"],
        "classic_roles": ["kimono", "shrine_miko", "merchant", "casual_street", "waitress"],
        "gap_roles": ["military", "police", "flight_attendant", "bodysuit", "knight"],
        "classic_arch": ["ottori", "dojikko", "genki", "haraguro"],
        "gap_arch": ["sadistic", "kuudere", "iinchou", "jishinka"],
        "hair_colors": ["brown hair", "dark brown hair", "gray hair"],
        "eye_colors": ["brown eyes", "golden eyes", "black eyes"],
        "skin": None,
        "classic_jp": "狸といえば化けと和の愛嬌——縞の尻尾と葉っぱでとぼけた可愛さを記号化",
        "gap_jp": "狸なのに{role}——とぼけた記号と規律的な服装のギャップ設計",
    },
    "dullahan": {
        "kind": "race",
        "jp": "デュラハン",
        "syn": ["デュラハン", "首なし", "dullahan", "headless"],
        "features_primary": ["dullahan, holding own head under the arm", "dullahan, severed head floating beside the body"],
        "features_optional": ["{accent} flames rising from the neck", "{accent} glowing eyes", "ornate {accent} neck brace"],
        "palettes": [("black", "crimson", "silver"), ("navy", "black", "gold"), ("dark purple", "black", "silver")],
        "patterns": ["skull motif", "cross pattern", "chain pattern", "thorn vine pattern", "flame pattern", "moon motif", "star pattern", "filigree motif"],
        "props": ["lance", "lantern", "black horse plush"],
        "classic_roles": ["knight", "military", "gothic_lolita", "princess_dress", "demon_lord"],
        "gap_roles": ["idol", "school_uniform", "maid", "nurse", "office_lady", "cheerleader"],
        "classic_arch": ["kuudere", "seiso", "dojikko", "iinchou"],
        "gap_arch": ["genki", "gal", "mesugaki", "amaama"],
        "hair_colors": ["black hair", "white hair", "silver hair"],
        "eye_colors": ["red eyes", "golden eyes", "glowing blue eyes"],
        "skin": "pale skin",
        "classic_jp": "デュラハンといえば抱えた首——騎士の装いと黒×紅で不吉な気品を記号化",
        "gap_jp": "デュラハンなのに{role}——不吉な記号と日常の服装のギャップ設計",
    },
    "moon": {
        "kind": "theme",
        "jp": "月",
        "syn": ["月", "ムーン", "三日月", "moon", "lunar", "crescent"],
        "features_primary": [],
        "features_optional": ["crescent moon hair ornament in {accent}", "moon-shaped {accent} earrings", "crescent moon embroidery on the hem", "crescent moon pendant"],
        "palettes": [("navy", "white", "gold"), ("dark purple", "silver", "white"), ("black", "gold", "white")],
        "patterns": ["crescent moon motif", "moon print", "star pattern", "constellation motif", "cloud motif", "rabbit motif", "filigree motif", "night sky gradient pattern"],
        "props": [],
        "classic_roles": ["witch_robe", "princess_dress", "goddess_dress", "kimono"],
        "gap_roles": [],
        "classic_arch": ["kuudere", "seiso", "oneesan", "fushigi"],
        "gap_arch": [],
        "hair_colors": ["silver hair", "white hair", "dark blue hair"],
        "eye_colors": ["golden eyes", "silver eyes"],
        "skin": None,
        "classic_jp": "月——紺×金×銀と三日月で静かな神秘性を添える",
        "gap_jp": "月——静かな記号を{role}に添える",
    },
    "sun": {
        "kind": "theme",
        "jp": "太陽",
        "syn": ["太陽", "サン", "日輪", "sun", "solar", "sunny"],
        "features_primary": [],
        "features_optional": ["sun-shaped {accent} hair ornament", "sun-shaped {accent} brooch on the chest", "sun embroidery on the hem", "sunburst-shaped earrings"],
        "palettes": [("orange", "gold", "white"), ("crimson", "gold", "white"), ("yellow", "white", "orange")],
        "patterns": ["sun motif", "sunflower motif", "ray pattern", "flame pattern", "star pattern", "sunrise gradient pattern", "laurel motif", "wheat motif"],
        "props": [],
        "classic_roles": ["goddess_dress", "idol", "cheerleader", "swimsuit", "shrine_miko"],
        "gap_roles": [],
        "classic_arch": ["genki", "nekketsu", "jishinka", "amaama"],
        "gap_arch": [],
        "hair_colors": ["blonde hair", "orange hair", "red hair"],
        "eye_colors": ["golden eyes", "orange eyes"],
        "skin": None,
        "classic_jp": "太陽——橙×金と光輪で明るさと力強さを添える",
        "gap_jp": "太陽——明るい記号を{role}に添える",
    },
    "thunder": {
        "kind": "theme",
        "jp": "雷",
        "syn": ["雷", "サンダー", "電気", "thunder", "lightning", "electric", "electricity"],
        "features_primary": [],
        "features_optional": ["lightning-bolt-shaped {accent} hair ornament", "lightning-bolt embroidery along the sleeves", "lightning-shaped {accent} brooch", "lightning-bolt earrings"],
        "palettes": [("yellow", "black", "white"), ("navy", "yellow", "white"), ("purple", "yellow", "black")],
        "patterns": ["lightning pattern", "zigzag pattern", "star pattern", "cloud motif", "drum motif", "stripe pattern", "spark motif", "checkered pattern"],
        "props": [],
        "classic_roles": ["shrine_miko", "bodysuit", "sportswear", "hero", "magical_girl"],
        "gap_roles": [],
        "classic_arch": ["genki", "nekketsu", "tsundere", "bokukko"],
        "gap_arch": [],
        "hair_colors": ["blonde hair", "black hair with yellow streaks", "light blue hair"],
        "eye_colors": ["yellow eyes", "blue eyes"],
        "skin": None,
        "classic_jp": "雷——黄×黒と稲妻で勢いと速さを添える",
        "gap_jp": "雷——勢いのある記号を{role}に添える",
    },
    "ocean": {
        "kind": "theme",
        "jp": "海",
        "syn": ["海", "オーシャン", "波", "マリン", "ocean", "sea", "marine", "nautical"],
        "features_primary": [],
        "features_optional": ["seashell hair ornament", "coral hair ornament", "wave embroidery on the hem", "anchor-shaped {accent} earrings"],
        "palettes": [("navy", "white", "gold"), ("sky blue", "white", "crimson"), ("teal", "white", "gold")],
        "patterns": ["wave pattern", "anchor motif", "seashell motif", "stripe pattern", "starfish motif", "fish motif", "bubble motif", "compass motif"],
        "props": [],
        "classic_roles": ["swimsuit", "school_uniform", "pirate", "idol", "flight_attendant"],
        "gap_roles": [],
        "classic_arch": ["genki", "seiso", "bokukko", "ottori"],
        "gap_arch": [],
        "hair_colors": ["light blue hair", "dark blue hair", "white hair"],
        "eye_colors": ["blue eyes", "teal eyes"],
        "skin": None,
        "classic_jp": "海——紺×白×金と波・錨で爽やかさを添える",
        "gap_jp": "海——爽やかな記号を{role}に添える",
    },
    "forest": {
        "kind": "theme",
        "jp": "森",
        "syn": ["森", "フォレスト", "自然", "forest", "nature", "woodland"],
        "features_primary": [],
        "features_optional": ["leaf hair ornament", "small vines wrapped around the arm", "mushroom hair ornament", "leaf embroidery on the collar"],
        "palettes": [("emerald green", "brown", "gold"), ("olive green", "cream", "crimson"), ("dark green", "white", "gold")],
        "patterns": ["leaf motif", "vine motif", "mushroom motif", "acorn motif", "pine tree motif", "flower pattern", "wood grain pattern", "fern motif"],
        "props": [],
        "classic_roles": ["archer", "witch_robe", "merchant", "hero", "goddess_dress"],
        "gap_roles": [],
        "classic_arch": ["ottori", "seiso", "uchiki", "genki"],
        "gap_arch": [],
        "hair_colors": ["green hair", "brown hair", "blonde hair"],
        "eye_colors": ["green eyes", "brown eyes"],
        "skin": None,
        "classic_jp": "森——緑×茶×金と葉・蔦で自然の穏やかさを添える",
        "gap_jp": "森——自然の記号を{role}に添える",
    },
    "sweets": {
        "kind": "theme",
        "jp": "お菓子",
        "syn": ["お菓子", "スイーツ", "キャンディ", "ケーキ", "チョコ", "苺", "sweets", "candy", "cake", "chocolate", "strawberry"],
        "features_primary": [],
        "features_optional": ["candy-shaped {accent} hair ornament", "strawberry hair ornament", "cherry-shaped earrings", "whipped-cream-like frills on the collar", "candy-print ribbons on the outfit"],
        "palettes": [("pastel pink", "white", "crimson"), ("cream", "brown", "pastel pink"), ("mint", "white", "hot pink")],
        "patterns": ["strawberry motif", "candy motif", "polka-dot pattern", "heart motif", "cherry motif", "macaron motif", "gingham pattern", "star pattern"],
        "props": [],
        "classic_roles": ["maid", "idol", "waitress", "loungewear", "gothic_lolita", "chef"],
        "gap_roles": [],
        "classic_arch": ["amaama", "dojikko", "genki", "mesugaki"],
        "gap_arch": [],
        "hair_colors": ["pink hair", "brown hair", "platinum blonde hair"],
        "eye_colors": ["pink eyes", "brown eyes"],
        "skin": None,
        "classic_jp": "お菓子——パステルピンク×白と苺・キャンディで甘さを添える",
        "gap_jp": "お菓子——甘い記号を{role}に添える",
    },
    "music": {
        "kind": "theme",
        "jp": "音楽",
        "syn": ["音楽", "ミュージック", "楽器", "music", "musical", "melody"],
        "features_primary": [],
        "features_optional": ["music-note-shaped {accent} hair ornament", "treble clef earrings", "headphones around the neck", "piano-key pattern trim on the hem"],
        "palettes": [("black", "white", "gold"), ("navy", "white", "crimson"), ("white", "hot pink", "black")],
        "patterns": ["musical note motif", "piano key pattern", "stripe pattern", "treble clef motif", "star pattern", "checkered pattern", "record disc motif", "heart motif"],
        "props": [],
        "classic_roles": ["idol", "gothic_lolita", "casual_street", "princess_dress", "cheerleader"],
        "gap_roles": [],
        "classic_arch": ["genki", "ojousama", "kuudere", "fushigi"],
        "gap_arch": [],
        "hair_colors": ["black hair", "white hair", "pink hair"],
        "eye_colors": ["blue eyes", "purple eyes"],
        "skin": None,
        "classic_jp": "音楽——黒×白×金と音符で華やかさを添える",
        "gap_jp": "音楽——華やかな記号を{role}に添える",
    },
    "gem": {
        "kind": "theme",
        "jp": "宝石",
        "syn": ["宝石", "ジュエル", "クリスタル", "鉱石", "gem", "jewel", "crystal", "mineral"],
        "features_primary": [],
        "features_optional": ["crystal-shaped {accent} hair ornament", "gem-studded choker", "gem embedded in the forehead", "crystal brooch on the chest"],
        "palettes": [("white", "sky blue", "gold"), ("dark purple", "lavender", "silver"), ("crimson", "gold", "white"), ("emerald green", "white", "gold")],
        "patterns": ["diamond pattern", "crystal motif", "facet pattern", "star pattern", "filigree motif", "hexagon pattern", "sparkle motif", "lace pattern"],
        "props": [],
        "classic_roles": ["princess_dress", "goddess_dress", "idol", "magical_girl", "gothic_lolita"],
        "gap_roles": [],
        "classic_arch": ["ojousama", "kuudere", "seiso", "jishinka"],
        "gap_arch": [],
        "hair_colors": ["crystal-like light blue hair", "white hair", "lavender hair"],
        "eye_colors": ["gem-like blue eyes", "gem-like red eyes"],
        "skin": None,
        "classic_jp": "宝石——透明感のある色と結晶で高級感を添える",
        "gap_jp": "宝石——高級感の記号を{role}に添える",
    },
    "clockwork": {
        "kind": "theme",
        "jp": "時計",
        "syn": ["時計", "クロック", "時間", "clock", "clockwork", "time"],
        "features_primary": [],
        "features_optional": ["clock-face hair ornament", "pocket watch on a chain", "gear-shaped earrings", "gear embroidery on the cuffs"],
        "palettes": [("brown", "gold", "cream"), ("black", "gold", "white"), ("navy", "gold", "white")],
        "patterns": ["clock motif", "gear motif", "roman numeral pattern", "key motif", "filigree motif", "checkered pattern", "hourglass motif", "spiral motif"],
        "props": [],
        "classic_roles": ["steampunk", "gothic_lolita", "maid", "merchant", "fortune_teller"],
        "gap_roles": [],
        "classic_arch": ["kuudere", "iinchou", "fushigi", "haraguro"],
        "gap_arch": [],
        "hair_colors": ["brown hair", "blonde hair", "white hair"],
        "eye_colors": ["golden eyes", "brown eyes"],
        "skin": None,
        "classic_jp": "時計——茶×金と歯車・文字盤で精密さを添える",
        "gap_jp": "時計——精密さの記号を{role}に添える",
    },
    "poison": {
        "kind": "theme",
        "jp": "毒",
        "syn": ["毒", "ポイズン", "poison", "toxic", "venom"],
        "features_primary": [],
        "features_optional": ["skull-and-crossbones hair ornament", "potion vial pendant", "{accent} snake armlet", "skull-and-crossbones embroidery on the hem"],
        "palettes": [("purple", "black", "emerald green"), ("dark purple", "emerald green", "hot pink"), ("black", "emerald green", "purple")],
        "patterns": ["skull motif", "bubble motif", "biohazard motif", "spiderweb pattern", "drip pattern", "thorn vine pattern", "star pattern", "checkered pattern"],
        "props": [],
        "classic_roles": ["witch_robe", "nurse", "gothic_lolita", "fortune_teller", "thief"],
        "gap_roles": [],
        "classic_arch": ["haraguro", "sadistic", "yandere", "jirai"],
        "gap_arch": [],
        "hair_colors": ["purple hair", "green hair", "black hair"],
        "eye_colors": ["purple eyes", "green eyes"],
        "skin": None,
        "classic_jp": "毒——紫×黒×緑と髑髏・泡で危うさを添える",
        "gap_jp": "毒——危うい記号を{role}に添える",
    },
    "rain": {
        "kind": "theme",
        "jp": "雨",
        "syn": ["雨", "レイン", "雨天", "rain", "rainy", "raindrop"],
        "features_primary": [],
        "features_optional": ["raindrop-shaped {accent} earrings", "transparent raincoat-like sheer cape", "raindrop embroidery on the hem", "umbrella-shaped {accent} brooch"],
        "palettes": [("navy", "sky blue", "silver"), ("gray", "sky blue", "white"), ("teal", "white", "silver")],
        "patterns": ["raindrop pattern", "umbrella motif", "cloud motif", "wave pattern", "stripe pattern", "hydrangea pattern", "frog motif", "puddle motif"],
        "props": [],
        "classic_roles": ["school_uniform", "office_lady", "casual_street", "loungewear"],
        "gap_roles": [],
        "classic_arch": ["uchiki", "kuudere", "ottori", "jirai"],
        "gap_arch": [],
        "hair_colors": ["dark blue hair", "light blue hair", "gray hair"],
        "eye_colors": ["blue eyes", "gray eyes"],
        "skin": None,
        "classic_jp": "雨——紺×水色×銀と雫で物憂げな静けさを添える",
        "gap_jp": "雨——記号を{role}に添える",
    },
    "cloud": {
        "kind": "theme",
        "jp": "雲・空",
        "syn": ["雲", "空", "クラウド", "青空", "cloud", "sky", "clouds"],
        "features_primary": [],
        "features_optional": ["cloud-shaped {accent} hair ornament", "fluffy cloud-like frills on the collar", "cloud embroidery on the hem", "bird-shaped {accent} earrings"],
        "palettes": [("sky blue", "white", "gold"), ("white", "sky blue", "pastel pink"), ("lavender", "white", "sky blue")],
        "patterns": ["cloud motif", "bird motif", "sun motif", "rainbow motif", "feather motif", "polka-dot pattern", "sky gradient pattern", "kite motif"],
        "props": [],
        "classic_roles": ["idol", "casual_street", "goddess_dress", "flight_attendant", "magical_girl"],
        "gap_roles": [],
        "classic_arch": ["genki", "ottori", "fushigi", "amaama"],
        "gap_arch": [],
        "hair_colors": ["light blue hair", "white hair", "platinum blonde hair"],
        "eye_colors": ["blue eyes", "sky blue eyes"],
        "skin": None,
        "classic_jp": "雲・空——水色×白とふわふわの縁取りで軽やかさを添える",
        "gap_jp": "雲・空——記号を{role}に添える",
    },
    "sakura": {
        "kind": "theme",
        "jp": "桜",
        "syn": ["桜", "さくら", "サクラ", "sakura", "cherry blossom"],
        "features_primary": [],
        "features_optional": ["cherry blossom hair ornament", "petal-shaped pastel pink earrings", "cherry blossom embroidery on the sleeves", "cherry blossom kanzashi"],
        "palettes": [("pastel pink", "white", "crimson"), ("white", "pastel pink", "gold"), ("black", "pastel pink", "white")],
        "patterns": ["sakura pattern", "petal motif", "branch motif", "wave pattern", "moon motif", "fan motif", "hemp-leaf pattern", "ribbon motif"],
        "props": [],
        "classic_roles": ["kimono", "shrine_miko", "school_uniform", "samurai", "idol"],
        "gap_roles": [],
        "classic_arch": ["seiso", "ottori", "amaama", "yandere"],
        "gap_arch": [],
        "hair_colors": ["pink hair", "black hair", "platinum blonde hair"],
        "eye_colors": ["pink eyes", "brown eyes"],
        "skin": None,
        "classic_jp": "桜——淡い桃色×白と花びらで儚い華やかさを添える",
        "gap_jp": "桜——記号を{role}に添える",
    },
    "rose": {
        "kind": "theme",
        "jp": "薔薇",
        "syn": ["薔薇", "バラ", "ばら", "rose", "roses"],
        "features_primary": [],
        "features_optional": ["rose hair ornament", "rose-shaped {accent} brooch", "rose embroidery on the hem", "thorn-and-rose choker"],
        "palettes": [("crimson", "black", "gold"), ("white", "crimson", "gold"), ("black", "wine red", "silver"), ("pastel pink", "white", "gold")],
        "patterns": ["rose motif", "rose print", "thorn vine pattern", "lace pattern", "damask pattern", "petal motif", "heart motif", "filigree motif"],
        "props": [],
        "classic_roles": ["gothic_lolita", "princess_dress", "sister", "waitress", "bunny_girl"],
        "gap_roles": [],
        "classic_arch": ["ojousama", "oneesan", "sadistic", "yandere"],
        "gap_arch": [],
        "hair_colors": ["red hair", "black hair", "blonde hair"],
        "eye_colors": ["red eyes", "green eyes"],
        "skin": None,
        "classic_jp": "薔薇——紅×黒×金と薔薇・茨で情熱と棘を添える",
        "gap_jp": "薔薇——記号を{role}に添える",
    },
    "feather": {
        "kind": "theme",
        "jp": "羽根",
        "syn": ["羽根", "羽", "フェザー", "feather", "feathers", "plume"],
        "features_primary": [],
        "features_optional": ["feather hair ornament", "feather-shaped {accent} earrings", "feather trim on the collar", "feather embroidery on the sleeves"],
        "palettes": [("white", "gold", "sky blue"), ("black", "silver", "crimson"), ("cream", "brown", "gold")],
        "patterns": ["feather motif", "feather print", "wing motif", "bird motif", "swirl pattern", "cloud motif", "star pattern", "lace pattern"],
        "props": [],
        "classic_roles": ["dancer", "princess_dress", "goddess_dress", "idol", "fortune_teller"],
        "gap_roles": [],
        "classic_arch": ["seiso", "fushigi", "ojousama", "ottori"],
        "gap_arch": [],
        "hair_colors": ["white hair", "black hair", "platinum blonde hair"],
        "eye_colors": ["golden eyes", "blue eyes"],
        "skin": None,
        "classic_jp": "羽根——軽やかな羽飾りと縁取りで優雅さを添える",
        "gap_jp": "羽根——記号を{role}に添える",
    },
    "chain": {
        "kind": "theme",
        "jp": "鎖",
        "syn": ["鎖", "チェーン", "chain", "chains", "shackle"],
        "features_primary": [],
        "features_optional": ["{accent} chain choker", "chain-wrapped {accent} armlet", "chain-link belt accents", "small {accent} chain hanging from the hem"],
        "palettes": [("black", "silver", "crimson"), ("gray", "black", "gold"), ("navy", "silver", "white")],
        "patterns": ["chain pattern", "chain print", "padlock motif", "cross pattern", "stripe pattern", "skull motif", "spiderweb pattern", "diamond pattern"],
        "props": [],
        "classic_roles": ["gothic_lolita", "delinquent", "bodysuit", "demon_lord", "thief"],
        "gap_roles": [],
        "classic_arch": ["jirai", "sadistic", "chuuni", "kuudere"],
        "gap_arch": [],
        "hair_colors": ["black hair", "silver hair", "white hair"],
        "eye_colors": ["red eyes", "silver eyes"],
        "skin": None,
        "classic_jp": "鎖——黒×銀と鎖の装飾で束縛と硬質さを添える",
        "gap_jp": "鎖——記号を{role}に添える",
    },
    "thorn": {
        "kind": "theme",
        "jp": "茨",
        "syn": ["茨", "いばら", "棘", "thorn", "thorns", "bramble"],
        "features_primary": [],
        "features_optional": ["thorn vine wrapped around the arm", "thorn crown", "thorn-shaped {accent} earrings", "thorn vine embroidery on the hem"],
        "palettes": [("black", "crimson", "emerald green"), ("dark green", "black", "crimson"), ("white", "crimson", "black")],
        "patterns": ["thorn vine pattern", "rose motif", "vine motif", "spiderweb pattern", "cross pattern", "leaf motif", "drip pattern", "lace pattern"],
        "props": [],
        "classic_roles": ["gothic_lolita", "witch_robe", "sister", "princess_dress", "knight"],
        "gap_roles": [],
        "classic_arch": ["yandere", "sadistic", "kuudere", "haraguro"],
        "gap_arch": [],
        "hair_colors": ["black hair", "dark red hair", "green hair"],
        "eye_colors": ["red eyes", "green eyes"],
        "skin": None,
        "classic_jp": "茨——黒×紅×緑と棘の蔦で危うい美しさを添える",
        "gap_jp": "茨——記号を{role}に添える",
    },
    "key": {
        "kind": "theme",
        "jp": "鍵",
        "syn": ["鍵", "キー", "key", "keys", "padlock"],
        "features_primary": [],
        "features_optional": ["ornate {accent} key pendant", "key-shaped earrings", "small padlock choker", "key embroidery on the cuffs"],
        "palettes": [("brown", "gold", "cream"), ("black", "gold", "white"), ("navy", "gold", "silver")],
        "patterns": ["key motif", "padlock motif", "filigree motif", "clock motif", "gear motif", "diamond pattern", "heart motif", "star pattern"],
        "props": [],
        "classic_roles": ["gothic_lolita", "steampunk", "maid", "thief", "merchant"],
        "gap_roles": [],
        "classic_arch": ["fushigi", "kuudere", "haraguro", "iinchou"],
        "gap_arch": [],
        "hair_colors": ["brown hair", "blonde hair", "black hair"],
        "eye_colors": ["golden eyes", "brown eyes"],
        "skin": None,
        "classic_jp": "鍵——茶×金と鍵・南京錠で秘密めいた雰囲気を添える",
        "gap_jp": "鍵——記号を{role}に添える",
    },
    "rainbow": {
        "kind": "theme",
        "jp": "虹",
        "syn": ["虹", "レインボー", "rainbow", "prism", "プリズム"],
        "features_primary": [],
        "features_optional": ["rainbow-gradient ribbon in the hair", "rainbow-striped trim on the hem", "prism-shaped {accent} earrings", "rainbow-colored inner hair"],
        "palettes": [("white", "sky blue", "pastel pink"), ("lavender", "white", "yellow"), ("cream", "mint", "hot pink")],
        "patterns": ["rainbow motif", "rainbow print", "stripe pattern", "star pattern", "cloud motif", "heart motif", "polka-dot pattern", "sparkle motif"],
        "props": [],
        "classic_roles": ["idol", "magical_girl", "cheerleader", "casual_street", "swimsuit"],
        "gap_roles": [],
        "classic_arch": ["genki", "fushigi", "amaama", "dojikko"],
        "gap_arch": [],
        "hair_colors": ["multicolored hair", "white hair", "pink hair"],
        "eye_colors": ["heterochromia, blue and pink eyes", "blue eyes"],
        "skin": None,
        "classic_jp": "虹——多色のグラデーション縁取りで華やかな明るさを添える",
        "gap_jp": "虹——記号を{role}に添える",
    },
    "holy_light": {
        "kind": "theme",
        "jp": "聖光",
        "syn": ["聖光", "光", "神聖", "ホーリー", "holy", "light", "sacred", "divine light"],
        "features_primary": [],
        "features_optional": ["golden halo-shaped hair ornament", "cross-shaped {accent} earrings", "gold filigree embroidery on the hem", "glowing {accent} cross pendant"],
        "palettes": [("white", "gold", "sky blue"), ("cream", "gold", "white"), ("white", "silver", "gold")],
        "patterns": ["cross pattern", "filigree motif", "sun motif", "feather motif", "stained-glass pattern", "halo ring motif", "lily motif", "star pattern"],
        "props": [],
        "classic_roles": ["saint", "sister", "pontiff", "goddess_dress", "knight"],
        "gap_roles": [],
        "classic_arch": ["seiso", "juujun", "ojousama", "iinchou"],
        "gap_arch": [],
        "hair_colors": ["blonde hair", "white hair", "platinum blonde hair"],
        "eye_colors": ["golden eyes", "blue eyes"],
        "skin": None,
        "classic_jp": "聖光——白×金と十字・光輪で神聖さを添える",
        "gap_jp": "聖光——記号を{role}に添える",
    },
    "shadow": {
        "kind": "theme",
        "jp": "影",
        "syn": ["影", "闇", "シャドウ", "ダーク", "shadow", "dark", "darkness"],
        "features_primary": [],
        "features_optional": ["black shadow-like trailing hem", "{accent} eye-shaped brooch", "black lace veil over one eye", "shadow-like black ribbons on the arms"],
        "palettes": [("black", "dark purple", "crimson"), ("black", "gray", "silver"), ("navy", "black", "purple")],
        "patterns": ["eye motif", "smoke swirl pattern", "spiderweb pattern", "moon motif", "skull motif", "lace pattern", "thorn vine pattern", "chain pattern"],
        "props": [],
        "classic_roles": ["gothic_lolita", "thief", "demon_lord", "witch_robe", "ninja"],
        "gap_roles": [],
        "classic_arch": ["kuudere", "yandere", "chuuni", "haraguro"],
        "gap_arch": [],
        "hair_colors": ["black hair", "dark purple hair", "white hair"],
        "eye_colors": ["red eyes", "purple eyes", "glowing eyes"],
        "skin": None,
        "classic_jp": "影——黒×紫と影のような縁取りで不穏さを添える",
        "gap_jp": "影——記号を{role}に添える",
    },
    "candle": {
        "kind": "theme",
        "jp": "蝋燭",
        "syn": ["蝋燭", "ロウソク", "キャンドル", "candle", "candles", "candlelight"],
        "features_primary": [],
        "features_optional": ["candle-shaped {accent} hair ornament", "wax-drip-like trim on the hem", "small {accent} flame-shaped earrings", "candelabra-shaped brooch"],
        "palettes": [("cream", "wine red", "gold"), ("black", "gold", "crimson"), ("white", "gold", "orange")],
        "patterns": ["candle motif", "flame pattern", "drip pattern", "filigree motif", "moon motif", "cross pattern", "lace pattern", "star pattern"],
        "props": [],
        "classic_roles": ["gothic_lolita", "sister", "fortune_teller", "princess_dress", "maid"],
        "gap_roles": [],
        "classic_arch": ["seiso", "uchiki", "yandere", "fushigi"],
        "gap_arch": [],
        "hair_colors": ["blonde hair", "black hair", "brown hair"],
        "eye_colors": ["golden eyes", "orange eyes"],
        "skin": None,
        "classic_jp": "蝋燭——クリーム×ワインレッド×金と蝋の滴りで静かな灯りを添える",
        "gap_jp": "蝋燭——記号を{role}に添える",
    },
    "royal": {
        "kind": "theme",
        "jp": "王冠",
        "syn": ["王冠", "王族", "ロイヤル", "王", "crown", "royal", "royalty", "regal"],
        "features_primary": [],
        "features_optional": ["small {accent} crown", "ceremonial {sub} sash across the chest", "ermine-trimmed cape collar", "{accent} scepter-shaped brooch"],
        "palettes": [("crimson", "gold", "white"), ("royal blue", "gold", "white"), ("purple", "gold", "white")],
        "patterns": ["crown motif", "fleur-de-lis pattern", "filigree motif", "lion motif", "damask pattern", "checkered pattern", "laurel motif", "star pattern"],
        "props": [],
        "classic_roles": ["princess_dress", "knight", "military", "demon_lord", "pontiff"],
        "gap_roles": [],
        "classic_arch": ["ojousama", "jishinka", "sadistic", "aneki"],
        "gap_arch": [],
        "hair_colors": ["blonde hair", "silver hair", "black hair"],
        "eye_colors": ["golden eyes", "blue eyes"],
        "skin": None,
        "classic_jp": "王冠——紅×金と王冠・紋章で格式を添える",
        "gap_jp": "王冠——記号を{role}に添える",
    },
    "neon": {
        "kind": "theme",
        "jp": "ネオン",
        "syn": ["ネオン", "サイバー", "neon", "cyber", "cyberpunk", "サイバーパンク"],
        "features_primary": [],
        "features_optional": ["glowing {accent} neon trim along the seams", "neon-lit {accent} visor on the head", "glowing neon earrings", "{accent} LED-strip choker"],
        "palettes": [("black", "hot pink", "sky blue"), ("black", "sky blue", "hot pink"), ("dark purple", "hot pink", "yellow")],
        "patterns": ["circuit pattern", "glowing line pattern", "hexagon pattern", "pixel pattern", "barcode motif", "wireframe grid pattern", "stripe pattern", "star pattern"],
        "props": [],
        "classic_roles": ["bodysuit", "casual_street", "race_queen", "idol", "police"],
        "gap_roles": [],
        "classic_arch": ["gal", "kuudere", "mesugaki", "dokuzetsu"],
        "gap_arch": [],
        "hair_colors": ["black hair", "hot pink hair", "light blue hair"],
        "eye_colors": ["glowing eyes", "magenta eyes"],
        "skin": None,
        "classic_jp": "ネオン——黒×蛍光色と発光する縁取りで未来感を添える",
        "gap_jp": "ネオン——記号を{role}に添える",
    },
    "heart": {
        "kind": "theme",
        "jp": "ハート",
        "syn": ["ハート", "heart", "hearts", "ラブ", "love"],
        "features_primary": [],
        "features_optional": ["heart-shaped {accent} hair ornament", "heart-shaped earrings", "heart cutout on the chest", "heart-print ribbons on the outfit"],
        "palettes": [("pastel pink", "white", "crimson"), ("crimson", "white", "gold"), ("black", "hot pink", "white")],
        "patterns": ["heart motif", "heart print", "polka-dot pattern", "ribbon motif", "lace pattern", "star pattern", "checkered pattern", "candy motif"],
        "props": [],
        "classic_roles": ["idol", "maid", "magical_girl", "loungewear", "bunny_girl"],
        "gap_roles": [],
        "classic_arch": ["amaama", "mesugaki", "jirai", "gal"],
        "gap_arch": [],
        "hair_colors": ["pink hair", "blonde hair", "black hair"],
        "eye_colors": ["pink eyes", "red eyes"],
        "skin": None,
        "classic_jp": "ハート——桃色×白×赤とハート型の小物で甘さを添える",
        "gap_jp": "ハート——記号を{role}に添える",
    },
    "skull": {
        "kind": "theme",
        "jp": "骸骨",
        "syn": ["骸骨", "ドクロ", "髑髏", "スカル", "skull", "skulls", "bones"],
        "features_primary": [],
        "features_optional": ["skull-shaped {accent} hair ornament", "skull-shaped earrings", "bone-shaped {accent} brooch", "skull embroidery on the hem"],
        "palettes": [("black", "white", "crimson"), ("black", "gray", "purple"), ("white", "black", "crimson")],
        "patterns": ["skull motif", "skull print", "bone pattern", "cross pattern", "spiderweb pattern", "chain pattern", "star pattern", "checkered pattern"],
        "props": [],
        "classic_roles": ["gothic_lolita", "pirate", "delinquent", "casual_street", "witch_robe"],
        "gap_roles": [],
        "classic_arch": ["chuuni", "jirai", "kuudere", "mesugaki"],
        "gap_arch": [],
        "hair_colors": ["black hair", "white hair", "silver hair"],
        "eye_colors": ["red eyes", "golden eyes"],
        "skin": None,
        "classic_jp": "骸骨——黒×白×紅とドクロで反骨と不吉さを添える",
        "gap_jp": "骸骨——記号を{role}に添える",
    },
    "human": {
        "jp": "人間（種族なし）",
        "syn": ["人間", "普通", "ノーマル", "モチーフなし", "human", "normal", "plain"],
        "features_primary": [],
        "features_optional": [],
        "palettes": [("white", "navy", "crimson"), ("black", "white", "gold"), ("pastel pink", "white", "gold"), ("navy", "white", "gold"), ("gray", "black", "sky blue")],
        "patterns": ["ribbon motif", "star accents", "stripe accents", "small floral motif", "checkered pattern", "plaid pattern", "polka-dot pattern", "heart motif", "lace pattern", "gingham pattern", "diagonal stripe pattern"],
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

# 種族（race）とモチーフ（theme）の分離ビュー。kind が無いエントリは種族
RACES = {k: v for k, v in MOTIFS.items() if v.get("kind", "race") == "race"}
THEMES = {k: v for k, v in MOTIFS.items() if v.get("kind") == "theme"}
# 指示文に種族指定が無い時の重み（human をやや高めにして「普通の子」も出す）
MOTIF_WEIGHTS = {k: (3 if k == "human" else 1) for k in RACES}
# 指示文にテーマ指定が無い時にテーマが付く確率
THEME_PROB = 0.35

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
        "syn": ["忍者", "くノ一", "くのいち", "忍び", "忍び装束", "ninja", "kunoichi", "shinobi"],
        # 忍び装束ベース（頭巾・覆面・鎖帷子・手甲・脚絆・地下足袋）。特定作品の記号（網シャツ・額当て・クナイ）は使わない
        "outfits": {
            "modest": [
                "{material} {main} shinobi shozoku, hooded ninja garb with {accent} cord ties at the wrists and ankles, {sub} {pattern} on the chest wrap",
                "{main} ninja hood with a face-covering mask",
                "{main} tekko hand guards",
                "{main} kyahan leg wraps",
                "jika-tabi split-toe boots",
                "{sub} obi sash tied with a {accent} knot",
            ],
            "standard": [
                "{material} {main} ninja garb with short sleeves and {accent} cord ties, chainmail undershirt showing at the collar, {sub} {pattern} on the chest wrap",
                "{main} ninja hood pulled down around the neck",
                "{main} tekko hand guards",
                "{main} short hakama-style shorts with {sub} obi sash",
                "{main} kyahan leg wraps",
                "jika-tabi split-toe boots",
            ],
            "high": [
                "{material} {main} ninja garb with a deep neckline and bare shoulders, chainmail underlayer, {accent} cord ties, {sub} {pattern} on the chest wrap",
                "{main} ninja hood pulled down around the neck",
                "{main} tekko hand guards",
                "{main} micro shorts with {sub} obi sash",
                "{main} thigh-high kyahan leg wraps",
                "jika-tabi split-toe boots",
            ],
        },
        "male": {
            "modest": ["{material} {main} shinobi shozoku, hooded ninja garb with {accent} cord ties, {sub} {pattern} on the chest wrap", "{main} ninja hood with a face-covering mask", "{main} tekko hand guards", "{main} kyahan leg wraps", "jika-tabi split-toe boots"],
            "standard": ["{material} {main} ninja garb with {accent} cord ties, chainmail undershirt, {sub} {pattern} on the chest wrap", "{main} ninja hood pulled down around the neck", "{main} tekko hand guards", "{main} hakama-style pants with {sub} obi sash", "{main} kyahan leg wraps", "jika-tabi split-toe boots"],
            "high": ["{material} {main} ninja garb worn open over a bare chest with chainmail underlayer, {accent} cord ties, {sub} {pattern} on the collar", "{main} ninja hood pulled down around the neck", "{main} tekko hand guards", "{main} hakama-style pants with {sub} obi sash", "jika-tabi split-toe boots"],
        },
        "props": ["ninjato short sword strapped to the back", "sealed scroll (makimono)", "shuriken held between the fingers", "smoke bomb"],
        "materials": ["cloth", "cotton"],
        "palettes": [("black", "navy", "crimson"), ("navy", "black", "silver"), ("dark purple", "black", "gold"), ("crimson", "black", "gold")],
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
                [
                    "{material} {main} long pajama set with {sub} {pattern} print and {accent} piping on the collar",
                    "{material} {main} ankle-length nightgown with {accent} lace trim on the collar, {sub} {pattern} print",
                    "{material} {main} oversized hoodie and {sub} sweatpants with {pattern} print on the chest",
                    "{material} {main} yukata-style sleepwear with {sub} {pattern}, {accent} sash",
                ],
                "?{main} sleep mask pushed up on the head with {accent} trim",
                ["{sub} fluffy slippers", "barefoot", "{sub} fluffy socks"],
                "?hugging a {sub} pillow",
            ],
            "standard": [
                [
                    "{material} {main} oversized sleep shirt with {sub} {pattern} print and {accent} buttons, reaching the thighs",
                    "{material} {main} camisole and {sub} shorts pajama set with {accent} lace trim and {pattern} print",
                    "{material} {main} short nightgown with {accent} lace trim, {sub} {pattern} print",
                    "{material} {main} oversized sweater worn as a dress with {sub} {pattern} print",
                ],
                "?{main} sleep mask pushed up on the head with {accent} trim",
                ["{main} thigh-high socks with {accent} top band", "bare legs", "{sub} fluffy socks"],
                ["{sub} fluffy slippers", "barefoot"],
            ],
            "high": [
                [
                    "{material} {main} sheer negligee with {accent} lace trim and {sub} {pattern} ribbons, deep neckline",
                    "{material} {main} lace babydoll with {accent} trim and {sub} {pattern} ribbons",
                    "{material} {main} oversized dress shirt worn open over {sub} lingerie, {pattern} print",
                    "{material} {main} silk camisole and micro shorts with {accent} lace trim, {sub} {pattern} ribbons",
                ],
                "?{main} sleep mask pushed up on the head with {accent} trim",
                ["{main} thigh-high stockings with {accent} lace tops", "bare legs"],
                ["{sub} fluffy slippers", "barefoot"],
            ],
        },
        "male": {
            "modest": [["{material} {main} pajama set with {sub} {pattern} print and {accent} piping", "{material} {main} t-shirt and {sub} sweatpants with {pattern} print", "{material} {main} yukata-style sleepwear with {sub} {pattern}"], "?{main} sleep mask pushed up on the head", ["{sub} slippers", "barefoot"]],
            "standard": [["{material} {main} pajama set with {sub} {pattern} print and {accent} piping", "{material} {main} t-shirt and {sub} sweatpants with {pattern} print", "{material} {main} yukata-style sleepwear with {sub} {pattern}"], "?{main} sleep mask pushed up on the head", ["{sub} slippers", "barefoot"]],
            "high": [["shirtless, {material} {main} pajama pants with {sub} {pattern} print and {accent} drawstring", "shirtless, {material} {main} boxers with {sub} {pattern} print"], "?{main} sleep mask pushed up on the head", ["{sub} slippers", "barefoot"]],
        },
        "props": ["oversized plush toy", "pillow", "mug of cocoa"],
        "materials": ["silk", "flannel", "cotton"],
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
    "saint": {
        "jp": "聖女",
        "syn": ["聖女", "聖人", "saint", "holy maiden"],
        "outfits": {
            "modest": [
                "{material} white holy robe with {accent} trim on every hem, high collar, long wide sleeves, {sub} {pattern} embroidered on the chest",
                "{sub} stole with {accent} cross",
                "white gloves",
                "{accent} circlet",
                "white low-heeled shoes",
            ],
            "standard": [
                "{material} white holy dress with {accent} trim, open shoulders, {sub} {pattern} embroidered on the bodice, knee-length layered skirt",
                "{sub} short cape with {accent} clasp",
                "white gloves with {accent} cuffs",
                "{accent} circlet",
                "white thigh-high socks with {accent} top band",
                "white heeled shoes",
            ],
            "high": [
                "{material} white holy dress with a deep plunging neckline framed in {accent} trim, high thigh slits, {sub} {pattern} embroidered on the bodice",
                "{sub} sheer veil with {accent} edge",
                "white opera gloves",
                "{accent} circlet",
                "white thigh-high stockings with {accent} lace tops and garter straps",
                "white heeled shoes",
            ],
        },
        "male": {
            "modest": ["{material} white holy robe with {accent} trim, {sub} {pattern} embroidered on the chest", "{sub} stole with {accent} cross", "white gloves", "white shoes"],
            "standard": ["{material} white holy robe with {accent} trim, {sub} {pattern} embroidered on the chest", "{sub} stole with {accent} cross", "white gloves", "white shoes"],
            "high": ["{material} white holy robe worn open at the chest with {accent} trim, {sub} {pattern} on the collar", "{sub} stole with {accent} cross", "white shoes"],
        },
        "props": ["glowing holy staff", "prayer beads", "holy relic in a {accent} case"],
        "materials": ["silk", "satin"],
        "palettes": [("white", "gold", "sky blue"), ("white", "navy", "gold"), ("cream", "crimson", "gold")],
    },
    "goddess_dress": {
        "jp": "女神衣装（ギリシャ風）",
        "syn": ["女神衣装", "トーガ", "ギリシャ", "toga", "greek dress", "chiton"],
        "outfits": {
            "modest": [
                "{material} {main} floor-length greek chiton with {accent} rope belt, {sub} {pattern} border on the hem, draped sleeves",
                "{sub} himation cloak pinned with {accent} brooch",
                "{accent} laurel hair ornament",
                "{accent} armlets",
                "{main} gladiator sandals",
            ],
            "standard": [
                "{material} {main} one-shoulder greek dress with {accent} rope belt, {sub} {pattern} border on the hem, knee-length",
                "{accent} laurel hair ornament",
                "{accent} armlets and bracelets",
                "{main} gladiator sandals laced to the knee",
            ],
            "high": [
                "{material} {main} greek dress with a plunging neckline held by {accent} clasps, high thigh slits, {sub} {pattern} border on the hem",
                "{accent} laurel hair ornament",
                "{accent} armlets and bracelets",
                "{main} gladiator sandals laced to the thigh",
                "{sub} sheer shawl",
            ],
        },
        "male": {
            "modest": ["{material} {main} greek chiton with {accent} rope belt, {sub} {pattern} border", "{sub} himation cloak", "{accent} laurel crown", "{main} sandals"],
            "standard": ["{material} {main} greek chiton with {accent} rope belt, {sub} {pattern} border", "{accent} laurel crown", "{accent} armlets", "{main} sandals"],
            "high": ["bare chest, {material} {main} draped cloth with {accent} clasp and {sub} {pattern} border", "{accent} laurel crown", "{accent} armlets", "{main} sandals"],
        },
        "props": ["golden chalice", "lyre", "golden apple"],
        "materials": ["silk", "linen"],
        "palettes": [("white", "gold", "sky blue"), ("cream", "gold", "crimson"), ("white", "lavender", "gold")],
    },
    "cow_suit": {
        "jp": "乳牛衣装（牛柄）",
        "syn": ["乳牛衣装", "牛柄", "牛柄ビキニ", "cow print", "cow bikini"],
        "outfits": {
            "modest": [
                "white and black cow-print long-sleeved bodysuit with {accent} piping, high neckline",
                "{accent} cowbell collar",
                "white and black cow-print thigh-high socks",
                "{main} boots",
            ],
            "standard": [
                "white and black cow-print bikini top with {accent} piping, white and black cow-print mini skirt",
                "{accent} cowbell collar",
                "white and black cow-print thigh-high socks",
                "white and black cow-print arm warmers",
                "{main} boots",
            ],
            "high": [
                "white and black cow-print micro bikini with {accent} piping",
                "{accent} cowbell collar",
                "white and black cow-print thigh-high stockings with garter straps",
                "white and black cow-print arm warmers",
                "{main} heeled shoes",
            ],
        },
        "male": {
            "modest": ["white and black cow-print vest with {accent} piping over a white shirt", "{accent} cowbell collar", "{main} trousers", "{main} boots"],
            "standard": ["white and black cow-print vest with {accent} piping over a white shirt", "{accent} cowbell collar", "{main} trousers", "{main} boots"],
            "high": ["shirtless, white and black cow-print shorts with {accent} belt", "{accent} cowbell collar", "white and black cow-print arm warmers"],
        },
        "props": ["milk bottle", "{accent} cowbell", "bucket of milk"],
        "materials": ["latex", "cotton"],
        "palettes": [("white", "black", "pastel pink"), ("white", "black", "gold"), ("cream", "brown", "crimson")],
    },
    "hero": {
        "jp": "勇者",
        "syn": ["勇者", "ヒーロー", "冒険者", "hero", "adventurer", "brave"],
        "outfits": {
            "modest": [
                "{material} {main} hero's tunic with {accent} trim and {sub} {pattern} emblem on the chest, over a white shirt",
                "{sub} long cape with {accent} clasp",
                "{main} leather bracers",
                "{main} trousers with {sub} leather belt",
                "{main} knee-high adventurer boots with {accent} buckles",
            ],
            "standard": [
                "{material} {main} sleeveless hero's tunic with {accent} trim and {sub} {pattern} emblem on the chest",
                "{sub} short cape with {accent} clasp",
                "{main} leather bracers",
                "{main} shorts with {sub} leather belt",
                "{main} thigh-high adventurer boots with {accent} buckles",
                "{sub} shoulder guard on one shoulder",
            ],
            "high": [
                "{material} {main} cropped hero's top with {accent} trim and {sub} {pattern} emblem, exposed midriff, deep neckline",
                "{sub} short cape with {accent} clasp",
                "{main} leather bracers",
                "{main} micro shorts with {sub} leather belt",
                "{main} thigh-high adventurer boots with {accent} buckles",
                "{sub} shoulder guard on one shoulder",
            ],
        },
        "male": {
            "modest": ["{material} {main} hero's tunic with {accent} trim and {sub} {pattern} emblem on the chest, over a white shirt", "{sub} long cape with {accent} clasp", "{main} leather bracers", "{main} trousers with {sub} leather belt", "{main} adventurer boots"],
            "standard": ["{material} {main} sleeveless hero's tunic with {accent} trim and {sub} {pattern} emblem on the chest", "{sub} short cape with {accent} clasp", "{main} leather bracers", "{main} trousers with {sub} leather belt", "{main} adventurer boots"],
            "high": ["{material} {main} hero's tunic worn open over a bare chest with {accent} trim, {sub} {pattern} emblem", "{sub} short cape with {accent} clasp", "{main} leather bracers", "{main} trousers with {sub} leather belt", "{main} adventurer boots"],
        },
        "props": ["holy sword with {accent} hilt", "round shield with {pattern}", "adventurer's backpack"],
        "materials": ["leather", "cotton"],
        "palettes": [("royal blue", "white", "gold"), ("emerald green", "brown", "gold"), ("crimson", "white", "gold")],
    },
    "steampunk": {
        "jp": "スチームパンク",
        "syn": ["スチームパンク", "スチパン", "歯車", "steampunk", "gears"],
        "outfits": {
            "modest": [
                "{material} {main} victorian steampunk jacket with {accent} brass buttons and {sub} {pattern} trim, high collar",
                "{sub} corset with {accent} brass buckles",
                "{main} long bustle skirt",
                "brass goggles on the head",
                "{main} lace-up boots with {accent} brass buckles",
                "{sub} leather gloves",
            ],
            "standard": [
                "{material} {main} steampunk corset over a white blouse with {accent} brass buckles and {sub} {pattern} trim",
                "{main} short bustle skirt with {sub} underskirt",
                "brass goggles on the head",
                "{main} thigh-high lace-up boots with {accent} brass buckles",
                "{sub} leather fingerless gloves",
                "{accent} gear-shaped hair ornament",
            ],
            "high": [
                "{material} {main} steampunk underbust corset with {accent} brass buckles over a {sub} lace bra, {pattern} trim",
                "{main} micro bustle skirt",
                "brass goggles on the head",
                "{main} thigh-high lace-up boots with {accent} brass buckles and garter straps",
                "{sub} leather fingerless gloves",
                "{accent} gear-shaped hair ornament",
            ],
        },
        "male": {
            "modest": ["{material} {main} steampunk waistcoat with {accent} brass buttons over a white shirt, {sub} {pattern} trim", "brass goggles on the head", "{main} trousers", "{main} boots with {accent} buckles"],
            "standard": ["{material} {main} steampunk waistcoat with {accent} brass buttons over a white shirt, {sub} {pattern} trim", "brass goggles on the head", "{main} trousers", "{main} boots with {accent} buckles"],
            "high": ["{material} {main} steampunk waistcoat worn open over a bare chest, {accent} brass buttons, {sub} {pattern} trim", "brass goggles on the head", "{main} trousers", "{main} boots with {accent} buckles"],
        },
        "props": ["brass pocket watch on a chain", "mechanical arm gauntlet", "steam-powered gun"],
        "materials": ["leather", "velvet"],
        "palettes": [("brown", "cream", "gold"), ("black", "wine red", "gold"), ("navy", "brown", "gold")],
    },
    "merchant": {
        "jp": "商人",
        "syn": ["商人", "行商", "商売", "merchant", "trader", "shopkeeper"],
        "outfits": {
            "modest": [
                "{material} {main} merchant's vest with {accent} buttons over a white shirt, {sub} {pattern} on the lapels",
                "{sub} long apron with {accent} trim",
                "{main} long skirt",
                "{sub} headscarf",
                "{main} ankle boots",
                "{accent} coin purse on the belt",
            ],
            "standard": [
                "{material} {main} merchant's vest with {accent} buttons over a white off-shoulder blouse, {sub} {pattern} on the lapels",
                "{sub} apron with {accent} trim",
                "{main} knee-length skirt",
                "{sub} headscarf",
                "{main} ankle boots",
                "{accent} coin purse on the belt",
                "{sub} satchel",
            ],
            "high": [
                "{material} {main} merchant's vest with {accent} buttons worn over a {sub} bikini top, {pattern} on the lapels",
                "{sub} short apron with {accent} trim",
                "{main} micro skirt",
                "{sub} headscarf",
                "{main} thigh-high boots",
                "{accent} coin purse on the belt",
            ],
        },
        "male": {
            "modest": ["{material} {main} merchant's vest with {accent} buttons over a white shirt, {sub} {pattern} on the lapels", "{sub} apron", "{main} trousers", "{main} boots", "{accent} coin purse on the belt"],
            "standard": ["{material} {main} merchant's vest with {accent} buttons over a white shirt, {sub} {pattern} on the lapels", "{sub} apron", "{main} trousers", "{main} boots", "{accent} coin purse on the belt"],
            "high": ["{material} {main} merchant's vest worn open over a bare chest, {accent} buttons, {sub} {pattern} on the lapels", "{main} trousers", "{main} boots", "{accent} coin purse on the belt"],
        },
        "props": ["ledger book", "bag of gold coins", "merchant's balance scale"],
        "materials": ["cotton", "wool"],
        "palettes": [("brown", "cream", "gold"), ("emerald green", "cream", "gold"), ("wine red", "cream", "gold")],
    },
    "pontiff": {
        "jp": "教皇",
        "syn": ["教皇", "法王", "枢機卿", "司教", "pope", "pontiff", "cardinal", "bishop"],
        "outfits": {
            "modest": [
                "{material} {main} papal vestments with {accent} ornate embroidery on every hem, {sub} {pattern} on the chest, floor-length",
                "{main} tall mitre with {accent} embroidery",
                "{sub} pallium stole with {accent} crosses",
                "white gloves with {accent} rings",
                "{main} embroidered slippers",
            ],
            "standard": [
                "{material} {main} papal robe with {accent} ornate embroidery, open front over a {sub} dress with {pattern}, knee-length",
                "{main} tall mitre with {accent} embroidery",
                "{sub} pallium stole with {accent} crosses",
                "white gloves with {accent} rings",
                "{main} thigh-high stockings with {accent} top band",
                "{main} heeled shoes",
            ],
            "high": [
                "{material} {main} papal robe with {accent} ornate embroidery worn open over a {sub} bikini-style top with {pattern}, deep cleavage",
                "{main} tall mitre with {accent} embroidery",
                "{sub} pallium stole with {accent} crosses",
                "white opera gloves with {accent} rings",
                "{main} thigh-high stockings with {accent} lace tops and garter straps",
                "{main} heeled shoes",
            ],
        },
        "male": {
            "modest": ["{material} {main} papal vestments with {accent} ornate embroidery, {sub} {pattern} on the chest, floor-length", "{main} tall mitre with {accent} embroidery", "{sub} pallium stole with {accent} crosses", "white gloves with {accent} rings", "{main} embroidered slippers"],
            "standard": ["{material} {main} papal vestments with {accent} ornate embroidery, {sub} {pattern} on the chest, floor-length", "{main} tall mitre with {accent} embroidery", "{sub} pallium stole with {accent} crosses", "white gloves with {accent} rings", "{main} embroidered slippers"],
            "high": ["{material} {main} papal robe worn open over a bare chest with {accent} ornate embroidery, {sub} {pattern} on the collar", "{main} tall mitre with {accent} embroidery", "{sub} pallium stole with {accent} crosses", "{main} trousers", "{main} embroidered slippers"],
        },
        "props": ["papal staff with a {accent} cross", "censer on a chain", "ring of office"],
        "materials": ["silk", "satin"],
        "palettes": [("white", "gold", "crimson"), ("crimson", "gold", "white"), ("black", "gold", "purple")],
    },
    "demon_lord": {
        "jp": "魔王装束",
        "syn": ["魔王", "魔王様", "demon lord", "demon king", "dark lord", "overlord", "maou"],
        "outfits": {
            "modest": [
                "{material} {main} demon lord's regalia: high-collared coat with {accent} ornate trim and {sub} {pattern} on the chest, floor-length",
                "{sub} long cape with {accent} lining and spiked shoulder guards",
                "{main} clawed gauntlets",
                "{accent} crown with dark gems",
                "{main} armored boots",
            ],
            "standard": [
                "{material} {main} demon lord's regalia: high-collared coat with {accent} ornate trim and {sub} {pattern} on the chest, knee-length",
                "{sub} long cape with {accent} lining and spiked shoulder guards",
                "{main} clawed gauntlets",
                "{accent} crown with dark gems",
                "{main} thigh-high armored boots",
            ],
            "high": [
                "{material} {main} demon lord's regalia: open high-collared coat with {accent} ornate trim over a {sub} bikini-style top with {pattern}, exposed midriff",
                "{sub} long cape with {accent} lining and spiked shoulder guards",
                "{main} clawed gauntlets",
                "{accent} crown with dark gems",
                "{main} thigh-high armored boots with {accent} garter straps",
            ],
        },
        "male": {
            "modest": ["{material} {main} demon lord's regalia: high-collared coat with {accent} ornate trim and {sub} {pattern} on the chest, floor-length", "{sub} long cape with {accent} lining and spiked shoulder guards", "{main} clawed gauntlets", "{accent} crown with dark gems", "{main} armored boots"],
            "standard": ["{material} {main} demon lord's regalia: high-collared coat with {accent} ornate trim and {sub} {pattern} on the chest", "{sub} long cape with {accent} lining and spiked shoulder guards", "{main} clawed gauntlets", "{accent} crown with dark gems", "{main} trousers", "{main} armored boots"],
            "high": ["{material} {main} demon lord's coat worn open over a bare chest with {accent} ornate trim, {sub} {pattern} on the collar", "{sub} long cape with {accent} lining and spiked shoulder guards", "{main} clawed gauntlets", "{accent} crown with dark gems", "{main} trousers", "{main} armored boots"],
        },
        "props": ["dark scepter with a {accent} orb", "dark orb held in the palm", "chained {accent} pendant"],
        "materials": ["velvet", "leather"],
        "palettes": [("black", "crimson", "gold"), ("dark purple", "black", "gold"), ("black", "purple", "silver")],
    },
    "thief": {
        "jp": "盗賊・暗殺者",
        "syn": ["盗賊", "シーフ", "怪盗", "暗殺者", "アサシン", "thief", "rogue", "assassin", "phantom thief"],
        "outfits": {
            "modest": [
                "{material} {main} hooded thief cloak with {accent} trim and {sub} {pattern} clasp, fitted leather vest",
                "{main} leather trousers",
                "{main} leather bracers",
                "{main} soft boots",
                "{sub} belt with many pouches",
            ],
            "standard": [
                "{material} {main} hooded short cloak with {accent} trim and {sub} {pattern} clasp, fitted leather vest over a {sub} shirt",
                "{main} leather shorts",
                "{main} leather bracers",
                "{main} thigh-high soft boots",
                "{sub} belt with many pouches",
                "{main} half-mask pulled down to the chin",
            ],
            "high": [
                "{material} {main} hooded short cloak with {accent} trim and {sub} {pattern} clasp, fitted leather corset with a deep neckline",
                "{main} leather micro shorts",
                "{main} leather bracers",
                "{main} thigh-high soft boots with {accent} straps",
                "{sub} belt with many pouches",
                "{main} half-mask pulled down to the chin",
            ],
        },
        "male": {
            "modest": ["{material} {main} hooded thief cloak with {accent} trim and {sub} {pattern} clasp, fitted leather vest", "{main} leather trousers", "{main} leather bracers", "{main} soft boots", "{sub} belt with many pouches"],
            "standard": ["{material} {main} hooded short cloak with {accent} trim and {sub} {pattern} clasp, fitted leather vest over a {sub} shirt", "{main} leather trousers", "{main} leather bracers", "{main} soft boots", "{sub} belt with many pouches", "{main} half-mask pulled down"],
            "high": ["{material} {main} hooded short cloak with {accent} trim, open leather vest over a bare chest, {sub} {pattern} clasp", "{main} leather trousers", "{main} leather bracers", "{main} soft boots", "{sub} belt with many pouches"],
        },
        "props": ["pair of daggers", "lockpick set", "stolen gem in a {accent} pouch"],
        "materials": ["leather"],
        "palettes": [("black", "dark purple", "silver"), ("navy", "black", "gold"), ("brown", "black", "crimson")],
    },
    "archer": {
        "jp": "弓使い・狩人",
        "syn": ["弓使い", "弓", "アーチャー", "レンジャー", "狩人", "archer", "ranger", "hunter", "bowman"],
        "outfits": {
            "modest": [
                "{material} {main} ranger's tunic with {accent} trim and {sub} {pattern} on the chest, long sleeves",
                "{sub} hooded cloak with {accent} clasp",
                "{main} leather bracers",
                "{main} trousers",
                "{main} knee-high boots",
                "{sub} quiver strap across the chest",
            ],
            "standard": [
                "{material} {main} sleeveless ranger's tunic with {accent} trim and {sub} {pattern} on the chest",
                "{sub} hooded short cloak with {accent} clasp",
                "{main} leather bracers",
                "{main} shorts with {sub} belt",
                "{main} thigh-high boots",
                "{sub} quiver strap across the chest",
            ],
            "high": [
                "{material} {main} cropped ranger's top with {accent} trim and {sub} {pattern}, exposed midriff",
                "{sub} hooded short cloak with {accent} clasp",
                "{main} leather bracers",
                "{main} micro shorts with {sub} belt",
                "{main} thigh-high boots with {accent} straps",
                "{sub} quiver strap across the chest",
            ],
        },
        "male": {
            "modest": ["{material} {main} ranger's tunic with {accent} trim and {sub} {pattern} on the chest", "{sub} hooded cloak with {accent} clasp", "{main} leather bracers", "{main} trousers", "{main} boots", "{sub} quiver strap across the chest"],
            "standard": ["{material} {main} sleeveless ranger's tunic with {accent} trim and {sub} {pattern} on the chest", "{sub} hooded short cloak with {accent} clasp", "{main} leather bracers", "{main} trousers", "{main} boots", "{sub} quiver strap across the chest"],
            "high": ["{material} {main} ranger's tunic worn open over a bare chest with {accent} trim, {sub} {pattern} on the collar", "{sub} hooded short cloak with {accent} clasp", "{main} leather bracers", "{main} trousers", "{main} boots", "{sub} quiver strap across the chest"],
        },
        "props": ["longbow with {accent} fittings", "hawk perched on the arm", "hunting horn"],
        "materials": ["leather", "cotton"],
        "palettes": [("emerald green", "brown", "gold"), ("navy", "brown", "silver"), ("olive green", "cream", "crimson")],
    },
    "samurai": {
        "jp": "侍",
        "syn": ["侍", "武士", "サムライ", "剣士", "samurai", "swordsman", "bushi"],
        "outfits": {
            "modest": [
                "{material} {main} kimono with {sub} {pattern} on the sleeves, {main} hakama with {accent} obi",
                "{sub} haori jacket with {accent} family crest",
                "{main} arm guards",
                "white tabi socks",
                "zori sandals",
            ],
            "standard": [
                "{material} {main} kimono top with {sub} {pattern} on the sleeves, short {main} hakama with {accent} obi",
                "{sub} haori jacket with {accent} family crest",
                "{main} arm guards and shin guards",
                "white thigh-high tabi socks",
                "zori sandals",
            ],
            "high": [
                "{material} {main} kimono top worn open with a sarashi chest wrap underneath, {sub} {pattern} on the sleeves, micro {main} hakama with {accent} obi",
                "{sub} haori jacket worn off the shoulders with {accent} family crest",
                "{main} arm guards",
                "white thigh-high stockings with {accent} top band",
                "zori sandals",
            ],
        },
        "male": {
            "modest": ["{material} {main} kimono with {sub} {pattern} on the sleeves, {main} hakama with {accent} obi", "{sub} haori jacket with {accent} family crest", "{main} arm guards", "white tabi socks", "zori sandals"],
            "standard": ["{material} {main} kimono with {sub} {pattern} on the sleeves, {main} hakama with {accent} obi", "{sub} haori jacket with {accent} family crest", "{main} arm guards", "white tabi socks", "zori sandals"],
            "high": ["{material} {main} kimono worn open over a bare chest with {sub} {pattern} on the sleeves, {main} hakama with {accent} obi", "{main} arm guards", "zori sandals"],
        },
        "props": ["katana at the hip with {accent} tsuba", "paper umbrella", "kiseru pipe"],
        "materials": ["silk", "cotton"],
        "palettes": [("navy", "white", "crimson"), ("black", "crimson", "gold"), ("white", "navy", "gold")],
    },
    "police": {
        "jp": "警官",
        "syn": ["警官", "警察", "婦警", "ポリス", "police", "cop", "policewoman"],
        "outfits": {
            "modest": [
                "{main} police uniform shirt with {accent} badge and {sub} {pattern} patch on the sleeve, long sleeves, {sub} necktie",
                "{main} trousers",
                "{main} police cap with {accent} badge",
                "black belt with holster",
                "black shoes",
            ],
            "standard": [
                "{main} police uniform shirt with {accent} badge and {sub} {pattern} patch on the sleeve, short sleeves, {sub} necktie",
                "{main} pencil skirt",
                "{main} police cap with {accent} badge",
                "black belt with holster",
                "black knee-high boots",
                "white gloves",
            ],
            "high": [
                "{main} cropped police shirt tied at the waist with {accent} badge and {sub} {pattern} patch, deep neckline",
                "{main} micro skirt",
                "{main} police cap with {accent} badge",
                "black belt with holster and {accent} handcuffs",
                "black thigh-high boots with garter straps",
                "white gloves",
            ],
        },
        "male": {
            "modest": ["{main} police uniform shirt with {accent} badge and {sub} {pattern} patch on the sleeve, {sub} necktie", "{main} trousers", "{main} police cap with {accent} badge", "black belt with holster", "black shoes"],
            "standard": ["{main} police uniform shirt with {accent} badge and {sub} {pattern} patch on the sleeve, {sub} necktie", "{main} trousers", "{main} police cap with {accent} badge", "black belt with holster", "black shoes"],
            "high": ["{main} police uniform shirt worn open over a bare chest, {accent} badge, {sub} {pattern} patch", "{main} trousers", "{main} police cap with {accent} badge", "black belt with holster", "black boots"],
        },
        "props": ["{accent} handcuffs", "police baton", "whistle on a cord"],
        "materials": ["polyester", "cotton"],
        "palettes": [("navy", "white", "gold"), ("black", "sky blue", "silver"), ("royal blue", "white", "gold")],
    },
    "chef": {
        "jp": "料理人",
        "syn": ["料理人", "シェフ", "コック", "パティシエ", "chef", "cook", "patissier"],
        "outfits": {
            "modest": [
                "white double-breasted chef's jacket with {accent} buttons and {sub} {pattern} on the collar",
                "{main} apron",
                "white tall chef's hat",
                "{main} trousers",
                "{main} kitchen shoes",
            ],
            "standard": [
                "white short-sleeved chef's jacket with {accent} buttons and {sub} {pattern} on the collar",
                "{main} apron with {accent} trim",
                "white tall chef's hat",
                "{main} shorts",
                "white thigh-high socks with {accent} top band",
                "{main} kitchen shoes",
            ],
            "high": [
                "white chef's jacket worn open over a {sub} bikini top, {accent} buttons, {pattern} on the collar",
                "{main} short apron with {accent} trim",
                "white tall chef's hat",
                "{main} micro shorts",
                "white thigh-high stockings with {accent} lace tops",
                "{main} heeled shoes",
            ],
        },
        "male": {
            "modest": ["white double-breasted chef's jacket with {accent} buttons and {sub} {pattern} on the collar", "{main} apron", "white tall chef's hat", "{main} trousers", "{main} kitchen shoes"],
            "standard": ["white double-breasted chef's jacket with {accent} buttons and {sub} {pattern} on the collar", "{main} apron", "white tall chef's hat", "{main} trousers", "{main} kitchen shoes"],
            "high": ["white chef's jacket worn open over a bare chest, {accent} buttons, {sub} {pattern} on the collar", "{main} apron", "white tall chef's hat", "{main} trousers", "{main} kitchen shoes"],
        },
        "props": ["oversized ladle", "frying pan", "basket of fresh bread"],
        "materials": ["cotton"],
        "palettes": [("white", "crimson", "gold"), ("white", "navy", "gold"), ("black", "white", "crimson")],
    },
    "cheerleader": {
        "jp": "チアリーダー",
        "syn": ["チア", "チアリーダー", "応援団", "cheerleader", "cheer"],
        "outfits": {
            "modest": [
                "{main} long-sleeved cheerleader top with {accent} stripes and {sub} {pattern} letter on the chest",
                "{main} knee-length pleated skirt with {sub} panels",
                "white tights",
                "white sneakers",
                "{sub} hair ribbon",
            ],
            "standard": [
                "{main} sleeveless cheerleader crop top with {accent} stripes and {sub} {pattern} letter on the chest, bare midriff",
                "{main} mini pleated skirt with {sub} panels",
                "white thigh-high socks with {accent} stripes",
                "white sneakers",
                "{sub} hair ribbon",
                "{sub} pom-poms",
            ],
            "high": [
                "{main} cheerleader bikini-style top with {accent} stripes and {sub} {pattern} letter on the chest",
                "{main} micro pleated skirt with {sub} panels",
                "white thigh-high socks with {accent} stripes",
                "white sneakers",
                "{sub} hair ribbon",
                "{sub} pom-poms",
            ],
        },
        "male": {
            "modest": ["{main} cheer uniform shirt with {accent} stripes and {sub} {pattern} letter on the chest", "{main} track pants with {accent} stripes", "white sneakers"],
            "standard": ["{main} cheer uniform shirt with {accent} stripes and {sub} {pattern} letter on the chest", "{main} track pants with {accent} stripes", "white sneakers", "{sub} headband"],
            "high": ["shirtless, {sub} {pattern} letter body paint on the chest", "{main} track pants with {accent} stripes", "white sneakers", "{sub} headband"],
        },
        "props": ["{sub} pom-poms", "megaphone with {accent} {pattern}"],
        "materials": ["polyester"],
        "palettes": [("crimson", "white", "gold"), ("royal blue", "white", "yellow"), ("black", "hot pink", "white")],
    },
    "race_queen": {
        "jp": "レースクイーン",
        "syn": ["レースクイーン", "レースクィーン", "RQ", "race queen", "grid girl"],
        "outfits": {
            "modest": [
                "{main} racing jacket with {accent} sponsor stripes and {sub} {pattern} logo on the chest, zipped up",
                "{main} long racing pants with {accent} stripes",
                "{main} racing cap with {accent} logo",
                "white boots",
            ],
            "standard": [
                "{main} racing crop jacket with {accent} sponsor stripes and {sub} {pattern} logo on the chest",
                "{main} racing mini skirt with {accent} stripes",
                "{main} racing cap with {accent} logo",
                "white thigh-high boots with {accent} trim",
                "{sub} racing umbrella",
            ],
            "high": [
                "{main} racing bikini-style top with {accent} sponsor stripes and {sub} {pattern} logo",
                "{main} racing micro skirt with {accent} stripes",
                "{main} racing cap with {accent} logo",
                "white thigh-high boots with {accent} trim",
                "{sub} racing umbrella",
                "{sub} arm sleeves with {accent} stripes",
            ],
        },
        "male": {
            "modest": ["{main} racing jacket with {accent} sponsor stripes and {sub} {pattern} logo on the chest", "{main} racing pants with {accent} stripes", "{main} racing cap with {accent} logo", "white boots"],
            "standard": ["{main} racing jacket with {accent} sponsor stripes and {sub} {pattern} logo on the chest", "{main} racing pants with {accent} stripes", "{main} racing cap with {accent} logo", "white boots"],
            "high": ["{main} racing jacket worn open over a bare chest, {accent} sponsor stripes, {sub} {pattern} logo", "{main} racing pants with {accent} stripes", "{main} racing cap with {accent} logo", "white boots"],
        },
        "props": ["{sub} racing umbrella", "checkered flag", "racing helmet under the arm"],
        "materials": ["latex", "polyester"],
        "palettes": [("white", "crimson", "black"), ("black", "hot pink", "white"), ("royal blue", "white", "yellow")],
    },
    "western": {
        "jp": "カウガール・ウエスタン",
        "syn": ["カウガール", "ウエスタン", "西部", "ガンマン", "cowgirl", "western", "gunslinger", "cowboy"],
        "outfits": {
            "modest": [
                "{material} {main} western shirt with {accent} piping and {sub} {pattern} embroidery on the yoke, long sleeves",
                "{sub} vest with {accent} buttons",
                "{main} jeans with {accent} belt buckle",
                "{main} cowboy hat with {accent} band",
                "{main} cowboy boots",
                "{sub} bandana",
            ],
            "standard": [
                "{material} {main} western shirt tied at the waist with {accent} piping and {sub} {pattern} embroidery on the yoke",
                "{sub} vest with {accent} buttons",
                "{main} denim shorts with {accent} belt buckle",
                "{main} cowboy hat with {accent} band",
                "{main} cowboy boots",
                "{sub} bandana",
                "gun holster on the hip",
            ],
            "high": [
                "{material} {main} western crop top tied at the chest with {accent} piping and {sub} {pattern} embroidery, deep neckline",
                "{sub} open vest with {accent} buttons",
                "{main} denim micro shorts with {accent} belt buckle",
                "{main} cowboy hat with {accent} band",
                "{main} thigh-high cowboy boots",
                "{sub} bandana",
                "gun holster on the thigh",
            ],
        },
        "male": {
            "modest": ["{material} {main} western shirt with {accent} piping and {sub} {pattern} embroidery on the yoke", "{sub} vest with {accent} buttons", "{main} jeans with {accent} belt buckle", "{main} cowboy hat with {accent} band", "{main} cowboy boots", "{sub} bandana"],
            "standard": ["{material} {main} western shirt with {accent} piping and {sub} {pattern} embroidery on the yoke", "{sub} vest with {accent} buttons", "{main} jeans with {accent} belt buckle", "{main} cowboy hat with {accent} band", "{main} cowboy boots", "gun holster on the hip"],
            "high": ["{sub} open vest over a bare chest with {accent} buttons, {pattern} embroidery", "{main} jeans with {accent} belt buckle", "{main} cowboy hat with {accent} band", "{main} cowboy boots", "{sub} bandana", "gun holster on the hip"],
        },
        "props": ["revolver", "lasso", "harmonica"],
        "materials": ["denim", "leather"],
        "palettes": [("brown", "cream", "gold"), ("crimson", "brown", "gold"), ("black", "white", "silver")],
    },
    "waitress": {
        "jp": "ウェイトレス",
        "syn": ["ウェイトレス", "カフェ", "喫茶店", "給仕", "waitress", "cafe", "diner"],
        "outfits": {
            "modest": [
                "{material} {main} long-sleeved waitress dress with white collar and {accent} piping, {sub} {pattern} on the hem, knee-length",
                "white frilled apron with {accent} ribbon",
                "white cafe headband",
                "{main} opaque tights",
                "{main} flat shoes",
                "{sub} bow tie",
            ],
            "standard": [
                "{material} {main} short-sleeved waitress dress with white collar and {accent} piping, {sub} {pattern} on the hem, above-knee",
                "white frilled apron with {accent} ribbon",
                "white cafe headband",
                "white thigh-high socks with {accent} top band",
                "{main} mary janes",
                "{sub} bow tie",
            ],
            "high": [
                "{material} {main} off-shoulder mini waitress dress with {accent} piping, deep neckline, {sub} {pattern} on the hem",
                "white frilled apron with {accent} ribbon",
                "white cafe headband",
                "white thigh-high stockings with {accent} lace tops and garter belt",
                "{main} heeled mary janes",
                "{sub} bow tie",
            ],
        },
        "male": {
            "modest": ["{material} {main} waiter's vest with {accent} buttons over a white shirt, {sub} bow tie with {pattern}", "{sub} long apron", "{main} trousers", "{main} dress shoes"],
            "standard": ["{material} {main} waiter's vest with {accent} buttons over a white shirt, {sub} bow tie with {pattern}", "{sub} long apron", "{main} trousers", "{main} dress shoes"],
            "high": ["{material} {main} waiter's vest worn open over a bare chest, {accent} buttons, {sub} bow tie with {pattern}", "{sub} short apron", "{main} trousers", "{main} dress shoes"],
        },
        "props": ["serving tray with a parfait", "coffee pot", "order notepad"],
        "materials": ["cotton"],
        "palettes": [("black", "white", "crimson"), ("brown", "cream", "gold"), ("pastel pink", "white", "crimson")],
    },
    "flight_attendant": {
        "jp": "キャビンアテンダント",
        "syn": ["CA", "キャビンアテンダント", "客室乗務員", "スチュワーデス", "flight attendant", "stewardess", "cabin crew"],
        "outfits": {
            "modest": [
                "{material} {main} flight attendant jacket with {accent} piping and {sub} {pattern} wing badge, white blouse, {sub} scarf",
                "{main} long pencil skirt",
                "{main} pillbox hat with {accent} trim",
                "sheer black pantyhose",
                "{main} pumps",
            ],
            "standard": [
                "{material} {main} flight attendant jacket with {accent} piping and {sub} {pattern} wing badge, white blouse, {sub} scarf",
                "{main} knee-length pencil skirt",
                "{main} pillbox hat with {accent} trim",
                "sheer black pantyhose",
                "{main} pumps",
                "{sub} gloves",
            ],
            "high": [
                "{material} {main} flight attendant jacket with {accent} piping open over a {sub} lace bra, {pattern} wing badge, {sub} scarf",
                "{main} micro pencil skirt",
                "{main} pillbox hat with {accent} trim",
                "sheer black pantyhose with {accent} garter straps",
                "{main} stiletto pumps",
                "{sub} gloves",
            ],
        },
        "male": {
            "modest": ["{material} {main} pilot jacket with {accent} piping and {sub} {pattern} wing badge, white shirt, {sub} necktie", "{main} trousers", "{main} pilot cap with {accent} badge", "{main} dress shoes"],
            "standard": ["{material} {main} pilot jacket with {accent} piping and {sub} {pattern} wing badge, white shirt, {sub} necktie", "{main} trousers", "{main} pilot cap with {accent} badge", "{main} dress shoes"],
            "high": ["{material} {main} pilot jacket worn open over a bare chest, {accent} piping, {sub} {pattern} wing badge, loosened {sub} necktie", "{main} trousers", "{main} pilot cap with {accent} badge", "{main} dress shoes"],
        },
        "props": ["rolling suitcase", "boarding pass", "tray of drinks"],
        "materials": ["wool", "polyester"],
        "palettes": [("navy", "white", "gold"), ("crimson", "white", "gold"), ("sky blue", "white", "navy")],
    },
    "fortune_teller": {
        "jp": "占い師",
        "syn": ["占い師", "占い", "タロット", "fortune teller", "fortune-teller", "diviner", "tarot", "oracle"],
        "outfits": {
            "modest": [
                "{material} {main} hooded fortune teller robe with {accent} coin trim on the hood, {sub} {pattern} embroidered on the chest, long wide sleeves",
                "{sub} shawl with {accent} tassels",
                "{sub} head scarf with {accent} coins",
                "{accent} bangles on both wrists",
                "{main} flat shoes",
            ],
            "standard": [
                "{material} {main} fortune teller dress with {accent} coin trim, {sub} {pattern} embroidered on the bodice, off-shoulder, knee-length layered skirt",
                "{sub} shawl with {accent} tassels",
                "{sub} head scarf with {accent} coins",
                "{accent} bangles on both wrists",
                "{accent} hoop earrings",
                "{main} sandals",
            ],
            "high": [
                "{material} {main} fortune teller top with a deep plunging neckline framed in {accent} coin trim, {sub} {pattern} embroidered, sheer {main} long skirt with high side slits",
                "{sub} sheer shawl with {accent} tassels",
                "{sub} head scarf with {accent} coins",
                "{accent} bangles on both wrists",
                "{accent} hoop earrings",
                "{main} sandals",
            ],
        },
        "male": {
            "modest": ["{material} {main} hooded fortune teller robe with {accent} coin trim, {sub} {pattern} embroidered on the chest", "{sub} sash", "{accent} rings on every finger", "{main} boots"],
            "standard": ["{material} {main} fortune teller vest with {accent} coin trim over a {sub} shirt, {pattern} embroidered", "{sub} head scarf", "{accent} rings on every finger", "{main} pants", "{main} boots"],
            "high": ["{material} {main} fortune teller vest worn open over a bare chest with {accent} coin trim, {sub} {pattern} embroidered", "{sub} head scarf", "{accent} rings on every finger", "{main} pants", "{main} sandals"],
        },
        "props": ["crystal ball with a {accent} glow", "spread of tarot cards", "{accent} pendulum on a chain"],
        "materials": ["velvet", "silk"],
        "palettes": [("dark purple", "black", "gold"), ("navy", "wine red", "gold"), ("black", "purple", "silver")],
    },
}

# モチーフの gap_roles で参照している別名（存在しないキーを吸収する）
ROLE_ALIASES = {
    "gal_street": "casual_street",
}

# ---------------------------------------------------------------------------
# 共通パーツ
# ---------------------------------------------------------------------------

# 模様のスタイル修飾。モチーフの模様と組み合わせて「どんな模様か」をより具体的に固定する
PATTERN_STYLES = [
    "small repeating", "large", "fine", "bold", "scattered", "subtle tone-on-tone",
    "metallic-thread", "outlined", "tiny all-over", "single large",
]

# 目の構造: 色 / 形 / 開き具合 / 瞳孔 / ハイライト / まつ毛 / 眉 / メイク / その他
EYE_SHAPES = ["tsurime", "tareme", "jitome", "sanpaku"]
EYE_LIDS = ["half-closed eyes", "narrowed eyes", "wide-eyed"]
EYE_PUPILS = ["slit pupils", "heart-shaped pupils", "star-shaped pupils", "ringed eyes", "constricted pupils", "symbol-shaped pupils", "diamond-shaped pupils", "no pupils"]
EYE_HIGHLIGHTS = ["sparkling eyes", "empty eyes", "glowing eyes"]
EYE_LASHES = ["long eyelashes", "thick eyelashes"]
EYE_BROWS = ["thick eyebrows", "thin eyebrows", "short eyebrows", "v-shaped eyebrows"]
EYE_MAKEUP = ["eyeliner", "mascara", "eyeshadow", "red eyeshadow", "{accent} eyeshadow"]
EYE_DETAILS = ["mole under eye", "bags under eyes", "eyes visible through hair", "gradient eyes"]

# 性格ごとの目のプロファイル（候補が無いカテゴリは出さない）。確率は engine 側（EYE_PROBS）
EYE_PROFILES = {
    "tsundere":  {"shape": ["tsurime"], "lashes": ["long eyelashes"], "brows": ["thick eyebrows", "v-shaped eyebrows"], "highlights": ["sparkling eyes"]},
    "amaama":    {"shape": ["tareme"], "pupils": ["heart-shaped pupils"], "highlights": ["sparkling eyes"], "lashes": ["long eyelashes"]},
    "mesugaki":  {"shape": ["jitome", "tsurime"], "lid": ["half-closed eyes"], "highlights": ["sparkling eyes"], "brows": ["short eyebrows"]},
    "seiso":     {"shape": ["tareme"], "lashes": ["long eyelashes"], "brows": ["thin eyebrows"]},
    "jirai":     {"shape": ["tareme"], "highlights": ["empty eyes"], "makeup": ["red eyeshadow", "eyeliner", "mascara"], "details": ["bags under eyes"], "lashes": ["long eyelashes"]},
    "uchiki":    {"shape": ["tareme"], "lid": ["half-closed eyes"], "details": ["eyes visible through hair"]},
    "kuudere":   {"shape": ["tsurime"], "lid": ["half-closed eyes", "narrowed eyes"], "brows": ["thin eyebrows"]},
    "yandere":   {"shape": ["tareme"], "pupils": ["constricted pupils"], "highlights": ["empty eyes"], "lid": ["wide-eyed"]},
    "genki":     {"shape": ["tsurime"], "highlights": ["sparkling eyes"], "brows": ["thick eyebrows"], "lid": ["wide-eyed"]},
    "ojousama":  {"shape": ["tsurime"], "lashes": ["long eyelashes", "thick eyelashes"], "makeup": ["eyeliner"]},
    "oneesan":   {"shape": ["tareme"], "lid": ["half-closed eyes"], "lashes": ["long eyelashes"], "details": ["mole under eye"], "makeup": ["eyeliner", "mascara"]},
    "gal":       {"shape": ["tsurime"], "lashes": ["thick eyelashes", "long eyelashes"], "makeup": ["eyeliner", "mascara", "eyeshadow"]},
    "chuuni":    {"shape": ["tsurime"], "pupils": ["slit pupils", "symbol-shaped pupils"], "highlights": ["glowing eyes"], "details": ["eyes visible through hair"]},
    "bokukko":   {"shape": ["tsurime"], "brows": ["thick eyebrows"]},
    "dojikko":   {"shape": ["tareme"], "highlights": ["sparkling eyes"], "lid": ["wide-eyed"]},
    "sadistic":  {"shape": ["tsurime"], "lid": ["narrowed eyes", "half-closed eyes"], "lashes": ["long eyelashes"], "makeup": ["eyeliner"]},
    "juujun":    {"shape": ["tareme"], "lid": ["half-closed eyes"], "highlights": ["sparkling eyes"], "lashes": ["long eyelashes"]},
    "okubyou":   {"shape": ["tareme"], "lid": ["wide-eyed"], "highlights": ["sparkling eyes"], "lashes": ["long eyelashes"]},
    "jishinka":  {"shape": ["tsurime"], "highlights": ["sparkling eyes"], "lashes": ["long eyelashes"], "brows": ["thick eyebrows"]},
    "haraguro":  {"shape": ["tareme"], "lid": ["narrowed eyes"], "highlights": ["empty eyes"]},
    "fushigi":   {"shape": ["tareme"], "pupils": ["star-shaped pupils", "ringed eyes"], "highlights": ["sparkling eyes"], "lid": ["wide-eyed"]},
    "iinchou":   {"shape": ["tsurime"], "brows": ["thin eyebrows"]},
    "ottori":    {"shape": ["tareme"], "lid": ["half-closed eyes"]},
    "nekketsu":  {"shape": ["tsurime"], "brows": ["thick eyebrows"], "highlights": ["sparkling eyes"]},
    "dokuzetsu": {"shape": ["jitome"], "lid": ["half-closed eyes"]},
    "aneki":     {"shape": ["tsurime"], "lashes": ["long eyelashes"], "makeup": ["eyeliner"]},
}
# 目の形の自然文での言い換え（Anima の Qwen エンコーダ向け。タグだけでは画風に負けるので文章で補強する）
EYE_SHAPE_NL = {
    "tsurime": "upturned, slanted eyes with sharp outer corners",
    "tareme": "downturned, droopy eyes with soft outer corners",
    "jitome": "flat, half-lidded deadpan eyes",
    "sanpaku": "sanpaku eyes with sclera visible below the iris",
}
# 反対の形（negative に入れる）
EYE_OPPOSITE = {"tsurime": "tareme", "tareme": "tsurime", "jitome": "wide-eyed", "sanpaku": "tareme"}
# 目の大きさ・輪郭の軸（形とは独立に組み合わせる）
EYE_SIZES = ["large round eyes", "almond-shaped eyes", "narrow eyes", "small eyes"]
# 形の強弱: (キー, 重み係数, 自然文の副詞)
EYE_INTENSITY = [("slight", 0.85, "slightly"), ("normal", 1.0, ""), ("strong", 1.15, "strongly")]
EYE_INTENSITY_WEIGHTS = [25, 45, 30]

# 性格の「署名」: 常に入るタグと、性格を表す自然文（{pron}=She/He, {poss}=her/his）
ARCH_SIGNATURE = {
    "tsundere":  {"tags": ["tsundere"], "persona": "{pron} is a tsundere: proud and sharp-tongued on the surface, blushing and flustered underneath."},
    "amaama":    {"tags": [], "persona": "{pron} is sweet and affectionate, with a soft, doting smile and gentle body language."},
    "mesugaki":  {"tags": ["smug", "fang"], "persona": "{pron} is a bratty, cocky little tease who looks down on the viewer with a smug grin."},
    "seiso":     {"tags": [], "persona": "{pron} is pure and graceful, with a serene, well-mannered air."},
    "jirai":     {"tags": ["bandaged wrist"], "persona": "{pron} is a jirai-kei girl: fragile, clingy and a little unhinged, with tired made-up eyes."},
    "uchiki":    {"tags": ["dandere"], "persona": "{pron} is timid and withdrawn, hiding behind {poss} hair and avoiding eye contact."},
    "kuudere":   {"tags": ["kuudere"], "persona": "{pron} is cool and composed, with a calm, unreadable expression."},
    "yandere":   {"tags": ["yandere"], "persona": "{pron} is a yandere: sweetly smiling with hollow, obsessive eyes."},
    "genki":     {"tags": [], "persona": "{pron} is bright and energetic, bursting with cheerful motion."},
    "ojousama":  {"tags": [], "persona": "{pron} is a haughty young lady of high class, chin raised with refined confidence."},
    "oneesan":   {"tags": [], "persona": "{pron} is a mature, teasing older-sister type with relaxed, knowing eyes."},
    "gal":       {"tags": ["gyaru"], "persona": "{pron} is a flashy, outgoing gyaru with heavy makeup and a playful attitude."},
    "chuuni":    {"tags": ["eyepatch"], "persona": "{pron} is a chuunibyou who strikes dramatic poses and believes in {poss} hidden powers."},
    "bokukko":   {"tags": [], "persona": "{pron} is a boyish, sporty tomboy with a confident grin."},
    "dojikko":   {"tags": [], "persona": "{pron} is a clumsy, flustered airhead, always a step from tripping."},
    "sadistic":  {"tags": ["riding crop", "evil smile", "looking down at viewer"], "persona": "{pron} is a cruel, dominant sadist who looks down on the viewer with a cold, condescending smile, holding a riding crop."},
    "juujun":    {"tags": ["collar"], "persona": "{pron} is obedient and devoted, keeping {poss} eyes lowered and {poss} hands folded, waiting quietly for instructions."},
    "okubyou":   {"tags": ["scared", "trembling", "tears"], "persona": "{pron} is a timid coward, trembling with teary eyes and hugging {poss} own body, ready to flinch at anything."},
    "jishinka":  {"tags": ["confident"], "persona": "{pron} is supremely self-assured, standing tall with {poss} chest out and a confident, unshakable smile."},
    "haraguro":  {"tags": [], "persona": "{pron} wears a perfect polite smile that hides a scheming, two-faced nature."},
    "fushigi":   {"tags": [], "persona": "{pron} is an eccentric, spacey dreamer whose gaze drifts somewhere far away."},
    "iinchou":   {"tags": ["glasses"], "persona": "{pron} is a strict, diligent class representative who pushes up {poss} glasses disapprovingly."},
    "ottori":    {"tags": [], "persona": "{pron} is gentle and laid-back, moving slowly with a relaxed, sleepy smile."},
    "nekketsu":  {"tags": [], "persona": "{pron} is hot-blooded and passionate, eyes burning with determination."},
    "dokuzetsu": {"tags": [], "persona": "{pron} is sharp-tongued and sarcastic, watching the viewer with unimpressed, half-lidded eyes."},
    "aneki":     {"tags": [], "persona": "{pron} is a bold big-sister leader type with a loud laugh and commanding presence."},
}

# 各カテゴリを出す確率（shape は常に出す）
EYE_PROBS = {"lid": 0.5, "pupils": 0.5, "highlights": 0.6, "lashes": 0.5, "brows": 0.4, "makeup": 0.7, "details": 0.5}

# 指示文の目ワード -> (カテゴリ, タグ)
EYE_WORDS = {
    ("shape", "tsurime"): ["ツリ目", "つり目", "釣り目", "tsurime"],
    ("shape", "tareme"): ["タレ目", "たれ目", "垂れ目", "tareme"],
    ("shape", "jitome"): ["ジト目", "じと目", "jitome"],
    ("shape", "sanpaku"): ["三白眼", "sanpaku"],
    ("lid", "half-closed eyes"): ["半目", "半眼", "half-closed eyes"],
    ("lid", "narrowed eyes"): ["細目", "narrowed eyes"],
    ("lid", "wide-eyed"): ["見開き", "wide-eyed"],
    ("pupils", "slit pupils"): ["猫目", "縦長瞳孔", "縦瞳", "slit pupils"],
    ("pupils", "heart-shaped pupils"): ["ハート瞳", "ハート目", "heart pupils", "heart-shaped pupils"],
    ("pupils", "star-shaped pupils"): ["星瞳", "星目", "star pupils", "star-shaped pupils"],
    ("pupils", "ringed eyes"): ["ぐるぐる目", "リング瞳", "ringed eyes"],
    ("pupils", "constricted pupils"): ["収縮瞳孔", "小さい瞳孔", "constricted pupils"],
    ("pupils", "no pupils"): ["瞳孔なし", "no pupils"],
    ("highlights", "sparkling eyes"): ["キラキラ目", "キラキラ", "sparkling eyes"],
    ("highlights", "empty eyes"): ["ハイライトなし", "死んだ目", "レイプ目", "empty eyes"],
    ("highlights", "glowing eyes"): ["光る目", "発光目", "glowing eyes"],
    ("lashes", "long eyelashes"): ["まつ毛長め", "長いまつ毛", "long eyelashes"],
    ("lashes", "thick eyelashes"): ["濃いまつ毛", "thick eyelashes"],
    ("brows", "thick eyebrows"): ["太眉", "thick eyebrows"],
    ("brows", "thin eyebrows"): ["細眉", "thin eyebrows"],
    ("brows", "short eyebrows"): ["短眉", "short eyebrows"],
    ("brows", "v-shaped eyebrows"): ["キリッと眉", "v-shaped eyebrows"],
    ("makeup", "red eyeshadow"): ["赤シャドウ", "赤アイシャドウ", "red eyeshadow"],
    ("makeup", "eyeliner"): ["アイライン", "eyeliner"],
    ("details", "bags under eyes"): ["目の隈", "クマ", "bags under eyes"],
    ("details", "gradient eyes"): ["グラデ瞳", "gradient eyes"],
}

# 髪の構造: 色 / 長さ / 質感 / 型 / 前髪 / 横髪 / 差し色・アホ毛
BANGS = ["blunt bangs", "swept bangs", "parted bangs", "hair between eyes", "asymmetrical bangs", "braided bangs", "crossed bangs", "curtained hair"]
HAIR_TEXTURES = ["straight hair", "wavy hair", "curly hair", "messy hair", "fluffy hair", "sleek hair"]
HAIR_TEXTURE_KEYWORDS = ["straight", "wavy", "curly", "messy", "fluffy", "spiky", "drill", "braid", "sleek", "wool"]
SIDELOCKS = ["sidelocks", "long sidelocks", "short sidelocks", "hair intakes", "hair flaps"]
# 差し色・アホ毛など（40% で1つ）。{accent} はテーマのアクセント色
HAIR_EXTRAS = ["ahoge", "antenna hair", "{accent} colored tips", "colored inner hair, {accent} inner hair", "streaked hair, {accent} streak", "two-tone hair", "gradient hair", "hair flower", "{accent} hairclip", "{accent} hair ribbon"]
HAIR_LENGTH_KEYWORDS = [("very long", "very long hair"), ("long", "long hair"), ("short", "short hair"), ("bob", "medium hair"), ("medium", "medium hair"), ("pixie", "very short hair")]

# 性格に体型指定が無い時の候補（女性）
BODY_DEFAULT_FEMALE = ["slender", "medium build", "petite", "curvy"]
BODY_DEFAULT_MALE = ["slender", "medium build", "athletic", "lean"]
CHEST_SIZES = ["small breasts", "medium breasts", "large breasts"]

# 服装アイテムの部位スロット（2系統の融合で矛盾を避けるために使う）。上から順に最初に一致したスロット
OUTFIT_SLOTS = [
    ("top", ["bikini top", "bikini armor", "breastplate", "crop top", "serafuku", "blazer", "jacket", "coat", "hoodie", "shirt", "blouse",
             "sweater", "cardigan", "vest", "waistcoat", "tailcoat", "corset", "camisole", "sports bra", "tank top", "tunic", "sarashi",
             "lace bra", "bra", "lingerie", "rash guard", "gakuran", "top"]),
    ("bottom", ["skirt", "shorts", "pants", "hakama", "buruma", "jeans", "denim", "sarong", "trousers", "boxers", "swim trunks", "swim briefs"]),
    ("full", ["dress", "gown", "kimono", "furisode", "habit", "robe", "bodysuit", "plugsuit", "pajamas", "negligee", "babydoll", "toga",
              "leotard", "one-piece", "swimsuit", "bikini", "uniform", "ninja outfit", "jester costume", "harem outfit", "racing suit",
              "track suit", "pantsuit", "suit", "cassock", "kariginu", "full armor", "plate armor", "armor", "nightgown", "yukata",
              "sleepwear", "changshan", "chiton", "regalia", "garb", "shozoku", "chinese clothes", "greek clothes", "vestments"]),
    ("legs", ["thighhighs", "pantyhose", "kneehighs", "over-kneehighs", "socks", "leg wraps", "kyahan", "tights", "bare legs", "fishnets", "legwear", "stockings"]),
    ("feet", ["boots", "shoes", "heels", "sandals", "tabi", "loafers", "sneakers", "zori", "geta", "flats", "footwear", "pumps", "mary janes", "slippers", "barefoot"]),
    ("head", ["hat", "cap", "hood", "veil", "headdress", "tiara", "crown", "mitre", "headband", "bonnet", "bandana", "head scarf", "circlet",
              "helmet", "goggles", "sleep mask", "rabbit ears", "tricorne", "laurel", "eboshi", "fake animal ears", "hitaikakushi"]),
    ("face", ["face mask", "surgical mask", "eyepatch", "glasses", "mask"]),
    ("hands", ["gloves", "gauntlets", "bracer", "arm guards", "wrist cuffs", "arm warmers", "tekko", "bangle", "bracelet", "armlet", "kote", "rings"]),
    ("neck", ["choker", "detached collar", "white collar", "collar", "necktie", "bowtie", "bow tie", "scarf", "necklace", "stole", "rosary", "neckerchief", "ribbon tie", "jabot", "pallium"]),
    ("outer", ["cape", "apron", "shawl", "haori", "cloak", "half cape", "himation", "surcoat", "pauldron", "pauldrons"]),
    ("waist", ["sash", "belt", "obi", "obijime"]),
    ("sleeves", ["long sleeves", "short sleeves", "sleeveless", "detached sleeves", "puffy sleeves", "wide sleeves", "puffy short sleeves", "puffy long sleeves"]),
    ("identity", ["nun", "maid", "ninja", "witch", "wizard", "nurse", "doctor", "idol", "magical girl", "magical boy", "office lady", "playboy bunny",
                  "princess", "prince", "pirate", "jester", "teacher", "dancer", "sukeban", "delinquent", "saint", "priest", "hero", "merchant", "pope",
                  "fortune teller", "archer", "samurai", "policewoman", "police", "chef", "cheerleader", "race queen", "waitress", "waiter",
                  "flight attendant", "pilot", "butler", "miko", "kannushi", "knight", "school uniform", "sportswear", "kunoichi", "lolita fashion",
                  "gothic lolita", "cowboy western", "victorian", "steampunk"]),
    ("descriptor", ["cleavage", "midriff", "bare shoulders", "side slit", "cutout", "open clothes", "see-through", "high collar", "double-breasted",
                    "frills", "lace trim", "garter straps", "garter belt", "off-shoulder", "strapless", "highleg", "plunging neckline",
                    "sweetheart neckline", "unbuttoned", "tied shirt", "hood down", "hood up", "skin tight", "two-tone", "mismatched",
                    "bare pectorals", "topless male", "layered", "miniskirt", "microskirt", "navel"]),
]
# 融合時に 2つ目の系統から取り込むスロットと上限（土台の系統が同じスロットを持つ場合は原則スキップ）
FUSION_TAKE = {"head": 1, "face": 1, "hands": 1, "neck": 1, "outer": 1, "waist": 1, "identity": 2, "accessory": 2, "legs": 1, "feet": 1}
# 土台側に既にあっても、この確率で 2つ目側が勝つスロット（どちらが主か seed で揺らぐ）
FUSION_OVERRIDE = {"head": 0.4, "outer": 0.4, "feet": 0.3, "legs": 0.3}

# 高露出のときに追加する露出部位タグ（strict/full 共通）。seed で3つ選び、先頭だけ重み付き。
# "revealing clothes" は特定の衣装構造を強く学習しているため固定アンカーには使わない
EXPOSURE_HIGH_COUNT = 3
EXPOSURE_HIGH_EXTRAS = ["sideboob", "underboob", "backless outfit", "see-through", "bare shoulders", "thighs", "navel", "bare back"]
EXPOSURE_HIGH_EXTRAS_MALE = ["bare pectorals", "abs", "bare shoulders", "bare back", "thighs", "see-through"]
EXPOSURE_HIGH_NEGATIVE = ["covered navel", "covered collarbone", "turtleneck"]

# ---------------------------------------------------------------------------
# 手持ち（武器・小道具）。既定ではキャラは何も持たない（モチーフ装飾が手持ち化するのを防ぐ）。
# 各項目: types=(説明, booruタグ), slots=部位ごとの選択肢（{main}/{sub}/{accent}/{pattern} 可）, holds=(持ち方の説明, booruタグ)
# 同じ seed なら同じ形状になり、形状の細部まで文章で固定される
# ---------------------------------------------------------------------------
HANDHELDS = {
    "sword": {
        "jp": "剣", "syn": ["剣", "ソード", "sword", "longsword", "rapier", "greatsword"],
        "tags": ["sword", "weapon"],
        "types": [("longsword", "sword"), ("rapier", "rapier"), ("greatsword", "greatsword"), ("scimitar", "scimitar"), ("short sword", "sword"), ("ornate ceremonial sword", "sword")],
        "slots": {
            "blade": ["polished silver blade", "black blade", "crimson-tinted blade", "translucent crystal blade", "golden blade", "glowing {accent} blade"],
            "guard": ["straight cross guard", "winged guard", "basket hilt", "ornate curved guard", "round disc guard"],
            "hilt": ["{main} leather-wrapped hilt", "{accent} wire-wrapped hilt", "black cord-wrapped hilt"],
            "pommel": ["{accent} gem pommel", "round steel pommel", "skull-shaped pommel", "crescent-shaped pommel"],
            "engraving": ["{pattern} engraving along the fuller", "rune engraving along the blade", "plain unadorned blade"],
        },
        "holds": [("held in the right hand pointing down", "holding sword"), ("resting on the shoulder", "holding sword, over shoulder"), ("planted tip-down in front", "planted sword"), ("held in both hands", "holding sword, two-handed"), ("sheathed at the hip in a {main} scabbard with {accent} fittings", "sheathed, sword at hip")],
    },
    "katana": {
        "jp": "刀", "syn": ["刀", "カタナ", "日本刀", "katana", "odachi", "wakizashi"],
        "tags": ["katana", "sword", "weapon"],
        "types": [("katana", "katana"), ("odachi", "katana"), ("wakizashi", "katana"), ("tachi", "katana")],
        "slots": {
            "blade": ["polished steel blade with a wavy hamon", "black blade", "crimson-tinted blade", "glowing {accent} blade"],
            "tsuba": ["round {accent} tsuba", "square tsuba", "flower-shaped tsuba", "cross-shaped tsuba"],
            "tsuka": ["{main} silk-wrapped tsuka", "{accent} silk-wrapped tsuka", "black silk-wrapped tsuka with {accent} menuki"],
            "saya": ["{main} lacquered saya with {accent} sageo cord", "black lacquered saya with {pattern} maki-e", "white saya with gold fittings"],
        },
        "holds": [("held in the right hand", "holding sword"), ("drawn in both hands", "holding sword, two-handed"), ("sheathed at the hip", "sheathed, katana at hip"), ("resting on the shoulder", "holding sword, over shoulder"), ("held by the saya in the left hand", "holding sheathed sword")],
    },
    "staff": {
        "jp": "杖", "syn": ["杖", "スタッフ", "staff", "mage staff"],
        "tags": ["staff", "holding staff"],
        "types": [("long wooden staff", "staff"), ("crystal-tipped mage staff", "staff"), ("metal mage staff", "staff"), ("twisted branch staff", "staff"), ("crozier-like holy staff", "staff")],
        "slots": {
            "top": ["{accent} crystal orb at the top", "crescent moon ornament at the top", "star-shaped ornament at the top", "ring holding a {accent} gem at the top", "skull ornament at the top"],
            "shaft": ["{main} shaft with {accent} bands", "dark wood shaft carved with {pattern}", "white shaft with gold filigree", "black metal shaft"],
            "extra": ["{accent} ribbons tied below the head", "small bells hanging from the top", "no extra ornaments"],
        },
        "holds": [("held upright in the right hand", "holding staff"), ("held across the body in both hands", "holding staff"), ("resting against the shoulder", "holding staff")],
    },
    "wand": {
        "jp": "短杖", "syn": ["短杖", "ワンド", "wand", "魔法のステッキ", "ステッキ"],
        "tags": ["wand", "holding wand"],
        "types": [("short wand", "wand"), ("star-tipped wand", "wand"), ("heart-tipped wand", "wand"), ("crystal wand", "wand")],
        "slots": {
            "tip": ["{accent} star at the tip", "{accent} heart at the tip", "{accent} crystal at the tip", "crescent moon at the tip"],
            "shaft": ["{main} shaft with {accent} spiral", "white shaft with gold bands", "black shaft with {pattern} engraving"],
            "extra": ["{accent} ribbons tied below the tip", "small wings on the tip", "no extra ornaments"],
        },
        "holds": [("held in the right hand", "holding wand"), ("pointed forward", "holding wand"), ("held against the chest", "holding wand")],
    },
    "grimoire": {
        "jp": "魔導書・本", "syn": ["魔導書", "本", "書物", "グリモワール", "grimoire", "book", "tome", "spellbook"],
        "tags": ["book", "holding book"],
        "types": [("thick grimoire", "book"), ("small leather-bound book", "book"), ("ancient tome", "book"), ("ornate spell book", "book")],
        "slots": {
            "cover": ["{main} leather cover with {accent} metal corners", "black cover with {accent} {pattern} emblem", "white cover with gold filigree", "dark red cover with {accent} clasp"],
            "clasp": ["{accent} lock clasp", "chain binding", "{accent} ribbon bookmark", "no clasp"],
        },
        "holds": [("held open in both hands", "holding book, open book"), ("held closed against the chest", "holding book, closed book"), ("tucked under the arm", "holding book, closed book"), ("held in one hand", "holding book")],
    },
    "bow": {
        "jp": "弓", "syn": ["弓", "ボウ", "bow", "longbow", "archery"],
        "tags": ["bow (weapon)", "holding bow (weapon)"],
        "types": [("longbow", "bow (weapon)"), ("recurve bow", "bow (weapon)"), ("ornate ceremonial bow", "bow (weapon)"), ("short bow", "bow (weapon)")],
        "slots": {
            "limbs": ["{main} limbs with {accent} tips", "white wood limbs with gold filigree", "black limbs with {accent} runes", "dark wood limbs with {pattern} carving"],
            "grip": ["{accent} leather grip", "{main} wrapped grip", "silver grip"],
            "quiver": ["{main} quiver on the back with {accent}-fletched arrows", "{sub} quiver at the hip", "no quiver"],
        },
        "holds": [("held in the left hand, lowered", "holding bow (weapon)"), ("drawn with an arrow nocked", "holding bow (weapon), drawing bow, arrow (projectile)"), ("slung over the shoulder", "bow (weapon) on back")],
    },
    "spear": {
        "jp": "槍", "syn": ["槍", "スピア", "ハルバード", "薙刀", "spear", "halberd", "naginata", "lance", "trident"],
        "tags": ["polearm", "holding polearm", "weapon"],
        "types": [("spear", "spear"), ("halberd", "halberd"), ("naginata", "naginata"), ("trident", "trident"), ("lance", "lance")],
        "slots": {
            "head": ["silver leaf-shaped head", "black barbed head", "{accent} crystal head", "golden ornate head"],
            "shaft": ["{main} shaft with {accent} bands", "dark wood shaft", "red lacquered shaft", "black metal shaft with {pattern} engraving"],
            "tassel": ["{accent} tassel below the head", "{sub} ribbon below the head", "no tassel"],
        },
        "holds": [("held upright in the right hand", "holding polearm"), ("held across the body", "holding polearm"), ("resting on the shoulder", "holding polearm, over shoulder")],
    },
    "scythe": {
        "jp": "鎌", "syn": ["鎌", "サイズ", "大鎌", "scythe"],
        "tags": ["scythe", "holding scythe", "weapon"],
        "types": [("oversized scythe", "scythe"), ("war scythe", "scythe"), ("crescent scythe", "scythe")],
        "slots": {
            "blade": ["black blade with {accent} edge", "silver crescent blade", "glowing {accent} blade", "bone-like white blade"],
            "shaft": ["black shaft with {accent} bands", "bone-like white shaft", "dark wood shaft", "{main} shaft with {pattern} engraving"],
            "ornament": ["skull ornament at the joint", "{accent} chain hanging from the joint", "{accent} ribbon at the joint"],
        },
        "holds": [("held in both hands", "holding scythe, two-handed"), ("resting on the shoulder", "holding scythe, over shoulder"), ("planted beside", "holding scythe")],
    },
    "dagger": {
        "jp": "短剣", "syn": ["短剣", "ダガー", "ナイフ", "dagger", "knife", "daggers"],
        "tags": ["dagger", "holding dagger", "weapon"],
        "types": [("dagger", "dagger"), ("curved dagger", "dagger"), ("twin daggers", "dagger, dual wielding"), ("stiletto", "dagger")],
        "slots": {
            "blade": ["polished silver blade", "black blade", "{accent}-tinted blade", "wavy kris-like blade"],
            "hilt": ["{main} wrapped hilt with {accent} pommel", "black hilt with {accent} gem", "bone hilt"],
            "sheath": ["{main} thigh sheath with {accent} straps", "{sub} sheath at the hip", "no sheath"],
        },
        "holds": [("held in reverse grip", "holding dagger, reverse grip"), ("held in the right hand", "holding dagger"), ("sheathed on the thigh", "sheathed, thigh sheath"), ("one in each hand", "holding dagger, dual wielding")],
    },
    "gun": {
        "jp": "銃", "syn": ["銃", "ガン", "拳銃", "ライフル", "gun", "pistol", "revolver", "rifle", "handgun"],
        "tags": ["gun", "holding gun", "weapon"],
        "types": [("revolver", "revolver"), ("flintlock pistol", "flintlock"), ("ornate handgun", "handgun"), ("rifle", "rifle"), ("oversized gun", "gun")],
        "slots": {
            "finish": ["silver finish with {accent} engraving", "black finish", "gold-plated finish with {pattern} engraving", "{main} body with {accent} details"],
            "grip": ["{main} grip", "ivory grip", "dark wood grip", "{accent} wrapped grip"],
        },
        "holds": [("held in the right hand pointing down", "holding gun"), ("held in both hands", "holding gun, two-handed"), ("holstered at the hip", "holster, holstered"), ("resting on the shoulder", "holding gun, over shoulder")],
    },
    "shield": {
        "jp": "盾", "syn": ["盾", "シールド", "shield"],
        "tags": ["shield", "holding shield"],
        "types": [("kite shield", "shield"), ("round shield", "shield"), ("tower shield", "shield"), ("heater shield", "shield"), ("buckler", "shield")],
        "slots": {
            "face": ["{main} face with {accent} {pattern} emblem", "silver face with gold rim", "black face with {accent} cross", "white face with {sub} stripe"],
            "rim": ["{accent} metal rim", "steel rim with rivets", "gold rim"],
        },
        "holds": [("held on the left arm", "holding shield"), ("planted in front", "holding shield"), ("slung on the back", "shield on back")],
    },
    "umbrella": {
        "jp": "傘", "syn": ["傘", "日傘", "パラソル", "umbrella", "parasol"],
        "tags": ["umbrella", "holding umbrella"],
        "types": [("lace parasol", "parasol"), ("paper umbrella (wagasa)", "oil-paper umbrella"), ("gothic umbrella", "umbrella"), ("frilled parasol", "parasol"), ("transparent umbrella", "transparent umbrella")],
        "slots": {
            "canopy": ["{main} canopy with {accent} trim", "white canopy with {accent} lace", "black canopy with {accent} frills", "{main} canopy with {pattern}"],
            "handle": ["{accent} curved handle", "dark wood handle", "crystal handle"],
        },
        "holds": [("held open over the shoulder", "holding umbrella, open umbrella"), ("held closed like a cane", "holding umbrella, closed umbrella"), ("held open in both hands", "holding umbrella, open umbrella")],
    },
    "fan": {
        "jp": "扇", "syn": ["扇", "扇子", "うちわ", "fan", "folding fan", "hand fan"],
        "tags": ["hand fan", "holding fan"],
        "types": [("folding fan", "folding fan"), ("paper fan (uchiwa)", "paper fan"), ("feather fan", "feather fan"), ("war fan (tessen)", "folding fan")],
        "slots": {
            "design": ["{main} fan with {accent} {pattern}", "white fan with gold flowers", "black fan with {accent} crest", "{sub} fan with {accent} edge"],
        },
        "holds": [("held open covering the mouth", "holding fan, covering mouth"), ("held closed in one hand", "holding fan"), ("held open beside the face", "holding fan")],
    },
    "instrument": {
        "jp": "楽器", "syn": ["楽器", "ヴァイオリン", "バイオリン", "ギター", "フルート", "instrument", "violin", "guitar", "flute", "lyre"],
        "tags": ["instrument", "holding instrument"],
        "types": [("violin", "violin"), ("acoustic guitar", "acoustic guitar"), ("electric guitar", "electric guitar"), ("flute", "flute"), ("lyre", "lyre")],
        "slots": {
            "finish": ["{main} body with {accent} details", "black lacquered body", "white body with gold inlay", "dark wood body with {pattern} inlay"],
        },
        "holds": [("held ready to play", "holding instrument"), ("slung on the back", "instrument on back"), ("held in one hand", "holding instrument")],
    },
    "lantern": {
        "jp": "ランタン", "syn": ["ランタン", "提灯", "灯り", "lantern"],
        "tags": ["lantern", "holding lantern"],
        "types": [("iron lantern", "lantern"), ("paper lantern", "paper lantern"), ("crystal lantern", "lantern"), ("skull-shaped lantern", "lantern")],
        "slots": {
            "light": ["{accent} flame inside", "blue flame inside", "soft golden light inside"],
            "frame": ["black iron frame", "{main} frame with {accent} details", "gold frame"],
        },
        "holds": [("held up in the right hand", "holding lantern"), ("hanging from a short pole", "holding lantern"), ("held at the side", "holding lantern")],
    },
    "whip": {
        "jp": "鞭", "syn": ["鞭", "ムチ", "whip", "riding crop"],
        "tags": ["whip", "holding whip"],
        "types": [("riding crop", "riding crop"), ("leather whip", "whip"), ("chain whip", "chain whip"), ("thorned whip", "whip")],
        "slots": {
            "handle": ["{main} leather handle with {accent} cap", "black handle with {accent} studs", "silver handle"],
            "lash": ["black leather lash", "{main} lash with {accent} tip", "braided lash"],
        },
        "holds": [("held in the right hand", "holding whip"), ("tapping against the palm", "holding whip"), ("coiled at the hip", "whip at hip")],
    },
}
# 手持ちが無いときに negative に入れる（装飾が手持ち化するのを防ぐ）
HANDHELD_NEGATIVE = ["holding object", "handheld object", "holding weapon"]
# 性格の署名に含まれる手持ち（これがある性格では HANDHELD_NEGATIVE を入れない）
SIGNATURE_HANDHELDS = ["riding crop"]

# 小物（持ち物）が体に固定されていると見なす語。含まれなければ engine が "holding " を前置して手に持たせる
PROP_ANCHORED_WORDS = ["worn", "on the", "around", "collar", "necklace", "pendant", "mask", "hair", "perched", "strapped",
                       "at the hip", "on a chain", "held", "holding", "floating", "hanging", "in the mouth", "under the arm",
                       "between the fingers", "on the back", "companion", "on the belt", "on the palm", "sitting on"]

# 「無くても成立する小物」の採用確率（単語境界で一致。先頭の主役の服には適用しない）
OPTIONAL_ITEM_KEYWORDS = {
    "sleep mask": 0.35, "stethoscope": 0.6, "headset": 0.6, "school bag": 0.5, "towel": 0.5, "watch": 0.5,
    "bell": 0.6, "chain": 0.6, "wrist cuffs": 0.7, "anklet": 0.6, "coin purse": 0.6, "satchel": 0.5,
    "crossbody bag": 0.5, "pom pom": 0.6, "pom-poms": 0.6, "umbrella": 0.5, "holster": 0.7, "surgical mask": 0.5,
    "bandaid": 0.6, "band-aid": 0.6, "bandage on the cheek": 0.6, "goggles": 0.7, "handcuffs": 0.6, "headband": 0.6,
    "armband": 0.6, "rosary": 0.7, "pearl necklace": 0.7, "hoop earrings": 0.6, "wristband": 0.6, "wristbands": 0.6,
    "fake tail": 0.7, "cotton tail": 0.7, "ribbon choker": 0.7, "choker": 0.7, "bow tie": 0.7, "bowtie": 0.7,
    "quiver": 0.7, "belt pouch": 0.7, "pouches": 0.7, "half-mask": 0.5, "mask around neck": 0.5, "scarf": 0.7,
}

# 体型の指定（ノードのドロップダウン）。指定が無ければ従来どおり種族・性格の推奨
# 胸: 0=flat chest … 5=gigantic breasts、6 以降は booru の上限を超えるので重みと文章で押す
BUST_LEVELS = [
    ("0 flat chest", ["flat chest"], "flat"),
    ("1 small", ["small breasts"], "small"),
    ("2 medium", ["medium breasts"], "medium-sized"),
    ("3 large", ["large breasts"], "large"),
    ("4 huge", ["huge breasts"], "huge"),
    ("5 gigantic", ["gigantic breasts"], "gigantic"),
    ("6 gigantic+", ["(gigantic breasts:1.3)", "oversized breasts"], "gigantic, far larger than her torso"),
    ("7 hyper", ["(gigantic breasts:1.6)", "hyper breasts"], "absurdly enormous, hyper-sized, dwarfing her body"),
    ("8 hyper+", ["(gigantic breasts:2.0)", "hyper breasts", "enormous"], "impossibly enormous, hyper-sized, larger than the rest of her body"),
]
HEIGHT_LEVELS = {
    "とても低い": (["petite", "very short stature"], "very short"),
    "低い": (["short stature"], "short"),
    "普通": ([], ""),
    "高い": (["tall"], "tall"),
    "とても高い": (["very tall", "tall female"], "very tall, towering"),
}
BUILD_LEVELS = {
    "華奢": (["skinny", "slender"], "very slim and delicate"),
    "細身": (["slender"], "slim"),
    "普通": ([], ""),
    "むっちり": (["thick thighs", "wide hips", "curvy"], "curvy and thick"),
    "ぽっちゃり": (["plump", "chubby", "thick thighs"], "plump and soft"),
    "筋肉質": (["muscular", "toned", "abs"], "muscular and toned"),
}
# 体型指定で置き換える既存タグ
BODY_BUST_TAGS = ["flat chest", "small breasts", "medium breasts", "large breasts", "huge breasts", "gigantic breasts"]
BODY_HEIGHT_TAGS = ["petite", "tall", "very tall", "short stature", "very short stature", "tall female", "small build"]
BODY_BUILD_TAGS = ["slender", "skinny", "curvy", "plump", "chubby", "muscular", "toned", "athletic", "medium build", "lean", "thick thighs", "wide hips", "abs"]

# 靴の判定キーワード（性格の footwear 置換に使う）
FOOTWEAR_KEYWORDS = ["shoes", "loafers", "boots", "sneakers", "heels", "sandals", "pumps", "mary janes", "slippers", "barefoot", "geta", "zori", "flats"]

# 品質系（lowres 等）はこのノードの責務外なので入れない。キャラ特徴の整合性に関わるものだけ
# strict モードで「出さない」不安定要素の判定キーワード（説明文にこれが含まれる記号・小物は省く）
UNSTABLE_KEYWORDS = [
    "face paint", "facial mark", "markings", "painted", "paint", "stitch", "cracked",
    "circuit lines", "tattoo", "body paint", "teardrop",
]

# strict モードで模様として出せる booru の print タグ（これ以外の模様は出さずシートのメモに残す）
BOORU_PRINT = {
    "heart motif": "heart print", "star pattern": "star print", "polka-dot pattern": "polka dot",
    "plaid pattern": "plaid", "checkered pattern": "checkered", "stripe pattern": "striped",
    "diagonal stripe pattern": "striped", "floral pattern": "floral print", "flower pattern": "floral print",
    "small floral motif": "floral print", "paw print motif": "paw print", "cow print": "cow print",
    "skull motif": "skull print", "bat-wing motif": "bat print", "cat silhouette motif": "cat print",
    "fish motif": "fish print", "butterfly motif": "butterfly print", "snowflake pattern": "snowflake print",
    "flame pattern": "flame print", "scale pattern": "scale print", "leaf motif": "leaf print",
    "rose motif": "rose print", "sakura pattern": "cherry blossom print", "moon motif": "moon print",
    "crescent moon motif": "crescent print", "cross pattern": "cross print", "gingham pattern": "gingham",
    "tiger-stripe pattern": "tiger stripes", "camouflage": "camouflage", "cloud motif": "cloud print",
    "lightning pattern": "lightning bolt print", "wave pattern": "wave print", "feather motif": "feather print",
    "ribbon motif": "ribbon print", "bone motif": "bone print", "hexagon pattern": "honeycomb print",
    "sakura pattern": "cherry blossom print", "rose print": "rose print", "feather print": "feather print", "chain print": "chain print",
    "skull print": "skull print", "heart print": "heart print", "rainbow motif": "rainbow print", "rainbow print": "rainbow print",
    "crown motif": "crown print", "cloud print": "cloud print", "raindrop pattern": "raindrop print", "key motif": "key print",
}

# テーマカラー -> 基本色（別色の同じ服を negative に入れる時に「同系色」を除外するため）
COLOR_BASE = {
    "black": "black", "white": "white", "crimson": "red", "scarlet": "red", "wine red": "red",
    "royal blue": "blue", "navy": "blue", "sky blue": "blue", "teal": "green", "emerald green": "green",
    "olive green": "green", "dark green": "green", "mint": "green", "gold": "yellow", "yellow": "yellow",
    "silver": "white", "cream": "white", "gray": "black", "pastel pink": "pink", "hot pink": "pink",
    "purple": "purple", "dark purple": "purple", "lavender": "purple", "orange": "orange", "brown": "brown",
}
ALT_COLORS = ["red", "blue", "white", "black", "pink", "green", "purple", "yellow"]

NEGATIVE_BASE = [
    "extra accessories", "mismatched colors",
]

# ---------------------------------------------------------------------------
# 自己検証（モジュール読み込み時に参照の整合性だけ確認する）
# ---------------------------------------------------------------------------

def _validate():
    from . import outfit_tags as _OT
    for rk in ROLES:
        assert rk in _OT.OUTFIT_TAGS, f"outfit_tags.py に {rk} のタグ列が無い"
        for g in ("female", "male"):
            for ex in ("modest", "standard", "high"):
                assert _OT.OUTFIT_TAGS[rk][g][ex], f"outfit_tags[{rk}][{g}][{ex}] が空"
                for it in _OT.OUTFIT_TAGS[rk][g][ex]:
                    assert isinstance(it, (str, list)) and it, f"outfit_tags[{rk}][{g}][{ex}] に不正な要素: {it!r}"
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
