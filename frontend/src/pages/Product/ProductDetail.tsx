import React, {useState, useEffect, ReactElement} from 'react';
import {useParams} from 'react-router-dom';
import Markdown from 'markdown-to-jsx';
import {getProduct} from '../../api/calls';
import {Grid} from '../../Components/Container/Grid';
import {Divider} from '../../Components/Divider/Divider';
import AnchorMenu from '../../Components/Header/AnchorMenu';
import {LocationCardList} from '../../Components/Card/LocationCardList';
import {Image} from '../../Components/Image/Image';
import {Social} from '../../Components/Social/Social';
import {TagList} from '../../Components/Tags/TagList';
import {H1} from '../../Components/Typography/H1';
import {H3} from '../../Components/Typography/H3';
import {H4} from '../../Components/Typography/H4';
import {iLinkProps, Link} from '../../Components/Typography/Link';
import {LinkList} from '../../Components/Typography/LinkList';
import {P} from '../../Components/Typography/P';
import {iRouteLinkProps} from '../../Components/Typography/RouteLink';
import {ROUTES} from '../../routes/routes';
import {iLocation, iProduct, iProductLink} from '../../types/pdc';
import './product.scss';
import {FileList} from '../../Components/File/FileList';


export default function ProductDetail() {
  const [product, setProduct] = useState<iProduct | undefined>(undefined);
  const {categorySlug, subCategorySlug, productSlug} = useParams<{ [index: string]: string }>();

  useEffect(() => {
    const load = async () => {
      const product = await getProduct(productSlug);
      setProduct(product as iProduct);
    };
    load();
  }, [productSlug]);

  /**
   * Returns the link props for the anchor menu.
   */
  const getAnchorMenuLinkProps = (): iLinkProps[] => [
    ['title', product?.name],
    (product?.files?.length) ? ['files', 'Bestanden'] : null,
    (product?.locations?.length) ? ['locations', 'Locaties'] : null,
    (product?.links?.length) ? ['links', 'Links'] : null,
    (product?.relatedProducts?.length) ? ['see', 'Zie ook'] : null,
    ['share', 'Delen']
  ].filter(v => v).map(([to, label]): iLinkProps => ({
    children: label,
    to: `#${to}`,
  }))

  /**
   * Returns the link props for the links section.
   * @return {iLinkProps[]}
   */
  const getLinkProps = (): iLinkProps[] => product?.links.map((productLink: iProductLink): iLinkProps => ({
    to: productLink.url,
    children: productLink.name
  })) || []

  /**
   * Returns the link props for the related section.
   * @return {iLinkProps[]}
   */
  const getRelatedLinkProps = (): iRouteLinkProps[] => product?.relatedProducts.map((relatedProduct: iProduct): iRouteLinkProps => ({
    route: ROUTES.PRODUCT,

    // TODO: category slugs should be based on related product.
    routeParams: {
      categorySlug: categorySlug,
      subCategorySlug: subCategorySlug,
      productSlug: relatedProduct.slug
    }
  })) || []

  /**
   * Returns the sidebar content.
   * @return {ReactElement}
   */
  const renderSidebarContent = (): ReactElement => (
    <AnchorMenu links={getAnchorMenuLinkProps()}/>
  );

  /**
   * Returns the main content.
   * @return {ReactElement}
   */
  const renderMainContent = (): ReactElement => (
    <>
      <H1 id="title">{product?.name}</H1>
      <TagList tags={product?.tags}/>
      <P>{product?.summary}</P>
      {renderProductContent()}
      {renderFiles()}
      {renderLocations()}
      {renderFooter()}
    </>
  );

  /**
   * Get the (main) product content.
   * FIXME: Add addtional typography compoent when ready.
   * @return {ReactElement}
   */
  const renderProductContent = (): ReactElement => {
    const Wrapper = (props: { children: any }): ReactElement => <>{props.children}</>;

    const options = {
      overrides: {
        a: {component: Link, props: {className: 'link'}},
        h1: {component: H1, props: {autoId: true, className: 'h1'}},
        h3: {component: H3, props: {autoId: true, className: 'h3'}},
        h4: {component: H4, props: {autoId: true, className: 'h4'}},
        img: {component: Image, props: {className: 'image'}},
        p: {component: P, props: {className: 'p'}},
      },
      wrapper: Wrapper
    }

    if (product && product.content) {
      return <Markdown options={options}>{product.content}</Markdown>;
    }
    return <></>;
  };


  /**
   * Return the product file content.
   * @return {ReactElement}
   */
  const renderFiles = (): ReactElement => {
    return (
      <>
        <Divider/>
        <FileList id='files' files={product?.files}/>
      </>
    )
  }

  /**
   * Renders the locations.
   */
  const renderLocations = (): ReactElement => {
    if (!product?.locations) {
      return <></>;
    }

    return (
      <>
        <Divider/>
        <LocationCardList id='locations' locations={product?.locations as iLocation[]}/>
      </>
    )
  }

  /**
   * Gets the product footer.
   * @return {ReactElement}
   */
  const renderFooter = (): ReactElement => (
    <>
      <Divider/>
      <Grid>
        <LinkList id="links" title="Links" links={getLinkProps()}/>
        <aside>
          <LinkList id="see" title="Gerelateerd" links={getRelatedLinkProps()}/>
          <Social id="share"/>
        </aside>
      </Grid>
    </>
  );


  return (
    <Grid sidebarContent={renderSidebarContent()} mainContent={renderMainContent()}/>
  );
}
