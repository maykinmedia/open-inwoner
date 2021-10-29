import React, { Component } from "react";
import './Grid.scss'

interface GridProps {
    isLoggedIn: Boolean,
    fixedLeft: Boolean,
    left?: any,
    right?: any,
}

export class Grid extends Component<GridProps, {}> {
    getClassNames = () => {
        let classNames = "grid"
        if (!this.props.isLoggedIn) {
            classNames += " grid--single"
        }
        if (this.props.fixedLeft) {
            classNames += " grid--fixed-left"
        }
        return classNames
    }

    getLeft = () => {
        if (this.props.isLoggedIn) {
            return <div className="grid__left">{this.props.left}</div>
        }
        return <></>
    }

    getContent = () => {
        if (this.props.children) {
            return this.props.children
        }
        return (
            <>
                {this.getLeft()}
                <div className="grid__right">{this.props.right}</div>
            </>
        )
    }

    render() {
        return (
            <div className={this.getClassNames()}>
                {this.getContent()}
            </div>
        )
    }
}
