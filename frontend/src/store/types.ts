import { Dispatch } from 'react';

export interface iUser {
    firstName: string,
    lastName: string,
    email: string,
}

export interface iToken {
    key: string,
}

export interface iGlobalStateInterface {
    token: iToken | null,
    user: iUser | null,
    error: string | null,
}

export type iActionType = {
    type: string;
    payload?: any;
};

export type iContextType = {
    globalState: iGlobalStateInterface;
    dispatch: Dispatch<iActionType>;
};
