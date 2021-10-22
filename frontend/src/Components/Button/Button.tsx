import React, { Component } from "react";
import './Button.scss'

interface ButtonProps {
    href?: string,
    type?: string,
    open?: boolean,
}

export class Button extends Component<ButtonProps, {}> {
    getClassNames = () => {
        let classNames = "button"
        if (this.props.open) {
            classNames += " button--open"
        }
        return classNames
    }

    render() {
        if (this.props.href) {
            return (
                <a className={ this.getClassNames() } href={this.props.href}>{ this.props.children }</a>
            )
        }
        return (
            <button className={ this.getClassNames() } type={this.props.type}>{ this.props.children }</button>
        )
    }
}
