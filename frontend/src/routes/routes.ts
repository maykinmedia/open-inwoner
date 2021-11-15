import AccountCircleOutlinedIcon from "@mui/icons-material/AccountCircleOutlined";
import AppsOutlinedIcon from "@mui/icons-material/AppsOutlined";
import ArticleOutlinedIcon from '@mui/icons-material/ArticleOutlined';
import DescriptionOutlinedIcon from "@mui/icons-material/DescriptionOutlined";
import InboxOutlinedIcon from "@mui/icons-material/InboxOutlined";
import Home from "../pages/Home";
import {iRoute} from "../types/route";
import NotFoundPage from "../pages/NotFound";
import Search from "../pages/Search";
import ProductDetail from "../pages/Product/detail";
import ThemeDetail from "../pages/Themas/detail";
import Themas from "../pages/Themas";
import Register from "../pages/Register";
import Login from "../pages/Login";
import Profile from '../pages/Profile';


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
  LOGOUT: {
    component: Home,  //TODO,
    label: 'Uitloggen',
    path: '/logout',
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
    component: Profile,
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
  SEARCH: {
    component: Search,
    label: 'Zoeken',
    path: '/search',
    exact: true,
    loginRequired: false,
  },
  NOTFOUND: {
    component: NotFoundPage,
    label: '404',
    path: '*',
    loginRequired: false,
  },

  PRIVACY_STATEMENT: {
    component: Home,  //TODO
    label: 'Privacyverklaring',
    path: '/privacy',
  },

  COOKIE_STATEMENT: {
    component: Home,  //TODO
    label: 'Cookieverklaring',
    path: '/cookies',
  },

  ACCESSIBILITY_STATEMENT: {
    component: Home,  //TODO
    label: 'Toegankelijkheidverklaring',
    path: '/accessibility',
  },

  PERSONAL_DATA: {
    component: Home,  //TODO
    label: 'Bescherming persoonsgegevens',
    path: '/personal-data',
  },

  TERMS_AND_CONDITIONS: {
    component: Home,  //TODO
    label: 'Gebruiksvoorwaarden',
    path: '/terms-and-conditions',
  },

  PROCLAIMER: {
    component: Home,  //TODO
    label: 'Proclaimer',
    path: '/proclaimer',
  },

  DISCLAIMER: {
    component: Home,  //TODO
    label: 'Disclaimer',
    path: '/disclaimer',
  },
}


