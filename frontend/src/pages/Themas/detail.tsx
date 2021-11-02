import { useState, useEffect, useContext } from 'react';
import { useParams } from 'react-router-dom';

import { Grid } from '../../Components/Container/Grid'
import { CardList } from '../../Components/Card/CardList'
import { Breadcrumbs } from '../../Components/Breadcrumbs/Breadcrumbs'
import SideMenu from '../../Components/Menu/SideMenu'

import { iCategory } from '../../types/pdc';
import { getCategory } from '../../api/calls'
import { globalContext } from '../../store';
import './theme.scss'

export default function ThemaDetail() {
    const { globalState, dispatch } = useContext(globalContext);
    const [category, setCategory] = useState<iCategory | undefined>(undefined);
    let { slug } = useParams();

    useEffect(() => {
        const load = async () => {
            const resCategory = await getCategory(slug);
            setCategory(resCategory);
        }
        load();
    }, []);

    const getLeft = () => {
        return (
            <SideMenu></SideMenu>
        )
    }
    const getRight = () => {
        return (
            <div className="theme-list">
                <Breadcrumbs breadcrumbs={[{icon: true, name: 'Home', to: '/'}, {icon: false, name: 'Themas', to: '/themas'}, {icon: false, name: category?.name, to: `/themas/${category?.slug}`}]} />
                <h1 className="theme-list__title">{category?.name}</h1>
                <p className="theme-list__description">{category?.description}</p>
                <CardList title={category?.name} categories={category?.children} products={category?.product} />
            </div>
        )
    }

    return (
        <Grid fixedLeft={true} left={getLeft()} right={getRight()} isLoggedIn={ false } />
    )
}
