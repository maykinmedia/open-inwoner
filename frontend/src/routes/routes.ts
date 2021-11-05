import AppsOutlinedIcon from "@mui/icons-material/AppsOutlined";
import DescriptionOutlinedIcon from "@mui/icons-material/DescriptionOutlined";
import InboxOutlinedIcon from "@mui/icons-material/InboxOutlined";
import AccountCircleOutlinedIcon from "@mui/icons-material/AccountCircleOutlined";
import ArticleOutlinedIcon from '@mui/icons-material/ArticleOutlined';
import Home from "../pages/Home";
import {iRoute} from "../types/route";
import NotFoundPage from "../pages/NotFound";
import About from "../pages/About";
import ProductDetail from "../pages/Product/detail";
import ThemeDetail from "../pages/Themas/detail";
import Themas from "../pages/Themas";
import Register from "../pages/Register";
import Login from "../pages/Login";


/**
 * The routes for the application.
 */
export const ROUTES: { [index: string]: iRoute } = {
  HOME: {
    component: Home,
    label: 'Home',
    path: '/',
    exact: true,
    icon: AppsOutlinedIcon,
    loginRequired: false,
  },
  LOGIN: {
    component: Login,
    label: 'Inloggen',
    path: '/login',
    exact: true,
    icon: AccountCircleOutlinedIcon,
    loginRequired: false,
  },
  REGISTER: {
    component: Register,
    label: 'Registreren',
    path: '/register',
    exact: true,
    icon: AccountCircleOutlinedIcon,
    loginRequired: false,
  },
  PROFILE: {
    component: Home,  // TODO
    label: 'Mijn profiel',
    path: '/account',
    exact: true,
    icon: AccountCircleOutlinedIcon,
    loginRequired: true
  },
  INBOX: {
    component: Home,  // TODO
    label: 'Mijn berichten',
    path: '/account/inbox',
    exact: true,
    icon: InboxOutlinedIcon,
    loginRequired: true
  },
  CATEGORIES: {
    component: Themas,
    label: 'Thema\'s',
    path: '/themas',
    exact: true,
    icon: DescriptionOutlinedIcon,
    loginRequired: false,
  },
  CATEGORY: {
    component: ThemeDetail,
    label: (slug: string): string => {
      if(!slug) {
        return 'Thema';
      }
      const str = slug.replace(/[-_]/g, ' ');
      return str.split(' ').reduce((label: string, word: string): string => `${label} ${word[0].toUpperCase()}${word.slice(1)}`, '');
    },
    path: '/themas/:slug',
    exact: true,
    icon: ArticleOutlinedIcon,
    loginRequired: false,
  },
  PRODUCT: {
    component: ProductDetail,
    label: 'Product',
    path: '/product/:slug',
    exact: true,
    loginRequired: false,
  },
  ABOUT: {
    component: About,
    label: 'Over',
    path: '/about',
    exact: true,
    loginRequired: true,
  },
  NOTFOUND: {
    component: NotFoundPage,
    label: '404',
    path: '*',
    loginRequired: false,
  },
}


