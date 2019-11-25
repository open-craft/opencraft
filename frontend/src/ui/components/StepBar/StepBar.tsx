import * as React from 'react';
import './styles.scss';

interface CircledNumberProps {
  number: number;
}

const CircledNumber: React.FC<CircledNumberProps> = ({
  number
}: CircledNumberProps) => (
  <svg
    className="circled-number"
    viewBox="0 0 20 20"
    xmlns="http://www.w3.org/2000/svg"
  >
    <circle r={10} cx={10} cy={10} className="outer-circle" />
    <circle r={7} cx={10} cy={10} strokeWidth={2} className="inner-circle" />
    <text
      x="50%"
      y="50%"
      textAnchor="middle"
      dy="0.4em"
      strokeWidth="1px"
      color="#1e4c59"
      className="circle-text"
      fontSize="10px"
    >
      {number}
    </text>
  </svg>
);

const circle = (
  <svg className="step" viewBox="0 0 10 10" xmlns="http://www.w3.org/2000/svg">
    <circle r={5} cx={5} cy={5} fill="#6d9cae" />
  </svg>
);

interface StepBarProps {
  count: number;
  currentStep: number;
}

export const StepBar: React.FC<StepBarProps> = ({
  count,
  currentStep
}: StepBarProps) => (
  <div className="step-bar">
    {[...Array(count).keys()].map(num => (
      <>
        {num + 1 === currentStep ? <CircledNumber number={num + 1} /> : circle}
        <span className="line" />
      </>
    ))}
  </div>
);
