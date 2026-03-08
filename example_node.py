class MyCustomStringNode:
    """
    これは簡単なカスタムノードのサンプルクラスです。
    """
    
    # ノードが初期化される時に呼ばれる
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        """
        ノードの入力（左側に繋ぐピンやUI上のウィジェット）を定義します。
        """
        return {
            "required": {
                # 文字列の入力フィールド（デフォルト値 "Hello World"、複数行入力可能）
                "my_text": ("STRING", {"multiline": True, "default": "Hello World"}),
                # 整数値の入力フィールド
                "repeat_count": ("INT", {"default": 1, "min": 1, "max": 10, "step": 1}),
            },
            "optional": {
                # 任意での接続が必要ならここに定義します
                # (例: "image": ("IMAGE",))
            }
        }

    # 出力される型（右側にでるピン）
    RETURN_TYPES = ("STRING",)
    
    # 出力ピンの表示名（オプション）。指定しない場合はRETURN_TYPESの名前になります
    RETURN_NAMES = ("text_output",)

    # UI上で処理を実行する際に呼ばれる関数名
    FUNCTION = "process_text"

    # 右クリックメニュー内での表示カテゴリ
    CATEGORY = "Test/Example Nodes"

    # 実行する処理の内容。引数の名前は INPUT_TYPES に定義したキー名と一致させます。
    def process_text(self, my_text, repeat_count):
        """
        この関数は `FUNCTION = "process_text"` と対応して呼び出されます。
        必ず RETURN_TYPES で定義した通りのタプルで返す必要があります。
        """
        result = "\n".join([my_text] * repeat_count)
        return (result,)
