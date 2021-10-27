import React, { createContext, ReactElement, ReactNode, useEffect, useReducer, useRef } from 'react';
import Reducer from './reducer';
import { ContextType, GlobalStateInterface } from './types';

/**
 * React Context-based Global Store with a reducer
 * and persistent saves to sessionStorage/localStorage
 **/
export function GlobalStore({ children }: { children: ReactNode }): ReactElement {
    const [globalState, dispatch] = useReducer(Reducer, initializeState());
    const initialRenderGlobalState = useRef(true);

    useEffect(() => {
        if (initialRenderGlobalState.current) {
            initialRenderGlobalState.current = false;
            return;
        }
        localStorage.setItem('globalState', JSON.stringify(globalState));
    }, [globalState]);

    return <globalContext.Provider value={{ globalState, dispatch }}>{children}</globalContext.Provider>;
}

export const globalContext = createContext({} as ContextType);

export const initialState: GlobalStateInterface = {
    token: null,
    user: null,
    error: null,
};

function initializeState() {
    /*
    the order in which the the data is compared is very important;
    first try to populate the state from Storage if not return initialState
    */

    if (typeof window === 'object' || typeof window !== 'undefined') {
        if (typeof (Storage) !== 'undefined') {
        } else {
            throw new Error('You need to enable Storage to run this app.');
        }

        const fromLocalStorage = JSON.parse(localStorage.getItem('globalState') as string);
        return fromLocalStorage || initialState;
    }
    return initialState;
}
