import { InstancesModel } from '../console/models';
import { LoginStateModel } from '../auth/models';
import { RegistrationStateModel } from '../registration/models';
import { UiStateModel } from '../ui/models';

export interface RootState {
  readonly console: Readonly<InstancesModel>;
  readonly registration: Readonly<RegistrationStateModel>;
  readonly loginState: Readonly<LoginStateModel>;
  readonly ui: Readonly<UiStateModel>;
}
