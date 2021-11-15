import {getCategories} from '../api/calls';
import {iCategory} from '../types/pdc';
import {iMenuItem} from '../types/menu-item';
import {ROUTES} from './routes';


/**
 * Returns a promise for an iRoute[] based on the categories.
 * @return {Promise}
 */
const getThemeNavigation = async () => {
  const categories = await getCategories().catch((error) => {
    // Catch the error so ti does not cause problems.
    console.error(error);
    return [];
  });
  return categories.map((category: iCategory): iMenuItem => ({
    label: category.name,
    route: ROUTES.CATEGORY,
    routeParams: {slug: category.slug}
  }));
}

/**
 * The main navigation.
 */
export const NAVIGATION: iMenuItem[] = [
  { route: ROUTES.HOME },
  { route: ROUTES.CATEGORIES, children: getThemeNavigation },
  { route: ROUTES.PROFILE },
  { route: ROUTES.INBOX },
  { route: ROUTES.SEARCH },
]
