import React, { useState, useEffect, useContext } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import Markdown from 'markdown-to-jsx';

import { Grid } from '../../Components/Container/Grid';
import { File } from '../../Components/File/File';
import { TagList } from '../../Components/Tags/TagList';
import { Breadcrumbs } from '../../Components/Breadcrumbs/Breadcrumbs';
import { Divider } from '../../Components/Divider/Divider';
import AnchorMenu from '../../Components/Menu/AnchorMenu';
import { Links } from '../../Components/Product/Links';
import { Related } from '../../Components/Product/Related';
import { Social } from '../../Components/Product/Social';

import { getProduct } from '../../api/calls';
import { globalContext } from '../../store';
import './product.scss';

interface iProduct {
    name: string,
    slug: string,
    summary: string,
    link: string,
    content: string,
    categories: string,
    relatedProducts?: Array<any>,
    tags: Array<any>,
    costs: string,
    created_on: string,
    organizations: string,
    files?: Array<any>,
    links?: Array<any>,
}

export default function ProductDetail() {
  const { globalState, dispatch } = useContext(globalContext);
  const [product, setProduct] = useState<iProduct | undefined>(undefined);
  const { slug } = useParams();

  useEffect(() => {
    const load = async () => {
      const product = await getProduct(slug);
      setProduct(product);
    };
    load();
  }, [slug]);

  const getContent = () => {
    if (product && product.content) {
      return <Markdown>{product.content}</Markdown>;
    }
    return <></>;
  };

  const getFiles = () => {
    if (product && product.files) {
      return (
        <>
          <Divider />
          <p id="files">Bestanden</p>
          <File />
          <File />
        </>
      );
    }
    return <></>;
  };

  const getFooter = () => (
    <>
      <Divider />
      <Grid isLoggedIn fixedLeft={false}>
        <Links id="links" links={product?.links} />
        <div>
          <Related id="see" related={product?.relatedProducts} />
          <Social id="share" />
        </div>
      </Grid>
    </>
  );

  const getLeft = () => (
    <AnchorMenu />
  );
  const getRight = () => (
    <>
      <Breadcrumbs breadcrumbs={[{ icon: true, name: 'Home', to: '/' }, { icon: false, name: 'Themas', to: '/themas' }, { icon: false, name: product?.name || '', to: `/product/${product?.slug}` }]} />
      <div className="product">
        <h1 id="title">{product?.name}</h1>
        <TagList tags={product?.tags} />
        <p>{product?.summary}</p>
        {getContent()}
        {getFiles()}
        {getFooter()}
      </div>
    </>
  );

  return (
    <Grid isLoggedIn fixedLeft left={getLeft()} right={getRight()} />
  );
}
