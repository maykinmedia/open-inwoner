import { Link } from 'react-router-dom'


export default function NotFoundPage() {
    return (
        <>
            <div className="login">
                <h1>Pagina niet gevonden</h1>
                <Link to="/">Terug naar de homepagina</Link>
            </div>
        </>
    )
}
