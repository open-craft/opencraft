import * as React from 'react';
import './styles.scss';
import * as styles from "styles/_theme.scss";

interface Props {
    count: number;
    currentStep: number;
}

const Circle = (number) => (
    <svg className="active-step">
        <circle r={10} stroke={styles["primary-1"]}></circle>

    </svg>
)

export const StepBar: React.FC<Props> = ({count, currentStep}) => (
    <div className="step-bar">
        {[...(Array(count).keys())].map(num => (
            <>
                {num + 1 === currentStep
                    ? <span className="step-border"><span className={"active-step"}>{num + 1}</span></span>
                    : <span className="step"/>}
                <span className="line"/>
            </>
        ))}
    </div>
);