import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "ComfyNodes.StringSelector",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "StringSelectorNode") {
            
            // ノード作成時に初期の入力ピン（string_0）を追加する
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                this.addInput("string_0", "STRING");
                return r;
            };

            // ピンが接続（または切断）されたときに呼ばれる関数をフック
            const onConnectionsChange = nodeType.prototype.onConnectionsChange;
            nodeType.prototype.onConnectionsChange = function (type, index, connected, link_info) {
                const r = onConnectionsChange ? onConnectionsChange.apply(this, arguments) : undefined;
                
                // 入力ピン以外の変更は無視
                if (type !== LiteGraph.INPUT) {
                    return r;
                }

                // 現在の `string_` ピンのインデックス（inputs配列内での位置）をすべて取得
                let stringIndices = [];
                for (let i = 0; i < this.inputs.length; i++) {
                    if (this.inputs[i].name.startsWith("string_")) {
                        stringIndices.push(i);
                    }
                }

                // 万が一 string_ ピンがない場合は何もしない
                if (stringIndices.length === 0) return r;

                let lastIdx = stringIndices[stringIndices.length - 1];

                // 一番最後のstring_ピンが何かに接続された場合、次の一番後ろとなる空ピンを追加
                if (this.inputs[lastIdx].link != null) {
                    // 追加する名前は、現在の数ベースで設定（0, 1, 2... と連番になる）
                    this.addInput("string_" + stringIndices.length, "STRING");
                } else {
                    // 逆に最後から見て複数のピンが未接続（空き）状態なら、1つだけ残して余分なピンを削除する
                    while (stringIndices.length > 1) {
                        let last = stringIndices[stringIndices.length - 1];
                        let secondLast = stringIndices[stringIndices.length - 2];

                        // 後ろから見て2つ連続で未接続なら、一番後ろのピンを削除
                        if (this.inputs[last].link == null && this.inputs[secondLast].link == null) {
                            this.removeInput(last);
                            stringIndices.pop();
                        } else {
                            break;
                        }
                    }
                }

                return r;
            };
        }
    }
});
