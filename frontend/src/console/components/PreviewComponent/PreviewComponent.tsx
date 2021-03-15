import * as React from 'react';
import './styles.scss';
import { InstanceSettingsModel } from '../../models';
import { PreviewDashboard } from '../PreviewDashboard';
import { PreviewCourseware } from '../PreviewCourseware';

interface PreviewComponentProps {
  children?: React.ReactNode;
  instanceData: InstanceSettingsModel;
  currentPreview: string;
}

export const PreviewComponent: React.FC<PreviewComponentProps> = (
  props: PreviewComponentProps
) => {
  const { instanceData } = props;

  if (props.currentPreview === 'dashboard') {
    return (
      <PreviewDashboard
        instanceData={instanceData}
      />
    );
  } else if (props.currentPreview === 'courseware') {
    return (
      <PreviewCourseware
        instanceData={instanceData}
      />
    );
  }
  return <div className="theme-preview" />;
};
