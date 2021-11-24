import React, {useState, useEffect, ReactElement} from 'react';
import {getCategories} from '../../api/calls';
import {Card} from '../../Components/Card/Card';
import {CardContainer} from '../../Components/CardContainer/CardContainer';
import {Grid} from '../../Components/Container/Grid';
import {iCategory} from '../../types/pdc';
import './CategoryList.scss';


/**
 * Category list.
 * @return {ReactElement}
 */
export default function CategoryList(): ReactElement {
  const [categories, setCategories] = useState<iCategory[]>([]);

  useEffect(() => {
    const load = async () => {
      const resCategories = await getCategories();
      setCategories(resCategories);
    };
    load();
  }, []);

  /**
   * Returns the main content.
   * @return {ReactElement}
   */
  const getMainContent = (): ReactElement => {
    return (
      <div className="category-list">
        <h1 className="category-list__title">Themas</h1>
        <p className="category-list__description">Nulla vitae elit libero, a pharetra augue.</p>
        <CardContainer>
          {categories.map((category) => (
            <Card key={category.slug} src={category.image?.file} alt={category.image?.name} title={category.name} to={`/themas/${category.slug}`}/>
          ))}
        </CardContainer>
      </div>
    );
  };

  return (
    <Grid mainContent={getMainContent()}/>
  );
}
