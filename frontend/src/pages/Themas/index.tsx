import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';

import { Card } from '../../Components/Card/Card';
import { CardContainer } from '../../Components/CardContainer/CardContainer';
import { Grid } from '../../Components/Container/Grid';
import { Breadcrumbs } from '../../Components/Breadcrumbs/Breadcrumbs';
import SideMenu from '../../Components/Menu/SideMenu';

import { getCategories } from '../../api/calls';

import { globalContext } from '../../store';

import './theme-list.scss';
import { iCategory } from '../../types/pdc';

export default function Themas() {
  const { globalState, dispatch } = useContext(globalContext);
  const [categories, setCategories] = useState<Array<iCategory> | undefined>([]);

  useEffect(() => {
    const load = async () => {
      const resCategories = await getCategories();
      setCategories(resCategories);
    };
    load();
  }, []);

  const getLeft = () => (
    <SideMenu />
  );
  const getRight = () => {
    console.log(categories);
    return (
      <div className="theme-list">
        <Breadcrumbs breadcrumbs={[{ icon: true, name: 'Home', to: '/' }, { icon: false, name: 'Themas', to: '/themas' }]} />
        <h1 className="theme-list__title">Themas</h1>
        <p className="theme-list__description">Nulla vitae elit libero, a pharetra augue.</p>
        <CardContainer isLoggedIn={!!globalState.user}>
          {categories.map((category) => <Card key={category.slug} src={category.image?.file} alt={category.image?.name} title={category.name} to={`/themas/${category.slug}`} />)}
        </CardContainer>
      </div>
    );
  };

  return (
    <Grid isLoggedIn={!!globalState.user} fixedLeft left={getLeft()} right={getRight()} />
  );
}
