import React from 'react';
import { Link } from 'react-router-dom';
import './Breadcrumbs.scss';
import HomeOutlinedIcon from '@mui/icons-material/HomeOutlined';
import { iBreadcrumb } from '../../types/general';

interface BreadcrumbsProps {
    breadcrumbs: Array<iBreadcrumb>
}

export function Breadcrumbs(props:BreadcrumbsProps) {
  const getIconOrText = (breadcrumb:iBreadcrumb) => {
    if (breadcrumb.icon) {
      return <HomeOutlinedIcon />;
    }
    return breadcrumb.name;
  };

  return (
    <div className="breadcrumbs">
      {props.breadcrumbs.map((breadcrumb: iBreadcrumb) => <Link key={breadcrumb.to} className="breadcrumbs__breadcrumb" to={breadcrumb.to}>{ getIconOrText(breadcrumb) }</Link>)}
    </div>
  );
}
