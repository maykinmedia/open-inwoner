import { Link } from "react-router-dom"
import { Card } from '../Components/Card/Card'

export default function Themas() {
    return (
        <>
            <h1>Themas</h1>
            <Link to="/">Home</Link>
            <Link to="/about">About</Link>
            <Link to="/login">Login</Link>
            <Card src="https://www.zwolle.nl/sites/all/themes/custom/zwolle_redesign/logo.png" alt="" title="Zorg en ondersteuning" to="/themas" />
            <Card src="https://www.zwolle.nl/sites/all/themes/custom/zwolle_redesign/logo.png" alt="" title="Vervoer" to="/themas" />
            <Card src="https://www.zwolle.nl/sites/all/themes/custom/zwolle_redesign/logo.png" alt="" title="Gezond blijven" to="/themas" />
        </>
    )
}
