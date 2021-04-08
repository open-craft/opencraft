import * as React from 'react';
import { HomePagePreview } from '../HomePagePreview';
import { InstanceSettingsModel } from '../../models';
import './styles.scss';
import { CourseOutlinePreview } from 'newConsole/components';

interface PreviewComponentProps {
  children?: React.ReactNode;
  instanceData: InstanceSettingsModel;
  currentPreview?: string;
}

export const PreviewComponent: React.FC<PreviewComponentProps> = (
  props: PreviewComponentProps
) => {
  const { instanceData, currentPreview } = props;

  switch(currentPreview) {
    case 'dasboard':
      return (
        <div className="theme-preview">
          <HomePagePreview instanceData={instanceData} />
        </div>
      );
    case 'courseoutline':
      return (
          <CourseOutlinePreview />
      );
    default:
      return (
          <HomePagePreview instanceData={instanceData} />
      );
  }


};
