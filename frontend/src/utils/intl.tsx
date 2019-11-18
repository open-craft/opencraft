import React from "react";
import { FormattedMessage, MessageDescriptor } from "react-intl";

type MessageMap = { [k: string]: Omit<MessageDescriptor, 'id'> };

interface Props<T, K extends keyof T> {
    id: K;
    messages: T;
    values?: any;
}


export const WrappedMessage = (props: Props<MessageMap, string>) => {
    const {messages, id, ...values} = props;
    return (
        <FormattedMessage  {...messages[id]} id={id} {...values}/>
    );
};
