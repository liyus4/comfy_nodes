import os

from .example_node import MyCustomStringNode
from .string_selector_node import StringSelectorNode, BatchIndexGeneratorNode
from .character_designer import CharacterDesignerNode
from .browser_download_node import BrowserDownloadImageNode

# ノードのクラスと、内部で管理される識別子のマッピング
NODE_CLASS_MAPPINGS = {
    # 識別子: クラス名
    "MyCustomStringNode": MyCustomStringNode,
    "StringSelectorNode": StringSelectorNode,
    "BatchIndexGeneratorNode": BatchIndexGeneratorNode,
    "CharacterDesignerNode": CharacterDesignerNode,
    "BrowserDownloadImageNode": BrowserDownloadImageNode,
}

# UI上で表示されるノードの表示名（無くても動くが、設定した方が親切）
NODE_DISPLAY_NAME_MAPPINGS = {
    "MyCustomStringNode": "My Custom String Generator",
    "StringSelectorNode": "Dynamic String Selector",
    "BatchIndexGeneratorNode": "Batch Index Generator",
    "CharacterDesignerNode": "Random Character Designer",
    "BrowserDownloadImageNode": "Browser Download Image",
}

# Web用のカスタムJSを含める場合は WEB_DIRECTORY を指定します
WEB_DIRECTORY = "./js"

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']
