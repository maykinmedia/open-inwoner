import React, { Component } from "react";
import './Tag.scss'

interface TagProps {
    key?: string
}

export class Tag extends Component<TagProps, {}> {
    render() {
        return (
            <div className="tag">{this.props.children}</div>
        )
    }
}
