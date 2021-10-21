import { Link } from "react-router-dom"

export default function Home() {
    console.log("Home page")
    return (
        <>
            <h1>Home page</h1>
            <Link to="/">Home</Link>
            <Link to="/about">About</Link>
            <Link to="/login">Login</Link>
            <Link to="/themas">Themas</Link>
        </>
    )
}
