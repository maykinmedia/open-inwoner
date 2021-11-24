import axios from 'axios';
import {iToken, iUser} from '../store/types';
import { iCategory, iProduct } from "../types/pdc";
import { iConfig } from '../types/configuration';

export const logout = async () => {
  const res = await axios.post(`${import.meta.env.VITE_API_URL}/api/auth/logout/`, {}).catch((err) => {
    throw err;
  });
  return res.data;
};

export const getToken = async (): Promise<iToken> => {
  const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/auth/get_token/`, { withCredentials: true }).catch((err) => {
    throw err;
  });
  return res.data as iToken;
};

export const login = async (email:string, password:string): Promise<iToken> => {
  const res = await axios.post(`${import.meta.env.VITE_API_URL}/api/auth/login/`, { email, password }).catch((err) => {
    console.error(err.reponse?.data);
    throw err;
  });
  return res.data as iToken;
};

export const getUser = async (token: iToken): Promise<iUser> => {
  const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/auth/user/`, { headers: { Authorization: `Token ${token.key}` } }).catch((err) => {
    throw err;
  });
  return res.data as iUser;
};

export const registerUser = async (email?: string, password1?: string, password2?: string, firstName?: string, lastName?: string): Promise<iToken> => {
  const res = await axios.post(`${import.meta.env.VITE_API_URL}/api/auth/registration/`, {
    email, password1, password2, firstName, lastName,
  }).catch((err) => {
    throw err;
  });
  return res.data as iToken;
};

export const getProduct = async (slug: string): Promise<iProduct> => {
  const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/products/${slug}/`).catch((err) => {
    throw err;
  });
  return res.data as iProduct;
};

export const getCategory = async (slug: string): Promise<iCategory> => {
  const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/categories/${slug}/`).catch((err) => {
    throw err;
  });
  return res.data as iCategory;
};

export const getCategories = async (): Promise<iCategory[]> => {
  const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/categories/`).catch((err) => {
    throw err;
  });
  return res.data as iCategory[];
};

export const search = async (query?: string): Promise<iProduct[]> => {
  const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/search/?search=${query}`).catch((err) => {
    throw err;
  });
  return res.data as iProduct[];
}

export const getConfiguration = async (): Promise<iConfig> => {
  const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/config/`).catch((err) => {
    throw err;
  });
  return res.data as iConfig;
}
