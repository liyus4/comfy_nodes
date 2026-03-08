import re

class StringSelectorNode:
    """
    指定したINDEXの複数のString入力から1つを選択して出力するノード。
    （入力端子は他ノードと「接続（リンク）」するたびにJSから動的に増減します）
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # どのインデックスの文字列を出力するか指定します
                "index": ("INT", {
                    "default": 0, 
                    "min": 0, 
                    "max": 999, 
                    "step": 1,
                    "display": "number"
                }),
            },
            "optional": {
                # 接続された動的入力ピン（string_0, string_1, ...）がここに渡されるため、
                # Python側では **kwargs で受け取ります。
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("selected_string",)
    FUNCTION = "select_string"
    CATEGORY = "Test/Example Nodes"

    def select_string(self, index, **kwargs):
        # kwargsとして渡されてくる全入力のうち、ピンの名前が 'string_' で始まるものを抽出します
        strings = {}
        for key, value in kwargs.items():
            if key.startswith("string_"):
                try:
                    # "string_0", "string_1" の数字部分を取り出して辞書に保持
                    idx = int(key.split("_")[1])
                    strings[idx] = value
                except ValueError:
                    continue
        
        # インデックス（数字部分）の昇順で並び替え
        sorted_strings = [strings[k] for k in sorted(strings.keys())]
        
        # 1つも入力が渡されてこなかった場合（空状態）のフォールバック
        if not sorted_strings:
            return ("",)
            
        # 安全のため、指定された index が範囲外なら最大インデックスにクリップする処理
        safe_index = max(0, min(index, len(sorted_strings) - 1))
        
        selected = sorted_strings[safe_index]
        if isinstance(selected, str):
            # 各行について、'#' から行末までを削除
            selected = re.sub(r'#.*', '', selected)
            
        return (selected,)


class BatchIndexGeneratorNode:
    """
    指定した複数のINDEX（例: "2-5", "1,3,4"）をパースし、
    対応する整数値（INT）を「リスト」として出力するノード。
    出力端子は1つですが、ComfyUIのバッチ機能により、繋いだ先の
    ノード（例: StringSelectorNodeのindex入力など）が複数回実行されます。
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # どのインデックスを出力するかを文字列で指定（例: "0-3" は 0,1,2,3）
                "indices": ("STRING", {"default": "0-3", "multiline": False}),
            }
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("batch_indices",)
    # これを True にすることで、ComfyUI内部で「この出力はリストである＝後続ノードをバッチ実行する」と認識されます
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "generate_indices"
    CATEGORY = "Test/Example Nodes"

    def generate_indices(self, indices):
        # indices の文字列をパース ("2-5, 8" -> [2, 3, 4, 5, 8])
        selected_indices = []
        for part in indices.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                try:
                    start, end = map(int, part.split("-"))
                    # 昇順か降順かに関わらず取得できるようにする
                    step = 1 if start <= end else -1
                    selected_indices.extend(range(start, end + step, step))
                except ValueError:
                    pass
            else:
                try:
                    selected_indices.append(int(part))
                except ValueError:
                    pass
        
        # 万が一リストが空になってしまった時のフォールバック
        if not selected_indices:
            selected_indices = [0]
            
        # リストをタプルに入れて返す
        return (selected_indices,)
