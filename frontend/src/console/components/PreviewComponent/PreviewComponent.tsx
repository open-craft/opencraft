import * as React from 'react';
import { HomePagePreview } from '../HomePagePreview';
import { InstanceSettingsModel } from '../../models';
import './styles.scss';

interface PreviewComponentProps {
  children?: React.ReactNode;
  instanceData: InstanceSettingsModel;
  currentPreview: string;
}

export const PreviewComponent: React.FC<PreviewComponentProps> = (
  props: PreviewComponentProps
) => {
  const { instanceData } = props;

  return (
    <div className="theme-preview">
      <HomePagePreview instanceData={instanceData} />
    </div>
  );
};
