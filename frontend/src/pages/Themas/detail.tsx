import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getCategory } from '../../api/calls';
import { Grid } from '../../Components/Container/Grid';
import { CardList } from '../../Components/Card/CardList';
import { iCategory } from '../../types/pdc';
import './theme.scss';

export default function ThemaDetail() {
  const [category, setCategory] = useState<iCategory | undefined>(undefined);
  const { slug } = useParams();

  useEffect(() => {
    const load = async () => {
      const resCategory = await getCategory(slug);
      setCategory(resCategory);
    };
    load();
  }, []);

  const getRight = () => (
    <div className="theme-list">
      <h1 className="theme-list__title">{category?.name}</h1>
      <p className="theme-list__description">{category?.description}</p>
      <CardList title={category?.name} categories={category?.children} products={category?.product} />
    </div>
  );

  return (
    <Grid right={getRight()} isLoggedIn={false} />
  );
}
