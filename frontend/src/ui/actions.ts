import { Action } from 'redux';

export enum Types {
    NAVIGATE_NEXT_PAGE = 'NAVIGATE_NEXT_PAGE',
    NAVIGATE_PREV_PAGE = 'NAVIGATE_PREV_PAGE',
}


export interface NavigateNextPage extends Action {
    readonly type: Types.NAVIGATE_NEXT_PAGE,
}

export interface NavigatePreviousPage extends Action {
    readonly type: Types.NAVIGATE_PREV_PAGE,
}

export type ActionTypes =
    | NavigateNextPage
    | NavigatePreviousPage;
