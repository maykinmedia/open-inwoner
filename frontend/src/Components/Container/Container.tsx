import React, { Component } from "react";
import './Container.scss'

interface ContainerProps {
}

export class Container extends Component<ContainerProps, {}> {
    render() {
        return (
            <main className="container">{ this.props.children }</main>
        )
    }
}
