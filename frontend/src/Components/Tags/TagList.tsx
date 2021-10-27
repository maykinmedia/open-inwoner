import React, { Component } from "react";
import './TagList.scss'
import { Tag } from './Tag'

interface TagListProps {
    tags: Array<String>
}

export class TagList extends Component<TagListProps, {}> {
    render() {
        return (
            <div className="tag-list">
                {this.props.tags.map((tagName) => <Tag key={tagName}>{tagName}</Tag>)}
            </div>
        )
    }
}
