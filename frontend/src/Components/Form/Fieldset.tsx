import React, { Component } from "react";
import './Fieldset.scss'
import { Direction } from '../../Enums/direction'


interface FieldsetProps {
    direction: Direction
}

export class Fieldset extends Component<FieldsetProps, {}> {
    render() {
        return (
            <fieldset className={`fieldset fieldset--${this.props.direction}`}>{ this.props.children }</fieldset>
        )
    }
}
