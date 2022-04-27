import React from 'react';
import ReactDOM from 'react-dom';
import Poll from './poll';
import { ChainId, ThirdwebProvider } from "@thirdweb-dev/react";

const App = () => {
  return (
    <ThirdwebProvider desiredChainId={ChainId.Mainnet}>
      <Poll />
    </ThirdwebProvider>
  );
};

// This method is only called once
ReactDOM.render(
  // Insert the Poll component into the DOM
  <App />,
  document.getElementById('reactEntry'),
);
