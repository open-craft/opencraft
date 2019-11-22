import { RootState } from '../global/state';
import { RegistrationModel } from './models';

export const getCurrentRegistrationStep = (state: RootState) => state.ui.currentRegistrationStep;

export const getRegistrationData = <K extends keyof RegistrationModel>(
  state: RootState,
  field: K,
): RegistrationModel[K] => state.registration[field];
