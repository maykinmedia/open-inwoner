import './Tag.scss'

interface TagProps {
    key?: string
    children?: any,
}

export function Tag(props:TagProps) {
    return (
        <div className="tag">{props.children}</div>
    )
}
