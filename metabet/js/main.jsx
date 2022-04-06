import React from 'react';
import ReactDOM from 'react-dom';
import Poll from './poll';
// This method is only called once
ReactDOM.render(
  // Insert the post component into the DOM
  <Poll url="/api/vote/" />,
  document.getElementById('reactEntry'),
);