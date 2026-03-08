import { app } from "../../scripts/app.js";

// カスタムノードのフロントエンド拡張スクリプト
app.registerExtension({
  name: "MyCustomNode.ExampleExtension",
  async beforeRegisterNodeDef(nodeType, nodeData, app) {
    if (nodeData.name === "MyCustomStringNode") {
      // ノードが登録される前に実行される処理
      // この中でノードの見た目や動作などをカスタマイズできます。
      // console.log("Registered MyCustomStringNode UI.");
    }
  },
});
