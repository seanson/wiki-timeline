import React from "react";
import "./App.css";
import data from "./years";
import Timeline from "react-visjs-timeline";

function App() {
  // http://visjs.org/docs/timeline/#Configuration_Options

  const args = {
    options: {
      width: "100vw",
      height: "100vh",
      zoomMin: 10000000000,
      start: "1300-01-01",
      min: "1300-01-01",
      max: "1400-12-31",
      showCurrentTime: false,
      stack: true
    },
    items: data.data["1300"]
  };

  // let items = [
  //   {
  //     id: 1,
  //     start: data.data[0].start,
  //     end: data.data[0].end,
  //     content: `<div style="{width: 50px;height: 50px;}">${
  //       data.data[0].content
  //     }</div>`
  //   }
  // ];
  // console.log(items);

  return (
    <div className="App">
      <Timeline {...args} />
    </div>
  );
}

export default App;
