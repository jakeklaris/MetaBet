import React from 'react';
import { useAddress, useDisconnect, useMetamask } from "@thirdweb-dev/react";
import { Button } from 'semantic-ui-react';


export const ConnectMetamaskButtonComponent = () => {
  const connectWithMetamask = useMetamask();

  const address = useAddress();
  return (
    <div>
      {address ? (
        <h4>Connected as {address}</h4>
      ) : (
        <Button onClick={connectWithMetamask}>Connect Metamask Wallet</Button>
      )}
    </div>
  );
};
