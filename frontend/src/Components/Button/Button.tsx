import React, { Component } from "react";
import { Link } from "react-router-dom";
import './Button.scss'

interface ButtonProps {
    href?: string,
    type?: string,
    open?: boolean,
    transparent?: boolean,
}

export class Button extends Component<ButtonProps, {}> {
    getClassNames = () => {
        let classNames = "button"
        if (this.props.open) {
            classNames += " button--open"
        }
        if (this.props.transparent) {
            classNames += " button--transparent"
        }
        return classNames
    }

    render() {
        if (this.props.href) {
            if (this.props.href.startsWith("http")) {
                return <a className={ this.getClassNames() } href={this.props.href}>{ this.props.children }</a>
            }
            return <Link className={ this.getClassNames() } to={this.props.href}>{ this.props.children }</Link>
        }
        return <button className={ this.getClassNames() } type={this.props.type}>{ this.props.children }</button>
    }
}
