import { RegistrationSteps } from '../global/constants';
import * as UIActions from './actions';
import { UiStateModel } from './models';

export const initialState: Readonly<UiStateModel> = {
  currentRegistrationStep: RegistrationSteps.INSTANCE
};

export function uiStateReducer(
  state = initialState,
  action: UIActions.ActionTypes
): UiStateModel {
  switch (action.type) {
    default:
      return state;
  }
}
