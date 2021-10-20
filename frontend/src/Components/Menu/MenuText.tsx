import React, { Component } from "react";

export class MenuText extends Component {
    render() {
        return (
            <span className="menu__text">{this.props.children}</span>
        )
    }
}
