import React, { Component } from "react";
import { Link } from "react-router-dom"

interface LogoProps {
    src: string,
    alt: string,
}

export class Logo extends Component<LogoProps, {}> {
    render() {
        return (
            <Link to="/">
                <img className="menu__logo" src={this.props.src} />
            </Link>
        )
    }
}
