import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// Browser Download Image のフロントエンド拡張
// 実行結果の画像を、ブラウザの規定ダウンロードフォルダに保存させます。
// 保存先や「毎回確認する」等の挙動はブラウザの設定に従います（ノード側からは変えられません）。
app.registerExtension({
    name: "ComfyNodes.BrowserDownload",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "BrowserDownloadImageNode") return;

        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            const r = onExecuted ? onExecuted.apply(this, arguments) : undefined;

            const images = message?.images;
            if (!Array.isArray(images)) return r;

            // 同時に click() すると2枚目以降が落ちないブラウザがあるので、少し間隔を空ける
            images.forEach((img, i) => {
                const params = new URLSearchParams({
                    filename: img.filename,
                    subfolder: img.subfolder ?? "",
                    type: img.type ?? "temp",
                });
                const url = api.apiURL(`/view?${params.toString()}`);
                setTimeout(() => {
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = img.filename;
                    a.style.display = "none";
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                }, i * 300);
            });
            return r;
        };
    },
});
