import React, { Component } from "react";

import './CardContainer.scss'

export class CardContainer extends Component {
    render() {
        return (
            <div className="card-container">
                {this.props.children}
            </div>
        )
    }
}
