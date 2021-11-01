export const getIsLoggedIn = (globalState: any) => {
    if (globalState.user) {
        return true;
    }
    return false;
}
