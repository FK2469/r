import React from "react";
import DragAndDrop from "./upload";
import ReactDOM from "react-dom";

import "../stylesheets/main";

main();

function main() {
  ReactDOM.render(<DragAndDrop />, document.getElementById("main"));
}
