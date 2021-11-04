export const getIsLoggedIn = (globalState: any) => {
  if (globalState.user) {
    return true;
  }
  return false;
};

export const isNotLoggedIn = (globalState: any) => {
  if (globalState.user) {
    return false;
  }
  return true;
};
