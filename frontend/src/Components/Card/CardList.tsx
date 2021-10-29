import React, { Component } from "react";
import { Link } from "react-router-dom"
import './Card.scss'

interface CardListProps {
    title?: string,
    products?: Array<any>,
}

export class CardList extends Component<CardListProps, {}> {
    render() {
        return (
            <div className="card">
                <h3 className="card__title">{this.props.title}</h3>
                {this.props.products?.map(product => <Link to={`/product/${product.slug}`}>{product.name}</Link>)}
            </div>
        )
    }
}
