import { useContext } from 'react'
import { Link } from "react-router-dom"
import { globalContext } from '../../store';
import OpenInNewOutlinedIcon from '@mui/icons-material/OpenInNewOutlined';
import './ProductLinks.scss'

interface iLink {
    name: string,
    url: string,
}

interface iLinkProps {
    id: string,
    links?: Array<iLink>;
}

export function Links(props:iLinkProps) {
    const { globalState, dispatch } = useContext(globalContext);
    return (
        <div id={props.id} className="product-links">
            <h4 className="product-links__title">Links</h4>
            {props.links?.map((link:iLink, index:Number) => {
                return (
                    <a key={`${index}`} className="product-links__link" target="_blank" href={link.url}>
                        {link.name}
                        <OpenInNewOutlinedIcon className="product-links__icon" />
                    </a>
                )
            })}
        </div>
    )
}
