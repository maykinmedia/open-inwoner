import React, {useState, useEffect} from 'react';
import {useParams} from 'react-router-dom';
import {getCategory} from '../../api/calls';
import {Grid} from '../../Components/Container/Grid';
import {iCategory} from '../../types/pdc';
import {H1} from '../../Components/Typography/H1';
import {P} from '../../Components/Typography/P';
import './CategoryDetail.scss';
import {CardContainer} from '../../Components/CardContainer/CardContainer';
import {CategoryCard} from '../../Components/Card/CategoryCard';


/**
 * Category detail.
 * @constructor
 */
export default function CategoryDetail() {
  const [category, setCategory] = useState<iCategory | null>(null);
  const {categorySlug} = useParams<{ [index: string]: string }>();

  useEffect(() => {
    const load = async () => {
      const resCategory = await getCategory(categorySlug);
      setCategory(resCategory);
    };
    load();
  }, []);

  /**
   * Returns the main content.
   * @return {ReactElement}
   */
  const getMainContent = () => (
    <>
      <H1>{category?.name}</H1>
      <P>{category?.description}</P>

      <CardContainer>
        {category?.children?.map((c: iCategory) => <CategoryCard key={c.slug} parentCategory={category} category={c}/>)}
      </CardContainer>
    </>

  );

  return (
    <Grid mainContent={getMainContent()}/>
  );
}
