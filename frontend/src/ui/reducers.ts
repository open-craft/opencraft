import { RegistrationSteps } from '../global/constants';
import * as UIActions from './actions';
import { UiStateModel } from './models';

export const initialState: Readonly<UiStateModel> = {
  currentRegistrationStep: RegistrationSteps.INSTANCE,
};

export function uiStateReducer(state = initialState,
  action: UIActions.ActionTypes): UiStateModel {
  switch (action.type) {
    case UIActions.Types.NAVIGATE_NEXT_PAGE: {
      if (state.currentRegistrationStep == null) return initialState;
      const nextStep = Math.min(
        state.currentRegistrationStep + 1,
        RegistrationSteps.LAST_STEP,
      );
      return { ...state, currentRegistrationStep: nextStep };
    }
    case UIActions.Types.NAVIGATE_PREV_PAGE: {
      if (state.currentRegistrationStep == null) return initialState;
      const prevStep = Math.min(
        state.currentRegistrationStep + 1,
        RegistrationSteps.LAST_STEP,
      );
      return { ...state, currentRegistrationStep: prevStep };
    }
    default:
      return state;
  }
}
