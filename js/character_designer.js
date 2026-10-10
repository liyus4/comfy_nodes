import { app } from "../../scripts/app.js";

// Random Character Designer のフロントエンド拡張
// 実行結果（キャラクターシート）をノード上の「キャラシート」欄に書き戻します。
// lock を ON にすると、その欄の内容がそのまま出力されるので同じキャラを再現できます。
app.registerExtension({
    name: "ComfyNodes.CharacterDesigner",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "CharacterDesignerNode") return;

        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            const r = onExecuted ? onExecuted.apply(this, arguments) : undefined;

            const text = message?.text?.[0];
            if (typeof text !== "string") return r;

            const widget = this.widgets?.find((w) => w.name === "キャラシート");
            if (widget && widget.value !== text) {
                widget.value = text;
                // 旧フロントエンドでは textarea 要素を直接更新する必要がある
                if (widget.inputEl && widget.inputEl.value !== text) {
                    widget.inputEl.value = text;
                }
                this.setDirtyCanvas?.(true, true);
            }
            return r;
        };

        // シートが読みやすいように初期サイズを少し広げる
        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
            const size = this.computeSize?.() ?? this.size;
            this.setSize?.([Math.max(size[0], 460), Math.max(size[1], 440)]);
            return r;
        };
    },
});
