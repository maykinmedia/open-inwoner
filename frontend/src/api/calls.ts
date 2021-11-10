import axios from 'axios';
import { iToken } from '../store/types';
import {iCategory} from "../types/pdc";

export const logout = async () => {
  const res = await axios.post(`${import.meta.env.VITE_API_URL}/api/auth/logout/`, {}).catch((err) => {
    console.error(err.response.data);
    throw err;
  });
  return res.data;
};

export const getToken = async () => {
  const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/auth/get_token/`, { withCredentials: true }).catch((err) => {
    console.error(err.response.data);
    throw err;
  });
  return res.data;
};

export const login = async (email:string, password:string) => {
  const res = await axios.post(`${import.meta.env.VITE_API_URL}/api/auth/login/`, { email, password }).catch((err) => {
    console.error(err.response.data);
    throw err;
  });
  return res.data;
};

export const getUser = async (token: iToken) => {
  const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/auth/user/`, { headers: { Authorization: `Token ${token.key}` } }).catch((err) => {
    console.error(err.response.data);
    throw err;
  });
  return res.data;
};

export const registerUser = async (email?: string, password1?: string, password2?: string, firstName?: string, lastName?: string) => {
  const res = await axios.post(`${import.meta.env.VITE_API_URL}/api/auth/registration/`, {
    email, password1, password2, firstName, lastName,
  }).catch((err) => {
    console.error(err.response.data);
    throw err;
  });
  return res.data;
};

export const getProduct = async (slug: string) => {
  const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/products/${slug}/`).catch((err) => {
    console.error(err.response.data);
    throw err;
  });
  return res.data;
};

export const getCategory = async (slug: string) => {
  const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/categories/${slug}/`).catch((err) => {
    console.error(err.response.data);
    throw err;
  });
  return res.data;
};

export const getCategories = async (): Promise<iCategory[]> => {
  const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/categories/`).catch((err) => {
    console.error(err.response.data);
    throw err;
  });
  return res.data as iCategory[];
};
