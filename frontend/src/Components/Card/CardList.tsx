import React, { Component } from "react";
import { Link } from "react-router-dom"

import { CategoryCard } from './CategoryCard'
import { ProductCard } from './ProductCard'

import './CardList.scss'

interface CardListProps {
    title?: string,
    products?: Array<any>,
    categories?: Array<any>,
}

export class CardList extends Component<CardListProps, {}> {
    getCategories() {
        if (this.props.categories) {
            return (
                <div className="card-list" style={{"--columns": 4}}>
                    {this.props.categories?.map(category => <CategoryCard key={category.slug} to={`/themas/${category.slug}`} title={category.name} products={category.product} />)}
                </div>
            )
        }
        return null
    }

    getProducts() {
        if (this.props.products) {
            return (
                <div className="card-list">
                    {this.props.products?.map(product => <ProductCard key={product.slug} to={`/product/${product.slug}`} title={product.name} summary={ product.summary } />)}
                </div>
            )
        }
        return null
    }

    render() {
        return (
            <>
                { this.getCategories() }
                { this.getProducts() }
            </>
        )
    }
}
