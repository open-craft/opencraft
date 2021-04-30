import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { OpenEdXInstanceConfigUpdateDnsConfigurationStateEnum as DnsStateEnum } from 'ocim-client';
import { DomainListItem } from './DomainItem';

it('renders correctly for subdomains', () => {
  const props = {
    domainName: 'test.opencraft.hosting',
    isExternal: false
  }
  const tree = setupComponentForTesting(
    <DomainListItem {...props}/>,
    ).toJSON();
    expect(tree).toMatchSnapshot();
});

it('renders correctly for unverified external domains', () => {
  const props = {
    domainName: 'example.com',
    isExternal: true,
    dnsState: DnsStateEnum.Failed,
  }
  const tree = setupComponentForTesting(<DomainListItem {...props}/>).toJSON();
  expect(tree).toMatchSnapshot();
})

it('renders correctly for verified external domains', () => {
  const props = {
    domainName: 'example.com',
    isExternal: true,
    dnsState: DnsStateEnum.Verified,
  }
  const tree = setupComponentForTesting(<DomainListItem {...props}/>).toJSON();
  expect(tree).toMatchSnapshot();
})
