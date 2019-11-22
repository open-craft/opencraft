import { LoginStatusModel } from '../auth/models';
import { RegistrationModel } from '../registration/models';
import { UiStateModel } from '../ui/models';

export interface RootState {
    readonly registration: Readonly<RegistrationModel>,
    readonly loginState: Readonly<LoginStatusModel>,
    readonly ui: Readonly<UiStateModel>,
}
