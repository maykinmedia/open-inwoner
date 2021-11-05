import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import Markdown from 'markdown-to-jsx';
import { getProduct } from '../../api/calls';
import { Grid } from '../../Components/Container/Grid';
import { Divider } from '../../Components/Divider/Divider';
import AnchorMenu from '../../Components/Header/AnchorMenu';
import { File } from '../../Components/File/File';
import { Links } from '../../Components/Product/Links';
import { Related } from '../../Components/Product/Related';
import { Social } from '../../Components/Product/Social';
import { TagList } from '../../Components/Tags/TagList';
import { iProduct } from '../../types/pdc';
import './product.scss';


export default function ProductDetail() {
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
