import { InstancesModel } from 'console/models';
import { RootState } from 'global/state';
import * as React from 'react';
import { connect } from 'react-redux';
import { updateThemeFieldValue } from 'console/actions';
import { WrappedMessage } from 'utils/intl';
import { ColorInputField } from 'ui/components';
import { ConsolePage } from '../newConsolePage';
import messages from './displayMessages';
import './styles.scss';

interface State {}

interface ActionProps {
  updateThemeFieldValue: Function;
}

interface StateProps extends InstancesModel {}

interface Props extends StateProps, ActionProps {
  history: {
    goBack: Function;
  };
}

export class ThemeNavigationComponent extends React.PureComponent<
  Props,
  State
> {
  private onChangeColor = (fieldName: string, newColor: string) => {
    const instance = this.props.activeInstance;

    if (instance.data) {
      this.props.updateThemeFieldValue(instance.data.id, fieldName, newColor);
    }
  };

  public render() {
    const instance = this.props.activeInstance;
    let themeData;

    if (instance.data && instance.data.draftThemeConfig) {
      themeData = instance.data.draftThemeConfig;
    }

    return (
      <ConsolePage
        contentLoading={this.props.loading}
        goBack={this.props.history.goBack}
        showSideBarEditComponent
      >
        <div>
          <h2 className="edit-heading">
            <WrappedMessage messages={messages} id="themeNavigation" />
          </h2>

          {themeData && themeData.version === 1 && (
            <div className="theme-navigation-container">
              <div>
                <ColorInputField
                  fieldName="headerBg"
                  initialValue={themeData.headerBg || ''}
                  onChange={this.onChangeColor}
                  messages={messages}
                  loading={instance.loading.includes('draftThemeConfig')}
                />
                <ColorInputField
                  fieldName="mainNavLinkColor"
                  initialValue={themeData.mainNavLinkColor || ''}
                  onChange={this.onChangeColor}
                  messages={messages}
                  loading={instance.loading.includes('draftThemeConfig')}
                />
                <ColorInputField
                  fieldName="mainNavItemBorderBottomColor"
                  initialValue={themeData.mainNavItemBorderBottomColor || ''}
                  onChange={this.onChangeColor}
                  messages={messages}
                  loading={instance.loading.includes('draftThemeConfig')}
                />
                <ColorInputField
                  fieldName="mainNavItemHoverBorderBottomColor"
                  initialValue={
                    themeData.mainNavItemHoverBorderBottomColor || ''
                  }
                  onChange={this.onChangeColor}
                  messages={messages}
                  loading={instance.loading.includes('draftThemeConfig')}
                />
                <ColorInputField
                  fieldName="userDropdownColor"
                  initialValue={themeData.userDropdownColor || ''}
                  onChange={this.onChangeColor}
                  messages={messages}
                  loading={instance.loading.includes('draftThemeConfig')}
                />
              </div>
            </div>
          )}
        </div>
      </ConsolePage>
    );
  }
}

export const ThemeNavigationPage = connect<
  StateProps,
  ActionProps,
  {},
  Props,
  RootState
>((state: RootState) => state.console, {
  updateThemeFieldValue
})(ThemeNavigationComponent);
