import { Grid } from '../../Components/Container/Grid'
import { TagList } from '../../Components/Tags/TagList'
import { Breadcrumbs } from '../../Components/Breadcrumbs/Breadcrumbs'
import SideMenu from '../../Components/Menu/SideMenu'

import './theme.scss'

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
                <div className="theme">
                    <h1>Themas</h1>
                    <TagList tags={["Zorg en ondersteuning", "Wmo", "Gezond blijven", "Thema"]} />
                    <p>Een persoonlijk plan is een document waarin u vastlegt welke problemen u ervaart en welke oplossingen, zorg en ondersteuning daarbij passen. Het is een hulpmiddel om na te denken over wat voor ondersteuning u nodig heeft.</p>
                    <h2>Eenvoudige uitleg</h2>
                    <p>Voor uitleg in simpele taal kunt u ook kijken op Mijnondersteuningsplan.nl, een website die informatie geeft over het ondersteuningsplan, een soort persoonlijk plan. U kunt ook zelf een ondersteuningsplan maken door de vragen op de website te beantwoorden. Daarna kunt u het plan uitprinten.</p>
                    <p>Klik op de afbeelding om naar de website te gaan:</p>
                    <img src="https://via.placeholder.com/1500" />
                    <h2>Persoonlijk plan en keukentafelgesprek</h2>
                    <p>U mag een persoonlijk plan maken als u een melding doet bij Team Toegang Wmo, maar dit is niet verplicht. Lever het plan in uiterlijk 7 dagen nadat u melding heeft gedaan. Levert u het plan op tijd in, dan is de gemeente verplicht om het plan te bespreken bij het keukentafelgesprek.</p>
                    <p>Het is daarom handig om al met het persoonlijk plan te beginnen voordat u een melding doet bij Team Toegang Wmo. Dan heeft u er meer tijd voor. Meer lezen over de Wmo-melding.</p>
                    <h2>Persoonlijk plan maken</h2>
                    <p>Een persoonlijk plan maakt u in principe zelf. Komt u er alleen niet uit, vraag dan hulp aan iemand in uw omgeving. U kunt ook gratis hulp en advies krijgen van een cliëntondersteuner.</p>
                    <p>Wilt u aan de slag met maken van een persoonlijk plan, dan kunt u hier een Word-bestand met uitleg en werkbladen downloaden (DOCX, 19,9 kB). Deze vragenlijsten kunt u invullen en als basis voor uw plan gebruiken. Ze zijn onderdeel van de uitgebreide folder over het keukentafelgesprek (PDF, 168,9 kB).</p>
                    <h2>Online vragenlijst als hulpmiddel bij persoonlijk plan</h2>
                    <p>Door een vragenlijst in te vullen over uw leven kunt u gemakkelijk een overzicht krijgen van wat er speelt. Dat kan handig zijn bij het maken van uw persoonlijk plan.</p>
                    <p>U kunt bijvoorbeeld eens kijken op Mijn ZRM, een website waar u uw zelfredzaamheid kunt meten door stellingen te beantwoorden. ZRM staat voor zelfredzaamheidsmatrix. Veel gemeenten werken met deze methode.<br />
    Mijn kwaliteit van leven: op deze website kunt u met vragenlijsten uw situatie in beeld brengen. U kunt het resultaat gebruiken bij het maken van een persoonlijk plan. Maar de gegevens helpen ook om voor heel Nederland een beeld te schetsen. De makers van de website gebruiken dit om landelijk aandacht te vragen voor betere zorg.<br />
    Bent u van plan om een persoonsgebonden budget (pgb) aan te vragen, dan kunt u eens kijken naar de tips en het voorbeeldformulier van Per Saldo, de belangenvereniging voor mensen met een pgb.</p>
                </div>
            </>
        )
    }

    return (
        <Grid fixedLeft={true} left={getLeft()} right={getRight()} />
    )
}
