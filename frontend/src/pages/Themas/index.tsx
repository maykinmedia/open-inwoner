import React, { useState, useEffect, useContext } from 'react';
import { getCategories } from '../../api/calls';
import { Card } from '../../Components/Card/Card';
import { CardContainer } from '../../Components/CardContainer/CardContainer';
import { Grid } from '../../Components/Container/Grid';
import { globalContext } from '../../store';
import { iCategory } from '../../types/pdc';
import './theme-list.scss';


export default function Themas() {
  const { globalState } = useContext(globalContext);
  const [categories, setCategories] = useState<Array<iCategory> | undefined>([]);

  useEffect(() => {
    const load = async () => {
      const resCategories = await getCategories();
      setCategories(resCategories);
    };
    load();
  }, []);

  const getRight = () => {
    return (
      <div className="theme-list">
        <h1 className="theme-list__title">Themas</h1>
        <p className="theme-list__description">Nulla vitae elit libero, a pharetra augue.</p>
        <CardContainer isLoggedIn={!!globalState.user}>
          {categories.map((category) => <Card key={category.slug} src={category.image?.file} alt={category.image?.name} title={category.name} to={`/themas/${category.slug}`} />)}
        </CardContainer>
      </div>
    );
  };

  return (
    <Grid isLoggedIn={!!globalState.user} mainContent={getRight()} />
  );
}
