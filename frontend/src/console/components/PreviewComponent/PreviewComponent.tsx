import * as React from 'react';
import { HomePagePreview } from 'console/components/HomePagePreview';
import { InstanceSettingsModel } from 'console/models';
import { CourseOutlinePreview } from 'newConsole/components';
import './styles.scss';

interface PreviewComponentProps {
  children?: React.ReactNode;
  instanceData: InstanceSettingsModel;
  currentPreview?: string;
}

export const PreviewComponent: React.FC<PreviewComponentProps> = (
  props: PreviewComponentProps
) => {
  const { instanceData, currentPreview } = props;

  switch (currentPreview) {
    case 'dashboard':
      return <HomePagePreview instanceData={instanceData} />;
    case 'courseoutline':
      return <CourseOutlinePreview />;
    default:
      return <HomePagePreview instanceData={instanceData} />;
  }
};
