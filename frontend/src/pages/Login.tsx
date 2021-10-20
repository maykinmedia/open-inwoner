export default function Login() {
    console.log("login page");
    return (
        <>
            <div className="card">
                <h1>Login</h1>
                <form  action="">
                    <fieldset>
                        <label htmlFor="">Emailadres</label>
                        <input type="email" name="email" id="id_email" />
                    </fieldset>
                    <fieldset>
                        <label htmlFor="">Wachtwoord</label>
                        <input type="password" name="password" id="id_password" />
                    </fieldset>
                    <input type="submit" value="Login" />
                    <a href="http://localhost:8000/digid/login/">Login met Digid</a>
                </form>
            </div>
        </>
    )
}
