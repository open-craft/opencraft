import { ThunkAction, ThunkDispatch } from 'redux-thunk';
import { ActionTypes } from './actions';
import { RootState } from './state';


export type OcimThunkAction<actionReturnType> =
    ThunkAction<Promise<actionReturnType>, RootState, undefined, ActionTypes>;

export type OcimThunkDispatch<actionReturnType> =
    ThunkDispatch<RootState, undefined, ActionTypes>;
