import React, {useEffect, useState} from 'react';
import { Grid } from '../Components/Container/Grid';
import {H1} from '../Components/Typography/H1';
import { P } from '../Components/Typography/P';
import { Card } from '../Components/Card/Card';
import {Map} from '../Components/Map/Map';
import { CardContainer } from '../Components/CardContainer/CardContainer';
import {getCategories} from '../api/calls';
import {iCategory} from '../types/pdc';

export default function Home() {
  const [categories, setCategories] = useState<iCategory[]>([]);

  useEffect(() => {
    const load = async () => {
      const resCategories = await getCategories();
      setCategories(resCategories);
    };
    load();
  }, []);

  const getMainContent = () => (
    <>
      <H1>Welkom</H1>
      <P>Nullam quis risus eget urna mollis ornare vel eu leo. Etiam porta sem malesuada magna mollis euismod.</P>
      <H1>Thema&apos;s</H1>
      <P>Nullam quis risus eget urna mollis ornare vel eu leo. Etiam porta sem malesuada magna mollis euismod.</P>
      <CardContainer>
        {categories.map((category, index) => {
          if (index < 4) {
            return <Card key={category.slug} src={category.image?.file} alt={category.image?.name} title={category.name} to={`/themas/${category.slug}`} />
          }
        })}
      </CardContainer>
      <H1>In de buurt</H1>
      <P>Nullam quis risus eget urna mollis ornare vel eu leo. Etiam porta sem malesuada magna mollis euismod.</P>
      <Map fixed={false} lat={52.259221} long={6.163435} height="464" />
    </>
  );

  return (
    <Grid mainContent={getMainContent()} />
  );
}
