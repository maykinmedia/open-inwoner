import React, { Component } from "react";
import { Link } from "react-router-dom"
import './Breadcrumbs.scss'

interface Breadcrumb {
    icon: boolean,
    name: string,
    to: string,
}

interface BreadcrumbsProps {
    breadcrumbs: Array<Breadcrumb>
}

export class Breadcrumbs extends Component<BreadcrumbsProps, {}> {
    render() {
        return (
            <div className="breadcrumbs">
                {this.props.breadcrumbs.map((breadcrumb) => <Link key={breadcrumb.to} className="breadcrumbs__breadcrumb" to={breadcrumb.to}>{breadcrumb.name}</Link>)}
            </div>
        )
    }
}
