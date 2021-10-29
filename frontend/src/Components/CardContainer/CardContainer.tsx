import React, { Component } from "react";

import './CardContainer.scss'

interface CardContainerProps {
    isLoggedIn: Boolean,
}

export class CardContainer extends Component<CardContainerProps, {}> {
    getClassNames = () => {
        let classNames = "card-container"
        if (this.props.isLoggedIn) {
            classNames += " card-container--with-menu"
        }
        return classNames
    }

    render() {
        return (
            <div className="card-container">
                {this.props.children}
            </div>
        )
    }
}
