import React, {ReactElement} from 'react';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import {iCategory, iSmallProduct} from '../../types/pdc';
import {Card} from './Card';
import './Card.scss';
import {Link} from '../Typography/Link';
import {generatePath} from 'react-router-dom';
import {ROUTES} from '../../routes/routes';


interface iCategoryCardProps {
  category: iCategory
  parentCategory: iCategory
}


export function CategoryCard(props: iCategoryCardProps) {
  const {category, parentCategory, ..._props} = props

  const renderProducts = (): ReactElement[] => {
    return category.product?.map((product: iSmallProduct) => {
      const to = generatePath(ROUTES.PRODUCT.path, {categorySlug: parentCategory.slug, subCategorySlug: category.slug, productSlug: product.slug});

      return (
        <Link key={product.slug} to={to} icon={ArrowForwardIcon} iconPosition='after' secondary={true}>
          {product.name}
        </Link>
      );
    }) || [<></>]
  }

  return (
    <Card title={category.name} {..._props}>
      {renderProducts()}
    </Card>
  );
}
