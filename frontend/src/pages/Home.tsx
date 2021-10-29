import { Grid } from '../Components/Container/Grid'
import { TagList } from '../Components/Tags/TagList'
import { Breadcrumbs } from '../Components/Breadcrumbs/Breadcrumbs'
import SideMenu from '../Components/Menu/SideMenu'

export default function Home() {
    const getLeft = () => {
        return (
            <SideMenu></SideMenu>
        )
    }
    const getRight = () => {
        return (
            <>
                Home
            </>
        )
    }

    return (
        <Grid isLoggedIn={true} fixedLeft={true} left={getLeft()} right={getRight()} />
    )
}
