import React, {ReactElement, useContext} from 'react';
import {Grid} from '../Components/Container/Grid';
import {H1} from '../Components/Typography/H1';
import {globalContext} from '../store';
import {P} from '../Components/Typography/P';
import {Form} from '../Components/Form/Form';
import {iField} from '../types/field';
import {ProgressIndicator} from '../Components/ProgressIndicator/ProgressIndicator';
import {iLinkProps} from '../Components/Typography/Link';


/**
 * The profile page.
 * @return {ReactElement}
 */
export default function Profile(): ReactElement {
  const {globalState} = useContext(globalContext);

  const getSteps = (): iLinkProps[] => [
    {active: true, children: 'Persoonlijke gegevens', secondary: true, to: '#'},
    {active: false, children: 'Interessegebieden', to: '#'},
    {active: false, children: 'Contacten', to: '#'},
  ];

  const getFields = (): iField[] => [
    {label: 'Postcode', name: 'postal-code', type: 'text'},
    {label: 'Huisnummer', name: 'street-number', type: 'number'},
    {label: 'Toevoeging', name: 'street-addition', type: 'text'},
    {label: 'Geboortedatrum', name: 'date-of-birth', type: 'date'},
    {
      label: 'Gezinssamenstelling', name: 'family-composition', type: 'select', choices: [
        {label: 'Ongehuwd', value: 'not-married'},
        {label: 'Gehuwd', value: 'married'},
        {label: 'Gehuwd met kinderen', value: 'married-with-children'},
      ]
    },
  ];

  /**
   * Returns the main content.
   * @return {ReactElement}
   */
  const getMainContent = (): ReactElement => (
    <>
      <H1>Hallo {globalState.user?.firstName} {globalState.user?.lastName}</H1>
      <P>Vul hier uw persoonlijke gegevens in om op maat gemaakte content voorgeschoteld te krijgen
        en nog beter te kunnen zoeken en vinden</P>

      <Form columns={3} fields={getFields()} submitLabel="Verder naar interessegebieden"></Form>
    </>
  );

  /**
   * Returns the sidebar content.
   * @return {ReactElement}
   */
  const getSidebarContent = (): ReactElement => (
    <>
      <ProgressIndicator steps={getSteps()}/>
    </>
  )

  return (
    <Grid mainContent={getMainContent()} sidebarContent={getSidebarContent()}/>
  );
}
