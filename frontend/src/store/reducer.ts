import { ActionType, GlobalStateInterface } from './types';
import { initialState } from './index';

function assertNever(x: never): never {
  throw new Error(`Unexpected object: ${x}`);
}

const Reducer = (state: GlobalStateInterface, action: ActionType): any => {
  switch (action.type) {
    case 'SET_TOKEN':
      return { ...state, token: action.payload, error: null };

    case 'SET_USER':
      return { ...state, user: action.payload, error: null };

    case 'LOGOUT':
      return {
        ...state, user: null, token: null, error: null,
      };

    case 'FAIL_REQUEST':
      return { ...state, error: action.payload };

    case 'PURGE_STATE':
      return initialState;

    default:
      return assertNever(action);
  }
};

export default Reducer;
