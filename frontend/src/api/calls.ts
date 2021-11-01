import axios from 'axios'
import { Token } from '../store/types';

export const logout = async () => {
    const res = await axios.post(`${import.meta.env.VITE_API_URL}/api/auth/logout/`, {}).catch(err => {
        console.log(err.response.data)
        throw err;
    });
    return res.data;
}

export const getToken = async () => {
    const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/auth/get_token/`, { withCredentials: true }).catch(err => {
        console.log(err.response.data)
        throw err;
    });
    return res.data;
}

export const login = async (email:string, password:string) => {
    const res = await axios.post(`${import.meta.env.VITE_API_URL}/api/auth/login/`, {email: email, password: password}).catch(err => {
        console.log(err.response.data)
        throw err;
    });
    return res.data;
}

export const getUser = async (token: Token) => {
    console.warn(token)
    const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/auth/user/`, {headers: {Authorization: `Token ${token.key}`,}}).catch(err => {
        console.log(err.response.data)
        throw err;
    });
    return res.data;
}
