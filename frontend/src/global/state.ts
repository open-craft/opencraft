import { LoginStatusModel } from '../auth/models';
import { RegistrationStateModel } from '../registration/models';
import { UiStateModel } from '../ui/models';

export interface RootState {
  readonly registration: Readonly<RegistrationStateModel>;
  readonly loginState: Readonly<LoginStatusModel>;
  readonly ui: Readonly<UiStateModel>;
}
