import React, { Component } from "react";
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { Button } from '../Button/Button';
import './Card.scss'

interface ProductCardProps {
    title: string,
    to: string,
    summary: string,
}

export class ProductCard extends Component<ProductCardProps, {}> {
    render() {
        return (
            <div className="card card--product">
                <h3 className="card__title">{this.props.title}</h3>
                <p className="card__summary">{this.props.summary}</p>
                <Button href={this.props.to} transparent={true}>
                    <ArrowForwardIcon />
                </Button>
            </div>
        )
    }
}
