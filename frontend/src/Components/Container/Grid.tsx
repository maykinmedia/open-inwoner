import './Grid.scss'

interface GridProps {
    isLoggedIn: Boolean,
    fixedLeft: Boolean,
    left?: any,
    right?: any,
    children?: any,
}

export function Grid (props:GridProps) {
    const getClassNames = () => {
        let classNames = "grid"
        if (!props.isLoggedIn) {
            classNames += " grid--single"
        }
        if (props.fixedLeft) {
            classNames += " grid--fixed-left"
        }
        return classNames
    }

    const getLeft = () => {
        if (props.isLoggedIn) {
            return <div className="grid__left">{ props.left }</div>
        }
        return <></>
    }

    const getContent = () => {
        if (props.children) {
            return props.children
        }
        return (
            <>
                { getLeft() }
                <div className="grid__right">{ props.right }</div>
            </>
        )
    }

    return (
        <div className={ getClassNames() }>
            { getContent() }
        </div>
    )
}
