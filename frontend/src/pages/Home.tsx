import { Grid } from '../Components/Container/Grid';
import SideMenu from '../Components/Menu/SideMenu';

export default function Home() {
  const getLeft = () => (
    <SideMenu />
  );
  const getRight = () => (
    <>
      Home
    </>
  );

  return (
    <Grid isLoggedIn fixedLeft left={getLeft()} right={getRight()} />
  );
}
