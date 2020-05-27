import React from 'react';
import { Alert } from 'react-bootstrap';
import classNames from 'classnames';

interface Props {
  children: React.ReactNode;
  className?: string;
}

export const AlertMessage: React.FC<Props> = (props: Props) => (
  <Alert 
    className={classNames('text-center', props.className)}
    variant="warning"
  >
    {props.children}
  </Alert>
);
