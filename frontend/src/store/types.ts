import { Dispatch } from 'react';

export interface User {
    firstName: string,
    lastName: string,
    email: string,
}

export interface Token {
    key: string,
}

export interface GlobalStateInterface {
    token: Token | null,
    user: User | null,
    error: string | null,
}

export type ActionType = {
    type: string;
    payload?: any;
};

export type ContextType = {
    globalState: GlobalStateInterface;
    dispatch: Dispatch<ActionType>;
};
