import AccountCircleOutlinedIcon from '@mui/icons-material/AccountCircleOutlined';
import AppsOutlinedIcon from '@mui/icons-material/AppsOutlined';
import ArticleOutlinedIcon from '@mui/icons-material/ArticleOutlined';
import DescriptionOutlinedIcon from '@mui/icons-material/DescriptionOutlined';
import InboxOutlinedIcon from '@mui/icons-material/InboxOutlined';
import Home from '../pages/Home';
import Login from '../pages/Login';
import CategoryDetail from '../pages/Category/CategoryDetail';
import CategoryList from '../pages/Category/CategoryList';
import NotFoundPage from '../pages/NotFound';
import ProductDetail from '../pages/Product/ProductDetail';
import Profile from '../pages/Profile';
import Register from '../pages/Register';
import Search from '../pages/Search';
import {iRoute} from '../types/route';


/**
 * Returns a function that returns a label based on a given slug or defaultLabel.
 * @param {string} defaultLabel
 */
export const labelFromSlug = (defaultLabel: string): Function => (
  (slug: string | string[]): string => {
    const _slugArray = ((Array.isArray(slug)) ? slug : [slug]) || [defaultLabel];
    const _slug = _slugArray[_slugArray.length - 1];
    const str = _slug.replace(/[-_]/g, ' ');
    return (str.length) ? str[0].toUpperCase() + str.slice(1) : '';
  }
)


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
    component: CategoryList,
    label: 'Thema\'s',
    path: '/themas',
    exact: true,
    icon: DescriptionOutlinedIcon,
    loginRequired: false,
  },
  CATEGORY: {
    component: CategoryDetail,
    label: labelFromSlug('Thema'),
    path: '/themas/:categorySlug',
    exact: true,
    icon: ArticleOutlinedIcon,
    loginRequired: false,
  },
  SUBCATEGORY: {
    component: CategoryDetail,
    label: labelFromSlug('Subthema'),
    path: '/themas/:categorySlug/:subCategorySlug',
    exact: true,
    icon: ArticleOutlinedIcon,
    loginRequired: false,
  },
  PRODUCT: {
    component: ProductDetail,
    label: labelFromSlug('Product'),
    path: '/product/:productSlug',
    exact: true,
    loginRequired: false,
  },
  TPRODUCT: {
    component: ProductDetail,
    label: labelFromSlug('Product'),
    path: '/themas/:categorySlug/product/:productSlug',
    exact: true,
    loginRequired: false,
  },
  TTPRODUCT: {
    component: ProductDetail,
    label: labelFromSlug('Product'),
    path: '/themas/:categorySlug/:subCategorySlug/product/:productSlug',
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


