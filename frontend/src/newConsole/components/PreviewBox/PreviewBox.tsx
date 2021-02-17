import * as React from 'react';
import { Card } from 'react-bootstrap';
import "./style.scss"

interface PreviewBoxProps {
    children: React.ReactNode
}


export const PreviewBox: React.FC<PreviewBoxProps> = (props: PreviewBoxProps) => {
return (
    <Card className="preview-box">
        {props.children}
    </Card>
)
}
