import React, { Component } from "react";
import { Link } from "react-router-dom"
import './Card.scss'

interface CardProps {
    src: string,
    alt: string,
    title: string,
    to: string,
}

export class Card extends Component<CardProps, {}> {
    render() {
        return (
            <Link className="card" to={this.props.to}>
                <img className="card__img" src={this.props.src} alt={this.props.alt} />
                <h3 className="card__title">{this.props.title}</h3>
            </Link>
        )
    }
}
