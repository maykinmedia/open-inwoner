import React, { useState, useEffect, useContext } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import ReactMarkdown from 'react-markdown'
import Markdown from 'markdown-to-jsx';

import { Grid } from '../../Components/Container/Grid'
import { File } from '../../Components/File/File'
import { TagList } from '../../Components/Tags/TagList'
import { Breadcrumbs } from '../../Components/Breadcrumbs/Breadcrumbs'
import { Divider } from '../../Components/Divider/Divider'
import SideMenu from '../../Components/Menu/SideMenu'
import { Links } from '../../Components/Product/Links'
import { Related } from '../../Components/Product/Related'
import { Social } from '../../Components/Product/Social'

import { globalContext } from '../../store';
import './product.scss'

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
    let { slug } = useParams();

    useEffect(() => {
        const getProduct = async () => {
            try {
                const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/products/${slug}/`).catch(err => {
                    console.log(err.response.data)
                    throw err;
                });
                setProduct(res.data);
            } catch(err) {
                console.log(err)
            }
        }
        getProduct();
    }, [slug]);

    const getContent = () => {
        console.log(product)
        if (product && product.content) {
            return <Markdown>{product.content}</Markdown>
        }
        return <></>
    }

    const getFiles = () => {
        if (product && product.files) {
            return (
                <>
                    <Divider />
                    <p>Bestanden</p>
                    <File />
                    <File />
                </>
            )
        }
        return <></>
    }

    const getFooter = () => {
        return (
            <>
                <Divider />
                <Grid isLoggedIn={true} fixedLeft={false}>
                    <Links links={product?.links} />
                    <div>
                        <Related related={product?.relatedProducts}/>
                        <Social />
                    </div>
                </Grid>
            </>
        )
    }

    const getLeft = () => {
        return (
            <SideMenu></SideMenu>
        )
    }
    const getRight = () => {
        return (
            <>
                <Breadcrumbs breadcrumbs={[{icon: false, name: 'Home', to: '/'}, {icon: false, name: 'Themas', to: '/themas'}]} />
                <div className="product">
                    <h1>{product?.name}</h1>
                    <TagList tags={product?.tags} />
                    <p>{product?.summary}</p>
                    {getContent()}
                    {getFiles()}
                    {getFooter()}
                </div>
            </>
        )
    }

    return (
        <Grid isLoggedIn={true} fixedLeft={true} left={getLeft()} right={getRight()} />
    )
}
