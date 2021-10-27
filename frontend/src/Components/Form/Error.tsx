import React, { Component } from "react";
import './Error.scss'

export class Error extends Component<{}, {}> {
    render() {
        return (
            <div className="error">{ this.props.children }</div>
        )
    }
}
