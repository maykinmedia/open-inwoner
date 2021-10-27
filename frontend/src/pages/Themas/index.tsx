import { Card } from '../../Components/Card/Card'
import { CardContainer } from "../../Components/CardContainer/CardContainer"
import { Grid } from '../../Components/Container/Grid'
import { Breadcrumbs } from '../../Components/Breadcrumbs/Breadcrumbs'
import SideMenu from '../../Components/Menu/SideMenu'

export default function Themas() {
    const getLeft = () => {
        return (
            <SideMenu></SideMenu>
        )
    }
    const getRight = () => {
        return (
            <>
                <Breadcrumbs breadcrumbs={[{icon: false, name: 'Home', to: '/'}, {icon: false, name: 'Themas', to: '/themas'}]} />
                <h1>Themas</h1>
                <CardContainer>
                    <Card src="https://www.zwolle.nl/sites/all/themes/custom/zwolle_redesign/logo.png" alt="" title="Vervoer" to="/themas/1" />
                    <Card src="https://www.zwolle.nl/sites/all/themes/custom/zwolle_redesign/logo.png" alt="" title="Zorg en ondersteuning" to="/themas/1" />
                    <Card src="https://www.zwolle.nl/sites/all/themes/custom/zwolle_redesign/logo.png" alt="" title="Zorg en ondersteuning" to="/themas/1" />
                    <Card src="https://www.zwolle.nl/sites/all/themes/custom/zwolle_redesign/logo.png" alt="" title="Vervoer" to="/themas/1" />
                    <Card src="https://www.zwolle.nl/sites/all/themes/custom/zwolle_redesign/logo.png" alt="" title="Gezond blijven" to="/themas/1" />
                    <Card src="https://www.zwolle.nl/sites/all/themes/custom/zwolle_redesign/logo.png" alt="" title="Zorg en ondersteuning" to="/themas/1" />
                    <Card src="https://www.zwolle.nl/sites/all/themes/custom/zwolle_redesign/logo.png" alt="" title="Gezond blijven" to="/themas/1" />
                    <Card src="https://www.zwolle.nl/sites/all/themes/custom/zwolle_redesign/logo.png" alt="" title="Vervoer" to="/themas/1" />
                    <Card src="https://www.zwolle.nl/sites/all/themes/custom/zwolle_redesign/logo.png" alt="" title="Gezond blijven" to="/themas/1" />
                </CardContainer>
            </>
        )
    }

    return (
        <Grid fixedLeft={true} left={getLeft()} right={getRight()} />
    )
}
