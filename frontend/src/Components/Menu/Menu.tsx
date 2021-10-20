import React, { Component } from "react";

import './Menu.scss'

export class Menu extends Component {
    render() {
        return (
            <header className="menu">
                <nav className="menu__container">
                    {this.props.children}
                </nav>
            </header>
        )
    }
}
