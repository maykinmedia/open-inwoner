import React, { Component } from "react";
import './TagList.scss'
import { Tag } from './Tag'

interface TagObject {
    pk: Number,
    name: String,
}

interface TagListProps {
    tags?: Array<TagObject>
}

export class TagList extends Component<TagListProps, {}> {
    render() {
        return (
            <div className="tag-list">
                {this.props.tags?.map((tag) => <Tag key={`${tag.pk}`}>{tag.name}</Tag>)}
            </div>
        )
    }
}
