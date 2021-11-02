import React, { Component } from "react";
import { Link } from "react-router-dom";
import ChevronRightIcon from '@mui/icons-material/ChevronRight';

import './Card.scss'

interface CategoryCardProps {
    title: string,
    to: string,
    products: Array<any>,
}

export class CategoryCard extends Component<CategoryCardProps, {}> {
    render() {
        return (
            <div className="card card--list">
                <h3 className="card__title">{this.props.title}</h3>
                <div className="card__links">
                    {this.props.products?.map(product => {
                        return (
                            <Link className="card__link" key={product.slug} to={`/product/${product.slug}`}>
                                {product.name}
                                <ChevronRightIcon />
                            </Link>
                        )
                    })}
                </div>
            </div>
        )
    }
}
