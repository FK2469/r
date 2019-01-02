import React from "react";
import ReactDOM from "react-dom";
import DragAndDrop from "./upload";

import "../stylesheets/main";

main();

function main() {
  ReactDOM.render(<DragAndDrop />, document.getElementById("main"));
}
