import * as React from 'react';
import messages from './displayMessages';
import './styles.scss';
import { ConsolePage } from 'console/components';
import { TextInputField } from 'ui/components';


export const InstanceSettings: React.FC = () => {
  let loading = true;

  if (loading) {
    return (
      <ConsolePage>
        
      </ConsolePage>
    );
  }

  return (
    <ConsolePage>
      <h2>Instance settings</h2>

      <TextInputField
        fieldName="instanceName"
        value={""}
        onChange={() => {}}
        messages={messages}
        error={""}
      />

      <TextInputField
        fieldName="publicContactEmail"
        value={""}
        onChange={() => {}}
        messages={messages}
        type="email"
        error={""}
      />
    </ConsolePage>
  );
};
