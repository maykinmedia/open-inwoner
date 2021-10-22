import React, { Component } from "react";
import './Input.scss'

interface InputProps {
    type: string,
    value?: string,
    name: string,
    required: boolean,
    changeAction: Function,
}

export class Input extends Component<InputProps, {}> {
    handleOnChange = (event: any) => {
        if (this.props.changeAction) {
            this.props.changeAction(event);
        }
    }

    render() {
        return (
            <input
                className="input"
                type={this.props.type}
                value={this.props.value}
                name={this.props.name}
                id={`id_${this.props.name}`}
                required={this.props.required}
                onChange={this.handleOnChange}
            />
        )
    }
}
