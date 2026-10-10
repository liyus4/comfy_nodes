import json
import os

import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo

import folder_paths


class BrowserDownloadImageNode:
    """
    受け取った画像をブラウザにダウンロードさせるノード。

    サーバー側(Python)はブラウザのダウンロードフォルダを知らないので直接は書けません。
    代わりに PreviewImage と同じく temp フォルダに PNG を保存して "ui" で返し、
    js/browser_download.js がその画像を <a download> でダウンロードさせます。
    保存先はブラウザ側の設定（規定のダウンロードフォルダ）に従います。
    """

    def __init__(self):
        self.output_dir = folder_paths.get_temp_directory()
        self.type = "temp"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                # ダウンロードされるファイル名の先頭。連番と .png が後ろに付きます
                "filename_prefix": ("STRING", {"default": "ComfyUI"}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ()
    FUNCTION = "download"
    CATEGORY = "Test/Example Nodes"
    OUTPUT_NODE = True

    def download(self, images, filename_prefix="ComfyUI", prompt=None, extra_pnginfo=None):
        full_output_folder, filename, counter, subfolder, _ = folder_paths.get_save_image_path(
            filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0]
        )

        results = []
        for image in images:
            arr = 255.0 * image.cpu().numpy()
            img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

            # SaveImage と同じく、ワークフローを PNG メタデータに埋め込む
            metadata = PngInfo()
            if prompt is not None:
                metadata.add_text("prompt", json.dumps(prompt))
            if extra_pnginfo is not None:
                for key, value in extra_pnginfo.items():
                    metadata.add_text(key, json.dumps(value))

            file = f"{filename}_{counter:05}_.png"
            img.save(os.path.join(full_output_folder, file), pnginfo=metadata, compress_level=4)
            results.append({"filename": file, "subfolder": subfolder, "type": self.type})
            counter += 1

        # "images" は標準のプレビュー表示にも使われ、js/browser_download.js がダウンロードを起動します
        return {"ui": {"images": results}}
