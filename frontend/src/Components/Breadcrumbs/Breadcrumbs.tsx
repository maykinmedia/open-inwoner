import React, { Component } from "react";
import { Link } from "react-router-dom"
import './Breadcrumbs.scss'
import HomeOutlinedIcon from '@mui/icons-material/HomeOutlined';

interface Breadcrumb {
    icon: boolean,
    name: string,
    to: string,
}

interface BreadcrumbsProps {
    breadcrumbs: Array<Breadcrumb>
}

export class Breadcrumbs extends Component<BreadcrumbsProps, {}> {
    getIconOrText = (breadcrumb:Breadcrumb) => {
        if (breadcrumb.icon) {
            return <HomeOutlinedIcon />
        }
        return breadcrumb.name
    }

    render() {
        return (
            <div className="breadcrumbs">
                {this.props.breadcrumbs.map((breadcrumb) => <Link key={breadcrumb.to} className="breadcrumbs__breadcrumb" to={breadcrumb.to}>{this.getIconOrText(breadcrumb)}</Link>)}
            </div>
        )
    }
}
