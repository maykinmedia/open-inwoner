import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';

import { Card } from '../../Components/Card/Card'
import { CardContainer } from "../../Components/CardContainer/CardContainer"
import { Grid } from '../../Components/Container/Grid'
import { Breadcrumbs } from '../../Components/Breadcrumbs/Breadcrumbs'
import SideMenu from '../../Components/Menu/SideMenu'

import { globalContext } from '../../store';

import './theme-list.scss'

export default function Themas() {
    console.log(import.meta.env);
    console.log(import.meta.env.VITE_API_URL);
    const { globalState, dispatch } = useContext(globalContext);
    const [categories, setCategories] = useState([]);

    useEffect(() => {
        const getCategories = async (email?: string, password?: string) => {
            try {
                const res = await axios.get(`${import.meta.env.VITE_API_URL}/api/categories/`).catch(err => {
                    console.log(err.response.data)
                    throw err;
                });
                setCategories(res.data);
            } catch(err) {
                console.log(err)
            }
        }
        getCategories();
    }, []);

    const getLeft = () => {
        return (
            <SideMenu></SideMenu>
        )
    }
    const getRight = () => {
        return (
            <div className="theme-list">
                <Breadcrumbs breadcrumbs={[{icon: false, name: 'Home', to: '/'}, {icon: false, name: 'Themas', to: '/themas'}]} />
                <h1 className="theme-list__title">Themas</h1>
                <p className="theme-list__description">Nulla vitae elit libero, a pharetra augue.</p>
                <CardContainer isLoggedIn={!!globalState.user}>
                    {categories.map((category) => <Card key={category.slug} src={category.image?.file} alt={category.image?.name} title={category.name} to={`/themas/${category.slug}`} />)}
                </CardContainer>
            </div>
        )
    }

    return (
        <Grid isLoggedIn={!!globalState.user} fixedLeft={true} left={getLeft()} right={getRight()} />
    )
}
