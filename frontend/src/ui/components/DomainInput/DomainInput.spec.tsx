import React from 'react';
import {
    mountComponentForTesting,
    setupComponentForTesting
} from "utils/testing";
import { DomainInput } from './DomainInput';


describe("Domain Input component", function() {
    it('renders without crashing', () => {
        const tree = setupComponentForTesting(<DomainInput />).toJSON();
        expect(tree).toMatchSnapshot();
    });

    it('renders with props without crashing', () => {
        const tree = mountComponentForTesting(
            <DomainInput
                domainName={'testDomain'}
                internalDomain={true}
                loading={false}
                error=''
                handleDomainChange={() => {}}
                handleSubmitDomain={() => {}}
            />
        );
        expect(tree).toMatchSnapshot();
    });

    it('calls handleDomainChange when writing on input', () => {
        const mock = jest.fn();
        const tree = mountComponentForTesting(
            <DomainInput
                internalDomain={true}
                loading={false}
                error=''
                handleDomainChange={mock}
            />
        );
        const mountedComponent = tree.find('DomainInput')
        const formControl = mountedComponent.find('FormControl')
        formControl.simulate('change', {target: {value: 'test-domain'}});
        expect(mock).toBeCalled()
    });

    it('calls handleSubmitDomain when clicking the button', () => {
        const mock = jest.fn();
        const tree = mountComponentForTesting(
            <DomainInput
                internalDomain={true}
                handleSubmitDomain={mock}
            />
        );
        const mountedComponent = tree.find('DomainInput')
        const button = mountedComponent.find('Button')
        button.simulate('click');
        expect(mock).toBeCalled()
    });

    it('renders InputGroup with internal domain if defined', () => {
        const tree = mountComponentForTesting(
            <DomainInput
                domainName={'.test.hosting'}
                internalDomain={true}
            />
        );
        const mountedComponent = tree.find('DomainInput')
        const inputGroup = mountedComponent.find('input').at(0)
        expect(inputGroup.prop('value')).toBe('.test.hosting')
    });

    it('only renders subdomain InputGroup if '+
        'there are no errors and internal domain is undefined', () => {
        const tree = mountComponentForTesting(
            <DomainInput/>
        );
        const mountedComponent = tree.find('DomainInput')
        // Only the subdomain inputGroup should always
        // be present.
        const numInputGroups = mountedComponent.find('input').length
        expect(numInputGroups).toBe(1)
    });

    it('renders Spinner and disables button if loading', () => {
        const tree = mountComponentForTesting(
            <DomainInput
                loading={true}
            />
        );
        const button = tree.find('Button')
        expect(tree).not.toContain('Spinner');
        expect(button.prop('disabled')).toBe(true);
    });

    it('renders error Feedback if defined', () => {
        const tree = mountComponentForTesting(
            <DomainInput
                error='some-error'
            />
        );
        const mountedComponent = tree.find('Feedback')
        expect(mountedComponent.text()).toBe('some-error');
    });

});
