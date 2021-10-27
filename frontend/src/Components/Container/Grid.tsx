import React, { Component } from "react";
import './Grid.scss'

interface GridProps {
    fixedLeft: Boolean,
    left: any,
    right: any,
}

export class Grid extends Component<GridProps, {}> {
    getClassNames = () => {
        let classNames = "grid"
        if (this.props.fixedLeft) {
            classNames += " grid--fixed-left"
        }
        return classNames
    }

    render() {
        return (
            <div className={this.getClassNames()}>
                <div className="grid__left">{this.props.left}</div>
                <div className="grid__right">{this.props.right}</div>
            </div>
        )
    }
}
