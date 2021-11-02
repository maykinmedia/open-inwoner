import axios from 'axios'
import { Token } from '../store/types';

export const logout = async () => {
    const res = await axios.post(`${import.meta.env.VITE_API_URL}/api/auth/logout/`, {}).catch(err => {
        console.error(err.response.data)
        throw err;
    });
    return res.data;
}

export const getToken = async () => {
    const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/auth/get_token/`, { withCredentials: true }).catch(err => {
        console.error(err.response.data)
        throw err;
    });
    return res.data;
}

export const login = async (email:string, password:string) => {
    const res = await axios.post(`${import.meta.env.VITE_API_URL}/api/auth/login/`, {email: email, password: password}).catch(err => {
        console.error(err.response.data)
        throw err;
    });
    return res.data;
}

export const getUser = async (token: Token) => {
    const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/auth/user/`, {headers: {Authorization: `Token ${token.key}`,}}).catch(err => {
        console.error(err.response.data)
        throw err;
    });
    return res.data;
}

export const registerUser = async (email?: string, password1?: string, password2?: string, firstName?: string, lastName?: string) => {
    const res = await axios.post(`${import.meta.env.VITE_API_URL}/api/auth/registration/`, {email: email, password1: password1, password2: password2, firstName: firstName, lastName: lastName}).catch(err => {
        console.error(err.response.data)
        throw err;
    });
    return res.data;
}

export const getProduct = async (slug: string) => {
    const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/products/${slug}/`).catch(err => {
        console.error(err.response.data)
        throw err;
    });
    return res.data;
}

export const getCategory = async (slug: string) => {
    const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/categories/${slug}/`).catch(err => {
        console.error(err.response.data)
        throw err;
    });
    return res.data;
}

export const getCategories = async () => {
    const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/categories/`).catch(err => {
        console.error(err.response.data)
        throw err;
    });
    return res.data;
}
