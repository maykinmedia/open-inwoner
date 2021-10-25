import React, { Component } from "react";
import './Submit.scss'

interface SubmitProps {
    value: string,
    name: string,
}

export class Submit extends Component<SubmitProps, {}> {
    render() {
        return (
            <input
                className="submit"
                type="submit"
                value={this.props.value}
                name={this.props.name}
                id={`id_${this.props.name}`}
            />
        )
    }
}
