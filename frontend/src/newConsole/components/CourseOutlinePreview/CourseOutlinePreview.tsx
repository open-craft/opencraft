import React from 'react';
import { useSelector } from 'react-redux';
import { RootState } from 'global/state';
import { CourseOutlinePreview as PreviewComponent } from 'console/components';

export const CourseOutlinePreview = () => {
  const instanceData = useSelector(
    (state: RootState) => state.console.activeInstance?.data
  );
  if (instanceData) {
    return <PreviewComponent instanceData={instanceData} />;
  }
  return null;
};
