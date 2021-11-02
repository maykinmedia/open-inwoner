import React, { Component } from "react";

import './CardContainer.scss'

interface CardContainerProps {
    isLoggedIn: Boolean,
    children?: any,
}

export function CardContainer (props:CardContainerProps) {
    const getClassNames = () => {
        let classNames = "card-container"
        if (props.isLoggedIn) {
            classNames += " card-container--with-menu"
        }
        return classNames
    }

    return (
        <div className="card-container">
            { props.children }
        </div>
    )
}
