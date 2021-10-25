import React, { Component } from "react";
import './Label.scss'

interface LabelProps {
    for: string,
}

export class Label extends Component<LabelProps, {}> {
    render() {
        return (
            <label className="label" htmlFor={`id_${this.props.for}`}>{ this.props.children }</label>
        )
    }
}
